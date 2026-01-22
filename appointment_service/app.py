# Servicio de Citas Médicas

from datetime import datetime

import requests
from flask import Blueprint, Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    get_jwt_identity,
    jwt_required,
)
from flask_sqlalchemy import SQLAlchemy

# Configuración de la aplicación Flask
app = Flask(__name__)

# Configuración de la base de datos SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///appointment_service.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configuración de JWT
app.config["JWT_SECRET_KEY"] = "clave-secreta-cambiar-en-produccion"

# URL del servicio de usuarios (para comunicación entre servicios)
USER_SERVICE_URL = "http://user_service:8000"

# Inicialización de extensiones
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)


# ========================================
# MODELO DE DATOS (SQLAlchemy)
# ========================================


class Appointment(db.Model):
    """Modelo de cita médica"""

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False)
    motivo = db.Column(db.String(200), nullable=False)
    estado = db.Column(
        db.String(20), default="PROGRAMADA"
    )  # PROGRAMADA, COMPLETADA, CANCELADA

    # Claves foráneas
    id_paciente = db.Column(db.Integer, nullable=False)
    id_doctor = db.Column(db.Integer, nullable=False)
    id_centro = db.Column(db.Integer, nullable=False)
    id_usuario_registra = db.Column(db.Integer, nullable=False)


# ========================================
# BLUEPRINT: citas_bp (Gestión de Citas)
# ========================================
citas_bp = Blueprint("citas_bp", __name__)


