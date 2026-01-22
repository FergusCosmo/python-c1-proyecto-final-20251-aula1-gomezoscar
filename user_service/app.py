# Servicio de Usuarios y Gestión Administrativa
# Reescritura con:
# - Hash de contraseñas
# - Soft delete para pacientes, doctores y centros
# - Listados con filtros y paginación
# - CRUD completo

from datetime import timedelta

from flask import Blueprint, Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

# Configuración de la aplicación Flask
app = Flask(__name__)

# Configuración de la base de datos SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///user_service.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configuración de JWT
app.config["JWT_SECRET_KEY"] = "clave-secreta-cambiar-en-produccion"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

# Inicialización de extensiones
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)

# ========================================
# MODELOS DE DATOS (SQLAlchemy)
# ========================================


class User(db.Model):
    """Modelo de usuario para autenticación"""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(
        db.String(20), nullable=False
    )  # admin, medico, secretaria, paciente


class Patient(db.Model):
    """Modelo de paciente"""

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    estado = db.Column(db.String(20), default="ACTIVO")  # ACTIVO/INACTIVO
    id_usuario = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)


class Doctor(db.Model):
    """Modelo de doctor"""

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    especialidad = db.Column(db.String(50))
    estado = db.Column(db.String(20), default="ACTIVO")  # ACTIVO/INACTIVO
    id_usuario = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)


class Center(db.Model):
    """Modelo de centro médico"""

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200))
    estado = db.Column(db.String(20), default="ACTIVO")  # ACTIVO/INACTIVO


# ========================================
# HELPERS
# ========================================


def require_admin():
    """Verifica que el usuario actual exista y sea admin."""
    user_id = get_jwt_identity()
    usuario_actual = User.query.get(int(user_id)) if user_id is not None else None
    if not usuario_actual or usuario_actual.rol != "admin":
        return None
    return usuario_actual


def paginate_query(query):
    """Aplica paginación estándar a una query SQLAlchemy."""
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    per_page = min(max(per_page, 1), 100)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return pagination


def build_meta(pagination):
    return {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    }


# ========================================
# BLUEPRINT: auth_bp (Autenticación)
# ========================================
auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """Registrar un nuevo usuario"""
    data = request.get_json() or {}

    if "username" not in data or "password" not in data:
        return jsonify({"error": "Faltan datos requeridos"}), 400

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "El usuario ya existe"}), 400

    hashed = generate_password_hash(data["password"])
    nuevo_usuario = User(
        username=data["username"],
        password=hashed,
        rol=data.get("rol", "paciente"),
    )
    db.session.add(nuevo_usuario)
    db.session.commit()

    return (
        jsonify(
            {
                "mensaje": "Usuario creado exitosamente",
                "usuario": {
                    "id": nuevo_usuario.id,
                    "username": nuevo_usuario.username,
                    "rol": nuevo_usuario.rol,
                },
            }
        ),
        201,
    )


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """Iniciar sesión y obtener token JWT"""
    data = request.get_json() or {}

    if "username" not in data or "password" not in data:
        return jsonify({"error": "Faltan datos requeridos"}), 400

    usuario = User.query.filter_by(username=data["username"]).first()
    if not usuario or not check_password_hash(usuario.password, data["password"]):
        return jsonify({"error": "Credenciales inválidas"}), 401

    token = create_access_token(identity=str(usuario.id))

    return (
        jsonify(
            {
                "mensaje": "Login exitoso",
                "access_token": token,
                "usuario": {
                    "id": usuario.id,
                    "username": usuario.username,
                    "rol": usuario.rol,
                },
            }
        ),
        200,
    )


# ========================================
# BLUEPRINT: admin_bp (Administración)
# ========================================
admin_bp = Blueprint("admin_bp", __name__)

# -------- Pacientes ---------


@admin_bp.route("/admin/pacientes", methods=["POST"])
@jwt_required()
def crear_paciente():
    """Crear un nuevo paciente (requiere rol admin)"""
    if not require_admin():
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json() or {}
    if "nombre" not in data:
        return jsonify({"error": "Faltan datos requeridos"}), 400

    nuevo_paciente = Patient(
        nombre=data["nombre"],
        telefono=data.get("telefono", ""),
        estado=data.get("estado", "ACTIVO"),
    )
    db.session.add(nuevo_paciente)
    db.session.commit()

    return (
        jsonify(
            {
                "mensaje": "Paciente creado exitosamente",
                "paciente": {
                    "id": nuevo_paciente.id,
                    "nombre": nuevo_paciente.nombre,
                    "telefono": nuevo_paciente.telefono,
                    "estado": nuevo_paciente.estado,
                },
            }
        ),
        201,
    )


