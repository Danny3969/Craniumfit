"""
whatsapp_service.py — Servicio de Notificaciones y OTP por WhatsApp para CraniumFit
==================================================================================
Maneja:
1. Generación y validación de códigos OTP de 6 dígitos con expiración de 15 minutos.
2. Formato de mensajes clínicos para activación de cuentas de Padres y Secretarias.
3. Almacenamiento en 'data/whatsapp_outbox.json' para inspección en tiempo real.
4. Conector listo para WhatsApp Business API (Evolution API / Meta Cloud API / Twilio).
"""

import os
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from database import get_core_connection

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTBOX_FILE = DATA_DIR / "whatsapp_outbox.json"

WHATSAPP_API_URL = os.environ.get("WHATSAPP_API_URL", "")
WHATSAPP_API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN", "")

def generate_otp(length: int = 6) -> str:
    """Genera un código numérico aleatorio de 6 dígitos."""
    return "".join(random.choices("0123456789", k=length))

def create_and_send_activation_otp(
    user_id: str,
    full_name: str,
    cedula: str,
    phone: str,
    role: str = "parent",
    branch_name: str = "Quito - Citimed"
) -> Dict[str, Any]:
    """
    Genera un OTP, lo persiste en la base de datos central y registra el mensaje en el outbox.
    """
    code = generate_otp(6)
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    otp_id = f"otp_{uuid.uuid4().hex[:8]}"

    # Guardar en base de datos
    conn = get_core_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO otp_verifications (id, user_id, phone, cedula, code, purpose, expires_at, is_used)
    VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    """, (otp_id, user_id, phone, cedula, code, "account_activation", expires_at.isoformat()))
    conn.commit()
    conn.close()

    # Redacción del mensaje personalizado según el rol
    if role == "parent":
        message_text = (
            f"👶 *Bienvenido a CraniumFit — {branch_name}*\n\n"
            f"Estimado(a) *{full_name}*:\n"
            f"La recepción ha registrado la ficha clínica de su bebé.\n\n"
            f"Su código de activación personal para la aplicación es:\n"
            f"🔑 *{code}*\n\n"
            f"📌 Ingrese con su número de cédula (*{cedula}*) en la app para definir su contraseña y acceder al historial 3D, evolución CVAI y agendamiento.\n"
            f"⏳ _Este código expira en 15 minutos._"
        )
    elif role == "secretary":
        message_text = (
            f"🏥 *CraniumFit — Activación de Personal Administrativo*\n\n"
            f"Estimada *{full_name}*:\n"
            f"Se ha creado su perfil de Secretaría en la sede *{branch_name}*.\n\n"
            f"Su código de acceso para activación de cuenta es:\n"
            f"🔑 *{code}*\n\n"
            f"📌 Ingrese con su cédula (*{cedula}*) para establecer su clave de ingreso al sistema."
        )
    else:
        message_text = (
            f"🏥 *CraniumFit — Código de Verificación*\n\n"
            f"Estimado(a) *{full_name}*, su código de verificación es:\n"
            f"🔑 *{code}*\n\n"
            f"Cédula: *{cedula}*."
        )

    outbox_entry = {
        "id": otp_id,
        "recipient_name": full_name,
        "phone": phone,
        "cedula": cedula,
        "code": code,
        "role": role,
        "branch": branch_name,
        "message": message_text,
        "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "delivered_simulated"
    }

    _append_to_outbox(outbox_entry)

    print(f"📲 [WhatsApp Outbox] OTP {code} enviado a {phone} ({full_name}) para cédula {cedula}")

    # Conector para API externa si existe configuración
    if WHATSAPP_API_URL and WHATSAPP_API_TOKEN:
        try:
            import urllib.request
            req = urllib.request.Request(
                WHATSAPP_API_URL,
                data=json.dumps({"phone": phone, "message": message_text}).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {WHATSAPP_API_TOKEN}"
                }
            )
            urllib.request.urlopen(req, timeout=5)
            outbox_entry["status"] = "delivered_gateway"
        except Exception as e:
            print(f"⚠️ [WhatsApp Gateway] Error al enviar por API externa: {e}")

    return outbox_entry

def verify_otp_and_consume(cedula: str, code: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Verifica si el código es válido, no expiró y no ha sido usado.
    Si es válido, lo marca como utilizado y retorna el usuario asociado.
    """
    clean_cedula = cedula.strip()
    clean_code = code.strip()

    conn = get_core_connection()
    c = conn.cursor()

    c.execute("""
    SELECT o.id, o.user_id, o.expires_at, o.is_used, u.full_name, u.role, u.default_branch, u.status
    FROM otp_verifications o
    LEFT JOIN global_users u ON o.user_id = u.id
    WHERE o.cedula = ? AND o.code = ? AND o.is_used = 0
    ORDER BY o.created_at DESC
    LIMIT 1
    """, (clean_cedula, clean_code))

    row = c.fetchone()
    if not row:
        conn.close()
        return False, "Código de verificación o número de cédula incorrecto.", None

    otp_id = row["id"]
    user_id = row["user_id"]
    expires_str = row["expires_at"]

    # Verificar expiración
    try:
        expires_dt = datetime.fromisoformat(expires_str)
        if datetime.utcnow() > expires_dt:
            conn.close()
            return False, "El código de verificación ha expirado. Solicite uno nuevo.", None
    except Exception:
        pass

    # Marcar OTP como utilizado
    c.execute("UPDATE otp_verifications SET is_used = 1 WHERE id = ?", (otp_id,))
    conn.commit()

    user_data = {
        "user_id": user_id,
        "full_name": row["full_name"],
        "role": row["role"],
        "default_branch": row["default_branch"],
        "status": row["status"]
    }
    conn.close()
    return True, "Código verificado con éxito.", user_data

