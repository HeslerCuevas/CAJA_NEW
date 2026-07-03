import time
import datetime
from utils.timezone import get_local_now

import types
from decimal import Decimal

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QStackedWidget,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QListWidget, QListWidgetItem, QInputDialog, QComboBox,
    QFrame, QScrollArea, QGridLayout, QSizePolicy,
    QDialog, QDialogButtonBox, QButtonGroup, QAbstractItemView,
    QSpinBox, QTextEdit, QCheckBox, QSplitter, QApplication,
    QScrollBar
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, Slot, QObject, QSize
from PySide6.QtGui import QColor, QBrush, QFont, QPalette, QCursor
from services.pos_service import POSService
from services.sync_service import SyncService
from utils.money import money, rich_money

# ─── Obsidian & Ember Design Tokens ──────────────────────────────────────────
CLR_BG           = "#10141A"
CLR_SURFACE      = "#1A1F26"
CLR_SURFACE_HIGH = "#262A31"
CLR_SURFACE_TOP  = "#353940"
CLR_BG_DEEP      = "#0A0E14"

CLR_EMBER        = "#FF6B00"
CLR_EMBER_DIM    = "rgba(255,107,0,0.15)"
CLR_CHAMPAGNE    = "#E2B49A"
CLR_SUCCESS      = "#00E676"
CLR_ERROR        = "#FF4C4C"
CLR_ERROR_BG     = "#93000A"

CLR_TEXT         = "#DFE2EB"
CLR_TEXT_MID     = "#94A3B8"
CLR_TEXT_DIM     = "#64748B"

CLR_BORDER       = "rgba(255,255,255,0.08)"
CLR_BORDER_MID   = "rgba(255,255,255,0.15)"

# ─── Master Stylesheet ────────────────────────────────────────────────────────
STYLESHEET = f"""
/* ── Root backgrounds ── */
QMainWindow {{
    background-color: {CLR_BG};
}}
QDialog {{
    background-color: {CLR_BG};
}}
/* Page-level full-window widget */
QWidget#PageBg {{
    background-color: {CLR_BG};
}}
/* All other plain QWidgets stay transparent so they don't paint over parents */
QWidget {{
    color: {CLR_TEXT};
    font-family: 'Manrope', 'Segoe UI', sans-serif;
    font-size: 13px;
}}


/* ── Labels ── */
QLabel {{
    color: {CLR_TEXT};
    background: transparent;
}}
QLabel#LblTitle {{
    color: {CLR_EMBER};
    font-family: 'Epilogue', 'Segoe UI Black', 'Segoe UI', sans-serif;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 1px;
}}
QLabel#LblSubtitle {{
    color: {CLR_CHAMPAGNE};
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
}}
QLabel#LblTotal {{
    color: {CLR_EMBER};
    font-family: 'Epilogue', 'Segoe UI Black', 'Segoe UI', sans-serif;
    font-size: 36px;
    font-weight: 900;
}}
QLabel#LblMeta {{
    color: {CLR_TEXT_MID};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
}}
QLabel#LblFund   {{ color: {CLR_TEXT_MID}; font-weight: 700; }}
QLabel#LblSales  {{ color: {CLR_CHAMPAGNE}; font-weight: 700; }}
QLabel#LblExpect {{ color: {CLR_EMBER}; font-weight: 700; }}
QLabel#LblHHActive {{
    color: {CLR_EMBER};
    font-weight: 800;
    font-size: 12px;
    padding: 4px 10px;
    border: 1px solid {CLR_EMBER};
    border-radius: 12px;
    background: rgba(255,107,0,0.1);
}}

/* ── Line Edits ── */
QLineEdit {{
    background-color: {CLR_SURFACE};
    color: {CLR_TEXT};
    border: 1px solid {CLR_BORDER};
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 14px;
    selection-background-color: {CLR_EMBER};
    selection-color: {CLR_BG};
}}
QLineEdit:focus {{
    border: 1px solid {CLR_EMBER};
    background-color: #1C2026;
}}
QLineEdit:disabled {{
    background-color: {CLR_BG_DEEP};
    color: {CLR_TEXT_DIM};
    border-color: rgba(255,255,255,0.04);
}}
QLineEdit#SearchInput {{
    font-size: 14px;
    padding: 12px 16px 12px 40px;
    border-radius: 12px;
}}
QLineEdit#CashInput {{
    font-size: 20px;
    font-weight: 700;
    text-align: center;
    padding: 14px;
    border-radius: 12px;
}}

/* ── ComboBox ── */
QComboBox {{
    background-color: {CLR_SURFACE};
    color: {CLR_TEXT};
    border: 1px solid {CLR_BORDER};
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 13px;
    font-weight: 600;
}}
QComboBox:focus {{ border-color: {CLR_EMBER}; }}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    image: none;
    width: 0;
}}
QComboBox QAbstractItemView {{
    background-color: {CLR_SURFACE};
    color: {CLR_TEXT};
    border: 1px solid {CLR_BORDER_MID};
    border-radius: 8px;
    selection-background-color: {CLR_EMBER};
    selection-color: {CLR_BG};
    padding: 4px;
    outline: none;
}}

/* ── Push Buttons (base) ── */
QPushButton {{
    background-color: {CLR_SURFACE_HIGH};
    color: {CLR_TEXT};
    border: 1px solid {CLR_BORDER};
    border-radius: 10px;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: 700;
    font-family: 'Epilogue', 'Segoe UI', sans-serif;
}}
QPushButton:hover {{
    background-color: {CLR_SURFACE_TOP};
    border-color: {CLR_BORDER_MID};
}}
QPushButton:pressed {{ background-color: {CLR_BG_DEEP}; }}
QPushButton:disabled {{
    background-color: {CLR_SURFACE};
    color: {CLR_TEXT_DIM};
    border-color: rgba(255,255,255,0.04);
}}

/* Primary / Success (Ember orange) */
QPushButton#BtnSuccess, QPushButton#BtnPrimary {{
    background-color: {CLR_EMBER};
    color: {CLR_BG};
    border: none;
    font-size: 15px;
    font-weight: 900;
    border-radius: 12px;
}}
QPushButton#BtnSuccess:hover, QPushButton#BtnPrimary:hover {{ background-color: #E56000; }}
QPushButton#BtnSuccess:disabled, QPushButton#BtnPrimary:disabled {{
    background-color: {CLR_SURFACE_HIGH};
    color: {CLR_TEXT_DIM};
}}

/* Danger */
QPushButton#BtnDanger {{
    background-color: {CLR_ERROR_BG};
    color: #FFDAD6;
    border: 1px solid rgba(255,76,76,0.5);
    font-size: 14px;
}}
QPushButton#BtnDanger:hover {{ background-color: #B0000D; }}

/* Champagne ghost (tables, change cashier) */
QPushButton#BtnChampagne, QPushButton#BtnMesas {{
    background-color: transparent;
    color: {CLR_CHAMPAGNE};
    border: 1px solid rgba(226,180,154,0.5);
    font-size: 13px;
}}
QPushButton#BtnChampagne:hover, QPushButton#BtnMesas:hover {{
    background-color: rgba(226,180,154,0.08);
    border-color: {CLR_CHAMPAGNE};
}}

/* Hold order */
QPushButton#BtnHold {{
    background-color: transparent;
    color: {CLR_CHAMPAGNE};
    border: 1px solid rgba(226,180,154,0.35);
    font-size: 12px;
    padding: 8px 14px;
}}
QPushButton#BtnHold:hover {{
    background-color: rgba(226,180,154,0.08);
    border-color: {CLR_CHAMPAGNE};
}}

/* Split Bill button */
QPushButton#BtnSplit {{
    background-color: transparent;
    color: {CLR_EMBER};
    border: 1px solid rgba(255,107,0,0.5);
    font-size: 13px;
}}
QPushButton#BtnSplit:hover {{ background-color: rgba(255,107,0,0.08); border-color: {CLR_EMBER}; }}

/* Category chip — inactive */
QPushButton#BtnCat {{
    background-color: {CLR_SURFACE};
    color: {CLR_TEXT_MID};
    border: 1px solid {CLR_BORDER};
    border-radius: 20px;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 600;
    min-width: 60px;
}}
QPushButton#BtnCat:hover {{ border-color: {CLR_EMBER}; color: {CLR_EMBER}; }}

QPushButton#BtnCatPromo {{
    background-color: rgba(0,180,160,0.10);
    color: {CLR_CHAMPAGNE};
    border: 1px solid rgba(0,180,160,0.42);
    border-radius: 20px;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 700;
    min-width: 60px;
}}
QPushButton#BtnCatPromo:hover {{
    background-color: rgba(0,180,160,0.16);
    border-color: #00B4A0;
    color: {CLR_TEXT};
}}

/* Category chip — active */
QPushButton#BtnCatActive {{
    background-color: {CLR_CHAMPAGNE};
    color: {CLR_BG};
    border: 1px solid {CLR_CHAMPAGNE};
    border-radius: 20px;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 700;
    min-width: 60px;
}}

QPushButton#BtnCatPromoActive {{
    background-color: rgba(226,180,154,0.92);
    color: {CLR_BG};
    border: 1px solid rgba(0,180,160,0.55);
    border-radius: 20px;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 800;
    min-width: 60px;
}}

/* Happy Hour chip — inactive */
QPushButton#BtnHH {{
    background-color: transparent;
    color: {CLR_CHAMPAGNE};
    border: 1px solid rgba(226,180,154,0.35);
    border-radius: 20px;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton#BtnHH:hover {{ border-color: {CLR_CHAMPAGNE}; }}

/* Happy Hour chip — active */
QPushButton#BtnHHActive {{
    background-color: {CLR_EMBER};
    color: {CLR_BG};
    border: none;
    border-radius: 20px;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 800;
}}

/* Product card — both variants share identical sizing so the grid stays uniform */
QPushButton#BtnProduct {{
    background-color: {CLR_SURFACE};
    color: {CLR_TEXT};
    border: 1px solid {CLR_BORDER};
    border-radius: 16px;
    padding: 12px 10px;
    font-size: 12px;
    font-family: 'Epilogue', 'Segoe UI', sans-serif;
    text-align: center;
    min-height: 110px;
    max-height: 110px;
}}
QPushButton#BtnProduct:hover {{
    background-color: {CLR_SURFACE_HIGH};
    border-color: rgba(255,107,0,0.4);
    color: {CLR_EMBER};
}}
QPushButton#BtnProduct:pressed {{ background-color: rgba(255,107,0,0.12); }}

QPushButton#BtnProductPromo {{
    background-color: rgba(0,180,160,0.12);
    color: #00B4A0;
    border: 1px solid rgba(0,180,160,0.4);
    border-radius: 16px;
    padding: 12px 10px;
    font-size: 12px;
    font-family: 'Epilogue', 'Segoe UI', sans-serif;
    text-align: center;
    min-height: 110px;
    max-height: 110px;
}}
QPushButton#BtnProductPromo:hover {{
    background-color: rgba(0,180,160,0.22);
    border-color: #00B4A0;
}}
QPushButton#BtnProductPromo:pressed {{ background-color: rgba(0,180,160,0.08); }}

/* Notes button (inactive) */
QPushButton#BtnNotes {{
    background-color: rgba(255,255,255,0.04);
    color: #94A3B8;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 700;
}}
QPushButton#BtnNotes:hover {{ 
    background-color: rgba(255,255,255,0.08); 
    color: #DFE2EB;
    border-color: rgba(255,255,255,0.2); 
}}

/* Notes button (has notes) */
QPushButton#BtnNotesActive {{
    background-color: {CLR_EMBER};
    color: {CLR_BG};
    border: none;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 800;
}}
QPushButton#BtnNotesActive:hover {{ background-color: #E56000; }}

/* Modifier chips in dialog */
QPushButton#BtnModOn {{
    background-color: {CLR_EMBER};
    color: {CLR_BG};
    border: none;
    border-radius: 16px;
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 700;
}}
QPushButton#BtnModOff {{
    background-color: {CLR_SURFACE};
    color: {CLR_TEXT_MID};
    border: 1px solid {CLR_BORDER};
    border-radius: 16px;
    padding: 7px 14px;
    font-size: 12px;
}}
QPushButton#BtnModOff:hover {{ border-color: {CLR_EMBER}; color: {CLR_TEXT}; }}

/* Guest card in split bill (equal/custom) */
QPushButton#BtnGuestCard {{
    background-color: {CLR_SURFACE};
    color: {CLR_TEXT};
    border: 1px solid {CLR_BORDER};
    border-radius: 14px;
    padding: 16px;
    font-size: 15px;
    text-align: center;
    min-height: 90px;
}}
QPushButton#BtnGuestCard:hover {{ border-color: rgba(255,107,0,0.4); }}

/* ── Tables ── */
QTableWidget {{
    background-color: {CLR_SURFACE};
    color: {CLR_TEXT};
    gridline-color: rgba(255,255,255,0.04);
    border: none;
    outline: none;
    font-size: 13px;
    alternate-background-color: rgba(38,42,49,0.5);
    selection-background-color: transparent;
    selection-color: {CLR_TEXT};
    border-radius: 0px;
}}
QTableWidget::item {{
    padding: 10px 8px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}}
QTableWidget::item:selected {{ background-color: transparent; color: {CLR_EMBER}; }}
QHeaderView::section {{
    background-color: {CLR_BG_DEEP};
    color: {CLR_TEXT_MID};
    padding: 10px 8px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 1.5px;
    border: none;
    border-bottom: 1px solid {CLR_BORDER};
    border-right: 1px solid {CLR_BORDER};
}}
QHeaderView {{ background-color: {CLR_BG_DEEP}; border: none; }}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background: transparent;
    width: 5px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {CLR_SURFACE_TOP};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: {CLR_EMBER}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 5px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {CLR_SURFACE_TOP};
    border-radius: 3px;
    min-width: 20px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Frames ── */
QFrame#CardFrame {{
    background-color: {CLR_SURFACE};
    border: 1px solid {CLR_BORDER};
    border-radius: 16px;
}}
QFrame#HeaderFrame {{
    background-color: {CLR_SURFACE};
    border: none;
    border-bottom: 1px solid {CLR_BORDER};
    border-radius: 0px;
}}
QFrame#DividerH {{
    background-color: {CLR_BORDER};
    max-height: 1px;
    border: none;
}}
QFrame#DividerV {{
    background-color: {CLR_BORDER};
    max-width: 1px;
    border: none;
}}

/* ── List Widget ── */
QListWidget {{
    background-color: {CLR_SURFACE};
    color: {CLR_TEXT};
    border: none;
    font-size: 13px;
}}
QListWidget::item {{ padding: 12px 10px; border-bottom: 1px solid rgba(255,255,255,0.04); }}
QListWidget::item:hover {{ background-color: rgba(255,255,255,0.03); }}
QListWidget::item:selected {{ background-color: rgba(255,107,0,0.15); color: {CLR_EMBER}; }}

/* ── Input Dialog & Message Box ── */
QInputDialog, QMessageBox {{ background-color: {CLR_BG}; }}
QInputDialog QLabel, QMessageBox QLabel {{ color: {CLR_TEXT}; }}
QInputDialog QLineEdit {{ background-color: {CLR_SURFACE}; color: {CLR_TEXT}; border: 1px solid {CLR_BORDER}; border-radius: 8px; padding: 8px; }}

/* ── Scroll Area ── */
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}

/* ── Text Edit ── */
QTextEdit {{
    background-color: {CLR_SURFACE};
    color: {CLR_TEXT};
    border: 1px solid {CLR_BORDER};
    border-radius: 10px;
    padding: 10px;
    font-size: 13px;
}}
QTextEdit:focus {{ border-color: {CLR_EMBER}; }}

/* ── Spin Box ── */
QSpinBox {{
    background-color: {CLR_SURFACE};
    color: {CLR_TEXT};
    border: 1px solid {CLR_BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 16px;
    font-weight: 700;
}}
QSpinBox:focus {{ border-color: {CLR_EMBER}; }}
QSpinBox::up-button, QSpinBox::down-button {{ width: 0; }}

/* ── CheckBox ── */
QCheckBox {{ color: {CLR_TEXT}; spacing: 8px; }}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {CLR_BORDER_MID};
    border-radius: 5px;
    background: {CLR_SURFACE};
}}
QCheckBox::indicator:checked {{ background: {CLR_EMBER}; border-color: {CLR_EMBER}; }}

/* ── SplitBillDialog named frames ── */
QFrame#SplitHdr {{
    background-color: {CLR_SURFACE};
    border: none;
    border-bottom: 1px solid {CLR_BORDER};
}}
QFrame#SplitSummary {{
    background-color: {CLR_SURFACE_HIGH};
    border: 1px solid {CLR_BORDER};
    border-radius: 12px;
}}
QFrame#SplitTabs {{
    background-color: {CLR_SURFACE_HIGH};
    border: 1px solid {CLR_BORDER};
    border-radius: 10px;
}}
QFrame#SplitFooter {{
    background-color: {CLR_BG_DEEP};
    border: none;
    border-top: 1px solid {CLR_BORDER};
}}

/* ── By Item left panel ── */
QFrame#BiLeft {{
    background-color: {CLR_SURFACE};
    border: none;
    border-right: 1px solid {CLR_BORDER};
}}

/* ── Close (✕) button ── */
QPushButton#BtnClose {{
    background: transparent;
    color: {CLR_TEXT_MID};
    border: none;
    font-size: 16px;
    font-weight: 600;
}}
QPushButton#BtnClose:hover {{
    color: {CLR_ERROR};
}}

/* ── Utility labels ── */
QLabel#LblBold {{
    color: {CLR_TEXT};
    font-weight: 700;
    font-size: 14px;
}}
QLabel#LblSplitTotal {{
    color: {CLR_EMBER};
    font-size: 24px;
    font-weight: 900;
    font-family: 'Epilogue', 'Segoe UI Black', 'Segoe UI', sans-serif;
}}
QLabel#LblCuRemaining {{
    color: {CLR_EMBER};
    font-size: 15px;
    font-weight: 800;
}}

/* ── Extra label classes ── */
QLabel#LblChampagne {{
    color: {CLR_CHAMPAGNE};
    font-size: 15px;
    font-weight: 700;
}}
QLabel#LblEmptyState {{
    color: {CLR_TEXT_MID};
    font-size: 15px;
    padding: 40px;
}}

/* ── Hold Order row ── */
QFrame#HoldRow {{
    background-color: {CLR_SURFACE_HIGH};
    border: 1px solid {CLR_BORDER};
    border-radius: 12px;
}}

/* ── Promotions button ── */
QPushButton#BtnPromo {{
    background-color: rgba(0,180,160,0.12);
    color: #00B4A0;
    border: 1px solid rgba(0,180,160,0.4);
    border-radius: 10px;
    font-size: 13px;
    font-weight: 800;
    padding: 8px 14px;
    letter-spacing: 0.5px;
}}
QPushButton#BtnPromo:hover {{
    background-color: rgba(0,180,160,0.22);
    border-color: #00B4A0;
}}
QPushButton#BtnPromoActive {{
    background-color: #00B4A0;
    color: {CLR_BG};
    border: none;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 900;
    padding: 8px 14px;
}}
QPushButton#BtnPromoActive:hover {{
    background-color: #009A8A;
}}

/* ── Discount badge chip ── */
QFrame#DiscountBadge {{
    background-color: rgba(0,180,160,0.10);
    border: 1px solid rgba(0,180,160,0.35);
    border-radius: 10px;
    padding: 0;
}}
QLabel#LblDiscountBadge {{
    color: #00B4A0;
    font-size: 12px;
    font-weight: 700;
    background: transparent;
    padding: 6px 10px;
}}
QPushButton#BtnBadgeRemove {{
    background: transparent;
    border: none;
    color: rgba(0,180,160,0.6);
    font-size: 14px;
    font-weight: 800;
    padding: 0 4px;
    min-width: 20px;
    max-width: 20px;
}}
QPushButton#BtnBadgeRemove:hover {{ color: #FF6B00; }}

/* ── Promo dialog section frames ── */
QFrame#PromoPanelSection {{
    background-color: {CLR_SURFACE_HIGH};
    border: 1px solid {CLR_BORDER};
    border-radius: 12px;
}}
QFrame#SupervisorPanel {{
    background-color: rgba(255,107,0,0.07);
    border: 1px solid rgba(255,107,0,0.3);
    border-radius: 12px;
}}
"""


# ─── Helper: create a styled card frame ──────────────────────────────────────
def _card(parent=None, radius=16, pad=0) -> QFrame:
    f = QFrame(parent)
    f.setObjectName("CardFrame")
    if pad:
        f.setContentsMargins(pad, pad, pad, pad)
    return f


def _hdiv() -> QFrame:
    d = QFrame()
    d.setObjectName("DividerH")
    d.setFixedHeight(1)
    return d


def _vdiv() -> QFrame:
    d = QFrame()
    d.setObjectName("DividerV")
    d.setFixedWidth(1)
    return d


def _lbl(text, obj_name=None, align=Qt.AlignLeft) -> QLabel:
    l = QLabel(text)
    if obj_name:
        l.setObjectName(obj_name)
    l.setAlignment(align)
    return l