@admin_bp.route("/admin/pacientes", methods=["GET"])
@jwt_required()
def listar_pacientes():
    """Listar pacientes con filtros y paginación (solo activos por defecto)"""
    if not require_admin():
        return jsonify({"error": "No autorizado"}), 403

    estado = request.args.get("estado", default="ACTIVO")
    nombre = request.args.get("nombre")

    query = Patient.query
    if estado:
        query = query.filter_by(estado=estado)
    if nombre:
        query = query.filter(Patient.nombre.ilike(f"%{nombre}%"))

    pagination = paginate_query(query.order_by(Patient.id))
    pacientes = [
        {
            "id": p.id,
            "nombre": p.nombre,
            "telefono": p.telefono,
            "estado": p.estado,
        }
        for p in pagination.items
    ]

    return jsonify({"pacientes": pacientes, "meta": build_meta(pagination)}), 200


@admin_bp.route("/admin/pacientes/<int:paciente_id>", methods=["GET"])
@jwt_required()
def obtener_paciente(paciente_id):
    """Obtener un paciente específico por ID"""
    if not require_admin():
        return jsonify({"error": "No autorizado"}), 403

    paciente = Patient.query.get(paciente_id)
    if not paciente:
        return jsonify({"error": "Paciente no encontrado"}), 404

    return (
        jsonify(
            {
                "paciente": {
                    "id": paciente.id,
                    "nombre": paciente.nombre,
                    "telefono": paciente.telefono,
                    "estado": paciente.estado,
                }
            }
        ),
        200,
    )


@admin_bp.route("/admin/pacientes/<int:paciente_id>", methods=["PUT"])
@jwt_required()
def actualizar_paciente(paciente_id):
    """Actualizar datos de un paciente (soft delete si estado=INACTIVO)"""
    if not require_admin():
        return jsonify({"error": "No autorizado"}), 403

    paciente = Patient.query.get(paciente_id)
    if not paciente:
        return jsonify({"error": "Paciente no encontrado"}), 404

    data = request.get_json() or {}
    paciente.nombre = data.get("nombre", paciente.nombre)
    paciente.telefono = data.get("telefono", paciente.telefono)
    paciente.estado = data.get("estado", paciente.estado)

    db.session.commit()

    return (
        jsonify(
            {
                "mensaje": "Paciente actualizado exitosamente",
                "paciente": {
                    "id": paciente.id,
                    "nombre": paciente.nombre,
                    "telefono": paciente.telefono,
                    "estado": paciente.estado,
                },
            }
        ),
        200,
    )


@admin_bp.route("/admin/pacientes/<int:paciente_id>", methods=["DELETE"])
@jwt_required()
def eliminar_paciente(paciente_id):
    """Soft delete de paciente (estado=INACTIVO)"""
    if not require_admin():
        return jsonify({"error": "No autorizado"}), 403

    paciente = Patient.query.get(paciente_id)
    if not paciente:
        return jsonify({"error": "Paciente no encontrado"}), 404

    paciente.estado = "INACTIVO"
    db.session.commit()

    return jsonify({"mensaje": "Paciente inactivado exitosamente"}), 200


# -------- Doctores ---------


@admin_bp.route("/admin/doctores", methods=["POST"])
@jwt_required()
def crear_doctor():
    """Crear un nuevo doctor (requiere rol admin)"""
    if not require_admin():
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json() or {}
    if "nombre" not in data:
        return jsonify({"error": "Faltan datos requeridos"}), 400

    nuevo_doctor = Doctor(
        nombre=data["nombre"],
        especialidad=data.get("especialidad", ""),
        estado=data.get("estado", "ACTIVO"),
    )
    db.session.add(nuevo_doctor)
    db.session.commit()

    return (
        jsonify(
            {
                "mensaje": "Doctor creado exitosamente",
                "doctor": {
                    "id": nuevo_doctor.id,
                    "nombre": nuevo_doctor.nombre,
                    "especialidad": nuevo_doctor.especialidad,
                    "estado": nuevo_doctor.estado,
                },
            }
        ),
        201,
    )


@admin_bp.route("/admin/doctores", methods=["GET"])
@jwt_required()
def listar_doctores():
    """Listar doctores con filtros y paginación"""
    if not require_admin():
        return jsonify({"error": "No autorizado"}), 403

    estado = request.args.get("estado", default="ACTIVO")
    nombre = request.args.get("nombre")
    especialidad = request.args.get("especialidad")

    query = Doctor.query
    if estado:
        query = query.filter_by(estado=estado)
    if nombre:
        query = query.filter(Doctor.nombre.ilike(f"%{nombre}%"))
    if especialidad:
        query = query.filter(Doctor.especialidad.ilike(f"%{especialidad}%"))

    pagination = paginate_query(query.order_by(Doctor.id))
    doctores = [
        {
            "id": d.id,
            "nombre": d.nombre,
            "especialidad": d.especialidad,
            "estado": d.estado,
        }
        for d in pagination.items
    ]

    return jsonify({"doctores": doctores, "meta": build_meta(pagination)}), 200


