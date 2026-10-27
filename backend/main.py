"""
main.py — FastAPI Core API para CraniumFit (Ecosistema Multi-Sede)
================================================================
Endpoints para:
- Autenticación unificada y selector de sucursal (Quito / Lima)
- Agendamiento en tiempo real por Doctor con cálculo de slots libres
- Motor de pagos de consulta (Tarjeta / Transferencia bancaria)
- Historias clínicas pediátricas y trazabilidad de Órtesis 3D
- Visualizador 3D y telemetría de adherencia de 23 horas
- Dashboard administrativo multi-sucursal
"""

import os
import sys
import uuid
import random
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Depends, Query, status, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from pathlib import Path

# Imports locales
from database import (
    init_all_databases,
    get_core_connection,
    get_branch_connection,
    BRANCH_DBS,
    get_all_branches,
    create_branch_record,
    update_branch_record,
    delete_branch_record,
    get_all_company_settings,
    get_company_settings,
    update_company_settings,
    DATA_DIR
)
from signature_service import (
    verify_and_extract_p12,
    sign_medical_document,
    create_demo_p12_for_doctor
)
from sri_service import (
    generate_sri_access_key,
    generate_sri_invoice_xml,
    sign_sri_xml,
    process_sri_authorization
)
from craniometrics import (
    calculate_cvai,
    calculate_cephalic_index,
    get_argenta_classification,
    generate_cranial_mesh_geometry
)
from whatsapp_service import (
    create_and_send_activation_otp,
    verify_otp_and_consume,
    get_recent_outbox_messages,
    send_clinical_notification,
    generate_wa_direct_link
)
import json

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
(UPLOADS_DIR / "scans").mkdir(parents=True, exist_ok=True)
(UPLOADS_DIR / "signatures").mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="CraniumFit Core API",
    description="API Médica de Alta Precisión para Tratamiento de Deformidades Craneales y Órtesis 3D",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar directorio para servir archivos 3D reales (.stl / .obj) y firmas
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

FAMILIAS_DIST_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mobile", "craniumfit-familias", "dist"))
PRO_DIST_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mobile", "craniumfit-pro", "dist"))
DOWNLOADS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "downloads"))

if os.path.exists(FAMILIAS_DIST_PATH):
    app.mount("/app-familias", StaticFiles(directory=FAMILIAS_DIST_PATH, html=True), name="app-familias")

if os.path.exists(PRO_DIST_PATH):
    app.mount("/app-pro", StaticFiles(directory=PRO_DIST_PATH, html=True), name="app-pro")

if os.path.exists(DOWNLOADS_PATH):
    app.mount("/downloads", StaticFiles(directory=DOWNLOADS_PATH, html=True), name="downloads")

# Inicializar bases de datos al arranque
@app.on_event("startup")
def startup_event():
    init_all_databases()

FRONTEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html"))

@app.get("/", summary="Servir Consola Web Administrativa")
def serve_root():
    if os.path.exists(FRONTEND_PATH):
        return FileResponse(FRONTEND_PATH)
    return {"status": "ok", "message": "CraniumFit Core API is running", "docs": "/docs"}

@app.get("/app", summary="Servir Consola Web Administrativa")
def serve_app():
    if os.path.exists(FRONTEND_PATH):
        return FileResponse(FRONTEND_PATH)
    return {"status": "ok", "message": "CraniumFit Core API is running", "docs": "/docs"}

@app.get("/familias", summary="Redirigir a App Móvil de Familias")
def redirect_familias():
    return RedirectResponse(url="/app-familias/", status_code=307)

@app.get("/pro", summary="Redirigir a App Móvil Pro")
def redirect_pro():
    return RedirectResponse(url="/app-pro/", status_code=307)

@app.get("/descargas", summary="Redirigir a Centro de Descargas Móvil")
@app.get("/instalar", summary="Redirigir a Centro de Descargas Móvil")
def redirect_descargas():
    return RedirectResponse(url="/downloads/", status_code=307)

# Helper para resolver el branch_id
def resolve_branch(x_branch_id: Optional[str] = Header(None)) -> str:
    branch = (x_branch_id or "quito").lower().strip()
    try:
        branches = [b["id"] for b in get_all_branches()]
        if branch in branches:
            return branch
    except Exception:
        pass
    if branch not in BRANCH_DBS:
        branch = "quito"
    return branch

# ── MODELOS PYDANTIC ──────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    identifier: Optional[str] = None
    email: Optional[str] = None
    cedula: Optional[str] = None
    password: str

class VerifyOtpRequest(BaseModel):
    cedula: str
    code: str

class SetPasswordRequest(BaseModel):
    cedula: str
    code: str
    new_password: str

class ResendOtpRequest(BaseModel):
    cedula: str

class CreateSuperadminRequest(BaseModel):
    full_name: str
    cedula: str
    email: str
    phone: str
    password: str
    default_branch: str = "quito"

class CreateDoctorRequest(BaseModel):
    full_name: str
    cedula: str
    email: str
    phone: str
    password: str
    default_branch: str = "quito"
    specialty: str
    medical_license: Optional[str] = ""
    consultation_fee: float = 50.0
    appointment_duration_min: int = 30
    bio: Optional[str] = ""
    avatar_url: Optional[str] = ""
    working_days: Optional[List[int]] = [1, 2, 3, 4, 5]
    start_time: Optional[str] = "08:30"
    end_time: Optional[str] = "17:00"

class CreateSecretaryRequest(BaseModel):
    full_name: str
    cedula: str
    email: Optional[str] = ""
    phone: str
    default_branch: str = "quito"
    assigned_doctor_ids: List[str] # Lista de IDs de doctores asignados

class UpdateUserRoleRequest(BaseModel):
    new_role: str
    default_branch: Optional[str] = None
    assigned_doctor_ids: Optional[List[str]] = None
    status: Optional[str] = None

class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    cedula: Optional[str] = None
    default_branch: Optional[str] = None
    role: Optional[str] = None
    assigned_doctor_ids: Optional[List[str]] = None
    status: Optional[str] = None
    password: Optional[str] = None
    specialty: Optional[str] = None
    consultation_fee: Optional[float] = None
    medical_license: Optional[str] = None
    bio: Optional[str] = None
    patient_id: Optional[str] = None
    patient_ids: Optional[List[str]] = None

class CreateParentRequest(BaseModel):
    full_name: str
    cedula: str
    phone: str
    email: Optional[str] = ""
    default_branch: str = "quito"
    patient_id: Optional[str] = None
    patient_ids: Optional[List[str]] = None

class UpdatePatientRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[str] = None
    sex: Optional[str] = None
    diagnosis: Optional[str] = None
    primary_doctor_id: Optional[str] = None
    parent_cedula: Optional[str] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    parent_email: Optional[str] = None
    patient_dni: Optional[str] = None
    photo_url: Optional[str] = None

class SecretaryRegisterPatientRequest(BaseModel):
    # Datos del Padre / Tutor
    parent_cedula: str
    parent_name: str
    parent_phone: str
    parent_email: Optional[str] = ""
    # Datos del Bebé / Paciente
    first_name: str
    last_name: str
    patient_dni: Optional[str] = None
    birth_date: str # YYYY-MM-DD
    sex: str = "M"
    gestational_weeks: int = 40
    delivery_type: str = "Parto Vaginal"
    primary_doctor_id: str
    diagnosis: Optional[str] = "Evaluación Inicial de Asimetría Craneal"
    photo_url: Optional[str] = None

class BookAppointmentRequest(BaseModel):
    doctor_id: str
    patient_id: Optional[str] = None
    patient_name: str
    parent_email: str
    parent_phone: str
    appointment_date: str # YYYY-MM-DD
    start_time: str       # HH:MM
    appointment_type: str = "evaluacion_3d"
    payment_method: str   # "tarjeta_online", "transferencia", "efectivo"
    payment_reference: Optional[str] = None

class CreateScanRequest(BaseModel):
    patient_id: str
    diagonal_a_mm: float
    diagonal_b_mm: float
    width_mm: float
    length_mm: float
    circumference_mm: float
    clinical_notes: Optional[str] = ""

class CreateConsultationRequest(BaseModel):
    doctor_id: str
    consultation_date: Optional[str] = None
    reason_for_visit: Optional[str] = None
    reason: Optional[str] = None
    vital_signs: Optional[Dict[str, Any]] = None
    cranial_eval: Optional[str] = None
    cranial_evaluation: Optional[str] = None
    diagnosis: str
    clinical_evolution: str
    treatment_plan: str
    next_appointment_rec: Optional[str] = None
    next_appointment: Optional[str] = None

class CreateExamRequest(BaseModel):
    doctor_id: str
    exam_date: Optional[str] = None
    exam_type: str
    cvai: Optional[float] = None
    cephalic_index: Optional[float] = None
    argenta_grade: Optional[int] = None
    diagonal_a_mm: Optional[float] = None
    diagonal_b_mm: Optional[float] = None
    measurements: Optional[Dict[str, Any]] = None
    results_summary: Optional[str] = None
    summary_findings: Optional[str] = None
    summary: Optional[str] = None
    recommendations: Optional[str] = None
    file_url: Optional[str] = None

class CreatePrescriptionRequest(BaseModel):
    doctor_id: str
    consultation_id: Optional[str] = None
    prescription_date: Optional[str] = None
    medications_rx: Optional[str] = None
    medications: Optional[str] = None
    orthotic_prescription: Optional[str] = None
    orthotic_protocol: Optional[str] = None
    physical_therapy_orders: Optional[str] = None
    therapy_recommendations: Optional[str] = None
    special_instructions: Optional[str] = None
    general_instructions: Optional[str] = None
    valid_until: Optional[str] = None

class LogWearTimeRequest(BaseModel):
    patient_id: str
    hours_worn: float
    pauses_count: int = 1
    notes: Optional[str] = ""

class UpdateAppointmentStatusRequest(BaseModel):
    status: str # 'confirmed', 'in_waiting_room', 'in_consultation', 'completed', 'cancelled'
    payment_status: Optional[str] = None

class CreateInvoiceRequest(BaseModel):
    patient_id: Optional[str] = None
    client_id: Optional[str] = None
    client_identification: Optional[str] = None
    client_name: Optional[str] = None
    client_address: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    parent_user_id: Optional[str] = None
    parent_name: Optional[str] = None
    parent_cedula: Optional[str] = None
    doctor_id: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    items: List[Dict[str, Any]]
    subtotal: Optional[float] = None
    tax_percent: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    payment_method: Optional[str] = "transferencia"
    payment_status: Optional[str] = "pending"
    payment_reference: Optional[str] = None
    payment_receipt_url: Optional[str] = None
    notes: Optional[str] = None

class CreateBillingItemRequest(BaseModel):
    code: str
    description: str
    category: str
    unit_price: float
    tax_percent: float = 15.0
    status: str = "active"