def get_recent_outbox_messages(limit: int = 20) -> list:
    """Retorna los últimos mensajes enviados para la simulación visual."""
    if not OUTBOX_FILE.exists():
        return []
    try:
        with open(OUTBOX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data[:limit]
    except Exception:
        return []

def generate_wa_direct_link(phone: str, message: str) -> str:
    """Genera enlace wa.me directo para abrir en WhatsApp Web o App Móvil."""
    import urllib.parse
    clean_phone = "".join(c for c in phone if c.isdigit())
    if clean_phone.startswith("0") and len(clean_phone) == 10:
        clean_phone = "593" + clean_phone[1:]
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{clean_phone}?text={encoded}"

def send_clinical_notification(
    recipient_phone: str,
    recipient_name: str,
    notification_type: str,
    branch_name: str = "Quito - Citimed",
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Despacha notificaciones clínicas automáticas:
    - appointment_reminder: Recordatorio de cita próxima.
    - scan_ready: Resultados de escaneo 3D y CVAI listos.
    - wear_time_alert: Felicitación o alerta de uso de 23h de casco.
    - prescription_ready: Receta médica y órdenes ortésicas emitidas.
    """
    details = details or {}
    baby_name = details.get("baby_name", "su bebé")
    doctor_name = details.get("doctor_name", "Especialista CraniumFit")
    msg_id = f"notif_{uuid.uuid4().hex[:8]}"

    if notification_type == "appointment_reminder":
        apt_date = details.get("date", "próximamente")
        apt_time = details.get("time", "hora acordada")
        apt_type = details.get("type", "Control Clínico")
        message_text = (
            f"📅 *Recordatorio de Cita Médica — CraniumFit {branch_name}*\n\n"
            f"Estimado(a) *{recipient_name}*:\n"
            f"Le recordamos la cita programada para *{baby_name}*:\n\n"
            f"🔹 *Tipo:* {apt_type}\n"
            f"👨‍⚕️ *Doctor:* {doctor_name}\n"
            f"📆 *Fecha:* {apt_date}\n"
            f"⏰ *Hora:* {apt_time}\n"
            f"📍 *Lugar:* Consultorio CraniumFit ({branch_name})\n\n"
            f"Por favor llegar con 10 minutos de anticipación. Si necesita reprogramar, responda a este mensaje."
        )

    elif notification_type == "scan_ready":
        cvai = details.get("cvai", 0.0)
        reduction = details.get("reduction", "")
        message_text = (
            f"🔬 *Resultados de Escaneo 3D Listos — CraniumFit*\n\n"
            f"Estimado(a) *{recipient_name}*:\n"
            f"El nuevo escaneo 3D de *{baby_name}* ha sido procesado con éxito por el equipo médico.\n\n"
            f"📊 *Índice CVAI Actual:* {cvai}%\n"
            f"📈 *Evolución:* {reduction}\n"
            f"👨‍⚕️ *Evaluado por:* {doctor_name}\n\n"
            f"Ya puede visualizar la reconstrucción 3D comparativa ('Antes vs. Después') directamente desde su portal de padres en la app."
        )

    elif notification_type == "wear_time_alert":
        hours = details.get("hours", 23.0)
        message_text = (
            f"⏱️ *Monitoreo de Adherencia 23h — CraniumFit*\n\n"
            f"Estimado(a) *{recipient_name}*:\n"
            f"¡Felicitaciones! Se ha registrado un tiempo de uso de *{hours} horas* hoy para el casco de *{baby_name}*.\n\n"
            f"🎯 Cumplir la meta de 23 horas diarias asegura el máximo potencial de remodelación de la bóveda craneal.\n"
            f"💪 ¡Excelente compromiso con el tratamiento!"
        )

    elif notification_type == "prescription_ready":
        rx_date = details.get("date", "hoy")
        message_text = (
            f"📋 *Nueva Receta & Plan de Cuidados — CraniumFit*\n\n"
            f"Estimado(a) *{recipient_name}*:\n"
            f"El *{doctor_name}* ha emitido la receta médica y pautas de cuidado para *{baby_name}* ({rx_date}).\n\n"
            f"Puede consultar la receta completa con membrete oficial y descargarlo en PDF ingresando a su portal CraniumFit."
        )

    else:
        custom_body = details.get("body", "Información importante de su tratamiento.")
        message_text = (
            f"🏥 *CraniumFit — Notificación Clínica ({branch_name})*\n\n"
            f"Estimado(a) *{recipient_name}*:\n"
            f"{custom_body}"
        )

    wa_link = generate_wa_direct_link(recipient_phone, message_text)

    outbox_entry = {
        "id": msg_id,
        "recipient_name": recipient_name,
        "phone": recipient_phone,
        "notification_type": notification_type,
        "branch": branch_name,
        "message": message_text,
        "wa_link": wa_link,
        "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "delivered_simulated"
    }

    _append_to_outbox(outbox_entry)
    print(f"📲 [WhatsApp Outbox] Notificación '{notification_type}' enviada a {recipient_phone} ({recipient_name})")

    return outbox_entry

def _append_to_outbox(entry: Dict[str, Any]):
    messages = []
    if OUTBOX_FILE.exists():
        try:
            with open(OUTBOX_FILE, "r", encoding="utf-8") as f:
                messages = json.load(f)
        except Exception:
            messages = []
    messages.insert(0, entry)
    messages = messages[:50]
    with open(OUTBOX_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
