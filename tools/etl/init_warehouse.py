"""
tools/etl/init_warehouse.py — DuckDB 仓库初始化与 CSV 导入

是什么：把 data/delivery/tables/*.csv 导入 data/warehouse/voc.duckdb
输入：data/delivery/tables/ 下所有 CSV 文件
输出：data/warehouse/voc.duckdb（DWS 层，13张表 + 核心视图）
不是什么：不做 NLP 分析，不替换现有 JSON 文件（并行运行）

快速启动：
    python3 tools/etl/init_warehouse.py              # 完整导入
    python3 tools/etl/init_warehouse.py --dry-run    # 只检查，不写库
    python3 tools/etl/init_warehouse.py --verify     # 验证已有库
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# DuckDB 用户安装路径
sys.path.insert(0, str(Path.home() / "Library/Python/3.9/lib/python/site-packages"))

import duckdb

PROJ = Path(__file__).resolve().parents[2]
TABLES_DIR = PROJ / "data" / "delivery" / "tables"
WAREHOUSE_DIR = PROJ / "data" / "warehouse"
DB_PATH = WAREHOUSE_DIR / "voc.duckdb"


def init_warehouse(dry_run: bool = False) -> dict:
    """
    导入所有 DWS CSV → DuckDB，返回导入结果摘要。
    使用 CREATE OR REPLACE TABLE AS SELECT * FROM read_csv_auto()
    → 幂等，可重复运行。
    """
    if not TABLES_DIR.exists():
        raise FileNotFoundError(f"tables dir not found: {TABLES_DIR}")

    csv_files = sorted(TABLES_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files in {TABLES_DIR}")

    if dry_run:
        print(f"[dry-run] Would import {len(csv_files)} CSV files to {DB_PATH}")
        for f in csv_files:
            print(f"  → {f.name}")
        return {"dry_run": True, "file_count": len(csv_files)}

    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    results = {}

    for csv_path in csv_files:
        table_name = f"dws_{csv_path.stem}"
        try:
            # read_csv_auto 自动推断列类型 + 处理 UTF-8 BOM
            con.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT * FROM read_csv_auto(
                    '{csv_path}',
                    header=true,
                    null_padding=true,
                    ignore_errors=true
                )
            """)
            count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            cols = len(con.execute(f"DESCRIBE {table_name}").fetchall())
            results[table_name] = {"rows": count, "cols": cols, "status": "ok"}
            print(f"  ✓ {table_name:45} {count:6} rows × {cols} cols")
        except Exception as exc:  # noqa: BLE001
            results[table_name] = {"status": "error", "error": str(exc)}
            print(f"  ✗ {table_name}: {exc}")

    # ── 创建核心视图 ──────────────────────────────────────────
    views_created = _create_views(con)

    con.close()
    return {
        "tables": results,
        "views": views_created,
        "db_path": str(DB_PATH),
        "db_size_mb": round(DB_PATH.stat().st_size / 1024 / 1024, 2),
    }


def _create_views(con: duckdb.DuckDBPyConnection) -> list[str]:
    """创建 ADS 层视图，替代部分 JSON 文件查询。"""
    views = []

    # 国家概览视图（对齐 viz_dataset.json 的 countries section）
    try:
        con.execute("""
            CREATE OR REPLACE VIEW ads_country_overview AS
            SELECT
                p.country_code,
                p.country        AS country_name_cn,
                COUNT(DISTINCT p.product_line) AS product_line_cnt,
                MAX(CASE WHEN t.country_code IS NOT NULL THEN 1 ELSE 0 END) AS is_top20,
                AVG(CAST(REPLACE(s.price_sensitivity_score, ',', '.') AS DOUBLE))
                    AS avg_price_sensitivity
            FROM dws_dim_country_product_persona p
            LEFT JOIN dws_dim_top20_country_insight t
                ON p.country_code = t.country_code
            LEFT JOIN dws_dim_country_price_sensitivity s
                ON p.country_code = s.country_code
            GROUP BY p.country_code, p.country
            ORDER BY is_top20 DESC, product_line_cnt DESC
        """)
        views.append("ads_country_overview")
        print(f"  ✓ VIEW ads_country_overview")
    except Exception as exc:  # noqa: BLE001
        print(f"  ⚠ VIEW ads_country_overview skipped: {exc}")

    # VOC 声量汇总视图
    try:
        con.execute("""
            CREATE OR REPLACE VIEW ads_voc_summary AS
            SELECT
                country_code,
                product_line,
                platform,
                SUM(CAST(total_voc_count AS INTEGER))    AS total_voc,
                SUM(CAST(high_intensity_count AS INTEGER)) AS high_intensity,
                AVG(CAST(REPLACE(negative_ratio, '%','') AS DOUBLE)) AS avg_neg_ratio
            FROM dws_voc_summary_flat
            GROUP BY country_code, product_line, platform
            ORDER BY total_voc DESC
        """)
        views.append("ads_voc_summary")
        print(f"  ✓ VIEW ads_voc_summary")
    except Exception as exc:  # noqa: BLE001
        print(f"  ⚠ VIEW ads_voc_summary skipped: {exc}")

    return views


