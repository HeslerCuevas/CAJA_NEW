import bcrypt
from db.connection import SessionLocal
from models.usuario import UsuarioLocal

class AuthService:
    current_user_id = None
    current_user_name = "Sin Usuario"
    
    def login_hibrido(self, user_id, password):
        db = SessionLocal()
        try:
            user = db.query(UsuarioLocal).filter_by(
                id_usuario=user_id, 
                hash_clave=password
            ).first()

            if user:
                AuthService.current_user_id = user.id_usuario
                AuthService.current_user_name = user.nombre
                return True
            
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            db.close()
