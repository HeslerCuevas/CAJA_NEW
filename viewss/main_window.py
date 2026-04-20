from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QStackedWidget, 
                             QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
                             QListWidget, QListWidgetItem, QInputDialog, QComboBox,
                             QFrame, QScrollArea, QGridLayout, QSizePolicy,
                             QDialog, QDialogButtonBox)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QObject
from PySide6.QtGui import QColor, QBrush
from services.pos_service import POSService
from services.sync_service import SyncService

STYLESHEET = """
    QMainWindow { background-color: #0b1120; }
    QLabel { color: #e2e8f0; font-family: 'Segoe UI', Consolas, monospace; }
    
    QLineEdit, QComboBox { 
        background-color: #1e293b; 
        color: #38bdf8; 
        padding: 12px; 
        border: 2px solid #334155; 
        border-radius: 6px; 
        font-size: 14px;
        font-weight: bold;
    }
    QLineEdit:focus, QComboBox:focus { border: 2px solid #0ea5e9; background-color: #0f172a; }
    
    QPushButton { 
        background-color: #0284c7; 
        color: white; 
        padding: 12px; 
        font-weight: bold; 
        font-size: 14px;
        border-radius: 6px;
        border: none;
    }
    QPushButton:hover { background-color: #0369a1; }
    
    QPushButton#BtnDanger { background-color: #e11d48; }
    QPushButton#BtnDanger:hover { background-color: #be123c; }
    
    QPushButton#BtnSuccess { background-color: #10b981; font-size: 16px; }
    QPushButton#BtnSuccess:hover { background-color: #059669; }
    
    QTableWidget { 
        background-color: #1e293b; 
        color: #f8fafc; 
        gridline-color: #334155; 
        border: 1px solid #475569;
        border-radius: 6px;
        font-size: 14px;
        selection-background-color: #0ea5e9; 
        selection-color: white;
    }
    QHeaderView::section { 
        background-color: #0f172a; 
        color: #94a3b8; 
        padding: 8px; 
        font-weight: bold;
        border: 1px solid #334155;
    }
    
    QListWidget { 
        background-color: #1e293b; 
        color: #f8fafc; 
        border: 2px solid #0ea5e9; 
        border-radius: 6px; 
        font-size: 14px;
    }
    QListWidget::item { padding: 12px; border-bottom: 1px solid #334155; }
    QListWidget::item:hover, QListWidget::item:selected { background-color: #0284c7; color: white; }
    
    QFrame#CajaFrame {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
    }
    QFrame#CobroFrame {
        background-color: #0f172a;
        border: 2px solid #38bdf8;
        border-radius: 8px;
    }
    QPushButton#BtnMesas {
        background-color: #d97706;
        color: white;
        border-radius: 6px;
        padding: 10px;
        font-weight: bold;
    }
    QPushButton#BtnMesas:hover { background-color: #b45309; }
"""


class SyncWorker(QObject):
    """Persistent worker that lives on a single background thread for the app lifetime.
    Work requests are dispatched via the request signal; results come back via finished.
    This avoids creating/destroying QThread objects which causes GC crashes in PySide6.
    """
    finished = Signal(bool, str, list, list)  # (sync_ok, sync_msg, categorias, pedidos)
    request = Signal(bool, bool)  # (fetch_pedidos, full_sync)

    def __init__(self, sincronizador):
        super().__init__()
        self.sincronizador = sincronizador
        self._busy = False

    def on_request(self, fetch_pedidos, full_sync):
        if self._busy:
            return  # Skip if we're already processing
        self._busy = True
        categorias = []
        pedidos = []
        sync_ok, sync_msg = True, ""
        try:
            # Always upload pending local sales FIRST so the CORE has current stock deductions
            sync_ok, sync_msg = self.sincronizador.sincronizar_ventas_pendientes()
            
            # Always sync products to ensure catalog is up to date constantly
            self.sincronizador.sincronizar_productos()
            
            if full_sync:
                self.sincronizador.sincronizar_empleados()
                categorias = self.sincronizador.sincronizar_categorias() or []
                
            if fetch_pedidos:
                pedidos = self.sincronizador.obtener_cuentas_abiertas() or []
        except Exception as e:
            sync_ok, sync_msg = False, str(e)
        self._busy = False
        self.finished.emit(sync_ok, sync_msg, categorias, pedidos)