# ─── Worker classes ───────────────────────────────────────────────────────────
class SyncWorker(QObject):
    """Persistent worker that lives on a single background thread for the app lifetime."""
    finished = Signal(bool, str, list, list, bool, float)
    request = Signal(bool, bool)

    def __init__(self, sincronizador):
        super().__init__()
        self.sincronizador = sincronizador
        self._busy = False

    def on_request(self, fetch_pedidos, full_sync):
        if self._busy:
            return
        self._busy = True
        categorias = []
        pedidos = []
        sync_ok, sync_msg = True, ""
        hh_active, hh_discount = False, 0.0
        try:
            sync_ok, sync_msg = self.sincronizador.sincronizar_ventas_pendientes()
            hh_active, hh_discount = self.sincronizador.sincronizar_happy_hour()
            categorias = self.sincronizador.sincronizar_categorias() or []
            self.sincronizador.sincronizar_productos()
            self.sincronizador.sincronizar_promociones()
            
            if full_sync:
                self.sincronizador.sincronizar_empleados()
                self.sincronizador.sincronizar_auditorias_promocion()
                self.sincronizador.sincronizar_sesiones_supervisor()
            if fetch_pedidos:
                pedidos = self.sincronizador.obtener_cuentas_abiertas() or []
        except Exception as e:
            sync_ok, sync_msg = False, str(e)
        self._busy = False
        self.finished.emit(sync_ok, sync_msg, categorias, pedidos, hh_active, hh_discount)


class StockWorker(QObject):
    finished = Signal(object)
    request = Signal(list)

    def __init__(self, sincronizador):
        super().__init__()
        self.sincronizador = sincronizador
        self._busy = False
        self._skip_persist = False

    def on_request(self, product_ids):
        print(f"[StockWorker] on_request received {len(product_ids)} ids, _busy={self._busy}", flush=True)
        if self._busy:
            return
        self._busy = True
        stock_data = {}
        try:
            for pid in product_ids:
                if self._skip_persist:
                    print("[StockWorker] ABORT — cooldown activated mid-fetch", flush=True)
                    stock_data = {}
                    break
                stock = self.sincronizador.obtener_stock_producto(pid)
                if stock != -1:
                    stock_data[pid] = stock

            if stock_data and not self._skip_persist:
                from db.connection import SessionLocal
                from models.entities import ProductoLocal, FacturaLocal, DetalleFactura
                from sqlalchemy import func
                db = SessionLocal()
                try:
                    for pid, stock_val in stock_data.items():
                        unsynced_qty = db.query(func.sum(DetalleFactura.cantidad))\
                                         .join(FacturaLocal, DetalleFactura.id_factura == FacturaLocal.id_factura)\
                                         .filter(DetalleFactura.id_producto == pid, FacturaLocal.sincronizado == False)\
                                         .scalar() or 0
                        effective_stock = max(0, stock_val - unsynced_qty)
                        
                        p = db.query(ProductoLocal).filter_by(id_producto=pid).first()
                        if p:
                            p.stock_local = effective_stock
                            stock_data[pid] = effective_stock
                    db.commit()
                    print(f"[StockWorker] OK - Persisted {len(stock_data)} stock values to DB", flush=True)
                except Exception as db_err:
                    db.rollback()
                    print(f"[StockWorker] DB persist error: {db_err}", flush=True)
                finally:
                    db.close()
            elif self._skip_persist:
                print("[StockWorker] SKIPPED DB persist — post-sale cooldown active", flush=True)
                stock_data = {}
        except Exception as e:
            print(f"[StockWorker] Unexpected error: {e}", flush=True)
        finally:
            self._busy = False
        self.finished.emit(stock_data)


class _FetchOrdersWorker(QObject):
    finished = Signal(list)
    request = Signal()

    def __init__(self, sincronizador):
        super().__init__()
        self.sincronizador = sincronizador
        self._busy = False

    def run(self):
        if self._busy:
            return
        self._busy = True
        try:
            pedidos = self.sincronizador.obtener_cuentas_abiertas() or []
        except Exception as e:
            print(f"Fetch orders error: {e}", flush=True)
            pedidos = []
        self._busy = False
        self.finished.emit(pedidos)


# ─── Custom Message Box ───────────────────────────────────────────────────────
class AppMessageBox(QDialog):
    @classmethod
    def show_msg(cls, parent, title, text, msg_type="INFO", buttons_type="OK"):
        dlg = QDialog(parent)
        dlg.setWindowTitle(title)
        dlg.setFixedWidth(420)
        dlg.setStyleSheet(STYLESHEET)
        dlg.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        root = QVBoxLayout(dlg)
        root.setContentsMargins(0, 0, 0, 0)

        card = _card()
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(32, 24, 32, 24)
        card_l.setSpacing(16)

        hdr = QHBoxLayout()
        title_lbl = _lbl(title.upper(), "LblTitle")
        
        if msg_type == "ERROR":
            title_lbl.setStyleSheet("color:#FF4A4A;font-weight:800;font-size:18px;background:transparent;")
        elif msg_type == "WARNING":
            title_lbl.setStyleSheet("color:#FFC107;font-weight:800;font-size:18px;background:transparent;")
        elif msg_type == "SUCCESS":
            title_lbl.setStyleSheet("color:#00E676;font-weight:800;font-size:18px;background:transparent;")
        else:
            title_lbl.setStyleSheet("color:#FFFFFF;font-weight:800;font-size:18px;background:transparent;")
            
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        card_l.addLayout(hdr)
        card_l.addWidget(_hdiv())

        msg_lbl = _lbl(text)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(f"color:{CLR_TEXT};font-size:15px;line-height:1.4;")
        card_l.addWidget(msg_lbl)
        card_l.addSpacing(8)

        btn_l = QHBoxLayout()
        btn_l.addStretch()

        if buttons_type == "YES_NO" or buttons_type == "YES_NO_CANCEL":
            if buttons_type == "YES_NO_CANCEL":
                btn_cancel = QPushButton("Cancel")
                btn_cancel.setObjectName("BtnChampagne")
                btn_cancel.setFixedWidth(100)
                btn_cancel.clicked.connect(lambda: dlg.done(QMessageBox.Cancel))
                btn_l.addWidget(btn_cancel)

            btn_no = QPushButton("No")
            btn_no.setObjectName("BtnChampagne")
            btn_no.setFixedWidth(100)
            btn_no.clicked.connect(lambda: dlg.done(QMessageBox.No))
            
            btn_yes = QPushButton("Yes")
            btn_yes.setObjectName("BtnSuccess")
            btn_yes.setFixedWidth(100)
            btn_yes.clicked.connect(lambda: dlg.done(QMessageBox.Yes))
            
            btn_l.addWidget(btn_no)
            btn_l.addWidget(btn_yes)
        else:
            btn_ok = QPushButton("OK")
            btn_ok.setObjectName("BtnSuccess")
            btn_ok.setFixedWidth(120)
            btn_ok.clicked.connect(lambda: dlg.done(QMessageBox.Ok))
            btn_l.addWidget(btn_ok)

        card_l.addLayout(btn_l)
        root.addWidget(card)

        # Allow layout to adjust height automatically
        root.setSizeConstraint(QVBoxLayout.SetFixedSize)
        return dlg.exec()

    @classmethod
    def information(cls, parent, title, text):
        cls.show_msg(parent, title, text, "INFO", "OK")

    @classmethod
    def warning(cls, parent, title, text):
        cls.show_msg(parent, title, text, "WARNING", "OK")

    @classmethod
    def critical(cls, parent, title, text):
        cls.show_msg(parent, title, text, "ERROR", "OK")

    @classmethod
    def question(cls, parent, title, text, flags=None):
        if flags and (flags & QMessageBox.Cancel):
            return cls.show_msg(parent, title, text, "[?]", "YES_NO_CANCEL")
        return cls.show_msg(parent, title, text, "[?]", "YES_NO")


# ─── Custom Input Dialog ──────────────────────────────────────────────────────
class AppInputDialog(QDialog):
    @classmethod
    def getText(cls, parent, title, label, placeholder=""):
        dlg = QDialog(parent)
        dlg.setWindowTitle(title)
        dlg.setFixedWidth(420)
        dlg.setStyleSheet(STYLESHEET)
        dlg.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        root = QVBoxLayout(dlg)
        root.setContentsMargins(0, 0, 0, 0)
        card = _card()
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(32, 24, 32, 24)
        card_l.setSpacing(16)

        hdr = QHBoxLayout()
        title_lbl = _lbl(title.upper(), "LblTitle")
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        card_l.addLayout(hdr)
        card_l.addWidget(_hdiv())

        msg_lbl = _lbl(label)
        msg_lbl.setStyleSheet(f"color:{CLR_TEXT};font-size:14px;")
        card_l.addWidget(msg_lbl)

        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setFixedHeight(46)
        card_l.addWidget(inp)
        inp.setFocus()

        btn_l = QHBoxLayout()
        btn_l.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("BtnChampagne")
        btn_cancel.setFixedWidth(100)
        btn_cancel.clicked.connect(dlg.reject)
        
        btn_ok = QPushButton("OK")
        btn_ok.setObjectName("BtnSuccess")
        btn_ok.setFixedWidth(100)
        btn_ok.clicked.connect(dlg.accept)
        inp.returnPressed.connect(dlg.accept)

        btn_l.addWidget(btn_cancel)
        btn_l.addWidget(btn_ok)

        card_l.addSpacing(10)
        card_l.addLayout(btn_l)
        root.addWidget(card)
        root.setSizeConstraint(QVBoxLayout.SetFixedSize)

        if dlg.exec() == QDialog.Accepted:
            return inp.text(), True
        return "", False

    @classmethod
    def getItem(cls, parent, title, label, items):
        dlg = QDialog(parent)
        dlg.setWindowTitle(title)
        dlg.setFixedWidth(420)
        dlg.setStyleSheet(STYLESHEET)
        dlg.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        root = QVBoxLayout(dlg)
        root.setContentsMargins(0, 0, 0, 0)
        card = _card()
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(32, 24, 32, 24)
        card_l.setSpacing(16)

        hdr = QHBoxLayout()
        title_lbl = _lbl(title.upper(), "LblTitle")
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        card_l.addLayout(hdr)
        card_l.addWidget(_hdiv())

        msg_lbl = _lbl(label)
        msg_lbl.setStyleSheet(f"color:{CLR_TEXT};font-size:14px;")
        card_l.addWidget(msg_lbl)

        combo = QComboBox()
        combo.addItems(items)
        combo.setFixedHeight(46)
        card_l.addWidget(combo)

        btn_l = QHBoxLayout()
        btn_l.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("BtnChampagne")
        btn_cancel.setFixedWidth(100)
        btn_cancel.clicked.connect(dlg.reject)
        
        btn_ok = QPushButton("OK")
        btn_ok.setObjectName("BtnSuccess")
        btn_ok.setFixedWidth(100)
        btn_ok.clicked.connect(dlg.accept)

        btn_l.addWidget(btn_cancel)
        btn_l.addWidget(btn_ok)

        card_l.addSpacing(10)
        card_l.addLayout(btn_l)
        root.addWidget(card)
        root.setSizeConstraint(QVBoxLayout.SetFixedSize)

        if dlg.exec() == QDialog.Accepted:
            return combo.currentText(), True
        return "", False