@admin_bp.route("/admin/doctores/<int:doctor_id>", methods=["GET"])
@jwt_required()
def obtener_doctor(doctor_id):
    """Obtener un doctor específico por ID"""
    if not require_admin():
        return jsonify({"error": "No autorizado"}), 403

    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor no encontrado"}), 404

    return (
        jsonify(
            {
                "doctor": {
                    "id": doctor.id,
                    "nombre": doctor.nombre,
                    "especialidad": doctor.especialidad,
                    "estado": doctor.estado,
                }
            }
        ),
        200,
    )


@admin_bp.route("/admin/doctores/<int:doctor_id>", methods=["PUT"])
@jwt_required()
def actualizar_doctor(doctor_id):
    """Actualizar datos de un doctor (soft delete si estado=INACTIVO)"""
    if not require_admin():
        return jsonify({"error": "No autorizado"}), 403

    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor no encontrado"}), 404

    data = request.get_json() or {}
    doctor.nombre = data.get("nombre", doctor.nombre)
    doctor.especialidad = data.get("especialidad", doctor.especialidad)
    doctor.estado = data.get("estado", doctor.estado)

    db.session.commit()

    return (
        jsonify(
            {
                "mensaje": "Doctor actualizado exitosamente",
                "doctor": {
                    "id": doctor.id,
                    "nombre": doctor.nombre,
                    "especialidad": doctor.especialidad,
                    "estado": doctor.estado,
                },
            }
        ),
        200,
    )


@admin_bp.route("/admin/doctores/<int:doctor_id>", methods=["DELETE"])
@jwt_required()
def eliminar_doctor(doctor_id):
    """Soft delete de doctor (estado=INACTIVO)"""
    if not require_admin():
        return jsonify({"error": "No autorizado"}), 403

    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor no encontrado"}), 404

    doctor.estado = "INACTIVO"
    db.session.commit()

    return jsonify({"mensaje": "Doctor inactivado exitosamente"}), 200


# -------- Centros ---------


@admin_bp.route("/admin/centros", methods=["POST"])
@jwt_required()
def crear_centro():
    """Crear un nuevo centro médico (requiere rol admin)"""
    if not require_admin():
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json() or {}
    if "nombre" not in data:
        return jsonify({"error": "Faltan datos requeridos"}), 400

    nuevo_centro = Center(
        nombre=data["nombre"],
        direccion=data.get("direccion", ""),
        estado=data.get("estado", "ACTIVO"),
    )
    db.session.add(nuevo_centro)
    db.session.commit()

    return (
        jsonify(
            {
                "mensaje": "Centro creado exitosamente",
                "centro": {
                    "id": nuevo_centro.id,
                    "nombre": nuevo_centro.nombre,
                    "direccion": nuevo_centro.direccion,
                    "estado": nuevo_centro.estado,
                },
            }
        ),
        201,
    )


@admin_bp.route("/admin/centros", methods=["GET"])
@jwt_required()
def listar_centros():
    """Listar centros con filtros y paginación"""
    if not require_admin():
        return jsonify({"error": "No autorizado"}), 403

    estado = request.args.get("estado", default="ACTIVO")
    nombre = request.args.get("nombre")
    direccion = request.args.get("direccion")

    query = Center.query
    if estado:
        query = query.filter_by(estado=estado)
    if nombre:
        query = query.filter(Center.nombre.ilike(f"%{nombre}%"))
    if direccion:
        query = query.filter(Center.direccion.ilike(f"%{direccion}%"))

    pagination = paginate_query(query.order_by(Center.id))
    centros = [
        {
            "id": c.id,
            "nombre": c.nombre,
            "direccion": c.direccion,
            "estado": c.estado,
        }
        for c in pagination.items
    ]

    return jsonify({"centros": centros, "meta": build_meta(pagination)}), 200


@admin_bp.route("/admin/centros/<int:centro_id>", methods=["GET"])
@jwt_required()
def obtener_centro(centro_id):
    """Obtener un centro específico por ID"""
    if not require_admin():
        return jsonify({"error": "No autorizado"}), 403

    centro = Center.query.get(centro_id)
    if not centro:
        return jsonify({"error": "Centro no encontrado"}), 404

    return (
        jsonify(
            {
                "centro": {
                    "id": centro.id,
                    "nombre": centro.nombre,
                    "direccion": centro.direccion,
                    "estado": centro.estado,
                }
            }
        ),
        200,
    )


