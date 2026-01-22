# 🦷 OdontoCare — Sistema de Gestión Dental

Plataforma de microservicios (Flask + SQLAlchemy + JWT + Docker) para administrar usuarios, roles, pacientes, doctores, centros y citas.

## 📚 Resumen rápido
- Microservicios:
  - `user_service`: autenticación, usuarios, pacientes, doctores, centros (puerto 8000).
  - `appointment_service`: gestión de citas y validación contra `user_service` (puerto 8001).
- Persistencia: SQLite (por defecto) con SQLAlchemy; volúmenes Docker para datos.
- Seguridad: JWT, validación de roles (admin, medico, secretaria, paciente).
- Cliente CLI: `carga_inicial.py` para poblar datos vía CSV y crear una cita de demostración.

## 🏗️ Arquitectura y características
- REST con Blueprints (`auth_bp`, `admin_bp`, `citas_bp`).
- Respuestas JSON y códigos HTTP adecuados.
- Contenerización por servicio y orquestación con `docker-compose.yml`.
- Red Docker compartida para comunicación entre servicios.

## 📂 Estructura del repositorio
```
Odontocare/
├─ appointment_service/   # Servicio de citas (8001)
├─ user_service/          # Servicio de usuarios/pacientes/doctores/centros (8000)
├─ csv_templates/         # CSV de ejemplo para carga masiva
├─ carga_inicial.py       # Cliente CLI para carga y cita de demo
├─ collection.json        # Colección de pruebas (p.ej. Postman)
├─ docker-compose.yml
└─ README.md
```

## 🚀 Puesta en marcha (Docker recomendado)
1) Ubicarse en el proyecto:
```bash
cd /home/ferguscosmo/Documentos/Odontocare
```
2) Construir y levantar:
```bash
docker-compose up --build -d
```
3) Verificar contenedores:
```bash
docker ps
```
4) Healthchecks:
```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```
5) Detener todo:
```bash
docker-compose down
```

## 🧑‍💻 Ejecución local (desarrollo)
Requisitos: Python 3.11+, pip, virtualenv.

- `user_service`:
```bash
cd user_service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py
```
- `appointment_service` (otra terminal):
```bash
cd appointment_service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## 🌐 API (resumen)
**Servicio de Usuarios** (`http://localhost:8000`)
- Auth: `POST /auth/register`, `POST /auth/login` (JWT).
- Admin (requiere `Authorization: Bearer <token>` y rol `admin`):
  - Pacientes: `POST /admin/pacientes`, `GET /admin/pacientes`, `GET /admin/pacientes/<id>`
  - Doctores: `POST /admin/doctores`, `GET /admin/doctores`
  - Centros: `POST /admin/centros`

**Servicio de Citas** (`http://localhost:8001`, requiere JWT)
- `POST /citas` (crea cita; valida paciente/doctor/centro y disponibilidad)
- `GET /citas` (filtros: `fecha_inicio`, `fecha_fin`, `id_doctor`, `id_centro`, `estado`)
- `GET /citas/<id>`
- `PUT /citas/<id>` (cancelar)

## 🤖 Carga inicial con CSV
- CSV de ejemplo: `csv_templates/datos.csv`.
- Requisitos: servicios arriba y usuario admin existente.
- Uso:
```bash
python carga_inicial.py csv_templates/datos.csv <admin_user> <admin_pass>
```
El script autentica, registra pacientes/doctores/centros desde el CSV y crea una cita de demostración.

## 🧪 Pruebas rápidas
- Health: `curl http://localhost:8000/health` y `curl http://localhost:8001/health`.
- Flujo mínimo (requiere `jq`):
  1) `POST /auth/register` (crear admin).
  2) `POST /auth/login` → `TOKEN=$(...)`.
  3) Crear paciente/doctor/centro en `user_service` con `Authorization: Bearer $TOKEN`.
  4) Crear cita en `appointment_service` con el mismo token.

## 🛠️ Solución de problemas breve
- Puertos 8000/8001 ocupados: liberar (`lsof -i :8000`, `lsof -i :8001`) y reconstruir (`docker-compose up --build -d`).
- Conexión entre servicios: revisar red y logs (`docker logs <container>`), asegurar ambos contenedores arriba.
- Token inválido: reautenticar y enviar header `Authorization: Bearer <token>`.
- BD no inicializa: `docker-compose down -v` y volver a levantar.

## 📞 Recursos
- [Flask](https://flask.palletsprojects.com/)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- [Docker](https://docs.docker.com/)
- [JWT.io](https://jwt.io/)