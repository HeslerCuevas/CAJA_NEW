"""
Shift Reconciliation & Audit Report Generator (Cuadre de Caja)
Generates a professional PDF audit report at register close using reportlab.
Reports are stored in the ShiftReports/ folder at the project root.
"""

import os
import datetime
from decimal import Decimal

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import (
    HexColor, white, black, Color
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas as pdf_canvas


# ── Colour Palette ─────────────────────────────────────────────────────
DARK_BG       = HexColor("#0b1120")
DARK_ROW      = HexColor("#131b2e")
HEADER_BG     = HexColor("#0f172a")
ACCENT_BLUE   = HexColor("#0ea5e9")
ACCENT_CYAN   = HexColor("#38bdf8")
SECTION_BG    = HexColor("#1e293b")
TEXT_WHITE     = HexColor("#f8fafc")
TEXT_MUTED     = HexColor("#94a3b8")
GREEN_OK      = HexColor("#10b981")
RED_ALERT     = HexColor("#e11d48")
AMBER_WARN    = HexColor("#fbbf24")
BORDER_LINE   = HexColor("#334155")
LIGHT_GRAY_BG = HexColor("#e2e8f0")
DARK_STRIPE   = HexColor("#f1f5f9")


def _get_reports_folder():
    """Return the ShiftReports folder path, creating it if needed."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    folder = os.path.join(project_root, "ShiftReports")
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder


def _fmt(value):
    """Format a numeric value as $#,##0.00"""
    try:
        v = float(value) if value is not None else 0.0
    except (ValueError, TypeError):
        v = 0.0
    return f"$ {v:,.2f}"


def _pct(value):
    """Format a percentage."""
    try:
        return f"{float(value):.1f}%"
    except:
        return "0.0%"


class _NumberedCanvas(pdf_canvas.Canvas):
    """Canvas subclass that adds page numbers in the footer."""

    def __init__(self, *args, **kwargs):
        pdf_canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        pdf_canvas.Canvas.showPage(self)

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_footer(num_pages)
            pdf_canvas.Canvas.showPage(self)
        pdf_canvas.Canvas.save(self)

    def _draw_footer(self, page_count):
        self.setFont("Helvetica", 7)
        self.setFillColor(HexColor("#94a3b8"))
        page_w = letter[0]
        self.drawCentredString(
            page_w / 2, 12 * mm,
            f"Page {self._pageNumber} of {page_count}  •  NOCTURNAL BAR  •  Confidential Audit Document"
        )


def generate_shift_report(shift_data: dict) -> str:
    """
    Generate a professional Shift Reconciliation & Audit Report PDF.

    Parameters
    ----------
    shift_data : dict
        Dictionary with keys: shift_info, cash_flow, sales_summary,
        financials, transactions.

    Returns
    -------
    str
        Absolute path to the generated PDF file.
    """
    folder = _get_reports_folder()
    shift_id = shift_data.get("shift_info", {}).get("shift_id", "UNKNOWN")
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(folder, f"ShiftReport_{shift_id}_{ts}.pdf")

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        topMargin=20 * mm,
        bottomMargin=25 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        title=f"Shift Audit {shift_id}",
        author="Nocturnal Bar POS",
    )

    styles = getSampleStyleSheet()

    # ── Custom Styles ──────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=HexColor("#0f172a"),
        alignment=TA_CENTER,
        spaceAfter=2,
        spaceBefore=0,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=HexColor("#64748b"),
        alignment=TA_CENTER,
        spaceAfter=10,
    )
    section_style = ParagraphStyle(
        "SectionHead",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=HexColor("#0f172a"),
        spaceBefore=14,
        spaceAfter=6,
        borderPadding=4,
    )
    cell_normal = ParagraphStyle(
        "CellNormal",
        fontName="Helvetica",
        fontSize=9,
        textColor=HexColor("#1e293b"),
        leading=12,
    )
    cell_bold = ParagraphStyle(
        "CellBold",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=HexColor("#0f172a"),
        leading=12,
    )
    cell_money = ParagraphStyle(
        "CellMoney",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=HexColor("#0f172a"),
        alignment=TA_RIGHT,
        leading=12,
    )
    cell_right = ParagraphStyle(
        "CellRight",
        fontName="Helvetica",
        fontSize=9,
        textColor=HexColor("#1e293b"),
        alignment=TA_RIGHT,
        leading=12,
    )

    elements = []

    # ══════════════════════════════════════════════════════════════════
    #  HEADER BANNER
    # ══════════════════════════════════════════════════════════════════
    banner_data = [[
        Paragraph(
            '<font color="#0ea5e9">■</font>&nbsp;&nbsp;'
            '<font color="#0f172a"><b>NOCTURNAL BAR</b></font>&nbsp;&nbsp;—&nbsp;&nbsp;'
            '<font color="#64748b">SHIFT RECONCILIATION &amp; AUDIT REPORT</font>',
            ParagraphStyle("banner", fontName="Helvetica-Bold", fontSize=14,
                           textColor=HexColor("#0f172a"), alignment=TA_CENTER, leading=18)
        )
    ]]
    banner_table = Table(banner_data, colWidths=[doc.width])
    banner_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 1.5, HexColor("#0ea5e9")),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    elements.append(banner_table)
    elements.append(Spacer(1, 4 * mm))

    # ══════════════════════════════════════════════════════════════════
    #  SECTION 1 — SHIFT INFORMATION
    # ══════════════════════════════════════════════════════════════════
    si = shift_data.get("shift_info", {})
    elements.append(Paragraph("① SHIFT INFORMATION", section_style))

    info_rows = [
        [Paragraph("<b>Field</b>", cell_bold),
         Paragraph("<b>Value</b>", cell_bold)],
        [Paragraph("Employee", cell_normal),
         Paragraph(str(si.get("employee_name", "—")), cell_normal)],
        [Paragraph("Shift ID", cell_normal),
         Paragraph(str(si.get("shift_id", "—")), cell_normal)],
        [Paragraph("Terminal", cell_normal),
         Paragraph(str(si.get("terminal", "POS-01")), cell_normal)],
        [Paragraph("Branch (Sucursal)", cell_normal),
         Paragraph(str(si.get("branch_id", "—")), cell_normal)],
        [Paragraph("Open Time", cell_normal),
         Paragraph(str(si.get("open_time", "—")), cell_normal)],
        [Paragraph("Close Time", cell_normal),
         Paragraph(str(si.get("close_time", "—")), cell_normal)],
        [Paragraph("Shift Duration", cell_normal),
         Paragraph(str(si.get("duration", "—")), cell_normal)],
    ]
    info_table = Table(info_rows, colWidths=[doc.width * 0.35, doc.width * 0.65])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#f8fafc")]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 4 * mm))

    # ══════════════════════════════════════════════════════════════════
    #  SECTION 2 — CASH FLOW ANALYSIS
    # ══════════════════════════════════════════════════════════════════
    cf = shift_data.get("cash_flow", {})
    elements.append(Paragraph("② CASH FLOW ANALYSIS", section_style))

    discrepancy = float(cf.get("discrepancy", 0))
    disc_color = GREEN_OK if discrepancy == 0 else RED_ALERT

    cf_rows = [
        [Paragraph("<b>Item</b>", cell_bold),
         Paragraph("<b>Amount</b>", ParagraphStyle("hdr_r", parent=cell_bold, alignment=TA_RIGHT))],
        [Paragraph("Starting Float (Fondo Inicial)", cell_normal),
         Paragraph(_fmt(cf.get("starting_float", 0)), cell_right)],
        [Paragraph("(+) Cash Sales during Shift", cell_normal),
         Paragraph(_fmt(cf.get("cash_sales", 0)), cell_right)],
        [Paragraph("(−) Cash Out / Withdrawals", cell_normal),
         Paragraph(_fmt(cf.get("cash_out", 0)), cell_right)],
    ]

    # Expected Cash row — highlighted
    cf_rows.append([
        Paragraph("<b>= Expected Cash in Drawer</b>", cell_bold),
        Paragraph("<b>" + _fmt(cf.get("expected_cash", 0)) + "</b>",
                  ParagraphStyle("exp", parent=cell_money, textColor=ACCENT_BLUE)),
    ])
    # Actual Cash Counted — highlighted
    cf_rows.append([
        Paragraph("<b>Actual Cash Counted</b>", cell_bold),
        Paragraph("<b>" + _fmt(cf.get("actual_cash", 0)) + "</b>",
                  ParagraphStyle("act", parent=cell_money, textColor=HexColor("#0f172a"))),
    ])
    # Discrepancy — conditional colour
    disc_text_color = "#10b981" if discrepancy == 0 else "#ffffff"
    disc_bg = GREEN_OK if discrepancy == 0 else RED_ALERT
    cf_rows.append([
        Paragraph("<b>⚠ DISCREPANCY (Descuadre)</b>", cell_bold),
        Paragraph(
            f'<b><font color="{disc_text_color}">{_fmt(discrepancy)}</font></b>',
            ParagraphStyle("disc", parent=cell_money,
                           textColor=HexColor(disc_text_color))
        ),
    ])

    cf_table = Table(cf_rows, colWidths=[doc.width * 0.60, doc.width * 0.40])
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -4), [white, HexColor("#f8fafc")]),
        ("BACKGROUND", (0, -3), (-1, -3), HexColor("#eff6ff")),  # expected
        ("BACKGROUND", (0, -2), (-1, -2), HexColor("#f0fdf4")),  # actual
        ("BACKGROUND", (0, -1), (-1, -1), disc_bg),              # discrepancy
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]
    if discrepancy != 0:
        style_cmds.append(("TEXTCOLOR", (0, -1), (-1, -1), white))
    cf_table.setStyle(TableStyle(style_cmds))
    elements.append(cf_table)

    # Discrepancy alert box
    if discrepancy != 0:
        elements.append(Spacer(1, 2 * mm))
        direction = "OVER" if discrepancy > 0 else "SHORT"
        alert_data = [[
            Paragraph(
                f'<font color="#ffffff"><b>⚠ CASH REGISTER IS {direction} BY {_fmt(abs(discrepancy))}. '
                f'MANAGER REVIEW REQUIRED.</b></font>',
                ParagraphStyle("alert", fontName="Helvetica-Bold", fontSize=10,
                               textColor=white, alignment=TA_CENTER, leading=14)
            )
        ]]
        alert_table = Table(alert_data, colWidths=[doc.width])
        alert_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), RED_ALERT),
            ("BOX", (0, 0), (-1, -1), 1.5, HexColor("#9f1239")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(alert_table)
    else:
        elements.append(Spacer(1, 2 * mm))
        ok_data = [[
            Paragraph(
                '<font color="#065f46"><b>✓ CASH BALANCED — No discrepancy detected.</b></font>',
                ParagraphStyle("ok", fontName="Helvetica-Bold", fontSize=10,
                               textColor=HexColor("#065f46"), alignment=TA_CENTER, leading=14)
            )
        ]]
        ok_table = Table(ok_data, colWidths=[doc.width])
        ok_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#d1fae5")),
            ("BOX", (0, 0), (-1, -1), 1, GREEN_OK),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(ok_table)
    elements.append(Spacer(1, 4 * mm))

    # ══════════════════════════════════════════════════════════════════
    #  SECTION 3 — SALES SUMMARY BY PAYMENT METHOD
    # ══════════════════════════════════════════════════════════════════
    ss = shift_data.get("sales_summary", {})
    elements.append(Paragraph("③ SALES SUMMARY BY PAYMENT METHOD", section_style))

    total_sales_all = sum(float(v.get("total", 0)) for v in ss.values()) if ss else 0

    ss_rows = [
        [Paragraph("<b>Payment Method</b>", cell_bold),
         Paragraph("<b>Transactions</b>", ParagraphStyle("h", parent=cell_bold, alignment=TA_CENTER)),
         Paragraph("<b>Total</b>", ParagraphStyle("h", parent=cell_bold, alignment=TA_RIGHT)),
         Paragraph("<b>% Share</b>", ParagraphStyle("h", parent=cell_bold, alignment=TA_RIGHT))],
    ]
    for method, data in ss.items():
        t = float(data.get("total", 0))
        pct = (t / total_sales_all * 100) if total_sales_all > 0 else 0
        ss_rows.append([
            Paragraph(str(method), cell_normal),
            Paragraph(str(data.get("count", 0)),
                      ParagraphStyle("c", parent=cell_normal, alignment=TA_CENTER)),
            Paragraph(_fmt(t), cell_right),
            Paragraph(_pct(pct), cell_right),
        ])
    # Grand total row
    total_count = sum(int(v.get("count", 0)) for v in ss.values()) if ss else 0
    ss_rows.append([
        Paragraph("<b>GRAND TOTAL</b>", cell_bold),
        Paragraph(f"<b>{total_count}</b>",
                  ParagraphStyle("tc", parent=cell_bold, alignment=TA_CENTER)),
        Paragraph(f"<b>{_fmt(total_sales_all)}</b>",
                  ParagraphStyle("tt", parent=cell_money)),
        Paragraph("<b>100%</b>",
                  ParagraphStyle("tp", parent=cell_money)),
    ])

    ss_table = Table(ss_rows, colWidths=[
        doc.width * 0.30, doc.width * 0.20, doc.width * 0.30, doc.width * 0.20
    ])
    ss_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#e2e8f0")),
        ("BACKGROUND", (0, -1), (-1, -1), HexColor("#dbeafe")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [white, HexColor("#f8fafc")]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEABOVE", (0, -1), (-1, -1), 1, ACCENT_BLUE),
    ]))
    elements.append(ss_table)
    elements.append(Spacer(1, 4 * mm))

    # ══════════════════════════════════════════════════════════════════
    #  SECTION 4 — FINANCIAL BREAKDOWN
    # ══════════════════════════════════════════════════════════════════
    fin = shift_data.get("financials", {})
    elements.append(Paragraph("④ FINANCIAL BREAKDOWN", section_style))

    fin_rows = [
        [Paragraph("<b>Concept</b>", cell_bold),
         Paragraph("<b>Amount</b>", ParagraphStyle("h", parent=cell_bold, alignment=TA_RIGHT))],
        [Paragraph("Gross Subtotal (before tax/tip)", cell_normal),
         Paragraph(_fmt(fin.get("gross_subtotal", 0)), cell_right)],
        [Paragraph("ITBIS Tax (18%)", cell_normal),
         Paragraph(_fmt(fin.get("itbis", 0)), cell_right)],
        [Paragraph("Legal Tip (10%)", cell_normal),
         Paragraph(_fmt(fin.get("legal_tip", 0)), cell_right)],
        [Paragraph("Extra Tips (Voluntary)", cell_normal),
         Paragraph(_fmt(fin.get("extra_tip", 0)), cell_right)],
    ]
    fin_rows.append([
        Paragraph("<b>NET TOTAL REVENUE</b>", cell_bold),
        Paragraph(f'<b>{_fmt(fin.get("net_total", 0))}</b>',
                  ParagraphStyle("nt", parent=cell_money, textColor=ACCENT_BLUE)),
    ])

    fin_table = Table(fin_rows, colWidths=[doc.width * 0.60, doc.width * 0.40])
    fin_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#e2e8f0")),
        ("BACKGROUND", (0, -1), (-1, -1), HexColor("#eff6ff")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [white, HexColor("#f8fafc")]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEABOVE", (0, -1), (-1, -1), 1, ACCENT_BLUE),
    ]))
    elements.append(fin_table)
    elements.append(Spacer(1, 4 * mm))

    # ══════════════════════════════════════════════════════════════════
    #  SECTION 5 — DETAILED TRANSACTIONS
    # ══════════════════════════════════════════════════════════════════
    txns = shift_data.get("transactions", [])
    elements.append(Paragraph(
        f"⑤ DETAILED TRANSACTIONS ({len(txns)} orders)",
        section_style
    ))

    if txns:
        txn_rows = [
            [Paragraph("<b>#</b>", ParagraphStyle("h", parent=cell_bold, alignment=TA_CENTER)),
             Paragraph("<b>Time</b>", cell_bold),
             Paragraph("<b>Invoice ID</b>", cell_bold),
             Paragraph("<b>Items</b>", cell_bold),
             Paragraph("<b>Payment</b>", ParagraphStyle("h", parent=cell_bold, alignment=TA_CENTER)),
             Paragraph("<b>Total</b>", ParagraphStyle("h", parent=cell_bold, alignment=TA_RIGHT))],
        ]
        for idx, tx in enumerate(txns, 1):
            invoice_id = str(tx.get("invoice_id", "—"))
            # Truncate UUID for readability — show first 8 + last 4
            if len(invoice_id) > 16:
                display_id = invoice_id[:8] + "..." + invoice_id[-4:]
            else:
                display_id = invoice_id

            items_str = str(tx.get("items_summary", "—"))
            # Wrap long item lists
            if len(items_str) > 40:
                items_str = items_str[:40] + "…"

            txn_rows.append([
                Paragraph(str(idx),
                          ParagraphStyle("n", parent=cell_normal, alignment=TA_CENTER)),
                Paragraph(str(tx.get("time", "—")), cell_normal),
                Paragraph(display_id,
                          ParagraphStyle("id", parent=cell_normal, fontName="Courier", fontSize=7)),
                Paragraph(items_str, cell_normal),
                Paragraph(str(tx.get("payment_method", "—")),
                          ParagraphStyle("pm", parent=cell_normal, alignment=TA_CENTER)),
                Paragraph(_fmt(tx.get("total", 0)), cell_right),
            ])

        col_widths = [
            doc.width * 0.05,   # #
            doc.width * 0.12,   # Time
            doc.width * 0.18,   # Invoice ID
            doc.width * 0.33,   # Items
            doc.width * 0.14,   # Payment
            doc.width * 0.18,   # Total
        ]
        txn_table = Table(txn_rows, colWidths=col_widths, repeatRows=1)
        txn_style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#f8fafc")]),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_LINE),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        txn_table.setStyle(TableStyle(txn_style_cmds))
        elements.append(txn_table)
    else:
        elements.append(Paragraph(
            '<font color="#94a3b8"><i>No transactions recorded during this shift.</i></font>',
            ParagraphStyle("empty", fontName="Helvetica-Oblique", fontSize=10,
                           textColor=TEXT_MUTED, alignment=TA_CENTER, spaceBefore=10)
        ))

    elements.append(Spacer(1, 6 * mm))

    # ══════════════════════════════════════════════════════════════════
    #  FOOTER — SIGNATURES
    # ══════════════════════════════════════════════════════════════════
    elements.append(HRFlowable(
        width="100%", thickness=0.5, color=BORDER_LINE,
        spaceBefore=6, spaceAfter=10
    ))

    sig_rows = [[
        Paragraph("_________________________<br/><b>Cashier Signature</b>",
                  ParagraphStyle("sig", fontName="Helvetica", fontSize=9,
                                 textColor=HexColor("#64748b"), alignment=TA_CENTER, leading=14)),
        Paragraph("_________________________<br/><b>Manager Signature</b>",
                  ParagraphStyle("sig2", fontName="Helvetica", fontSize=9,
                                 textColor=HexColor("#64748b"), alignment=TA_CENTER, leading=14)),
    ]]
    sig_table = Table(sig_rows, colWidths=[doc.width * 0.50, doc.width * 0.50])
    sig_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 20),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(sig_table)

    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph(
        f'<font color="#94a3b8" size="7">'
        f'Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  •  '
        f'System: NOCTURNAL BAR POS v1.0  •  Terminal: {si.get("terminal", "POS-01")}'
        f'</font>',
        ParagraphStyle("ts", alignment=TA_CENTER, leading=10)
    ))

    # ── Build PDF ──────────────────────────────────────────────────────
    doc.build(elements, canvasmaker=_NumberedCanvas)
    return filename
