from db.connection import SessionLocal, transaction_scope
from models.entities import UsuarioLocal, ProductoLocal, TurnoCaja, FacturaLocal, DetalleFactura, LogCaja, SystemAppLog
import traceback
import bcrypt
from decimal import Decimal
import datetime
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
import os

class POSService:
    active_user = None
    active_turno = None

    def __init__(self):
        self.current_import_uuid = None  # Set when a remote order is loaded

    @staticmethod
    def log_system_event(nivel, modulo, mensaje, e=None):
        try:
            with transaction_scope() as db:
                stack = traceback.format_exc() if e else None
                # Trim stack to avoid huge payloads if necessary
                if stack and len(stack) > 2000: stack = stack[:2000] + "...(truncated)"
                lg = SystemAppLog(nivel=nivel, modulo_origen=modulo, mensaje=str(mensaje), stack_trace=stack)
                db.add(lg)
        except Exception as log_e: 
            print(f"Failed to log to SystemAppLog: {log_e}")

    def login(self, email_input, clave):
        db = SessionLocal()
        try:
            # 1. Basic validation
            if not email_input or "@" not in email_input:
                print(f"❌ Login Error: '{email_input}' is not a valid email.")
                return False

            # 2. Consult by Email
            user = db.query(UsuarioLocal).filter_by(
                email=email_input.strip(),
                activo=True
            ).first()

            if user:
                # 3. Verify password with bcrypt
                password_bytes = clave.encode('utf-8')
                hash_guardado_bytes = user.hash_clave.encode('utf-8')
                
                if bcrypt.checkpw(password_bytes, hash_guardado_bytes):
                    POSService.active_user = user
                    POSService.log_system_event("INFO", "POSService.login", f"Successful login for {email_input}")
                    return True
                else:
                    POSService.log_system_event("WARNING", "POSService.login", f"Incorrect password for {email_input}")
            else:
                POSService.log_system_event("WARNING", "POSService.login", f"Failed login attempt (not found/inactive) for {email_input}")
                
            return False
        except Exception as e:
            POSService.log_system_event("ERROR", "POSService.login", f"Error during login", e)
            return False
        finally:
            db.close()
    def abrir_turno(self, monto):
        try:
            with transaction_scope() as db:
                nuevo = TurnoCaja(
                    id_usuario=POSService.active_user.id_usuario,
                    id_sucursal=POSService.active_user.id_sucursal,
                    monto_inicial=Decimal(str(monto)),
                    estado='ABIERTO'
                )
                db.add(nuevo)
                db.flush()
                POSService.active_turno = nuevo
                POSService.log_system_event("INFO", "POSService.abrir_turno", f"Opened register shift, Initial $ {monto}")
            return True
        except Exception as e:
            POSService.log_system_event("ERROR", "POSService.abrir_turno", f"Error opening register shift", e)
            return False

    def cerrar_turno(self, monto_fisico):
        try:
            db = SessionLocal()
            ventas = db.query(FacturaLocal).filter_by(id_turno=POSService.active_turno.id_turno).all()
            total_ventas = sum(f.total_general for f in ventas)
            monto_esperado = POSService.active_turno.monto_inicial + total_ventas

            with transaction_scope() as db_trans:
                turno = db_trans.query(TurnoCaja).get(POSService.active_turno.id_turno)
                turno.fecha_cierre = datetime.datetime.now()
                turno.monto_calculado = monto_esperado
                turno.monto_fisico = Decimal(str(monto_fisico))
                turno.estado = 'CERRADO'
            
            descuadre = Decimal(str(monto_fisico)) - monto_esperado
            POSService.log_system_event("INFO", "POSService.cerrar_turno", f"Register closed. Expected: {monto_esperado}, Physical: {monto_fisico}, Diff: {descuadre}")
            return float(monto_esperado), float(descuadre)
        except Exception as e:
            POSService.log_system_event("ERROR", "POSService.cerrar_turno", "Failed to close register", e)
            raise e
        finally: db.close()

    def buscar_producto(self, termino):
        db = SessionLocal()
        try:
            # Si el término es un número (o un string que parece número), buscamos por ID
            if str(termino).isdigit():
                return db.query(ProductoLocal).filter(ProductoLocal.id_producto == int(termino)).all()
            
            # Si son letras, buscamos por Nombre (como estaba antes)
            return db.query(ProductoLocal).filter(ProductoLocal.nombre.contains(termino)).all()
        finally: 
            db.close()

    def obtener_productos(self, categoria=None):
        db = SessionLocal()
        try:
            from models.entities import ProductoLocal, CategoriaLocal
            query = db.query(ProductoLocal)
            if categoria and categoria != "TODOS" and categoria != "ALL":
                cat_obj = db.query(CategoriaLocal).filter(CategoriaLocal.nombre == categoria).first()
                if cat_obj:
                    query = query.filter(ProductoLocal.id_categoria == cat_obj.id)
                else:
                    return [] # Or we could just return an empty list if category not found locally
            return query.order_by(ProductoLocal.nombre).all()
        finally:
            db.close()

    def calcular_totales(self, carrito, propina_extra=0):
        sub = sum(Decimal(str(i['precio'])) * i['cant'] for i in carrito)
        imp = sum((Decimal(str(i['precio'])) * Decimal(str(i['tasa']))) * i['cant'] for i in carrito)
        propina_legal = sub * Decimal("0.10")
        try:
            extra = Decimal(str(propina_extra)) if propina_extra else Decimal("0")
        except:
            extra = Decimal("0")
        tot = sub + imp + propina_legal + extra
        return sub, imp, propina_legal, tot

    def cargar_pedido_remoto(self, pedido_header, items_raw):
        """Populate the in-memory cart from a remote order.
        pedido_header: the dict from /api/v1/pedidos/pendientes
        items_raw: list of item dicts from /api/v1/pedidos/{uuid}
        Returns (carrito, warnings) where warnings is a list of user-readable strings.
        """
        carrito = []
        warnings = []
        self.current_import_uuid = pedido_header.get("factura_local_uuid")

        db = SessionLocal()
        try:
            for item in items_raw:
                # Flexible key mapping
                id_prod = (item.get("id_producto") or item.get("producto_id") or
                           item.get("id") or item.get("product_id"))
                cantidad = int(item.get("cantidad") or item.get("qty") or item.get("quantity") or 1)
                precio_override = item.get("precio_unitario") or item.get("precio") or item.get("price")

                if not id_prod:
                    warnings.append(f"Skipped item with no product ID: {item}")
                    continue

                prod = db.query(ProductoLocal).filter_by(id_producto=int(id_prod)).first()
                if not prod:
                    warnings.append(f"Product ID {id_prod} not found in local cache — skipped.")
                    continue

                if prod.stock_local < cantidad and prod.stock_local != 9999:
                    warnings.append(
                        f"'{prod.nombre}': requested {cantidad} but only {prod.stock_local} in stock."
                    )
                    # Still load it but flag it

                precio = Decimal(str(precio_override)) if precio_override else prod.precio_actual
                carrito.append({
                    'id': prod.id_producto,
                    'nombre': prod.nombre,
                    'precio': precio,
                    'cant': cantidad,
                    'tasa': prod.tasa_impuesto,
                    'stock': prod.stock_local,
                })
        finally:
            db.close()

        POSService.log_system_event(
            "INFO", "POSService.cargar_pedido_remoto",
            f"Loaded remote order {self.current_import_uuid} — {len(carrito)} items, {len(warnings)} warnings."
        )
        return carrito, warnings

    def procesar_venta(self, carrito, efectivo, metodo, ncf_tipo, ncf_num, notas, cliente,
                       sincronizador=None, propina_extra=0):
        """Process a sale. If self.current_import_uuid is set, use it as the invoice ID
        and notify CORE when done."""
        sub, imp, prop_legal, total = self.calcular_totales(carrito, propina_extra=propina_extra)
        try:
            efec_val = efectivo.strip() if efectivo and str(efectivo).strip() else "0"
            efec = Decimal(str(efec_val)) if metodo == "EFECTIVO" else total
        except Exception as e:
            POSService.log_system_event("WARNING", "POSService.procesar_venta", f"Invalid cash format: '{efectivo}'", e)
            return None, "Invalid cash amount entered."
            
        if metodo == "EFECTIVO" and efec < total:
            POSService.log_system_event("WARNING", "POSService.procesar_venta", f"Insufficient cash: {efec} < {total}")
            return None, "Insufficient cash"

        # Determine invoice ID: use external UUID if importing a remote order
        import_uuid = self.current_import_uuid

        try:
            with transaction_scope() as db:
                factura = FacturaLocal(
                    id_factura=import_uuid if import_uuid else None,
                    id_turno=POSService.active_turno.id_turno,
                    id_sucursal=POSService.active_user.id_sucursal,
                    subtotal=sub,
                    total_impuestos=imp,
                    propina_legal=prop_legal,
                    # Ensure property is in entities.py: if not, default will just ignore or crash. We know it is.
                    propina_extra=Decimal(str(propina_extra)) if propina_extra else 0,
                    total_general=total,
                    metodo_pago=metodo,
                    canal_origen="MOVIL" if import_uuid else "CAJA",
                    estado="FACTURADO",
                )
                # Only set id explicitly when we have an external one (no IDENTITY on this column)
                if import_uuid:
                    factura.id_factura = import_uuid

                db.add(factura)
                db.flush()

                for i in carrito:
                    p_unit = Decimal(str(i['precio']))
                    m_imp = p_unit * Decimal(str(i['tasa']))
                    det = DetalleFactura(
                        id_factura=factura.id_factura, id_producto=i['id'],
                        cantidad=i['cant'], precio_unitario=p_unit,
                        monto_impuesto=m_imp, subtotal_linea=(p_unit + m_imp) * i['cant']
                    )
                    db.add(det)

                    # Deduct local stock — 9999 = unlimited stock marker, never decrement
                    prod = db.query(ProductoLocal).filter_by(id_producto=i['id']).first()
                    if prod and prod.stock_local is not None and prod.stock_local != 9999:
                        prod.stock_local = max(0, prod.stock_local - i['cant'])

                # Construct payload for remote sync
                detalles_payload = []
                for i in carrito:
                    p_unit = Decimal(str(i['precio']))
                    m_imp = p_unit * Decimal(str(i['tasa']))
                    detalles_payload.append({
                        "producto_id": i['id'],
                        "cantidad": i['cant'],
                        "precio_unitario": float(p_unit),
                        "monto_impuesto": float(m_imp),
                        "subtotal_linea": float((p_unit + m_imp) * i['cant']),
                        "detalle_local_uuid": None
                    })
                
                pedido_payload = {
                    "factura_local_uuid": str(factura.id_factura),
                    "mesa": None,
                    "subtotal": float(sub),
                    "total_impuestos": float(imp),
                    "propina_legal": float(prop_legal),
                    "propina_extra": float(propina_extra) if propina_extra else 0.0,
                    "total_general": float(total),
                    "detalles": detalles_payload
                }

                self.generar_ticket_pdf(factura, carrito, efec, ncf_tipo, ncf_num, notas, cliente)

                log_data = f"Factura:{factura.id_factura} | Cliente:{cliente} | Notas:{notas} | NCF:{ncf_num} | Pago:{metodo} | Origen:{'REMOTO' if import_uuid else 'LOCAL'}"
                log = LogCaja(id_usuario=POSService.active_user.id_usuario,
                              id_sucursal=POSService.active_user.id_sucursal,
                              nivel="INFO", accion="VENTA_FISCAL", descripcion=log_data)
                db.add(log)

            # --- If remote, notify CORE gateway to close the order ---
            if import_uuid and sincronizador:
                ok, msg = sincronizador.notificar_facturacion_remota(import_uuid)
                if not ok:
                    print(f"⚠️ CORE notification failed for {import_uuid}: {msg}", flush=True)
                    POSService.log_system_event("WARNING", "POSService.procesar_venta",
                                               f"Could not notify CORE for {import_uuid}: {msg}")
            elif not import_uuid and sincronizador:
                ok, msg = sincronizador.crear_pedido(pedido_payload)
                if not ok:
                    print(f"⚠️ CORE order sync failed: {msg}", flush=True)
                    POSService.log_system_event("WARNING", "POSService.procesar_venta",
                                               f"Could not create order in CORE: {msg}")
                else:
                    factura_id_str = str(factura.id_factura)
                    ok2, msg2 = sincronizador.notificar_facturacion_remota(factura_id_str)
                    if not ok2:
                        print(f"⚠️ CORE order billing failed: {msg2}", flush=True)
                        POSService.log_system_event("WARNING", "POSService.procesar_venta",
                                                   f"Could not bill newly created order in CORE: {msg2}")

            self.current_import_uuid = None  # Reset after successful billing
            return float(efec - total), "Successful Sale"
        except Exception as e:
            POSService.log_system_event("ERROR", "POSService.procesar_venta", "Fatal error during sale processing", e)
            return None, "A critical database error occurred during billing."

    def descontar_stock_remoto(self, items):
        """Manually deduct stock for remote orders right after payment to avoid sync race conditions.
        items uses the mapped remote format e.g. [{"id_producto": X, "cantidad": Y}, ...]
        """
        try:
            with transaction_scope() as db:
                for item in items:
                    pid = item.get("id_producto") or item.get("id") or item.get("producto_id")
                    cant = int(item.get("cantidad") or item.get("cant") or item.get("qty") or 0)
                    if pid and cant > 0:
                        prod = db.query(ProductoLocal).filter_by(id_producto=int(pid)).first()
                        # 9999 = unlimited stock marker — never decrement
                        if prod and prod.stock_local is not None and prod.stock_local != 9999:
                            prod.stock_local = max(0, prod.stock_local - cant)
        except Exception as e:
            POSService.log_system_event("WARNING", "POSService.descontar_stock_remoto", "Failed to deduct remote stock locally", e)

    def generar_ticket_desde_pedido(self, pedido, carrito_raw, ncf_tipo="CONSUMER", ncf_num="B0200000001", notas="", cliente=""):
        """Generate a PDF ticket for a remote order paid directly from the Active Tables dialog.
        pedido: the raw dict from obtener_cuentas_abiertas.
        carrito_raw: list of cart item dicts with keys 'nombre', 'cant', 'precio'.
        """
        import types
        # Some remote systems don't explicitly send propina_legal or propina_extra, so we calculate/safely get it
        subt_val = pedido.get("subtotal", 0)
        prop_legal_val = pedido.get("propina_legal")
        if not prop_legal_val:
            prop_legal_val = float(subt_val) * 0.10

        # Build a lightweight factura-like namespace so generar_ticket_pdf can be reused as-is
        factura = types.SimpleNamespace(
            id_factura=pedido.get("factura_local_uuid", "REMOTE"),
            fecha_hora=None,  # will fall back to datetime.now() inside generar_ticket_pdf
            subtotal=subt_val,
            total_impuestos=pedido.get("total_impuestos", 0),
            propina_legal=prop_legal_val,
            propina_extra=pedido.get("propina_extra", 0),
            total_general=pedido.get("total_general", 0),
            metodo_pago="TARJETA",
        )
        # Cash equals total (card payment — no change)
        efec = factura.total_general
        # Normalise carrito keys so generar_ticket_pdf can read 'precio', 'cant', 'nombre'
        carrito = []
        for item in carrito_raw:
            carrito.append({
                'nombre': item.get('nombre') or item.get('name') or 'Product',
                'cant':   item.get('cant') or item.get('cantidad') or item.get('qty') or 1,
                'precio': item.get('precio') or item.get('precio_unitario') or item.get('price') or 0,
            })
        self.generar_ticket_pdf(factura, carrito, efec, ncf_tipo, ncf_num, notas, cliente)

    def generar_ticket_pdf(self, factura, carrito, efec, ncf_tipo, ncf_num, notas, cliente):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))

            project_root = os.path.dirname(current_dir) 

            folder = os.path.join(project_root, "Tickets")

            if not os.path.exists(folder):
                os.makedirs(folder)
            

            id_str = str(factura.id_factura)
            filename = os.path.join(folder, f"Ticket_{id_str}.pdf")
            
            print(f"DEBUG: Intentando guardar ticket en: {filename}")
            
            c = canvas.Canvas(filename, pagesize=(80*mm, 180*mm))
            y = 170*mm
            
            # 2. Manejo de fecha (si es None, usamos la hora actual)
            fecha_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            if factura.fecha_hora:
                fecha_str = factura.fecha_hora.strftime('%Y-%m-%d %H:%M')

            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(40*mm, y, "MASTER POS SYSTEM")
            y -= 5*mm
            c.setFont("Helvetica", 8)
            c.drawCentredString(40*mm, y, "INVOICE OF " + str(ncf_tipo).upper())
            y -= 4*mm
            c.drawCentredString(40*mm, y, f"NCF: {ncf_num}")
            y -= 6*mm
            
            c.line(5*mm, y, 75*mm, y); y -= 4*mm
            c.drawString(5*mm, y, f"Customer: {str(cliente)[:25]}")
            y -= 4*mm
            notas_str = notas if notas and str(notas).strip() else "N/A"
            c.drawString(5*mm, y, f"Notes: {notas_str}")
            y -= 4*mm
            c.drawString(5*mm, y, f"Date: {fecha_str}")
            y -= 4*mm
            c.line(5*mm, y, 75*mm, y); y -= 6*mm
            
            c.setFont("Helvetica-Bold", 7)
            c.drawString(5*mm, y, "QTY     DESCRIPTION")
            c.drawRightString(75*mm, y, "PRICE")
            y -= 4*mm
            c.setFont("Helvetica", 7)
            
            for item in carrito:
                precio_f = float(item['precio'])
                c.drawString(5*mm, y, f"{item['cant']}x  {str(item['nombre'])[:20]}")
                c.drawRightString(75*mm, y, f"{precio_f:.2f}")
                y -= 4*mm
                if y < 30*mm: 
                    c.showPage()
                    y = 170*mm 
            
            y -= 2*mm
            c.line(5*mm, y, 75*mm, y); y -= 6*mm
            
            c.setFont("Helvetica", 8)
            c.drawString(5*mm, y, "SUBTOTAL:")
            c.drawRightString(75*mm, y, f"$ {float(factura.subtotal):.2f}")
            y -= 4*mm
            c.drawString(5*mm, y, "ITBIS TAX (18%):")
            c.drawRightString(75*mm, y, f"$ {float(factura.total_impuestos):.2f}")
            y -= 4*mm
            c.drawString(5*mm, y, "LEGAL TIP (10%):")
            c.drawRightString(75*mm, y, f"$ {float(factura.propina_legal):.2f}")
            y -= 4*mm
            
            prop_extra = getattr(factura, 'propina_extra', 0)
            if prop_extra and float(prop_extra) > 0:
                c.drawString(5*mm, y, "EXTRA TIP:")
                c.drawRightString(75*mm, y, f"$ {float(prop_extra):.2f}")
                y -= 4*mm
                
            y -= 2*mm
            c.setFont("Helvetica-Bold", 10)
            c.drawString(5*mm, y, "TOTAL:")
            c.drawRightString(75*mm, y, f"$ {float(factura.total_general):.2f}")
            y -= 7*mm
            
            c.setFont("Helvetica", 8)
            c.drawString(5*mm, y, f"Method: {factura.metodo_pago}")
            y -= 4*mm
            c.drawString(5*mm, y, f"Cash: $ {float(efec):.2f}")
            y -= 4*mm
            cambio = float(efec) - float(factura.total_general)
            c.drawString(5*mm, y, f"Change: $ {cambio:.2f}")
            y -= 10*mm
            c.drawCentredString(40*mm, y, "Thank you for your purchase") 
            
            c.save()
            print(f"✅ Ticket successfully generated at: {filename}")
            
        except Exception as e:
            POSService.log_system_event("ERROR", "POSService.generar_ticket_pdf", "Could not generate PDF invoice ticket", e)
            print(f"❌ Fatal PDF Error: {str(e)}")