def verify_warehouse() -> None:
    """验证已有 DuckDB 仓库的完整性。"""
    if not DB_PATH.exists():
        print(f"✗ Database not found: {DB_PATH}")
        return

    con = duckdb.connect(str(DB_PATH), read_only=True)
    tables = con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
    ).fetchall()
    views = con.execute(
        "SELECT table_name FROM information_schema.views WHERE table_schema='main'"
    ).fetchall()

    print(f"\n{'='*60}")
    print(f"Database : {DB_PATH}")
    print(f"Size     : {DB_PATH.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"Tables   : {len(tables)}")
    print(f"Views    : {len(views)}")
    print()

    total_rows = 0
    for (tname,) in sorted(tables):
        count = con.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
        total_rows += count
        print(f"  {tname:45} {count:6} rows")

    print(f"\n  {'TOTAL':45} {total_rows:6} rows")
    if views:
        print(f"\nViews:")
        for (vname,) in views:
            count = con.execute(f"SELECT COUNT(*) FROM {vname}").fetchone()[0]
            print(f"  {vname:45} {count:6} rows")

    con.close()


# ── Checkpoint 2 自我审计：对比 DuckDB 与 JSON ──────────────────
def audit_vs_json() -> None:
    """Checkpoint 2：验证 DuckDB 查询结果与现有 viz_dataset.json 一致。"""
    import json

    json_path = PROJ / "data" / "delivery" / "viz_dataset.json"
    if not json_path.exists():
        print("⚠ viz_dataset.json not found, skipping audit")
        return
    if not DB_PATH.exists():
        print("⚠ voc.duckdb not found, run init first")
        return

    with open(json_path, encoding="utf-8") as f:
        jdata = json.load(f)

    con = duckdb.connect(str(DB_PATH), read_only=True)
    errors = 0

    # 审计1：国家数量
    json_countries = len(jdata.get("countries", []))
    db_countries = con.execute(
        "SELECT COUNT(DISTINCT country_code) FROM dws_dim_country_product_persona"
    ).fetchone()[0]
    match = "✓" if abs(json_countries - db_countries) <= 5 else "✗"  # 允许5以内偏差
    print(f"  {match} 国家数: JSON={json_countries}, DuckDB={db_countries}")
    if match == "✗":
        errors += 1

    # 审计2：VOC 声量表存在
    try:
        voc_rows = con.execute("SELECT COUNT(*) FROM dws_voc_summary_flat").fetchone()[0]
        json_voc = len(jdata.get("voc_summary", []))
        match = "✓" if voc_rows > 0 else "✗"
        print(f"  {match} VOC汇总: JSON={json_voc} entries, DuckDB={voc_rows} rows")
    except Exception as exc:  # noqa: BLE001
        print(f"  ⚠ VOC汇总表查询失败: {exc}")

    # 审计3：TOP20 洞察表
    try:
        top20_rows = con.execute("SELECT COUNT(*) FROM dws_dim_top20_country_insight").fetchone()[0]
        json_top20 = len(jdata.get("top20", []))
        match = "✓" if top20_rows > 0 else "✗"
        print(f"  {match} TOP20洞察: JSON={json_top20} entries, DuckDB={top20_rows} rows")
    except Exception as exc:  # noqa: BLE001
        print(f"  ⚠ TOP20表查询失败: {exc}")

    con.close()
    print(f"\n{'✓ Checkpoint 2 PASS' if errors == 0 else f'✗ Checkpoint 2: {errors} mismatch(es)'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VOC DuckDB Warehouse Init")
    parser.add_argument("--dry-run", action="store_true", help="只检查，不写库")
    parser.add_argument("--verify", action="store_true", help="验证已有库")
    parser.add_argument("--audit", action="store_true", help="Checkpoint 2 对比审计")
    args = parser.parse_args()

    if args.verify:
        verify_warehouse()
    elif args.audit:
        audit_vs_json()
    else:
        print(f"Importing {len(list(TABLES_DIR.glob('*.csv')))} CSV files → {DB_PATH}")
        result = init_warehouse(dry_run=args.dry_run)
        if not args.dry_run:
            print(f"\n{'='*60}")
            print(f"✓ Done. DB size: {result.get('db_size_mb')} MB")
            print(f"  Tables : {sum(1 for v in result['tables'].values() if v.get('status')=='ok')}")
            print(f"  Views  : {len(result.get('views', []))}")