@admin_bp.route("/admin/centros/<int:centro_id>", methods=["PUT"])
@jwt_required()
def actualizar_centro(centro_id):
    """Actualizar datos de un centro (soft delete si estado=INACTIVO)"""
    if not require_admin():
        return jsonify({"error": "No autorizado"}), 403

    centro = Center.query.get(centro_id)
    if not centro:
        return jsonify({"error": "Centro no encontrado"}), 404

    data = request.get_json() or {}
    centro.nombre = data.get("nombre", centro.nombre)
    centro.direccion = data.get("direccion", centro.direccion)
    centro.estado = data.get("estado", centro.estado)

    db.session.commit()

    return (
        jsonify(
            {
                "mensaje": "Centro actualizado exitosamente",
                "centro": {
                    "id": centro.id,
                    "nombre": centro.nombre,
                    "direccion": centro.direccion,
                    "estado": centro.estado,
                },
            }
        ),
        200,
    )


@admin_bp.route("/admin/centros/<int:centro_id>", methods=["DELETE"])
@jwt_required()
def eliminar_centro(centro_id):
    """Soft delete de centro (estado=INACTIVO)"""
    if not require_admin():
        return jsonify({"error": "No autorizado"}), 403

    centro = Center.query.get(centro_id)
    if not centro:
        return jsonify({"error": "Centro no encontrado"}), 404

    centro.estado = "INACTIVO"
    db.session.commit()

    return jsonify({"mensaje": "Centro inactivado exitosamente"}), 200


# ========================================
# BLUEPRINT: verify_bp (Verificación de Existencia)
# ========================================
verify_bp = Blueprint("verify_bp", __name__)


@verify_bp.route("/verify/pacientes/<int:paciente_id>", methods=["GET"])
@jwt_required()
def verificar_paciente(paciente_id):
    """Verificar si existe un paciente (sin devolver datos completos)"""
    paciente = Patient.query.filter_by(id=paciente_id, estado="ACTIVO").first()

    if not paciente:
        return jsonify({"exists": False, "error": "Paciente no encontrado"}), 404

    return jsonify({"exists": True, "id": paciente.id}), 200


@verify_bp.route("/verify/doctores/<int:doctor_id>", methods=["GET"])
@jwt_required()
def verificar_doctor(doctor_id):
    """Verificar si existe un doctor (sin devolver datos completos)"""
    doctor = Doctor.query.filter_by(id=doctor_id, estado="ACTIVO").first()

    if not doctor:
        return jsonify({"exists": False, "error": "Doctor no encontrado"}), 404

    return jsonify({"exists": True, "id": doctor.id}), 200


@verify_bp.route("/verify/centros/<int:centro_id>", methods=["GET"])
@jwt_required()
def verificar_centro(centro_id):
    """Verificar si existe un centro (sin devolver datos completos)"""
    centro = Center.query.filter_by(id=centro_id, estado="ACTIVO").first()

    if not centro:
        return jsonify({"exists": False, "error": "Centro no encontrado"}), 404

    return jsonify({"exists": True, "id": centro.id}), 200


@verify_bp.route("/verify/token", methods=["GET"])
@jwt_required()
def verificar_token():
    """Verificar que un token JWT sea válido"""
    user_id = get_jwt_identity()
    usuario = User.query.get(int(user_id)) if user_id is not None else None

    if not usuario:
        return jsonify({"valid": False, "error": "Usuario no encontrado"}), 404

    return jsonify(
        {
            "valid": True,
            "user_id": usuario.id,
            "username": usuario.username,
            "rol": usuario.rol,
        }
    ), 200


# ========================================
# ENDPOINTS DE HEALTH Y ROOT
# ========================================


@app.route("/health")
def health():
    """Endpoint de verificación de salud del servicio"""
    return jsonify(
        {"service": "user_service", "status": "ok", "environment": "development"}
    ), 200


@app.route("/")
def root():
    """Endpoint raíz con información del servicio"""
    return (
        jsonify(
            {
                "name": "OdontoCare - Servicio de Gestión de Usuarios",
                "version": "1.0.0",
                "endpoints": {"auth": "/auth", "admin": "/admin", "health": "/health"},
            }
        ),
        200,
    )


# ========================================
# INICIALIZACIÓN
# ========================================

# Registrar blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(verify_bp)

# Crear tablas de la base de datos
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