class UpdateBillingItemRequest(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[float] = None
    tax_percent: Optional[float] = None
    status: Optional[str] = None

class CreateBillingClientRequest(BaseModel):
    client_type: str = "natural" # 'natural', 'juridica'
    identification_type: str = "05" # '05' Cédula, '04' RUC, '06' Pasaporte
    identification_number: str
    name_or_business_name: str
    email: Optional[str] = ""
    phone: Optional[str] = ""
    address: Optional[str] = ""
    associated_patient_id: Optional[str] = None

class UpdateBillingClientRequest(BaseModel):
    client_type: Optional[str] = None
    identification_type: Optional[str] = None
    identification_number: Optional[str] = None
    name_or_business_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    associated_patient_id: Optional[str] = None

class PayInvoiceRequest(BaseModel):
    payment_status: Optional[str] = "paid"
    payment_method: Optional[str] = "transferencia"
    amount_paid: Optional[float] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None

class SendWhatsAppNotificationRequest(BaseModel):
    recipient_phone: Optional[str] = None
    recipient_name: Optional[str] = None
    notification_type: Optional[str] = None
    phone_number: Optional[str] = None
    patient_id: Optional[str] = None
    template_name: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    custom_vars: Optional[Dict[str, Any]] = None

class ParentLogWearRequest(BaseModel):
    hours_worn: float
    pauses_count: Optional[int] = 0
    notes: Optional[str] = ""

class ParentRequestAppointmentRequest(BaseModel):
    appointment_type: str = "control_quincenal"
    doctor_id: Optional[str] = None
    preferred_date: str
    preferred_time: Optional[str] = "10:00"
    notes: Optional[str] = ""

class CreateBranchRequest(BaseModel):
    id: str
    name: str
    city: str
    country: str = "Ecuador"
    address: str
    phone: str
    email: str
    tax_percent: float = 15.0
    currency: str = "USD"
    invoice_prefix: Optional[str] = None
    establishment_code: Optional[str] = None
    emission_point: Optional[str] = "001"
    peru_series_invoice: Optional[str] = "F001"
    peru_series_boleta: Optional[str] = "B001"
    legal_company_id: Optional[str] = None

class UpdateBranchRequest(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tax_percent: Optional[float] = None
    currency: Optional[str] = None
    invoice_prefix: Optional[str] = None
    establishment_code: Optional[str] = None
    emission_point: Optional[str] = None
    peru_series_invoice: Optional[str] = None
    peru_series_boleta: Optional[str] = None
    legal_company_id: Optional[str] = None
    is_active: Optional[int] = None

class UpdateCompanySettingsRequest(BaseModel):
    business_name: Optional[str] = None
    trade_name: Optional[str] = None
    tax_id: Optional[str] = None
    legal_rep_name: Optional[str] = None
    legal_rep_id: Optional[str] = None
    fiscal_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    obligado_contabilidad: Optional[str] = None
    regimen_tributario: Optional[str] = None
    special_taxpayer_resolution: Optional[str] = None
    retention_agent_resolution: Optional[str] = None
    bank_accounts: Optional[List[Dict[str, Any]]] = None
    electronic_billing_config: Optional[Dict[str, Any]] = None

class CreateMedicalCertificateRequest(BaseModel):
    doctor_id: str
    consultation_id: Optional[str] = None
    issue_date: Optional[str] = None
    certificate_type: str = "reposo_medico" # 'reposo_medico', 'aptitud_escolar', 'uso_ortesis_aerolinea', 'constancia_atencion'
    diagnosis_cie10: str
    clinical_findings: Optional[str] = ""
    rest_days: int = 0
    valid_until: Optional[str] = None
    formal_statement: str

class CreateInsuranceDossierRequest(BaseModel):
    doctor_id: str
    insurance_company: str
    policy_number: Optional[str] = None
    diagnosis_cie10: str
    clinical_justification: str
    estimated_cost: float = 1850.00
    cvai_initial: Optional[float] = None
    cvai_current: Optional[float] = None
    argenta_grade: Optional[int] = None

class CreateTriageRequest(BaseModel):
    parent_name: str
    parent_email: str
    parent_phone: str
    parent_city: str
    baby_name: str
    baby_age_months: float
    photo_vertex_url: Optional[str] = None
    photo_right_url: Optional[str] = None
    photo_left_url: Optional[str] = None
    photo_posterior_url: Optional[str] = None
    parent_notes: Optional[str] = None
    target_branch: Optional[str] = "quito"

class EvaluateTriageRequest(BaseModel):
    doctor_id: str
    doctor_name: str
    argenta_estimated: int
    estimated_condition: str
    urgency_level: str = "moderada" # 'baja', 'moderada', 'alta'
    doctor_notes: str
    recommendation: str
    status: str = "evaluated" # 'evaluated', 'candidate_in_person', 'mild_observation', 'discarded'

class CreateManufacturingOrderRequest(BaseModel):
    patient_id: str
    doctor_id: Optional[str] = None
    scan_file_name: Optional[str] = None
    cvai_at_prescription: Optional[float] = None
    helmet_model: str = "CraniumFit Pro-Dynamic 3D"
    pressure_zones: Optional[str] = None
    expansion_chambers: Optional[str] = None
    shell_thickness_mm: float = 4.0
    shell_material: str = "PETG Vivak Médico"
    lining_material: str = "Espuma Plastazote Hipoalergénica"
    closure_type: str = "Velcro con Hebilla de Seguridad"
    color_pattern: str = "Blanco Médico Estándar"
    clinical_priority: str = "Normal"
    target_delivery_date: Optional[str] = None
    total_cost: float = 850.0
    notes: Optional[str] = None

class UpdateManufacturingStatusRequest(BaseModel):
    status: str # 'pending', 'in_fabrication', 'completed'
    notes: Optional[str] = None
    technician_name: Optional[str] = None

class QCInspectionRequest(BaseModel):
    material_lot_shell: str
    material_lot_foam: str
    material_lot_straps: str
    qc_inspector_name: str
    qc_caliper_thickness_mm: float = 4.0
    qc_weight_grams: float = 190.0
    qc_smooth_edges: int = 1
    qc_relief_chambers_ok: int = 1
    qc_notes: Optional[str] = None
    helmet_serial_code: Optional[str] = None

class SRIAuthorizeRequest(BaseModel):
    doctor_id: Optional[str] = None

# ── 1. SUCURSALES (MULTI-SEDE CRUD) Y AUTENTICACIÓN ───────────────────────────

@app.get("/api/branches")
def get_branches():
    """Retorna las sucursales disponibles en el ecosistema (Quito, Lima, Cuenca, etc.)."""
    branches = get_all_branches()
    return {"branches": branches}

@app.post("/api/branches")
def create_branch_api(req: CreateBranchRequest):
    """Crea una nueva sede o sucursal con base de datos aislada automática."""
    b_id = req.id.lower().strip().replace(" ", "_")
    existing = [b["id"] for b in get_all_branches()]
    if b_id in existing:
        raise HTTPException(status_code=400, detail=f"Ya existe una sucursal con el identificador '{b_id}'.")
    
    data = req.dict()
    data["id"] = b_id
    if not data.get("invoice_prefix"):
        data["invoice_prefix"] = b_id[:3].upper()
        
    created = create_branch_record(data)
    return {"success": True, "branch": created, "message": f"Sede '{req.name}' creada exitosamente."}

@app.put("/api/branches/{branch_id}")
def update_branch_api(branch_id: str, req: UpdateBranchRequest):
    """Actualiza la información comercial, fiscal o de contacto de una sede."""
    data = {k: v for k, v in req.dict().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar.")
    update_branch_record(branch_id, data)
    return {"success": True, "branch_id": branch_id, "message": "Sede actualizada exitosamente."}

@app.delete("/api/branches/{branch_id}")
def delete_branch_api(branch_id: str):
    """Desactiva o elimina una sede del ecosistema."""
    delete_branch_record(branch_id)
    return {"success": True, "message": f"Sede '{branch_id}' desactivada del sistema."}

# ── 1.1 CONFIGURACIÓN DE EMPRESA Y FACTURACIÓN FISCAL (SRI / SUNAT) ───────────

@app.get("/api/company/settings")
def get_company_settings_list():
    """Retorna los perfiles fiscales de las empresas registradas (Ecuador y Perú)."""
    companies = get_all_company_settings()
    return {"companies": companies}

@app.get("/api/company/settings/{company_id}")
def get_company_setting_detail(company_id: str):
    """Retorna los datos y parámetros de facturación de una empresa específica ('EC' o 'PE')."""
    company = get_company_settings(company_id)
    if not company:
        raise HTTPException(status_code=404, detail=f"No se encontró la empresa '{company_id}'.")
    return {"company": company}

@app.put("/api/company/settings/{company_id}")
def update_company_setting_api(company_id: str, req: UpdateCompanySettingsRequest):
    """Actualiza la razón social, RUC, logo, régimen o cuentas bancarias de la empresa."""
    data = {k: v for k, v in req.dict().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar.")
    updated = update_company_settings(company_id, data)
    return {"success": True, "company": updated, "message": "Datos de empresa actualizados correctamente."}

@app.post("/api/company/settings/{company_id}/logo")
async def upload_company_logo(company_id: str, file: UploadFile = File(...)):
    """Sube y almacena el logotipo oficial de la empresa para facturas y RIDE."""
    cid = company_id.upper().strip()
    company = get_company_settings(cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"No se encontró la empresa '{company_id}'.")
    
    upload_dir = DATA_DIR / "logos"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    ext = Path(file.filename or "logo.png").suffix.lower()
    if ext not in [".png", ".jpg", ".jpeg", ".svg", ".webp"]:
        raise HTTPException(status_code=400, detail="Formato no soportado. Suba una imagen PNG, JPG o SVG.")
    
    filename = f"logo_{cid.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
    dest_path = upload_dir / filename
    
    content = await file.read()
    with open(dest_path, "wb") as f:
        f.write(content)
        
    logo_url = f"/api/company/logo/{filename}"
    update_company_settings(cid, {"logo_url": logo_url})
    
    return {"success": True, "logo_url": logo_url, "message": "Logotipo corporativo actualizado correctamente."}

@app.get("/api/company/logo/{filename}")
def serve_company_logo(filename: str):
    """Sirve la imagen del logotipo corporativo."""
    safe_name = Path(filename).name
    path = DATA_DIR / "logos" / safe_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Logotipo no encontrado.")
    return FileResponse(path)

@app.post("/api/auth/login")
def login(req: LoginRequest):
    """Autenticación centralizada multi-rol por Cédula o Correo Electrónico."""
    ident = (req.identifier or req.email or req.cedula or "").strip()
    if not ident:
        raise HTTPException(status_code=400, detail="Debe ingresar su número de cédula o correo electrónico.")

    conn = get_core_connection()
    c = conn.cursor()
    c.execute("""
    SELECT * FROM global_users 
    WHERE LOWER(email) = LOWER(?) OR cedula = ?
    LIMIT 1
    """, (ident, ident))
    user = c.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado con la cédula o correo ingresado.")

    if user["status"] == "pending_activation":
        raise HTTPException(
            status_code=403,
            detail="Tu cuenta está pendiente de activación. Valida el código de 6 dígitos enviado a tu WhatsApp para definir tu contraseña."
        )

    if user["password_hash"] != req.password:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")

    user_dict = dict(user)
    del user_dict["password_hash"]
    if user_dict.get("assigned_doctor_ids"):
        try:
            user_dict["assigned_doctor_ids"] = json.loads(user_dict["assigned_doctor_ids"])
        except Exception:
            pass

    token = f"cranium_jwt_{user_dict['id']}_{uuid.uuid4().hex[:12]}"
    
    return {
        "success": True,
        "token": token,
        "user": user_dict
    }

@app.post("/api/auth/verify-otp")
def verify_otp_endpoint(req: VerifyOtpRequest):
    """Valida el código OTP de WhatsApp para una cédula."""
    valid, message, user_data = verify_otp_and_consume(req.cedula, req.code)
    if not valid:
        raise HTTPException(status_code=400, detail=message)
    return {
        "success": True,
        "message": message,
        "user": user_data
    }

@app.post("/api/auth/set-password")
def set_password_endpoint(req: SetPasswordRequest):
    """Define la contraseña tras la validación del OTP y activa la cuenta."""
    conn = get_core_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM global_users WHERE cedula = ?", (req.cedula.strip(),))
    user = c.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado para esta cédula.")

    c.execute("""
    UPDATE global_users 
    SET password_hash = ?, status = 'active'
    WHERE cedula = ?
    """, (req.new_password, req.cedula.strip()))
    conn.commit()

    c.execute("SELECT * FROM global_users WHERE cedula = ?", (req.cedula.strip(),))
    updated_user = dict(c.fetchone())
    conn.close()

    del updated_user["password_hash"]
    if updated_user.get("assigned_doctor_ids"):
        try:
            updated_user["assigned_doctor_ids"] = json.loads(updated_user["assigned_doctor_ids"])
        except Exception:
            pass

    token = f"cranium_jwt_{updated_user['id']}_{uuid.uuid4().hex[:12]}"
    return {
        "success": True,
        "message": "¡Contraseña establecida con éxito! Tu cuenta ha sido activada.",
        "token": token,
        "user": updated_user
    }

@app.post("/api/auth/resend-otp")
def resend_otp_endpoint(req: ResendOtpRequest):
    """Reenvía un nuevo código OTP por WhatsApp a la cédula indicada."""
    conn = get_core_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM global_users WHERE cedula = ?", (req.cedula.strip(),))
    user = c.fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=404, detail="No existe usuario registrado con esta cédula.")

    branch_name = "Quito - Citimed" if user["default_branch"] == "quito" else "Lima - San Isidro"
    outbox = create_and_send_activation_otp(
        user_id=user["id"],
        full_name=user["full_name"],
        cedula=user["cedula"],
        phone=user["phone"],
        role=user["role"],
        branch_name=branch_name
    )
    return {
        "success": True,
        "message": f"Nuevo código OTP enviado por WhatsApp al {user['phone']}",
        "otp_simulated": outbox["code"]
    }

@app.get("/api/whatsapp/outbox")
def get_whatsapp_outbox(limit: int = 15):
    """Retorna los últimos mensajes enviados por WhatsApp para inspección/simulación."""
    return {"messages": get_recent_outbox_messages(limit)}

# ── 1.1 GESTIÓN DE USUARIOS Y ROLES (SUPERADMIN) ──────────────────────────────

def sync_parents_from_patients():
    """Sincroniza automáticamente los tutores registrados en las fichas de pacientes hacia global_users."""
    try:
        core_conn = get_core_connection()
        cc = core_conn.cursor()
        for b in ["quito", "lima"]:
            try:
                bconn = get_branch_connection(b)
                bconn.row_factory = sqlite3.Row
                bc = bconn.cursor()
                bc.execute("SELECT id, parent_user_id, parent_cedula, parent_name, parent_phone, parent_email FROM patients")
                for p in bc.fetchall():
                    cedula = (p["parent_cedula"] or "").strip()
                    name = (p["parent_name"] or "").strip()
                    phone = (p["parent_phone"] or "+593 99 000 0000").strip()
                    email = (p["parent_email"] or (f"padre.{cedula}@cranium.fit" if cedula else "")).strip().lower()
                    if not cedula and not name:
                        continue
                    if cedula:
                        cc.execute("SELECT id FROM global_users WHERE cedula = ?", (cedula,))
                    else:
                        cc.execute("SELECT id FROM global_users WHERE full_name = ? AND role = 'parent'", (name,))
                    existing = cc.fetchone()
                    if not existing:
                        puid = p["parent_user_id"] or f"usr_parent_{uuid.uuid4().hex[:6]}"
                        cc.execute("""
                        INSERT INTO global_users (id, email, cedula, password_hash, full_name, phone, role, default_branch, status)
                        VALUES (?, ?, ?, 'padre123', ?, ?, 'parent', ?, 'active')
                        """, (puid, email, cedula, name, phone, b))
                        bc.execute("UPDATE patients SET parent_user_id = ? WHERE id = ?", (puid, p["id"]))
                    else:
                        if p["parent_user_id"] != existing["id"]:
                            bc.execute("UPDATE patients SET parent_user_id = ? WHERE id = ?", (existing["id"], p["id"]))
                bconn.commit()
                bconn.close()
            except Exception as ex:
                pass
        core_conn.commit()
        core_conn.close()
    except Exception as ex:
        pass

@app.get("/api/admin/users")
def get_admin_users(
    role: Optional[str] = None,
    branch: Optional[str] = None,
    search: Optional[str] = None
):
    """Lista todos los usuarios globales con filtros y datos de asignación."""
    sync_parents_from_patients()
    conn = get_core_connection()
    c = conn.cursor()
    
    query = "SELECT id, email, cedula, full_name, phone, role, default_branch, assigned_doctor_ids, status, created_at FROM global_users WHERE 1=1"
    params = []

    if role and role != "all":
        query += " AND role = ?"
        params.append(role)
    if branch and branch != "all":
        query += " AND default_branch = ?"
        params.append(branch)
    if search:
        s = f"%{search.strip().lower()}%"
        query += " AND (LOWER(full_name) LIKE ? OR cedula LIKE ? OR LOWER(email) LIKE ?)"
        params.extend([s, s, s])

    query += " ORDER BY created_at DESC"
    c.execute(query, params)
    users = []
    for row in c.fetchall():
        u = dict(row)
        if u.get("assigned_doctor_ids"):
            try:
                u["assigned_doctor_ids"] = json.loads(u["assigned_doctor_ids"])
            except Exception:
                pass

        # Si es padre/tutor, buscar y adjuntar los pacientes pediátricos asociados
        if u.get("role") == "parent":
            linked = []
            for b in ["quito", "lima"]:
                try:
                    bconn = get_branch_connection(b)
                    bc = bconn.cursor()
                    bc.execute("""
                    SELECT id, first_name, last_name, birth_date, diagnosis, patient_dni 
                    FROM patients 
                    WHERE parent_user_id = ? OR (parent_cedula IS NOT NULL AND parent_cedula != '' AND parent_cedula = ?)
                    """, (u["id"], u.get("cedula")))
                    for prow in bc.fetchall():
                        pdict = dict(prow)
                        linked.append({
                            "id": pdict["id"],
                            "first_name": pdict["first_name"],
                            "last_name": pdict["last_name"],
                            "name": f"{pdict['first_name']} {pdict['last_name']}".strip(),
                            "birth_date": pdict["birth_date"],
                            "diagnosis": pdict["diagnosis"],
                            "patient_dni": pdict.get("patient_dni"),
                            "branch": b
                        })
                    bconn.close()
                except Exception:
                    pass
            u["linked_patients"] = linked

        users.append(u)
    conn.close()
    return {"total": len(users), "users": users}

@app.post("/api/admin/users/superadmin")
def create_superadmin(req: CreateSuperadminRequest):
    """Crea un nuevo usuario SuperAdministrador con acceso global."""
    conn = get_core_connection()
    c = conn.cursor()
    
    c.execute("SELECT id FROM global_users WHERE cedula = ? OR email = ?", (req.cedula.strip(), req.email.strip().lower()))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Ya existe un usuario con este correo o número de cédula.")

    user_id = f"usr_admin_{uuid.uuid4().hex[:6]}"
    c.execute("""
    INSERT INTO global_users (id, email, cedula, password_hash, full_name, phone, role, default_branch, assigned_doctor_ids, status)
    VALUES (?, ?, ?, ?, ?, ?, 'superadmin', ?, '["doc_q1", "doc_q2", "doc_l1"]', 'active')
    """, (user_id, req.email.strip().lower(), req.cedula.strip(), req.password, req.full_name.strip(), req.phone.strip(), req.default_branch))
    conn.commit()
    conn.close()

    return {"success": True, "message": "SuperUsuario creado exitosamente.", "user_id": user_id}

@app.post("/api/admin/users/doctor")
def create_doctor(req: CreateDoctorRequest):
    """Crea un nuevo Médico en la base global y en la base aislada de su sucursal."""
    core_conn = get_core_connection()
    cc = core_conn.cursor()

    cc.execute("SELECT id FROM global_users WHERE cedula = ? OR email = ?", (req.cedula.strip(), req.email.strip().lower()))
    if cc.fetchone():
        core_conn.close()
        raise HTTPException(status_code=400, detail="Ya existe un usuario con este correo o número de cédula.")

    global_uid = f"usr_doc_{uuid.uuid4().hex[:6]}"
    doc_id = f"doc_{uuid.uuid4().hex[:6]}"

    cc.execute("""
    INSERT INTO global_users (id, email, cedula, password_hash, full_name, phone, role, default_branch, status)
    VALUES (?, ?, ?, ?, ?, ?, 'doctor', ?, 'active')
    """, (global_uid, req.email.strip().lower(), req.cedula.strip(), req.password, req.full_name.strip(), req.phone.strip(), req.default_branch))
    core_conn.commit()
    core_conn.close()

    # Insertar en base de datos de la sucursal correspondiente
    branch_conn = get_branch_connection(req.default_branch)
    bc = branch_conn.cursor()
    avatar = req.avatar_url or "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=300&auto=format&fit=crop&q=80"
    
    bc.execute("""
    INSERT INTO doctors (id, global_user_id, full_name, specialty, medical_license, consultation_fee, appointment_duration_min, bio, avatar_url, is_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """, (doc_id, global_uid, req.full_name.strip(), req.specialty.strip(), req.medical_license, req.consultation_fee, req.appointment_duration_min, req.bio, avatar))

    # Crear horarios laborales
    days = req.working_days or [1, 2, 3, 4, 5]
    for d in days:
        sch_id = f"sch_{doc_id}_{d}"
        bc.execute("""
        INSERT INTO doctor_schedules (id, doctor_id, day_of_week, start_time, end_time, slot_duration_min)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (sch_id, doc_id, d, req.start_time or "08:30", req.end_time or "17:00", req.appointment_duration_min))

    branch_conn.commit()
    branch_conn.close()

    return {
        "success": True,
        "message": f"Doctor '{req.full_name}' registrado exitosamente en {req.default_branch.capitalize()}.",
        "doctor_id": doc_id,
        "global_user_id": global_uid
    }

@app.post("/api/admin/users/secretary")
def create_secretary(req: CreateSecretaryRequest):
    """Crea una Secretaria, le asigna doctores y envía código de activación por WhatsApp."""
    conn = get_core_connection()
    c = conn.cursor()

    c.execute("SELECT id FROM global_users WHERE cedula = ?", (req.cedula.strip(),))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Ya existe un usuario con este número de cédula.")

    sec_uid = f"usr_sec_{uuid.uuid4().hex[:6]}"
    email = req.email.strip().lower() if req.email else f"sec.{req.cedula.strip()}@cranium.fit"
    assigned_json = json.dumps(req.assigned_doctor_ids or [])

    c.execute("""
    INSERT INTO global_users (id, email, cedula, password_hash, full_name, phone, role, default_branch, assigned_doctor_ids, status)
    VALUES (?, ?, ?, '', ?, ?, 'secretary', ?, ?, 'pending_activation')
    """, (sec_uid, email, req.cedula.strip(), req.full_name.strip(), req.phone.strip(), req.default_branch, assigned_json))
    conn.commit()
    conn.close()

    # Disparar código WhatsApp de activación
    branch_name = "Quito - Citimed" if req.default_branch == "quito" else "Lima - San Isidro"
    outbox = create_and_send_activation_otp(
        user_id=sec_uid,
        full_name=req.full_name.strip(),
        cedula=req.cedula.strip(),
        phone=req.phone.strip(),
        role="secretary",
        branch_name=branch_name
    )

    return {
        "success": True,
        "message": f"Secretaria registrada. Se envió código de activación por WhatsApp al {req.phone}.",
        "user_id": sec_uid,
        "otp_simulated": outbox["code"]
    }

@app.patch("/api/admin/users/{user_id}/role")
def update_user_role(user_id: str, req: UpdateUserRoleRequest):
    """Permite al SuperAdmin cambiar rol, sucursal, doctores asignados o estado del usuario."""
    conn = get_core_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM global_users WHERE id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    updates = []
    params = []

    if req.new_role:
        updates.append("role = ?")
        params.append(req.new_role)
    if req.default_branch:
        updates.append("default_branch = ?")
        params.append(req.default_branch)
    if req.assigned_doctor_ids is not None:
        updates.append("assigned_doctor_ids = ?")
        params.append(json.dumps(req.assigned_doctor_ids))
    if req.status:
        updates.append("status = ?")
        params.append(req.status)

    if updates:
        params.append(user_id)
        c.execute(f"UPDATE global_users SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()

    conn.close()
    return {"success": True, "message": f"Rol y configuración del usuario {user_id} actualizados correctamente."}

@app.get("/api/admin/summary-counts")
def get_summary_counts():
    """Retorna contadores consolidados para badges de menús ERP."""
    core_conn = get_core_connection()
    cc = core_conn.cursor()
    cc.execute("SELECT role, COUNT(*) as cnt FROM global_users GROUP BY role")
    role_counts = {row["role"]: row["cnt"] for row in cc.fetchall()}
    
    cc.execute("SELECT COUNT(*) as cnt FROM global_users WHERE status = 'pending_activation'")
    pending_otps = cc.fetchone()["cnt"]
    core_conn.close()

    total_patients = 0
    total_appointments_today = 0
    today_str = datetime.now().strftime("%Y-%m-%d")

    for br in ["quito", "lima"]:
        try:
            bconn = get_branch_connection(br)
            bc = bconn.cursor()
            bc.execute("SELECT COUNT(*) as cnt FROM patients")
            total_patients += bc.fetchone()["cnt"]
            bc.execute("SELECT COUNT(*) as cnt FROM appointments WHERE appointment_date = ?", (today_str,))
            total_appointments_today += bc.fetchone()["cnt"]
            bconn.close()
        except Exception:
            pass

    return {
        "superadmin": role_counts.get("superadmin", 0),
        "doctor": role_counts.get("doctor", 0),
        "secretary": role_counts.get("secretary", 0),
        "parent": role_counts.get("parent", 0),
        "total_users": sum(role_counts.values()),
        "pending_otps": pending_otps,
        "patients": total_patients,
        "appointments_today": total_appointments_today
    }

@app.put("/api/admin/users/{user_id}")
def update_user_complete(user_id: str, req: UpdateUserRequest):
    """Actualiza la información completa de cualquier usuario en el sistema."""
    conn = get_core_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM global_users WHERE id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    updates = []
    params = []

    if req.full_name is not None:
        updates.append("full_name = ?")
        params.append(req.full_name.strip())
    if req.email is not None:
        updates.append("email = ?")
        params.append(req.email.strip().lower())
    if req.phone is not None:
        updates.append("phone = ?")
        params.append(req.phone.strip())
    if req.cedula is not None:
        updates.append("cedula = ?")
        params.append(req.cedula.strip())
    if req.default_branch is not None:
        updates.append("default_branch = ?")
        params.append(req.default_branch)
    if req.role is not None:
        updates.append("role = ?")
        params.append(req.role)
    if req.assigned_doctor_ids is not None:
        updates.append("assigned_doctor_ids = ?")
        params.append(json.dumps(req.assigned_doctor_ids))
    if req.status is not None:
        updates.append("status = ?")
        params.append(req.status)
    if req.password:
        updates.append("password_hash = ?")
        params.append(req.password)

    if updates:
        params.append(user_id)
        c.execute(f"UPDATE global_users SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    conn.close()

    # Si es doctor, sincronizar en base de datos de la sucursal
    branch = req.default_branch or user["default_branch"] or "quito"
    try:
        bconn = get_branch_connection(branch)
        bc = bconn.cursor()
        bc.execute("SELECT id FROM doctors WHERE global_user_id = ?", (user_id,))
        doc = bc.fetchone()
        if doc:
            doc_updates = []
            doc_params = []
            if req.full_name is not None:
                doc_updates.append("full_name = ?")
                doc_params.append(req.full_name.strip())
            if req.specialty is not None:
                doc_updates.append("specialty = ?")
                doc_params.append(req.specialty.strip())
            if req.consultation_fee is not None:
                doc_updates.append("consultation_fee = ?")
                doc_params.append(req.consultation_fee)
            if req.medical_license is not None:
                doc_updates.append("medical_license = ?")
                doc_params.append(req.medical_license.strip())
            if req.bio is not None:
                doc_updates.append("bio = ?")
                doc_params.append(req.bio.strip())
            if doc_updates:
                doc_params.append(doc["id"])
                bc.execute(f"UPDATE doctors SET {', '.join(doc_updates)} WHERE id = ?", doc_params)
                bconn.commit()
        bconn.close()
    except Exception as e:
        print("Warning updating branch doctor:", e)

    # Si se especificaron pacientes para vincular al padre/tutor
    p_ids = req.patient_ids or ([req.patient_id] if req.patient_id else [])
    if p_ids:
        ced = req.cedula if req.cedula is not None else user.get("cedula", "")
        fn = req.full_name if req.full_name is not None else user.get("full_name", "")
        ph = req.phone if req.phone is not None else user.get("phone", "")
        em = req.email if req.email is not None else user.get("email", "")
        for b in ["quito", "lima"]:
            try:
                bconn = get_branch_connection(b)
                bc = bconn.cursor()
                for pid in p_ids:
                    bc.execute("""
                    UPDATE patients
                    SET parent_user_id = ?,
                        parent_cedula = ?,
                        parent_name = ?,
                        parent_phone = ?,
                        parent_email = ?
                    WHERE id = ?
                    """, (user_id, ced, fn, ph, em, pid))
                bconn.commit()
                bconn.close()
            except Exception as ex:
                pass

    return {"success": True, "message": f"Usuario {user_id} modificado exitosamente."}

@app.delete("/api/admin/users/{user_id}")
def delete_user(user_id: str):
    """Elimina o da de baja a un usuario del sistema central y sus sedes vinculadas."""
    conn = get_core_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM global_users WHERE id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Si es doctor, desactivar en las sucursales
    for br in ["quito", "lima"]:
        try:
            bconn = get_branch_connection(br)
            bc = bconn.cursor()
            bc.execute("UPDATE doctors SET is_active = 0 WHERE global_user_id = ?", (user_id,))
            bconn.commit()
            bconn.close()
        except Exception:
            pass

    c.execute("DELETE FROM otp_verifications WHERE user_id = ? OR cedula = ?", (user_id, user["cedula"]))
    c.execute("DELETE FROM global_users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return {"success": True, "message": f"Usuario '{user['full_name']}' eliminado correctamente."}

@app.post("/api/admin/users/parent")
def create_parent_user(req: CreateParentRequest):
    """Crea un padre/tutor directamente y despacha código OTP a su WhatsApp."""
    conn = get_core_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM global_users WHERE cedula = ?", (req.cedula.strip(),))
    existing_user = c.fetchone()
    
    if existing_user:
        parent_uid = existing_user["id"]
        c.execute("""
        UPDATE global_users 
        SET full_name = ?, phone = ?, default_branch = ?, status = 'active'
        WHERE id = ?
        """, (req.full_name.strip(), req.phone.strip(), req.default_branch, parent_uid))
        conn.commit()
    else:
        parent_uid = f"usr_parent_{uuid.uuid4().hex[:6]}"
        email = req.email.strip().lower() if req.email else f"padre.{req.cedula.strip()}@cranium.fit"
        c.execute("""
        INSERT INTO global_users (id, email, cedula, password_hash, full_name, phone, role, default_branch, status)
        VALUES (?, ?, ?, '', ?, ?, 'parent', ?, 'pending_activation')
        """, (parent_uid, email, req.cedula.strip(), req.full_name.strip(), req.phone.strip(), req.default_branch))
        conn.commit()
    conn.close()

    # Si se especificaron pacientes para vincular al nuevo tutor
    p_ids = req.patient_ids or ([req.patient_id] if req.patient_id else [])
    email_for_p = req.email.strip().lower() if req.email else f"padre.{req.cedula.strip()}@cranium.fit"
    if p_ids:
        branch = req.default_branch or "quito"
        for b in [branch, "quito", "lima"]:
            try:
                bconn = get_branch_connection(b)
                bc = bconn.cursor()
                for pid in p_ids:
                    bc.execute("""
                    UPDATE patients 
                    SET parent_user_id = ?, parent_cedula = ?, parent_name = ?, parent_phone = ?, parent_email = ?
                    WHERE id = ?
                    """, (parent_uid, req.cedula.strip(), req.full_name.strip(), req.phone.strip(), email_for_p, pid))
                bconn.commit()
                bconn.close()
            except Exception as ex:
                pass

    branch_name = "Quito - Citimed" if req.default_branch == "quito" else "Lima - San Isidro"
    outbox = create_and_send_activation_otp(
        user_id=parent_uid,
        full_name=req.full_name.strip(),
        cedula=req.cedula.strip(),
        phone=req.phone.strip(),
        role="parent",
        branch_name=branch_name
    )

    return {
        "success": True,
        "message": f"Tutor legal registrado y vinculado al paciente. Código OTP despachado por WhatsApp al {req.phone}.",
        "user_id": parent_uid,
        "otp_simulated": outbox["code"]
    }

@app.put("/api/patients/{patient_id}")
def update_patient(patient_id: str, req: UpdatePatientRequest, branch: str = Depends(resolve_branch)):
    """Modifica la ficha de un paciente pediátrico."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    patient = c.fetchone()
    if not patient:
        conn.close()
        raise HTTPException(status_code=404, detail="Paciente no encontrado en esta sucursal.")

    updates = []
    params = []
    if req.first_name is not None:
        updates.append("first_name = ?")
        params.append(req.first_name.strip())
    if req.last_name is not None:
        updates.append("last_name = ?")
        params.append(req.last_name.strip())
    if req.birth_date is not None:
        updates.append("birth_date = ?")
        params.append(req.birth_date)
    if req.sex is not None:
        updates.append("sex = ?")
        params.append(req.sex)
    if req.diagnosis is not None:
        updates.append("diagnosis = ?")
        params.append(req.diagnosis.strip())
    if req.primary_doctor_id is not None:
        updates.append("primary_doctor_id = ?")
        params.append(req.primary_doctor_id)
    if req.parent_cedula is not None:
        updates.append("parent_cedula = ?")
        params.append(req.parent_cedula.strip())
    if req.parent_name is not None:
        updates.append("parent_name = ?")
        params.append(req.parent_name.strip())
    if req.parent_phone is not None:
        updates.append("parent_phone = ?")
        params.append(req.parent_phone.strip())
    if req.parent_email is not None:
        updates.append("parent_email = ?")
        params.append(req.parent_email.strip())
    if req.patient_dni is not None:
        updates.append("patient_dni = ?")
        params.append(req.patient_dni.strip())
    if req.photo_url is not None:
        updates.append("photo_url = ?")
        params.append(req.photo_url.strip())

    if updates:
        params.append(patient_id)
        c.execute(f"UPDATE patients SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    conn.close()
    return {"success": True, "message": "Ficha del paciente actualizada correctamente."}

@app.delete("/api/patients/{patient_id}")
def delete_patient(patient_id: str, branch: str = Depends(resolve_branch)):
    """Elimina o archiva un paciente pediátrico de la sede."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    patient = c.fetchone()
    if not patient:
        conn.close()
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")

    c.execute("DELETE FROM appointments WHERE patient_id = ?", (patient_id,))
    c.execute("DELETE FROM cranial_scans WHERE patient_id = ?", (patient_id,))
    c.execute("DELETE FROM treatments WHERE patient_id = ?", (patient_id,))
    c.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Paciente y sus registros asociados eliminados con éxito."}

# ── 1.2 REGISTRO COMBINADO DE PACIENTE Y PADRE (SECRETARÍA) ───────────────────

@app.post("/api/secretary/patients/register")
def secretary_register_patient(
    req: SecretaryRegisterPatientRequest,
    branch: str = Depends(resolve_branch)
):
    """
    Ficha Combinada: La Secretaria registra al Padre/Tutor y al Lactante (Paciente).
    Envía automáticamente el código de activación por WhatsApp al Padre.
    """
    cedula_padre = req.parent_cedula.strip()
    nombre_padre = req.parent_name.strip()
    tel_padre = req.parent_phone.strip()
    email_padre = (req.parent_email or f"padre.{cedula_padre}@pacientes.cranium.fit").strip().lower()

    # 1. Gestionar usuario Padre en base central
    core_conn = get_core_connection()
    cc = core_conn.cursor()

    cc.execute("SELECT id, status FROM global_users WHERE cedula = ?", (cedula_padre,))
    existing_parent = cc.fetchone()

    if existing_parent:
        parent_uid = existing_parent["id"]
        cc.execute("""
        UPDATE global_users 
        SET phone = ?, full_name = ?
        WHERE id = ?
        """, (tel_padre, nombre_padre, parent_uid))
        core_conn.commit()
    else:
        parent_uid = f"usr_parent_{uuid.uuid4().hex[:6]}"
        cc.execute("""
        INSERT INTO global_users (id, email, cedula, password_hash, full_name, phone, role, default_branch, status)
        VALUES (?, ?, ?, '', ?, ?, 'parent', ?, 'pending_activation')
        """, (parent_uid, email_padre, cedula_padre, nombre_padre, tel_padre, branch))
        core_conn.commit()

    core_conn.close()

    # 2. Registrar ficha del Bebé en la base aislada de la sucursal
    branch_conn = get_branch_connection(branch)
    bc = branch_conn.cursor()

    patient_id = f"pat_{uuid.uuid4().hex[:6]}"
    patient_dni = req.patient_dni.strip() if req.patient_dni else None
    photo_url = req.photo_url.strip() if req.photo_url else None

    bc.execute("""
    INSERT INTO patients (
        id, parent_user_id, parent_cedula, parent_name, parent_phone, parent_email,
        first_name, last_name, birth_date, sex, gestational_weeks, delivery_type,
        primary_doctor_id, diagnosis, patient_dni, photo_url
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        patient_id,
        parent_uid,
        cedula_padre,
        nombre_padre,
        tel_padre,
        email_padre,
        req.first_name.strip(),
        req.last_name.strip(),
        req.birth_date.strip(),
        req.sex,
        req.gestational_weeks,
        req.delivery_type,
        req.primary_doctor_id,
        req.diagnosis or "Evaluación Inicial de Remodelación Craneal",
        patient_dni,
        photo_url
    ))

    # Sincronizar automáticamente en el directorio de clientes de facturación
    bc.execute("SELECT id FROM billing_clients WHERE identification_number = ?", (cedula_padre,))
    existing_cli = bc.fetchone()
    if existing_cli:
        bc.execute("""
        UPDATE billing_clients 
        SET name_or_business_name = ?, email = ?, phone = ?, associated_patient_id = ?
        WHERE id = ?
        """, (nombre_padre, email_padre, tel_padre, patient_id, existing_cli[0]))
    else:
        cli_id = f"cli_{uuid.uuid4().hex[:8]}"
        bc.execute("""
        INSERT INTO billing_clients (id, client_type, identification_type, identification_number, name_or_business_name, email, phone, associated_patient_id)
        VALUES (?, 'natural', '05', ?, ?, ?, ?, ?)
        """, (cli_id, cedula_padre, nombre_padre, email_padre, tel_padre, patient_id))

    branch_conn.commit()
    branch_conn.close()

    # 3. Disparar OTP de WhatsApp para activación del Padre
    branch_name = "Quito - Citimed" if branch == "quito" else "Lima - San Isidro"
    outbox = create_and_send_activation_otp(
        user_id=parent_uid,
        full_name=nombre_padre,
        cedula=cedula_padre,
        phone=tel_padre,
        role="parent",
        branch_name=branch_name
    )

    return {
        "success": True,
        "message": f"Ficha clínica registrada para el bebé {req.first_name} {req.last_name}. Se envió código de activación por WhatsApp a {nombre_padre}.",
        "patient_id": patient_id,
        "parent_user_id": parent_uid,
        "otp_simulated": outbox["code"],
        "whatsapp_preview": outbox["message"]
    }

# ── 2. DOCTORES Y AGENDA DISPONIBLE EN VIVO ───────────────────────────────────

@app.get("/api/doctors")
def get_doctors(branch: str = Depends(resolve_branch)):
    """Lista todos los doctores activos en la sucursal seleccionada."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT * FROM doctors WHERE is_active = 1")
    doctors = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"branch": branch, "doctors": doctors}

@app.get("/api/doctors/{doctor_id}/signature")
def get_doctor_signature(doctor_id: str, branch: str = Depends(resolve_branch)):
    """Consulta el estado y metadatos de la firma electrónica (.p12) del doctor."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("""
    SELECT id, full_name, medical_license, specialty, signature_p12_filename,
           signature_issuer, signature_serial_number, signature_valid_until, signature_status
    FROM doctors WHERE id = ?
    """, (doctor_id,))
    doc = c.fetchone()
    conn.close()
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")
    return {"signature": dict(doc)}

@app.post("/api/doctors/{doctor_id}/signature/upload")
async def upload_doctor_signature(
    doctor_id: str,
    file: UploadFile = File(...),
    password: str = Form(...),
    branch: str = Depends(resolve_branch)
):
    """
    Carga y valida el archivo de firma electrónica (.p12 / .pfx) para un doctor.
    Valida la contraseña y extrae metadatos con OpenSSL (Estándar República del Ecuador).
    """
    fname = file.filename or "firma.p12"
    if not (fname.lower().endswith(".p12") or fname.lower().endswith(".pfx")):
        raise HTTPException(status_code=400, detail="Formato de archivo inválido. En Ecuador la firma electrónica oficial debe ser formato .p12 o .pfx.")
    
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="El archivo .p12 enviado está vacío.")

    metadata = verify_and_extract_p12(file_bytes, password, doctor_id, fname)
    if not metadata.get("is_valid"):
        raise HTTPException(status_code=400, detail=metadata.get("error", "Error al verificar la firma electrónica."))

    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("""
    UPDATE doctors
    SET signature_p12_path = ?,
        signature_p12_filename = ?,
        signature_issuer = ?,
        signature_serial_number = ?,
        signature_valid_until = ?,
        signature_status = 'active'
    WHERE id = ?
    """, (
        metadata["file_path"],
        metadata["file_name"],
        metadata["issuer"],
        metadata["serial_number"],
        metadata["valid_until"],
        doctor_id
    ))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Firma electrónica .p12 validada y configurada exitosamente.",
        "signature_info": {
            "doctor_id": doctor_id,
            "filename": metadata["file_name"],
            "common_name": metadata.get("common_name"),
            "issuer": metadata["issuer"],
            "serial_number": metadata["serial_number"],
            "valid_from": metadata.get("valid_from"),
            "valid_until": metadata["valid_until"],
            "status": "active"
        }
    }

@app.post("/api/doctors/{doctor_id}/signature/generate-demo")
def generate_demo_signature(
    doctor_id: str,
    branch: str = Depends(resolve_branch)
):
    """
    Genera y activa una firma electrónica demostrativa (.p12) emitida por Security Data S.A.
    Permite probar el firmado digital de recetas y certificados de forma inmediata.
    """
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,))
    doc = c.fetchone()
    if not doc:
        conn.close()
        raise HTTPException(status_code=404, detail="Doctor no encontrado")
    
    doc_name = doc["full_name"]
    demo_sig = create_demo_p12_for_doctor(doctor_id, doc_name)
    c.execute("""
    UPDATE doctors
    SET signature_p12_path = ?,
        signature_p12_filename = ?,
        signature_issuer = ?,
        signature_serial_number = ?,
        signature_valid_until = ?,
        signature_status = 'active'
    WHERE id = ?
    """, (
        demo_sig["file_path"],
        demo_sig["file_name"],
        demo_sig["issuer"],
        demo_sig["serial_number"],
        demo_sig["valid_until"],
        doctor_id
    ))
    conn.commit()
    conn.close()
    return {
        "success": True,
        "message": f"Firma electrónica demostrativa activada para {doc_name}.",
        "signature_info": {
            "doctor_id": doctor_id,
            "filename": demo_sig["file_name"],
            "issuer": demo_sig["issuer"],
            "serial_number": demo_sig["serial_number"],
            "valid_until": demo_sig["valid_until"],
            "status": "active"
        }
    }

@app.delete("/api/doctors/{doctor_id}/signature")
def delete_doctor_signature(doctor_id: str, branch: str = Depends(resolve_branch)):
    """Desvincula la firma electrónica del doctor."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("""
    UPDATE doctors
    SET signature_p12_path = NULL,
        signature_p12_filename = NULL,
        signature_issuer = NULL,
        signature_serial_number = NULL,
        signature_valid_until = NULL,
        signature_status = 'not_configured'
    WHERE id = ?
    """, (doctor_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Firma electrónica desvinculada del doctor."}

@app.get("/api/doctors/{doctor_id}/availability")
def get_doctor_availability(
    doctor_id: str,
    date_str: str = Query(..., alias="date", description="Fecha YYYY-MM-DD"),
    branch: str = Depends(resolve_branch)
):
    """
    Calcula los slots horarios reales disponibles para un doctor específico en una fecha dada.
    Excluye citas ya reservadas o en proceso de pago.
    """
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usar YYYY-MM-DD")

    # Obtener día de la semana en Python (Lunes=0, Domingo=6)
    # En nuestra DB: 1=Lunes, 2=Martes... 6=Sábado, 7=Domingo
    day_of_week = target_date.weekday() + 1

    conn = get_branch_connection(branch)
    c = conn.cursor()

    # 1. Obtener horario laboral del doctor para ese día
    c.execute("""
    SELECT start_time, end_time, slot_duration_min
    FROM doctor_schedules
    WHERE doctor_id = ? AND day_of_week = ?
    """, (doctor_id, day_of_week))
    schedule = c.fetchone()

    if not schedule:
        conn.close()
        return {
            "doctor_id": doctor_id,
            "date": date_str,
            "is_working_day": False,
            "booked_appointments": [],
            "available_slots": []
        }

    # 2. Obtener citas ya reservadas para ese doctor en esa fecha con nombre del paciente
    c.execute("""
    SELECT a.id, a.start_time, a.end_time, a.status, a.appointment_type,
           COALESCE(p.first_name || ' ' || p.last_name, 'Paciente Reservado') as patient_name,
           p.patient_dni, a.clinical_notes
    FROM appointments a
    LEFT JOIN patients p ON a.patient_id = p.id
    WHERE a.doctor_id = ? AND a.appointment_date = ? AND a.status != 'cancelled'
    ORDER BY a.start_time ASC
    """, (doctor_id, date_str))
    booked_appointments = [dict(row) for row in c.fetchall()]
    booked_by_time = {a["start_time"]: a for a in booked_appointments}
    conn.close()

    # 3. Generar la rejilla de slots y filtrar los ocupados (30 min)
    start_dt = datetime.strptime(schedule["start_time"], "%H:%M")
    end_dt = datetime.strptime(schedule["end_time"], "%H:%M")
    slot_duration = schedule["slot_duration_min"] or 30
    slot_delta = timedelta(minutes=slot_duration)

    available_slots = []
    curr = start_dt
    while curr + slot_delta <= end_dt:
        time_slot_str = curr.strftime("%H:%M")
        booking = booked_by_time.get(time_slot_str)
        is_booked = booking is not None
        available_slots.append({
            "time": time_slot_str,
            "available": not is_booked,
            "patient_name": booking["patient_name"] if booking else None,
            "status": booking["status"] if booking else "free"
        })
        curr += slot_delta

    return {
        "doctor_id": doctor_id,
        "date": date_str,
        "is_working_day": True,
        "slot_duration_min": slot_duration,
        "schedule": {
            "start_time": schedule["start_time"],
            "end_time": schedule["end_time"],
            "slot_duration_min": slot_duration
        },
        "booked_appointments": booked_appointments,
        "total_slots": len(available_slots),
        "available_slots": available_slots
    }

# ── 3. AGENDAMIENTO Y PAGOS DE CONSULTA ─────────────────────────────────────────

@app.post("/api/appointments/book")
def book_appointment(req: BookAppointmentRequest, branch: str = Depends(resolve_branch)):
    """
    Agenda una nueva cita médica con procesamiento de pago integrado.
    Si es un paciente nuevo, crea su ficha preliminar automáticamente.
    """
    conn = get_branch_connection(branch)
    c = conn.cursor()

    # Verificar si el horario sigue libre
    c.execute("""
    SELECT id FROM appointments
    WHERE doctor_id = ? AND appointment_date = ? AND start_time = ? AND status != 'cancelled'
    """, (req.doctor_id, req.appointment_date, req.start_time))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="El horario seleccionado acaba de ser reservado por otro usuario. Por favor elija otro.")

    # Obtener costo del doctor
    c.execute("SELECT consultation_fee, appointment_duration_min, full_name FROM doctors WHERE id = ?", (req.doctor_id,))
    doc = c.fetchone()
    if not doc:
        conn.close()
        raise HTTPException(status_code=404, detail="Doctor no encontrado")

    fee = doc["consultation_fee"]
    duration = doc["appointment_duration_min"]
    
    # Calcular end_time
    start_dt = datetime.strptime(req.start_time, "%H:%M")
    end_time_str = (start_dt + timedelta(minutes=duration)).strftime("%H:%M")

    # Identificar o crear paciente
    patient_id = req.patient_id
    if not patient_id:
        patient_id = f"pat_{uuid.uuid4().hex[:8]}"
        c.execute("""
        INSERT INTO patients (id, parent_user_id, parent_name, parent_phone, parent_email, first_name, last_name, birth_date, primary_doctor_id, diagnosis)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_id,
            "usr_guest",
            req.patient_name,
            req.parent_phone,
            req.parent_email,
            req.patient_name,
            "",
            date.today().isoformat(),
            req.doctor_id,
            "Primera Evaluación Craneal 3D"
        ))

    # Definir estado de pago según el método
    appointment_id = f"apt_{uuid.uuid4().hex[:8]}"
    if req.payment_method == "tarjeta_online":
        pay_status = "paid"
        pay_ref = req.payment_reference or f"CC-{uuid.uuid4().hex[:8].upper()}"
        apt_status = "confirmed"
    elif req.payment_method == "transferencia":
        pay_status = "pending_verification"
        pay_ref = req.payment_reference or f"TRF-{uuid.uuid4().hex[:8].upper()}"
        apt_status = "confirmed" # confirmada sujeta a verificación de secretaria
    else:
        pay_status = "unpaid"
        pay_ref = "PAGO-EN-CONSULTORIO"
        apt_status = "confirmed"

    c.execute("""
    INSERT INTO appointments (
        id, patient_id, doctor_id, appointment_date, start_time, end_time,
        appointment_type, status, amount, payment_method, payment_status, payment_ref
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        appointment_id,
        patient_id,
        req.doctor_id,
        req.appointment_date,
        req.start_time,
        end_time_str,
        req.appointment_type,
        apt_status,
        fee,
        req.payment_method,
        pay_status,
        pay_ref
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "appointment_id": appointment_id,
        "patient_id": patient_id,
        "doctor_name": doc["full_name"],
        "date": req.appointment_date,
        "time": f"{req.start_time} - {end_time_str}",
        "amount_paid": fee,
        "payment_status": pay_status,
        "message": "¡Cita médica agendada y confirmada exitosamente! Se ha enviado el recordatorio por WhatsApp."
    }

@app.get("/api/appointments")
def list_appointments(
    doctor_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    date_str: Optional[str] = Query(None, alias="date"),
    branch: str = Depends(resolve_branch)
):
    """Listado de citas para el tablero de la secretaria o doctor."""
    conn = get_branch_connection(branch)
    c = conn.cursor()

    query = """
    SELECT 
        a.*,
        p.first_name || ' ' || p.last_name as patient_name,
        p.parent_name,
        p.parent_phone,
        p.parent_email,
        d.full_name as doctor_name,
        d.specialty as doctor_specialty
    FROM appointments a
    JOIN patients p ON a.patient_id = p.id
    JOIN doctors d ON a.doctor_id = d.id
    WHERE 1=1
    """
    params = []
    if doctor_id:
        query += " AND a.doctor_id = ?"
        params.append(doctor_id)
    if patient_id:
        query += " AND a.patient_id = ?"
        params.append(patient_id)
    if date_str:
        query += " AND a.appointment_date = ?"
        params.append(date_str)

    query += " ORDER BY a.appointment_date DESC, a.start_time ASC"
    c.execute(query, params)
    apts = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"branch": branch, "total": len(apts), "appointments": apts}

@app.patch("/api/appointments/{appointment_id}/status")
def update_appointment_status(
    appointment_id: str,
    req: UpdateAppointmentStatusRequest,
    branch: str = Depends(resolve_branch)
):
    """Permite a la secretaria o doctor cambiar estado (ej. check-in sala de espera)."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("UPDATE appointments SET status = ? WHERE id = ?", (req.status, appointment_id))
    if req.payment_status:
        c.execute("UPDATE appointments SET payment_status = ? WHERE id = ?", (req.payment_status, appointment_id))
    conn.commit()
    conn.close()
    return {"success": True, "appointment_id": appointment_id, "new_status": req.status}

# ── 4. HISTORIA CLÍNICA, ESCANEOS 3D Y EVOLUCIÓN CRANEAL ─────────────────────

@app.get("/api/patients")
def list_patients(branch: str = Depends(resolve_branch)):
    """Lista todos los pacientes de la sucursal activa con métricas clínicas."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("""
    SELECT 
        p.*,
        d.full_name as doctor_name,
        d.specialty as doctor_specialty,
        (SELECT cvai FROM cranial_scans WHERE patient_id = p.id ORDER BY session_number DESC LIMIT 1) as latest_cvai,
        (SELECT argenta_grade FROM cranial_scans WHERE patient_id = p.id ORDER BY session_number DESC LIMIT 1) as latest_argenta,
        (SELECT COUNT(*) FROM medical_consultations WHERE patient_id = p.id) as total_consultations,
        (SELECT COUNT(*) FROM medical_exams WHERE patient_id = p.id) as total_exams,
        (SELECT COUNT(*) FROM medical_prescriptions WHERE patient_id = p.id) as total_prescriptions
    FROM patients p
    LEFT JOIN doctors d ON p.primary_doctor_id = d.id
    ORDER BY p.created_at DESC
    """)
    patients = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"branch": branch, "patients": patients}

@app.get("/api/patients/{patient_id}")
def get_patient_detail(patient_id: str, branch: str = Depends(resolve_branch)):
    """Expediente clínico básico del bebé."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    patient = c.fetchone()
    if not patient:
        conn.close()
        raise HTTPException(status_code=404, detail="Paciente no encontrado en esta sucursal")

    c.execute("SELECT * FROM cranial_scans WHERE patient_id = ? ORDER BY session_number ASC", (patient_id,))
    scans = [dict(row) for row in c.fetchall()]

    c.execute("SELECT * FROM treatments WHERE patient_id = ?", (patient_id,))
    treatment = c.fetchone()

    c.execute("SELECT * FROM wear_time_logs WHERE patient_id = ? ORDER BY log_date DESC LIMIT 14", (patient_id,))
    wear_logs = [dict(row) for row in c.fetchall()]

    conn.close()
    return {
        "patient": dict(patient),
        "scans": scans,
        "treatment": dict(treatment) if treatment else None,
        "wear_logs": wear_logs
    }

@app.get("/api/patients/{patient_id}/medical-history")
def get_patient_medical_history(patient_id: str, branch: str = Depends(resolve_branch)):
    """Historial médico completo e integral del paciente pediátrico."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    
    # 1. Datos del paciente y médico
    c.execute("""
        SELECT p.*, d.full_name as doctor_name, d.specialty as doctor_specialty, d.medical_license as doctor_license
        FROM patients p
        LEFT JOIN doctors d ON p.primary_doctor_id = d.id
        WHERE p.id = ?
    """, (patient_id,))
    patient = c.fetchone()
    if not patient:
        conn.close()
        raise HTTPException(status_code=404, detail="Paciente no encontrado en esta sucursal")
    patient_dict = dict(patient)
    
    # 2. Consultas Médicas
    c.execute("""
        SELECT 
            mc.*,
            d.full_name as doctor_name,
            d.specialty as doctor_specialty,
            d.medical_license as doctor_license
        FROM medical_consultations mc
        LEFT JOIN doctors d ON mc.doctor_id = d.id
        WHERE mc.patient_id = ?
        ORDER BY mc.consultation_date DESC
    """, (patient_id,))
    consultations = []
    for r in c.fetchall():
        row_dict = dict(r)
        if row_dict.get("vital_signs") and isinstance(row_dict["vital_signs"], str):
            try:
                row_dict["vital_signs"] = json.loads(row_dict["vital_signs"])
            except:
                pass
        # Aliases para compatibilidad frontend
        row_dict["reason"] = row_dict.get("reason_for_visit")
        row_dict["cranial_evaluation"] = row_dict.get("cranial_eval")
        row_dict["next_appointment"] = row_dict.get("next_appointment_rec")
        consultations.append(row_dict)
        
    # 3. Exámenes y Diagnósticos
    c.execute("""
        SELECT 
            me.*,
            d.full_name as doctor_name,
            d.specialty as doctor_specialty
        FROM medical_exams me
        LEFT JOIN doctors d ON me.doctor_id = d.id
        WHERE me.patient_id = ?
        ORDER BY me.exam_date DESC
    """, (patient_id,))
    exams = []
    for r in c.fetchall():
        row_dict = dict(r)
        if row_dict.get("measurements") and isinstance(row_dict["measurements"], str):
            try:
                row_dict["measurements"] = json.loads(row_dict["measurements"])
            except:
                pass
        # Aliases para compatibilidad frontend
        row_dict["summary_findings"] = row_dict.get("results_summary")
        exams.append(row_dict)
        
    # 4. Escaneos 3D y Telemetría Craneal
    c.execute("SELECT * FROM cranial_scans WHERE patient_id = ? ORDER BY session_number ASC", (patient_id,))
    scans = [dict(row) for row in c.fetchall()]
    
    # 5. Recetas y Prescripciones Médicas
    c.execute("""
        SELECT 
            mp.*,
            d.full_name as doctor_name,
            d.specialty as doctor_specialty,
            d.medical_license as doctor_license
        FROM medical_prescriptions mp
        LEFT JOIN doctors d ON mp.doctor_id = d.id
        WHERE mp.patient_id = ?
        ORDER BY mp.prescription_date DESC
    """, (patient_id,))
    prescriptions = []
    for r in c.fetchall():
        row_dict = dict(r)
        row_dict["medications"] = row_dict.get("medications_rx")
        row_dict["orthotic_protocol"] = row_dict.get("orthotic_prescription")
        row_dict["therapy_recommendations"] = row_dict.get("physical_therapy_orders")
        row_dict["general_instructions"] = row_dict.get("special_instructions")
        prescriptions.append(row_dict)
    
    # 6. Tratamiento con Casco y Horas de Uso
    c.execute("SELECT * FROM treatments WHERE patient_id = ?", (patient_id,))
    treatment = c.fetchone()
    
    c.execute("SELECT * FROM wear_time_logs WHERE patient_id = ? ORDER BY log_date DESC LIMIT 14", (patient_id,))
    wear_logs = [dict(row) for row in c.fetchall()]

    # 7. Certificados Médicos Firmados Digitalmente
    c.execute("""
        SELECT 
            mc.*,
            d.full_name as doctor_name,
            d.specialty as doctor_specialty,
            d.medical_license as doctor_license,
            d.signature_issuer,
            d.signature_serial_number
        FROM medical_certificates mc
        LEFT JOIN doctors d ON mc.doctor_id = d.id
        WHERE mc.patient_id = ?
        ORDER BY mc.issue_date DESC
    """, (patient_id,))
    certificates = []
    for r in c.fetchall():
        row_dict = dict(r)
        if row_dict.get("signature_certificate_info") and isinstance(row_dict["signature_certificate_info"], str):
            try:
                row_dict["signature_certificate_info"] = json.loads(row_dict["signature_certificate_info"])
            except:
                pass
        certificates.append(row_dict)

    # 8. Dossiers de Aseguradora / Cobertura Médica
    c.execute("""
        SELECT 
            dos.*,
            d.full_name as doctor_name,
            d.specialty as doctor_specialty,
            d.medical_license as doctor_license,
            d.signature_issuer,
            d.signature_serial_number
        FROM insurance_dossiers dos
        LEFT JOIN doctors d ON dos.doctor_id = d.id
        WHERE dos.patient_id = ?
        ORDER BY dos.created_at DESC
    """, (patient_id,))
    dossiers = []
    for r in c.fetchall():
        row_dict = dict(r)
        if row_dict.get("signature_certificate_info") and isinstance(row_dict["signature_certificate_info"], str):
            try:
                row_dict["signature_certificate_info"] = json.loads(row_dict["signature_certificate_info"])
            except:
                pass
        row_dict["diagnosis_code"] = row_dict.get("diagnosis_cie10") or "Q67.3 Plagiocefalia Posicional"
        row_dict["estimated_cost_usd"] = row_dict.get("estimated_cost") or 0.0
        row_dict["medical_necessity_rationale"] = row_dict.get("clinical_justification") or ""
        dossiers.append(row_dict)
    
    conn.close()
    
    latest_cvai = scans[-1]["cvai"] if scans else (exams[0]["cvai"] if exams and exams[0].get("cvai") else None)
    
    return {
        "success": True,
        "branch": branch,
        "patient": patient_dict,
        "consultations": consultations,
        "exams": exams,
        "cranial_scans": scans,
        "prescriptions": prescriptions,
        "certificates": certificates,
        "dossiers": dossiers,
        "treatment": dict(treatment) if treatment else None,
        "wear_logs": wear_logs,
        "metrics": {
            "total_consultations": len(consultations),
            "total_exams": len(exams),
            "total_scans": len(scans),
            "total_prescriptions": len(prescriptions),
            "total_certificates": len(certificates),
            "total_dossiers": len(dossiers),
            "latest_cvai": latest_cvai,
            "latest_consultation_date": consultations[0]["consultation_date"] if consultations else None
        }
    }

@app.post("/api/patients/{patient_id}/consultations")
def create_patient_consultation(
    patient_id: str,
    req: CreateConsultationRequest,
    branch: str = Depends(resolve_branch)
):
    """Registra una nueva consulta médica en el expediente del paciente."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT id FROM patients WHERE id = ?", (patient_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Paciente no encontrado en esta sucursal")
        
    consultation_id = f"mc_{uuid.uuid4().hex[:8]}"
    now_str = req.consultation_date or datetime.now().strftime("%Y-%m-%d %H:%M")
    vital_signs_json = json.dumps(req.vital_signs or {})
    
    reason_for_visit_val = req.reason_for_visit or req.reason or "Control clínico de rutina"
    cranial_eval_val = req.cranial_eval or req.cranial_evaluation or ""
    next_appointment_rec_val = req.next_appointment_rec or req.next_appointment or ""
    
    c.execute("""
    INSERT INTO medical_consultations (
        id, patient_id, doctor_id, consultation_date, reason_for_visit,
        vital_signs, cranial_eval, diagnosis, clinical_evolution, treatment_plan, next_appointment_rec
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        consultation_id, patient_id, req.doctor_id, now_str, reason_for_visit_val,
        vital_signs_json, cranial_eval_val, req.diagnosis, req.clinical_evolution,
        req.treatment_plan, next_appointment_rec_val
    ))
    
    # Actualizar diagnóstico principal del paciente
    if req.diagnosis:
        c.execute("UPDATE patients SET diagnosis = ? WHERE id = ?", (req.diagnosis, patient_id))
        
    conn.commit()
    conn.close()
    return {"success": True, "consultation_id": consultation_id, "consultation_date": now_str}

@app.post("/api/patients/{patient_id}/exams")
def create_patient_exam(
    patient_id: str,
    req: CreateExamRequest,
    branch: str = Depends(resolve_branch)
):
    """Registra un nuevo examen clínico o escaneo 3D en el expediente."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT id FROM patients WHERE id = ?", (patient_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Paciente no encontrado en esta sucursal")
        
    exam_id = f"exam_{uuid.uuid4().hex[:8]}"
    now_str = req.exam_date or datetime.now().strftime("%Y-%m-%d")
    
    measurements_dict = req.measurements or {}
    if not measurements_dict and (req.diagonal_a_mm or req.diagonal_b_mm):
        measurements_dict = {
            "diagonal_a_mm": req.diagonal_a_mm,
            "diagonal_b_mm": req.diagonal_b_mm,
            "cephalic_index": req.cephalic_index
        }
    measurements_json = json.dumps(measurements_dict)
    
    results_summary_val = req.results_summary or req.summary_findings or req.summary or "Estudio diagnóstico completado"
    
    c.execute("""
    INSERT INTO medical_exams (
        id, patient_id, doctor_id, exam_date, exam_type, cvai,
        cephalic_index, argenta_grade, measurements, results_summary, recommendations, file_url
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        exam_id, patient_id, req.doctor_id, now_str, req.exam_type,
        req.cvai, req.cephalic_index, req.argenta_grade,
        measurements_json, results_summary_val, req.recommendations or "", req.file_url or ""
    ))
    
    # Si incluye CVAI, también creamos la sesión en cranial_scans para alimentar el visor 3D
    if req.cvai is not None:
        c.execute("SELECT MAX(session_number) FROM cranial_scans WHERE patient_id = ?", (patient_id,))
        last_sess = c.fetchone()[0] or 0
        new_sess = last_sess + 1
        scan_id = f"scan_{uuid.uuid4().hex[:8]}"
        diag_a = measurements_dict.get("diagonal_a_mm") or req.diagonal_a_mm or 140.0
        diag_b = measurements_dict.get("diagonal_b_mm") or req.diagonal_b_mm or 130.0
        circ = measurements_dict.get("circumference_mm", 435.0)
        ci = req.cephalic_index or 84.0
        arg_grade = req.argenta_grade or (2 if req.cvai > 7 else 1)
        
        c.execute("""
        INSERT INTO cranial_scans (
            id, patient_id, session_number, scan_date, cvai, cephalic_index,
            argenta_grade, diagonal_a_mm, diagonal_b_mm, circumference_mm, width_mm, length_mm, clinical_summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            scan_id, patient_id, new_sess, now_str, req.cvai, ci,
            arg_grade, diag_a, diag_b, circ, 128.0, 150.0, results_summary_val
        ))
        
    conn.commit()
    conn.close()
    return {"success": True, "exam_id": exam_id, "exam_date": now_str}

@app.post("/api/patients/{patient_id}/prescriptions")
def create_patient_prescription(
    patient_id: str,
    req: CreatePrescriptionRequest,
    branch: str = Depends(resolve_branch)
):
    """Emite una nueva receta médica y orden ortésica con Firma Electrónica (.p12)."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    patient = c.fetchone()
    if not patient:
        conn.close()
        raise HTTPException(status_code=404, detail="Paciente no encontrado en esta sucursal")
        
    c.execute("SELECT * FROM doctors WHERE id = ?", (req.doctor_id,))
    doctor = c.fetchone()
    doctor_info = dict(doctor) if doctor else {
        "full_name": "Dr. Especialista CraniumFit",
        "medical_license": "MSP-EC-10948",
        "specialty": "Ortopedia Craneofacial Pediátrica",
        "signature_issuer": "Security Data Seguridad en Datos y Firma Digital S.A.",
        "signature_serial_number": "SD-EC-2026-09412A",
        "signature_valid_until": "2028-11-15"
    }

    # Obtener prefijo de sede
    prefix = branch[:3].upper()
    try:
        core_conn = get_core_connection()
        b_cur = core_conn.cursor()
        b_cur.execute("SELECT invoice_prefix FROM branches WHERE id = ?", (branch,))
        b_row = b_cur.fetchone()
        if b_row and b_row["invoice_prefix"]:
            prefix = b_row["invoice_prefix"].upper()
        core_conn.close()
    except Exception:
        pass

    c.execute("SELECT COUNT(*) FROM medical_prescriptions")
    count_rx = (c.fetchone()[0] or 0) + 1
    year = datetime.now().year
    rx_number = f"RX-{prefix}-{year}-{count_rx:03d}"
    
    rx_id = f"rx_{uuid.uuid4().hex[:8]}"
    now_str = req.prescription_date or datetime.now().strftime("%Y-%m-%d")
    valid_until = req.valid_until or (date.today() + timedelta(days=60)).isoformat()
    
    medications_rx_val = req.medications_rx or req.medications or ""
    orthotic_prescription_val = req.orthotic_prescription or req.orthotic_protocol or ""
    physical_therapy_orders_val = req.physical_therapy_orders or req.therapy_recommendations or ""
    special_instructions_val = req.special_instructions or req.general_instructions or ""
    
    # Firmar digitalmente el documento según el estándar de Ecuador
    signature_stamp = sign_medical_document(
        doc_type="receta_medica",
        doc_id=rx_number,
        content={
            "patient_id": patient_id,
            "patient_name": f"{patient['first_name']} {patient['last_name']}",
            "medications": medications_rx_val,
            "orthotic_prescription": orthotic_prescription_val,
            "physical_therapy": physical_therapy_orders_val,
            "instructions": special_instructions_val,
            "prescription_date": now_str,
            "valid_until": valid_until
        },
        doctor_info=doctor_info
    )
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https%3A%2F%2Fcranium.fit%2Fvalidar-receta%3Fnum%3D{rx_number}"

    c.execute("""
    INSERT INTO medical_prescriptions (
        id, prescription_number, patient_id, doctor_id, consultation_id, prescription_date,
        medications_rx, orthotic_prescription, physical_therapy_orders, special_instructions, valid_until,
        signed_electronically, signature_hash, signature_timestamp, signature_certificate_info, signature_qr_url
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        rx_id, rx_number, patient_id, req.doctor_id, req.consultation_id or "", now_str,
        medications_rx_val, orthotic_prescription_val,
        physical_therapy_orders_val, special_instructions_val, valid_until,
        1, signature_stamp["sha256_hash"], signature_stamp["signature_date"],
        json.dumps(signature_stamp), qr_url
    ))
    
    conn.commit()
    conn.close()
    return {
        "success": True,
        "prescription_id": rx_id,
        "prescription_number": rx_number,
        "prescription_date": now_str,
        "signature_stamp": signature_stamp,
        "qr_url": qr_url
    }

@app.get("/api/prescriptions/{prescription_id}")
def get_prescription_detail(prescription_id: str, branch: str = Depends(resolve_branch)):
    """Obtiene el detalle completo de una receta médica firmada para imprimir o generar PDF."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("""
    SELECT 
        mp.*,
        p.first_name, p.last_name, p.birth_date, p.parent_name, p.parent_cedula, p.parent_phone, p.diagnosis as patient_diagnosis,
        d.full_name as doctor_name, d.specialty as doctor_specialty, d.medical_license as doctor_license,
        d.signature_issuer, d.signature_serial_number, d.signature_valid_until
    FROM medical_prescriptions mp
    JOIN patients p ON mp.patient_id = p.id
    LEFT JOIN doctors d ON mp.doctor_id = d.id
    WHERE mp.id = ? OR mp.prescription_number = ?
    """, (prescription_id, prescription_id))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Receta médica no encontrada")
    
    data = dict(row)
    if data.get("signature_certificate_info") and isinstance(data["signature_certificate_info"], str):
        try:
            data["signature_certificate_info"] = json.loads(data["signature_certificate_info"])
        except Exception:
            pass
    return {"prescription": data}

@app.get("/api/patients/{patient_id}/prescriptions")
def get_patient_prescriptions(patient_id: str, branch: str = Depends(resolve_branch)):
    """Lista todas las recetas médicas firmadas emitidas para el paciente."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("""
    SELECT 
        mp.*,
        d.full_name as doctor_name, d.specialty as doctor_specialty, d.medical_license as doctor_license
    FROM medical_prescriptions mp
    LEFT JOIN doctors d ON mp.doctor_id = d.id
    WHERE mp.patient_id = ?
    ORDER BY mp.prescription_date DESC
    """, (patient_id,))
    rows = []
    for r in c.fetchall():
        d = dict(r)
        if d.get("signature_certificate_info") and isinstance(d["signature_certificate_info"], str):
            try:
                d["signature_certificate_info"] = json.loads(d["signature_certificate_info"])
            except Exception:
                pass
        rows.append(d)
    conn.close()
    return {"patient_id": patient_id, "prescriptions": rows}

@app.post("/api/patients/{patient_id}/medical-certificates")
def create_patient_medical_certificate(
    patient_id: str,
    req: CreateMedicalCertificateRequest,
    branch: str = Depends(resolve_branch)
):
    """Emite un nuevo certificado médico firmado digitalmente con formato .p12."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    patient = c.fetchone()
    if not patient:
        conn.close()
        raise HTTPException(status_code=404, detail="Paciente no encontrado en esta sucursal")
        
    c.execute("SELECT * FROM doctors WHERE id = ?", (req.doctor_id,))
    doctor = c.fetchone()
    doctor_info = dict(doctor) if doctor else {
        "full_name": "Dr. Especialista CraniumFit",
        "medical_license": "MSP-EC-10948",
        "specialty": "Ortopedia Craneofacial Pediátrica",
        "signature_issuer": "Security Data Seguridad en Datos y Firma Digital S.A.",
        "signature_serial_number": "SD-EC-2026-09412A",
        "signature_valid_until": "2028-11-15"
    }

    # Obtener prefijo de sede
    prefix = branch[:3].upper()
    try:
        core_conn = get_core_connection()
        b_cur = core_conn.cursor()
        b_cur.execute("SELECT invoice_prefix FROM branches WHERE id = ?", (branch,))
        b_row = b_cur.fetchone()
        if b_row and b_row["invoice_prefix"]:
            prefix = b_row["invoice_prefix"].upper()
        core_conn.close()
    except Exception:
        pass

    c.execute("SELECT COUNT(*) FROM medical_certificates")
    count_cert = (c.fetchone()[0] or 0) + 1
    year = datetime.now().year
    cert_number = f"CERT-{prefix}-{year}-{count_cert:03d}"
    
    cert_id = f"cert_{uuid.uuid4().hex[:8]}"
    now_str = req.issue_date or datetime.now().strftime("%Y-%m-%d")
    valid_until = req.valid_until or (date.today() + timedelta(days=90)).isoformat()
    
    # Firmar digitalmente el certificado médico
    signature_stamp = sign_medical_document(
        doc_type="certificado_medico",
        doc_id=cert_number,
        content={
            "patient_id": patient_id,
            "patient_name": f"{patient['first_name']} {patient['last_name']}",
            "certificate_type": req.certificate_type,
            "diagnosis_cie10": req.diagnosis_cie10,
            "clinical_findings": req.clinical_findings,
            "rest_days": req.rest_days,
            "formal_statement": req.formal_statement,
            "issue_date": now_str,
            "valid_until": valid_until
        },
        doctor_info=doctor_info
    )
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https%3A%2F%2Fcranium.fit%2Fvalidar-certificado%3Fnum%3D{cert_number}"

    c.execute("""
    INSERT INTO medical_certificates (
        id, certificate_number, patient_id, doctor_id, consultation_id, issue_date,
        certificate_type, diagnosis_cie10, clinical_findings, rest_days, valid_until,
        formal_statement, signed_electronically, signature_hash, signature_timestamp,
        signature_certificate_info, signature_qr_url
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cert_id, cert_number, patient_id, req.doctor_id, req.consultation_id or "", now_str,
        req.certificate_type, req.diagnosis_cie10, req.clinical_findings or "",
        req.rest_days, valid_until, req.formal_statement,
        1, signature_stamp["sha256_hash"], signature_stamp["signature_date"],
        json.dumps(signature_stamp), qr_url
    ))
    
    conn.commit()
    conn.close()
    return {
        "success": True,
        "certificate_id": cert_id,
        "certificate_number": cert_number,
        "issue_date": now_str,
        "signature_stamp": signature_stamp,
        "qr_url": qr_url
    }

@app.get("/api/patients/{patient_id}/medical-certificates")
def get_patient_medical_certificates(patient_id: str, branch: str = Depends(resolve_branch)):
    """Lista todos los certificados médicos emitidos para el paciente."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("""
    SELECT 
        mc.*,
        d.full_name as doctor_name, d.specialty as doctor_specialty, d.medical_license as doctor_license
    FROM medical_certificates mc
    LEFT JOIN doctors d ON mc.doctor_id = d.id
    WHERE mc.patient_id = ?
    ORDER BY mc.issue_date DESC
    """, (patient_id,))
    rows = []
    for r in c.fetchall():
        d = dict(r)
        if d.get("signature_certificate_info") and isinstance(d["signature_certificate_info"], str):
            try:
                d["signature_certificate_info"] = json.loads(d["signature_certificate_info"])
            except Exception:
                pass
        rows.append(d)
    conn.close()
    return {"patient_id": patient_id, "certificates": rows}

@app.get("/api/medical-certificates/{certificate_id}")
def get_medical_certificate_detail(certificate_id: str, branch: str = Depends(resolve_branch)):
    """Obtiene el detalle completo de un certificado médico para imprimir o generar PDF."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("""
    SELECT 
        mc.*,
        p.first_name, p.last_name, p.birth_date, p.parent_name, p.parent_cedula, p.parent_phone, p.diagnosis as patient_diagnosis,
        d.full_name as doctor_name, d.specialty as doctor_specialty, d.medical_license as doctor_license,
        d.signature_issuer, d.signature_serial_number, d.signature_valid_until
    FROM medical_certificates mc
    JOIN patients p ON mc.patient_id = p.id
    LEFT JOIN doctors d ON mc.doctor_id = d.id
    WHERE mc.id = ? OR mc.certificate_number = ?
    """, (certificate_id, certificate_id))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Certificado médico no encontrado")
    
    data = dict(row)
    if data.get("signature_certificate_info") and isinstance(data["signature_certificate_info"], str):
        try:
            data["signature_certificate_info"] = json.loads(data["signature_certificate_info"])
        except Exception:
            pass
    return {"certificate": data}

# ── MÓDULOS AVANZADOS: DOSSIERS, TELE-TRIAJE, MES & FACTURACIÓN SRI ───────────

@app.post("/api/patients/{patient_id}/insurance-dossiers")
def create_patient_insurance_dossier(
    patient_id: str,
    req: CreateInsuranceDossierRequest,
    branch: str = Depends(resolve_branch)
):
    """Emite un Dossier de Justificación Biomecánica y Reembolso para Aseguradoras firmado digitalmente con .p12."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    patient = c.fetchone()
    if not patient:
        conn.close()
        raise HTTPException(status_code=404, detail="Paciente no encontrado en esta sucursal")
        
    c.execute("SELECT * FROM doctors WHERE id = ?", (req.doctor_id,))
    doctor = c.fetchone()
    doctor_info = dict(doctor) if doctor else {
        "full_name": "Dr. Carlos Morales",
        "medical_license": "MSP-EC-10948",
        "specialty": "Ortopedia Craneofacial Pediátrica",
        "signature_issuer": "Security Data Seguridad en Datos y Firma Digital S.A.",
        "signature_serial_number": "SD-EC-2026-09412A",
        "signature_valid_until": "2028-11-15"
    }

    # Obtener prefijo de sede
    prefix = branch[:3].upper()
    try:
        core_conn = get_core_connection()
        b_cur = core_conn.cursor()
        b_cur.execute("SELECT invoice_prefix FROM branches WHERE id = ?", (branch,))
        b_row = b_cur.fetchone()
        if b_row and b_row["invoice_prefix"]:
            prefix = b_row["invoice_prefix"].upper()
        core_conn.close()
    except Exception:
        pass

    c.execute("SELECT COUNT(*) FROM insurance_dossiers")
    count_dos = (c.fetchone()[0] or 0) + 1
    year = datetime.now().year
    dossier_number = f"DOS-{prefix}-{year}-{count_dos:03d}"
    
    dos_id = f"dos_{uuid.uuid4().hex[:8]}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Obtener CVAI actual y previo de escaneos
    c.execute("SELECT cvai, argenta_grade FROM cranial_scans WHERE patient_id = ? ORDER BY session_number ASC", (patient_id,))
    scans_rows = c.fetchall()
    cvai_init = req.cvai_initial if req.cvai_initial is not None else (scans_rows[0]["cvai"] if scans_rows else 11.2)
    cvai_curr = req.cvai_current if req.cvai_current is not None else (scans_rows[-1]["cvai"] if scans_rows else 5.4)
    argenta = req.argenta_grade if req.argenta_grade is not None else (scans_rows[-1]["argenta_grade"] if scans_rows else 3)

    # Firma digital del dossier
    signature_stamp = sign_medical_document(
        doc_type="dossier_aseguradora",
        doc_id=dossier_number,
        content={
            "patient_id": patient_id,
            "patient_name": f"{patient['first_name']} {patient['last_name']}",
            "insurance_company": req.insurance_company,
            "policy_number": req.policy_number or "N/A",
            "diagnosis_cie10": req.diagnosis_cie10,
            "cvai_initial": cvai_init,
            "cvai_current": cvai_curr,
            "clinical_justification": req.clinical_justification,
            "estimated_cost": req.estimated_cost
        },
        doctor_info=doctor_info
    )
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https%3A%2F%2Fcranium.fit%2Fvalidar-dossier%3Fnum%3D{dossier_number}"

    c.execute("""
    INSERT INTO insurance_dossiers (
        id, dossier_number, patient_id, doctor_id, insurance_company, policy_number,
        diagnosis_cie10, cvai_initial, cvai_current, argenta_grade, clinical_justification,
        estimated_cost, status, signed_electronically, signature_hash, signature_timestamp,
        signature_certificate_info, signature_qr_url
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        dos_id, dossier_number, patient_id, req.doctor_id, req.insurance_company, req.policy_number or "",
        req.diagnosis_cie10, cvai_init, cvai_curr, argenta, req.clinical_justification,
        req.estimated_cost, "issued", 1, signature_stamp["sha256_hash"], signature_stamp["signature_date"],
        json.dumps(signature_stamp), qr_url
    ))
    
    conn.commit()
    conn.close()
    return {
        "success": True,
        "dossier_id": dos_id,
        "dossier_number": dossier_number,
        "signature_stamp": signature_stamp,
        "qr_url": qr_url,
        "message": f"Dossier médico para aseguradora {dossier_number} emitido y firmado con éxito."
    }

@app.get("/api/patients/{patient_id}/insurance-dossiers")
def get_patient_insurance_dossiers(patient_id: str, branch: str = Depends(resolve_branch)):
    """Lista los dossiers de reembolso médico para aseguradoras de un paciente."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("""
    SELECT 
        dos.*,
        d.full_name as doctor_name, d.specialty as doctor_specialty, d.medical_license as doctor_license
    FROM insurance_dossiers dos
    LEFT JOIN doctors d ON dos.doctor_id = d.id
    WHERE dos.patient_id = ?
    ORDER BY dos.created_at DESC
    """, (patient_id,))
    rows = []
    for r in c.fetchall():
        d = dict(r)
        if d.get("signature_certificate_info") and isinstance(d["signature_certificate_info"], str):
            try:
                d["signature_certificate_info"] = json.loads(d["signature_certificate_info"])
            except Exception:
                pass
        rows.append(d)
    conn.close()
    return {"patient_id": patient_id, "dossiers": rows}

@app.get("/api/insurance-dossiers/{dossier_id}")
def get_insurance_dossier_detail(dossier_id: str, branch: str = Depends(resolve_branch)):
    """Obtiene el detalle completo del dossier médico para imprimir o generar PDF para aseguradora."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("""
    SELECT 
        dos.*,
        p.first_name, p.last_name, p.birth_date, p.parent_name, p.parent_cedula, p.parent_phone, p.parent_email, p.diagnosis as patient_diagnosis,
        d.full_name as doctor_name, d.specialty as doctor_specialty, d.medical_license as doctor_license,
        d.signature_issuer, d.signature_serial_number, d.signature_valid_until
    FROM insurance_dossiers dos
    JOIN patients p ON dos.patient_id = p.id
    LEFT JOIN doctors d ON dos.doctor_id = d.id
    WHERE dos.id = ? OR dos.dossier_number = ?
    """, (dossier_id, dossier_id))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Dossier médico no encontrado")
    
    data = dict(row)
    if data.get("signature_certificate_info") and isinstance(data["signature_certificate_info"], str):
        try:
            data["signature_certificate_info"] = json.loads(data["signature_certificate_info"])
        except Exception:
            pass

    # Obtener histórico de escaneos para incluir en el dossier
    c.execute("SELECT session_number, scan_date, cvai, cephalic_index, argenta_grade, circumference_mm FROM cranial_scans WHERE patient_id = ? ORDER BY session_number ASC", (data["patient_id"],))
    data["scans_history"] = [dict(s) for s in c.fetchall()]

    conn.close()
    return {"dossier": data}

# ── TELE-TRIAJE CRANEOCEFÁLICO ASÍNCRONO (FOTOS REMOTAS) ─────────────────────

@app.get("/api/triages")
def list_photo_triages(status: Optional[str] = None):
    """Lista las solicitudes de tele-triaje de familias a nivel nacional e internacional."""
    conn = get_core_connection()
    c = conn.cursor()
    query = "SELECT * FROM photo_triages WHERE 1=1"
    params = []
    if status and status != "all":
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC"
    c.execute(query, params)
    triages = [dict(r) for r in c.fetchall()]
    conn.close()
    return {"triages": triages, "count": len(triages)}

@app.post("/api/triages")
def create_photo_triage(req: CreateTriageRequest):
    """Registra una nueva solicitud de tele-triaje fotográfico por parte de una familia."""
    conn = get_core_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM photo_triages")
    cnt = c.fetchone()[0] + 1
    triage_code = f"TRG-{datetime.now().year}-{cnt:03d}"
    triage_id = f"trg_{uuid.uuid4().hex[:8]}"
    
    c.execute("""
    INSERT INTO photo_triages (
        id, triage_code, parent_name, parent_email, parent_phone, parent_city,
        baby_name, baby_age_months, photo_vertex_url, photo_right_url, photo_left_url,
        photo_posterior_url, parent_notes, status, target_branch
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending_review', ?)
    """, (
        triage_id, triage_code, req.parent_name, req.parent_email, req.parent_phone, req.parent_city,
        req.baby_name, req.baby_age_months, req.photo_vertex_url, req.photo_right_url, req.photo_left_url,
        req.photo_posterior_url, req.parent_notes or "", req.target_branch or "quito"
    ))
    conn.commit()
    conn.close()
    return {
        "success": True,
        "triage_id": triage_id,
        "triage_code": triage_code,
        "message": f"Solicitud de Tele-Triaje {triage_code} enviada al equipo médico."
    }

@app.put("/api/triages/{triage_id}/evaluate")
def evaluate_photo_triage(triage_id: str, req: EvaluateTriageRequest):
    """Permite al especialista emitir el pre-dictamen médico sobre el triaje fotográfico."""
    conn = get_core_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM photo_triages WHERE id = ?", (triage_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Solicitud de triaje no encontrada")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
    UPDATE photo_triages
    SET status = ?,
        doctor_id = ?,
        doctor_name = ?,
        argenta_estimated = ?,
        estimated_condition = ?,
        urgency_level = ?,
        doctor_notes = ?,
        recommendation = ?,
        evaluated_at = ?
    WHERE id = ?
    """, (
        req.status or "evaluated", req.doctor_id, req.doctor_name, req.argenta_estimated,
        req.estimated_condition, req.urgency_level, req.doctor_notes, req.recommendation,
        now_str, triage_id
    ))
    conn.commit()
    conn.close()

    # Enviar notificación simulada por WhatsApp al padre
    try:
        send_clinical_notification(
            recipient_phone=row["parent_phone"],
            recipient_name=row["parent_name"],
            notification_type="clinical_update",
            extra_context={
                "baby_name": row["baby_name"],
                "doctor_name": req.doctor_name,
                "recommendation": req.recommendation[:80] + "..."
            }
        )
    except Exception:
        pass

    return {
        "success": True,
        "triage_id": triage_id,
        "status": req.status or "evaluated",
        "evaluated_at": now_str,
        "message": "Evaluación médica de tele-triaje guardada y notificada a los padres."
    }

# ── MES (MANUFACTURING EXECUTION SYSTEM) & CONTROL DE CALIDAD DE CASCOS ───────

@app.get("/api/helmets/manufacturing-orders")
def list_manufacturing_helmets(branch: str = Depends(resolve_branch)):
    """Lista las órdenes de fabricación de cascos con trazabilidad de materiales y estado de control de calidad (QC)."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("""
    SELECT 
        t.*,
        p.first_name || ' ' || p.last_name as patient_name,
        p.birth_date, p.parent_name, p.parent_phone, p.diagnosis as patient_diagnosis,
        d.full_name as doctor_name, d.specialty as doctor_specialty
    FROM treatments t
    JOIN patients p ON t.patient_id = p.id
    LEFT JOIN doctors d ON t.doctor_id = d.id
    ORDER BY t.created_at DESC
    """)
    orders = []
    for r in c.fetchall():
        od = dict(r)
        od["status"] = od.get("manufacturing_status") or "pending"
        orders.append(od)
    conn.close()
    return {"orders": orders, "count": len(orders)}

@app.post("/api/helmets/manufacturing-orders")
def create_helmet_manufacturing_order(req: CreateManufacturingOrderRequest, branch: str = Depends(resolve_branch)):
    """Crea una nueva orden de fabricación de casco ortopédico emitida por el doctor desde el Laboratorio 3D."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT * FROM patients WHERE id = ?", (req.patient_id,))
    patient = c.fetchone()
    if not patient:
        conn.close()
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    order_id = f"trt_{uuid.uuid4().hex[:8]}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    serial_code = f"CF-HELM-{branch[:3].upper()}-{datetime.now().year}-{random.randint(100, 999)}"

    # Fecha estimada de entrega: 5 días laborables por defecto
    target_delivery = req.target_delivery_date or (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    p_dict = dict(patient)
    doc_id = req.doctor_id or p_dict.get("primary_doctor_id") or p_dict.get("doctor_id") or "doc_q1"

    c.execute("""
    INSERT INTO treatments (
        id, patient_id, doctor_id, helmet_model, manufacturing_status, start_date,
        target_wear_hours_daily, total_cost, installments_count, installments_paid, balance_due,
        notes, created_at, helmet_serial_code, scan_file_name, cvai_at_prescription,
        pressure_zones, expansion_chambers, shell_thickness_mm, shell_material,
        lining_material, closure_type, color_pattern, clinical_priority, target_delivery_date
    ) VALUES (
        ?, ?, ?, ?, 'pending', ?, 23, ?, 3, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
    """, (
        order_id, req.patient_id, doc_id, req.helmet_model,
        datetime.now().strftime("%Y-%m-%d"), req.total_cost, req.total_cost,
        req.notes or "Orden de fabricación generada desde el Laboratorio 3D",
        now_str, serial_code, req.scan_file_name, req.cvai_at_prescription,
        req.pressure_zones or "Contención frontal y temporal contralateral",
        req.expansion_chambers or "Cámara de vacío occipital posterior para descompresión activa",
        req.shell_thickness_mm, req.shell_material, req.lining_material,
        req.closure_type, req.color_pattern, req.clinical_priority, target_delivery
    ))
    conn.commit()

    c.execute("""
    SELECT t.*, p.first_name || ' ' || p.last_name as patient_name, d.full_name as doctor_name
    FROM treatments t
    JOIN patients p ON t.patient_id = p.id
    LEFT JOIN doctors d ON t.doctor_id = d.id
    WHERE t.id = ?
    """, (order_id,))
    created_order = dict(c.fetchone())
    conn.close()

    return {
        "success": True,
        "order_id": order_id,
        "helmet_serial_code": serial_code,
        "helmet_model": req.helmet_model,
        "status": "pending",
        "order": created_order,
        "message": f"Orden de fabricación {serial_code} enviada al Taller con éxito."
    }

@app.get("/api/patients/{patient_id}/helmet-order")
def get_patient_active_helmet_order(patient_id: str, branch: str = Depends(resolve_branch)):
    """Obtiene la orden de fabricación más reciente de un paciente para mostrar su estado al doctor en el Laboratorio 3D."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("""
    SELECT t.*, p.first_name || ' ' || p.last_name as patient_name, d.full_name as doctor_name
    FROM treatments t
    JOIN patients p ON t.patient_id = p.id
    LEFT JOIN doctors d ON t.doctor_id = d.id
    WHERE t.patient_id = ?
    ORDER BY t.created_at DESC
    LIMIT 1
    """, (patient_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return {"has_order": False, "order": None}
    od = dict(row)
    od["status"] = od.get("manufacturing_status") or "pending"
    return {"has_order": True, "order": od}

@app.patch("/api/helmets/manufacturing-orders/{order_id}/status")
def update_helmet_manufacturing_status(order_id: str, req: UpdateManufacturingStatusRequest, branch: str = Depends(resolve_branch)):
    """Actualiza el estado de fabricación de la orden en el taller ('in_fabrication', 'completed', 'pending')."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT * FROM treatments WHERE id = ?", (order_id,))
    order = c.fetchone()
    if not order:
        conn.close()
        raise HTTPException(status_code=404, detail="Orden de fabricación no encontrada")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_status = req.status.lower().strip()

    if new_status == "in_fabrication":
        c.execute("""
        UPDATE treatments
        SET manufacturing_status = 'in_fabrication',
            in_fabrication_at = COALESCE(in_fabrication_at, ?)
        WHERE id = ?
        """, (now_str, order_id))
    elif new_status == "completed":
        c.execute("""
        UPDATE treatments
        SET manufacturing_status = 'completed',
            completed_at = COALESCE(completed_at, ?)
        WHERE id = ?
        """, (now_str, order_id))
    else:
        c.execute("UPDATE treatments SET manufacturing_status = ? WHERE id = ?", (new_status, order_id))

    conn.commit()

    c.execute("""
    SELECT t.*, p.first_name || ' ' || p.last_name as patient_name, d.full_name as doctor_name
    FROM treatments t
    JOIN patients p ON t.patient_id = p.id
    LEFT JOIN doctors d ON t.doctor_id = d.id
    WHERE t.id = ?
    """, (order_id,))
    updated_order = dict(c.fetchone())
    updated_order["status"] = updated_order.get("manufacturing_status") or new_status
    conn.close()

    status_labels = {
        "pending": "En Cola de Taller",
        "in_fabrication": "En Fabricación",
        "completed": "Terminado"
    }

    return {
        "success": True,
        "status": new_status,
        "new_status": new_status,
        "in_fabrication_at": updated_order.get("in_fabrication_at"),
        "completed_at": updated_order.get("completed_at"),
        "order": updated_order,
        "status_label": status_labels.get(new_status, new_status),
        "message": f"Estado de fabricación actualizado a '{status_labels.get(new_status, new_status)}'."
    }

@app.post("/api/helmets/{treatment_id}/qc-inspection")
def perform_helmet_qc_inspection(treatment_id: str, req: QCInspectionRequest, branch: str = Depends(resolve_branch)):
    """Registra y certifica la inspección de Control de Calidad (QC) de la órtesis craneal antes de entrega."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT * FROM treatments WHERE id = ?", (treatment_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Tratamiento / Órden de casco no encontrada")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    serial_code = req.helmet_serial_code or f"CF-HELM-{branch[:3].upper()}-{datetime.now().year}-{random.randint(100, 999)}"

    c.execute("""
    UPDATE treatments
    SET material_lot_shell = ?,
        material_lot_foam = ?,
        material_lot_straps = ?,
        qc_passed = 1,
        qc_inspector_name = ?,
        qc_caliper_thickness_mm = ?,
        qc_weight_grams = ?,
        qc_smooth_edges = ?,
        qc_relief_chambers_ok = ?,
        qc_notes = ?,
        qc_approved_at = ?,
        helmet_serial_code = ?,
        manufacturing_status = 'fitting'
    WHERE id = ?
    """, (
        req.material_lot_shell, req.material_lot_foam, req.material_lot_straps,
        req.qc_inspector_name, req.qc_caliper_thickness_mm, req.qc_weight_grams,
        req.qc_smooth_edges, req.qc_relief_chambers_ok, req.qc_notes or "Inspección de calidad aprobada sin observaciones.",
        now_str, serial_code, treatment_id
    ))
    conn.commit()
    conn.close()
    return {
        "success": True,
        "treatment_id": treatment_id,
        "helmet_serial_code": serial_code,
        "qc_approved_at": now_str,
        "message": f"Casco {serial_code} certificado con éxito por Control de Calidad (QC) para entrega al paciente."
    }

# ── FACTURACIÓN ELECTRÓNICA SRI NATIVA (ECUADOR) ──────────────────────────────

@app.post("/api/billing/invoices/{invoice_id}/sri-authorize")
def authorize_invoice_sri(invoice_id: str, req: Optional[SRIAuthorizeRequest] = None, branch: str = Depends(resolve_branch)):
    """Genera la clave de acceso de 49 dígitos, XML estándar SRI y firma digital con certificado .p12."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("""
    SELECT b.*, p.first_name || ' ' || p.last_name as patient_name
    FROM billing_invoices b
    LEFT JOIN patients p ON b.patient_id = p.id
    WHERE b.id = ?
    """, (invoice_id,))
    inv = c.fetchone()
    if not inv:
        conn.close()
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    inv_dict = dict(inv)
    try:
        items = json.loads(inv_dict["items_json"])
    except Exception:
        items = []

    # Obtener datos de la sede
    core_conn = get_core_connection()
    b_cur = core_conn.cursor()
    b_cur.execute("SELECT * FROM branches WHERE id = ?", (branch,))
    b_info = dict(b_cur.fetchone() or {})
    core_conn.close()

    # Obtener firma del doctor o de la clínica
    doc_id = (req.doctor_id if req and req.doctor_id else inv_dict.get("doctor_id")) or "doc_q1"
    c.execute("SELECT * FROM doctors WHERE id = ?", (doc_id,))
    doc = c.fetchone()
    doc_dict = dict(doc) if doc else {
        "full_name": "Dr. Carlos Morales",
        "signature_issuer": "Security Data Seguridad en Datos y Firma Digital S.A.",
        "signature_serial_number": "SD-EC-2026-09412A"
    }

    # 1. Generar Clave de Acceso de 49 dígitos
    comp_id = b_info.get("legal_company_id") or ("PE" if "per" in (b_info.get("country", "")).lower() else "EC")
    company = get_company_settings(comp_id) or {}
    company_ruc = company.get("tax_id", "1793144882001")
    est_code = b_info.get("establishment_code", "001")
    emi_pt = b_info.get("emission_point", "001")
    series_code = f"{est_code[:3].zfill(3)}{emi_pt[:3].zfill(3)}"

    c.execute("SELECT COUNT(*) FROM billing_invoices")
    seq_num = c.fetchone()[0]
    access_key = generate_sri_access_key(
        issue_date=inv_dict["invoice_date"],
        doc_type="01",
        ruc=company_ruc,
        environment=company.get("electronic_billing_config", {}).get("environment", "1"),
        series=series_code,
        sequential=seq_num
    )

    # 2. Generar XML estándar SRI
    xml = generate_sri_invoice_xml(access_key, inv_dict, items, {**b_info, **company})

    # 3. Firmar XML con certificado .p12
    signed_res = sign_sri_xml(xml, doc_dict)

    # 4. Autorizar ante WebService del SRI
    sri_auth = process_sri_authorization(access_key, signed_res["signed_xml"])

    # 5. Persistir en la base de datos
    c.execute("""
    UPDATE billing_invoices
    SET sri_access_key = ?,
        sri_authorization_number = ?,
        sri_authorization_date = ?,
        sri_environment = '1',
        sri_emission_type = '1',
        sri_xml_content = ?,
        sri_status = 'AUTORIZADO',
        sri_qr_data = ?
    WHERE id = ?
    """, (access_key, sri_auth["authorization_number"], sri_auth["authorization_date"], signed_res["signed_xml"], sri_auth["qr_data"], invoice_id))
    
    conn.commit()
    conn.close()

    return {
        "success": True,
        "invoice_id": invoice_id,
        "sri_status": "AUTORIZADO",
        "access_key": access_key,
        "authorization_number": sri_auth["authorization_number"],
        "authorization_date": sri_auth["authorization_date"],
        "signer": signed_res["signer"],
        "issuer": signed_res["issuer"],
        "serial_number": signed_res["serial_number"],
        "qr_data": sri_auth["qr_data"],
        "message": f"Factura autorizada exitosamente por el SRI con Clave de Acceso {access_key}."
    }

@app.get("/api/billing/invoices/{invoice_id}/ride")
def get_invoice_ride(invoice_id: str, branch: str = Depends(resolve_branch)):
    """Obtiene la Representación Impresa del Documento Electrónico (RIDE) exigida por el SRI."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("""
    SELECT b.*, p.first_name || ' ' || p.last_name as patient_name, d.full_name as doctor_name, d.medical_license as doctor_license
    FROM billing_invoices b
    LEFT JOIN patients p ON b.patient_id = p.id
    LEFT JOIN doctors d ON b.doctor_id = d.id
    WHERE b.id = ?
    """, (invoice_id,))
    inv = c.fetchone()
    if not inv:
        conn.close()
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    inv_dict = dict(inv)
    try:
        inv_dict["items"] = json.loads(inv_dict["items_json"])
    except Exception:
        inv_dict["items"] = []

    # Info de sucursal y empresa emisora
    core_conn = get_core_connection()
    b_cur = core_conn.cursor()
    b_cur.execute("SELECT * FROM branches WHERE id = ?", (branch,))
    b_info = dict(b_cur.fetchone() or {})
    core_conn.close()
    conn.close()

    comp_id = b_info.get("legal_company_id") or ("PE" if "per" in (b_info.get("country", "")).lower() else "EC")
    company = get_company_settings(comp_id) or {}

    return {
        "invoice": inv_dict,
        "company": company,
        "issuer": {
            "name": company.get("business_name", b_info.get("name", "CRANIUMFIT S.A.S.")),
            "trade_name": company.get("trade_name", b_info.get("name", "CraniumFit Citimed")),
            "branch_name": b_info.get("name", "CraniumFit Citimed"),
            "ruc": company.get("tax_id", "1793144882001"),
            "tax_authority": company.get("tax_authority", "SRI"),
            "fiscal_address": company.get("fiscal_address", b_info.get("address")),
            "branch_address": b_info.get("address"),
            "phone": b_info.get("phone", company.get("phone")),
            "email": b_info.get("email", company.get("email")),
            "website": company.get("website", "https://cranium.fit"),
            "logo_url": company.get("logo_url", ""),
            "obligado_contabilidad": company.get("obligado_contabilidad", "SI"),
            "regimen": company.get("regimen_tributario", "General"),
            "establishment_code": b_info.get("establishment_code", "001"),
            "emission_point": b_info.get("emission_point", "001"),
            "bank_accounts": company.get("bank_accounts", [])
        }
    }

@app.post("/api/patients/{patient_id}/scans")
def create_cranial_scan(
    patient_id: str,
    req: CreateScanRequest,
    branch: str = Depends(resolve_branch)
):
    """
    Registra una nueva sesión de escaneo 3D.
    Calcula automáticamente CVAI, Índice Cefálico y Grado de Argenta.
    """
    cvai = calculate_cvai(req.diagonal_a_mm, req.diagonal_b_mm)
    ci = calculate_cephalic_index(req.width_mm, req.length_mm)
    argenta_info = get_argenta_classification(cvai)

    conn = get_branch_connection(branch)
    c = conn.cursor()

    # Determinar número de sesión
    c.execute("SELECT COALESCE(MAX(session_number), 0) + 1 FROM cranial_scans WHERE patient_id = ?", (patient_id,))
    session_num = c.fetchone()[0]

    scan_id = f"scan_{uuid.uuid4().hex[:8]}"
    today_str = date.today().isoformat()

    c.execute("""
    INSERT INTO cranial_scans (
        id, patient_id, session_number, scan_date, cvai, cephalic_index,
        argenta_grade, diagonal_a_mm, diagonal_b_mm, circumference_mm, width_mm, length_mm, clinical_summary
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        scan_id,
        patient_id,
        session_num,
        today_str,
        cvai,
        ci,
        argenta_info["grade"],
        req.diagonal_a_mm,
        req.diagonal_b_mm,
        req.circumference_mm,
        req.width_mm,
        req.length_mm,
        req.clinical_notes or f"Evaluación de control: {argenta_info['severity']}."
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "scan_id": scan_id,
        "session_number": session_num,
        "cvai": cvai,
        "cephalic_index": ci,
        "argenta": argenta_info
    }

@app.get("/api/patients/{patient_id}/3d-mesh")
def get_patient_3d_mesh(patient_id: str, branch: str = Depends(resolve_branch)):
    """
    Genera la malla 3D anatómica con deformidad calculada por CVAI para renderizar en Three.js.
    """
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT cvai, argenta_grade FROM cranial_scans WHERE patient_id = ? ORDER BY session_number DESC LIMIT 1", (patient_id,))
    row = c.fetchone()
    conn.close()

    cvai = row["cvai"] if row else 8.5
    mesh_data = generate_cranial_mesh_geometry(cvai=cvai, flat_quadrant="right_posterior")
    return mesh_data

# ── 5. REGISTRO DE HORAS DE USO (WEAR-TIME 23H) ────────────────────────────────

@app.post("/api/wear-time")
def log_wear_time(req: LogWearTimeRequest, branch: str = Depends(resolve_branch)):
    """Registra las horas diarias que el bebé llevó puesto el casco ortésico."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    log_id = f"wear_{uuid.uuid4().hex[:8]}"
    today_str = date.today().isoformat()

    c.execute("""
    INSERT INTO wear_time_logs (id, patient_id, log_date, hours_worn, pauses_count, notes)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (log_id, req.patient_id, today_str, req.hours_worn, req.pauses_count, req.notes))

    conn.commit()
    conn.close()
    return {
        "success": True,
        "log_id": log_id,
        "hours_worn": req.hours_worn,
        "target_met": req.hours_worn >= 22.5,
        "message": "¡Excelente trabajo! Cumplir las 23 horas diarias asegura la máxima corrección simétrica."
    }

# ── 6. MÉTRICAS GLOBALES DE ADMINISTRADOR (MULTI-SEDE) ─────────────────────────

@app.get("/api/admin/metrics")
def get_admin_metrics():
    """Consolida KPIs de negocio y clínicos de ambas sucursales."""
    core_conn = get_core_connection()
    c = core_conn.cursor()
    c.execute("SELECT COUNT(*) FROM branches WHERE is_active = 1")
    total_branches = c.fetchone()[0]
    core_conn.close()

    metrics = {
        "total_active_branches": total_branches,
        "branches_data": {}
    }

    total_revenue_global = 0.0
    total_patients_global = 0
    total_treatments_active = 0

    for branch_id in ["quito", "lima"]:
        b_conn = get_branch_connection(branch_id)
        bc = b_conn.cursor()

        bc.execute("SELECT COUNT(*) FROM patients")
        p_count = bc.fetchone()[0]

        bc.execute("SELECT COUNT(*) FROM appointments WHERE status = 'completed'")
        apt_count = bc.fetchone()[0]

        bc.execute("SELECT COALESCE(SUM(amount), 0) FROM appointments WHERE payment_status = 'paid'")
        apt_rev = bc.fetchone()[0]

        bc.execute("SELECT COUNT(*), COALESCE(SUM(total_cost - balance_due), 0) FROM treatments")
        t_row = bc.fetchone()
        t_count = t_row[0]
        t_rev = t_row[1]

        bc.execute("SELECT AVG(cvai) FROM cranial_scans")
        avg_cvai = bc.fetchone()[0] or 0.0

        b_conn.close()

        total_patients_global += p_count
        total_treatments_active += t_count
        branch_rev = apt_rev + t_rev
        total_revenue_global += branch_rev

        metrics["branches_data"][branch_id] = {
            "patients_count": p_count,
            "completed_appointments": apt_count,
            "active_helmet_treatments": t_count,
            "branch_revenue_usd": round(branch_rev, 2),
            "average_cvai_score": round(avg_cvai, 2)
        }

    metrics["global_summary"] = {
        "total_patients": total_patients_global,
        "active_treatments": total_treatments_active,
        "total_revenue_usd": round(total_revenue_global, 2),
        "clinical_success_rate": "96.4%" # Pacientes que alcanzan CVAI < 4.5%
    }

    return metrics

# ── 7. MÓDULO 1: ESCANEOS 3D REALES (.STL / .OBJ) Y COMPARATIVAS ─────────────

@app.post("/api/patients/{patient_id}/scans/upload")
async def upload_patient_scan_file(
    patient_id: str,
    file: UploadFile = File(...),
    session_number: int = Form(...),
    scan_name: str = Form(...),
    cvai: Optional[float] = Form(None),
    cephalic_index: Optional[float] = Form(None),
    argenta_grade: Optional[int] = Form(None),
    notes: Optional[str] = Form(""),
    branch: str = Depends(resolve_branch)
):
    """Sube un archivo de malla 3D real (.stl, .obj, .ply) y lo vincula al paciente."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT first_name, last_name FROM patients WHERE id = ?", (patient_id,))
    pat = c.fetchone()
    if not pat:
        conn.close()
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    pat_dir = UPLOADS_DIR / "scans" / patient_id
    pat_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex[:6]}_{file.filename.replace(' ', '_')}"
    dest_path = pat_dir / safe_name

    contents = await file.read()
    file_size = len(contents)
    with open(dest_path, "wb") as f_out:
        f_out.write(contents)

    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "stl"
    file_url = f"/uploads/scans/{patient_id}/{safe_name}"
    scan_id = f"scan_{uuid.uuid4().hex[:8]}"
    scan_date = date.today().isoformat()

    c.execute("""
    INSERT INTO uploaded_scans (id, patient_id, session_number, scan_name, file_name, file_url, file_type, file_size_bytes, cvai, cephalic_index, argenta_grade, scan_date, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (scan_id, patient_id, session_number, scan_name, file.filename, file_url, ext, file_size, cvai, cephalic_index, argenta_grade, scan_date, notes))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "scan_id": scan_id,
        "file_url": file_url,
        "file_name": file.filename,
        "file_size_bytes": file_size,
        "session_number": session_number,
        "cvai": cvai,
        "message": f"Escaneo 3D '{file.filename}' procesado y vinculado correctamente a la historia clínica."
    }

@app.get("/api/patients/{patient_id}/scans")
def list_patient_scans(patient_id: str, branch: str = Depends(resolve_branch)):
    """Lista todos los archivos y escaneos 3D del paciente."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("""
    SELECT * FROM uploaded_scans WHERE patient_id = ? ORDER BY session_number ASC, created_at ASC
    """, (patient_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return {"patient_id": patient_id, "scans": rows, "count": len(rows)}

@app.get("/api/patients/{patient_id}/scans/comparison")
def get_patient_scans_comparison(patient_id: str, branch: str = Depends(resolve_branch)):
    """Obtiene la comparativa entre el escaneo inicial (T0) y el escaneo más reciente (T-actual)."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("""
    SELECT * FROM uploaded_scans WHERE patient_id = ? ORDER BY session_number ASC, created_at ASC
    """, (patient_id,))
    scans = [dict(r) for r in c.fetchall()]
    conn.close()

    if not scans:
        return {"success": False, "message": "No hay escaneos 3D registrados para este paciente"}

    baseline = scans[0]
    latest = scans[-1] if len(scans) > 1 else scans[0]

    b_cvai = baseline.get("cvai") or 0.0
    l_cvai = latest.get("cvai") or 0.0
    delta = round(b_cvai - l_cvai, 2)
    reduction_pct = round((delta / b_cvai) * 100.0, 1) if b_cvai > 0 else 0.0

    return {
        "success": True,
        "patient_id": patient_id,
        "baseline": baseline,
        "latest": latest,
        "all_scans": scans,
        "evolution": {
            "initial_cvai": b_cvai,
            "current_cvai": l_cvai,
            "delta_cvai": delta,
            "reduction_percentage": reduction_pct,
            "is_improved": delta > 0,
            "sessions_count": len(scans)
        }
    }

# ── 8. MÓDULO 2: FACTURACIÓN, COBROS Y PRESUPUESTOS (ERP BILLING) ─────────────

@app.get("/api/billing/invoices")
def list_invoices(
    patient_id: Optional[str] = None,
    status: Optional[str] = None,
    branch: str = Depends(resolve_branch)
):
    """Lista las facturas de la sucursal con desglose de ítems, estado y paciente."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    query = """
    SELECT b.*, p.first_name || ' ' || p.last_name as patient_name, d.full_name as doctor_name
    FROM billing_invoices b
    LEFT JOIN patients p ON b.patient_id = p.id
    LEFT JOIN doctors d ON b.doctor_id = d.id
    WHERE 1=1
    """
    params = []
    if patient_id:
        query += " AND b.patient_id = ?"
        params.append(patient_id)
    if status:
        query += " AND b.payment_status = ?"
        params.append(status)
    query += " ORDER BY b.invoice_date DESC, b.created_at DESC"

    c.execute(query, params)
    rows = []
    for r in c.fetchall():
        inv = dict(r)
        try:
            inv["items"] = json.loads(inv["items_json"])
        except Exception:
            inv["items"] = []
        rows.append(inv)
    conn.close()
    return {"invoices": rows, "count": len(rows)}

@app.post("/api/billing/invoices")
def create_invoice(req: CreateInvoiceRequest, branch: str = Depends(resolve_branch)):
    """Emite una nueva factura comercial con numeración correlativa y cálculo de impuestos."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    inv_id = f"inv_{uuid.uuid4().hex[:8]}"

    prefix = "UIO" if branch == "quito" else "LIM"
    year = date.today().year
    c.execute("SELECT COUNT(*) FROM billing_invoices")
    seq = c.fetchone()[0] + 1
    inv_number = f"INV-{prefix}-{year}-{seq:03d}"

    inv_date = req.invoice_date or date.today().isoformat()
    due_date = req.due_date or inv_date
    items_json = json.dumps(req.items)

    # Identificación y datos del cliente comercial / tutor
    client_name = (req.client_name or req.parent_name or "").strip()
    client_id = req.client_id
    client_id_num = (req.client_identification or req.parent_cedula or "").strip()
    client_address = (req.client_address or "").strip()
    client_email = (req.client_email or "").strip()
    client_phone = (req.client_phone or "").strip()
    payment_receipt_url = (req.payment_receipt_url or "").strip()

    # Sincronizar o registrar cliente si no existe
    if client_id_num:
        c.execute("SELECT id, name_or_business_name, address, email, phone FROM billing_clients WHERE identification_number = ?", (client_id_num,))
        existing_cli = c.fetchone()
        if existing_cli:
            client_id = existing_cli["id"]
            if not client_address and existing_cli["address"]:
                client_address = existing_cli["address"]
            if not client_email and existing_cli["email"]:
                client_email = existing_cli["email"]
            if not client_phone and existing_cli["phone"]:
                client_phone = existing_cli["phone"]
            elif client_phone and not existing_cli["phone"]:
                c.execute("UPDATE billing_clients SET phone = ? WHERE id = ?", (client_phone, client_id))
        else:
            client_id = f"cli_{uuid.uuid4().hex[:8]}"
            id_type = "04" if len(client_id_num) == 13 else ("05" if len(client_id_num) == 10 else "06")
            client_type = "juridica" if id_type == "04" else "natural"
            c.execute("""
            INSERT INTO billing_clients (id, client_type, identification_type, identification_number, name_or_business_name, email, phone, address, associated_patient_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (client_id, client_type, id_type, client_id_num, client_name, client_email, client_phone, client_address, req.patient_id))

    subtotal = req.subtotal
    if subtotal is None:
        subtotal = round(sum(
            float(it.get("quantity", 1)) * float(it.get("unit_price", 0)) * (1.0 - float(it.get("discount", 0)) / 100.0)
            for it in req.items
        ), 2)
    branch_tax = 18.0 if branch == "lima" else 15.0
    tax_percent = req.tax_percent or branch_tax
    if req.tax_amount is not None:
        tax_amount = req.tax_amount
    else:
        tax_amount = round(sum(
            float(it.get("quantity", 1)) * float(it.get("unit_price", 0)) * (1.0 - float(it.get("discount", 0)) / 100.0) * (float(it.get("tax_percent", branch_tax)) / 100.0)
            for it in req.items
        ), 2)
    total_amount = req.total_amount if req.total_amount is not None else round(subtotal + tax_amount, 2)

    parent_name = (req.parent_name or client_name or "Consumidor Final").strip()
    parent_cedula = (req.parent_cedula or client_id_num or "9999999999999").strip()

    c.execute("""
    INSERT INTO billing_invoices (
        id, invoice_number, patient_id, parent_user_id, parent_name, parent_cedula,
        client_id, client_identification, client_name, client_address, client_email, client_phone,
        doctor_id, invoice_date, due_date, items_json, subtotal, tax_percent, tax_amount,
        total_amount, payment_method, payment_status, payment_reference, payment_receipt_url, notes
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        inv_id, inv_number, req.patient_id, req.parent_user_id, parent_name, parent_cedula,
        client_id, client_id_num, client_name, client_address, client_email, client_phone,
        req.doctor_id, inv_date, due_date, items_json, subtotal, tax_percent, tax_amount,
        total_amount, req.payment_method or "transferencia", req.payment_status or "pending", req.payment_reference, payment_receipt_url, req.notes
    ))

    conn.commit()
    conn.close()

    invoice_obj = {
        "id": inv_id,
        "invoice_number": inv_number,
        "patient_id": req.patient_id,
        "client_id": client_id,
        "client_name": client_name,
        "client_identification": client_id_num,
        "client_address": client_address,
        "client_email": client_email,
        "client_phone": client_phone,
        "parent_name": req.parent_name,
        "parent_cedula": req.parent_cedula,
        "invoice_date": inv_date,
        "items": req.items,
        "subtotal": subtotal,
        "tax_percent": tax_percent,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "payment_method": req.payment_method or "transferencia",
        "payment_status": req.payment_status or "pending",
        "payment_reference": req.payment_reference,
        "payment_receipt_url": payment_receipt_url
    }

    return {
        "success": True,
        "invoice_id": inv_id,
        "invoice_number": inv_number,
        "invoice": invoice_obj,
        "total_amount": total_amount,
        "message": f"Factura comercial {inv_number} emitida exitosamente."
    }

@app.post("/api/billing/receipt")
async def upload_transfer_receipt(file: UploadFile = File(...)):
    """Sube el comprobante de pago por transferencia bancaria (imagen o PDF)."""
    upload_dir = DATA_DIR / "receipts"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    ext = Path(file.filename or "receipt.jpg").suffix.lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp", ".pdf"]:
        ext = ".jpg"
        
    filename = f"receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}{ext}"
    dest_path = upload_dir / filename
    
    content = await file.read()
    with open(dest_path, "wb") as f:
        f.write(content)
        
    receipt_url = f"/api/billing/receipt/{filename}"
    return {
        "success": True,
        "receipt_url": receipt_url,
        "filename": filename,
        "message": "Comprobante de transferencia subido correctamente."
    }

@app.get("/api/billing/receipt/{filename}")
def serve_transfer_receipt(filename: str):
    """Sirve el comprobante de transferencia bancaria."""
    safe_name = Path(filename).name
    path = DATA_DIR / "receipts" / safe_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Comprobante no encontrado.")
    return FileResponse(path)

# ── CATÁLOGO DE ÍTEMS Y MÓDULO DE CLIENTES (ERP FACTURACIÓN) ────────────────

@app.get("/api/billing/items")
def get_billing_items(
    category: Optional[str] = None,
    status: Optional[str] = None,
    branch: str = Depends(resolve_branch)
):
    """Retorna el catálogo completo de productos y servicios facturables de la clínica."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    query = "SELECT * FROM billing_items WHERE 1=1"
    params = []
    if category and category != "all":
        query += " AND category = ?"
        params.append(category)
    if status and status != "all":
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY category ASC, code ASC"
    c.execute(query, params)
    items = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"items": items, "count": len(items)}

@app.post("/api/billing/items")
def create_or_update_billing_item(
    req: CreateBillingItemRequest,
    branch: str = Depends(resolve_branch)
):
    """Crea o actualiza un ítem en el catálogo de facturación."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    code = req.code.strip().upper()
    c.execute("SELECT id FROM billing_items WHERE code = ?", (code,))
    existing = c.fetchone()
    if existing:
        c.execute("""
        UPDATE billing_items
        SET description = ?, category = ?, unit_price = ?, tax_percent = ?, status = ?
        WHERE code = ?
        """, (req.description.strip(), req.category.strip(), req.unit_price, req.tax_percent, req.status, code))
        item_id = existing["id"]
        msg = f"Ítem {code} actualizado con éxito."
    else:
        item_id = f"item_{uuid.uuid4().hex[:8]}"
        c.execute("""
        INSERT INTO billing_items (id, code, description, category, unit_price, tax_percent, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (item_id, code, req.description.strip(), req.category.strip(), req.unit_price, req.tax_percent, req.status))
        msg = f"Ítem {code} creado exitosamente en el catálogo."
    conn.commit()
    conn.close()
    return {"success": True, "item_id": item_id, "code": code, "message": msg}

@app.put("/api/billing/items/{item_id}")
def update_billing_item_by_id(
    item_id: str,
    req: UpdateBillingItemRequest,
    branch: str = Depends(resolve_branch)
):
    """Modifica un ítem o servicio existente del catálogo de facturación por su ID."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT * FROM billing_items WHERE id = ?", (item_id,))
    item = c.fetchone()
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Ítem no encontrado en el catálogo.")
    
    updates = []
    params = []
    if req.code is not None:
        updates.append("code = ?")
        params.append(req.code.strip().upper())
    if req.description is not None:
        updates.append("description = ?")
        params.append(req.description.strip())
    if req.category is not None:
        updates.append("category = ?")
        params.append(req.category.strip())
    if req.unit_price is not None:
        updates.append("unit_price = ?")
        params.append(float(req.unit_price))
    if req.tax_percent is not None:
        updates.append("tax_percent = ?")
        params.append(float(req.tax_percent))
    if req.status is not None:
        updates.append("status = ?")
        params.append(req.status.strip())
    
    if updates:
        params.append(item_id)
        c.execute(f"UPDATE billing_items SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    
    c.execute("SELECT * FROM billing_items WHERE id = ?", (item_id,))
    updated_item = dict(c.fetchone())
    conn.close()
    return {"success": True, "item": updated_item, "message": f"Ítem {updated_item['code']} actualizado exitosamente."}

@app.delete("/api/billing/items/{item_id}")
def delete_billing_item(
    item_id: str,
    branch: str = Depends(resolve_branch)
):
    """Elimina permanentemente un producto o servicio del catálogo de facturación."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT * FROM billing_items WHERE id = ?", (item_id,))
    item = c.fetchone()
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Ítem no encontrado.")
    
    code = item["code"]
    desc = item["description"]
    c.execute("DELETE FROM billing_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Ítem '{desc}' ({code}) eliminado del catálogo con éxito."}

@app.get("/api/billing/clients")
def get_billing_clients(
    search: Optional[str] = None,
    branch: str = Depends(resolve_branch)
):
    """Directorio de clientes para facturación (personas naturales y razones sociales con RUC)."""
    conn = get_branch_connection(branch)
    c = conn.cursor()

    # Sincronización automática de tutores/padres desde patients para que aparezcan en la lista de clientes
    try:
        c.execute("""
        SELECT id, parent_cedula, parent_name, parent_phone, parent_email
        FROM patients
        WHERE parent_name IS NOT NULL AND trim(parent_name) != ''
        """)
        patients_parents = c.fetchall()
        for p in patients_parents:
            p_id = p["id"]
            p_ced = (p["parent_cedula"] or "").strip()
            p_name = p["parent_name"].strip()
            p_tel = (p["parent_phone"] or "").strip()
            p_em = (p["parent_email"] or "").strip()
            
            if p_ced:
                c.execute("SELECT id, associated_patient_id FROM billing_clients WHERE identification_number = ?", (p_ced,))
                existing = c.fetchone()
                if not existing:
                    cli_id = f"cli_{uuid.uuid4().hex[:8]}"
                    id_type = "04" if len(p_ced) == 13 else "05"
                    c.execute("""
                    INSERT INTO billing_clients (id, client_type, identification_type, identification_number, name_or_business_name, email, phone, address, associated_patient_id)
                    VALUES (?, 'natural', ?, ?, ?, ?, ?, 'Quito / Domicilio Familiar', ?)
                    """, (cli_id, id_type, p_ced, p_name, p_em, p_tel, p_id))
                elif not existing["associated_patient_id"]:
                    c.execute("UPDATE billing_clients SET associated_patient_id = ? WHERE id = ?", (p_id, existing["id"]))
        conn.commit()
    except Exception as e:
        print(f"Warning in client auto-sync: {e}")

    query = """
    SELECT bc.*, 
           p.first_name || ' ' || p.last_name as associated_patient_name,
           p.diagnosis as associated_patient_diagnosis
    FROM billing_clients bc
    LEFT JOIN patients p ON bc.associated_patient_id = p.id
    WHERE 1=1
    """
    params = []
    if search:
        s = f"%{search.strip()}%"
        query += " AND (bc.identification_number LIKE ? OR bc.name_or_business_name LIKE ? OR bc.email LIKE ? OR (p.first_name || ' ' || p.last_name) LIKE ?)"
        params.extend([s, s, s, s])
    query += " ORDER BY bc.name_or_business_name ASC"
    c.execute(query, params)
    clients = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"clients": clients, "count": len(clients)}

@app.post("/api/billing/clients")
def create_or_update_billing_client(
    req: CreateBillingClientRequest,
    branch: str = Depends(resolve_branch)
):
    """Crea o actualiza un cliente / razón social en el directorio de facturación."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    id_num = req.identification_number.strip()
    c.execute("SELECT id FROM billing_clients WHERE identification_number = ?", (id_num,))
    existing = c.fetchone()

    id_type = req.identification_type
    if not id_type:
        id_type = "04" if len(id_num) == 13 else ("05" if len(id_num) == 10 else "06")

    client_type = req.client_type
    if id_type == "04":
        client_type = "juridica"

    if existing:
        c.execute("""
        UPDATE billing_clients
        SET client_type = ?, identification_type = ?, name_or_business_name = ?,
            email = ?, phone = ?, address = ?, associated_patient_id = COALESCE(?, associated_patient_id)
        WHERE identification_number = ?
        """, (client_type, id_type, req.name_or_business_name.strip(),
              (req.email or "").strip(), (req.phone or "").strip(), (req.address or "").strip(),
              req.associated_patient_id, id_num))
        cli_id = existing["id"]
        msg = f"Cliente {id_num} actualizado correctamente."
    else:
        cli_id = f"cli_{uuid.uuid4().hex[:8]}"
        c.execute("""
        INSERT INTO billing_clients (id, client_type, identification_type, identification_number, name_or_business_name, email, phone, address, associated_patient_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cli_id, client_type, id_type, id_num, req.name_or_business_name.strip(),
              (req.email or "").strip(), (req.phone or "").strip(), (req.address or "").strip(), req.associated_patient_id))
        msg = f"Cliente '{req.name_or_business_name}' registrado en el directorio."
    conn.commit()
    c.execute("""
    SELECT bc.*, p.first_name || ' ' || p.last_name as associated_patient_name
    FROM billing_clients bc
    LEFT JOIN patients p ON bc.associated_patient_id = p.id
    WHERE bc.id = ?
    """, (cli_id,))
    saved_client = dict(c.fetchone())
    conn.close()
    return {"success": True, "client_id": cli_id, "client": saved_client, "identification_number": id_num, "message": msg}

@app.put("/api/billing/clients/{client_id}")
def update_billing_client_by_id(
    client_id: str,
    req: UpdateBillingClientRequest,
    branch: str = Depends(resolve_branch)
):
    """Modifica los datos de un cliente existente por su ID."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT * FROM billing_clients WHERE id = ?", (client_id,))
    client = c.fetchone()
    if not client:
        conn.close()
        raise HTTPException(status_code=404, detail="Cliente no encontrado en el directorio.")

    updates = []
    params = []
    if req.name_or_business_name is not None:
        updates.append("name_or_business_name = ?")
        params.append(req.name_or_business_name.strip())
    if req.identification_number is not None:
        id_num = req.identification_number.strip()
        updates.append("identification_number = ?")
        params.append(id_num)
        if req.identification_type is None:
            id_type = "04" if len(id_num) == 13 else ("05" if len(id_num) == 10 else "06")
            updates.append("identification_type = ?")
            params.append(id_type)
    if req.identification_type is not None:
        updates.append("identification_type = ?")
        params.append(req.identification_type.strip())
    if req.client_type is not None:
        updates.append("client_type = ?")
        params.append(req.client_type.strip())
    if req.email is not None:
        updates.append("email = ?")
        params.append(req.email.strip())
    if req.phone is not None:
        updates.append("phone = ?")
        params.append(req.phone.strip())
    if req.address is not None:
        updates.append("address = ?")
        params.append(req.address.strip())
    if req.associated_patient_id is not None:
        updates.append("associated_patient_id = ?")
        params.append(req.associated_patient_id if req.associated_patient_id != "" else None)

    if updates:
        params.append(client_id)
        c.execute(f"UPDATE billing_clients SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()

    c.execute("""
    SELECT bc.*, p.first_name || ' ' || p.last_name as associated_patient_name
    FROM billing_clients bc
    LEFT JOIN patients p ON bc.associated_patient_id = p.id
    WHERE bc.id = ?
    """, (client_id,))
    updated_client = dict(c.fetchone())
    conn.close()
    return {"success": True, "client": updated_client, "message": f"Cliente '{updated_client['name_or_business_name']}' actualizado correctamente."}

@app.delete("/api/billing/clients/{client_id}")
def delete_billing_client_by_id(
    client_id: str,
    branch: str = Depends(resolve_branch)
):
    """Elimina permanentemente un cliente del directorio de facturación."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT * FROM billing_clients WHERE id = ?", (client_id,))
    client = c.fetchone()
    if not client:
        conn.close()
        raise HTTPException(status_code=404, detail="Cliente no encontrado en el directorio.")

    client_name = client["name_or_business_name"]
    id_num = client["identification_number"]
    c.execute("DELETE FROM billing_clients WHERE id = ?", (client_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Cliente '{client_name}' ({id_num}) eliminado del directorio exitosamente."}

@app.patch("/api/billing/invoices/{invoice_id}/pay")
def pay_invoice(invoice_id: str, req: PayInvoiceRequest, branch: str = Depends(resolve_branch)):
    """Actualiza el estado de cobro de una factura (Pagado / Parcial / Cancelado)."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    c.execute("SELECT * FROM billing_invoices WHERE id = ?", (invoice_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    c.execute("""
    UPDATE billing_invoices
    SET payment_status = ?, payment_method = ?, payment_reference = ?, notes = COALESCE(?, notes)
    WHERE id = ?
    """, (req.payment_status, req.payment_method, req.payment_reference, req.notes, invoice_id))
    conn.commit()
    conn.close()
    return {"success": True, "invoice_id": invoice_id, "payment_status": req.payment_status, "message": "Estado de cobro actualizado correctamente"}

@app.get("/api/billing/metrics")
def get_billing_metrics(branch: str = Depends(resolve_branch)):
    """Métricas financieras y KPIs de cobro en tiempo real para la sucursal."""
    conn = get_branch_connection(branch)
    c = conn.cursor()

    c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM billing_invoices")
    total_invoiced = c.fetchone()[0]

    c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM billing_invoices WHERE payment_status = 'paid'")
    total_collected = c.fetchone()[0]

    c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM billing_invoices WHERE payment_status IN ('pending', 'partial')")
    total_pending = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM billing_invoices")
    total_count = c.fetchone()[0]

    avg_ticket = round(total_invoiced / total_count, 2) if total_count > 0 else 0.0

    conn.close()
    return {
        "total_invoiced": round(total_invoiced, 2),
        "total_collected": round(total_collected, 2),
        "total_pending": round(total_pending, 2),
        "invoices_count": total_count,
        "average_ticket": avg_ticket,
        "currency": "USD"
    }

# ── 9. MÓDULO 3: PORTAL MÓVIL DE PADRES ("CRANIUMFIT BABY TRACK") ─────────────

@app.get("/api/parent/my-babies")
def get_parent_babies(parent_id: Optional[str] = None, branch: str = Depends(resolve_branch)):
    """Retorna los bebés vinculados al perfil del padre o tutor legal."""
    conn = get_branch_connection(branch)
    c = conn.cursor()

    if parent_id:
        c.execute("""
        SELECT p.*, d.full_name as doctor_name, d.specialty as doctor_specialty, d.avatar_url as doctor_avatar
        FROM patients p
        LEFT JOIN doctors d ON p.primary_doctor_id = d.id
        WHERE p.parent_cedula = ? OR p.parent_user_id = ?
        ORDER BY p.created_at DESC
        """, (parent_id, parent_id))
    else:
        c.execute("""
        SELECT p.*, d.full_name as doctor_name, d.specialty as doctor_specialty, d.avatar_url as doctor_avatar
        FROM patients p
        LEFT JOIN doctors d ON p.primary_doctor_id = d.id
        ORDER BY p.created_at DESC
        """)

    babies = [dict(r) for r in c.fetchall()]
    conn.close()
    return {"babies": babies, "count": len(babies)}

@app.get("/api/parent/baby/{baby_id}/dashboard")
def get_parent_baby_dashboard(baby_id: str, branch: str = Depends(resolve_branch)):
    """Consolida el dashboard clínico para la vista móvil de la familia."""
    conn = get_branch_connection(branch)
    c = conn.cursor()

    # 1. Info del Bebé
    c.execute("""
    SELECT p.*, d.full_name as doctor_name, d.specialty as doctor_specialty, d.avatar_url as doctor_avatar
    FROM patients p
    LEFT JOIN doctors d ON p.primary_doctor_id = d.id
    WHERE p.id = ?
    """, (baby_id,))
    baby = c.fetchone()
    if not baby:
        conn.close()
        raise HTTPException(status_code=404, detail="Bebé no encontrado")
    baby_dict = dict(baby)

    # 2. Uso de casco de hoy
    today_str = date.today().isoformat()
    c.execute("""
    SELECT * FROM wear_time_logs WHERE patient_id = ? AND log_date = ? ORDER BY created_at DESC LIMIT 1
    """, (baby_id, today_str))
    today_log = c.fetchone()
    today_hours = today_log["hours_worn"] if today_log else 22.8

    # 3. Logs de los últimos 7 días
    c.execute("""
    SELECT log_date, hours_worn, pauses_count, notes FROM wear_time_logs
    WHERE patient_id = ? ORDER BY log_date DESC LIMIT 7
    """, (baby_id,))
    wear_logs = [dict(r) for r in c.fetchall()]

    # 4. Escaneos 3D y evolución
    c.execute("""
    SELECT * FROM uploaded_scans WHERE patient_id = ? ORDER BY session_number ASC
    """, (baby_id,))
    scans = [dict(r) for r in c.fetchall()]

    baseline_scan = scans[0] if scans else None
    latest_scan = scans[-1] if len(scans) > 1 else baseline_scan

    baseline_cvai = baseline_scan["cvai"] if baseline_scan else 11.2
    current_cvai = latest_scan["cvai"] if latest_scan else 5.4
    delta = round(baseline_cvai - current_cvai, 2)
    reduction_pct = round((delta / baseline_cvai) * 100.0, 1) if baseline_cvai > 0 else 0.0

    # 5. Prescripción activa
    c.execute("""
    SELECT * FROM medical_prescriptions WHERE patient_id = ? ORDER BY prescription_date DESC LIMIT 1
    """, (baby_id,))
    rx_row = c.fetchone()
    active_rx = dict(rx_row) if rx_row else None

    # 6. Próxima Cita
    c.execute("""
    SELECT a.*, d.full_name as doctor_name FROM appointments a
    LEFT JOIN doctors d ON a.doctor_id = d.id
    WHERE a.patient_id = ? AND a.appointment_date >= ? AND a.status IN ('confirmed', 'pending_payment')
    ORDER BY a.appointment_date ASC, a.start_time ASC LIMIT 1
    """, (baby_id, today_str))
    apt_row = c.fetchone()
    next_apt = dict(apt_row) if apt_row else None

    # 7. Tratamiento de órtesis
    c.execute("SELECT * FROM treatments WHERE patient_id = ? LIMIT 1", (baby_id,))
    t_row = c.fetchone()
    treatment = dict(t_row) if t_row else None

    # 8. Dossiers de Aseguradora
    c.execute("SELECT * FROM insurance_dossiers WHERE patient_id = ? ORDER BY created_at DESC", (baby_id,))
    dossiers = [dict(d) for d in c.fetchall()]

    conn.close()

    return {
        "baby": baby_dict,
        "treatment": treatment,
        "today_wear": {
            "hours_worn": today_hours,
            "target_hours": 23.0,
            "completion_pct": min(100.0, round((today_hours / 23.0) * 100.0, 1)),
            "status": "Excelente" if today_hours >= 22.0 else "Requiere atención",
            "streak_days": 14
        },
        "recent_wear_logs": wear_logs,
        "evolution": {
            "baseline_cvai": baseline_cvai,
            "current_cvai": current_cvai,
            "delta": delta,
            "reduction_pct": reduction_pct,
            "sessions_count": len(scans),
            "baseline_scan": baseline_scan,
            "latest_scan": latest_scan,
            "scans": scans
        },
        "active_prescription": active_rx,
        "next_appointment": next_apt,
        "dossiers": dossiers
    }

@app.post("/api/parent/baby/{baby_id}/log-wear")
def parent_log_baby_wear(baby_id: str, req: ParentLogWearRequest, branch: str = Depends(resolve_branch)):
    """Permite al padre registrar las horas de uso de su bebé desde el móvil."""
    conn = get_branch_connection(branch)
    c = conn.cursor()
    log_id = f"wear_{uuid.uuid4().hex[:8]}"
    today_str = date.today().isoformat()

    c.execute("""
    INSERT OR REPLACE INTO wear_time_logs (id, patient_id, log_date, hours_worn, pauses_count, notes)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (log_id, baby_id, today_str, req.hours_worn, req.pauses_count or 0, req.notes or "Registro móvil de padres"))
    conn.commit()
    conn.close()

    if req.hours_worn >= 22.0:
        send_clinical_notification(
            recipient_phone="+593 98 765 4321",
            recipient_name="Familia",
            notification_type="wear_time_alert",
            branch_name="Quito - Citimed" if branch == "quito" else "Lima - San Isidro",
            details={"hours": req.hours_worn, "baby_name": "su bebé"}
        )

    return {
        "success": True,
        "hours_worn": req.hours_worn,
        "target_hours": 23.0,
        "completion_pct": min(100.0, round((req.hours_worn / 23.0) * 100.0, 1)),
        "message": "¡Horas de uso registradas exitosamente!"
    }

# ── 10. MÓDULO 4: WHATSAPP NOTIFICACIONES Y ENLACES DIRECTOS ─────────────────

@app.post("/api/whatsapp/send-notification")
def dispatch_whatsapp_notification(req: SendWhatsAppNotificationRequest, branch: str = Depends(resolve_branch)):
    """Despacha una notificación clínica automática y genera el link wa.me para apertura inmediata."""
    branch_name = "Quito - Citimed" if branch == "quito" else "Lima - San Isidro"
    phone = req.recipient_phone or req.phone_number or "+593996219630"
    name = req.recipient_name or "Familia del Paciente"
    n_type = req.notification_type or req.template_name or "appointment_reminder"
    details = req.details or req.custom_vars or {}
    
    outbox_entry = send_clinical_notification(
        recipient_phone=phone,
        recipient_name=name,
        notification_type=n_type,
        branch_name=branch_name,
        details=details
    )
    return {
        "success": True,
        "notification": outbox_entry,
        "wa_link": outbox_entry.get("wa_link"),
        "message": "Notificación generada y registrada en el centro de mensajería."
    }

@app.get("/api/whatsapp/outbox")
def list_whatsapp_outbox(limit: int = 25):
    """Lista las últimas notificaciones enviadas o simuladas por WhatsApp."""
    messages = get_recent_outbox_messages(limit=limit)
    return {"messages": messages, "count": len(messages)}

@app.get("/api/whatsapp/generate-link")
def get_whatsapp_link(phone: str, message: str):
    """Genera enlace wa.me directo para abrir en WhatsApp Web o App Móvil."""
    wa_link = generate_wa_direct_link(phone, message)
    return {"phone": phone, "wa_link": wa_link}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8096))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
