import requests
import traceback
from db.connection import SessionLocal, transaction_scope
from models.entities import FacturaLocal, UsuarioLocal, SystemAppLog, DetalleFactura, TurnoCaja


class SyncService:
    def __init__(self, api_base_url="http://localhost:8001"):
        self.api_base_url = api_base_url
        self.token = None

    @staticmethod
    def _log(nivel, modulo, mensaje, e=None):
        try:
            with transaction_scope() as db:
                stack = traceback.format_exc() if e else None
                if stack and len(stack) > 2000: stack = stack[:2000] + "...(truncated)"
                db.add(SystemAppLog(nivel=nivel, modulo_origen=modulo, mensaje=str(mensaje), stack_trace=stack))
        except Exception as log_e:
            print(f"SyncService log failure: {log_e}")

    def autenticar(self, identificador, password):
        url = f"{self.api_base_url}/api/v1/auth/login"
        payload = {"username": identificador.strip(), "password": password.strip()}
        try:
            response = requests.post(url, data=payload, timeout=10)
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                SyncService._log("INFO", "SyncService.autenticar", f"Successfully authenticated user '{identificador}'")
                return True, "Authenticated successfully"
            SyncService._log("WARNING", "SyncService.autenticar", f"Authentication failed for user '{identificador}': HTTP {response.status_code}")
            return False, "Invalid credentials"
        except Exception as e:
            SyncService._log("ERROR", "SyncService.autenticar", f"Connection error during authentication", e)
            return False, f"Connection error: {str(e)}"

    def sincronizar_ventas_pendientes(self):
        db = SessionLocal()
        try:
            ventas = db.query(FacturaLocal).filter(FacturaLocal.sincronizado == False).all()

            if not ventas:
                return True, "No pending sales to sync."

            exitos = 0
            for v in ventas:
                try:
                    detalles = db.query(DetalleFactura).filter_by(id_factura=v.id_factura).all()

                    user_id = None
                    if v.id_turno:
                        turno = db.query(TurnoCaja).filter_by(id_turno=v.id_turno).first()
                        if turno:
                            user_id = turno.id_usuario

                    # PedidoCreate schema: detalles only need producto_id + cantidad.
                    # Financial fields (precio_unitario, monto_impuesto, subtotal_linea)
                    # belong to DetallePedidoRequest and must NOT be sent here.
                    detalles_create = [
                        {
                            "producto_id": d.id_producto,
                            "cantidad": d.cantidad,
                            "detalle_local_uuid": str(d.id_detalle) if hasattr(d, 'id_detalle') else None,
                        }
                        for d in detalles
                    ]

                    # PedidoCreate payload — no subtotal / total_general / propina_legal here.
                    payload = {
                        "empleado_id": user_id,
                        "canal_origen": v.canal_origen or "CAJA",
                        "factura_local_uuid": str(v.id_factura),
                        "mesa": v.mesa,
                        "cliente_id": v.id_cliente,
                        "propina_extra": float(v.propina_extra) if hasattr(v, 'propina_extra') and v.propina_extra else 0.0,
                        "detalles": detalles_create,
                    }

                    # crear_pedido now handles both create + /facturar internally.
                    ok, msg = self.crear_pedido(payload)
                    if ok:
                        v.sincronizado = True
                        exitos += 1
                    else:
                        SyncService._log("WARNING", "SyncService.sincronizar_ventas",
                                         f"Failed to create/bill {v.id_factura}: {msg}")

                except Exception as ex:
                    SyncService._log("ERROR", "SyncService.sincronizar_ventas", f"Error syncing sale {v.id_factura}", ex)

            db.commit()
            SyncService._log("INFO", "SyncService.sincronizar_ventas", f"Synced {exitos} pending sales.")
            return True, f"{exitos} sales synced successfully."
        except Exception as e:
            db.rollback()
            SyncService._log("ERROR", "SyncService.sincronizar_ventas", "Error syncing pending sales", e)
            return False, f"Sync error: could not upload pending sales."
        finally:
            db.close()

    def sincronizar_empleados(self):
        url = f"{self.api_base_url}/api/v1/empleados/locales"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            headers["x-gateway-token"] = self.token
            
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, dict):
                    data = data.get("empleados") or data.get("data") or data.get("results") or []
                
                print(f"📡 Employee sync: received {len(data)} records from API", flush=True)
                if data and len(data) > 0:
                    print(f"📡 Sample employee keys: {list(data[0].keys())}", flush=True)
                
                db = SessionLocal()
                saved = 0
                try:
                    for emp in data:
 
                        emp_id = emp.get("id_usuario") or emp.get("id_empleado") or emp.get("id") or emp.get("ID_Usuario")
                        if not emp_id:
                            print(f"⚠️ Skipping employee with no ID: {emp}", flush=True)
                            continue
                        
                        user = db.query(UsuarioLocal).filter_by(id_usuario=int(emp_id)).first()
                        if not user:
                            user = UsuarioLocal(id_usuario=int(emp_id))
                            db.add(user)
                        

                        user.nombre = emp.get("nombre_completo") or emp.get("nombre") or emp.get("Nombre") or emp.get("name") or user.nombre
                        user.hash_clave = emp.get("hash_clave") or emp.get("Hash_Clave") or emp.get("clave") or emp.get("password") or user.hash_clave
                        user.id_sucursal = emp.get("id_sucursal") or emp.get("ID_Sucursal") or emp.get("sucursal") or user.id_sucursal or 1
                        user.email = emp.get("gmail") or emp.get("email") or emp.get("Email") or emp.get("correo") or user.email
                        
                        activo_val = emp.get("activo") if "activo" in emp else emp.get("Activo") if "Activo" in emp else None
                        if activo_val is not None:
                            user.activo = activo_val
                        
                        saved += 1
                    
                    db.flush()
                    db.commit()
                    print(f"✅ Employee sync: saved {saved} employees to local DB", flush=True)
                    SyncService._log("INFO", "SyncService.sincronizar_empleados", f"Synced and saved {saved} employees to local DB.")
                except Exception as e:
                    db.rollback()
                    print(f"❌ Employee sync DB error: {e}", flush=True)
                    SyncService._log("ERROR", "SyncService.sincronizar_empleados", "Error saving employees to local DB", e)
                finally:
                    db.close()
                return True, f"Employees synced: {saved}"
            SyncService._log("WARNING", "SyncService.sincronizar_empleados", f"Employee sync failed: HTTP {response.status_code}")
            return False, f"Error: {response.status_code}"
        except Exception as e:
            SyncService._log("ERROR", "SyncService.sincronizar_empleados", "Connection error during employee sync", e)
            return False, str(e)

    def sincronizar_categorias(self):
        url = f"{self.api_base_url}/api/v1/productos/categorias"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"📡 Category sync: received {len(data)} categories from API", flush=True)
                if data and len(data) > 0:
                    print(f"📡 Sample category: {data[0]}", flush=True)
                from models.entities import CategoriaLocal
                from sqlalchemy import text
                db = SessionLocal()
                saved = 0
                try:
                    db.execute(text("SET IDENTITY_INSERT [Categorias] ON"))
                    for cat in data:
                        cat_id = cat.get('id') or cat.get('Id')
                        if not cat_id: continue
                        
                        existente = db.query(CategoriaLocal).filter_by(id=int(cat_id)).first()
                        if not existente:
                            nueva = CategoriaLocal(
                                id=int(cat_id),
                                nombre=cat.get('nombre') or 'Unknown',
                                descripcion=cat.get('descripcion')
                            )
                            db.add(nueva)
                        else:
                            existente.nombre = cat.get('nombre') or existente.nombre
                            existente.descripcion = cat.get('descripcion') or existente.descripcion
                        saved += 1
                    db.commit()
                    print(f"✅ Category sync: saved {saved} categories to local DB", flush=True)
                except Exception as e:
                    db.rollback()
                    print(f"❌ Category sync DB error: {e}", flush=True)
                    SyncService._log("ERROR", "SyncService.sincronizar_categorias", "DB Error", e)
                finally:
                    try:
                        db.execute(text("SET IDENTITY_INSERT [Categorias] OFF"))
                        db.commit()
                    except: pass
                    db.close()
                    
                return data
            print(f"⚠️ Category sync failed: HTTP {response.status_code}", flush=True)
            SyncService._log("WARNING", "SyncService.sincronizar_categorias", f"Category sync failed: HTTP {response.status_code}")
            return []
        except Exception as e:
            print(f"❌ Category sync connection error: {e}", flush=True)
            SyncService._log("ERROR", "SyncService.sincronizar_categorias", "Connection error during category sync", e)
            return []

    def sincronizar_productos(self):
        url = f"{self.api_base_url}/api/v1/productos/"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()

                if isinstance(data, dict):
                    data = data.get("productos") or data.get("data") or data.get("results") or []
                
                print(f"📡 Product sync: received {len(data)} records from API", flush=True)
                if data and len(data) > 0:
                    print(f"📡 Sample product: {data[0]}", flush=True)
                
                from models.entities import ProductoLocal
                db = SessionLocal()
                saved = 0
                try:
                    for prod in data:
                        prod_id = prod.get("id_producto") or prod.get("id") or prod.get("ID_Producto")
                        if not prod_id:
                            continue
                        
                        is_new = False
                        p = db.query(ProductoLocal).filter_by(id_producto=int(prod_id)).first()
                        if not p:
                            p = ProductoLocal(id_producto=int(prod_id))
                            db.add(p)
                            is_new = True

                        p.nombre = prod.get("nombre") or prod.get("Nombre") or prod.get("nombre_producto") or p.nombre or "Sin Nombre"
                        
                        precio_val = prod.get("precio_actual") or prod.get("precio") or prod.get("Precio") or prod.get("Precio_Venta") or prod.get("precio_base")
                        p.precio_actual = float(precio_val) if precio_val is not None else (p.precio_actual or 0.0)
                        
                        tasa_val = prod.get("tasa_impuesto") or prod.get("impuesto")
                        p.tasa_impuesto = float(tasa_val) if tasa_val is not None else (p.tasa_impuesto or 0.18)

                        if is_new:
                            stock_val = prod.get("stock_local") or prod.get("stock") or prod.get("cantidad") or prod.get("cantidad_disponible")
                            p.stock_local = int(stock_val) if stock_val is not None else 0
                        
                        cat_id = prod.get("categoria_id") or prod.get("id_categoria") or prod.get("Id_Categoria")
                        if cat_id is not None:
                            p.id_categoria = int(cat_id)
                        
                        saved += 1
                        
                    db.flush()
                    db.commit()
                    print(f"✅ Product sync: saved {saved} products to local DB", flush=True)
                    SyncService._log("INFO", "SyncService.sincronizar_productos", f"Synced and saved {saved} products to local DB.")
                except Exception as e:
                    db.rollback()
                    print(f"❌ Product sync DB error: {e}", flush=True)
                    SyncService._log("ERROR", "SyncService.sincronizar_productos", "Error saving products to local DB", e)
                finally:
                    db.close()
                return True, f"Products synced: {saved}"
            SyncService._log("WARNING", "SyncService.sincronizar_productos", f"Product sync failed: HTTP {response.status_code}")
            return False, f"Error: {response.status_code}"
        except Exception as e:
            SyncService._log("ERROR", "SyncService.sincronizar_productos", "Connection error during product sync", e)
            return False, str(e)

    def obtener_stock_producto(self, producto_id):
        url = f"{self.api_base_url}/api/v1/inventario/{producto_id}"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            print(f"[Stock] Requesting stock for producto {producto_id}", flush=True)
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                stock = (
                    data.get("stock") if data.get("stock") is not None else
                    None
                )
                if stock is not None:
                    return int(stock)
                print(f"[Stock] WARNING: No stock key found for producto {producto_id}: {data}", flush=True)
                return -1
            print(f"[Stock] WARNING: HTTP {response.status_code} for producto {producto_id}: {response.text[:200]}", flush=True)
            return -1
        except Exception as e:
            print(f"[Stock] ERROR for producto {producto_id}: {e}", flush=True)
            return -1

    def crear_pedido(self, payload: dict):
        """Create a new order in CORE and immediately bill it.
        Step 1 — POST /api/v1/pedidos/          (PedidoCreate)
        Step 2 — POST /api/v1/pedidos/{uuid}/facturar  (runs right after step 1 succeeds)
        """
        create_url = f"{self.api_base_url}/api/v1/pedidos/"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        factura_uuid = payload.get("factura_local_uuid")

        try:
            # Step 1 — create the order
            print(f"📡 [crear_pedido] POST {create_url}", flush=True)
            response = requests.post(create_url, headers=headers, json=payload, timeout=10)
            print(f"📡 [crear_pedido] Create response: HTTP {response.status_code} — {response.text[:200]}", flush=True)

            if response.status_code not in (200, 201):
                error_text = response.text[:200] if response.text else "No response body"
                return False, f"CORE returned HTTP {response.status_code}: {error_text}"

            # Step 2 — immediately bill the order
            if factura_uuid:
                ok, msg = self.notificar_facturacion_remota(str(factura_uuid))
                if not ok:
                    # Order was created but billing failed — log and surface the error.
                    SyncService._log("WARNING", "SyncService.crear_pedido",
                                     f"Order {factura_uuid} created but /facturar failed: {msg}")
                    return False, f"Order created but billing failed: {msg}"

            return True, "Pedido created and billed successfully."

        except Exception as e:
            print(f"❌ [crear_pedido] Connection error: {e}", flush=True)
            return False, f"Connection error: {str(e)}"


    def obtener_cuentas_abiertas(self):
        url = f"{self.api_base_url}/api/v1/pedidos/pendientes"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            print(f"📡 [MESAS] GET {url}", flush=True)
            response = requests.get(url, headers=headers, timeout=10)
            print(f"📡 [MESAS] HTTP {response.status_code}", flush=True)

            if response.status_code == 200:
                raw = response.text
                print(f"📡 [MESAS] Raw response (first 500 chars): {raw[:500]}", flush=True)
                data = response.json()

                # Unwrap envelope if the API returns {"pedidos": [...]} or similar
                if isinstance(data, dict):
                    print(f"📡 [MESAS] Response is a dict, keys: {list(data.keys())}", flush=True)
                    data = data.get("pedidos") or data.get("data") or data.get("results") or []

                print(f"📡 [MESAS] Orders in list: {len(data)}", flush=True)
                if data:
                    print(f"📡 [MESAS] Sample order keys: {list(data[0].keys())}", flush=True)
                    print(f"📡 [MESAS] Sample order estados: {[p.get('estado') or p.get('Estado') for p in data[:5]]}", flush=True)

                filtered_data = [p for p in data if (p.get("estado") or p.get("Estado")) == "POR_FACTURAR"]

                print(f"✅ [MESAS] {len(filtered_data)} POR_FACTURAR orders returned to UI.", flush=True)
                SyncService._log(
                    "INFO", "SyncService.obtener_cuentas_abiertas",
                    f"Fetched {len(data)} orders from gateway, {len(filtered_data)} are POR_FACTURAR."
                )
                return filtered_data

            if response.status_code == 401:
                print("⚠️ [MESAS] 401 Unauthorized — token expired or not set.", flush=True)
                SyncService._log("WARNING", "SyncService.obtener_cuentas_abiertas", "401 Unauthorized fetching open orders.")
                return []

            print(f"⚠️ [MESAS] Unexpected HTTP {response.status_code}: {response.text[:300]}", flush=True)
            SyncService._log("WARNING", "SyncService.obtener_cuentas_abiertas",
                             f"HTTP {response.status_code}: {response.text[:200]}")
            return []
        except Exception as e:
            print(f"❌ [MESAS] Connection error: {e}", flush=True)
            SyncService._log("ERROR", "SyncService.obtener_cuentas_abiertas", "Connection error fetching open orders", e)
            return []

    def obtener_detalle_pedido(self, factura_uuid):
        url = f"{self.api_base_url}/api/v1/pedidos/{factura_uuid}"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            print(f"📡 Fetching order detail: {url}", flush=True)
            response = requests.get(url, headers=headers, timeout=10)
            print(f"📡 Order detail response: HTTP {response.status_code}", flush=True)
            if response.status_code == 200:
                data = response.json()
                print(f"📡 Order detail raw keys: {list(data.keys()) if isinstance(data, dict) else 'list'}", flush=True)
                print(f"📡 Order detail raw data: {data}", flush=True)

                if isinstance(data, list):
                    print(f"✅ Order detail: {len(data)} items (root list)", flush=True)
                    return data
                items = (data.get("items") or data.get("detalles") or
                         data.get("lineas") or data.get("productos") or [])
                print(f"✅ Order detail: {len(items)} items found", flush=True)
                return items
            print(f"⚠️ Order detail failed: HTTP {response.status_code} — {response.text[:200]}", flush=True)
            SyncService._log("WARNING", "SyncService.obtener_detalle_pedido",
                             f"Detail fetch failed for {factura_uuid}: HTTP {response.status_code}")
            return []
        except Exception as e:
            print(f"❌ Order detail connection error: {e}", flush=True)
            SyncService._log("ERROR", "SyncService.obtener_detalle_pedido",
                             f"Connection error fetching detail for {factura_uuid}", e)
            return []

    def notificar_facturacion_remota(self, factura_uuid):

        url = f"{self.api_base_url}/api/v1/pedidos/{factura_uuid}/facturar"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            print(f"📡 Sending payment confirmation to CORE: POST {url}", flush=True)

            response = requests.post(url, headers=headers, json={}, timeout=10)
            print(f"📡 Payment confirmation response: HTTP {response.status_code}", flush=True)
            
            if response.status_code in (200, 201):
                SyncService._log("INFO", "SyncService.notificar_facturacion_remota",
                                 f"Billed remote order {factura_uuid} — CORE notified.")
                return True, "Remote order closed successfully."
            
            error_text = response.text[:200] if response.text else "No response body"
            print(f"⚠️ Payment confirmation failed: {error_text}", flush=True)
            SyncService._log("WARNING", "SyncService.notificar_facturacion_remota",
                             f"CORE notification failed for {factura_uuid}: HTTP {response.status_code}")
            return False, f"CORE returned HTTP {response.status_code}: {error_text}"
        except Exception as e:
            print(f"❌ Payment confirmation connection error: {e}", flush=True)
            SyncService._log("ERROR", "SyncService.notificar_facturacion_remota",
                             f"Connection error notifying CORE for {factura_uuid}", e)
            return False, f"Connection error: {str(e)}"
