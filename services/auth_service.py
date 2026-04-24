import bcrypt
import requests
from sqlalchemy import or_
from db.connection import SessionLocal
from models.entities import UsuarioLocal
from services.sync_service import SyncService

class AuthService:
    current_user_id = None
    current_user_name = "Sin Usuario"
    current_rol = "Sin Rol"
    current_sucursal_id = 1
    token = None
    # Cached credentials for background token retry (never persisted to disk)
    _last_identificador = None
    _last_password = None
    
    api_base_url = "http://localhost:8001" 

    @classmethod
    def login_maestro(cls, identificador, password):
        # Cache credentials so background sync can retry token acquisition if API was down
        cls._last_identificador = identificador
        cls._last_password = password
        url = f"{cls.api_base_url}/api/v1/auth/login"
        payload = {"username": identificador.strip(), "password": password.strip()}
        
        try:

            response = requests.post(url, data=payload, timeout=3.0) 
            
            if response.status_code == 200:
                data = response.json()
                cls.token = data.get("access_token")
                cls.current_user_id = data.get("usuario_id")
                cls.current_user_name = data.get("nombre")
                cls.current_rol = data.get("rol", "Cajero")
                cls.current_sucursal_id = data.get("sucursal_id", 1)
                
                SyncService._log("INFO", "AuthService", f"Successful login via Integration: {identificador}")
                return True, "Successful login via Integration"
            

            err_msg = response.json().get("detail", "Invalid Credentials")
            SyncService._log("WARNING", "AuthService", f"Login API Rechazado: {err_msg}")
            return False, err_msg
            
        except requests.exceptions.RequestException as e:
            SyncService._log("WARNING", "AuthService", "Gateway unreachable. Starting local fallback.")
            print(f"⚠️ Gateway unreachable, using direct DB read: {e}")

        db = SessionLocal()
        try:
            user = db.query(UsuarioLocal).filter(
                or_(
                    UsuarioLocal.email == identificador.strip()
                )
            ).first()

            if not user:
                return False, "User not found in local fallback mode."

            if not getattr(user, 'activo', True):
                return False, "User is inactive."

            try:
                if bcrypt.checkpw(password.encode('utf-8'), user.hash_clave.encode('utf-8')):
                    cls.current_user_id = user.id_usuario
                    cls.current_user_name = user.nombre
                    cls.current_rol = getattr(user, 'rol', 'Cajero')
                    cls.current_sucursal_id = user.id_sucursal
                    
                    SyncService._log("INFO", "AuthService", f"Successful local fallback login for: {identificador}")
                    return True, "Successful local fallback login"
            except Exception as e:
                print(f"Error de validación bcrypt: {e}")
                pass 
            
            return False, "Invalid credentials."
            
        except Exception as e:
            SyncService._log("ERROR", "AuthService", f"Error DB Fallback: {e}")
            return False, "Internal critical error while reading database."
        finally:
            db.close()