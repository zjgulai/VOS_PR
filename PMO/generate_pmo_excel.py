"""生成 PMO 业务协作 Excel（黄色高亮 = 业务需填写列）。

用法：python3 PMO/generate_pmo_excel.py
输出：PMO/01_阶段一_产品设计与数据契约/业务协作_竞品账号确认表.xlsx
      PMO/02_阶段二_数据采集落地/业务协作_待业务填写事项.xlsx
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "Library/Python/3.9/lib/python/site-packages"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from tools.social.dictionary import load_dictionary

PROJ = Path(__file__).resolve().parents[1]
PMO = PROJ / "PMO"

HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF")
FILL_FILL = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
OK_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
CENTER = Alignment(horizontal="center", vertical="center")


def _style_header(ws, ncols: int) -> None:
    for c in range(1, ncols + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = CENTER


def _fill_col(ws, col: int, nrows: int) -> None:
    for r in range(2, nrows + 2):
        ws.cell(row=r, column=col).fill = FILL_FILL


def _set_widths(ws, widths: list[int]) -> None:
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def gen_competitor_sheet() -> None:
    d = load_dictionary()
    fb = d.get("facebook_pages", {})
    wb = Workbook()
    ws = wb.active
    ws.title = "竞品账号确认"
    headers = ["品牌key", "品牌名", "品线", "层级", "优先级",
               "TikTok(预填)", "Instagram(预填)", "Facebook(预填)",
               "业务确认", "修正后handle"]
    ws.append(headers)
    for line in d["competitors"]["pump"] + d["competitors"]["feeding_appliance"]:
        ws.append([
            line["brand_key"], line["name"],
            "pump" if line in d["competitors"]["pump"] else "feeding_appliance",
            line["tier"], line["priority"],
            line.get("tiktok") or "", line.get("instagram") or "",
            fb.get(line["brand_key"], ""),
            "", "",
        ])
    _style_header(ws, len(headers))
    nrows = ws.max_row - 1
    _fill_col(ws, 9, nrows)
    _fill_col(ws, 10, nrows)
    _set_widths(ws, [16, 16, 18, 6, 8, 20, 22, 32, 10, 20])
    ws.freeze_panes = "A2"
    out = PMO / "01_阶段一_产品设计与数据契约" / "业务协作_竞品账号确认表.xlsx"
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(f"✓ {out.relative_to(PROJ)} ({nrows} 品牌)")


def gen_fill_sheet() -> None:
    wb = Workbook()

    ws1 = wb.active
    ws1.title = "1.FacebookGroups群组"
    ws1.append(["群组名称", "群组URL", "是否公开", "主题/垂类", "备注"])
    for _ in range(8):
        ws1.append(["", "", "", "", ""])
    _style_header(ws1, 5)
    for c in range(1, 6):
        _fill_col(ws1, c, 8)
    _set_widths(ws1, [28, 40, 10, 20, 20])
    ws1.freeze_panes = "A2"

    ws2 = wb.create_sheet("2.KOL关注池")
    ws2.append(["Creator账号", "平台", "垂类", "是否已合作", "备注"])
    for _ in range(8):
        ws2.append(["", "", "", "", ""])
    _style_header(ws2, 5)
    for c in range(1, 6):
        _fill_col(ws2, c, 8)
    _set_widths(ws2, [24, 12, 16, 12, 20])
    ws2.freeze_panes = "A2"

    ws3 = wb.create_sheet("3.周报接收人")
    ws3.append(["团队", "角色", "姓名/账号", "周报语言偏好", "接收方式"])
    for _ in range(6):
        ws3.append(["", "", "", "", ""])
    _style_header(ws3, 5)
    for c in range(1, 6):
        _fill_col(ws3, c, 6)
    _set_widths(ws3, [14, 16, 18, 16, 16])
    ws3.freeze_panes = "A2"

    ws4 = wb.create_sheet("4.部署服务器")
    ws4.append(["服务器类型", "访问方式", "IP/域名", "Python版本", "备注"])
    for _ in range(4):
        ws4.append(["", "", "", "", ""])
    _style_header(ws4, 5)
    for c in range(1, 6):
        _fill_col(ws4, c, 4)
    _set_widths(ws4, [16, 14, 20, 14, 20])
    ws4.freeze_panes = "A2"

    ws5 = wb.create_sheet("5.型号与别名")
    d = load_dictionary()
    ws5.append(["品牌", "核心型号(预填)", "是否监测", "标准型号", "BP编码", "别名"])
    for line in d["competitors"]["pump"] + d["competitors"]["feeding_appliance"]:
        ws5.append([
            line["name"], " / ".join(line.get("models") or []),
            "", "", "", "",
        ])
    _style_header(ws5, 6)
    nrows = ws5.max_row - 1
    for c in (3, 4, 5, 6):
        _fill_col(ws5, c, nrows)
    _set_widths(ws5, [16, 40, 10, 16, 12, 20])
    ws5.freeze_panes = "A2"

    out = PMO / "02_阶段二_数据采集落地" / "业务协作_待业务填写事项.xlsx"
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(f"✓ {out.relative_to(PROJ)} (5 sheets)")


if __name__ == "__main__":
    gen_competitor_sheet()
    gen_fill_sheet()
    print("完成")