def verificar_usuario(token):
    """Verificar token con el servicio de usuarios"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{USER_SERVICE_URL}/verify/token", headers=headers, timeout=5
        )
        return response.status_code == 200
    except:
        return False


def verificar_existencia_user_service(endpoint, token):
    """Verificar que una entidad exista en el servicio de usuarios (reenviando JWT)

    Devuelve: (ok: bool, status_code: int | None, body: str | None)
    """
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.get(
            f"{USER_SERVICE_URL}{endpoint}", headers=headers, timeout=5
        )
        return response.status_code == 200, response.status_code, response.text
    except Exception as e:
        return False, None, str(e)


@citas_bp.route("/citas", methods=["POST"])
@jwt_required()
def crear_cita():
    """Crear una nueva cita médica"""
    usuario_id = get_jwt_identity()

    data = request.get_json()

    # Validación básica de datos requeridos
    if not data or not all(
        k in data for k in ["fecha", "motivo", "id_paciente", "id_doctor", "id_centro"]
    ):
        return jsonify({"error": "Faltan datos requeridos"}), 400

    try:
        # Convertir la fecha a formato datetime
        fecha_dt = datetime.fromisoformat(data["fecha"].replace("Z", "+00:00"))
    except:
        return jsonify({"error": "Formato de fecha inválido"}), 400

    # Reenviar token al user_service para endpoints de verificación
    auth = request.headers.get("Authorization", "")
    token = auth.split(" ", 1)[1].strip() if auth.lower().startswith("bearer ") else ""

    # Verificar que el paciente exista
    ok, status, body = verificar_existencia_user_service(
        f"/verify/pacientes/{data['id_paciente']}", token
    )
    if not ok:
        if status in (401, 403):
            return (
                jsonify(
                    {
                        "error": "No autorizado para verificar paciente",
                        "user_service_status": status,
                        "user_service_body": body,
                    }
                ),
                status,
            )
        return (
            jsonify(
                {
                    "error": "El paciente no existe o está inactivo",
                    "user_service_status": status,
                    "user_service_body": body,
                }
            ),
            400,
        )

    # Verificar que el doctor exista
    ok, status, body = verificar_existencia_user_service(
        f"/verify/doctores/{data['id_doctor']}", token
    )
    if not ok:
        if status in (401, 403):
            return (
                jsonify(
                    {
                        "error": "No autorizado para verificar doctor",
                        "user_service_status": status,
                        "user_service_body": body,
                    }
                ),
                status,
            )
        return (
            jsonify(
                {
                    "error": "El doctor no existe o está inactivo",
                    "user_service_status": status,
                    "user_service_body": body,
                }
            ),
            400,
        )

    # Verificar que el centro exista
    ok, status, body = verificar_existencia_user_service(
        f"/verify/centros/{data['id_centro']}", token
    )
    if not ok:
        if status in (401, 403):
            return (
                jsonify(
                    {
                        "error": "No autorizado para verificar centro",
                        "user_service_status": status,
                        "user_service_body": body,
                    }
                ),
                status,
            )
        return (
            jsonify(
                {
                    "error": "El centro no existe o está inactivo",
                    "user_service_status": status,
                    "user_service_body": body,
                }
            ),
            400,
        )

    # Verificar que no haya otra cita del doctor en la misma fecha y hora
    cita_conflicto = Appointment.query.filter_by(
        id_doctor=data["id_doctor"],
        fecha=fecha_dt,
        estado="PROGRAMADA",
    ).first()

    if cita_conflicto:
        return jsonify(
            {"error": "El doctor ya tiene una cita programada en esa fecha y hora"}
        ), 400

    # Crear nueva cita
    nueva_cita = Appointment(
        fecha=fecha_dt,
        motivo=data["motivo"],
        id_paciente=data["id_paciente"],
        id_doctor=data["id_doctor"],
        id_centro=data["id_centro"],
        id_usuario_registra=usuario_id,
    )

    db.session.add(nueva_cita)
    db.session.commit()

    return jsonify(
        {
            "mensaje": "Cita creada exitosamente",
            "cita": {
                "id": nueva_cita.id,
                "fecha": nueva_cita.fecha.isoformat(),
                "motivo": nueva_cita.motivo,
                "estado": nueva_cita.estado,
                "id_paciente": nueva_cita.id_paciente,
                "id_doctor": nueva_cita.id_doctor,
                "id_centro": nueva_cita.id_centro,
            },
        }
    ), 201


@citas_bp.route("/citas", methods=["GET"])
@jwt_required()
def listar_citas():
    """Listar citas con filtros opcionales"""
    usuario_id = get_jwt_identity()

    # Obtener parámetros de consulta
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    id_doctor = request.args.get("id_doctor", type=int)
    id_centro = request.args.get("id_centro", type=int)
    estado = request.args.get("estado")

    # Construir consulta base
    query = Appointment.query

    # Aplicar filtros si se proporcionan
    if fecha_inicio:
        query = query.filter(Appointment.fecha >= datetime.fromisoformat(fecha_inicio))
    if fecha_fin:
        query = query.filter(Appointment.fecha <= datetime.fromisoformat(fecha_fin))
    if id_doctor:
        query = query.filter_by(id_doctor=id_doctor)
    if id_centro:
        query = query.filter_by(id_centro=id_centro)
    if estado:
        query = query.filter_by(estado=estado)

    citas = query.all()

    return jsonify(
        {
            "citas": [
                {
                    "id": c.id,
                    "fecha": c.fecha.isoformat(),
                    "motivo": c.motivo,
                    "estado": c.estado,
                    "id_paciente": c.id_paciente,
                    "id_doctor": c.id_doctor,
                    "id_centro": c.id_centro,
                }
                for c in citas
            ]
        }
    ), 200


@citas_bp.route("/citas/<int:cita_id>", methods=["GET"])
@jwt_required()
def obtener_cita(cita_id):
    """Obtener una cita específica por ID"""
    cita = Appointment.query.get(cita_id)

    if not cita:
        return jsonify({"error": "Cita no encontrada"}), 404

    return jsonify(
        {
            "cita": {
                "id": cita.id,
                "fecha": cita.fecha.isoformat(),
                "motivo": cita.motivo,
                "estado": cita.estado,
                "id_paciente": cita.id_paciente,
                "id_doctor": cita.id_doctor,
                "id_centro": cita.id_centro,
            }
        }
    ), 200


@citas_bp.route("/citas/<int:cita_id>", methods=["PUT"])
@jwt_required()
def cancelar_cita(cita_id):
    """Cancelar una cita existente"""
    cita = Appointment.query.get(cita_id)

    if not cita:
        return jsonify({"error": "Cita no encontrada"}), 404

    # Verificar que no esté ya cancelada
    if cita.estado == "CANCELADA":
        return jsonify({"error": "La cita ya está cancelada"}), 400

    # Cambiar estado a cancelada
    cita.estado = "CANCELADA"
    db.session.commit()

    return jsonify(
        {
            "mensaje": "Cita cancelada exitosamente",
            "cita": {
                "id": cita.id,
                "fecha": cita.fecha.isoformat(),
                "motivo": cita.motivo,
                "estado": cita.estado,
            },
        }
    ), 200


# ========================================
# ENDPOINTS DE HEALTH Y ROOT
# ========================================


@app.route("/health")
def health():
    """Endpoint de verificación de salud del servicio"""
    return jsonify(
        {"service": "appointment_service", "status": "ok", "environment": "development"}
    ), 200


@app.route("/")
def root():
    """Endpoint raíz con información del servicio"""
    return jsonify(
        {
            "name": "OdontoCare - Servicio de Gestión de Citas",
            "version": "1.0.0",
            "endpoints": {"citas": "/citas", "health": "/health"},
        }
    ), 200


# ========================================
# INICIALIZACIÓN
# ========================================

# Registrar blueprint
app.register_blueprint(citas_bp)

# Crear tablas de la base de datos
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)
