"""Fixed column-width geometry for python-docx tables.

Vendored locally so ``build_agenda_docx.py`` can be rebuilt on any machine
without depending on an absolute path into one contributor's tooling cache.

``apply_table_geometry(table, col_widths_twips)`` switches a table to a fixed
layout and pins each column to an explicit width in twips (1/1440 inch), which
is the only reliable way to make Word honour column widths instead of
auto-fitting to content.
"""

from __future__ import annotations

from typing import Sequence

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Twips
from docx.table import Table


def apply_table_geometry(table: Table, col_widths_twips: Sequence[int]) -> Table:
    """Pin ``table`` to a fixed layout with the given per-column widths (twips)."""
    tbl = table._tbl
    tbl_pr = tbl.tblPr

    # Fixed layout: Word honours explicit widths instead of autofitting.
    table.autofit = False
    layout = tbl_pr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tbl_pr.append(layout)
    layout.set(qn("w:type"), "fixed")

    total = int(sum(col_widths_twips))
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(total))
    tbl_w.set(qn("w:type"), "dxa")

    # Grid definition (one <w:gridCol> per column).
    grid = tbl.find(qn("w:tblGrid"))
    if grid is not None:
        cols = grid.findall(qn("w:gridCol"))
        for col, width in zip(cols, col_widths_twips):
            col.set(qn("w:w"), str(int(width)))

    # Per-cell width, applied to every row.
    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            if idx < len(col_widths_twips):
                cell.width = Twips(int(col_widths_twips[idx]))

    return table
