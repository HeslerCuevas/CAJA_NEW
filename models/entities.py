from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey
from db.connection import Base
import datetime
from utils.timezone import get_local_now
import uuid

class UsuarioLocal(Base):
    __tablename__ = "Usuarios_Locales"
    id_usuario = Column("ID_Usuario", Integer, primary_key=True, autoincrement=False)
    nombre = Column("Nombre", String(150), nullable=False)
    hash_clave = Column("Hash_Clave", String(255), nullable=False)
    id_sucursal = Column("ID_Sucursal", Integer, nullable=False)
    activo = Column("Activo", Boolean, default=True)
    email = Column("Email", String(255), nullable=True, unique=True)
    ultima_actualizacion = Column("Ultima_Actualizacion", DateTime, default=get_local_now)

class ProductoLocal(Base):
    __tablename__ = "Productos_Cache"
    id_producto = Column("ID_Producto", Integer, primary_key=True, autoincrement=False)
    nombre = Column("Nombre", String(150), nullable=False)
    precio_actual = Column("Precio_Actual", Numeric(12, 2), nullable=False)
    tasa_impuesto = Column("Tasa_Impuesto", Numeric(5, 2), default=0.18)
    stock_local = Column("Stock_Local", Integer, default=0)
    id_categoria = Column("ID_Categoria", Integer, nullable=True)
    ultima_actualizacion = Column("Ultima_Actualizacion", DateTime, default=get_local_now)

class CategoriaLocal(Base):
    __tablename__ = "Categorias"
    id = Column("Id", Integer, primary_key=True, autoincrement=False)
    nombre = Column("Nombre", String(100), nullable=False, unique=True)
    descripcion = Column("Descripcion", String(255), nullable=True)
    activo = Column("Activo", Boolean, default=True)

