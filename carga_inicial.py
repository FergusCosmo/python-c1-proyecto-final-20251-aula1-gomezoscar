#!/usr/bin/env python3
"""
OdontoCare - Cliente REST Simple

Este script es un cliente HTTP simple para interactuar con los servicios:
- user_service (http://localhost:8000)
- appointment_service (http://localhost:8001)

Características:
- SIN validaciones del lado del cliente
- Solo envía datos y muestra las respuestas de la API
- Menú interactivo para operar con los endpoints REST
- Permite ingresar datos desde consola para generar JSON de envío
- Ctrl+C vuelve automáticamente al menú principal
- Leyenda visible en el menú principal
"""

import argparse
import csv
import getpass
import json
import os
import sys

import requests

# Configuración por defecto
DEFAULT_USER_SERVICE_URL = "http://localhost:8000"
DEFAULT_APPOINTMENT_SERVICE_URL = "http://localhost:8001"
DEFAULT_TIMEOUT = 10
DEFAULT_TEMPLATES_DIR = "csv_templates"


# ---------- Colores ANSI para la terminal ----------

class Colors:
    """Clase para manejar colores ANSI en la terminal"""
    RESET = "[0m"
    BOLD = "[1m"
    DIM = "[2m"

    # Colores de texto - Paleta minimalista profesional
    BLUE = "[34m"
    GREEN = "[32m"
    YELLOW = "[33m"
    GRAY = "[90m"
    WHITE = "[37m"

    # Combinaciones
    HEADER = BLUE + BOLD
    OPTION = WHITE
    SUCCESS = GREEN
    ERROR = YELLOW
    INFO = BLUE
    PROMPT = BLUE
    DIM = GRAY


def print_header(text):
    """Imprime un encabezado decorado"""
    width = 70
    padding = (width - len(text) - 2) // 2
    print(Colors.BLUE + Colors.BOLD + "╔" + "═" * (width - 2) + "╗" + Colors.RESET)
    print(
        Colors.BLUE
        + Colors.BOLD
        + "║"
        + Colors.RESET
        + " " * padding
        + Colors.HEADER
        + text
        + Colors.RESET
        + " " * (width - 2 - padding - len(text))
        + Colors.BLUE
        + Colors.BOLD
        + "║"
        + Colors.RESET
    )
    print(Colors.BLUE + Colors.BOLD + "╚" + "═" * (width - 2) + "╝" + Colors.RESET)


def print_section(title):
    """Imprime un separador de sección"""
    print(f"\n{Colors.BLUE + Colors.BOLD}───────────────────────────────────────────────────────────────{Colors.RESET}")
    print(f"{Colors.BLUE + Colors.BOLD}  {title}{Colors.RESET}")
    print(f"{Colors.BLUE + Colors.BOLD}───────────────────────────────────────────────────────────────{Colors.RESET}")


def print_item(number, text):
    """Imprime una opción de menú"""
    print(f"  {Colors.BLUE}{number}){Colors.RESET} {text}")


def print_success(text):
    """Imprime un mensaje de éxito"""
    print(f"{Colors.GREEN}OK: {text}{Colors.RESET}")


def print_error(text):
    """Imprime un mensaje de error"""
    print(f"{Colors.YELLOW}Error: {text}{Colors.RESET}")


def print_info(text):
    """Imprime un mensaje de información"""
    print(f"{Colors.BLUE}Info: {text}{Colors.RESET}")


def print_warning(text):
    """Imprime un mensaje de advertencia"""
    print(f"{Colors.YELLOW}Advertencia: {text}{Colors.RESET}")


def print_prompt(text):
    """Imprime un prompt para el usuario"""
    print(f"{Colors.BLUE}► {text}{Colors.RESET}", end="")


# ---------- Cliente REST Simple ----------