# ─── Verifone Dialog (restyled) ───────────────────────────────────────────────
class VerifoneDialog(QDialog):
    def __init__(self, amount, subtotal_str=None, itbis_str=None,
                 legaltip_str=None, extratip_str=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Card Payment — Processing")
        self.setFixedSize(440, 480)
        self.setStyleSheet(STYLESHEET)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = _card()
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(32, 32, 32, 32)
        card_l.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        icon = _lbl("PAY")
        icon.setStyleSheet("font-size: 28px;")
        title = _lbl("CARD PAYMENT", "LblTitle")
        hdr.addWidget(icon)
        hdr.addWidget(title)
        hdr.addStretch()
        card_l.addLayout(hdr)
        card_l.addWidget(_hdiv())

        card_l.addWidget(_lbl("Please swipe card or insert chip...", "LblMeta",
                              Qt.AlignCenter))
        card_l.addSpacing(8)

        # Breakdown
        if subtotal_str:
            r = QHBoxLayout()
            r.addWidget(_lbl("Subtotal:", "LblMeta"))
            r.addStretch()
            r.addWidget(_lbl(subtotal_str))
            card_l.addLayout(r)
        if itbis_str:
            r = QHBoxLayout()
            r.addWidget(_lbl("ITBIS TAX (18%):", "LblMeta"))
            r.addStretch()
            r.addWidget(_lbl(itbis_str))
            card_l.addLayout(r)
        if legaltip_str:
            r = QHBoxLayout()
            r.addWidget(_lbl("Legal Tip (10%):", "LblMeta"))
            r.addStretch()
            r.addWidget(_lbl(legaltip_str))
            card_l.addLayout(r)

        tip_str = extratip_str if extratip_str else money(0)
        r = QHBoxLayout()
        r.addWidget(_lbl("Extra Tip:", "LblMeta"))
        r.addStretch()
        r.addWidget(_lbl(tip_str))
        card_l.addLayout(r)

        card_l.addWidget(_hdiv())

        total_lbl = _lbl(f"TOTAL DUE:  {amount}", obj_name="LblTotal",
                         align=Qt.AlignCenter)
        total_lbl.setStyleSheet(
            f"color: {CLR_EMBER}; font-size: 28px; font-weight: 900; "
            f"font-family: 'Epilogue','Segoe UI Black','Segoe UI',sans-serif;"
        )
        card_l.addWidget(total_lbl)
        card_l.addSpacing(8)

        self.lbl_status = _lbl("Processing...", align=Qt.AlignCenter)
        self.lbl_status.setStyleSheet(
            f"color: {CLR_CHAMPAGNE}; font-size: 16px; font-weight: 700;"
        )
        card_l.addWidget(self.lbl_status)
        card_l.addStretch()

        root.addWidget(card)

        self.timer_process = QTimer(self)
        self.timer_process.setSingleShot(True)
        self.timer_process.timeout.connect(self._on_success)
        self.timer_process.start(5000)

    def _on_success(self):
        try:
            self.lbl_status.setText("OK  Payment Approved!")
            self.lbl_status.setStyleSheet(
                f"color: {CLR_SUCCESS}; font-size: 16px; font-weight: 700;"
            )
        except RuntimeError:
            return
        self.timer_close = QTimer(self)
        self.timer_close.setSingleShot(True)
        self.timer_close.timeout.connect(self.accept)
        self.timer_close.start(1500)

    def closeEvent(self, event):
        for attr in ('timer_process', 'timer_close'):
            t = getattr(self, attr, None)
            if t and t.isActive():
                t.stop()
        super().closeEvent(event)


# ─── Item Modifier Dialog ─────────────────────────────────────────────────────
class ItemModifierDialog(QDialog):
    """Dialog to add per-item instructions (e.g. 'Sin Hielo', 'Doble Shot')."""

    def __init__(self, product_name, product_id, modifiers,
                 current_notes=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Item Instructions")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(STYLESHEET)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        self.selected = set(current_notes or [])
        self._mod_btns = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = _card()
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(28, 28, 28, 28)
        card_l.setSpacing(14)

        # Header
        hdr = QHBoxLayout()
        title = _lbl("ITEM INSTRUCTIONS", "LblTitle")
        close_btn = QPushButton("✕")
        close_btn.setObjectName("BtnClose")
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(self.reject)
        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(close_btn)
        card_l.addLayout(hdr)

        prod_lbl = _lbl(product_name, "LblChampagne")
        card_l.addWidget(prod_lbl)
        card_l.addWidget(_hdiv())

        # Modifier chips
        chips_lbl = _lbl("SELECT MODIFIERS", "LblMeta")
        card_l.addWidget(chips_lbl)

        chips_scroll = QScrollArea()
        chips_scroll.setWidgetResizable(True)
        chips_scroll.setFixedHeight(160)
        chips_scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        chips_w = QWidget()
        chips_w.setStyleSheet("background:transparent;")
        chips_grid = QGridLayout(chips_w)
        chips_grid.setSpacing(8)
        chips_grid.setContentsMargins(0, 0, 0, 0)

        col = 0
        row = 0
        MAX_COLS = 3
        for mod in modifiers:
            btn = QPushButton(mod)
            is_on = mod in self.selected
            self._apply_mod_style(btn, is_on)
            btn.setCheckable(False)
            btn.clicked.connect(lambda checked, m=mod: self._toggle(m))
            self._mod_btns[mod] = btn
            chips_grid.addWidget(btn, row, col)
            col += 1
            if col >= MAX_COLS:
                col = 0
                row += 1

        chips_scroll.setWidget(chips_w)
        card_l.addWidget(chips_scroll)

        # Free text
        notes_lbl = _lbl("ADDITIONAL NOTES", "LblMeta")
        card_l.addWidget(notes_lbl)
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText(
            "e.g.  extra salt on the rim, serve cold..."
        )
        # Pre-fill with any non-modifier notes
        free = [n for n in (current_notes or []) if n not in modifiers]
        if free:
            self.notes_input.setText(", ".join(free))
        card_l.addWidget(self.notes_input)

        card_l.addStretch()
        card_l.addWidget(_hdiv())

        # Footer
        foot = QHBoxLayout()
        no_mod_btn = QPushButton("No Modifications")
        no_mod_btn.setObjectName("BtnChampagne")
        no_mod_btn.clicked.connect(self._clear_and_confirm)
        confirm_btn = QPushButton("Confirm")
        confirm_btn.setObjectName("BtnSuccess")
        confirm_btn.clicked.connect(self.accept)
        foot.addWidget(no_mod_btn)
        foot.addStretch()
        foot.addWidget(confirm_btn)
        card_l.addLayout(foot)

        root.addWidget(card)

    def _apply_mod_style(self, btn, is_on):
        if is_on:
            btn.setStyleSheet(
                f"background-color:{CLR_EMBER};color:{CLR_BG};"
                f"border:none;border-radius:18px;padding:12px 18px;"
                f"font-size:14px;font-weight:800;"
            )
        else:
            btn.setStyleSheet(
                f"background-color:transparent;color:{CLR_TEXT};"
                f"border:1px solid {CLR_BORDER};border-radius:18px;padding:12px 18px;"
                f"font-size:14px;font-weight:600;"
            )

    def _toggle(self, mod):
        if mod in self.selected:
            self.selected.discard(mod)
            self._apply_mod_style(self._mod_btns[mod], False)
        else:
            self.selected.add(mod)
            self._apply_mod_style(self._mod_btns[mod], True)

    def _clear_and_confirm(self):
        self.selected.clear()
        self.notes_input.clear()
        self.accept()

    def get_notes(self):
        result = list(self.selected)
        free = self.notes_input.text().strip()
        if free:
            result.append(free)
        return result


# ─── Held Orders Dialog ───────────────────────────────────────────────────────
class HeldOrdersDialog(QDialog):
    """Shows all held (paused) orders and lets the cashier resume one."""
    order_resumed = Signal(int)  # emits the index of the held order to resume

    def __init__(self, held_orders, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Held Orders")
        self.setMinimumSize(780, 420)
        self.setStyleSheet(STYLESHEET)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self._held = held_orders

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = _card()
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(28, 28, 28, 28)
        card_l.setSpacing(14)

        # Header
        hdr = QHBoxLayout()
        title = _lbl("HELD ORDERS", "LblTitle")
        close_btn = QPushButton("✕")
        close_btn.setObjectName("BtnClose")
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(self.reject)
        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(close_btn)
        card_l.addLayout(hdr)
        card_l.addWidget(_hdiv())

        if not held_orders:
            empty = _lbl("No held orders at this time.", "LblEmptyState", align=Qt.AlignCenter)
            card_l.addWidget(empty)
        else:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
            container = QWidget()
            container.setStyleSheet("background:transparent;")
            vbox = QVBoxLayout(container)
            vbox.setSpacing(8)
            vbox.setContentsMargins(0, 0, 0, 0)

            for idx, order in enumerate(held_orders):
                row_frame = QFrame()
                row_frame.setObjectName("HoldRow")
                row_l = QHBoxLayout(row_frame)
                row_l.setContentsMargins(16, 12, 16, 12)

                ts = order.get('timestamp', '')
                cliente = order.get('cliente', '—') or '—'
                n_items = sum(int(float(i.get('cant', 1))) for i in order.get('carrito', []))
                sub = sum(
                    float(i.get('precio', 0)) * i.get('cant', 1)
                    for i in order.get('carrito', [])
                )

                info_l = QVBoxLayout()
                info_l.setSpacing(2)
                name_lbl = _lbl(f"Order #{idx + 1}  —  {cliente}")
                name_lbl.setStyleSheet(f"color:{CLR_TEXT};font-weight:700;font-size:14px;")
                meta_lbl = _lbl(f"{n_items} item(s)  •  Subtotal: {money(sub)}  •  {ts}", "LblMeta")
                info_l.addWidget(name_lbl)
                info_l.addWidget(meta_lbl)
                row_l.addLayout(info_l)
                row_l.addStretch()

                resume_btn = QPushButton("Resume")
                resume_btn.setObjectName("BtnSuccess")
                resume_btn.setFixedWidth(120)
                resume_btn.setStyleSheet("background-color: #00E676; color: black; font-weight: bold; border-radius: 6px; font-size: 14px;")
                resume_btn.clicked.connect(lambda checked, i=idx: self._resume(i))

                discard_btn = QPushButton("Discard")
                discard_btn.setObjectName("BtnDanger")
                discard_btn.setFixedSize(100, 38)
                discard_btn.setStyleSheet("background-color: #FF4A4A; color: white; font-weight: bold; border-radius: 6px; font-size: 14px;")
                discard_btn.clicked.connect(lambda checked, o=order, row=row_frame: self._discard(o, row))

                row_l.addWidget(resume_btn)
                row_l.addWidget(discard_btn)
                vbox.addWidget(row_frame)

            vbox.addStretch()
            scroll.setWidget(container)
            card_l.addWidget(scroll, 1)

        card_l.addWidget(_hdiv())
        foot = QHBoxLayout()
        cancel_btn = QPushButton("Close")
        cancel_btn.setObjectName("BtnChampagne")
        cancel_btn.clicked.connect(self.reject)
        foot.addStretch()
        foot.addWidget(cancel_btn)
        card_l.addLayout(foot)

        root.addWidget(card)

    def _resume(self, idx):
        self.order_resumed.emit(idx)
        self.accept()

    def _discard(self, order, row):
        reply = AppMessageBox.question(
            self, "Discard Order",
            "Are you sure you want to permanently discard this Hold Order?"
        )
        if reply == QMessageBox.Yes:
            if order in self._held:
                self._held.remove(order)
            row.hide()
            row.deleteLater()


# ─── Split Bill Dialog ────────────────────────────────────────────────────────
class SplitBillDialog(QDialog):
    """
    Full-featured Split Bill dialog with three methods:
      0 — Equal Split
      1 — By Item
      2 — Custom Amount
    Each guest pays via an independent procesar_venta() call (By Item),
    or all guests' payments are collected before one final procesar_venta
    (Equal / Custom).
    """

    def __init__(self, carrito, pos_service, sincronizador,
                 ncf_tipo, ncf_num, notas, cliente,
                 happy_hour_discount=0.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Split Bill")
        self.setMinimumSize(860, 620)
        self.setStyleSheet(STYLESHEET)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        self.carrito = carrito
        self.pos = pos_service
        self.sincronizador = sincronizador
        self.ncf_tipo = ncf_tipo
        self.ncf_num = ncf_num
        self.notas = notas
        self.cliente = cliente
        self.hh_discount = happy_hour_discount

        self.sub, self.imp, self.prop_legal, self.total = pos_service.calcular_totales(
            carrito, happy_hour_discount=happy_hour_discount
        )

        # Equal split state
        self._eq_guests = 2
        self._eq_selected = 0        # currently highlighted guest card index
        self._eq_paid = set()        # indices of guests who've confirmed payment
        self._eq_methods = {}        # guest_idx -> payment method string
        self._eq_card_btns = []      # QPushButton references for guest cards

        # By Item state
        self._bi_guests = []         # [{'name': str, 'items': [...carrito items]}]
        self._bi_unassigned = {i: item['cant'] for i, item in enumerate(carrito)}
        self._bi_paid = set()
        self._bi_selected_guest = 0

        # Custom state
        self._cu_guests = []         # [{'name': str, 'amount_str': str}]
        self._cu_inputs = []         # QLineEdit refs

        self._current_mode = 0

        self._build_ui()

    # ── UI Build ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        outer = _card()
        outer_l = QVBoxLayout(outer)
        outer_l.setContentsMargins(0, 0, 0, 0)
        outer_l.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        hdr_w = QFrame()
        hdr_w.setObjectName("SplitHdr")
        hdr_l = QVBoxLayout(hdr_w)
        hdr_l.setContentsMargins(28, 20, 28, 16)
        hdr_l.setSpacing(12)

        title_row = QHBoxLayout()
        title = _lbl("SPLIT BILL", "LblTitle")
        close_btn = QPushButton("✕")
        close_btn.setObjectName("BtnClose")
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(self.reject)
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(close_btn)
        hdr_l.addLayout(title_row)

        # Total summary strip
        sum_w = QFrame()
        sum_w.setObjectName("SplitSummary")
        sum_l = QHBoxLayout(sum_w)
        sum_l.setContentsMargins(20, 12, 20, 12)
        sum_l.setSpacing(24)

        for label, val in [
            ("SUBTOTAL", money(self.sub)),
            ("ITBIS (18%)", money(self.imp)),
            ("LEGAL TIP (10%)", money(self.prop_legal)),
        ]:
            col = QVBoxLayout()
            col.setSpacing(2)
            col.addWidget(_lbl(label, "LblMeta"))
            v = _lbl(val)
            v.setObjectName("LblBold")
            col.addWidget(v)
            sum_l.addLayout(col)

        sum_l.addStretch()

        total_lbl = _lbl(f"TOTAL:  {money(self.total)}", "LblSplitTotal",
                         Qt.AlignRight)
        sum_l.addWidget(total_lbl)
        hdr_l.addWidget(sum_w)

        # Tab selector
        tab_w = QFrame()
        tab_w.setObjectName("SplitTabs")
        tab_l = QHBoxLayout(tab_w)
        tab_l.setContentsMargins(4, 4, 4, 4)
        tab_l.setSpacing(4)

        self._tab_btns = []
        for i, label in enumerate(["EQUAL SPLIT", "BY ITEM", "CUSTOM AMOUNT"]):
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, idx=i: self._switch_mode(idx))
            self._tab_btns.append(btn)
            tab_l.addWidget(btn)

        self._style_tabs()
        hdr_l.addWidget(tab_w)
        outer_l.addWidget(hdr_w)

        # ── Content stack ─────────────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_equal_page())
        self._stack.addWidget(self._build_byitem_page())
        self._stack.addWidget(self._build_custom_page())
        outer_l.addWidget(self._stack, 1)

        # ── Footer ────────────────────────────────────────────────────────────
        foot_w = QFrame()
        foot_w.setObjectName("SplitFooter")
        foot_l = QHBoxLayout(foot_w)
        foot_l.setContentsMargins(28, 16, 28, 16)
        foot_l.setSpacing(12)

        self.lbl_progress = _lbl("", "LblMeta")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("BtnChampagne")
        cancel_btn.clicked.connect(self.reject)

        self.btn_pay = QPushButton("Select a guest to pay")
        self.btn_pay.setObjectName("BtnSuccess")
        self.btn_pay.setFixedHeight(48)
        self.btn_pay.setMinimumWidth(260)
        self.btn_pay.setEnabled(False)
        self.btn_pay.clicked.connect(self._on_pay_click)

        foot_l.addWidget(self.lbl_progress)
        foot_l.addStretch()
        foot_l.addWidget(cancel_btn)
        foot_l.addWidget(self.btn_pay)
        outer_l.addWidget(foot_w)

        root.addWidget(outer)
        self._update_footer()

    # ── Equal Split Page ──────────────────────────────────────────────────────
    def _build_equal_page(self):
        page = QWidget()
        l = QVBoxLayout(page)
        l.setContentsMargins(28, 20, 28, 20)
        l.setSpacing(16)

        # Guest counter
        ctr_row = QHBoxLayout()
        ctr_lbl = _lbl("NUMBER OF GUESTS", "LblMeta")

        self._eq_spin = QSpinBox()
        self._eq_spin.setRange(2, 20)
        self._eq_spin.setValue(self._eq_guests)
        self._eq_spin.setFixedWidth(120)
        self._eq_spin.valueChanged.connect(self._on_eq_guests_changed)

        ctr_row.addWidget(ctr_lbl)
        ctr_row.addStretch()
        ctr_row.addWidget(self._eq_spin)
        l.addLayout(ctr_row)

        # Guest cards area
        self._eq_cards_scroll = QScrollArea()
        self._eq_cards_scroll.setWidgetResizable(True)
        self._eq_cards_scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        self._eq_cards_w = QWidget()
        self._eq_cards_w.setStyleSheet("background:transparent;")
        self._eq_cards_grid = QGridLayout(self._eq_cards_w)
        self._eq_cards_grid.setSpacing(12)
        self._rebuild_eq_cards()
        self._eq_cards_scroll.setWidget(self._eq_cards_w)
        l.addWidget(self._eq_cards_scroll, 1)

        note = _lbl("* Rounding differences applied to last guest.", "LblMeta",
                    Qt.AlignCenter)
        l.addWidget(note)

        return page

    def _rebuild_eq_cards(self):
        # Clear existing
        for i in reversed(range(self._eq_cards_grid.count())):
            w = self._eq_cards_grid.itemAt(i).widget()
            if w:
                w.deleteLater()
        self._eq_card_btns.clear()

        per_guest = float(self.total) / self._eq_guests
        last_guest_amt = float(self.total) - per_guest * (self._eq_guests - 1)

        COLS = 4
        for idx in range(self._eq_guests):
            amount = last_guest_amt if idx == self._eq_guests - 1 else per_guest
            paid = idx in self._eq_paid
            selected = idx == self._eq_selected

            btn = QPushButton()
            if paid:
                btn.setText(f"Guest {idx+1}\nPAID\n{money(amount)}")
                btn.setEnabled(False)
                btn.setStyleSheet(
                    f"background:{CLR_SURFACE};color:{CLR_SUCCESS};"
                    f"border:1px solid {CLR_SUCCESS};border-radius:14px;"
                    f"padding:16px;font-size:15px;min-height:90px;text-align:center;"
                )
            elif selected:
                btn.setText(f"Guest {idx+1}\n{money(amount)}\nSELECTED")
                btn.setStyleSheet(
                    f"background:rgba(255,107,0,0.12);color:{CLR_EMBER};"
                    f"border:2px solid {CLR_EMBER};border-radius:14px;"
                    f"padding:16px;font-size:15px;font-weight:700;"
                    f"min-height:90px;text-align:center;"
                )
                btn.clicked.connect(lambda checked, i=idx: self._select_eq_guest(i))
            else:
                btn.setText(f"Guest {idx+1}\n{money(amount)}\nPending")
                btn.setObjectName("BtnGuestCard")
                btn.clicked.connect(lambda checked, i=idx: self._select_eq_guest(i))

            self._eq_card_btns.append(btn)
            row = idx // COLS
            col = idx % COLS
            self._eq_cards_grid.addWidget(btn, row, col)

    def _on_eq_guests_changed(self, n):
        self._eq_guests = n
        self._eq_paid.clear()
        self._eq_selected = 0
        self._rebuild_eq_cards()
        self._update_footer()

    def _select_eq_guest(self, idx):
        if idx in self._eq_paid:
            return
        self._eq_selected = idx
        self._rebuild_eq_cards()
        self._update_footer()

    # ── By Item Page ──────────────────────────────────────────────────────────
    def _build_byitem_page(self):
        page = QWidget()
        l = QHBoxLayout(page)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)

        # Left — unassigned items
        left_w = QFrame()
        left_w.setObjectName("BiLeft")
        left_l = QVBoxLayout(left_w)
        left_l.setContentsMargins(20, 16, 20, 16)
        left_l.setSpacing(8)

        left_hdr = QHBoxLayout()
        left_hdr.addWidget(_lbl("UNASSIGNED ITEMS", "LblMeta"))
        self._bi_count_lbl = _lbl(f"({len(self.carrito)})", "LblMeta", Qt.AlignRight)
        left_hdr.addWidget(self._bi_count_lbl)
        left_l.addLayout(left_hdr)
        left_l.addWidget(_hdiv())

        self._bi_unassigned_list = QListWidget()
        self._rebuild_bi_unassigned()
        left_l.addWidget(self._bi_unassigned_list, 1)

        assign_hint = _lbl("Click + 1 or ALL to assign to selected guest",
                           "LblMeta", Qt.AlignCenter)
        left_l.addWidget(assign_hint)

        l.addWidget(left_w, 1)

        # Right — guests
        right_w = QWidget()
        right_l = QVBoxLayout(right_w)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.setSpacing(0)

        # Guest panels scroll
        self._bi_guests_scroll = QScrollArea()
        self._bi_guests_scroll.setWidgetResizable(True)
        self._bi_guests_scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        self._bi_guests_container = QWidget()
        self._bi_guests_vbox = QVBoxLayout(self._bi_guests_container)
        self._bi_guests_vbox.setContentsMargins(16, 12, 16, 12)
        self._bi_guests_vbox.setSpacing(10)

        # Start with 1 guest
        if not self._bi_guests:
            self._bi_guests.append({'name': 'Guest 1', 'items': []})
        self._rebuild_bi_guests()

        self._bi_guests_scroll.setWidget(self._bi_guests_container)
        right_l.addWidget(self._bi_guests_scroll, 1)

        l.addWidget(right_w, 1)
        return page

    def _rebuild_bi_unassigned(self):
        self._bi_unassigned_list.clear()
        for idx, qty in self._bi_unassigned.items():
            if qty <= 0: continue
            item = self.carrito[idx]
            li = QListWidgetItem()
            li.setSizeHint(QSize(0, 72))
            self._bi_unassigned_list.addItem(li)
            
            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(10, 8, 10, 8)
            
            name_lbl = _lbl(f"  {item['nombre']}  (x{qty})")
            price_lbl = _lbl(money(float(item['precio']) * qty), align=Qt.AlignRight)
            price_lbl.setStyleSheet(f"color:{CLR_CHAMPAGNE};")
            
            l.addWidget(name_lbl)
            l.addStretch()
            l.addWidget(price_lbl)
            
            if qty > 1:
                btn_1 = QPushButton("  + 1  ")
                btn_1.setFixedHeight(28)
                btn_1.setCursor(Qt.PointingHandCursor)
                btn_1.setStyleSheet(f"QPushButton{{background:rgba(255,255,255,0.08);color:{CLR_TEXT};border-radius:6px;font-size:12px;font-weight:700;padding: 0 12px;}} QPushButton:hover{{background:rgba(255,107,0,0.3);}}")
                btn_1.clicked.connect(lambda checked, ci=idx: self._bi_assign_qty(ci, 1))
                l.addWidget(btn_1)
                
            btn_all = QPushButton("  ALL  " if qty > 1 else "  + 1  ")
            btn_all.setFixedHeight(28)
            btn_all.setCursor(Qt.PointingHandCursor)
            btn_all.setStyleSheet(f"QPushButton{{background:rgba(255,107,0,0.8);color:{CLR_TEXT};border-radius:6px;font-size:12px;font-weight:700;padding: 0 12px;}} QPushButton:hover{{background:{CLR_EMBER};}}")
            btn_all.clicked.connect(lambda checked, ci=idx, q=qty: self._bi_assign_qty(ci, q))
            l.addWidget(btn_all)
            
            self._bi_unassigned_list.setItemWidget(li, w)
            
        self._bi_count_lbl.setText(f"({len([k for k, v in self._bi_unassigned.items() if v > 0])})")

    def _rebuild_bi_guests(self):
        while self._bi_guests_vbox.count():
            item = self._bi_guests_vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for g_idx, guest in enumerate(self._bi_guests):
            g_total = sum(
                float(it['precio']) * it['cant'] for it in guest['items']
            )
            paid = g_idx in self._bi_paid
            selected = g_idx == self._bi_selected_guest

            panel = QFrame()
            panel.setObjectName("GuestPanel")
            border_color = CLR_EMBER if selected else CLR_BORDER
            bg_color = "rgba(255,107,0,0.06)" if selected else CLR_SURFACE
            panel.setStyleSheet(
                f"QFrame#GuestPanel{{background:{bg_color};border:1px solid {border_color};"
                f"border-radius:12px;}}"
            )
            panel_l = QVBoxLayout(panel)
            panel_l.setContentsMargins(14, 10, 14, 10)
            panel_l.setSpacing(6)

            # Guest header
            g_hdr = QHBoxLayout()
            g_name = _lbl(f"{'' if paid else ''}  {guest['name']}")
            g_name.setStyleSheet(
                f"color:{'#'+('00E676' if paid else 'DFE2EB')};"
                f"font-weight:700;font-size:14px;background:transparent;"
            )
            g_total_lbl = _lbl(money(g_total))
            g_total_lbl.setStyleSheet(
                f"color:{CLR_EMBER};font-weight:800;font-size:14px;background:transparent;"
            )
            g_hdr.addWidget(g_name)
            g_hdr.addStretch()
            g_hdr.addWidget(g_total_lbl)
            panel_l.addLayout(g_hdr)

            # Items list
            if guest['items']:
                for it_idx, it in enumerate(guest['items']):
                    it_row = QHBoxLayout()
                    it_lbl = _lbl(f"  {it['nombre']} x{it['cant']}")
                    it_lbl.setStyleSheet(f"color:{CLR_TEXT_MID};font-size:12px;background:transparent;")
                    it_price = _lbl(money(float(it['precio']) * it['cant']), align=Qt.AlignRight)
                    it_price.setStyleSheet(f"color:{CLR_CHAMPAGNE};font-size:12px;background:transparent;")
                    
                    it_row.addWidget(it_lbl)
                    it_row.addStretch()
                    it_row.addWidget(it_price)

                    unassign_btn = QPushButton("  Remove  ")
                    unassign_btn.setFixedHeight(24)
                    unassign_btn.setCursor(Qt.PointingHandCursor)
                    unassign_btn.setStyleSheet(f"QPushButton{{background:rgba(255,76,76,0.1);color:{CLR_ERROR};border:none;border-radius:4px;font-weight:bold;font-size:11px;padding: 0 8px;}} QPushButton:hover{{background:rgba(255,76,76,0.2);}}")
                    unassign_btn.clicked.connect(lambda checked, gi=g_idx, ii=it_idx, ci=it.get('_orig_cart_idx', -1): self._bi_unassign_item(gi, ii, ci))
                    if paid:
                        unassign_btn.setVisible(False)
                    it_row.addWidget(unassign_btn)
                    
                    panel_l.addLayout(it_row)
            else:
                empty = _lbl("  No items assigned yet", "LblMeta")
                empty.setStyleSheet(f"color:{CLR_TEXT_DIM};font-size:12px;font-style:italic;background:transparent;")
                panel_l.addWidget(empty)

            # Select / Pay row
            if not paid:
                btn_row = QHBoxLayout()
                if not selected:
                    sel_btn = QPushButton("Select Guest")
                    sel_btn.setObjectName("BtnChampagne")
                    sel_btn.setFixedHeight(42)
                    sel_btn.clicked.connect(lambda checked, gi=g_idx: self._bi_select_guest(gi))
                    btn_row.addWidget(sel_btn)

                if guest['items']:
                    pay_btn = QPushButton(f"Pay  {money(g_total)}")
                    pay_btn.setObjectName("BtnSuccess")
                    pay_btn.setFixedHeight(42)
                    pay_btn.clicked.connect(lambda checked, gi=g_idx: self._bi_pay_guest(gi))
                    btn_row.addWidget(pay_btn)
                btn_row.addStretch()
                panel_l.addLayout(btn_row)

            panel.mousePressEvent = lambda event, gi=g_idx: self._bi_select_guest(gi)
            self._bi_guests_vbox.addWidget(panel)

        self._bi_guests_vbox.addStretch()
        add_g_btn = QPushButton("ADD GUEST")
        add_g_btn.setObjectName("BtnChampagne")
        add_g_btn.setFixedHeight(42)
        add_g_btn.setStyleSheet(
            f"QPushButton{{background:transparent;color:{CLR_CHAMPAGNE};"
            f"border:1px dashed rgba(226,180,154,0.4);border-radius:10px;"
            f"font-size:13px;font-weight:700;}}"
            f"QPushButton:hover{{border-color:{CLR_CHAMPAGNE};"
            f"background:rgba(226,180,154,0.06);}}"
        )
        add_g_btn.clicked.connect(self._bi_add_guest)
        self._bi_guests_vbox.addWidget(add_g_btn)

    def _bi_select_guest(self, idx):
        self._bi_selected_guest = idx
        self._rebuild_bi_guests()
        self._update_footer()

    def _bi_add_guest(self):
        n = len(self._bi_guests) + 1
        self._bi_guests.append({'name': f'Guest {n}', 'items': []})
        self._bi_selected_guest = n - 1
        self._rebuild_bi_guests()
        self._update_footer()

    def _bi_unassign_item(self, g_idx, item_idx, cart_idx):
        if cart_idx == -1: return
        it = self._bi_guests[g_idx]['items'].pop(item_idx)
        if cart_idx not in self._bi_unassigned:
            self._bi_unassigned[cart_idx] = 0
        self._bi_unassigned[cart_idx] += it['cant']
        self._rebuild_bi_unassigned()
        self._rebuild_bi_guests()
        self._update_footer()

    def _bi_assign_qty(self, cart_idx, qty):
        if cart_idx not in self._bi_unassigned or self._bi_unassigned[cart_idx] < qty:
            return
        if not self._bi_guests:
            self._bi_add_guest()
            
        cart_item = self.carrito[cart_idx].copy()
        cart_item['cant'] = qty
        cart_item['_orig_cart_idx'] = cart_idx
        
        guest_items = self._bi_guests[self._bi_selected_guest]['items']
        existing = next((i for i in guest_items if i.get('_orig_cart_idx') == cart_idx), None)
        if existing:
            existing['cant'] += qty
        else:
            guest_items.append(cart_item)
            
        self._bi_unassigned[cart_idx] -= qty
        if self._bi_unassigned[cart_idx] <= 0:
            del self._bi_unassigned[cart_idx]
            
        self._rebuild_bi_unassigned()
        self._rebuild_bi_guests()
        self._update_footer()

    def _bi_pay_guest(self, g_idx):
        guest = self._bi_guests[g_idx]
        if not guest['items']:
            return
        method_text, ok = AppInputDialog.getItem(
            self, "Payment Method", f"Payment method for {guest['name']}:",
            ["CASH", "CARD", "TRANSFER"]
        )
        if not ok:
            return
        method_map = {"CASH": "EFECTIVO", "CARD": "TARJETA", "TRANSFER": "TRANSFERENCIA"}
        method = method_map.get(method_text, "EFECTIVO")
        cambio = 0.0

        cash_val = "0"
        if method == "EFECTIVO":
            cash_val, ok2 = AppInputDialog.getText(
                self, "Cash Amount",
                f"Enter cash received from {guest['name']}:"
            )
            if not ok2:
                return

        # Verifone dialog for card
        if method == "TARJETA":
            g_sub, g_imp, g_prop, g_total = self.pos.calcular_totales(
                guest['items'], happy_hour_discount=self.hh_discount
            )
            vd = VerifoneDialog(
                money(g_total),
                subtotal_str=money(g_sub),
                itbis_str=money(g_imp),
                legaltip_str=money(g_prop),
                parent=self
            )
            if vd.exec() != QDialog.Accepted:
                return

        cambio, msg = self.pos.procesar_venta(
            carrito=guest['items'],
            efectivo=cash_val,
            metodo=method,
            ncf_tipo=self.ncf_tipo,
            ncf_num=self.ncf_num,
            notas=f"Split Bill — {guest['name']} | {self.notas}",
            cliente=f"{self.cliente} ({guest['name']})",
            sincronizador=self.sincronizador,
            deduct_stock=True,
            happy_hour_discount=self.hh_discount,
        )
        if cambio is not None:
            self._bi_paid.add(g_idx)
            if method == "EFECTIVO":
                change_text = f"\nChange to return: {money(cambio)}" if cambio > 0.009 else ""
                AppMessageBox.information(
                    self, "Payment Processed",
                    f"{guest['name']} has successfully paid their portion.{change_text}"
                )
            else:
                AppMessageBox.information(self, "Payment Processed",
                                        f"{guest['name']} has successfully paid their portion.")
            self._rebuild_bi_guests()
            self._update_footer()
            # Check if all guests with items are paid
            guests_with_items = [i for i, g in enumerate(self._bi_guests) if g['items']]
            if guests_with_items and all(i in self._bi_paid for i in guests_with_items) \
                    and not self._bi_unassigned:
                AppMessageBox.information(
                    self, "Split Complete",
                    "All guests have paid! The bill is fully settled."
                )
                self.accept()
        else:
            AppMessageBox.warning(self, "Payment Failed", msg)

    # ── Custom Amount Page ────────────────────────────────────────────────────
    def _build_custom_page(self):
        page = QWidget()
        l = QVBoxLayout(page)
        l.setContentsMargins(28, 20, 28, 20)
        l.setSpacing(14)

        # Summary bar
        sum_row = QHBoxLayout()
        total_txt = _lbl(f"Total Bill:  {money(self.total)}", "LblBold")
        self._cu_remaining_lbl = _lbl(f"Remaining:  {money(self.total)}",
                                      "LblCuRemaining")
        sum_row.addWidget(total_txt)
        sum_row.addStretch()
        sum_row.addWidget(self._cu_remaining_lbl)
        l.addLayout(sum_row)
        l.addWidget(_hdiv())

        # Guest list scroll
        self._cu_scroll = QScrollArea()
        self._cu_scroll.setWidgetResizable(True)
        self._cu_scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        self._cu_container = QWidget()
        self._cu_vbox = QVBoxLayout(self._cu_container)
        self._cu_vbox.setContentsMargins(0, 0, 0, 0)
        self._cu_vbox.setSpacing(8)

        # Start with 2 guests
        self._cu_guests = [
            {'name': 'Guest 1', 'amount_str': ''},
            {'name': 'Guest 2', 'amount_str': ''},
        ]
        self._cu_rebuild()
        self._cu_scroll.setWidget(self._cu_container)
        l.addWidget(self._cu_scroll, 1)

        # Add guest
        add_btn = QPushButton("Add Guest")
        add_btn.setObjectName("BtnChampagne")
        add_btn.setFixedHeight(40)
        add_btn.clicked.connect(self._cu_add_guest)
        l.addWidget(add_btn)

        return page

    def _cu_rebuild(self):
        for i in reversed(range(self._cu_vbox.count())):
            w = self._cu_vbox.itemAt(i).widget()
            if w:
                w.deleteLater()
        self._cu_inputs.clear()

        for g_idx, guest in enumerate(self._cu_guests):
            row_w = QFrame()
            row_w.setObjectName("CardFrame")
            row_w.setStyleSheet(
                f"QFrame#CardFrame{{background:{CLR_SURFACE_HIGH};"
                f"border:1px solid {CLR_BORDER};border-radius:12px;}}"
            )
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(16, 10, 16, 10)
            row_l.setSpacing(12)

            # Name label
            name_lbl = _lbl(guest['name'])
            name_lbl.setStyleSheet(
                f"color:{CLR_TEXT};font-weight:700;font-size:14px;background:transparent;"
            )
            name_lbl.setFixedWidth(100)
            row_l.addWidget(name_lbl)

            row_l.addStretch()

            # Dollar sign
            dollar = _lbl("$")
            dollar.setStyleSheet(
                f"color:{CLR_CHAMPAGNE};font-weight:700;font-size:16px;background:transparent;"
            )
            row_l.addWidget(dollar)

            # Amount input
            amt_input = QLineEdit()
            amt_input.setPlaceholderText("0.00")
            amt_input.setText(guest.get('amount_str', ''))
            amt_input.setFixedWidth(140)
            amt_input.setStyleSheet(
                f"color:{CLR_EMBER};font-weight:800;font-size:15px;"
                f"text-align:right;background:{CLR_SURFACE};"
                f"border:1px solid {CLR_BORDER};border-radius:8px;padding:8px;"
            )
            amt_input.textChanged.connect(
                lambda text, gi=g_idx: self._cu_amount_changed(gi, text)
            )
            self._cu_inputs.append(amt_input)
            row_l.addWidget(amt_input)

            # Remove button
            btn_del = QPushButton("DEL")
            btn_del.setObjectName("BtnEmber")
            btn_del.setFixedSize(48, 36)
            btn_del.clicked.connect(lambda checked, gi=g_idx: self._cu_remove_guest(gi))
            if len(self._cu_guests) <= 2:
                btn_del.setEnabled(False)
            row_l.addWidget(btn_del)

            self._cu_vbox.addWidget(row_w)

        self._cu_vbox.addStretch()

    def _cu_amount_changed(self, g_idx, text):
        if 0 <= g_idx < len(self._cu_guests):
            self._cu_guests[g_idx]['amount_str'] = text
        self._cu_update_remaining()
        self._update_footer()

    def _cu_update_remaining(self):
        used = 0.0
        for g in self._cu_guests:
            try:
                used += float(g.get('amount_str') or '0')
            except ValueError:
                pass
        remaining = float(self.total) - used
        color = CLR_SUCCESS if abs(remaining) < 0.01 else CLR_EMBER
        self._cu_remaining_lbl.setText(f"Remaining:  {money(remaining)}")
        self._cu_remaining_lbl.setStyleSheet(
            f"color:{color};font-size:15px;font-weight:800;"
        )

    def _cu_add_guest(self):
        n = len(self._cu_guests) + 1
        self._cu_guests.append({'name': f'Guest {n}', 'amount_str': ''})
        self._cu_rebuild()

    def _cu_remove_guest(self, g_idx):
        if len(self._cu_guests) > 2:
            self._cu_guests.pop(g_idx)
            self._cu_rebuild()
            self._cu_update_remaining()

    # ── Tab switching ─────────────────────────────────────────────────────────
    def _switch_mode(self, idx):
        self._current_mode = idx
        self._stack.setCurrentIndex(idx)
        self._style_tabs()
        self._update_footer()

    def _style_tabs(self):
        for i, btn in enumerate(self._tab_btns):
            clr = CLR_EMBER if i == self._current_mode else CLR_TEXT_MID
            brd = CLR_EMBER if i == self._current_mode else "transparent"
            w   = "800"   if i == self._current_mode else "600"
            btn.setStyleSheet(
                f"QPushButton{{background:transparent;color:{clr};"
                f"border:none;border-bottom:3px solid {brd};border-radius:0px;padding:12px 20px;"
                f"font-size:14px;font-weight:{w};}}"
                f"QPushButton:hover{{color:{CLR_TEXT};}}"
            )

    # ── Footer update ─────────────────────────────────────────────────────────
    def _update_footer(self):
        mode = self._current_mode

        if mode == 0:  # Equal
            n_paid = len(self._eq_paid)
            n_total = self._eq_guests
            per_guest = float(self.total) / n_total
            last_amt = float(self.total) - per_guest * (n_total - 1)
            g_idx = self._eq_selected
            amt = last_amt if g_idx == n_total - 1 else per_guest

            self.lbl_progress.setText(
                f"Paid: {n_paid}/{n_total} guests"
            )
            if g_idx in self._eq_paid:
                self.btn_pay.setText("Already Paid — Select Another Guest")
                self.btn_pay.setEnabled(False)
            else:
                self.btn_pay.setText(f"Pay Guest {g_idx+1}  ({money(amt)})")
                self.btn_pay.setEnabled(True)

        elif mode == 1:  # By Item
            guests_with_items = [i for i, g in enumerate(self._bi_guests) if g['items']]
            n_paid = len([i for i in guests_with_items if i in self._bi_paid])
            self.lbl_progress.setText(
                f"Unassigned: {len(self._bi_unassigned)} items  •  "
                f"Paid: {n_paid}/{len(guests_with_items)} guests"
            )
            self.btn_pay.setText("Use guest → Pay buttons")
            self.btn_pay.setEnabled(False)

        elif mode == 2:  # Custom
            used = 0.0
            for g in self._cu_guests:
                try:
                    used += float(g.get('amount_str') or '0')
                except ValueError:
                    pass
            remaining = float(self.total) - used
            all_filled = all(g.get('amount_str', '').strip() for g in self._cu_guests)
            self.lbl_progress.setText(f"Remaining: {money(remaining)}" if abs(remaining) > 0.009 else "Fully allocated")
            self.btn_pay.setText("Process Custom Payments")
            self.btn_pay.setEnabled(abs(remaining) < 0.01 and all_filled)

    # ── Payments ─────────────────────────────────────────────────────────────
        if g_idx in self._eq_paid:
            return

        per_guest = float(self.total) / self._eq_guests
        last_amt = float(self.total) - per_guest * (self._eq_guests - 1)
        amount = last_amt if g_idx == self._eq_guests - 1 else per_guest

        method_text, ok = AppInputDialog.getItem(
            self, "Payment Method",
            f"Select payment method for Guest {g_idx+1} ({money(amount)}):",
            ["CASH", "CARD", "TRANSFER"]
        )
        if not ok:
            return

        method_map = {"CASH": "EFECTIVO", "CARD": "TARJETA", "TRANSFER": "TRANSFERENCIA"}
        method = method_map.get(method_text, "EFECTIVO")
        cambio = 0.0

        cash_val = "0"
        if method == "EFECTIVO":
            cash_val, ok = AppInputDialog.getText(
                self, "Cash Received",
                f"Cash received from Guest {g_idx+1} ({money(amount)}):"
            )
            if not ok:
                return

        if method == "TARJETA":
            vd = VerifoneDialog(
                money(amount),
                subtotal_str=money(amount),
                parent=self
            )
            if vd.exec() != QDialog.Accepted:
                return

        # Build a synthetic single-item cart for accounting
        # The first guest triggers stock deduction, others skip it
        is_first = len(self._eq_paid) == 0
        # Proportional sub-carrito
        ratio = Decimal(str(amount)) / Decimal(str(float(self.total)))
        synthetic_cart = []
        for it in self.carrito:
            synthetic_cart.append({
                'id': it.get('id'),
                'nombre': it['nombre'],
                'precio': float(Decimal(str(it['precio'])) * ratio),
                'cant': it['cant'],
                'tasa': 0.0,   # tax already included in ratio
                'stock': it.get('stock', 9999),
                'notas_item': it.get('notas_item', []),
            })

        cambio, msg = self.pos.procesar_venta(
            carrito=synthetic_cart,
            efectivo=cash_val,
            metodo=method,
            ncf_tipo=self.ncf_tipo,
            ncf_num=self.ncf_num,
            notas=f"Equal Split ({g_idx+1}/{self._eq_guests}) | {self.notas}",
            cliente=f"{self.cliente} (Guest {g_idx+1})",
            sincronizador=self.sincronizador,
            deduct_stock=is_first,
            happy_hour_discount=0.0,  # already accounted in total
        )

        if cambio is not None:
            self._eq_paid.add(g_idx)
            if method == "EFECTIVO":
                change_text = f"\nChange to return: {money(cambio)}" if cambio > 0.009 else ""
                AppMessageBox.information(
                    self, "Payment Processed",
                    f"Guest {g_idx+1} has successfully paid their portion.{change_text}"
                )
            else:
                AppMessageBox.information(self, "Payment Processed",
                                        f"Guest {g_idx+1} has successfully paid their portion.")
            self._rebuild_eq_cards()
            # Auto-select next unpaid guest
            for ni in range(self._eq_guests):
                if ni not in self._eq_paid:
                    self._eq_selected = ni
                    break
            self._rebuild_eq_cards()
            self._update_footer()

            if len(self._eq_paid) == self._eq_guests:
                AppMessageBox.information(
                    self, "Split Complete",
                    "All guests have paid! The bill is fully settled."
                )
                self.accept()
        else:
            AppMessageBox.warning(self, "Payment Failed", msg)

    # ── Custom split confirm ──────────────────────────────────────────────────
    def _cu_confirm_all(self):
        """Process each guest's custom amount as a separate invoice."""
        amounts = []
        for g in self._cu_guests:
            try:
                amounts.append(float(g['amount_str']))
            except ValueError:
                AppMessageBox.warning(self, "Invalid Amount",
                                    f"Please enter a valid amount for {g['name']}.")
                return

        # Method selection dialog for each guest
        method_map = {"CASH": "EFECTIVO", "CARD": "TARJETA", "TRANSFER": "TRANSFERENCIA"}
        first_done = False
        for g_idx, (guest, amount) in enumerate(zip(self._cu_guests, amounts)):
            method_text, ok = QInputDialog.getItem(
                self, "Payment Method",
                f"Payment method for {guest['name']} ({money(amount)}):",
                ["CASH", "CARD", "TRANSFER"], 0, False
            )
            if not ok:
                return
            method = method_map.get(method_text, "EFECTIVO")

            cash_val = "0"
            if method == "EFECTIVO":
                cash_val, ok2 = QInputDialog.getText(
                    self, "Cash Received",
                    f"Cash received from {guest['name']} ({money(amount)}):"
                )
                if not ok2:
                    return

            if method == "TARJETA":
                vd = VerifoneDialog(money(amount), parent=self)
                if vd.exec() != QDialog.Accepted:
                    return

            # Synthetic cart
            ratio = Decimal(str(amount)) / Decimal(str(float(self.total)))
            synthetic_cart = []
            for it in self.carrito:
                synthetic_cart.append({
                    'id': it.get('id'),
                    'nombre': it['nombre'],
                    'precio': float(Decimal(str(it['precio'])) * ratio),
                    'cant': it['cant'],
                    'tasa': it.get('tasa', 0.18),
                    'stock': it.get('stock', 9999),
                    'notas_item': it.get('notas_item', []),
                })

            cambio, msg = self.pos.procesar_venta(
                carrito=synthetic_cart,
                efectivo=cash_val,
                metodo=method,
                ncf_tipo=self.ncf_tipo,
                ncf_num=self.ncf_num,
                notas=f"Custom Split ({g_idx+1}/{len(self._cu_guests)}) | {self.notas}",
                cliente=f"{self.cliente} ({guest['name']})",
                sincronizador=self.sincronizador,
                deduct_stock=not first_done,
                happy_hour_discount=0.0,
            )
            if cambio is None:
                AppMessageBox.warning(self, "Payment Failed", msg)
                return
            first_done = True

        AppMessageBox.information(
            self, "Split Complete",
            "All custom split payments have been processed successfully!"
        )
        self.accept()


# ─── Active Tables Dialog (restyled) ─────────────────────────────────────────
class MesasDialog(QDialog):
    order_selected = Signal(dict)

    def __init__(self, sincronizador, pos_service, parent=None):
        super().__init__(parent)
        self.sincronizador = sincronizador
        self.pos = pos_service
        self._pedidos = []

        self._refresh_thread = QThread(self)
        self._refresh_worker = _FetchOrdersWorker(self.sincronizador)
        self._refresh_worker.moveToThread(self._refresh_thread)
        self._refresh_worker.request.connect(self._refresh_worker.run)
        self._refresh_worker.finished.connect(self._on_refresh_done)
        self._refresh_thread.start()

        self.setWindowTitle("Active Tables — Open Orders")
        self.setMinimumSize(900, 560)
        self.setStyleSheet(STYLESHEET)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setObjectName("HeaderFrame")
        hdr.setFixedHeight(64)
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(24, 0, 24, 0)
        title = _lbl("ACTIVE TABLES", "LblTitle")
        hint = _lbl("Double-click a row to import and pay an order", "LblMeta")
        hdr_l.addWidget(title)
        hdr_l.addSpacing(20)
        hdr_l.addWidget(hint)
        hdr_l.addStretch()
        root.addWidget(hdr)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["TABLE", "CHANNEL", "STATUS", "SUBTOTAL", "TOTAL", "DATE"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.doubleClicked.connect(self._on_double_click)
        root.addWidget(self.table, 1)

        # Footer
        foot = QFrame()
        foot.setStyleSheet(
            f"background:{CLR_SURFACE};border-top:1px solid {CLR_BORDER};"
        )
        foot.setFixedHeight(60)
        foot_l = QHBoxLayout(foot)
        foot_l.setContentsMargins(20, 0, 20, 0)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.setObjectName("BtnChampagne")
        btn_refresh.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; border-radius: 6px; font-size: 14px; padding: 8px 16px;")
        btn_refresh.clicked.connect(self.refresh)
        btn_close = QPushButton("Close")
        btn_close.setObjectName("BtnDanger")
        btn_close.setFixedWidth(100)
        btn_close.setStyleSheet("background-color: #FF4A4A; color: white; font-weight: bold; border-radius: 6px; font-size: 14px; padding: 8px 16px;")
        btn_close.clicked.connect(self.hide)
        foot_l.addWidget(btn_refresh)
        foot_l.addStretch()
        foot_l.addWidget(btn_close)
        root.addWidget(foot)

    def cleanup_thread(self):
        if self._refresh_thread.isRunning():
            self._refresh_thread.quit()
            self._refresh_thread.wait(2000)

    def refresh(self):
        self.table.setRowCount(0)
        self.table.insertRow(0)
        loading = QTableWidgetItem("Loading...")
        loading.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(0, 0, loading)
        self._refresh_worker.request.emit()

    def _on_refresh_done(self, pedidos):
        try:
            self.isVisible()
        except RuntimeError:
            return
        self._pedidos = pedidos or []
        self._populate(self._pedidos)

    def populate_from_data(self, pedidos):
        self._pedidos = pedidos or []
        self._populate(self._pedidos)

    def _populate(self, pedidos):
        self.table.setRowCount(0)
        for pedido in pedidos:
            row = self.table.rowCount()
            self.table.insertRow(row)
            mesa_val  = pedido.get("mesa") or "—"
            canal     = pedido.get("canal_origen") or "—"
            estado    = pedido.get("estado") or "—"
            subtotal  = money(pedido.get('subtotal') or 0)
            total     = money(pedido.get('total_general') or 0)
            raw_fecha = pedido.get("fecha_creacion") or ""
            fecha = str(raw_fecha)[:19].replace("T", " ") if raw_fecha else "—"

            for col, val in enumerate([str(mesa_val), canal, estado, subtotal, total, fecha]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

            if estado in ("POR_FACTURAR", "EN_ESPERA", "PENDIENTE"):
                for col in range(6):
                    cell = self.table.item(row, col)
                    if cell:
                        cell.setForeground(QBrush(QColor(CLR_EMBER)))
                        cell.setBackground(QBrush(QColor("rgba(255,107,0,0.08)")))

    def _on_double_click(self, index):
        row = index.row()
        if row < 0 or row >= len(self._pedidos):
            return
        pedido = self._pedidos[row]
        uuid = pedido.get("factura_local_uuid")
        if not uuid:
            AppMessageBox.warning(self, "Error", "Order has no UUID.")
            return

        subtotal_val = float(pedido.get('subtotal') or 0.0)
        itbis_val    = float(pedido.get('total_impuestos') or 0.0)
        try:
            prop_legal = float(pedido.get('propina_legal') or 0.0)
        except (ValueError, TypeError):
            prop_legal = 0.0
        if prop_legal <= 0.0:
            prop_legal = subtotal_val * 0.10

        extra_tip_input, ok_tip = AppInputDialog.getText(
            self, "Extra Tip", "Enter extra tip amount (or leave blank for $0):"
        )
        if not ok_tip:
            return
        try:
            prop_extra = float(extra_tip_input.strip()) if extra_tip_input.strip() else 0.0
        except (ValueError, TypeError):
            prop_extra = 0.0

        total_val    = subtotal_val + itbis_val + prop_legal + prop_extra
        total_str    = money(total_val)
        subtotal_str = money(subtotal_val)
        itbis_str    = money(itbis_val)
        legal_tip_str= money(prop_legal)
        extra_tip_str= money(prop_extra)

        dialog = VerifoneDialog(
            total_str,
            subtotal_str=subtotal_str,
            itbis_str=itbis_str,
            legaltip_str=legal_tip_str,
            extratip_str=extra_tip_str,
            parent=self
        )
        result = dialog.exec()
        dialog.deleteLater()

        if result == QDialog.Accepted:
            ok, msg = self.sincronizador.notificar_facturacion_remota(uuid)
            if ok:
                pedido['propina_extra']  = prop_extra
                pedido['propina_legal']  = prop_legal
                pedido['total_general']  = total_val

                carrito = pedido.get("carrito", [])
                mesa    = pedido.get("mesa", "")
                cliente = f"Table {mesa}" if mesa and str(mesa).strip() else "TABLE CUSTOMER"
                try:
                    self.pos.generar_ticket_desde_pedido(
                        pedido=pedido,
                        carrito_raw=carrito,
                        ncf_tipo="CONSUMER",
                        ncf_num="B0200000001",
                        notas="",
                        cliente=cliente,
                    )
                except Exception as ticket_err:
                    print(f"Could not generate ticket for {uuid}: {ticket_err}", flush=True)

                AppMessageBox.information(
                    self, "Transaction Successful",
                    "Order has been paid, closed, and ticket generated."
                )
                self.pos.descontar_stock_remoto(carrito)
                self.refresh()
                parent = self.parentWidget()
                if parent and hasattr(parent, '_activate_stock_cooldown'):
                    parent._activate_stock_cooldown()
                if parent and hasattr(parent, '_start_sync'):
                    parent._start_sync(
                        parent._on_manual_sync_done,
                        fetch_pedidos=True, full_sync=True
                    )
            else:
                AppMessageBox.critical(
                    self, "CORE Notification Failed",
                    f"Payment went through, but failed to notify CORE:\n{msg}"
                )


# ─── Supervisor Authorization Dialog (TOTP) ───────────────────────────────────
class SupervisorAuthDialog(QDialog):
    """
    Requires supervisor email + password + 6-digit TOTP OTP.
    Returns supervisor info on accept, empty dict on cancel/failure.
    """
    def __init__(self, sincronizador, action_label="Manual Discount", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Supervisor Authorization Required")
        self.setFixedWidth(480)
        self.setStyleSheet(STYLESHEET)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.sincronizador = sincronizador
        self.action_label = action_label
        self._result_data = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = _card()
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(32, 28, 32, 28)
        card_l.setSpacing(14)

        # Header
        hdr = QHBoxLayout()
        icon_lbl = _lbl("🔐")
        icon_lbl.setStyleSheet("font-size:24px;background:transparent;")
        title_lbl = _lbl("SUPERVISOR AUTHORIZATION", "LblTitle")
        title_lbl.setStyleSheet(f"color:{CLR_EMBER};font-weight:800;font-size:16px;background:transparent;")
        hdr.addWidget(icon_lbl)
        hdr.addSpacing(8)
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setObjectName("BtnClose")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.reject)
        hdr.addWidget(close_btn)
        card_l.addLayout(hdr)
        card_l.addWidget(_hdiv())

        # Supervisor panel frame
        sup_frame = QFrame()
        sup_frame.setObjectName("SupervisorPanel")
        sup_l = QVBoxLayout(sup_frame)
        sup_l.setContentsMargins(16, 14, 16, 14)
        sup_l.setSpacing(10)

        action_lbl = _lbl(f"Authorization required for:  {action_label}")
        action_lbl.setStyleSheet(f"color:{CLR_CHAMPAGNE};font-size:13px;font-weight:600;background:transparent;")
        action_lbl.setWordWrap(True)
        sup_l.addWidget(action_lbl)

        note_lbl = _lbl("The supervisor must be physically present and enter their credentials.")
        note_lbl.setStyleSheet(f"color:{CLR_TEXT_MID};font-size:12px;background:transparent;")
        note_lbl.setWordWrap(True)
        sup_l.addWidget(note_lbl)
        card_l.addWidget(sup_frame)

        card_l.addWidget(_lbl("SUPERVISOR EMAIL", "LblMeta"))
        self.inp_email = QLineEdit()
        self.inp_email.setPlaceholderText("supervisor@email.com")
        self.inp_email.setFixedHeight(42)
        card_l.addWidget(self.inp_email)


        otp_row = QHBoxLayout()
        otp_row.setSpacing(6)
        otp_lbl = _lbl("ONE-TIME CODE (OTP)", "LblMeta")
        totp_hint = _lbl("Google Authenticator")
        totp_hint.setStyleSheet(f"color:{CLR_TEXT_DIM};font-size:11px;background:transparent;")
        otp_row.addWidget(otp_lbl)
        otp_row.addStretch()
        otp_row.addWidget(totp_hint)
        card_l.addLayout(otp_row)
        self.inp_otp = QLineEdit()
        self.inp_otp.setPlaceholderText("6-digit code")
        self.inp_otp.setFixedHeight(42)
        self.inp_otp.setMaxLength(6)
        self.inp_otp.returnPressed.connect(self._do_auth)
        card_l.addWidget(self.inp_otp)

        self.err_lbl = _lbl("")
        self.err_lbl.setStyleSheet("color:#FF4C4C;font-size:12px;background:transparent;")
        self.err_lbl.setWordWrap(True)
        self.err_lbl.setVisible(False)
        card_l.addWidget(self.err_lbl)

        card_l.addSpacing(4)
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("BtnChampagne")
        btn_cancel.setFixedWidth(110)
        btn_cancel.clicked.connect(self.reject)
        self.btn_auth = QPushButton("AUTHORIZE  →")
        self.btn_auth.setObjectName("BtnSuccess")
        self.btn_auth.setFixedHeight(46)
        self.btn_auth.setMinimumWidth(180)
        self.btn_auth.clicked.connect(self._do_auth)
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_auth)
        card_l.addLayout(btn_row)

        root.addWidget(card)
        root.setSizeConstraint(QVBoxLayout.SetFixedSize)

    def _do_auth(self):
        email = self.inp_email.text().strip()
        otp = self.inp_otp.text().strip()
        if not email or not otp:
            self.err_lbl.setText("All fields are required.")
            self.err_lbl.setVisible(True)
            return
        if len(otp) != 6 or not otp.isdigit():
            self.err_lbl.setText("OTP must be exactly 6 digits.")
            self.err_lbl.setVisible(True)
            return
        self.btn_auth.setEnabled(False)
        self.btn_auth.setText("Verifying…")
        try:
            result = self.sincronizador.autenticar_supervisor_totp(email, otp)
        except Exception as e:
            result = {"ok": False, "error": str(e)}
        self.btn_auth.setEnabled(True)
        self.btn_auth.setText("AUTHORIZE  →")
        if result.get("ok"):
            self._result_data = result
            self.accept()
        else:
            self.err_lbl.setText(f"Authorization denied: {result.get('error', 'Unknown error.')}")
            self.err_lbl.setVisible(True)
            self.inp_otp.clear()
            self.inp_otp.setFocus()

    def get_supervisor_info(self) -> dict:
        return self._result_data


# ─── Eligibility Identifier Dialog ────────────────────────────────────────────
class EligibilityIdentifierDialog(QDialog):
    """
    Prompts the cashier to capture the customer's credential identifier
    (e.g., Student ID, Military ID). No external validation is performed —
    the identifier is recorded for audit purposes only.
    """
    def __init__(self, promo_nombre: str, etiqueta: str, requiere: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Eligibility — {promo_nombre}")
        self.setFixedWidth(460)
        self.setStyleSheet(STYLESHEET)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self._identifier = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = _card()
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(32, 28, 32, 28)
        card_l.setSpacing(14)

        hdr = QHBoxLayout()
        icon_lbl = _lbl("🎫")
        icon_lbl.setStyleSheet("font-size:22px;background:transparent;")
        title_lbl = _lbl("ELIGIBILITY VERIFICATION", "LblTitle")
        title_lbl.setStyleSheet("color:#00B4A0;font-weight:800;font-size:15px;background:transparent;")
        hdr.addWidget(icon_lbl)
        hdr.addSpacing(6)
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setObjectName("BtnClose")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.reject)
        hdr.addWidget(close_btn)
        card_l.addLayout(hdr)
        card_l.addWidget(_hdiv())

        promo_panel = QFrame()
        promo_panel.setObjectName("PromoPanelSection")
        promo_l = QVBoxLayout(promo_panel)
        promo_l.setContentsMargins(14, 12, 14, 12)
        promo_l.setSpacing(4)
        promo_name_lbl = _lbl(promo_nombre)
        promo_name_lbl.setStyleSheet("color:#00B4A0;font-weight:800;font-size:15px;background:transparent;")
        instr_lbl = _lbl("Physically inspect the customer's credential and enter the identifier shown below.")
        instr_lbl.setStyleSheet(f"color:{CLR_TEXT_MID};font-size:12px;background:transparent;")
        instr_lbl.setWordWrap(True)
        promo_l.addWidget(promo_name_lbl)
        promo_l.addWidget(instr_lbl)
        card_l.addWidget(promo_panel)

        lbl_text = etiqueta if etiqueta else "Credential ID"
        if not requiere:
            lbl_text += "  (Optional)"
        card_l.addWidget(_lbl(lbl_text.upper(), "LblMeta"))
        self.inp_id = QLineEdit()
        self.inp_id.setPlaceholderText(f"Enter {etiqueta}…")
        self.inp_id.setFixedHeight(46)
        self.inp_id.returnPressed.connect(self._do_confirm)
        card_l.addWidget(self.inp_id)

        self.err_lbl = _lbl("")
        self.err_lbl.setStyleSheet("color:#FF4C4C;font-size:12px;background:transparent;")
        self.err_lbl.setVisible(False)
        card_l.addWidget(self.err_lbl)

        card_l.addSpacing(4)
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("BtnChampagne")
        btn_cancel.setFixedWidth(110)
        btn_cancel.clicked.connect(self.reject)
        btn_confirm = QPushButton("APPLY DISCOUNT  →")
        btn_confirm.setObjectName("BtnSuccess")
        btn_confirm.setFixedHeight(46)
        btn_confirm.setMinimumWidth(180)
        btn_confirm.clicked.connect(self._do_confirm)
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(btn_confirm)
        card_l.addLayout(btn_row)

        root.addWidget(card)
        root.setSizeConstraint(QVBoxLayout.SetFixedSize)
        self.inp_id.setFocus()
        self._requiere = requiere

    def _do_confirm(self):
        val = self.inp_id.text().strip()
        if self._requiere and not val:
            self.err_lbl.setText(f"An identifier is required to apply this promotion.")
            self.err_lbl.setVisible(True)
            return
        self._identifier = val
        self.accept()

    def get_identifier(self) -> str:
        return self._identifier


# ─── Promotions Dialog ────────────────────────────────────────────────────────
class PromotionsDialog(QDialog):
    """
    Central promotion management dialog for the POS.
    Shows automatic promotions (read-only), eligibility promotions,
    promo code entry, and supervisor-authorized manual discount.
    Returns a list of applied promotion dicts on accept.
    """
    def __init__(self, pos_service, sincronizador, carrito, existing_promos, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Promotions & Discounts")
        self.setMinimumSize(620, 640)
        self.setStyleSheet(STYLESHEET)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.pos = pos_service
        self.sincronizador = sincronizador
        self.carrito = carrito
        # Mutable working copy of applied promotions
        self._working = list(existing_promos)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        outer = _card()
        outer_l = QVBoxLayout(outer)
        outer_l.setContentsMargins(0, 0, 0, 0)
        outer_l.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = QFrame()
        hdr.setObjectName("SplitHdr")
        hdr_l = QVBoxLayout(hdr)
        hdr_l.setContentsMargins(28, 20, 28, 16)
        hdr_l.setSpacing(6)

        title_row = QHBoxLayout()
        icon_lbl = _lbl("🏷️")
        icon_lbl.setStyleSheet("font-size:20px;background:transparent;")
        title_lbl = _lbl("PROMOTIONS & DISCOUNTS", "LblTitle")
        close_btn = QPushButton("✕")
        close_btn.setObjectName("BtnClose")
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(self.reject)
        title_row.addWidget(icon_lbl)
        title_row.addSpacing(6)
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        title_row.addWidget(close_btn)
        hdr_l.addLayout(title_row)

        sub_lbl = _lbl("Only promotions that follow authorization and audit requirements may be applied.", "LblMeta")
        sub_lbl.setWordWrap(True)
        hdr_l.addWidget(sub_lbl)
        outer_l.addWidget(hdr)

        # ── Scrollable body ───────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        body = QWidget()
        body.setStyleSheet("background:transparent;")
        body_l = QVBoxLayout(body)
        body_l.setContentsMargins(28, 18, 28, 18)
        body_l.setSpacing(16)

        # ── Section: Automatic Promotions ─────────────────────────────────────
        auto_promos = self.pos.obtener_promociones_automaticas_activas()
        auto_sec = self._make_section("⚡  AUTOMATIC PROMOTIONS")
        auto_body_l = QVBoxLayout()
        auto_body_l.setSpacing(6)
        auto_body_l.setContentsMargins(0, 8, 0, 4)
        if auto_promos:
            for ap in auto_promos:
                row = QHBoxLayout()
                nm = _lbl(ap['nombre'])
                nm.setStyleSheet(f"color:{CLR_TEXT};font-weight:600;font-size:13px;background:transparent;")
                val_str = f"{int(ap['valor'])}%" if ap['tipo_descuento'] == 'PORCENTAJE' else money(ap['valor'])
                if ap.get('aplica_happy_hour'):
                    val_str += f"  •  {ap.get('hora_inicio_hh','')}–{ap.get('hora_fin_hh','')}"
                vl = _lbl(val_str)
                vl.setStyleSheet("color:#00B4A0;font-weight:700;font-size:13px;background:transparent;")
                row.addWidget(nm)
                row.addStretch()
                row.addWidget(vl)
                auto_body_l.addLayout(row)
        else:
            no_lbl = _lbl("No automatic promotions are currently active.")
            no_lbl.setStyleSheet(f"color:{CLR_TEXT_DIM};font-size:13px;background:transparent;")
            auto_body_l.addWidget(no_lbl)
        note_lbl = _lbl("These are applied automatically by the system. No action required.")
        note_lbl.setStyleSheet(f"color:{CLR_TEXT_DIM};font-size:11px;background:transparent;")
        auto_body_l.addWidget(note_lbl)
        auto_sec_inner = auto_sec.findChild(QFrame, "PromoPanelSection")
        if auto_sec_inner:
            for i in range(auto_body_l.count()):
                item = auto_body_l.itemAt(i)
                if item.widget():
                    auto_sec_inner.layout().addWidget(item.widget())
                elif item.layout():
                    auto_sec_inner.layout().addLayout(item.layout())
        body_l.addWidget(auto_sec)

        # ── Section: Eligibility Promotions ───────────────────────────────────
        eleg_promos = self.pos.obtener_promociones_elegibilidad()
        eleg_sec = self._make_section("🎫  ELIGIBILITY PROMOTIONS")
        eleg_inner = eleg_sec.findChild(QFrame, "PromoPanelSection")
        if eleg_promos:
            for ep in eleg_promos:
                ep_row = QFrame()
                ep_row_l = QHBoxLayout(ep_row)
                ep_row_l.setContentsMargins(0, 4, 0, 4)
                ep_row_l.setSpacing(8)

                ep_info = QVBoxLayout()
                ep_info.setSpacing(2)
                ep_nm = _lbl(ep['nombre'])
                ep_nm.setStyleSheet(f"color:{CLR_TEXT};font-weight:700;font-size:13px;background:transparent;")
                val_str = f"{int(ep['valor'])}%" if ep['tipo_descuento'] == 'PORCENTAJE' else money(ep['valor'])
                ep_id_lbl = _lbl(f"{ep['etiqueta_identificador']}  •  {val_str}")
                ep_id_lbl.setStyleSheet(f"color:{CLR_TEXT_MID};font-size:12px;background:transparent;")
                ep_info.addWidget(ep_nm)
                ep_info.addWidget(ep_id_lbl)
                ep_row_l.addLayout(ep_info)
                ep_row_l.addStretch()

                # Check if already applied
                already = any(
                    p.get('id') == ep['id'] and p.get('tipo') == 'ELEGIBILIDAD'
                    for p in self._working
                )
                if already:
                    applied_lbl = _lbl("✓ Applied")
                    applied_lbl.setStyleSheet("color:#00B4A0;font-weight:800;font-size:12px;background:transparent;")
                    ep_row_l.addWidget(applied_lbl)
                else:
                    apply_btn = QPushButton("Apply")
                    apply_btn.setObjectName("BtnPromo")
                    apply_btn.setFixedSize(90, 34)
                    apply_btn.clicked.connect(lambda checked, e=ep: self._apply_eligibility(e))
                    ep_row_l.addWidget(apply_btn)

                if eleg_inner:
                    eleg_inner.layout().addWidget(ep_row)
        else:
            no_e = _lbl("No eligibility promotions configured. Set them up in CORE.")
            no_e.setStyleSheet(f"color:{CLR_TEXT_DIM};font-size:13px;background:transparent;")
            if eleg_inner:
                eleg_inner.layout().addWidget(no_e)
        body_l.addWidget(eleg_sec)

        # ── Section: Promo Code ───────────────────────────────────────────────
        code_sec = self._make_section("🏷️  PROMO CODE")
        code_inner = code_sec.findChild(QFrame, "PromoPanelSection")
        if code_inner:
            code_note = _lbl("Enter a promo code. Only one code per transaction is permitted.")
            code_note.setStyleSheet(f"color:{CLR_TEXT_MID};font-size:12px;background:transparent;")
            code_inner.layout().addWidget(code_note)

            code_input_row = QHBoxLayout()
            self.inp_code = QLineEdit()
            self.inp_code.setPlaceholderText("PROMO CODE")
            self.inp_code.setFixedHeight(40)
            self.inp_code.returnPressed.connect(self._apply_promo_code)
            code_input_row.addWidget(self.inp_code, 1)
            self.btn_validate_code = QPushButton("Validate")
            self.btn_validate_code.setObjectName("BtnPromo")
            self.btn_validate_code.setFixedSize(100, 40)
            self.btn_validate_code.clicked.connect(self._apply_promo_code)
            code_input_row.addWidget(self.btn_validate_code)
            code_inner.layout().addLayout(code_input_row)

            self.lbl_code_result = _lbl("")
            self.lbl_code_result.setStyleSheet("font-size:12px;font-weight:700;background:transparent;")
            self.lbl_code_result.setVisible(False)
            code_inner.layout().addWidget(self.lbl_code_result)

            # Pre-fill if code already applied
            for p in self._working:
                if p.get('tipo') == 'CODIGO_PROMO':
                    self.inp_code.setText(p.get('nombre', '').replace("Promo Code: ", ""))
                    self.lbl_code_result.setText(f"✓ Code applied: {p.get('nombre','')}")
                    self.lbl_code_result.setStyleSheet("color:#00B4A0;font-size:12px;font-weight:700;background:transparent;")
                    self.lbl_code_result.setVisible(True)
                    self.inp_code.setEnabled(False)
                    self.btn_validate_code.setEnabled(False)
                    break
        body_l.addWidget(code_sec)

        # ── Section: Manual Discount (Supervisor Required) ────────────────────
        manual_sec = self._make_section("🔐  MANUAL DISCOUNT  —  SUPERVISOR REQUIRED")
        manual_inner = manual_sec.findChild(QFrame, "PromoPanelSection")
        if manual_inner:
            manual_note = _lbl(
                "A supervisor must be physically present and authorize this discount using their email, "
                "password, and Google Authenticator OTP. Authorization expires after this transaction."
            )
            manual_note.setStyleSheet(f"color:{CLR_TEXT_MID};font-size:12px;background:transparent;")
            manual_note.setWordWrap(True)
            manual_inner.layout().addWidget(manual_note)

            self.manual_auth_widget = QWidget()
            self.manual_auth_widget.setStyleSheet("background:transparent;")
            mal = QVBoxLayout(self.manual_auth_widget)
            mal.setContentsMargins(0, 6, 0, 0)
            mal.setSpacing(8)

            manual_lbl = _lbl("DISCOUNT AMOUNT ($  or  %)", "LblMeta")
            self.inp_manual_disc = QLineEdit()
            self.inp_manual_disc.setPlaceholderText("Ex: 150  or  10%")
            self.inp_manual_disc.setFixedHeight(40)
            mal.addWidget(manual_lbl)
            mal.addWidget(self.inp_manual_disc)

            self.manual_auth_widget.setVisible(False)  # shown after auth

            self.btn_request_auth = QPushButton("Request Supervisor Authorization")
            self.btn_request_auth.setObjectName("BtnChampagne")
            self.btn_request_auth.setFixedHeight(42)

            # If already authorized in this session
            existing_manual = next((p for p in self._working if p.get('tipo') == 'MANUAL'), None)
            if existing_manual:
                self.manual_auth_widget.setVisible(True)
                self.btn_request_auth.setVisible(False)
                self.inp_manual_disc.setText(
                    f"{int(existing_manual.get('valor', 0))}%" if existing_manual.get('tipo_descuento') == 'PORCENTAJE'
                    else f"{existing_manual.get('valor', 0)}"
                )
                auth_done_lbl = _lbl(f"✓ Authorized by {existing_manual.get('supervisor_nombre', 'Supervisor')}")
                auth_done_lbl.setStyleSheet("color:#00B4A0;font-weight:800;font-size:12px;background:transparent;")
                mal.insertWidget(0, auth_done_lbl)
            else:
                self.btn_request_auth.clicked.connect(self._request_supervisor_auth)

            manual_inner.layout().addWidget(self.btn_request_auth)
            manual_inner.layout().addWidget(self.manual_auth_widget)
            self._manual_inner = manual_inner
        body_l.addWidget(manual_sec)
        body_l.addStretch()
        scroll.setWidget(body)
        outer_l.addWidget(scroll, 1)

        # ── Footer ────────────────────────────────────────────────────────────
        foot = QFrame()
        foot.setObjectName("SplitFooter")
        foot_l = QHBoxLayout(foot)
        foot_l.setContentsMargins(28, 14, 28, 14)
        foot_l.setSpacing(12)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("BtnChampagne")
        btn_cancel.clicked.connect(self.reject)

        self.btn_done = QPushButton("APPLY & CLOSE  →")
        self.btn_done.setObjectName("BtnSuccess")
        self.btn_done.setFixedHeight(48)
        self.btn_done.setMinimumWidth(200)
        self.btn_done.clicked.connect(self._finalize)
        foot_l.addWidget(btn_cancel)
        foot_l.addStretch()
        foot_l.addWidget(self.btn_done)
        outer_l.addWidget(foot)

        root.addWidget(outer)

    def _make_section(self, title: str) -> QFrame:
        """Create a titled section frame with an inner PromoPanelSection."""
        outer_frame = QFrame()
        outer_frame.setStyleSheet("background:transparent;")
        outer_l = QVBoxLayout(outer_frame)
        outer_l.setContentsMargins(0, 0, 0, 0)
        outer_l.setSpacing(6)

        title_lbl = _lbl(title, "LblMeta")
        title_lbl.setStyleSheet(f"color:{CLR_TEXT_MID};font-size:11px;font-weight:700;letter-spacing:1.5px;background:transparent;")
        outer_l.addWidget(title_lbl)

        inner = QFrame()
        inner.setObjectName("PromoPanelSection")
        inner_l = QVBoxLayout(inner)
        inner_l.setContentsMargins(16, 14, 16, 14)
        inner_l.setSpacing(8)
        outer_l.addWidget(inner)
        return outer_frame

    def _apply_eligibility(self, ep: dict):
        dlg = EligibilityIdentifierDialog(
            promo_nombre=ep['nombre'],
            etiqueta=ep['etiqueta_identificador'],
            requiere=ep['requiere_identificador'],
            parent=self
        )
        if dlg.exec() == QDialog.Accepted:
            identifier = dlg.get_identifier()
            # Remove any existing eligibility promotion from same entry
            self._working = [p for p in self._working if not (p.get('tipo') == 'ELEGIBILIDAD' and p.get('id') == ep['id'])]
            subtotal = sum(float(it['precio']) * it['cant'] for it in self.carrito)
            if ep['tipo_descuento'] == 'PORCENTAJE':
                monto = subtotal * ep['valor'] / 100.0
            else:
                monto = min(ep['valor'], subtotal)
            self._working.append({
                'id': ep['id'],
                'nombre': ep['nombre'],
                'tipo': 'ELEGIBILIDAD',
                'tipo_descuento': ep['tipo_descuento'],
                'valor': ep['valor'],
                'monto': round(monto, 2),
                'identificador': identifier,
                'supervisor_id': None,
                'supervisor_nombre': None,
                'codigo_id': None,
            })
            self.accept()  # Close and apply immediately

    def _apply_promo_code(self):
        codigo = self.inp_code.text().strip().upper()
        if not codigo:
            self.lbl_code_result.setText("Please enter a promo code.")
            self.lbl_code_result.setStyleSheet(f"color:{CLR_ERROR};font-size:12px;font-weight:700;background:transparent;")
            self.lbl_code_result.setVisible(True)
            return
        # Check if a code is already applied
        if any(p.get('tipo') == 'CODIGO_PROMO' for p in self._working):
            self.lbl_code_result.setText("Only one promo code per transaction is allowed.")
            self.lbl_code_result.setStyleSheet(f"color:{CLR_ERROR};font-size:12px;font-weight:700;background:transparent;")
            self.lbl_code_result.setVisible(True)
            return
        self.btn_validate_code.setEnabled(False)
        self.btn_validate_code.setText("Checking…")
        subtotal = sum(float(it['precio']) * it['cant'] for it in self.carrito)
        try:
            result = self.sincronizador.validar_codigo_promo(codigo, subtotal)
        except Exception as e:
            result = {"valido": False, "error": str(e)}
        self.btn_validate_code.setEnabled(True)
        self.btn_validate_code.setText("Validate")
        if result.get("valido"):
            if result['tipo_descuento'] == 'PORCENTAJE':
                monto = subtotal * result['valor'] / 100.0
            else:
                monto = min(result['valor'], subtotal)
            self._working.append({
                'id': result.get('promocion_id'),
                'nombre': f"Promo Code: {codigo}",
                'tipo': 'CODIGO_PROMO',
                'tipo_descuento': result['tipo_descuento'],
                'valor': result['valor'],
                'monto': round(monto, 2),
                'identificador': codigo,
                'supervisor_id': None,
                'supervisor_nombre': None,
                'codigo_id': result.get('codigo_id'),
            })
            self.lbl_code_result.setText(f"✓ Code valid: {result.get('nombre','')}  —  {result['valor']}% discount")
            self.lbl_code_result.setStyleSheet("color:#00B4A0;font-size:12px;font-weight:700;background:transparent;")
            self.lbl_code_result.setVisible(True)
            self.inp_code.setEnabled(False)
            self.btn_validate_code.setEnabled(False)
        else:
            self.lbl_code_result.setText(f"✗ {result.get('error', 'Invalid promo code.')}")
            self.lbl_code_result.setStyleSheet(f"color:{CLR_ERROR};font-size:12px;font-weight:700;background:transparent;")
            self.lbl_code_result.setVisible(True)

    def _request_supervisor_auth(self):
        main_win = self.parent()
        if main_win and hasattr(main_win, 'supervisor_session_active') and main_win.supervisor_session_active:
            sup_info = {
                "supervisor_id": main_win.supervisor_id,
                "supervisor_nombre": main_win.supervisor_nombre
            }
            self._apply_auth_ui(sup_info)
            return

        dlg = SupervisorAuthDialog(self.sincronizador, "Manual Discount", parent=self)
        if dlg.exec() == QDialog.Accepted:
            sup_info = dlg.get_supervisor_info()
            if main_win and hasattr(main_win, 'start_supervisor_session'):
                main_win.start_supervisor_session(
                    sup_info.get("supervisor_id"), 
                    sup_info.get("supervisor_nombre", "Supervisor")
                )
            self._apply_auth_ui(sup_info)

    def _apply_auth_ui(self, sup_info: dict):
        self.manual_auth_widget.setVisible(True)
        self.btn_request_auth.setVisible(False)
        auth_lbl = _lbl(f"✓ Authorized by {sup_info.get('supervisor_nombre', 'Supervisor')}")
        auth_lbl.setStyleSheet("color:#00B4A0;font-weight:800;font-size:12px;background:transparent;")
        self._manual_inner.layout().insertWidget(0, auth_lbl)
        self._sup_info = sup_info

    def _finalize(self):
        """Collect manual discount and finalize working list."""
        # Process manual discount if panel is visible
        if hasattr(self, 'manual_auth_widget') and self.manual_auth_widget.isVisible():
            disc_text = self.inp_manual_disc.text().strip()
            if disc_text:
                subtotal = sum(float(it['precio']) * it['cant'] for it in self.carrito)
                sup_info = getattr(self, '_sup_info', {})
                # Parse discount
                try:
                    if disc_text.endswith('%'):
                        pct = float(disc_text[:-1]) / 100.0
                        monto = subtotal * pct
                        valor = float(disc_text[:-1])
                        tipo_d = 'PORCENTAJE'
                    else:
                        monto = min(float(disc_text), subtotal)
                        pct = monto / subtotal if subtotal > 0 else 0.0
                        valor = float(disc_text)
                        tipo_d = 'MONTO_FIJO'
                except ValueError:
                    AppMessageBox.warning(self, "Invalid Amount",
                                          "Please enter a valid discount amount (e.g. 150 or 10%).")
                    return
                # Remove any existing manual discount
                self._working = [p for p in self._working if p.get('tipo') != 'MANUAL']
                self._working.append({
                    'id': None,
                    'nombre': f"Manual Discount ({disc_text})",
                    'tipo': 'MANUAL',
                    'tipo_descuento': tipo_d,
                    'valor': valor,
                    'monto': round(monto, 2),
                    '_pct': pct,
                    'identificador': disc_text,
                    'supervisor_id': sup_info.get('supervisor_id'),
                    'supervisor_nombre': sup_info.get('supervisor_nombre'),
                    'codigo_id': None,
                })
        self.accept()

    def get_applied_promotions(self) -> list:
        return self._working


# ─── Main Window ──────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pos  = POSService()
        self.sincronizador = SyncService()

        self.carrito = []
        self.ventas_turno = 0.0
        self.fondo_inicial = 0.0
        self._mesas_dialog = None
        self._auto_sync_counter = 0
        self._current_sync_callback = None
        self._post_sale_stock_delay_s = 2.0
        self._stock_cooldown_until = 0.0

        # ── New feature state ────────────────────────────────────────────────
        self.held_orders = []          # list of saved cart dicts
        self.happy_hour_active = False
        self.happy_hour_discount = 0.15  # 15% discount
        self.happy_hour_start = 18       # 18:00
        self.happy_hour_end   = 21       # 21:00
        self._btn_hh = None              # reference to Happy Hour chip button
        self._btn_hold_indicator = None  # reference to held orders count label

        # ── Supervisor Authorization Mode State ──────────────────────────────
        self.supervisor_session_active = False
        self.supervisor_id = None
        self.supervisor_nombre = None
        self.supervisor_session_timer = QTimer(self)
        self.supervisor_session_timer.timeout.connect(self.tick_supervisor_session)
        self.supervisor_session_seconds_left = 0
        self._lbl_supervisor_mode = None
        self._btn_end_supervisor = None
        self._active_session_db_id = None

        # ── Applied promotions (structured discount model) ───────────────────
        # Each entry: {'id': int|None, 'nombre': str, 'tipo': str,
        #              'tipo_descuento': str, 'valor': float,
        #              'monto': float, 'identificador': str|None,
        #              'supervisor_id': int|None, 'supervisor_nombre': str|None,
        #              'codigo_id': int|None}
        self._applied_promotions = []

        # ── Background workers ────────────────────────────────────────────────
        self._sync_thread = QThread(self)
        self._sync_worker = SyncWorker(self.sincronizador)
        self._sync_worker.moveToThread(self._sync_thread)
        self._sync_worker.request.connect(self._sync_worker.on_request)
        self._sync_worker.finished.connect(self._on_sync_result)
        self._sync_thread.start()

        self.product_buttons = {}
        self._live_stock_cache = {}
        self._stock_thread = QThread(self)
        self._stock_worker = StockWorker(self.sincronizador)
        self._stock_worker.moveToThread(self._stock_thread)
        self._stock_worker.request.connect(self._stock_worker.on_request)
        self._stock_worker.finished.connect(self._on_stock_result)
        self._stock_thread.start()

        # ── Window setup ─────────────────────────────────────────────────────
        self.setMinimumSize(1100, 750)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.showMaximized()
        self.setWindowTitle("MASTER POS SYSTEM — CASH TERMINAL")
        self.setStyleSheet(STYLESHEET)
        
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        title_bar = QFrame()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet(f"background-color: {CLR_SURFACE_HIGH}; border-bottom: 1px solid {CLR_BORDER};")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)
        title_layout.setSpacing(10)
        
        icon_lbl = QLabel("🛒")
        icon_lbl.setStyleSheet(f"font-size: 18px; color: {CLR_EMBER}; background: transparent;")
        title_layout.addWidget(icon_lbl)
        
        title_lbl = QLabel("MASTER POS SYSTEM — CASH TERMINAL")
        title_lbl.setStyleSheet(f"font-weight: 800; color: {CLR_EMBER}; font-size: 14px; background: transparent;")
        title_layout.addWidget(title_lbl)
        title_layout.addStretch()
        
        btn_min = QPushButton("—")
        btn_max = QPushButton("◻")
        btn_close = QPushButton("✕")
        for btn in (btn_min, btn_max, btn_close):
            btn.setFixedSize(46, 32)
            btn.setStyleSheet(f"QPushButton {{ background: transparent; border: none; color: {CLR_TEXT}; font-size: 14px; font-family: 'Segoe UI', sans-serif; padding-bottom: 2px; }} QPushButton:hover {{ background: rgba(255,255,255,0.1); }}")
            title_layout.addWidget(btn)
        
        btn_close.setStyleSheet(f"QPushButton {{ background: transparent; border: none; color: {CLR_TEXT}; font-size: 14px; font-family: 'Segoe UI', sans-serif; padding-bottom: 2px; }} QPushButton:hover {{ background: #E81123; color: white; }}")
        
        btn_min.clicked.connect(self.showMinimized)
        btn_max.clicked.connect(lambda: self.showNormal() if self.isMaximized() else self.showMaximized())
        btn_close.clicked.connect(self.close)
        
        main_layout.addWidget(title_bar)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 1)
        self.setCentralWidget(main_widget)
        self.init_login()
        self.init_apertura()
        self.init_ventas()

        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self.auto_sync)
        self.auto_sync()

        self.stock_timer = QTimer(self)
        self.stock_timer.timeout.connect(self.request_stock_update)

    # ─────────────────────────────────────────────────────────────────────────
    # Screens
    # ─────────────────────────────────────────────────────────────────────────
    def init_login(self):
        page = QWidget()
        page.setObjectName("PageBg")
        outer = QVBoxLayout(page)
        outer.setAlignment(Qt.AlignCenter)

        card = _card()
        card.setFixedSize(480, 440)
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(44, 44, 44, 44)
        card_l.setSpacing(14)

        # Logo / Title
        logo = _lbl("MASTER POS", align=Qt.AlignCenter)
        logo.setStyleSheet(
            f"color: {CLR_EMBER}; font-size: 32px; font-weight: 900; margin-bottom: -10px; background: transparent;"
        )
        card_l.addWidget(logo)

        title = _lbl("TERMINAL AUTHENTICATION", "LblTitle", Qt.AlignCenter)
        card_l.addWidget(title)

        sub = _lbl("Enter your credentials to continue", "LblSubtitle",
                   Qt.AlignCenter)
        card_l.addWidget(sub)
        card_l.addWidget(_hdiv())
        card_l.addSpacing(8)

        card_l.addWidget(_lbl("EMAIL ADDRESS", "LblMeta"))
        self.u = QLineEdit()
        self.u.setPlaceholderText("cashier@email.com")
        self.u.setFixedHeight(46)
        card_l.addWidget(self.u)

        card_l.addWidget(_lbl("PASSWORD", "LblMeta"))
        self.p = QLineEdit()
        self.p.setPlaceholderText("••••••••")
        self.p.setEchoMode(QLineEdit.Password)
        self.p.setFixedHeight(46)
        self.p.returnPressed.connect(self.do_login)
        card_l.addWidget(self.p)

        card_l.addSpacing(12)
        btn = QPushButton("AUTHENTICATE  →")
        btn.setObjectName("BtnSuccess")
        btn.setFixedHeight(50)
        btn.clicked.connect(self.do_login)
        card_l.addWidget(btn)

        outer.addWidget(card)
        self.stack.addWidget(page)

    def init_apertura(self):
        page = QWidget()
        page.setObjectName("PageBg")
        outer = QVBoxLayout(page)
        outer.setAlignment(Qt.AlignCenter)

        card = _card()
        card.setFixedSize(480, 360)
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(44, 44, 44, 44)
        card_l.setSpacing(14)

        title = _lbl("CASH DECLARATION", "LblTitle", Qt.AlignCenter)
        card_l.addWidget(title)

        sub = _lbl("Enter the initial cash in the drawer to open the register",
                   "LblSubtitle", Qt.AlignCenter)
        card_l.addWidget(sub)
        card_l.addWidget(_hdiv())
        card_l.addSpacing(6)

        card_l.addWidget(_lbl("INITIAL CASH IN DRAWER ($)", "LblMeta"))
        self.f = QLineEdit()
        self.f.setPlaceholderText("Ex. 5,000.00")
        self.f.setFixedHeight(46)
        self.f.returnPressed.connect(self.do_apertura)
        card_l.addWidget(self.f)

        card_l.addSpacing(12)
        btn = QPushButton("OPEN REGISTER  →")
        btn.setObjectName("BtnSuccess")
        btn.setFixedHeight(50)
        btn.clicked.connect(self.do_apertura)
        card_l.addWidget(btn)

        outer.addWidget(card)
        self.stack.addWidget(page)

    def init_ventas(self):
        page = QWidget()
        page.setObjectName("PageBg")
        main_l = QVBoxLayout(page)
        main_l.setContentsMargins(0, 0, 0, 0)
        main_l.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────────────
        hdr = QFrame()
        hdr.setObjectName("HeaderFrame")
        hdr.setFixedHeight(64)
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(20, 0, 20, 0)
        hdr_l.setSpacing(16)

        # Telemetry
        self.lbl_fondo   = _lbl("FUND: $ 0.00", "LblFund")
        self.lbl_ventas  = _lbl("SALES: $ 0.00", "LblSales")
        self.lbl_esperado= _lbl("REGISTER: $ 0.00", "LblExpect")
        
        # Style them to look like flat buttons / chips
        for lbl in (self.lbl_fondo, self.lbl_ventas, self.lbl_esperado):
            lbl.setStyleSheet(lbl.styleSheet() + "font-size:14px;font-weight:800;background-color:rgba(255,255,255,0.05);padding:8px 12px;border-radius:6px;qproperty-alignment:AlignCenter;")
            
        hdr_l.addWidget(self.lbl_fondo)
        hdr_l.addWidget(self.lbl_ventas)
        hdr_l.addWidget(self.lbl_esperado)

        # Happy Hour live indicator
        self.lbl_hh_active = _lbl("HAPPY HOUR", "LblHHActive")
        self.lbl_hh_active.setVisible(False)
        hdr_l.addWidget(self.lbl_hh_active)

        # Supervisor Mode UI
        self._lbl_supervisor_mode = _lbl("SUPERVISOR MODE: 00:00")
        self._lbl_supervisor_mode.setStyleSheet("color:#FFAA00;font-size:14px;font-weight:800;background-color:rgba(255,170,0,0.1);padding:8px 12px;border-radius:6px;border:1px solid #FFAA00;")
        self._lbl_supervisor_mode.setVisible(False)
        hdr_l.addWidget(self._lbl_supervisor_mode)

        self._btn_end_supervisor = QPushButton("End Session")
        self._btn_end_supervisor.setObjectName("BtnDanger")
        self._btn_end_supervisor.setFixedHeight(38)
        self._btn_end_supervisor.setVisible(False)
        self._btn_end_supervisor.clicked.connect(lambda: self.end_supervisor_session("MANUAL_REVOKE"))
        hdr_l.addWidget(self._btn_end_supervisor)

        hdr_l.addStretch()

        # Hold order controls
        self._btn_hold_count = QPushButton("HOLD  (0)")
        self._btn_hold_count.setObjectName("BtnHold")
        self._btn_hold_count.setFixedHeight(38)
        self._btn_hold_count.clicked.connect(self.do_resume_orders)

        btn_hold_new = QPushButton("+ Hold Order")
        btn_hold_new.setObjectName("BtnHold")
        btn_hold_new.setFixedHeight(38)
        btn_hold_new.clicked.connect(self.do_hold_order)

        btn_mesas = QPushButton("ACTIVE TABLES")
        btn_mesas.setObjectName("BtnMesas")
        btn_mesas.setFixedHeight(38)
        btn_mesas.clicked.connect(self.do_abrir_mesas)

        btn_change = QPushButton("CHANGE CASHIER")
        btn_change.setObjectName("BtnChampagne")
        btn_change.setFixedHeight(38)
        btn_change.clicked.connect(self.do_change_cashier)

        btn_close = QPushButton("CLOSE REGISTER (Z)")
        btn_close.setObjectName("BtnDanger")
        btn_close.setFixedHeight(38)
        btn_close.clicked.connect(self.do_cierre_caja)

        for w in (btn_hold_new, self._btn_hold_count, btn_mesas, btn_change, btn_close):
            hdr_l.addWidget(w)

        main_l.addWidget(hdr)

        # ── Body ──────────────────────────────────────────────────────────────
        body = QWidget()
        body_l = QHBoxLayout(body)
        body_l.setContentsMargins(16, 16, 16, 16)
        body_l.setSpacing(16)

        # ══ LEFT PANEL ════════════════════════════════════════════════════════
        left_w = QWidget()
        left_l = QVBoxLayout(left_w)
        left_l.setContentsMargins(0, 0, 0, 0)
        left_l.setSpacing(10)

        # Search bar
        search_card = _card()
        search_card_l = QHBoxLayout(search_card)
        search_card_l.setContentsMargins(12, 6, 12, 6)
        self.search = QLineEdit()
        self.search.setObjectName("SearchInput")
        self.search.setPlaceholderText("SEARCH PRODUCTS...")
        self.search.textChanged.connect(self.on_typing)
        self.search.setFrame(False)
        self.search.setStyleSheet(
            f"background:transparent;border:none;color:{CLR_TEXT};font-size:15px;font-weight:600;padding:4px;"
        )
        search_card_l.addWidget(self.search, 1)
        left_l.addWidget(search_card)

        # Category chips + Happy Hour
        self.cat_scroll = QScrollArea()
        self.cat_scroll.setWidgetResizable(True)
        self.cat_scroll.setFixedHeight(52)
        self.cat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cat_scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")

        self.cat_container = QWidget()
        self.cat_container.setStyleSheet("background:transparent;")
        self.cat_layout = QHBoxLayout(self.cat_container)
        self.cat_layout.setContentsMargins(0, 4, 0, 4)
        self.cat_layout.setSpacing(8)
        self.cat_scroll.setWidget(self.cat_container)
        left_l.addWidget(self.cat_scroll)

        # Product grid
        self.prod_scroll = QScrollArea()
        self.prod_scroll.setWidgetResizable(True)
        self.prod_scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        self.prod_container = QWidget()
        self.prod_container.setStyleSheet("background:transparent;")
        self.prod_layout = QGridLayout(self.prod_container)
        self.prod_layout.setSpacing(10)
        self.prod_scroll.setWidget(self.prod_container)
        left_l.addWidget(self.prod_scroll, 1)

        # ── Bottom billing + payment row ──────────────────────────────────────
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)

        # Billing Details card
        billing_card = _card()
        billing_l = QVBoxLayout(billing_card)
        billing_l.setContentsMargins(16, 14, 16, 14)
        billing_l.setSpacing(8)
        billing_l.addWidget(_lbl("BILLING DETAILS", "LblMeta"))
        billing_l.addWidget(_hdiv())

        btn_split = QPushButton("SPLIT BILL")
        btn_split.setObjectName("BtnSplit")
        btn_split.setFixedHeight(38)
        btn_split.clicked.connect(self.do_split_bill)
        billing_l.addWidget(btn_split)

        self.txt_cliente = QLineEdit()
        self.txt_cliente.setPlaceholderText("Customer Name (Optional)")
        self.txt_cliente.setFixedHeight(38)
        billing_l.addWidget(self.txt_cliente)

        self.txt_notes = QLineEdit()
        self.txt_notes.setPlaceholderText("Order Notes (Optional)")
        self.txt_notes.setFixedHeight(38)
        billing_l.addWidget(self.txt_notes)

        self.cb_ncf = QComboBox()
        self.cb_ncf.addItems(["CONSUMER", "TAX CREDIT", "GOVERNMENT"])
        self.cb_ncf.setFixedHeight(38)
        billing_l.addWidget(self.cb_ncf)
        billing_l.addStretch()

        bottom_row.addWidget(billing_card, 1)

        # Payment details card
        payment_card = _card()
        payment_l = QVBoxLayout(payment_card)
        payment_l.setContentsMargins(16, 14, 16, 14)
        payment_l.setSpacing(8)
        payment_l.addWidget(_lbl("PAYMENT", "LblMeta"))
        payment_l.addWidget(_hdiv())

        payment_l.addWidget(_lbl("PAYMENT METHOD", "LblMeta"))
        self.cb_metodo = QComboBox()
        self.cb_metodo.addItems(["CASH", "CARD", "TRANSFER"])
        self.cb_metodo.setFixedHeight(38)
        self.cb_metodo.currentTextChanged.connect(self.on_payment_change)
        payment_l.addWidget(self.cb_metodo)

        payment_l.addWidget(_lbl("ADDITIONAL TIP ($)", "LblMeta"))
        self.txt_extra_tip = QLineEdit()
        self.txt_extra_tip.setPlaceholderText("0.00")
        self.txt_extra_tip.setFixedHeight(38)
        self.txt_extra_tip.textChanged.connect(self.update_totals)
        payment_l.addWidget(self.txt_extra_tip)

        self.btn_promotions = QPushButton("PROMOTIONS")
        self.btn_promotions.setObjectName("BtnPromo")
        self.btn_promotions.setFixedHeight(42)
        self.btn_promotions.clicked.connect(self.open_promotions_dialog)
        payment_l.addWidget(self.btn_promotions)
        payment_l.addStretch()

        bottom_row.addWidget(payment_card, 1)

        left_l.addLayout(bottom_row)
        body_l.addWidget(left_w, 3)

        # ══ RIGHT PANEL ═══════════════════════════════════════════════════════
        right_w = QWidget()
        right_l = QVBoxLayout(right_w)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.setSpacing(10)

        # Delete item button
        btn_delete = QPushButton("DELETE ITEM")
        btn_delete.setObjectName("BtnDanger")
        btn_delete.setFixedHeight(46)
        btn_delete.clicked.connect(self.do_delete_item)
        right_l.addWidget(btn_delete)

        # Cart table (with Notes column)
        cart_card = _card()
        cart_card_l = QVBoxLayout(cart_card)
        cart_card_l.setContentsMargins(0, 0, 0, 0)
        cart_card_l.setSpacing(0)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["PRODUCT", "QTY", "PRICE", "NOTES"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 140)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setShowGrid(False)
        cart_card_l.addWidget(self.table)
        right_l.addWidget(cart_card, 1)

        # Totals card
        totals_card = _card()
        totals_l = QVBoxLayout(totals_card)
        totals_l.setContentsMargins(20, 16, 20, 16)
        totals_l.setSpacing(8)

        # Sub-totals row
        sub_row = QHBoxLayout()
        sub_row.setSpacing(0)
        self.subtotal_lbl  = _lbl("SUBTOTAL: $ 0.00", "LblMeta")
        self.itbis_lbl     = _lbl("ITBIS (18%): $ 0.00", "LblMeta", Qt.AlignCenter)
        self.legaltip_lbl  = _lbl("TIP (10%): $ 0.00", "LblMeta", Qt.AlignRight)
        for l in (self.subtotal_lbl, self.itbis_lbl, self.legaltip_lbl):
            sub_row.addWidget(l, 1)
        totals_l.addLayout(sub_row)

        totals_l.addWidget(_hdiv())

        # Happy Hour discount line
        self.hh_discount_lbl = _lbl("", align=Qt.AlignCenter)
        self.hh_discount_lbl.setStyleSheet(
            f"color:{CLR_EMBER};font-size:13px;font-weight:700;"
        )
        self.hh_discount_lbl.setVisible(False)
        totals_l.addWidget(self.hh_discount_lbl)

        # Applied promotions badges area
        self._promo_badges_layout = QHBoxLayout()
        self._promo_badges_layout.setSpacing(6)
        self._promo_badges_layout.setContentsMargins(0, 0, 0, 0)
        self._promo_badges_widget = QWidget()
        self._promo_badges_widget.setStyleSheet("background:transparent;")
        self._promo_badges_widget.setLayout(self._promo_badges_layout)
        self._promo_badges_widget.setVisible(False)
        totals_l.addWidget(self._promo_badges_widget)

        # Grand total
        self.total_lbl = _lbl("TOTAL: $ 0.00", "LblTotal", Qt.AlignCenter)
        totals_l.addWidget(self.total_lbl)

        totals_l.addWidget(_hdiv())

        # Cash received
        self.cash = QLineEdit()
        self.cash.setObjectName("CashInput")
        self.cash.setPlaceholderText("Cash Received ($)")
        self.cash.setFixedHeight(52)
        self.cash.setAlignment(Qt.AlignCenter)
        totals_l.addWidget(self.cash)

        # Process & Bill
        btn_pago = QPushButton("PROCESS AND BILL")
        btn_pago.setObjectName("BtnSuccess")
        btn_pago.setFixedHeight(56)
        btn_pago.setStyleSheet(
            btn_pago.styleSheet() +
            f"font-size:16px;letter-spacing:1.5px;"
        )
        btn_pago.clicked.connect(self.do_pago)
        totals_l.addWidget(btn_pago)

        right_l.addWidget(totals_card)
        body_l.addWidget(right_w, 2)

        main_l.addWidget(body, 1)
        self.stack.addWidget(page)

        # Load initial data
        self.build_category_filters(self.pos.obtener_categorias())
        self.load_catalog()

    # ─────────────────────────────────────────────────────────────────────────
    # Utility
    # ─────────────────────────────────────────────────────────────────────────
    def show_info(self, title, msg):
        print(f"[{title}]: {msg}", flush=True)
        AppMessageBox.information(self, title, msg)

    def show_warning(self, title, msg):
        print(f"[{title}]: {msg}", flush=True)
        AppMessageBox.warning(self, title, msg)

    def show_error(self, title, msg):
        print(f"[{title}]: {msg}", flush=True)
        AppMessageBox.critical(self, title, msg)

    # ─────────────────────────────────────────────────────────────────────────
    # Catalog & Categories
    # ─────────────────────────────────────────────────────────────────────────
    def load_catalog(self, categoria=None, search_term=None):
        while self.prod_layout.count():
            item = self.prod_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if search_term:
            productos = self.pos.buscar_producto(search_term)
        else:
            productos = self.pos.obtener_productos(categoria)

        row, col, MAX_COLS = 0, 0, 5
        self.product_buttons.clear()
        in_cooldown = time.monotonic() < self._stock_cooldown_until
        
        # Load active auto promos for display
        auto_promos = self.pos.obtener_promociones_automaticas_activas()

        for p in productos:
            if in_cooldown:
                display_stock = p.stock_local
            else:
                display_stock = self._live_stock_cache.get(p.id_producto, p.stock_local)

            nuevo_precio, promos_aplicadas = self.pos.evaluar_precio_producto(
                producto_id=p.id_producto,
                categoria_id=p.id_categoria,
                precio_base=float(p.precio_actual),
                auto_promos=auto_promos,
                happy_hour_active=self.happy_hour_active
            )

            discount_str = ""
            if promos_aplicadas:
                promo = promos_aplicadas[0]
                val = int(float(promo.get('valor', 0)))
                if promo.get('tipo_descuento') == 'PORCENTAJE':
                    discount_str = f"{val}% OFF"
                else:
                    discount_str = f"-${val}"

            if nuevo_precio < float(p.precio_actual):
                btn_text = f"{discount_str}\n{p.nombre}\n{money(nuevo_precio)}\nStock: {display_stock}"
            else:
                btn_text = f"\n{p.nombre}\n{money(p.precio_actual)}\nStock: {display_stock}"

            btn = QPushButton(btn_text)
            
            btn.setObjectName("BtnProductPromo" if nuevo_precio < float(p.precio_actual) else "BtnProduct")
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.clicked.connect(
                lambda checked, prod=p, button=btn: self.agregar_a_tabla(prod, button)
            )
            self.prod_layout.addWidget(btn, row, col)
            self.product_buttons[p.id_producto] = (btn, p.nombre, float(p.precio_actual), nuevo_precio, discount_str)
            col += 1
            if col >= MAX_COLS:
                col = 0
                row += 1

        if self.sincronizador.token:
            self.request_stock_update()

    def build_category_filters(self, categorias):
        while self.cat_layout.count():
            item = self.cat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # ALL chip
        btn_all = QPushButton("ALL")
        btn_all.setObjectName("BtnCatActive")
        btn_all.setStyleSheet(f"background-color: {CLR_CHAMPAGNE}; color: {CLR_BG}; border: 1px solid {CLR_CHAMPAGNE}; border-radius: 20px; font-weight: 700;")
        btn_all.clicked.connect(lambda: self._set_category(None, btn_all))
        self.cat_layout.addWidget(btn_all)
        self._active_cat_btn = btn_all

        for c in categorias:
            cat_name = c.get("nombre") if isinstance(c, dict) else str(c)
            btn = QPushButton(cat_name)
            btn.setObjectName("BtnCat")
            btn.clicked.connect(
                lambda checked, cat=cat_name, b=btn: self._set_category(cat, b)
            )
            self.cat_layout.addWidget(btn)

        self.cat_layout.addStretch()

    def _set_category(self, cat_name, btn):
        if hasattr(self, '_active_cat_btn') and self._active_cat_btn:
            self._active_cat_btn.setStyleSheet("")
            self._active_cat_btn.setObjectName("BtnCat")
            self._active_cat_btn.style().unpolish(self._active_cat_btn)
            self._active_cat_btn.style().polish(self._active_cat_btn)
            
        btn.setStyleSheet(f"background-color: {CLR_CHAMPAGNE}; color: {CLR_BG}; border: 1px solid {CLR_CHAMPAGNE}; border-radius: 20px; font-weight: 700;")
        self._active_cat_btn = btn
        self.load_catalog(cat_name)

    # ─────────────────────────────────────────────────────────────────────────
    # Happy Hour
    # ─────────────────────────────────────────────────────────────────────────
    def _update_happy_hour_ui(self, is_active, discount):
        changed = False
        if self.happy_hour_active != is_active:
            self.happy_hour_active = is_active
            changed = True
        if self.happy_hour_discount != discount:
            self.happy_hour_discount = discount
            changed = True
            
        if changed:
            if hasattr(self, 'lbl_hh_active'):
                self.lbl_hh_active.setVisible(self.happy_hour_active)
            if hasattr(self, 'hh_discount_lbl'):
                self.hh_discount_lbl.setVisible(self.happy_hour_active)
                if self.happy_hour_active:
                    self.hh_discount_lbl.setText(
                        f"HAPPY HOUR  —  {int(self.happy_hour_discount * 100)}% DISCOUNT APPLIED"
                    )
            self.update_totals()

    # ─────────────────────────────────────────────────────────────────────────
    # Cart Operations
    # ─────────────────────────────────────────────────────────────────────────
    def agregar_a_tabla(self, p, source_btn=None):
        precio_final = float(p.precio_actual)
        if p.id_producto in self.product_buttons:
            _, _, _, nuevo_precio, _ = self.product_buttons[p.id_producto]
            precio_final = float(nuevo_precio)

        # Button flash
        if source_btn:
            orig_style = getattr(source_btn, '_base_style', None)
            if orig_style is None:
                orig_style = source_btn.styleSheet()
                source_btn._base_style = orig_style
            source_btn.setStyleSheet(
                orig_style +
                f"background-color:rgba(255,107,0,0.25);border-color:{CLR_EMBER};"
            )
            QTimer.singleShot(160, lambda: self._reset_btn_style(source_btn, orig_style))

        idx = next(
            (i for i, it in enumerate(self.carrito) if it["id"] == p.id_producto),
            None
        )
        if idx is not None:
            # Increment qty — stock check
            if p.stock_local != 9999 and self.carrito[idx]['cant'] + 1 > p.stock_local:
                self.show_warning(
                    "Stock Limit Reached",
                    f"Cannot add more '{p.nombre}'. Only {p.stock_local} in stock."
                )
                return
            self.carrito[idx]['cant'] += 1
            self.table.item(idx, 1).setText(str(self.carrito[idx]['cant']))
        else:
            # New product — stock check
            if p.stock_local != 9999 and p.stock_local < 1:
                self.show_warning("Out of Stock", f"'{p.nombre}' is out of stock.")
                return

            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(p.nombre))
            self.table.setItem(row, 1, QTableWidgetItem("1"))
            self.table.setItem(row, 2, QTableWidgetItem(money(precio_final)))

            # Notes button
            notes_btn = QPushButton("+ NOTE")
            notes_btn.setObjectName("BtnNotes")
            notes_btn.setCursor(QCursor(Qt.PointingHandCursor))
            notes_btn.clicked.connect(
                lambda checked, r=row: self.open_modifier_for_row(r)
            )
            self.table.setCellWidget(row, 3, notes_btn)

            self.carrito.append({
                'id': p.id_producto,
                'nombre': p.nombre,
                'precio': p.precio_actual,
                'precio_final': precio_final,
                'cant': 1,
                'tasa': p.tasa_impuesto,
                'stock': p.stock_local,
                'notas_item': []
            })

        self.update_totals()

    def _reset_btn_style(self, btn, orig_style):
        try:
            btn.setStyleSheet(orig_style)
        except RuntimeError:
            pass

    def open_modifier_for_row(self, row):
        if row < 0 or row >= len(self.carrito):
            return
        item_data = self.carrito[row]
        modifiers = self.pos.obtener_modificadores_producto(
            item_data['id'], sincronizador=self.sincronizador
        )
        dlg = ItemModifierDialog(
            product_name=item_data['nombre'],
            product_id=item_data['id'],
            modifiers=modifiers,
            current_notes=item_data.get('notas_item', []),
            parent=self
        )
        if dlg.exec() == QDialog.Accepted:
            self.carrito[row]['notas_item'] = dlg.get_notes()
            self._refresh_notes_cell(row)

    def _refresh_notes_cell(self, row):
        if row < 0 or row >= len(self.carrito):
            return
        notas = self.carrito[row].get('notas_item', [])
        btn = self.table.cellWidget(row, 3)
        if btn:
            if notas:
                text = ', '.join(notas)
                btn.setText(text[:18] + '…' if len(text) > 18 else text)
                btn.setObjectName("BtnNotesActive")
            else:
                btn.setText("+ NOTE")
                btn.setObjectName("BtnNotes")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def do_delete_item(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self.carrito.pop(row)
            self.update_totals()
            self.search.setFocus()
        else:
            self.show_warning("Attention", "Select a row in the table to delete.")

    # ─────────────────────────────────────────────────────────────────────────
    # Hold Orders
    # ─────────────────────────────────────────────────────────────────────────
    def do_hold_order(self):
        if not self.carrito:
            self.show_warning("Empty Cart", "No items in cart to hold.")
            return
        ts = get_local_now().strftime("%H:%M:%S")
        held = {
            'carrito': list(self.carrito),
            'cliente': self.txt_cliente.text().strip(),
            'notas': self.txt_notes.text().strip(),
            'ncf': self.cb_ncf.currentText(),
            'metodo': self.cb_metodo.currentText(),
            'extra_tip': self.txt_extra_tip.text().strip(),
            'timestamp': ts,
        }
        self.held_orders.append(held)
        self._update_hold_btn()

        # Clear current cart
        self.carrito = []
        self.table.setRowCount(0)
        self.txt_extra_tip.clear()
        self.txt_cliente.clear()
        self.txt_notes.clear()
        self.update_totals()
        self.show_info(
            "Order Held",
            f"Order #{len(self.held_orders)} placed on hold at {ts}.\n"
            "You can start a new order now."
        )

    def do_resume_orders(self):
        if not self.held_orders:
            self.show_info("No Held Orders", "There are no held orders at this time.")
            return
        dlg = HeldOrdersDialog(self.held_orders, parent=self)
        dlg.order_resumed.connect(self._on_order_resumed)
        dlg.exec()
        self._update_hold_btn()

    def _on_order_resumed(self, idx):
        if idx < 0 or idx >= len(self.held_orders):
            return
        if self.carrito:
            reply = AppMessageBox.question(
                self, "Replace Current Cart?",
                "There are items in the current cart. Are you sure you want to replace it with the held order?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        order = self.held_orders.pop(idx)
        self.carrito = order['carrito']
        self.table.setRowCount(0)
        for row, item in enumerate(self.carrito):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(item['nombre']))
            self.table.setItem(row, 1, QTableWidgetItem(str(item['cant'])))
            self.table.setItem(row, 2, QTableWidgetItem(f"$ {float(item['precio']):,.2f}"))
            notes_btn = QPushButton("+ NOTE")
            notes_btn.setObjectName("BtnNotes")
            notas = item.get('notas_item', [])
            if notas:
                notes_btn.setText(', '.join(notas)[:18] + '…' if len(', '.join(notas)) > 18 else ', '.join(notas))
                notes_btn.setObjectName("BtnNotesActive")
            notes_btn.clicked.connect(lambda checked, r=row: self.open_modifier_for_row(r))
            self.table.setCellWidget(row, 3, notes_btn)

        # Restore billing info
        self.txt_cliente.setText(order.get('cliente', ''))
        self.txt_notes.setText(order.get('notas', ''))
        self.txt_extra_tip.setText(order.get('extra_tip', ''))
        idx_ncf = self.cb_ncf.findText(order.get('ncf', 'CONSUMER'))
        if idx_ncf >= 0:
            self.cb_ncf.setCurrentIndex(idx_ncf)
        idx_met = self.cb_metodo.findText(order.get('metodo', 'CASH'))
        if idx_met >= 0:
            self.cb_metodo.setCurrentIndex(idx_met)

        self.update_totals()
        self._update_hold_btn()

    def _update_hold_btn(self):
        n = len(self.held_orders)
        self._btn_hold_count.setText(f"[HOLD]  HELD  ({n})")

    # ─────────────────────────────────────────────────────────────────────────
    # Split Bill
    # ─────────────────────────────────────────────────────────────────────────
    def do_split_bill(self):
        if not self.carrito:
            self.show_warning("Empty Cart", "No items in the cart to split.")
            return

        ncf_num = (
            "B0200000001" if "CONSUMER" in self.cb_ncf.currentText()
            else "B0100000001"
        )
        cliente = self.txt_cliente.text().strip() or "SPLIT CUSTOMER"
        notas   = self.txt_notes.text().strip()
        hh_disc = self.happy_hour_discount if self.happy_hour_active else 0.0

        dlg = SplitBillDialog(
            carrito=list(self.carrito),
            pos_service=self.pos,
            sincronizador=self.sincronizador,
            ncf_tipo=self.cb_ncf.currentText(),
            ncf_num=ncf_num,
            notas=notas,
            cliente=cliente,
            happy_hour_discount=hh_disc,
            parent=self,
        )
        result = dlg.exec()
        if result == QDialog.Accepted:
            # Bill fully settled — clear the cart
            self.ventas_turno += float(
                self.pos.calcular_totales(
                    self.carrito,
                    happy_hour_discount=hh_disc
                )[3]
            )
            self.actualizar_visor_caja()
            self.carrito = []
            self.table.setRowCount(0)
            self.txt_extra_tip.clear()
            self.txt_cliente.clear()
            self.txt_notes.clear()
            self.update_totals()
            self._activate_stock_cooldown()
            self.load_catalog()
            self.search.setFocus()

    # ─────────────────────────────────────────────────────────────────────────
    # Totals & Payment
    # ─────────────────────────────────────────────────────────────────────────
    def on_payment_change(self, text):
        if text != "CASH":
            self.cash.setEnabled(False)
            self.cash.setText("")
            self.cash.setStyleSheet(
                f"background:{CLR_BG_DEEP};color:{CLR_TEXT_DIM};"
                f"border:1px solid {CLR_BORDER};border-radius:12px;"
                f"font-size:20px;font-weight:700;text-align:center;"
            )
        else:
            self.cash.setEnabled(True)
            self.cash.clear()
            self.cash.setStyleSheet("")

    def update_totals(self):
        try:
            extra = float(self.txt_extra_tip.text().strip() or "0")
        except ValueError:
            extra = 0.0

        # Compute total discount from structured promotion list (manual discounts)
        manual_discount_pct = 0.0
        for promo in self._applied_promotions:
            if promo['tipo'] == 'MANUAL':
                # Already stored as a fraction
                manual_discount_pct = max(manual_discount_pct, promo.get('_pct', 0.0))

        sub, imp, pro, tot = self.pos.calcular_totales(
            self.carrito,
            propina_extra=extra,
            global_discount_pct=manual_discount_pct,
            happy_hour_active=self.happy_hour_active
        )

        self.subtotal_lbl.setText(f"SUBTOTAL: {money(sub)}")
        self.itbis_lbl.setText(f"ITBIS (18%): {money(imp)}")
        self.legaltip_lbl.setText(f"TIP (10%): {money(pro)}")
        self.total_lbl.setText(f"TOTAL: {money(tot)}")

    def do_pago(self):
        if not self.carrito:
            return self.show_warning("Attention", "No products in the cart.")

        for item in self.carrito:
            if item.get('stock') != 9999 and item['cant'] > item.get('stock', 0):
                return self.show_warning(
                    "Stock Validation Error",
                    f"Order quantity for '{item['nombre']}' exceeds available stock "
                    f"({item.get('stock', 0)} available)."
                )

        ncf_num = (
            "B0200000001" if "CONSUMER" in self.cb_ncf.currentText()
            else "B0100000001"
        )
        metodo_combo = self.cb_metodo.currentText()
        metodo = "EFECTIVO"
        if metodo_combo == "CARD":     metodo = "TARJETA"
        elif metodo_combo == "TRANSFER": metodo = "TRANSFERENCIA"

        cliente = self.txt_cliente.text().strip()
        notas   = self.txt_notes.text().strip()
        ncf_type= self.cb_ncf.currentText()

        if ncf_type in ["TAX CREDIT", "GOVERNMENT"] and not cliente:
            return self.show_warning(
                "Missing Billing Info",
                f"Customer Name is required for {ncf_type} invoices."
            )
        if not cliente:
            cliente = "CASH CUSTOMER"

        try:
            extra = float(self.txt_extra_tip.text().strip() or "0")
        except (ValueError, TypeError):
            extra = 0.0

        hh = self.happy_hour_discount if self.happy_hour_active else 0.0

        # Combine HH with any manual discount from structured promotions
        combined_discount = hh
        for promo in self._applied_promotions:
            if promo['tipo'] == 'MANUAL':
                combined_discount = max(combined_discount, promo.get('_pct', 0.0))

        sub, imp, pro, total_venta = self.pos.calcular_totales(
            self.carrito, propina_extra=extra, happy_hour_discount=combined_discount
        )

        if metodo == "TARJETA" and not self.pos.current_import_uuid:
            dialog = VerifoneDialog(
                money(total_venta),
                subtotal_str=money(sub),
                itbis_str=money(imp),
                legaltip_str=money(pro),
                extratip_str=money(extra),
                parent=self
            )
            result = dialog.exec()
            dialog.deleteLater()
            if result != QDialog.Accepted:
                return

        cambio, msg = self.pos.procesar_venta(
            self.carrito,
            self.cash.text(),
            metodo,
            self.cb_ncf.currentText(),
            ncf_num,
            notas,
            cliente,
            sincronizador=self.sincronizador,
            propina_extra=extra,
            deduct_stock=True,
            happy_hour_discount=combined_discount,
        )

        if cambio is not None:
            # Write promotion audit records for every applied promotion
            factura_uuid_str = None
            try:
                from db.connection import SessionLocal as _SL
                from models.entities import FacturaLocal
                _db = _SL()
                last = _db.query(FacturaLocal).order_by(FacturaLocal.id_factura.desc()).first()
                if last:
                    factura_uuid_str = str(last.id_factura)
                _db.close()
            except Exception:
                pass

            from services.auth_service import AuthService as _AS
            _cashier_id = _AS.current_user_id
            for promo in self._applied_promotions:
                self.pos.registrar_aplicacion_promocion(
                    nombre_promocion=promo['nombre'],
                    tipo_aplicacion=promo['tipo'],
                    monto_descuento=promo.get('monto', 0.0),
                    factura_uuid=factura_uuid_str,
                    promocion_id=promo.get('id'),
                    empleado_id=_cashier_id,
                    empleado_autorizador_id=promo.get('supervisor_id'),
                    identificador_capturado=promo.get('identificador'),
                    notas=promo.get('supervisor_nombre'),
                )

            self.ventas_turno += float(total_venta)
            self.actualizar_visor_caja()
            change_text = f"\n\nChange to return: {money(cambio)}" if cambio > 0.009 else ""
            self.show_info(
                "Transaction Complete",
                f"Invoice saved.{change_text}"
            )
            self.carrito = []
            self.table.setRowCount(0)
            self.txt_extra_tip.clear()
            self._applied_promotions.clear()
            self._refresh_promo_badges()
            self.update_totals()
            self.cash.clear()
            self.txt_cliente.clear()
            self.txt_notes.clear()
            self.cb_metodo.setCurrentIndex(0)
            self.cb_ncf.setCurrentIndex(0)
            self._activate_stock_cooldown()
            self.load_catalog()
            self.search.setFocus()
        else:
            self.show_warning("Transaction Error", msg)

    # ─────────────────────────────────────────────────────────────────────────
    # Register Management
    # ─────────────────────────────────────────────────────────────────────────
    def do_login(self):
        from services.auth_service import AuthService
        exito, mensaje = AuthService.login_maestro(self.u.text(), self.p.text())
        if exito:
            if AuthService.token:
                self.sincronizador.token = AuthService.token
            else:
                auth_ok, _ = self.sincronizador.autenticar(self.u.text(), self.p.text())
                if not auth_ok:
                    print("[Login] WARNING: API unreachable.", flush=True)
            if not self.sync_timer.isActive():
                self.sync_timer.start(5000)
            if hasattr(self, 'stock_timer') and not self.stock_timer.isActive():
                self.stock_timer.start(5000)
            self.stack.setCurrentIndex(1)
        else:
            self.show_error("Access Denied", mensaje)

    def do_apertura(self):
        if self.pos.abrir_turno(self.f.text()):
            self.fondo_inicial = float(self.pos.active_turno.monto_inicial)
            self.ventas_turno  = 0.0
            self.actualizar_visor_caja()
            self.stack.setCurrentIndex(2)
        else:
            self.show_warning(
                "Error", "Please enter a valid initial amount (Ex: 1500.50)."
            )

    def do_change_cashier(self):
        """Log out and return to login screen without closing the shift."""
        reply = AppMessageBox.question(
            self, "Change Cashier",
            "Are you sure you want to log out and return to the login screen?\n"
            "(The current register shift will remain open.)",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.carrito:
                hold_reply = AppMessageBox.question(
                    self, "Active Cart",
                    "You have items in the cart. Would you like to hold the order before logging out?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                )
                if hold_reply == QMessageBox.Cancel:
                    return
                if hold_reply == QMessageBox.Yes:
                    self.do_hold_order()
            self.end_supervisor_session(reason="LOGOUT")
            self.u.clear()
            self.p.clear()
            self.stack.setCurrentIndex(0)

    def actualizar_visor_caja(self):
        esperado = self.fondo_inicial + self.ventas_turno
        self.lbl_fondo.setText(f"FUND: {money(self.fondo_inicial)}")
        self.lbl_ventas.setText(f"SALES: {money(self.ventas_turno)}")
        self.lbl_esperado.setText(f"REGISTER: {money(esperado)}")

    def on_typing(self, text):
        if len(text) >= 2:
            self.load_catalog(search_term=text)
        else:
            self.load_catalog()

    def do_cierre_caja(self):
        monto_fisico, ok = AppInputDialog.getText(
            self, "Register Close (Z)",
            "Enter the total physical amount counted in the drawer ($):"
        )
        if ok and monto_fisico:
            try:
                report_path = None
                try:
                    report_path, expected_cash, disc = self.pos.generar_reporte_cuadre(
                        monto_fisico
                    )
                except Exception as rep_err:
                    print(f"Could not generate shift report: {rep_err}", flush=True)

                esperado, descuadre = self.pos.cerrar_turno(monto_fisico)
                report_line = ""
                if report_path:
                    import os
                    report_line = (
                        f"\n📄 Audit Report saved to:\n"
                        f"{os.path.basename(report_path)}\n"
                        f"(in ShiftReports/ folder)\n"
                    )
                disc_symbol = "[OK]" if descuadre == 0 else "[NO]"
                reporte = (
                    f"─── Z CLOSE REPORT ───\n\n"
                    f"Expected Amount in System: {money(esperado)}\n"
                    f"Declared Physical Amount:  {money(monto_fisico)}\n"
                    f"{disc_symbol} Discrepancy: {money(descuadre)}\n"
                    f"{report_line}\n"
                    f"The shift has been securely closed."
                )
                self.show_info("Close Completed", reporte)
                if report_path:
                    try:
                        import os
                        os.startfile(report_path)
                    except Exception:
                        pass

                self.ventas_turno = 0.0
                self.fondo_inicial = 0.0
                self.end_supervisor_session(reason="LOGOUT")
                self.u.clear()
                self.p.clear()
                self.f.clear()
                self.stack.setCurrentIndex(0)
            except Exception as e:
                self.show_error("Fatal Error", f"Could not close the register: {str(e)}")

    def do_abrir_mesas(self):
        if self._mesas_dialog is None:
            self._mesas_dialog = MesasDialog(self.sincronizador, self.pos, parent=self)
            self._mesas_dialog.order_selected.connect(self._on_pedido_importado)
        self._mesas_dialog.refresh()
        self._mesas_dialog.show()
        self._mesas_dialog.raise_()
        self._mesas_dialog.activateWindow()

    def _on_pedido_importado(self, data):
        carrito = data.get("carrito", [])
        mesa    = data.get("mesa", "")
        if not carrito:
            self.show_warning("Empty Order", "The selected order has no importable items.")
            return
        self.carrito = carrito
        self.table.setRowCount(0)
        for row, item in enumerate(carrito):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(item['nombre']))
            self.table.setItem(row, 1, QTableWidgetItem(str(item['cant'])))
            self.table.setItem(row, 2, QTableWidgetItem(f"$ {float(item['precio']):,.2f}"))
            notes_btn = QPushButton("+ NOTE")
            notes_btn.setObjectName("BtnNotes")
            notas = item.get('notas_item', [])
            if notas:
                text = ', '.join(notas)
                notes_btn.setText(text[:18] + '…' if len(text) > 18 else text)
                notes_btn.setObjectName("BtnNotesActive")
            notes_btn.clicked.connect(lambda checked, r=row: self.open_modifier_for_row(r))
            self.table.setCellWidget(row, 3, notes_btn)
        self.update_totals()
        if mesa and str(mesa).strip():
            self.txt_cliente.setText(f"Table {mesa}")
        self.show_info(
            "Order Imported",
            f"Remote order loaded — {len(carrito)} item(s).\n"
            "Select NCF type and payment method, then press BILL."
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Sync & Stock
    # ─────────────────────────────────────────────────────────────────────────
    def _start_sync(self, on_done_callback, fetch_pedidos=False, full_sync=False):
        self._current_sync_callback = on_done_callback
        self._sync_worker.request.emit(fetch_pedidos, full_sync)

    def _on_sync_result(self, sync_ok, sync_msg, categorias, pedidos, hh_active, hh_discount):
        self._update_happy_hour_ui(hh_active, hh_discount)
        cb = self._current_sync_callback
        if cb:
            cb(sync_ok, sync_msg, categorias, pedidos)

    def do_sincronizacion(self):
        self._start_sync(self._on_manual_sync_done, fetch_pedidos=True)

    def _on_manual_sync_done(self, sync_ok, sync_msg, categorias, pedidos):
        if categorias:
            self.build_category_filters(categorias)
        if pedidos and self._mesas_dialog and self._mesas_dialog.isVisible():
            self._mesas_dialog.populate_from_data(pedidos)
        
        # Refresh product grid and cart in case prices or promos changed
        if hasattr(self, 'search') and not self.search.text():
            self.load_catalog()
        self.actualizar_tabla()
        self.update_totals()
        
        if sync_ok:
            self.show_info("Sync Completed", sync_msg)
        else:
            self.show_warning("Sync Failed", sync_msg)

    def auto_sync(self):
        if time.monotonic() < self._stock_cooldown_until:
            print("[AutoSync] SKIPPED — post-sale stock cooldown active", flush=True)
            return
        self._auto_sync_counter += 1
        if not self.sincronizador.token:
            from services.auth_service import AuthService
            cached_id = getattr(AuthService, '_last_identificador', None)
            cached_pw = getattr(AuthService, '_last_password', None)
            if cached_id and cached_pw:
                ok, _ = self.sincronizador.autenticar(cached_id, cached_pw)
                if ok:
                    print("[AutoSync] API token acquired on retry.", flush=True)
        fetch   = (self._auto_sync_counter % 6 == 0)
        do_full = (self._auto_sync_counter == 1 or self._auto_sync_counter % 60 == 0)
        self._start_sync(self._on_auto_sync_done, fetch_pedidos=fetch, full_sync=do_full)

    def _on_auto_sync_done(self, sync_ok, sync_msg, categorias, pedidos):
        if categorias:
            self.build_category_filters(categorias)
        if pedidos and self._mesas_dialog and self._mesas_dialog.isVisible():
            self._mesas_dialog.populate_from_data(pedidos)
            
        # Refresh product grid and cart in case prices or promos changed
        if hasattr(self, 'search') and not self.search.text():
            self.load_catalog()
        self.update_totals()

    def _activate_stock_cooldown(self):
        self._stock_cooldown_until = time.monotonic() + self._post_sale_stock_delay_s
        self._stock_worker._skip_persist = True
        self._live_stock_cache.clear()
        delay_ms = int(self._post_sale_stock_delay_s * 1000) + 200
        print(
            f"[StockCooldown] Activated — blocking for {self._post_sale_stock_delay_s}s",
            flush=True
        )
        QTimer.singleShot(delay_ms, self._on_cooldown_expired)

    def _on_cooldown_expired(self):
        self._stock_worker._skip_persist = False
        print("[StockCooldown] Expired — re-enabling stock fetches", flush=True)
        self.request_stock_update()

    def request_stock_update(self):
        now = time.monotonic()
        if now < self._stock_cooldown_until:
            remaining = self._stock_cooldown_until - now
            print(
                f"[StockTimer] BLOCKED — cooldown active ({remaining:.1f}s left)",
                flush=True
            )
            return
        token_ok  = bool(self.sincronizador.token)
        btn_count = len(self.product_buttons) if hasattr(self, 'product_buttons') else 0
        busy      = self._stock_worker._busy
        print(f"[StockTimer] token={token_ok} buttons={btn_count} busy={busy}", flush=True)
        if not self.sincronizador.token:
            return
        if btn_count > 0:
            self._stock_worker.request.emit(list(self.product_buttons.keys()))
        else:
            print("[StockTimer] No product buttons yet — skipping", flush=True)

    @Slot(object)
    def _on_stock_result(self, stock_data):
        if time.monotonic() < self._stock_cooldown_until:
            print(
                f"[_on_stock_result] DISCARDED {len(stock_data)} stale values",
                flush=True
            )
            return
        if not stock_data:
            print("[_on_stock_result] Empty result — nothing to update", flush=True)
            return
        print(f"[_on_stock_result] Updating {len(stock_data)} buttons", flush=True)
        self._live_stock_cache.update(stock_data)
        updated = 0
        for pid, stock in stock_data.items():
            if pid in self.product_buttons:
                tup = self.product_buttons[pid]
                btn, nombre, precio = tup[0], tup[1], tup[2]
                nuevo_precio = tup[3] if len(tup) > 3 else precio
                discount_text = tup[4] if len(tup) > 4 else ""
                try:
                    if nuevo_precio < precio:
                        btn_text = f"{discount_text}\n{nombre}\n{money(nuevo_precio)}\nStock: {stock}"
                    else:
                        btn_text = f"\n{nombre}\n{money(precio)}\nStock: {stock}"
                    btn.setText(btn_text)
                    updated += 1
                except RuntimeError:
                    pass
            else:
                pid_int = int(pid) if not isinstance(pid, int) else pid
                if pid_int in self.product_buttons:
                    tup = self.product_buttons[pid_int]
                    btn, nombre, precio = tup[0], tup[1], tup[2]
                    nuevo_precio = tup[3] if len(tup) > 3 else precio
                    discount_text = tup[4] if len(tup) > 4 else ""
                    try:
                        if nuevo_precio < precio:
                            btn_text = f"{nombre}\n{money(precio)}  ->  {money(nuevo_precio)}\n{discount_text}\nStock: {stock}"
                        else:
                            btn_text = f"{nombre}\n{money(precio)}\nStock: {stock}"
                        btn.setText(btn_text)
                        updated += 1
                    except RuntimeError:
                        pass
        print(f"[_on_stock_result] Updated {updated}/{len(stock_data)} buttons", flush=True)

    # ─────────────────────────────────────────────────────────────────────────
    # Promotion Workflow
    # ─────────────────────────────────────────────────────────────────────────
    def open_promotions_dialog(self):
        """Open the structured promotion dialog. Blocked if cart is empty."""
        if not self.carrito:
            self.show_warning("Empty Cart", "Add items to the cart before applying promotions.")
            return
        dlg = PromotionsDialog(
            pos_service=self.pos,
            sincronizador=self.sincronizador,
            carrito=self.carrito,
            existing_promos=list(self._applied_promotions),
            parent=self
        )
        if dlg.exec() == QDialog.Accepted:
            self._applied_promotions = dlg.get_applied_promotions()
            self._refresh_promo_badges()
            self.update_totals()

    def _refresh_promo_badges(self):
        """Rebuild the discount badge row below the totals from _applied_promotions."""
        # Clear existing badges
        while self._promo_badges_layout.count():
            item = self._promo_badges_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._applied_promotions:
            self._promo_badges_widget.setVisible(False)
            self.btn_promotions.setObjectName("BtnPromo")
            self.btn_promotions.setText("\u2295  PROMOTIONS")
            self.btn_promotions.style().unpolish(self.btn_promotions)
            self.btn_promotions.style().polish(self.btn_promotions)
            return

        self._promo_badges_widget.setVisible(True)
        for i, promo in enumerate(self._applied_promotions):
            badge = QFrame()
            badge.setObjectName("DiscountBadge")
            badge_l = QHBoxLayout(badge)
            badge_l.setContentsMargins(0, 0, 4, 0)
            badge_l.setSpacing(0)

            icon_map = {'ELEGIBILIDAD': '🎫', 'CODIGO_PROMO': '🏷️', 'MANUAL': '🔐', 'AUTOMATICA': '⚡'}
            icon = icon_map.get(promo.get('tipo', ''), '•')
            monto = promo.get('monto', 0.0)
            text = f"{icon} {promo['nombre']}  -{money(monto)}"
            lbl = _lbl(text, "LblDiscountBadge")
            badge_l.addWidget(lbl)

            remove_btn = QPushButton("✕")
            remove_btn.setObjectName("BtnBadgeRemove")
            remove_btn.clicked.connect(lambda checked, idx=i: self._remove_promotion(idx))
            badge_l.addWidget(remove_btn)
            self._promo_badges_layout.addWidget(badge)

        self._promo_badges_layout.addStretch()

        # Update button style to indicate active promotions
        count = len(self._applied_promotions)
        self.btn_promotions.setObjectName("BtnPromoActive")
        self.btn_promotions.setText(f"\u2713  {count} PROMO{'S' if count != 1 else ''} APPLIED")
        self.btn_promotions.style().unpolish(self.btn_promotions)
        self.btn_promotions.style().polish(self.btn_promotions)

    def _remove_promotion(self, idx: int):
        """Remove a promotion at the given index and refresh the badge row."""
        if 0 <= idx < len(self._applied_promotions):
            removed = self._applied_promotions.pop(idx)
            print(f"[Promotions] Removed: {removed.get('nombre')}", flush=True)
        self._refresh_promo_badges()
        self.update_totals()

    # ─────────────────────────────────────────────────────────────────────────
    # Supervisor Authorization Session
    # ─────────────────────────────────────────────────────────────────────────
    def start_supervisor_session(self, supervisor_id: int, supervisor_nombre: str):
        from models.entities import SupervisorSessionLocal
        from db.connection import SessionLocal
        import datetime

        
        self.supervisor_session_active = True
        self.supervisor_id = supervisor_id
        self.supervisor_nombre = supervisor_nombre
        self.supervisor_session_seconds_left = 300 # 5 minutes
        
        self._lbl_supervisor_mode.setText(f"SUPERVISOR: {supervisor_nombre.upper()} | 05:00")
        self._lbl_supervisor_mode.setVisible(True)
        self._btn_end_supervisor.setVisible(True)
        self.supervisor_session_timer.start(1000)
        
        db = SessionLocal()
        try:
            session_audit = SupervisorSessionLocal(
                supervisor_id=supervisor_id,
                cajero_id=self.pos.empleado_id if self.pos else 0,
                terminal="POS-01",
                inicio=get_local_now()
            )
            db.add(session_audit)
            db.commit()
            self._active_session_db_id = session_audit.id
        except Exception as e:
            print(f"Failed to save supervisor session start: {e}", flush=True)
        finally:
            db.close()

    def tick_supervisor_session(self):
        self.supervisor_session_seconds_left -= 1
        if self.supervisor_session_seconds_left <= 0:
            self.end_supervisor_session(reason="EXPIRED")
        else:
            m = self.supervisor_session_seconds_left // 60
            s = self.supervisor_session_seconds_left % 60
            self._lbl_supervisor_mode.setText(f"SUPERVISOR: {self.supervisor_nombre.upper()} | {m:02d}:{s:02d}")

    def end_supervisor_session(self, reason: str = "LOGOUT"):
        if not self.supervisor_session_active:
            return
            
        self.supervisor_session_active = False
        self.supervisor_session_timer.stop()
        self._lbl_supervisor_mode.setVisible(False)
        self._btn_end_supervisor.setVisible(False)
        
        if self._active_session_db_id:
            from models.entities import SupervisorSessionLocal
            from db.connection import SessionLocal
            import datetime

            db = SessionLocal()
            try:
                session_audit = db.query(SupervisorSessionLocal).filter_by(id=self._active_session_db_id).first()
                if session_audit:
                    session_audit.fin = get_local_now()
                    session_audit.motivo_fin = reason
                    db.commit()
            except Exception as e:
                print(f"Failed to end supervisor session: {e}", flush=True)
            finally:
                db.close()
                self._active_session_db_id = None
            
            # Request async sync
            QTimer.singleShot(100, lambda: self._sync_worker.request.emit(False, False))

    # ─────────────────────────────────────────────────────────────────────────
    # Close / Cleanup
    # ─────────────────────────────────────────────────────────────────────────
    def _cleanup_and_close(self, event):
        try:
            for attr in ('sync_timer', 'stock_timer', 'hh_timer'):
                t = getattr(self, attr, None)
                if t and t.isActive():
                    t.stop()
            if self._mesas_dialog is not None:
                self._mesas_dialog.cleanup_thread()
            for attr in ('_sync_thread', '_stock_thread'):
                t = getattr(self, attr, None)
                if t and t.isRunning():
                    t.quit()
                    t.wait(3000)
        except Exception:
            pass
        super().closeEvent(event)

    def closeEvent(self, event):
        self._cleanup_and_close(event)