class VerifoneDialog(QDialog):
    """Mock Verifone processing dialog for remote orders."""
    def __init__(self, amount, subtotal_str=None, itbis_str=None, legaltip_str=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Verifone Payment")
        self.setFixedSize(400, 320)
        self.setStyleSheet("""
            QDialog { background-color: #0b1120; }
            QLabel { color: #f8fafc; font-size: 16px; font-weight: bold; }
            QLabel#status { color: #fbbf24; font-size: 20px; margin-top: 20px; }
        """)
        layout = QVBoxLayout(self)
        
        lbl_msg = QLabel("Please swipe card or insert chip...")
        lbl_msg.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_msg)
        layout.addStretch()

        if subtotal_str:
            lbl_sub = QLabel(f"Subtotal: {subtotal_str}")
            lbl_sub.setAlignment(Qt.AlignCenter)
            lbl_sub.setStyleSheet("color: #94a3b8; font-size: 16px;")
            layout.addWidget(lbl_sub)
            
        if itbis_str:
            lbl_itbis = QLabel(f"ITBIS TAX (18%): {itbis_str}")
            lbl_itbis.setAlignment(Qt.AlignCenter)
            lbl_itbis.setStyleSheet("color: #94a3b8; font-size: 16px;")
            layout.addWidget(lbl_itbis)
            
        if legaltip_str:
            lbl_tip = QLabel(f"LEGAL TIP (10%): {legaltip_str}")
            lbl_tip.setAlignment(Qt.AlignCenter)
            lbl_tip.setStyleSheet("color: #94a3b8; font-size: 16px;")
            layout.addWidget(lbl_tip)
        
        lbl_amount = QLabel(f"TOTAL DUE: {amount}")
        lbl_amount.setAlignment(Qt.AlignCenter)
        lbl_amount.setStyleSheet("color: #38bdf8; font-size: 26px; padding-top: 10px;")
        layout.addWidget(lbl_amount)
        
        self.lbl_status = QLabel("Processing...")
        self.lbl_status.setObjectName("status")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_status)
        layout.addStretch()
        
        # Safe class-bound timer to prevent garbage collection crashes
        self.timer_process = QTimer(self)
        self.timer_process.setSingleShot(True)
        self.timer_process.timeout.connect(self._on_success)
        self.timer_process.start(5000)

    def _on_success(self):
        try:
            self.lbl_status.setStyleSheet("color: #10b981; font-size: 20px;")
            self.lbl_status.setText("Payment Approved!")
        except RuntimeError: 
            return # Dialog was closed early

        self.timer_close = QTimer(self)
        self.timer_close.setSingleShot(True)
        self.timer_close.timeout.connect(self.accept)
        self.timer_close.start(1500)


class _FetchOrdersWorker(QObject):
    """Persistent worker for fetching pending orders without blocking UI."""
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
            print(f"❌ Fetch orders error: {e}", flush=True)
            pedidos = []
        self._busy = False
        self.finished.emit(pedidos)