class RestClient:
    """Cliente REST simple para interactuar con los servicios"""

    def __init__(self, user_service_url, appointment_service_url):
        self.user_service_url = user_service_url
        self.appointment_service_url = appointment_service_url
        self.session = requests.Session()
        self._token = None

    # ---------- Auth ----------

    def login(self, username, password):
        """POST /auth/login"""
        url = f"{self.user_service_url}/auth/login"
        data = {"username": username, "password": password}
        response = self.session.post(url, json=data, timeout=DEFAULT_TIMEOUT)
        self._token = response.json().get("access_token")
        return response.json()

    def register_user(self, data):
        """POST /auth/register"""
        url = f"{self.user_service_url}/auth/register"
        response = self.session.post(url, json=data, timeout=DEFAULT_TIMEOUT)
        return response.json()

    def verify_token(self):
        """GET /verify/token"""
        url = f"{self.user_service_url}/verify/token"
        headers = self._get_auth_headers()
        response = self.session.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        return response.json()

    # ---------- Pacientes ----------

    def list_patients(self, params=None):
        """GET /admin/pacientes"""
        url = f"{self.user_service_url}/admin/pacientes"
        headers = self._get_auth_headers()
        response = self.session.get(url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT)
        return response.json()

    def get_patient(self, patient_id):
        """GET /admin/pacientes/{id}"""
        url = f"{self.user_service_url}/admin/pacientes/{patient_id}"
        headers = self._get_auth_headers()
        response = self.session.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        return response.json()

    def create_patient(self, data):
        """POST /admin/pacientes"""
        url = f"{self.user_service_url}/admin/pacientes"
        headers = self._get_auth_headers()
        response = self.session.post(url, headers=headers, json=data, timeout=DEFAULT_TIMEOUT)
        return response.json()

    def update_patient(self, patient_id, data):
        """PUT /admin/pacientes/{id}"""
        url = f"{self.user_service_url}/admin/pacientes/{patient_id}"
        headers = self._get_auth_headers()
        response = self.session.put(url, headers=headers, json=data, timeout=DEFAULT_TIMEOUT)
        return response.json()

    def delete_patient(self, patient_id):
        """DELETE /admin/pacientes/{id}"""
        url = f"{self.user_service_url}/admin/pacientes/{patient_id}"
        headers = self._get_auth_headers()
        response = self.session.delete(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        return response.json()

    # ---------- Doctores ----------

    def list_doctors(self, params=None):
        """GET /admin/doctores"""
        url = f"{self.user_service_url}/admin/doctores"
        headers = self._get_auth_headers()
        response = self.session.get(url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT)
        return response.json()

    def get_doctor(self, doctor_id):
        """GET /admin/doctores/{id}"""
        url = f"{self.user_service_url}/admin/doctores/{doctor_id}"
        headers = self._get_auth_headers()
        response = self.session.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        return response.json()

    def create_doctor(self, data):
        """POST /admin/doctores"""
        url = f"{self.user_service_url}/admin/doctores"
        headers = self._get_auth_headers()
        response = self.session.post(url, headers=headers, json=data, timeout=DEFAULT_TIMEOUT)
        return response.json()

    def update_doctor(self, doctor_id, data):
        """PUT /admin/doctores/{id}"""
        url = f"{self.user_service_url}/admin/doctores/{doctor_id}"
        headers = self._get_auth_headers()
        response = self.session.put(url, headers=headers, json=data, timeout=DEFAULT_TIMEOUT)
        return response.json()

    def delete_doctor(self, doctor_id):
        """DELETE /admin/doctores/{id}"""
        url = f"{self.user_service_url}/admin/doctores/{doctor_id}"
        headers = self._get_auth_headers()
        response = self.session.delete(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        return response.json()

    # ---------- Centros ----------

    def list_centers(self, params=None):
        """GET /admin/centros"""
        url = f"{self.user_service_url}/admin/centros"
        headers = self._get_auth_headers()
        response = self.session.get(url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT)
        return response.json()

    def get_center(self, center_id):
        """GET /admin/centros/{id}"""
        url = f"{self.user_service_url}/admin/centros/{center_id}"
        headers = self._get_auth_headers()
        response = self.session.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        return response.json()

    def create_center(self, data):
        """POST /admin/centros"""
        url = f"{self.user_service_url}/admin/centros"
        headers = self._get_auth_headers()
        response = self.session.post(url, headers=headers, json=data, timeout=DEFAULT_TIMEOUT)
        return response.json()

    def update_center(self, center_id, data):
        """PUT /admin/centros/{id}"""
        url = f"{self.user_service_url}/admin/centros/{center_id}"
        headers = self._get_auth_headers()
        response = self.session.put(url, headers=headers, json=data, timeout=DEFAULT_TIMEOUT)
        return response.json()

    def delete_center(self, center_id):
        """DELETE /admin/centros/{id}"""
        url = f"{self.user_service_url}/admin/centros/{center_id}"
        headers = self._get_auth_headers()
        response = self.session.delete(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        return response.json()

    # ---------- Citas ----------

    def list_appointments(self, params=None):
        """GET /citas"""
        url = f"{self.appointment_service_url}/citas"
        headers = self._get_auth_headers()
        response = self.session.get(url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT)
        return response.json()

    def get_appointment(self, appointment_id):
        """GET /citas/{id}"""
        url = f"{self.appointment_service_url}/citas/{appointment_id}"
        headers = self._get_auth_headers()
        response = self.session.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        return response.json()

    def create_appointment(self, data):
        """POST /citas"""
        url = f"{self.appointment_service_url}/citas"
        headers = self._get_auth_headers()
        response = self.session.post(url, headers=headers, json=data, timeout=DEFAULT_TIMEOUT)
        return response.json()

    def cancel_appointment(self, appointment_id):
        """PUT /citas/{id}"""
        url = f"{self.appointment_service_url}/citas/{appointment_id}"
        headers = self._get_auth_headers()
        response = self.session.put(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        return response.json()

    # ---------- Helpers ----------

    def _get_auth_headers(self):
        """Retorna headers con token JWT"""
        if not self._token:
            return {}
        return {"Authorization": f"Bearer {self._token}"}


# ---------- Funciones de utilidad para el menú ----------


def _prompt(message, default=""):
    """Pide input al usuario"""
    if default:
        prompt = f"{message} [{default}]: "
    else:
        prompt = f"{message}: "
    return input(prompt).strip() or default


def _prompt_secret(message):
    """Pide password al usuario"""
    return getpass.getpass(message + ": ")


def _prompt_int(message, default=None):
    """Pide un número entero al usuario"""
    while True:
        val = _prompt(message, str(default) if default is not None else "")
        try:
            return int(val) if val else default
        except ValueError:
            print("Por favor, introduce un número válido.")


def _print_json(data):
    """Imprime JSON formateado"""
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ---------- Menús interactivos ----------


def _print_main_menu(is_authenticated):
    """Imprime el menú principal"""
    print_header("OdontoCare - Cliente REST")

    status = (
        f"{Colors.GREEN}Autenticado{Colors.RESET}"
        if is_authenticated
        else f"{Colors.GRAY}No autenticado{Colors.RESET}"
    )
    print(f"  Estado: {status}\n")

    if not is_authenticated:
        print_item("1", "Registrarse nuevo usuario")
        print_item("2", "Iniciar sesión")
        print(f"\n  {Colors.DIM}0) Salir{Colors.RESET}")
    else:
        print_item("1", "Verificar token actual")
        print_item("2", "Cerrar sesión")
        print(f"\n{Colors.BLUE + Colors.BOLD}  Gestión de Entidades{Colors.RESET}")
        print_item("3", "Gestionar Pacientes")
        print_item("4", "Gestionar Doctores")
        print_item("5", "Gestionar Centros")
        print_item("6", "Gestionar Citas")
        print(f"\n{Colors.BLUE + Colors.BOLD}  Operaciones de Datos{Colors.RESET}")
        print_item("7", "Carga Masiva desde CSV")
        print(f"\n  {Colors.DIM}0) Salir{Colors.RESET}")

    # Leyenda
    print(f"\n{Colors.DIM}Leyenda: Ctrl+C para volver al menú principal{Colors.RESET}")


# ---------- Submenú Pacientes ----------


def _menu_patients(client):
    """Submenú de Pacientes"""
    while True:
        try:
            print_section("Gestión de Pacientes")

            print_item("1", "Listar todos los pacientes")
            print_item("2", "Buscar paciente por ID")
            print_item("3", "Registrar nuevo paciente")
            print_item("4", "Actualizar datos de paciente")
            print_item("5", "Eliminar paciente")
            print(f"\n  {Colors.DIM}0) Volver{Colors.RESET}")

            choice = _prompt("Opción", "1")

            if choice == "1":
                # Listar
                params = {}
                estado = _prompt("estado (ACTIVO/INACTIVO, opcional)", "")
                if estado:
                    params["estado"] = estado
                nombre = _prompt("filtro nombre (opcional)", "")
                if nombre:
                    params["nombre"] = nombre
                page = _prompt_int("page", "1")
                if page:
                    params["page"] = page
                per_page = _prompt_int("per_page", "10")
                if per_page:
                    params["per_page"] = per_page

                print(f"\n[REQUEST] GET /admin/pacientes")
                print(f"Params: {params}")
                print(f"\n[RESPONSE]")
                result = client.list_patients(params)
                _print_json(result)

            elif choice == "2":
                # Obtener por ID
                paciente_id = _prompt_int("paciente_id")
                print(f"\n[REQUEST] GET /admin/pacientes/{paciente_id}")
                print(f"\n[RESPONSE]")
                result = client.get_patient(paciente_id)
                _print_json(result)

            elif choice == "3":
                # Crear
                print(f"\nIngresa los datos del paciente:")
                data = {}
                data["nombre"] = _prompt("nombre")
                telefono = _prompt("telefono (opcional)", "")
                if telefono:
                    data["telefono"] = telefono
                estado = _prompt("estado (ACTIVO/INACTIVO opcional)", "")
                if estado:
                    data["estado"] = estado

                print(f"\n[REQUEST] POST /admin/pacientes")
                print(f"Payload:")
                _print_json(data)
                print(f"\n[RESPONSE]")
                result = client.create_patient(data)
                _print_json(result)

            elif choice == "4":
                # Actualizar
                paciente_id = _prompt_int("paciente_id")
                print(f"\nIngresa los datos a actualizar (deja vacío para mantener):")
                data = {}
                nombre = _prompt("nombre", "")
                if nombre:
                    data["nombre"] = nombre
                telefono = _prompt("telefono (opcional)", "")
                if telefono:
                    data["telefono"] = telefono
                estado = _prompt("estado (ACTIVO/INACTIVO opcional)", "")
                if estado:
                    data["estado"] = estado

                if not data:
                    print("No se especificaron cambios.")
                    return

                print(f"\n[REQUEST] PUT /admin/pacientes/{paciente_id}")
                print(f"Payload:")
                _print_json(data)
                print(f"\n[RESPONSE]")
                result = client.update_patient(paciente_id, data)
                _print_json(result)

            elif choice == "5":
                # Eliminar
                paciente_id = _prompt_int("paciente_id")
                confirm = _prompt(f"¿Eliminar paciente {paciente_id}? (s/N)", "n")
                if confirm.lower() in ["s", "y", "si", "sí"]:
                    print(f"\n[REQUEST] DELETE /admin/pacientes/{paciente_id}")
                    print(f"\n[RESPONSE]")
                    result = client.delete_patient(paciente_id)
                    _print_json(result)
                else:
                    print("Cancelado.")

            elif choice == "0":
                return

            else:
                print_error("Opción inválida.")

        except KeyboardInterrupt:
            print_warning("Interrupción detectada (Ctrl+C) - Volviendo al menú principal...")
            return


# ---------- Submenú Doctores ----------


def _menu_doctors(client):
    """Submenú de Doctores"""
    while True:
        try:
            print_section("Gestión de Doctores")

            print_item("1", "Listar todos los doctores")
            print_item("2", "Buscar doctor por ID")
            print_item("3", "Registrar nuevo doctor")
            print_item("4", "Actualizar datos de doctor")
            print_item("5", "Eliminar doctor")
            print(f"\n  {Colors.DIM}0) Volver{Colors.RESET}")

            choice = _prompt("Opción", "1")

            if choice == "1":
                # Listar
                params = {}
                estado = _prompt("estado (ACTIVO/INACTIVO, opcional)", "")
                if estado:
                    params["estado"] = estado
                especialidad = _prompt("filtro especialidad (opcional)", "")
                if especialidad:
                    params["especialidad"] = especialidad
                page = _prompt_int("page", "1")
                if page:
                    params["page"] = page
                per_page = _prompt_int("per_page", "10")
                if per_page:
                    params["per_page"] = per_page

                print(f"\n[REQUEST] GET /admin/doctores")
                print(f"Params: {params}")
                print(f"\n[RESPONSE]")
                result = client.list_doctors(params)
                _print_json(result)

            elif choice == "2":
                # Obtener por ID
                doctor_id = _prompt_int("doctor_id")
                print(f"\n[REQUEST] GET /admin/doctores/{doctor_id}")
                print(f"\n[RESPONSE]")
                result = client.get_doctor(doctor_id)
                _print_json(result)

            elif choice == "3":
                # Crear
                print(f"\nIngresa los datos del doctor:")
                data = {}
                data["nombre"] = _prompt("nombre")
                especialidad = _prompt("especialidad (opcional)", "")
                if especialidad:
                    data["especialidad"] = especialidad
                estado = _prompt("estado (ACTIVO/INACTIVO opcional)", "")
                if estado:
                    data["estado"] = estado

                print(f"\n[REQUEST] POST /admin/doctores")
                print(f"Payload:")
                _print_json(data)
                print(f"\n[RESPONSE]")
                result = client.create_doctor(data)
                _print_json(result)

            elif choice == "4":
                # Actualizar
                doctor_id = _prompt_int("doctor_id")
                print(f"\nIngresa los datos a actualizar (deja vacío para mantener):")
                data = {}
                nombre = _prompt("nombre", "")
                if nombre:
                    data["nombre"] = nombre
                especialidad = _prompt("especialidad (opcional)", "")
                if especialidad:
                    data["especialidad"] = especialidad
                estado = _prompt("estado (ACTIVO/INACTIVO opcional)", "")
                if estado:
                    data["estado"] = estado

                if not data:
                    print("No se especificaron cambios.")
                    return

                print(f"\n[REQUEST] PUT /admin/doctores/{doctor_id}")
                print(f"Payload:")
                _print_json(data)
                print(f"\n[RESPONSE]")
                result = client.update_doctor(doctor_id, data)
                _print_json(result)

            elif choice == "5":
                # Eliminar
                doctor_id = _prompt_int("doctor_id")
                confirm = _prompt(f"¿Eliminar doctor {doctor_id}? (s/N)", "n")
                if confirm.lower() in ["s", "y", "si", "sí"]:
                    print(f"\n[REQUEST] DELETE /admin/doctores/{doctor_id}")
                    print(f"\n[RESPONSE]")
                    result = client.delete_doctor(doctor_id)
                    _print_json(result)
                else:
                    print("Cancelado.")

            elif choice == "0":
                return

            else:
                print_error("Opción inválida.")

        except KeyboardInterrupt:
            print_warning("Interrupción detectada (Ctrl+C) - Volviendo al menú principal...")
            return


# ---------- Submenú Centros ----------


def _menu_centers(client):
    """Submenú de Centros"""
    while True:
        try:
            print_section("Gestión de Centros Médicos")

            print_item("1", "Listar todos los centros")
            print_item("2", "Buscar centro por ID")
            print_item("3", "Registrar nuevo centro")
            print_item("4", "Actualizar datos de centro")
            print_item("5", "Eliminar centro")
            print(f"\n  {Colors.DIM}0) Volver{Colors.RESET}")

            choice = _prompt("Opción", "1")

            if choice == "1":
                # Listar
                params = {}
                estado = _prompt("estado (ACTIVO/INACTIVO, opcional)", "")
                if estado:
                    params["estado"] = estado
                page = _prompt_int("page", "1")
                if page:
                    params["page"] = page
                per_page = _prompt_int("per_page", "10")
                if per_page:
                    params["per_page"] = per_page

                print(f"\n[REQUEST] GET /admin/centros")
                print(f"Params: {params}")
                print(f"\n[RESPONSE]")
                result = client.list_centers(params)
                _print_json(result)

            elif choice == "2":
                # Obtener por ID
                center_id = _prompt_int("centro_id")
                print(f"\n[REQUEST] GET /admin/centros/{center_id}")
                print(f"\n[RESPONSE]")
                result = client.get_center(center_id)
                _print_json(result)

            elif choice == "3":
                # Crear
                print(f"\nIngresa los datos del centro:")
                data = {}
                data["nombre"] = _prompt("nombre")
                direccion = _prompt("direccion (opcional)", "")
                if direccion:
                    data["direccion"] = direccion
                estado = _prompt("estado (ACTIVO/INACTIVO opcional)", "")
                if estado:
                    data["estado"] = estado

                print(f"\n[REQUEST] POST /admin/centros")
                print(f"Payload:")
                _print_json(data)
                print(f"\n[RESPONSE]")
                result = client.create_center(data)
                _print_json(result)

            elif choice == "4":
                # Actualizar
                center_id = _prompt_int("centro_id")
                print(f"\nIngresa los datos a actualizar (deja vacío para mantener):")
                data = {}
                nombre = _prompt("nombre", "")
                if nombre:
                    data["nombre"] = nombre
                direccion = _prompt("direccion (opcional)", "")
                if direccion:
                    data["direccion"] = direccion
                estado = _prompt("estado (ACTIVO/INACTIVO opcional)", "")
                if estado:
                    data["estado"] = estado

                if not data:
                    print("No se especificaron cambios.")
                    return

                print(f"\n[REQUEST] PUT /admin/centros/{center_id}")
                print(f"Payload:")
                _print_json(data)
                print(f"\n[RESPONSE]")
                result = client.update_center(center_id, data)
                _print_json(result)

            elif choice == "5":
                # Eliminar
                center_id = _prompt_int("centro_id")
                confirm = _prompt(f"¿Eliminar centro {center_id}? (s/N)", "n")
                if confirm.lower() in ["s", "y", "si", "sí"]:
                    print(f"\n[REQUEST] DELETE /admin/centros/{center_id}")
                    print(f"\n[RESPONSE]")
                    result = client.delete_center(center_id)
                    _print_json(result)
                else:
                    print("Cancelado.")

            elif choice == "0":
                return

            else:
                print_error("Opción inválida.")

        except KeyboardInterrupt:
            print_warning("Interrupción detectada (Ctrl+C) - Volviendo al menú principal...")
            return


# ---------- Submenú Citas ----------


def _menu_appointments(client):
    """Submenú de Citas"""
    while True:
        try:
            print_section("Gestión de Citas")

            print_item("1", "Listar todas las citas")
            print_item("2", "Buscar cita por ID")
            print_item("3", "Agendar nueva cita")
            print_item("4", "Cancelar cita existente")
            print(f"\n  {Colors.DIM}0) Volver{Colors.RESET}")

            choice = _prompt("Opción", "1")

            if choice == "1":
                # Listar
                params = {}
                fecha_inicio = _prompt("fecha_inicio (YYYY-MM-DD, opcional)", "")
                if fecha_inicio:
                    params["fecha_inicio"] = fecha_inicio
                fecha_fin = _prompt("fecha_fin (YYYY-MM-DD, opcional)", "")
                if fecha_fin:
                    params["fecha_fin"] = fecha_fin
                id_doctor = _prompt_int("id_doctor (opcional)", "")
                if id_doctor:
                    params["id_doctor"] = id_doctor
                id_centro = _prompt_int("id_centro (opcional)", "")
                if id_centro:
                    params["id_centro"] = id_centro
                estado = _prompt("estado (opcional)", "")
                if estado:
                    params["estado"] = estado

                print(f"\n[REQUEST] GET /citas")
                print(f"Params: {params}")
                print(f"\n[RESPONSE]")
                result = client.list_appointments(params)
                _print_json(result)

            elif choice == "2":
                # Obtener por ID
                appointment_id = _prompt_int("cita_id")
                print(f"\n[REQUEST] GET /citas/{appointment_id}")
                print(f"\n[RESPONSE]")
                result = client.get_appointment(appointment_id)
                _print_json(result)

            elif choice == "3":
                # Crear
                print(f"\nIngresa los datos de la cita:")
                data = {}
                data["fecha"] = _prompt("fecha (ISO 8601, ej: 2026-01-20T10:00:00)")
                data["motivo"] = _prompt("motivo")
                data["id_paciente"] = _prompt_int("id_paciente")
                data["id_doctor"] = _prompt_int("id_doctor")
                data["id_centro"] = _prompt_int("id_centro")

                print(f"\n[REQUEST] POST /citas")
                print(f"Payload:")
                _print_json(data)
                print(f"\n[RESPONSE]")
                result = client.create_appointment(data)
                _print_json(result)

            elif choice == "4":
                # Cancelar
                appointment_id = _prompt_int("cita_id")
                confirm = _prompt(f"¿Cancelar cita {appointment_id}? (s/N)", "n")
                if confirm.lower() in ["s", "y", "si", "sí"]:
                    print(f"\n[REQUEST] PUT /citas/{appointment_id}")
                    print(f"\n[RESPONSE]")
                    result = client.cancel_appointment(appointment_id)
                    _print_json(result)
                else:
                    print("Cancelado.")

            elif choice == "0":
                return

            else:
                print_error("Opción inválida.")

        except KeyboardInterrupt:
            print_warning("Interrupción detectada (Ctrl+C) - Volviendo al menú principal...")
            return


# ---------- Menú Principal ----------


def run_interactive_menu(client):
    """Ejecuta el menú principal interactivo"""
    while True:
        try:
            _print_main_menu(client._token is not None)
            choice = _prompt("\nSelecciona una opción", "0")

            if choice == "0":
                print(f"\n{Colors.GREEN}Gracias por usar OdontoCare!{Colors.RESET}\n")
                break

            # Menú no autenticado
            if client._token is None:
                if choice == "1":
                    # Registrarse
                    print(f"\n{Colors.BLUE + Colors.BOLD}Registro de Nuevo Usuario{Colors.RESET}\n")
                    data = {}
                    data["username"] = _prompt("Username")
                    data["password"] = _prompt_secret("Password")
                    rol = _prompt("Rol (opcional, default: paciente)", "")
                    if rol:
                        data["rol"] = rol

                    print(f"\n{Colors.INFO}REQUEST{Colors.RESET} POST /auth/register")
                    print(f"{Colors.DIM}Payload:{Colors.RESET}")
                    _print_json(data)
                    print(f"\n{Colors.SUCCESS}RESPONSE{Colors.RESET}")
                    result = client.register_user(data)
                    _print_json(result)

                elif choice == "2":
                    # Login
                    print(f"\n{Colors.BLUE + Colors.BOLD}Iniciar Sesión{Colors.RESET}\n")
                    username = _prompt("Username")
                    password = _prompt_secret("Password")

                    print(f"\n{Colors.INFO}REQUEST{Colors.RESET} POST /auth/login")
                    print(f"{Colors.DIM}Payload: {{'username': '{username}', 'password': '***'}}{Colors.RESET}")
                    print(f"\n{Colors.SUCCESS}RESPONSE{Colors.RESET}")
                    result = client.login(username, password)
                    _print_json(result)
                    print_success(f"Bienvenido, {username}")

                else:
                    print_error("Opción inválida. Por favor, selecciona una opción válida.")

            # Menú autenticado
            else:
                if choice == "1":
                    # Verificar token
                    print(f"\n{Colors.BLUE + Colors.BOLD}Verificar Token{Colors.RESET}\n")
                    print(f"{Colors.INFO}REQUEST{Colors.RESET} GET /verify/token")
                    print(f"\n{Colors.SUCCESS}RESPONSE{Colors.RESET}")
                    result = client.verify_token()
                    _print_json(result)

                elif choice == "2":
                    # Cerrar sesión
                    client._token = None
                    print_warning("Sesión cerrada correctamente")

                elif choice == "3":
                    _menu_patients(client)

                elif choice == "4":
                    _menu_doctors(client)

                elif choice == "5":
                    _menu_centers(client)

                elif choice == "6":
                    _menu_appointments(client)

                elif choice == "7":
                    _menu_bulk_load(client)

                else:
                    print_error("Opción inválida. Por favor, selecciona una opción válida.")

        except KeyboardInterrupt:
            print_warning("Interrupción detectada (Ctrl+C)")
            cont = _prompt("¿Deseas continuar? (S/n)", "n")
            if not cont.lower() in ["s", "y", "si", "sí"]:
                print(f"\n{Colors.GREEN}Hasta pronto!{Colors.RESET}\n")
                break


# ---------- Carga Masiva CSV ----------


def _load_csv_file(csv_path):
    """Lee un archivo CSV y retorna una lista de diccionarios"""
    rows = []
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cleaned_row = {k: (v if v else None) for k, v in row.items()}
            rows.append(cleaned_row)
    return rows


def _bulk_load_users(client, csv_path):
    """Carga masiva de usuarios desde CSV"""
    print(f"\n[CSV] Cargando usuarios desde: {csv_path}")
    rows = _load_csv_file(csv_path)

    ok = failed = 0
    for i, row in enumerate(rows, start=2):
        try:
            data = {
                "username": row.get("username"),
                "password": row.get("password"),
            }
            if row.get("rol"):
                data["rol"] = row.get("rol")

            print(f"\n[REQUEST] POST /auth/register [L{i}]")
            print("Payload:")
            _print_json(data)

            result = client.register_user(data)
            print("\n[RESPONSE]")
            _print_json(result)
            ok += 1

        except Exception as e:
            print(f"\n[ERROR][L{i}] {e}")
            failed += 1

    print(f"\n[RESUMEN] Usuarios: OK={ok}, Fallidos={failed}")
    return ok, failed


def _bulk_load_patients(client, csv_path):
    """Carga masiva de pacientes desde CSV"""
    print(f"\n[CSV] Cargando pacientes desde: {csv_path}")
    rows = _load_csv_file(csv_path)

    ok = failed = 0
    for i, row in enumerate(rows, start=2):
        try:
            data = {
                "nombre": row.get("nombre"),
            }
            if row.get("telefono"):
                data["telefono"] = row.get("telefono")
            if row.get("estado"):
                data["estado"] = row.get("estado")

            print(f"\n[REQUEST] POST /admin/pacientes [L{i}]")
            print("Payload:")
            _print_json(data)

            result = client.create_patient(data)
            print("\n[RESPONSE]")
            _print_json(result)
            ok += 1

        except Exception as e:
            print(f"\n[ERROR][L{i}] {e}")
            failed += 1

    print(f"\n[RESUMEN] Pacientes: OK={ok}, Fallidos={failed}")
    return ok, failed


def _bulk_load_doctors(client, csv_path):
    """Carga masiva de doctores desde CSV"""
    print(f"\n[CSV] Cargando doctores desde: {csv_path}")
    rows = _load_csv_file(csv_path)

    ok = failed = 0
    for i, row in enumerate(rows, start=2):
        try:
            data = {
                "nombre": row.get("nombre"),
            }
            if row.get("especialidad"):
                data["especialidad"] = row.get("especialidad")
            if row.get("estado"):
                data["estado"] = row.get("estado")

            print(f"\n[REQUEST] POST /admin/doctores [L{i}]")
            print("Payload:")
            _print_json(data)

            result = client.create_doctor(data)
            print("\n[RESPONSE]")
            _print_json(result)
            ok += 1

        except Exception as e:
            print(f"\n[ERROR][L{i}] {e}")
            failed += 1

    print(f"\n[RESUMEN] Doctores: OK={ok}, Fallidos={failed}")
    return ok, failed


def _bulk_load_centers(client, csv_path):
    """Carga masiva de centros desde CSV"""
    print(f"\n[CSV] Cargando centros desde: {csv_path}")
    rows = _load_csv_file(csv_path)

    ok = failed = 0
    for i, row in enumerate(rows, start=2):
        try:
            data = {
                "nombre": row.get("nombre"),
            }
            if row.get("direccion"):
                data["direccion"] = row.get("direccion")
            if row.get("estado"):
                data["estado"] = row.get("estado")

            print(f"\n[REQUEST] POST /admin/centros [L{i}]")
            print("Payload:")
            _print_json(data)

            result = client.create_center(data)
            print("\n[RESPONSE]")
            _print_json(result)
            ok += 1

        except Exception as e:
            print(f"\n[ERROR][L{i}] {e}")
            failed += 1

    print(f"\n[RESUMEN] Centros: OK={ok}, Fallidos={failed}")
    return ok, failed


def _bulk_load_appointments(client, csv_path):
    """Carga masiva de citas desde CSV"""
    print(f"\n[CSV] Cargando citas desde: {csv_path}")
    rows = _load_csv_file(csv_path)

    ok = failed = 0
    for i, row in enumerate(rows, start=2):
        try:
            data = {
                "fecha": row.get("fecha"),
                "motivo": row.get("motivo"),
                "id_paciente": int(row.get("id_paciente")),
                "id_doctor": int(row.get("id_doctor")),
                "id_centro": int(row.get("id_centro")),
            }

            print(f"\n[REQUEST] POST /citas [L{i}]")
            print("Payload:")
            _print_json(data)

            result = client.create_appointment(data)
            print("\n[RESPONSE]")
            _print_json(result)
            ok += 1

        except Exception as e:
            print(f"\n[ERROR][L{i}] {e}")
            failed += 1

    print(f"\n[RESUMEN] Citas: OK={ok}, Fallidos={failed}")
    return ok, failed


def _menu_bulk_load(client):
    """Menú de carga masiva desde CSV"""
    print_section("Carga Masiva desde CSV")

    # Mostrar templates disponibles
    print(f"\n{Colors.INFO}Directorio de templates:{Colors.RESET} {DEFAULT_TEMPLATES_DIR}/")
    print(f"{Colors.DIM}Archivos disponibles:{Colors.RESET}")
    templates_found = []
    if os.path.exists(DEFAULT_TEMPLATES_DIR):
        for fname in sorted(os.listdir(DEFAULT_TEMPLATES_DIR)):
            fpath = os.path.join(DEFAULT_TEMPLATES_DIR, fname)
            if os.path.isfile(fpath) and fname.endswith(".csv"):
                templates_found.append(fname)
                print(f"    {Colors.GREEN}[CSV]{Colors.RESET} {fname}")

    if not templates_found:
        print(f"    {Colors.DIM}  (No se encontraron archivos CSV en templates){Colors.RESET}")

    # Pedir ruta del archivo CSV
    print(f"\n{Colors.BLUE}Ingresa la ruta del archivo CSV (o presiona Enter para ver templates):{Colors.RESET}")
    csv_path = _prompt("Ruta", "")

    # Si no se ingresa ruta, mostrar selección de templates
    if not csv_path:
        print(f"\n{Colors.BLUE}Templates disponibles:{Colors.RESET}")
        templates_map = {}
        for i, fname in enumerate(templates_found, start=1):
            fpath = os.path.join(DEFAULT_TEMPLATES_DIR, fname)
            templates_map[str(i)] = fpath
            print_item(str(i), fname)

        print(f"\n  {Colors.DIM}0) Ingresar ruta personalizada{Colors.RESET}")
        choice = _prompt("Selecciona un template", "0")

        if choice == "0":
            csv_path = _prompt("Ruta del archivo CSV")
        elif choice in templates_map:
            csv_path = templates_map[choice]
        else:
            print_error("Opción inválida.")
            return

    if not os.path.exists(csv_path):
        print_error(f"El archivo no existe: {csv_path}")
        return

    # Seleccionar tipo de carga
    print(f"\n{Colors.BLUE}Tipo de carga:{Colors.RESET}")
    print_item("1", "Usuarios (POST /auth/register)")
    print_item("2", "Pacientes (POST /admin/pacientes)")
    print_item("3", "Doctores (POST /admin/doctores)")
    print_item("4", "Centros (POST /admin/centros)")
    print_item("5", "Citas (POST /citas)")
    print(f"\n  {Colors.DIM}0) Cancelar{Colors.RESET}")

    choice = _prompt("Opción", "1")

    if choice == "0":
        print_warning("Operación cancelada por el usuario.")
        return

    try:
        if choice == "1":
            _bulk_load_users(client, csv_path)
        elif choice == "2":
            _bulk_load_patients(client, csv_path)
        elif choice == "3":
            _bulk_load_doctors(client, csv_path)
        elif choice == "4":
            _bulk_load_centers(client, csv_path)
        elif choice == "5":
            _bulk_load_appointments(client, csv_path)
        else:
            print("Opción inválida.")

    except KeyboardInterrupt:
        print_warning("Carga masiva interrumpida por el usuario (Ctrl+C)")


# ---------- Argument Parser ----------


def parse_args():
    parser = argparse.ArgumentParser(
        description="OdontoCare - Cliente REST Simple",
    )
    parser.add_argument(
        "--user-service",
        default=DEFAULT_USER_SERVICE_URL,
        help=f"URL del servicio de usuarios (default: {DEFAULT_USER_SERVICE_URL})",
    )
    parser.add_argument(
        "--appointment-service",
        default=DEFAULT_APPOINTMENT_SERVICE_URL,
        help=f"URL del servicio de citas (default: {DEFAULT_APPOINTMENT_SERVICE_URL})",
    )
    return parser.parse_args()


# ---------- Main ----------


def main():
    args = parse_args()

    client = RestClient(args.user_service, args.appointment_service)

    # Banner de bienvenida
    print(f"\n{Colors.BLUE + Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(
        f"{Colors.BLUE + Colors.BOLD}│{Colors.RESET}{' ' * 20}OdontoCare - Cliente REST Simple{' ' * 21}{Colors.BLUE + Colors.BOLD}│{Colors.RESET}"
    )
    print(f"{Colors.BLUE + Colors.BOLD}{'=' * 70}{Colors.RESET}\n")

    print(f"{Colors.DIM}  Servicios configurados:{Colors.RESET}")
    print(f"    {Colors.INFO}●{Colors.RESET} User Service:      {args.user_service}")
    print(
        f"    {Colors.INFO}●{Colors.RESET} Appointment Service: {args.appointment_service}"
    )
    print(f"\n{Colors.BLUE + Colors.BOLD}{'=' * 70}{Colors.RESET}\n")

    run_interactive_menu(client)


if __name__ == "__main__":
    main()