class TurnoCaja(Base):
    __tablename__ = "Turnos_Caja"
    id_turno = Column("ID_Turno", String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_usuario = Column("ID_Usuario", Integer, ForeignKey("Usuarios_Locales.ID_Usuario"))
    id_sucursal = Column("ID_Sucursal", Integer, nullable=False)
    fecha_apertura = Column("Fecha_Apertura", DateTime, default=get_local_now)
    monto_inicial = Column("Monto_Inicial", Numeric(12, 2), nullable=False)
    fecha_cierre = Column("Fecha_Cierre", DateTime, nullable=True)
    monto_calculado = Column("Monto_Calculado", Numeric(12, 2), nullable=True)
    monto_fisico = Column("Monto_Fisico", Numeric(12, 2), nullable=True)
    estado = Column("Estado", String(20), default="ABIERTO")
    sincronizado = Column("Sincronizado", Boolean, default=False)

class MovimientoEfectivo(Base):
    __tablename__ = "Movimientos_Efectivo"
    id_movimiento = Column("ID_Movimiento", String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_turno = Column("ID_Turno", String(50), ForeignKey("Turnos_Caja.ID_Turno"))
    tipo_movimiento = Column("Tipo_Movimiento", String(20), nullable=False)
    monto = Column("Monto", Numeric(12, 2), nullable=False)
    concepto = Column("Concepto", String(255), nullable=False)
    fecha_hora = Column("Fecha_Hora", DateTime, default=get_local_now)
    sincronizado = Column("Sincronizado", Boolean, default=False)

class FacturaLocal(Base):
    __tablename__ = "Facturas_Locales"
    id_factura = Column("ID_Factura", String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_turno = Column("ID_Turno", String(50), ForeignKey("Turnos_Caja.ID_Turno"))
    id_sucursal = Column("ID_Sucursal", Integer, nullable=False)
    fecha_hora = Column("Fecha_Hora", DateTime, default=get_local_now)
    
    subtotal = Column("Subtotal", Numeric(12, 2), nullable=False)
    total_impuestos = Column("Total_Impuestos", Numeric(12, 2), nullable=False)
    propina_legal = Column("Propina_Legal", Numeric(12, 2), default=0)
    propina_extra = Column("Propina_Extra", Numeric(12, 2), default=0)
    total_general = Column("Total_General", Numeric(12, 2), nullable=False)
    
    metodo_pago = Column("Metodo_Pago", String(50), nullable=False)
    mesa = Column("Mesa", Integer, nullable=True)
    canal_origen = Column("Canal_Origen", String(50), default="CAJA")
    id_cliente = Column("ID_Cliente", Integer, nullable=True)
    estado = Column("Estado", String(50), default="FACTURADO")
    
    sincronizado = Column("Sincronizado", Boolean, default=False)

class DetalleFactura(Base):
    __tablename__ = "Detalle_Facturas"
    id_detalle = Column("ID_Detalle", String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_factura = Column("ID_Factura", String(50), ForeignKey("Facturas_Locales.ID_Factura"))
    id_producto = Column("ID_Producto", Integer, ForeignKey("Productos_Cache.ID_Producto"))
    cantidad = Column("Cantidad", Integer, nullable=False)
    precio_unitario = Column("Precio_Unitario", Numeric(12, 2), nullable=False)
    monto_impuesto = Column("Monto_Impuesto", Numeric(12, 2), nullable=False)
    subtotal_linea = Column("Subtotal_Linea", Numeric(12, 2), nullable=False)

class LogCaja(Base):
    __tablename__ = "Logs_Caja"
    id_log = Column("ID_Log", String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_usuario = Column("ID_Usuario", Integer, ForeignKey("Usuarios_Locales.ID_Usuario"), nullable=True)
    id_sucursal = Column("ID_Sucursal", Integer, nullable=False)
    nivel = Column("Nivel", String(20), nullable=False)
    accion = Column("Accion", String(100), nullable=False)
    descripcion = Column("Descripcion", String(1000), nullable=False)
    fecha_hora = Column("Fecha_Hora", DateTime, default=get_local_now)
    sincronizado = Column("Sincronizado", Boolean, default=False)


class SystemAppLog(Base):
    __tablename__ = "System_App_Logs"
    id_syslog = Column("ID_SysLog", String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    fecha_hora = Column("Fecha_Hora", DateTime, default=get_local_now)
    nivel = Column("Nivel", String(20), nullable=False)
    modulo_origen = Column("Modulo_Origen", String(100), nullable=False)
    mensaje = Column("Mensaje", String, nullable=False)
    stack_trace = Column("StackTrace", String, nullable=True)


class PromocionLocal(Base):
    """Locally cached promotion catalog synchronized from Integration."""
    __tablename__ = "Promociones_Cache"
    id = Column("Id", Integer, primary_key=True, autoincrement=False)
    nombre = Column("Nombre", String(150), nullable=False)
    tipo_aplicacion = Column("TipoAplicacion", String(20), nullable=False, default="AUTOMATICA")
    tipo_descuento = Column("TipoDescuento", String(20), nullable=False)
    valor = Column("Valor", Numeric(12, 2), nullable=False)
    aplica_a = Column("AplicaA", String(20), nullable=False, default="TODOS")
    aplica_happy_hour = Column("AplicaHappyHour", Boolean, default=False)
    hora_inicio_hh = Column("HoraInicioHH", String(5), nullable=True)
    hora_fin_hh = Column("HoraFinHH", String(5), nullable=True)
    fecha_inicio = Column("FechaInicio", DateTime, nullable=False)
    fecha_fin = Column("FechaFin", DateTime, nullable=True)
    activo = Column("Activo", Boolean, default=True)
    prioridad = Column("Prioridad", Integer, default=0)
    etiqueta_identificador = Column("EtiquetaIdentificador", String(100), nullable=True)
    requiere_identificador = Column("RequiereIdentificador", Boolean, default=True)
    ultima_actualizacion = Column("UltimaActualizacion", DateTime, default=get_local_now)


class AplicacionPromocionLocal(Base):
    """Local promotion audit queue — uploaded to Integration on each sync."""
    __tablename__ = "Aplicaciones_Promocion_Local"
    id = Column("Id", String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    promocion_id = Column("PromocionId", Integer, nullable=True)
    nombre_promocion = Column("NombrePromocion", String(150), nullable=False)
    tipo_aplicacion = Column("TipoAplicacion", String(20), nullable=False)
    factura_uuid = Column("FacturaUUID", String(50), nullable=True)
    empleado_id = Column("EmpleadoId", Integer, nullable=True)
    empleado_autorizador_id = Column("EmpleadoAutorizadorId", Integer, nullable=True)
    identificador_capturado = Column("IdentificadorCapturado", String(255), nullable=True)
    monto_descuento = Column("MontoDescuento", Numeric(12, 2), nullable=False, default=0)
    terminal = Column("Terminal", String(50), nullable=True, default="POS-01")
    fecha_hora = Column("FechaHora", DateTime, default=get_local_now)
    notas = Column("Notas", String(500), nullable=True)
    sincronizado = Column("Sincronizado", Boolean, default=False)


class SupervisorSessionLocal(Base):
    """Local queue for supervisor sessions, synced to Integration Gateway."""
    __tablename__ = "SupervisorSessionLocal"
    id = Column("id", String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    supervisor_id = Column("supervisor_id", Integer, nullable=False)
    cajero_id = Column("cajero_id", Integer, nullable=False)
    terminal = Column("terminal", String(50), nullable=False, default="POS-01")
    inicio = Column("inicio", DateTime, nullable=False, default=get_local_now)
    fin = Column("fin", DateTime, nullable=True)
    motivo_fin = Column("motivo_fin", String(50), nullable=True)
    sincronizado = Column("sincronizado", Boolean, default=False)
    creado_en = Column("creado_en", DateTime, default=get_local_now)