class MesasDialog(QDialog):
    """Dialog showing all active/pending remote orders."""
    order_selected = Signal(dict)  # Emits the selected order header

    def __init__(self, sincronizador, pos_service, parent=None):
        super().__init__(parent)
        self.sincronizador = sincronizador
        self.pos = pos_service
        self._pedidos = []

        # Persistent refresh thread — lives for the dialog's lifetime
        self._refresh_thread = QThread(self)
        self._refresh_worker = _FetchOrdersWorker(self.sincronizador)
        self._refresh_worker.moveToThread(self._refresh_thread)
        self._refresh_worker.request.connect(self._refresh_worker.run)
        self._refresh_worker.finished.connect(self._on_refresh_done)
        self._refresh_thread.start()
        self.setWindowTitle("Active Tables / Open Orders")
        self.setMinimumSize(800, 500)
        self.setStyleSheet("""
            QDialog { background-color: #0b1120; }
            QLabel { color: #e2e8f0; }
            QTableWidget { background-color: #1e293b; color: #f8fafc;
                           gridline-color: #334155; font-size: 13px; }
            QHeaderView::section { background-color: #0f172a; color: #94a3b8;
                                   padding: 8px; font-weight: bold; }
            QPushButton { background-color: #0284c7; color: white; padding: 10px;
                          font-weight: bold; border-radius: 6px; }
        """)
        layout = QVBoxLayout(self)

        title = QLabel("🍽️  Active Tables — Double-click to import order")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc; padding: 8px;")
        layout.addWidget(title)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Table", "Channel", "Status", "Subtotal", "Total", "Date"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        btn_refresh = QPushButton("♻️  Refresh")
        btn_refresh.clicked.connect(self.refresh)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.hide)  # Hide, don't destroy
        btn_row.addWidget(btn_refresh)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def cleanup_thread(self):
        """Called by MainWindow.closeEvent to stop the thread before app exit."""
        if self._refresh_thread.isRunning():
            self._refresh_thread.quit()
            self._refresh_thread.wait(2000)

    def refresh(self):
        """Send a fetch request to the persistent worker."""
        self.table.setRowCount(0)
        self.table.setRowCount(1)
        item = QTableWidgetItem("Loading...")
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(0, 0, item)
        self._refresh_worker.request.emit()

    def _on_refresh_done(self, pedidos):
        try:
            self.isVisible()  # guard against deleted dialog
        except RuntimeError:
            return
        self._pedidos = pedidos or []
        self._populate(self._pedidos)

    def populate_from_data(self, pedidos):
        """Populate from pre-fetched data (called by auto-sync)."""
        self._pedidos = pedidos or []
        self._populate(self._pedidos)

    def _populate(self, pedidos):
        self.table.setRowCount(0)
        orange = QColor("#92400e")  # dark amber background for urgent rows
        amber_text = QColor("#fbbf24")
        for pedido in pedidos:
            row = self.table.rowCount()
            self.table.insertRow(row)
            mesa_val = pedido.get("mesa", "—")
            canal = pedido.get("canal_origen", "—")
            estado = pedido.get("estado", "—")
            subtotal = f"$ {pedido.get('subtotal', 0):,.2f}"
            total = f"$ {pedido.get('total_general', 0):,.2f}"
            fecha = pedido.get("fecha_creacion", "—")
            for col, val in enumerate([str(mesa_val), canal, estado, subtotal, total, fecha]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
            # Highlight urgent orders
            if estado in ("POR_FACTURAR", "EN_ESPERA", "PENDIENTE"):
                for col in range(6):
                    self.table.item(row, col).setBackground(QBrush(orange))
                    self.table.item(row, col).setForeground(QBrush(amber_text))

    def _on_double_click(self, index):
        row = index.row()
        if row < 0 or row >= len(self._pedidos):
            return
        pedido = self._pedidos[row]
        uuid = pedido.get("factura_local_uuid")
        if not uuid:
            QMessageBox.warning(self, "Error", "Order has no UUID.")
            return

        total_str = f"$ {pedido.get('total_general', 0):,.2f}"
        subtotal_str = f"$ {pedido.get('subtotal', 0):,.2f}"
        itbis_str = f"$ {pedido.get('total_impuestos', 0):,.2f}"
        legal_tip_str = f"$ {pedido.get('propina_legal', 0):,.2f}"

        # Show Mock Verifone Payment Flow
        dialog = VerifoneDialog(total_str, subtotal_str=subtotal_str, itbis_str=itbis_str, legaltip_str=legal_tip_str, parent=self)
        if dialog.exec() == QDialog.Accepted:
            # Payment success -> Tell CORE the order is paid
            ok, msg = self.sincronizador.notificar_facturacion_remota(uuid)
            if ok:
                QMessageBox.information(self, "Transaction Successful", "Order has been paid and closed.")
                
                # Update stock synchronously so user sees it right away
                carrito = pedido.get("carrito", [])
                self.pos.descontar_stock_remoto(carrito)

                self.refresh()
                # Also do a full sync to fetch any other backend changes
                parent = self.parentWidget()
                if parent and hasattr(parent, '_start_sync'):
                    parent._start_sync(parent._on_manual_sync_done, fetch_pedidos=True, full_sync=True)
            else:
                QMessageBox.critical(self, "CORE Notification Failed", 
                    f"Payment went through, but failed to notify CORE:\n{msg}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pos = POSService()
        self.sincronizador = SyncService()
        self.carrito = []
        self.ventas_turno = 0.0  # Variable en memoria para el visor de caja
        self.fondo_inicial = 0.0
        self._mesas_dialog = None  # Track open mesas dialog
        self._auto_sync_counter = 0  # Count auto-sync ticks for 30s order poll
        self._current_sync_callback = None  # Which callback to route results to
        
        # --- PERSISTENT SYNC THREAD (lives for entire app lifetime) ---
        self._sync_thread = QThread(self)
        self._sync_worker = SyncWorker(self.sincronizador)
        self._sync_worker.moveToThread(self._sync_thread)
        self._sync_worker.request.connect(self._sync_worker.on_request)
        self._sync_worker.finished.connect(self._on_sync_result)
        self._sync_thread.start()
        
        self.setMinimumSize(1000, 700)
        self.showMaximized()
        self.setWindowTitle("MASTER POS SYSTEM - CASH TERMINAL")
        self.setStyleSheet(STYLESHEET)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.init_login()
        self.init_apertura()
        self.init_ventas()
        
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self.auto_sync)
        # Timer starts every 5s after login, but we do one initial sync NOW
        self.auto_sync()

    def closeEvent(self, event):
        """Handle application close: stop timer, then cleanly stop all persistent threads."""
        if self.sync_timer.isActive():
            self.sync_timer.stop()
        if self._mesas_dialog is not None:
            self._mesas_dialog.cleanup_thread()
        if self._sync_thread.isRunning():
            self._sync_thread.quit()
            self._sync_thread.wait(3000)
        super().closeEvent(event)

    def init_login(self):
        w = QWidget(); l = QVBoxLayout(w); l.setAlignment(Qt.AlignCenter)
        frame = QFrame(); frame.setObjectName("CajaFrame"); frame.setFixedSize(450, 400)
        fl = QVBoxLayout(frame); fl.setContentsMargins(40, 40, 40, 40)
        
        lbl_titulo = QLabel("TERMINAL AUTHENTICATION")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #38bdf8;")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        
        self.u = QLineEdit(); self.u.setPlaceholderText("Email (gmail)")
        self.p = QLineEdit(); self.p.setPlaceholderText("Password"); self.p.setEchoMode(QLineEdit.Password)
        btn = QPushButton("LOGIN"); btn.clicked.connect(self.do_login)
        
        fl.addWidget(lbl_titulo); fl.addSpacing(30)
        fl.addWidget(QLabel("CREDENTIALS:")); fl.addWidget(self.u); fl.addWidget(self.p)
        fl.addSpacing(20); fl.addWidget(btn)
        
        l.addWidget(frame)
        self.stack.addWidget(w)

    def init_apertura(self):
        w = QWidget(); l = QVBoxLayout(w); l.setAlignment(Qt.AlignCenter)
        frame = QFrame(); frame.setObjectName("CajaFrame"); frame.setFixedSize(450, 300)
        fl = QVBoxLayout(frame); fl.setContentsMargins(40, 40, 40, 40)
        
        lbl_titulo = QLabel("CASH DECLARATION")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #10b981;")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        
        self.f = QLineEdit(); self.f.setPlaceholderText("Ex. 5000.00")
        btn = QPushButton("OPEN REGISTER AND START"); btn.setObjectName("BtnSuccess")
        btn.clicked.connect(self.do_apertura)
        
        fl.addWidget(lbl_titulo); fl.addSpacing(20)
        fl.addWidget(QLabel("INITIAL CASH IN DRAWER ($):")); fl.addWidget(self.f); fl.addSpacing(10); fl.addWidget(btn)
        
        l.addWidget(frame)
        self.stack.addWidget(w)

    def init_ventas(self):
        w = QWidget(); main_l = QVBoxLayout(w); main_l.setContentsMargins(20, 20, 20, 20)
        
        # --- PANEL SUPERIOR: VISOR DE CAJA Y CONTROLES ---
        top_frame = QFrame(); top_frame.setObjectName("CajaFrame")
        top_layout = QHBoxLayout(top_frame); top_layout.setContentsMargins(15, 10, 15, 10)
        
        # Visor de telemetría de efectivo
        telemetria_layout = QHBoxLayout()
        self.lbl_fondo = QLabel("FUND: $ 0.00"); self.lbl_fondo.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 16px;")
        self.lbl_ventas = QLabel("SALES: $ 0.00"); self.lbl_ventas.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 16px;")
        self.lbl_esperado = QLabel("REGISTER SHOULD HAVE: $ 0.00"); self.lbl_esperado.setStyleSheet("color: #10b981; font-weight: bold; font-size: 18px;")
        
        telemetria_layout.addWidget(self.lbl_fondo); telemetria_layout.addSpacing(20)
        telemetria_layout.addWidget(self.lbl_ventas); telemetria_layout.addSpacing(20)
        telemetria_layout.addWidget(self.lbl_esperado)
        
        btn_close = QPushButton("CLOSE REGISTER (Z)"); btn_close.setObjectName("BtnDanger"); btn_close.setFixedWidth(250)
        btn_close.clicked.connect(self.do_cierre_caja)

        btn_mesas = QPushButton("🍽️  ACTIVE TABLES"); btn_mesas.setObjectName("BtnMesas"); btn_mesas.setFixedWidth(250)
        btn_mesas.clicked.connect(self.do_abrir_mesas)
        
        top_layout.addLayout(telemetria_layout); top_layout.addStretch()
        top_layout.addWidget(btn_mesas); top_layout.addWidget(btn_close)
        main_l.addWidget(top_frame)

        # --- PANEL CENTRAL: BUSCADOR Y TABLA ---
        mid_layout = QHBoxLayout()
        
        # Buscador con autocompletado
        search_l = QVBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText(" Search product by name or ID...")
        self.search.textChanged.connect(self.on_typing)
        
        self.cat_layout = QHBoxLayout()
        cat_scroll = QScrollArea()
        cat_scroll.setWidgetResizable(True)
        cat_scroll.setMaximumHeight(65)
        cat_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        cat_container = QWidget()
        cat_container.setStyleSheet("background-color: transparent;")
        cat_container.setLayout(self.cat_layout)
        cat_scroll.setWidget(cat_container)
        
        self.prod_scroll = QScrollArea()
        self.prod_scroll.setWidgetResizable(True)
        self.prod_scroll.setStyleSheet("QScrollArea { border: 2px solid #334155; border-radius: 6px; }")
        self.prod_container = QWidget()
        self.prod_container.setStyleSheet("background-color: transparent;")
        self.prod_layout = QGridLayout(self.prod_container)
        self.prod_scroll.setWidget(self.prod_container)

        search_l.addWidget(self.search)
        search_l.addWidget(cat_scroll)
        search_l.addWidget(self.prod_scroll, stretch=1)
        
        mid_layout.addLayout(search_l, stretch=3)
        
        right_l = QVBoxLayout()
        btn_delete = QPushButton("DELETE ITEM"); btn_delete.setObjectName("BtnDanger")
        btn_delete.clicked.connect(self.do_delete_item); btn_delete.setFixedHeight(45)
        right_l.addWidget(btn_delete, alignment=Qt.AlignTop)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["PRODUCT", "QTY", "UNIT PRICE"])
        
        # Columns scale with available space
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)          # Product fills remaining
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Qty fits content
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Price fits content
        
        # Hide vertical header (row numbers)
        self.table.verticalHeader().hide()
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        right_l.addWidget(self.table, stretch=1)
        
        mid_layout.addLayout(right_l, stretch=2)
        main_l.addLayout(mid_layout, stretch=1)

        # --- PANEL INFERIOR: FACTURACIÓN Y COBRO ---
        bot_layout = QHBoxLayout()
        
        # Datos Fiscales
        fiscal_frame = QFrame(); fiscal_frame.setObjectName("CajaFrame")
        fiscal_l = QVBoxLayout(fiscal_frame)
        self.txt_cliente = QLineEdit(); self.txt_cliente.setPlaceholderText("Customer Name (Optional)")
        self.txt_notes = QLineEdit(); self.txt_notes.setPlaceholderText("Order Notes (Optional)")
        self.cb_ncf = QComboBox(); self.cb_ncf.addItems(["CONSUMER", "TAX CREDIT", "GOVERNMENT"])
        fiscal_l.addWidget(QLabel("BILLING DETAILS")); fiscal_l.addWidget(self.txt_cliente)
        fiscal_l.addWidget(self.txt_notes); fiscal_l.addWidget(self.cb_ncf)
        
        # Método de Pago
        pago_frame = QFrame(); pago_frame.setObjectName("CajaFrame")
        pago_l = QVBoxLayout(pago_frame)
        self.cb_metodo = QComboBox(); self.cb_metodo.addItems(["CASH", "CARD", "TRANSFER"])
        self.cb_metodo.currentTextChanged.connect(self.on_payment_change)
        self.txt_extra_tip = QLineEdit()
        self.txt_extra_tip.setPlaceholderText("Extra Tip ($)")
        self.txt_extra_tip.textChanged.connect(self.update_totals)
        pago_l.addWidget(QLabel("PAYMENT METHOD")); pago_l.addWidget(self.cb_metodo)
        pago_l.addWidget(QLabel("ADDITIONAL TIP")); pago_l.addWidget(self.txt_extra_tip)
        pago_l.addStretch()
        
        # Resumen y Cobro (Destacado)
        cobro_frame = QFrame(); cobro_frame.setObjectName("CobroFrame")
        calc_l = QVBoxLayout(cobro_frame)
        
        details_layout = QHBoxLayout()
        self.subtotal_lbl = QLabel("SUBTOTAL: $ 0.00"); self.subtotal_lbl.setStyleSheet("font-size: 14px; color: #94a3b8;")
        self.itbis_lbl = QLabel("ITBIS TAX (18%): $ 0.00"); self.itbis_lbl.setStyleSheet("font-size: 14px; color: #94a3b8;")
        self.legaltip_lbl = QLabel("LEGAL TIP (10%): $ 0.00"); self.legaltip_lbl.setStyleSheet("font-size: 14px; color: #94a3b8;")
        self.subtotal_lbl.setAlignment(Qt.AlignCenter); self.itbis_lbl.setAlignment(Qt.AlignCenter); self.legaltip_lbl.setAlignment(Qt.AlignCenter)
        details_layout.addWidget(self.subtotal_lbl); details_layout.addWidget(self.itbis_lbl); details_layout.addWidget(self.legaltip_lbl)
        
        calc_l.addLayout(details_layout)
        
        self.total_lbl = QLabel("TOTAL: $ 0.00"); self.total_lbl.setStyleSheet("font-size: 32px; color: #38bdf8; font-weight: bold;")
        self.total_lbl.setAlignment(Qt.AlignRight)
        self.cash = QLineEdit(); self.cash.setPlaceholderText("Cash Received"); self.cash.setStyleSheet("font-size: 18px;")
        btn_pago = QPushButton("PROCESS AND BILL"); btn_pago.setObjectName("BtnSuccess"); btn_pago.setFixedHeight(50)
        btn_pago.clicked.connect(self.do_pago)
        
        calc_l.addWidget(self.total_lbl); calc_l.addWidget(self.cash); calc_l.addWidget(btn_pago)
        
        bot_layout.addWidget(fiscal_frame, 2); bot_layout.addWidget(pago_frame, 1); bot_layout.addWidget(cobro_frame, 2)
        
        # Wrap bottom layout in a widget to stop it from pushing the grid up uncontrollably
        bot_wrapper = QWidget()
        bot_wrapper.setLayout(bot_layout)
        bot_wrapper.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        
        main_l.addWidget(bot_wrapper, stretch=0)
        
        self.stack.addWidget(w)
        
        # Load initial catalog
        self.load_catalog()

    # --- WRAPPERS PARA ALERTAS Y LOGS EN CONSOLA ---
    def show_info(self, title, msg):
        print(f"ℹ️ UI INFO [{title}]: {msg}", flush=True)
        QMessageBox.information(self, title, msg)
        
    def show_warning(self, title, msg):
        print(f"⚠️ UI WARNING [{title}]: {msg}", flush=True)
        QMessageBox.warning(self, title, msg)
        
    def show_error(self, title, msg):
        print(f"❌ UI ERROR [{title}]: {msg}", flush=True)
        QMessageBox.critical(self, title, msg)

    # --- LÓGICA DE INTERFAZ ---

    def load_catalog(self, categoria=None, search_term=None):
        for i in reversed(range(self.prod_layout.count())): 
            widget = self.prod_layout.itemAt(i).widget()
            if widget is not None: widget.deleteLater()
            
        if search_term:
            productos = self.pos.buscar_producto(search_term)
        else:
            productos = self.pos.obtener_productos(categoria)
            
        row, col, max_cols = 0, 0, 4
        for p in productos:
            btn = QPushButton(f"{p.nombre}\n$ {p.precio_actual:,.2f}\nStock: {p.stock_local}")
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setStyleSheet("background-color: #1e293b; color: #f8fafc; border: 1px solid #38bdf8; border-radius: 8px; padding: 10px; font-weight: bold; min-height: 80px;")
            btn.clicked.connect(lambda checked, prod=p, button=btn: self.agregar_a_tabla(prod, button))
            self.prod_layout.addWidget(btn, row, col)
            col += 1
            if col >= max_cols:
                col = 0; row += 1

    def build_category_filters(self, categorias):
        for i in reversed(range(self.cat_layout.count())): 
            widget = self.cat_layout.itemAt(i).widget()
            if widget is not None: widget.deleteLater()
            
        btn_all = QPushButton("ALL")
        btn_all.setStyleSheet("background-color: #4f46e5; color: white; border-radius: 6px; padding: 10px; font-weight: bold; min-width: 100px;")
        btn_all.clicked.connect(lambda: self.load_catalog(None))
        self.cat_layout.addWidget(btn_all)
        
        for c in categorias:
            cat_name = c.get("nombre") if isinstance(c, dict) else str(c)
            btn = QPushButton(cat_name)
            btn.setStyleSheet("background-color: #0ea5e9; color: white; border-radius: 6px; padding: 10px; font-weight: bold; min-width: 100px;")
            btn.clicked.connect(lambda checked, cat=cat_name: self.load_catalog(cat))
            self.cat_layout.addWidget(btn)
        self.cat_layout.addStretch()

    # --- SYNC THREADING HELPERS ---

    def _start_sync(self, on_done_callback, fetch_pedidos=False, full_sync=False):
        """Send a work request to the persistent sync worker.
        If the worker is busy, the request is silently skipped.
        """
        self._current_sync_callback = on_done_callback
        self._sync_worker.request.emit(fetch_pedidos, full_sync)

    def _on_sync_result(self, sync_ok, sync_msg, categorias, pedidos):
        """Route results from the persistent worker to the appropriate callback."""
        cb = self._current_sync_callback
        if cb:
            cb(sync_ok, sync_msg, categorias, pedidos)

    # --- LÓGICA DE NEGOCIO ---

    def do_login(self):
            u_id = self.u.text()
            clave = self.p.text()
            
            # 1. Local Login (Guarantees access even if offline)
            if self.pos.login(u_id, clave): 
                # 2. Try to get a token from the Gateway in the background
                auth_ok, msg = self.sincronizador.autenticar(u_id, clave)
                if not auth_ok:
                    print(f"⚠️ Offline Mode or Auth Error: {msg}. Continuing with local cache.")
                
                # 3. Start the auto-sync timer now that we have credentials/token
                if not self.sync_timer.isActive():
                    self.sync_timer.start(5000)
                
                self.stack.setCurrentIndex(1)
            else: 
                self.show_error("Access Denied", "Incorrect credentials or inactive user.")

    def do_apertura(self):
        if self.pos.abrir_turno(self.f.text()):
            # Inicializamos el visor de caja
            self.fondo_inicial = float(self.pos.active_turno.monto_inicial)
            self.ventas_turno = 0.0
            self.actualizar_visor_caja()
            self.stack.setCurrentIndex(2)
        else:
            self.show_warning("Error", "Please enter a valid initial amount (Ex: 1500.50).")

    def actualizar_visor_caja(self):
        esperado = self.fondo_inicial + self.ventas_turno
        self.lbl_fondo.setText(f"FUND: $ {self.fondo_inicial:,.2f}")
        self.lbl_ventas.setText(f"SALES: $ {self.ventas_turno:,.2f}")
        self.lbl_esperado.setText(f"REGISTER SHOULD HAVE: $ {esperado:,.2f}")

    def on_typing(self, text):
        if len(text) >= 2:
            self.load_catalog(search_term=text)
        else: 
            self.load_catalog() # Restores full list

    def agregar_a_tabla(self, p, source_btn=None):
        if source_btn:
            if "background-color: #10b981" not in source_btn.styleSheet():
                source_btn.setProperty("orig_style", source_btn.styleSheet())
            orig = source_btn.property("orig_style")
            if orig:
                source_btn.setStyleSheet(orig + " background-color: #10b981; border: 2px solid #fff;")
                def _reset_style(btn=source_btn, style=orig):
                    try:
                        btn.setStyleSheet(style)
                    except RuntimeError:
                        pass  # Widget was deleted before timer fired
                QTimer.singleShot(150, _reset_style)
            
            
        idx = next((i for (i, it) in enumerate(self.carrito) if it["id"] == p.id_producto), None)
        if idx is not None:
            if self.carrito[idx]['cant'] + 1 > p.stock_local:
                self.show_warning("Stock Limit Reached", f"Cannot add more '{p.nombre}'. Only {p.stock_local} available in stock.")
                return
            self.carrito[idx]['cant'] += 1
            # Update Qty in column 1
            self.table.item(idx, 1).setText(str(self.carrito[idx]['cant']))
        else:
            if p.stock_local < 1:
                self.show_warning("Out of Stock", f"'{p.nombre}' is out of stock.")
                return
            row = self.table.rowCount(); self.table.insertRow(row)
            # Column 0: Product Name
            self.table.setItem(row, 0, QTableWidgetItem(p.nombre))
            # Column 1: Quantity
            self.table.setItem(row, 1, QTableWidgetItem("1"))
            # Column 2: Unit Price
            self.table.setItem(row, 2, QTableWidgetItem(str(p.precio_actual)))
            self.carrito.append({'id': p.id_producto, 'nombre': p.nombre, 'precio': p.precio_actual, 'cant': 1, 'tasa': p.tasa_impuesto, 'stock': p.stock_local})
        self.update_totals()

    def do_delete_item(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self.carrito.pop(row)
            self.update_totals()
            self.search.setFocus()
        else:
            self.show_warning("Attention", "Select a row in the table to delete it.")

    def on_payment_change(self, text):
        if text != "CASH":
            self.cash.setEnabled(False)
            self.cash.setText("0.00")
            self.cash.setStyleSheet("background-color: #334155; color: #94a3b8; font-size: 18px;")
        else:
            self.cash.setEnabled(True)
            self.cash.clear()
            self.cash.setStyleSheet("font-size: 18px;")

    def update_totals(self):
        try:
            extra = float(self.txt_extra_tip.text().strip())
        except ValueError:
            extra = 0.0
        sub, imp, pro, tot = self.pos.calcular_totales(self.carrito, propina_extra=extra)
        self.subtotal_lbl.setText(f"SUBTOTAL: $ {sub:,.2f}")
        self.itbis_lbl.setText(f"ITBIS TAX (18%): $ {imp:,.2f}")
        self.legaltip_lbl.setText(f"LEGAL TIP (10%): $ {pro:,.2f}")
        self.total_lbl.setText(f"TOTAL: $ {tot:,.2f}")

    def do_pago(self):
        if not self.carrito: 
            return self.show_warning("Attention", "No products in the cart.")
            
        # Validate stock during checkout as an extra safety measure
        for item in self.carrito:
            if item['cant'] > item.get('stock', 0):
                return self.show_warning("Stock Validation Error", f"The order quantity for '{item['nombre']}' exceeds available stock ({item.get('stock', 0)} available). Please adjust the cart.")
        
        ncf_num = "B0200000001" if "CONSUMER" in self.cb_ncf.currentText() else "B0100000001"
        
        metodo_combo = self.cb_metodo.currentText()
        metodo = "EFECTIVO"
        if metodo_combo == "CARD": metodo = "TARJETA"
        elif metodo_combo == "TRANSFER": metodo = "TRANSFERENCIA"
        
        cliente = self.txt_cliente.text().strip()
        notas = self.txt_notes.text().strip()
        
        ncf_type = self.cb_ncf.currentText()
        if ncf_type in ["TAX CREDIT", "GOVERNMENT"]:
            if not cliente:
                return self.show_warning("Missing Billing Information", f"Customer Name is required when issuing a {ncf_type} invoice.")
        
        if not cliente:
            cliente = "CASH CUSTOMER"
        
        try:
            extra = float(self.txt_extra_tip.text().strip())
        except ValueError:
            extra = 0.0
            
        sub, imp, pro, total_venta = self.pos.calcular_totales(self.carrito, propina_extra=extra)
        
        if metodo == "TARJETA" and not self.pos.current_import_uuid:
            total_str = f"$ {total_venta:,.2f}"
            subtotal_str = f"$ {sub:,.2f}"
            itbis_str = f"$ {imp:,.2f}"
            legal_tip_str = f"$ {pro:,.2f}"

            dialog = VerifoneDialog(total_str, subtotal_str=subtotal_str, itbis_str=itbis_str, legaltip_str=legal_tip_str, parent=self)
            if dialog.exec() != QDialog.Accepted:
                return
        
        cambio, msg = self.pos.procesar_venta(
            self.carrito, self.cash.text(), metodo, self.cb_ncf.currentText(), 
            ncf_num, notas, cliente, sincronizador=self.sincronizador, propina_extra=extra
        )
        
        if cambio is not None:
            # Actualizamos el visor de caja en memoria
            self.ventas_turno += float(total_venta)
            self.actualizar_visor_caja()
            
            self.show_info("Successful Transaction", f"Invoice saved correctly.\n\nChange to return: $ {cambio:,.2f}")
            
            # Limpieza del panel
            self.carrito = []; self.table.setRowCount(0); self.txt_extra_tip.clear(); self.update_totals()
            self.cash.clear(); self.txt_cliente.clear(); self.txt_notes.clear()
            self.cb_metodo.setCurrentIndex(0); self.cb_ncf.setCurrentIndex(0)
            self.load_catalog()  # Instantly update local UI product grid so minus stock shows
            self.search.setFocus()
        else: 
            self.show_warning("Transaction Error", msg)

    def do_cierre_caja(self):
        monto_fisico, ok = QInputDialog.getText(self, "Register Close (Z)", "Enter the total physical amount counted in the drawer ($):")
        if ok and monto_fisico:
            try:
                esperado, descuadre = self.pos.cerrar_turno(monto_fisico)
                reporte = (
                    f"--- Z CLOSE REPORT ---\n\n"
                    f"Expected Amount in System: $ {esperado:,.2f}\n"
                    f"Declared Physical Amount: $ {float(monto_fisico):,.2f}\n"
                    f"Discrepancy Detected: $ {descuadre:,.2f}\n\n"
                    f"The turn has been securely closed."
                )
                self.show_info("Close Completed", reporte)
                
                # Reseteamos variables y bloqueamos terminal volviendo al login
                self.ventas_turno = 0.0; self.fondo_inicial = 0.0
                self.u.clear(); self.p.clear(); self.f.clear()
                self.stack.setCurrentIndex(0)
            except Exception as e:
                self.show_error("Fatal Error", f"Could not close the register: {str(e)}")

    def do_abrir_mesas(self):
        """Open the Active Tables dialog. Creates it once, then reuses it."""
        if self._mesas_dialog is None:
            self._mesas_dialog = MesasDialog(self.sincronizador, self.pos, parent=self)
            self._mesas_dialog.order_selected.connect(self._on_pedido_importado)
        self._mesas_dialog.refresh()
        self._mesas_dialog.show()
        self._mesas_dialog.raise_()
        self._mesas_dialog.activateWindow()

    def _on_pedido_importado(self, data):
        """Called when user double-clicks an order in MesasDialog."""
        carrito = data.get("carrito", [])
        mesa = data.get("mesa", "")
        if not carrito:
            self.show_warning("Empty Order", "The selected order has no importable items.")
            return

        # Load cart into UI
        self.carrito = carrito
        self.table.setRowCount(0)
        for item in carrito:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(item['nombre']))
            self.table.setItem(row, 1, QTableWidgetItem(str(item['cant'])))
            self.table.setItem(row, 2, QTableWidgetItem(str(item['precio'])))
        self.update_totals()

        # Pre-fill customer if we have a mesa
        if mesa and str(mesa).strip():
            self.txt_cliente.setText(f"Table {mesa}")

        self.show_info("Order Imported",
            f"Remote order loaded — {len(carrito)} item(s).\n"
            f"Please select the NCF type and payment method, then press BILL.")

    def do_sincronizacion(self):
        """Sincroniza con el Core incluyendo empleados, categorias y ventas (threaded)."""
        self._start_sync(self._on_manual_sync_done, fetch_pedidos=True)

    def _on_manual_sync_done(self, sync_ok, sync_msg, categorias, pedidos):
        """Callback on main thread after manual sync finishes."""
        if categorias:
            self.build_category_filters(categorias)
        if pedidos and self._mesas_dialog and self._mesas_dialog.isVisible():
            self._mesas_dialog.populate_from_data(pedidos)
            
        # Refresh the UI grid with the new products from the DB
        if hasattr(self, 'search') and not self.search.text():
            self.load_catalog()
            
        if sync_ok:
            self.show_info("Sync Completed", sync_msg)
        else:
            self.show_warning("Sync Failed", sync_msg)

    def auto_sync(self):
        """Sincroniza silenciosamente en background (threaded)."""
        # Every 6 ticks (30s if timer is 5s) also fetch pending orders
        self._auto_sync_counter += 1
        fetch = (self._auto_sync_counter % 6 == 0)
        # Full DB Sync (Products, categories, etc) only on First Tick or Every 5 minutes (60 ticks)
        do_full = (self._auto_sync_counter == 1 or self._auto_sync_counter % 60 == 0)
        self._start_sync(self._on_auto_sync_done, fetch_pedidos=fetch, full_sync=do_full)

    def _on_auto_sync_done(self, sync_ok, sync_msg, categorias, pedidos):
        """Callback on main thread after auto-sync finishes. Silent — no dialogs."""
        if categorias:
            self.build_category_filters(categorias)
        # Refresh mesas dialog if open
        if pedidos and self._mesas_dialog and self._mesas_dialog.isVisible():
            self._mesas_dialog.populate_from_data(pedidos)
        
        # Silently update catalog to load new products
        if hasattr(self, 'search') and not self.search.text():
            self.load_catalog()

    def closeEvent(self, event):
        """Cleanly handle application exit by shutting down all worker threads."""
        try:
            if hasattr(self, '_sync_thread') and self._sync_thread.isRunning():
                self._sync_thread.quit()
                self._sync_thread.wait(2000)
            if hasattr(self, '_mesas_dialog') and self._mesas_dialog:
                self._mesas_dialog.cleanup_thread()
        except:
            pass
        super().closeEvent(event)