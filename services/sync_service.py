import time
import requests
import traceback
from db.connection import SessionLocal, transaction_scope
from models.entities import FacturaLocal, UsuarioLocal, SystemAppLog, DetalleFactura, TurnoCaja


class SyncService:
    def __init__(self, api_base_url="http://localhost:8001"):
        self.api_base_url = api_base_url
        self.token = None
        self._offline_until = 0.0
        self._offline_backoff_s = 15.0

    @staticmethod
    def _log(nivel, modulo, mensaje, e=None):
        try:
            with transaction_scope() as db:
                stack = traceback.format_exc() if e else None
                if stack and len(stack) > 2000: stack = stack[:2000] + "...(truncated)"
                db.add(SystemAppLog(nivel=nivel, modulo_origen=modulo, mensaje=str(mensaje), stack_trace=stack))
        except Exception as log_e:
            print(f"SyncService log failure: {log_e}")

    def _remote_available(self):
        return time.monotonic() >= self._offline_until

    def _mark_remote_failure(self):
        self._offline_until = time.monotonic() + self._offline_backoff_s

    def _mark_remote_success(self):
        self._offline_until = 0.0

    def _request(self, method, url, *, timeout=(0.75, 1.5), offline_sensitive=True, **kwargs):
        if offline_sensitive and not self._remote_available():
            return None
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
            if response.status_code >= 500:
                self._mark_remote_failure()
            else:
                self._mark_remote_success()
            return response
        except requests.exceptions.RequestException:
            if offline_sensitive:
                self._mark_remote_failure()
            raise

    def autenticar(self, identificador, password):
        url = f"{self.api_base_url}/api/v1/auth/login"
        payload = {"username": identificador.strip(), "password": password.strip()}
        if not self._remote_available():
            return False, "Connection error: gateway temporarily unavailable."
        try:
            response = self._request("post", url, data=payload, timeout=(0.75, 1.25))
            if response is None:
                return False, "Connection error: gateway temporarily unavailable."
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

                    detalles_create = [
                        {
                            "producto_id": d.id_producto,
                            "cantidad": d.cantidad,
                            "precio_unitario": float(d.precio_unitario),
                            "monto_impuesto": float(d.monto_impuesto),
                            "subtotal_linea": float(d.subtotal_linea),
                            "detalle_local_uuid": str(d.id_detalle) if hasattr(d, 'id_detalle') else None,
                        }
                        for d in detalles
                    ]

                    payload = {
                        "empleado_id": user_id,
                        "canal_origen": v.canal_origen or "CAJA",
                        "factura_local_uuid": str(v.id_factura),
                        "mesa": v.mesa,
                        "cliente_id": v.id_cliente,
                        "subtotal": float(v.subtotal),
                        "total_impuestos": float(v.total_impuestos),
                        "propina_legal": float(v.propina_legal) if hasattr(v, 'propina_legal') and v.propina_legal else 0.0,
                        "propina_extra": float(v.propina_extra) if hasattr(v, 'propina_extra') and v.propina_extra else 0.0,
                        "total_general": float(v.total_general),
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
            response = self._request("get", url, headers=headers, timeout=(0.75, 1.5))
            if response is None:
                return False, "Gateway temporarily unavailable."
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

    def sincronizar_happy_hour(self):
        url = f"{self.api_base_url}/api/v1/promociones/happy-hour/activo"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            response = self._request("get", url, headers=headers, timeout=(0.75, 1.25))
            if response is None:
                return False, 0.0
            if response.status_code == 200:
                data = response.json()
                active = data.get("happy_hour_activo", False)
                discount = 0.0
                if active and data.get("promociones_activas"):
                    discount = data["promociones_activas"][0].get("valor", 0.0) / 100.0
                return active, float(discount)
            return False, 0.0
        except Exception:
            return False, 0.0

    def sincronizar_categorias(self):
        url = f"{self.api_base_url}/api/v1/productos/categorias"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            
        try:
            response = self._request("get", url, headers=headers, timeout=(0.75, 1.5))
            if response is None:
                return []
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
            response = self._request("get", url, headers=headers, timeout=(0.75, 2.0))
            if response is None:
                return False, "Gateway temporarily unavailable."
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

                        # Download and store product image
                        image_url = prod.get("imagen_url") or prod.get("image_url") or prod.get("imagen")
                        if image_url:
                            try:
                                import os
                                images_dir = os.path.join(os.path.dirname(__file__), '..', 'images')
                                os.makedirs(images_dir, exist_ok=True)
                                img_path = os.path.join(images_dir, f"product_{prod_id}.jpg")
                                
                                # Only download if we don't have it or we want to overwrite
                                img_resp = self._request("get", image_url, timeout=(0.75, 2.0), offline_sensitive=False)
                                if img_resp.status_code == 200:
                                    with open(img_path, 'wb') as f:
                                        f.write(img_resp.content)
                            except Exception as img_e:
                                print(f"⚠️ Failed to download image for product {prod_id}: {img_e}", flush=True)

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
            response = self._request("get", url, headers=headers, timeout=(0.75, 1.25))
            if response is None:
                return -1
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
            response = self._request("post", create_url, headers=headers, json=payload, timeout=(0.75, 2.0))
            if response is None:
                return False, "Gateway temporarily unavailable."
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
            response = self._request("get", url, headers=headers, timeout=(0.75, 1.5))
            if response is None:
                return []
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
            response = self._request("get", url, headers=headers, timeout=(0.75, 1.5))
            if response is None:
                return []
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

            response = self._request("post", url, headers=headers, json={}, timeout=(0.75, 2.0))
            if response is None:
                return False, "Gateway temporarily unavailable."
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

    def get_modificadores_producto(self, producto_id):
        '''Fetch available modifiers for a product from the CORE API.
        GET /api/v1/productos/{producto_id}/modificadores
        Returns a list of modifier name strings, or [] on any failure / 404.
        '''
        if not self.token:
            return []
        url = f'{self.api_base_url}/api/v1/productos/{producto_id}/modificadores'
        headers = {'Accept': 'application/json', 'Authorization': f'Bearer {self.token}'}
        try:
            response = self._request("get", url, headers=headers, timeout=(0.75, 1.25))
            if response is None:
                return []
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    mods = data
                elif isinstance(data, dict):
                    mods = data.get('modificadores') or data.get('modifiers') or data.get('data') or []
                else:
                    return []
                return [str(m.get('nombre') or m.get('name') or m) for m in mods if m]
            return []
        except Exception as e:
            print(f'[Modificadores] Could not fetch modifiers for {producto_id}: {e}', flush=True)
            return []

    # ── Promotion System Sync ─────────────────────────────────────────────────

    def sincronizar_promociones(self):
        """Fetch active promotions and store them in the local Cache (PromocionLocal)."""
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            url = f"{self.api_base_url}/api/v1/promociones/"
            response = self._request("get", url, headers=headers, timeout=(0.75, 1.5))
            if response is None:
                return []
            
            if response.status_code == 200:
                data = response.json()
                from models.entities import PromocionLocal
                db = SessionLocal()
                try:
                    import datetime
                    for p in data:
                        promo = db.query(PromocionLocal).filter(PromocionLocal.id == p.get('id')).first()
                        if promo:
                            promo.nombre = p.get('nombre', promo.nombre)
                            promo.tipo_aplicacion = p.get('tipo_aplicacion', 'AUTOMATICA')
                            promo.tipo_descuento = p.get('tipo_descuento')
                            promo.valor = p.get('valor')
                            promo.aplica_a = p.get('aplica_a', 'TODOS')
                            promo.aplica_happy_hour = p.get('aplica_happy_hour', False)
                            promo.hora_inicio_hh = p.get('hora_inicio_hh')
                            promo.hora_fin_hh = p.get('hora_fin_hh')
                            promo.fecha_inicio = datetime.datetime.now() # Simplified
                            promo.activo = p.get('activo', True)
                            promo.prioridad = p.get('prioridad', 0)
                            promo.etiqueta_identificador = p.get('etiqueta_identificador')
                            promo.requiere_identificador = p.get('requiere_identificador', True)
                        else:
                            promo = PromocionLocal(
                                id=p.get('id'),
                                nombre=p.get('nombre', ''),
                                tipo_aplicacion=p.get('tipo_aplicacion', 'AUTOMATICA'),
                                tipo_descuento=p.get('tipo_descuento'),
                                valor=p.get('valor'),
                                aplica_a=p.get('aplica_a', 'TODOS'),
                                aplica_happy_hour=p.get('aplica_happy_hour', False),
                                hora_inicio_hh=p.get('hora_inicio_hh'),
                                hora_fin_hh=p.get('hora_fin_hh'),
                                fecha_inicio=datetime.datetime.now(), # Simplified
                                fecha_fin=None,
                                activo=p.get('activo', True),
                                prioridad=p.get('prioridad', 0),
                                etiqueta_identificador=p.get('etiqueta_identificador'),
                                requiere_identificador=p.get('requiere_identificador', True)
                            )
                            db.add(promo)
                    db.commit()
                    
                    # Also save full JSON catalog for category/product eligibility
                    import json
                    import os
                    json_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'promociones_catalog.json')
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f)
                        
                    print(f"[OK] Synced {len(data)} promotions to local cache", flush=True)
                except Exception as e:
                    db.rollback()
                    print(f"[ERROR] DB Error syncing promotions: {e}", flush=True)
                finally:
                    db.close()
                return data
            return []
        except Exception as e:
            print(f"[ERROR] Connection error syncing promotions: {e}", flush=True)
            return []

    def sincronizar_auditorias_promocion(self):
        """Upload offline promotion application audits to the Integration Gateway."""
        from models.entities import AplicacionPromocionLocal
        db = SessionLocal()
        
        try:
            pendientes = db.query(AplicacionPromocionLocal).filter(
                AplicacionPromocionLocal.sincronizado == False
            ).limit(50).all()
            
            if not pendientes:
                return 0
                
            url = f"{self.api_base_url}/api/v1/promociones/aplicaciones"
            headers = {"Accept": "application/json"}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
                
            procesados = 0
            for ap in pendientes:
                payload = {
                    "factura_uuid": str(ap.factura_uuid) if ap.factura_uuid else None,
                    "promocion_id": ap.promocion_id,
                    "nombre_promocion_snap": ap.nombre_promocion,
                    "tipo_aplicacion": ap.tipo_aplicacion,
                    "empleado_id": ap.empleado_id,
                    "empleado_autorizador_id": ap.empleado_autorizador_id,
                    "identificador_capturado": ap.identificador_capturado,
                    "monto_descuento": float(ap.monto_descuento),
                    "terminal": ap.terminal,
                    "notas": ap.notas
                }
                
                try:
                    resp = self._request("post", url, json=payload, headers=headers, timeout=(0.75, 1.5))
                    if resp is None:
                        break
                    if resp.status_code in (200, 201):
                        ap.sincronizado = True
                        procesados += 1
                except Exception as e:
                    print(f"Failed to sync promotion audit {ap.id}: {e}")
                    
            db.commit()
            if procesados > 0:
                print(f"✅ Uploaded {procesados} promotion audits", flush=True)
            return procesados
            
        finally:
            db.close()

    def autenticar_supervisor_totp(self, email: str, otp: str) -> dict:
        """Call the Integration Gateway to authenticate a supervisor using TOTP."""
        url = f"{self.api_base_url}/api/v1/promociones/supervisor/auth"
        params = {
            "email": email,
            "otp": otp
        }
        try:
            resp = self._request("post", url, params=params, timeout=(0.75, 1.5))
            if resp is None:
                raise Exception("Connection error.")
            if resp.status_code == 200:
                data = resp.json()
                if not data.get("ok"):
                    raise Exception(data.get("error", "Invalid or expired code."))
                return data
            else:
                try:
                    msg = resp.json().get("detail", "Invalid or expired code.")
                except:
                    msg = "Invalid or expired code."
                raise Exception(msg)
        except Exception as e:
            if "Connection error" in str(e):
                raise Exception("Connection error.")
            raise

    def validar_codigo_promo(self, codigo: str, subtotal: float) -> dict:
        """Validate a promotional code with the Integration Gateway."""
        url = f"{self.api_base_url}/api/v1/promociones/codigos/validar"
        params = {
            "codigo": codigo,
            "subtotal": subtotal
        }
        try:
            resp = self._request("post", url, params=params, timeout=(0.75, 1.5))
            if resp is None:
                raise Exception("Connection error verifying code.")
            if resp.status_code == 200:
                return resp.json()
            else:
                try:
                    msg = resp.json().get("detail", "Code invalid or expired.")
                except:
                    msg = "Code invalid or expired."
                raise Exception(msg)
        except Exception as e:
            if "Code invalid" in str(e) or "expired" in str(e) or "Minimum" in str(e) or "No existe" in str(e):
                raise
            raise Exception("Connection error verifying code.")

    def sincronizar_sesiones_supervisor(self):
        """Upload offline supervisor session records to the Integration Gateway."""
        from models.entities import SupervisorSessionLocal
        db = SessionLocal()
        
        try:
            pendientes = db.query(SupervisorSessionLocal).filter(
                SupervisorSessionLocal.sincronizado == False
            ).limit(50).all()
            
            if not pendientes:
                return 0
                
            url = f"{self.api_base_url}/api/v1/promociones/supervisor/sessions/sync"
            headers = {"Accept": "application/json"}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
                
            payload = []
            for s in pendientes:
                payload.append({
                    "id": str(s.id),
                    "supervisor_id": s.supervisor_id,
                    "cajero_id": s.cajero_id,
                    "terminal": s.terminal,
                    "inicio": s.inicio.isoformat() if s.inicio else None,
                    "fin": s.fin.isoformat() if s.fin else None,
                    "motivo_fin": s.motivo_fin
                })
            
            try:
                resp = self._request("post", url, json=payload, headers=headers, timeout=(0.75, 1.5))
                if resp is None:
                    return 0
                if resp.status_code in (200, 201):
                    for s in pendientes:
                        s.sincronizado = True
                    db.commit()
                    print(f"✅ Uploaded {len(pendientes)} supervisor sessions", flush=True)
                    return len(pendientes)
                else:
                    print(f"❌ Failed to sync supervisor sessions: HTTP {resp.status_code}", flush=True)
            except Exception as e:
                print(f"❌ Connection error syncing supervisor sessions: {e}", flush=True)
                
            return 0
            
        finally:
            db.close()

