"""
Inner join SPU dimension and VOC detail on SPU code, star < 3, merge ticket + buyer text.
"""
from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DIM_SHEET = "组件"
DIM_KEY = "SPU编码"
DIM_EXTRA = ["SPU名称", "产品品线"]
VOC_SHEET = "VOC明细"
VOC_KEY = "SPU编码"
VOC_COLS = [
    "VOC产生日期", "平台名称", "渠道名称", "国家名称", "VOC标签",
    "工单客户原文", "买家评论", "星级评分",
]
STAR_COL = "星级评分"
MERGE_COL = "客户原文_合并"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_inputs(data_dir: Path) -> tuple[Path, Path]:
    candidates = [data_dir, data_dir / "add_data"]
    dim_path = voc_path = None
    for base in candidates:
        if not base.is_dir():
            continue
        for p in base.glob("*.xlsx"):
            if p.name.startswith("~$"):
                continue
            n = p.name
            if "SPU" in n and "产品线" in n and "维度" in n:
                dim_path = p
            if n.startswith("VOC差评明细表") and "202601" in n:
                voc_path = p
    if dim_path is None or voc_path is None:
        raise FileNotFoundError(
            f"未找到文件，已搜索: {candidates}。请用 --dim --voc 指定。"
        )
    return dim_path, voc_path


def normalize_spu_key(s):
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    t = str(s).strip()
    if not t or t.lower() == "nan":
        return None
    if re.fullmatch(r"\d+\.0", t):
        t = t[:-2]
    return t


def star_to_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    def one(x):
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return float("nan")
        if isinstance(x, (int, float)) and not isinstance(x, bool):
            return float(x)
        s = str(x).strip()
        m = re.search(r"(\d+(?:\.\d+)?)", s)
        return float(m.group(1)) if m else float("nan")

    return series.map(one)


def merge_two_texts(a, b, sep: str = "\n---\n") -> str:
    def clean(x) -> str:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return ""
        return str(x).strip()
    ca, cb = clean(a), clean(b)
    if ca and cb:
        return f"{ca}{sep}{cb}"
    return ca or cb


def main() -> None:
    root = _project_root()
    data_dir = root / "data"
    default_out_dir = data_dir / "add_data"

    parser = argparse.ArgumentParser()
    parser.add_argument("--dim", type=Path, default=None)
    parser.add_argument("--voc", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--star-lt", type=float, default=3.0)
    args = parser.parse_args()

    if args.dim and args.voc:
        dim_path, voc_path = args.dim, args.voc
    else:
        dim_path, voc_path = _resolve_inputs(data_dir)

    if args.out is None:
        default_out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_path = default_out_dir / f"VOC差评_SPU关联_星级lt3_合并原文_{ts}.xlsx"
    else:
        out_path = args.out

    dim = pd.read_excel(dim_path, sheet_name=DIM_SHEET)
    voc = pd.read_excel(voc_path, sheet_name=VOC_SHEET)

    for c in [DIM_KEY] + DIM_EXTRA:
        if c not in dim.columns:
            raise KeyError(f"维度表缺少列: {c}")
    for c in [VOC_KEY, STAR_COL] + VOC_COLS:
        if c not in voc.columns:
            raise KeyError(f"VOC表缺少列: {c}")

    dim["_spu_k"] = dim[DIM_KEY].map(normalize_spu_key)
    dim = dim.dropna(subset=["_spu_k"]).drop_duplicates(subset=["_spu_k"], keep="first")

    voc["_spu_k"] = voc[VOC_KEY].map(normalize_spu_key)
    voc["_star_num"] = star_to_numeric(voc[STAR_COL])
    voc_f = voc[voc["_star_num"] < args.star_lt].copy()
    n_voc_f = len(voc_f)

    dim_small = dim[["_spu_k"] + DIM_EXTRA].rename(columns={"SPU名称": "维度_SPU名称"})
    merged = voc_f.merge(dim_small, on="_spu_k", how="inner")
    n_after_join = len(merged)

    merged[MERGE_COL] = merged.apply(
        lambda r: merge_two_texts(r.get("工单客户原文"), r.get("买家评论")),
        axis=1,
    )
    merged = merged[merged[MERGE_COL].str.strip() != ""]

    out_cols = [VOC_KEY, "产品品线", "维度_SPU名称"] + VOC_COLS + [MERGE_COL, "_star_num"]
    seen = set()
    out_cols_unique = []
    for c in out_cols:
        if c in merged.columns and c not in seen:
            seen.add(c)
            out_cols_unique.append(c)

    result = merged[out_cols_unique].copy().rename(columns={"_star_num": "星级_数值"})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_excel(out_path, index=False, engine="openpyxl")

    profile_path = out_path.with_suffix(".profile.txt")
    n_dim = int(dim["_spu_k"].nunique())
    profile_path.write_text(
        "\n".join([
            f"dim_file={dim_path}",
            f"voc_file={voc_path}",
            f"out_file={out_path}",
            f"voc_rows_total={len(voc)}",
            f"voc_rows_star_lt={n_voc_f}",
            f"rows_after_inner_join={n_after_join}",
            f"rows_final={len(result)}",
            f"unique_spu_dim={n_dim}",
        ]) + "\n",
        encoding="utf-8",
    )
    print(out_path)
    print(len(result))


if __name__ == "__main__":
    main()
