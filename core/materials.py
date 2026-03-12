"""Material aggregation and supplier Excel export."""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from pathlib import Path

import xlsxwriter

from core.parser_excel import SmetaItem


@dataclass
class MaterialRow:
    index: int
    name: str
    unit: str
    quantity: float
    smeta_total: float  # Ceiling price from smeta
    codes: list[str]  # All FSNB codes for this material


def _normalize_name(name: str) -> str:
    """Normalize material name for grouping."""
    s = name.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


# Pattern: "1000 м3", "100 м2", "10 м", "1000 кг" etc.
_UNIT_MULTIPLIER_RE = re.compile(
    r"^(\d+)\s+(.+)$"
)


def _normalize_unit(unit: str, quantity: float) -> tuple[str, float]:
    """Strip multiplier prefix from unit and adjust quantity.

    "100 м2", qty=2.211 → "м2", qty=221.1
    "т", qty=1.19 → "т", qty=1.19 (no change)
    """
    stripped = unit.strip()
    m = _UNIT_MULTIPLIER_RE.match(stripped)
    if m:
        multiplier = int(m.group(1))
        base_unit = m.group(2).strip()
        if multiplier > 1:
            return base_unit, round(quantity * multiplier, 4)
    return stripped, quantity


def aggregate_materials(items: list[SmetaItem]) -> list[MaterialRow]:
    """Aggregate materials from smeta items by normalized name + unit.

    Groups identical materials, sums quantities and totals.
    If same name but different unit — keeps as separate rows.
    """
    groups: dict[tuple[str, str], MaterialRow] = {}

    mat_items = [it for it in items if it.item_type in ("material", "equipment")]
    idx = 0

    for it in mat_items:
        norm_unit, norm_qty = _normalize_unit(it.unit, it.quantity)
        key = (_normalize_name(it.name), norm_unit.lower().strip())

        if key in groups:
            groups[key].quantity += norm_qty
            groups[key].smeta_total += it.total_price
            if it.code not in groups[key].codes:
                groups[key].codes.append(it.code)
        else:
            idx += 1
            groups[key] = MaterialRow(
                index=idx,
                name=it.name,
                unit=norm_unit,
                quantity=norm_qty,
                smeta_total=it.total_price,
                codes=[it.code],
            )

    # Re-number after aggregation
    result = list(groups.values())
    for i, row in enumerate(result, 1):
        row.index = i
    return result


def export_supplier_excel(materials: list[MaterialRow], output: str | Path | io.BytesIO) -> None:
    """Export materials to Excel for supplier price request.

    Format: №, Name, Unit, Quantity, Price (empty), Total (empty), Note (empty).
    """
    wb = xlsxwriter.Workbook(output, {"in_memory": isinstance(output, io.BytesIO)})
    ws = wb.add_worksheet("Ведомость материалов")

    # Formats
    header_fmt = wb.add_format({
        "bold": True,
        "bg_color": "#4472C4",
        "font_color": "white",
        "border": 1,
        "text_wrap": True,
        "valign": "vcenter",
        "align": "center",
    })
    cell_fmt = wb.add_format({"border": 1, "text_wrap": True, "valign": "vcenter"})
    num_fmt = wb.add_format({"border": 1, "num_format": "#,##0.000", "valign": "vcenter"})
    price_fmt = wb.add_format({
        "border": 1,
        "num_format": "#,##0.00",
        "valign": "vcenter",
        "bg_color": "#FFF2CC",
    })

    # Column widths
    ws.set_column(0, 0, 5)   # №
    ws.set_column(1, 1, 55)  # Наименование
    ws.set_column(2, 2, 10)  # Ед. изм.
    ws.set_column(3, 3, 12)  # Объём
    ws.set_column(4, 4, 18)  # Цена поставщика
    ws.set_column(5, 5, 18)  # Сумма
    ws.set_column(6, 6, 25)  # Примечание

    # Headers
    headers = ["№", "Наименование", "Ед. изм.", "Объём", "Цена поставщика (руб.)", "Сумма (руб.)", "Примечание"]
    for col, h in enumerate(headers):
        ws.write(0, col, h, header_fmt)

    # Data rows
    for i, mat in enumerate(materials):
        row = i + 1
        ws.write_number(row, 0, mat.index, cell_fmt)
        ws.write_string(row, 1, mat.name, cell_fmt)
        ws.write_string(row, 2, mat.unit, cell_fmt)
        ws.write_number(row, 3, mat.quantity, num_fmt)
        ws.write_blank(row, 4, None, price_fmt)  # Supplier fills
        ws.write_blank(row, 5, None, price_fmt)  # Auto-calc or supplier fills
        ws.write_blank(row, 6, None, cell_fmt)

    wb.close()
