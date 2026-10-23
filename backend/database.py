"""
database.py — Motor de Base de Datos Multi-Sede para CraniumFit
==============================================================
Implementa el patrón Database-per-Branch:
- core.db: Usuarios globales, catálogo de sucursales y autenticación.
- quito.db: Pacientes, doctores, citas, historiales 3D y tratamientos de Quito (Citimed).
- lima.db: Pacientes, doctores, citas, historiales 3D y tratamientos de Lima.
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CORE_DB_PATH = DATA_DIR / "cranium_core.db"
QUITO_DB_PATH = DATA_DIR / "cranium_quito.db"
LIMA_DB_PATH = DATA_DIR / "cranium_lima.db"

BRANCH_DBS = {
    "quito": QUITO_DB_PATH,
    "lima": LIMA_DB_PATH
}

def get_core_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(CORE_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def get_branch_connection(branch_id: str) -> sqlite3.Connection:
    branch = branch_id.lower().strip()
    db_path = DATA_DIR / f"cranium_{branch}.db"
    BRANCH_DBS[branch] = db_path
    if not db_path.exists():
        _init_branch_db(branch, f"CraniumFit {branch.capitalize()}")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def get_all_branches() -> List[Dict[str, Any]]:
    conn = get_core_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM branches WHERE is_active = 1 ORDER BY created_at ASC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def create_branch_record(data: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_core_connection()
    c = conn.cursor()
    b_id = data["id"].lower().strip().replace(" ", "_")
    country = data.get("country", "Ecuador")
    default_company = "PE" if "per" in country.lower() else "EC"
    c.execute("""
    INSERT INTO branches (
        id, name, city, country, address, phone, email, tax_percent, currency, invoice_prefix,
        establishment_code, emission_point, peru_series_invoice, peru_series_boleta, legal_company_id, is_active
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        b_id,
        data["name"],
        data["city"],
        country,
        data["address"],
        data["phone"],
        data["email"],
        data.get("tax_percent", 18.0 if default_company == "PE" else 15.0),
        data.get("currency", "PEN" if default_company == "PE" else "USD"),
        data.get("invoice_prefix", b_id[:3].upper()),
        data.get("establishment_code", "0001" if default_company == "PE" else "001"),
        data.get("emission_point", "001"),
        data.get("peru_series_invoice", "F001"),
        data.get("peru_series_boleta", "B001"),
        data.get("legal_company_id", default_company),
        data.get("is_active", 1)
    ))
    conn.commit()
    conn.close()
    
    # Inicializar automáticamente la base de datos de la nueva sede
    _init_branch_db(b_id, data["name"])
    return data

def update_branch_record(branch_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_core_connection()
    c = conn.cursor()
    c.execute("""
    UPDATE branches
    SET name = COALESCE(?, name),
        city = COALESCE(?, city),
        country = COALESCE(?, country),
        address = COALESCE(?, address),
        phone = COALESCE(?, phone),
        email = COALESCE(?, email),
        tax_percent = COALESCE(?, tax_percent),
        currency = COALESCE(?, currency),
        invoice_prefix = COALESCE(?, invoice_prefix),
        establishment_code = COALESCE(?, establishment_code),
        emission_point = COALESCE(?, emission_point),
        peru_series_invoice = COALESCE(?, peru_series_invoice),
        peru_series_boleta = COALESCE(?, peru_series_boleta),
        legal_company_id = COALESCE(?, legal_company_id),
        is_active = COALESCE(?, is_active)
    WHERE id = ?
    """, (
        data.get("name"),
        data.get("city"),
        data.get("country"),
        data.get("address"),
        data.get("phone"),
        data.get("email"),
        data.get("tax_percent"),
        data.get("currency"),
        data.get("invoice_prefix"),
        data.get("establishment_code"),
        data.get("emission_point"),
        data.get("peru_series_invoice"),
        data.get("peru_series_boleta"),
        data.get("legal_company_id"),
        data.get("is_active"),
        branch_id
    ))
    conn.commit()
    conn.close()
    return data

def delete_branch_record(branch_id: str) -> bool:
    conn = get_core_connection()
    c = conn.cursor()
    c.execute("UPDATE branches SET is_active = 0 WHERE id = ?", (branch_id,))
    conn.commit()
    conn.close()
    return True

# ── FUNCIONES DE CONFIGURACIÓN DE EMPRESA (SRI / SUNAT) ──────────────────────

def get_all_company_settings() -> List[Dict[str, Any]]:
    conn = get_core_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM company_settings ORDER BY id ASC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    for r in rows:
        try:
            r["bank_accounts"] = json.loads(r.get("bank_accounts_json") or "[]")
        except Exception:
            r["bank_accounts"] = []
        try:
            r["electronic_billing_config"] = json.loads(r.get("electronic_billing_config_json") or "{}")
        except Exception:
            r["electronic_billing_config"] = {}
    return rows

def get_company_settings(company_id: str = "EC") -> Optional[Dict[str, Any]]:
    conn = get_core_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM company_settings WHERE id = ?", (company_id.upper().strip(),))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    res = dict(row)
    try:
        res["bank_accounts"] = json.loads(res.get("bank_accounts_json") or "[]")
    except Exception:
        res["bank_accounts"] = []
    try:
        res["electronic_billing_config"] = json.loads(res.get("electronic_billing_config_json") or "{}")
    except Exception:
        res["electronic_billing_config"] = {}
    return res

def update_company_settings(company_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_core_connection()
    c = conn.cursor()
    cid = company_id.upper().strip()
    
    bank_acc = data.get("bank_accounts")
    bank_acc_json = json.dumps(bank_acc, ensure_ascii=False) if bank_acc is not None else None
    
    eb_cfg = data.get("electronic_billing_config")
    eb_cfg_json = json.dumps(eb_cfg, ensure_ascii=False) if eb_cfg is not None else None

    c.execute("""
    UPDATE company_settings
    SET business_name = COALESCE(?, business_name),
        trade_name = COALESCE(?, trade_name),
        tax_id = COALESCE(?, tax_id),
        legal_rep_name = COALESCE(?, legal_rep_name),
        legal_rep_id = COALESCE(?, legal_rep_id),
        fiscal_address = COALESCE(?, fiscal_address),
        phone = COALESCE(?, phone),
        email = COALESCE(?, email),
        website = COALESCE(?, website),
        logo_url = COALESCE(?, logo_url),
        obligado_contabilidad = COALESCE(?, obligado_contabilidad),
        regimen_tributario = COALESCE(?, regimen_tributario),
        special_taxpayer_resolution = COALESCE(?, special_taxpayer_resolution),
        retention_agent_resolution = COALESCE(?, retention_agent_resolution),
        bank_accounts_json = COALESCE(?, bank_accounts_json),
        electronic_billing_config_json = COALESCE(?, electronic_billing_config_json),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (
        data.get("business_name"),
        data.get("trade_name"),
        data.get("tax_id"),
        data.get("legal_rep_name"),
        data.get("legal_rep_id"),
        data.get("fiscal_address"),
        data.get("phone"),
        data.get("email"),
        data.get("website"),
        data.get("logo_url"),
        data.get("obligado_contabilidad"),
        data.get("regimen_tributario"),
        data.get("special_taxpayer_resolution"),
        data.get("retention_agent_resolution"),
        bank_acc_json,
        eb_cfg_json,
        cid
    ))
    conn.commit()
    conn.close()
    return get_company_settings(cid) or {}

def init_all_databases():
    """Inicializa esquemas y semillas en todas las bases de datos si no existen."""
    _init_core_db()
    _init_branch_db("quito", "Quito - Citimed")
    _init_branch_db("lima", "Lima - San Isidro")
    print("✅ [CraniumFit DB] Todas las bases de datos multi-sede inicializadas correctamente.")

def _init_core_db():
    conn = get_core_connection()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS branches (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        country TEXT NOT NULL,
        address TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT NOT NULL,
        tax_percent REAL DEFAULT 15.0,
        currency TEXT DEFAULT 'USD',
        invoice_prefix TEXT DEFAULT 'UIO',
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS global_users (
        id TEXT PRIMARY KEY,
        email TEXT,
        cedula TEXT UNIQUE,
        password_hash TEXT,
        full_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        role TEXT NOT NULL, -- 'superadmin', 'doctor', 'secretary', 'parent'
        default_branch TEXT NOT NULL,
        assigned_doctor_ids TEXT, -- JSON array de IDs de doctores: '["doc_q1", "doc_q2"]'
        status TEXT DEFAULT 'active', -- 'active', 'pending_activation', 'suspended'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS otp_verifications (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        phone TEXT NOT NULL,
        cedula TEXT NOT NULL,
        code TEXT NOT NULL,
        purpose TEXT NOT NULL, -- 'account_activation', 'password_reset'
        expires_at TIMESTAMP NOT NULL,
        is_used INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS photo_triages (
        id TEXT PRIMARY KEY,
        triage_code TEXT NOT NULL,
        parent_name TEXT NOT NULL,
        parent_email TEXT NOT NULL,
        parent_phone TEXT NOT NULL,
        parent_city TEXT NOT NULL,
        baby_name TEXT NOT NULL,
        baby_age_months REAL NOT NULL,
        photo_vertex_url TEXT,
        photo_right_url TEXT,
        photo_left_url TEXT,
        photo_posterior_url TEXT,
        parent_notes TEXT,
        status TEXT DEFAULT 'pending_review', -- 'pending_review', 'evaluated', 'candidate_in_person', 'mild_observation', 'discarded'
        doctor_id TEXT,
        doctor_name TEXT,
        target_branch TEXT DEFAULT 'quito',
        argenta_estimated INTEGER,
        estimated_condition TEXT,
        urgency_level TEXT DEFAULT 'moderada', -- 'baja', 'moderada', 'alta'
        doctor_notes TEXT,
        recommendation TEXT,
        evaluated_at TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS company_settings (
        id TEXT PRIMARY KEY, -- 'EC', 'PE'
        country TEXT NOT NULL,
        tax_authority TEXT NOT NULL,
        business_name TEXT NOT NULL,
        trade_name TEXT NOT NULL,
        tax_id TEXT NOT NULL,
        legal_rep_name TEXT,
        legal_rep_id TEXT,
        fiscal_address TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        website TEXT,
        logo_url TEXT,
        obligado_contabilidad TEXT DEFAULT 'SI',
        regimen_tributario TEXT DEFAULT 'General',
        special_taxpayer_resolution TEXT DEFAULT '',
        retention_agent_resolution TEXT DEFAULT '',
        bank_accounts_json TEXT DEFAULT '[]',
        electronic_billing_config_json TEXT DEFAULT '{}',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Migración de columnas en branches si no existían
    c.execute("PRAGMA table_info(branches)")
    b_cols = [row[1] for row in c.fetchall()]
    if "tax_percent" not in b_cols:
        c.execute("ALTER TABLE branches ADD COLUMN tax_percent REAL DEFAULT 15.0")
    if "currency" not in b_cols:
        c.execute("ALTER TABLE branches ADD COLUMN currency TEXT DEFAULT 'USD'")
    if "invoice_prefix" not in b_cols:
        c.execute("ALTER TABLE branches ADD COLUMN invoice_prefix TEXT DEFAULT 'UIO'")
    if "establishment_code" not in b_cols:
        c.execute("ALTER TABLE branches ADD COLUMN establishment_code TEXT DEFAULT '001'")
    if "emission_point" not in b_cols:
        c.execute("ALTER TABLE branches ADD COLUMN emission_point TEXT DEFAULT '001'")
    if "peru_series_invoice" not in b_cols:
        c.execute("ALTER TABLE branches ADD COLUMN peru_series_invoice TEXT DEFAULT 'F001'")
    if "peru_series_boleta" not in b_cols:
        c.execute("ALTER TABLE branches ADD COLUMN peru_series_boleta TEXT DEFAULT 'B001'")
    if "legal_company_id" not in b_cols:
        c.execute("ALTER TABLE branches ADD COLUMN legal_company_id TEXT DEFAULT 'EC'")

    # Migración de columnas en global_users si no existían
    c.execute("PRAGMA table_info(global_users)")
    existing_cols = [row[1] for row in c.fetchall()]
    if "cedula" not in existing_cols:
        c.execute("ALTER TABLE global_users ADD COLUMN cedula TEXT")
    if "assigned_doctor_ids" not in existing_cols:
        c.execute("ALTER TABLE global_users ADD COLUMN assigned_doctor_ids TEXT")
    if "status" not in existing_cols:
        c.execute("ALTER TABLE global_users ADD COLUMN status TEXT DEFAULT 'active'")

    # Semillas de sucursales
    c.execute("SELECT COUNT(*) FROM branches")
    if c.fetchone()[0] == 0:
        c.executemany("""
        INSERT INTO branches (
            id, name, city, country, address, phone, email, tax_percent, currency, invoice_prefix,
            establishment_code, emission_point, peru_series_invoice, peru_series_boleta, legal_company_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            ("quito", "CraniumFit Citimed", "Quito", "Ecuador", "Av. Mariana de Jesús y Nuño de Valderrama, Edificio Citimed, Cons. 402", "+593 99 621 9630", "quito@cranium.fit", 15.0, "USD", "UIO", "001", "001", "F001", "B001", "EC"),
            ("lima", "CraniumFit San Isidro", "Lima", "Perú", "Av. Javier Prado Este 1520, Torre Médica, Cons. 601", "+51 940 012 643", "lima@cranium.fit", 18.0, "PEN", "LIM", "0001", "001", "F001", "B001", "PE")
        ])
    else:
        c.execute("UPDATE branches SET tax_percent = 15.0, currency = 'USD', invoice_prefix = 'UIO', establishment_code = '001', emission_point = '001', legal_company_id = 'EC' WHERE id = 'quito'")
        c.execute("UPDATE branches SET tax_percent = 18.0, currency = 'PEN', invoice_prefix = 'LIM', establishment_code = '0001', emission_point = '001', peru_series_invoice = 'F001', peru_series_boleta = 'B001', legal_company_id = 'PE' WHERE id = 'lima'")

    # Semillas de Configuración de Empresa (Ecuador SRI y Perú SUNAT)
    c.execute("SELECT COUNT(*) FROM company_settings WHERE id = 'EC'")
    if c.fetchone()[0] == 0:
        c.execute("""
        INSERT INTO company_settings (
            id, country, tax_authority, business_name, trade_name, tax_id,
            legal_rep_name, legal_rep_id, fiscal_address, phone, email, website,
            logo_url, obligado_contabilidad, regimen_tributario, special_taxpayer_resolution,
            retention_agent_resolution, bank_accounts_json, electronic_billing_config_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'EC', 'Ecuador', 'SRI', 'CRANIUMFIT S.A.S.', 'CraniumFit Centro de Ortesis Craneal 3D', '1793144882001',
            'Dr. Carlos Morales', '1712345678', 'Av. Mariana de Jesús y Nuño de Valderrama, Edificio Citimed, Cons. 402, Quito, Ecuador',
            '+593 99 621 9630', 'administracion@cranium.fit', 'https://cranium.fit',
            'https://cranium.fit/assets/brand/logo-craniumfit.png', 'SI', 'General', 'Resolución NAC-DNCRASC20-00000001',
            'Resolución Nro. NAC-DNCRASC20-00000001',
            json.dumps([
                {
                    "bank_name": "Banco Pichincha",
                    "account_type": "Corriente",
                    "account_number": "2100234567",
                    "holder_name": "CraniumFit S.A.S.",
                    "holder_id": "1793144882001",
                    "currency": "USD",
                    "is_default": True
                },
                {
                    "bank_name": "Banco de Guayaquil",
                    "account_type": "Ahorros",
                    "account_number": "1140987654",
                    "holder_name": "CraniumFit S.A.S.",
                    "holder_id": "1793144882001",
                    "currency": "USD",
                    "is_default": False
                }
            ], ensure_ascii=False),
            json.dumps({
                "environment": "1",
                "emission_type": "1",
                "signature_file": "firma_craniumfit.p12",
                "signature_password": "",
                "establishment_code": "001",
                "emission_point": "001"
            }, ensure_ascii=False)
        ))

    c.execute("SELECT COUNT(*) FROM company_settings WHERE id = 'PE'")
    if c.fetchone()[0] == 0:
        c.execute("""
        INSERT INTO company_settings (
            id, country, tax_authority, business_name, trade_name, tax_id,
            legal_rep_name, legal_rep_id, fiscal_address, phone, email, website,
            logo_url, obligado_contabilidad, regimen_tributario, special_taxpayer_resolution,
            retention_agent_resolution, bank_accounts_json, electronic_billing_config_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'PE', 'Perú', 'SUNAT', 'CRANIUMFIT PERÚ S.A.C.', 'CraniumFit Perú — Ortesis Pediátrica', '20608912345',
            'Dr. Carlos Morales', '09876543', 'Av. Javier Prado Este 2465, Torre Médica San Borja, Lima, Perú',
            '+51 987 654 321', 'lima@cranium.fit', 'https://cranium.fit',
            'https://cranium.fit/assets/brand/logo-craniumfit.png', 'SI', 'MYPE Tributario', '', '',
            json.dumps([
                {
                    "bank_name": "BCP - Banco de Crédito del Perú",
                    "account_type": "Corriente Soles",
                    "account_number": "193-98765432-0-12",
                    "cci": "002-193-009876543200-12",
                    "holder_name": "CraniumFit Perú S.A.C.",
                    "holder_id": "20608912345",
                    "currency": "PEN",
                    "is_default": True
                },
                {
                    "bank_name": "BBVA Perú",
                    "account_type": "Ahorros Dólares",
                    "account_number": "0011-0123-0200987654",
                    "cci": "011-123-000200987654-21",
                    "holder_name": "CraniumFit Perú S.A.C.",
                    "holder_id": "20608912345",
                    "currency": "USD",
                    "is_default": False
                }
            ], ensure_ascii=False),
            json.dumps({
                "sol_user": "MODDATOS",
                "sol_pass": "moddatos",
                "certificate_file": "certificado_sunat.pfx",
                "certificate_password": "",
                "environment": "beta",
                "ose_provider": "direct_sunat",
                "series_invoice": "F001",
                "series_boleta": "B001",
                "anexo_code": "0000"
            }, ensure_ascii=False)
        ))

    # Semillas de usuarios globales
    c.execute("SELECT COUNT(*) FROM global_users")
    if c.fetchone()[0] == 0:
        c.executemany("""
        INSERT INTO global_users (id, email, cedula, password_hash, full_name, phone, role, default_branch, assigned_doctor_ids, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            ("usr_admin", "admin@cranium.fit", "1710000001", "admin123", "Ing. Dirección General", "+593 99 111 2222", "superadmin", "quito", '["doc_q1", "doc_q2", "doc_l1"]', "active"),
            ("usr_doc_quito_1", "dr.morales@cranium.fit", "1710000002", "doc123", "Dr. Carlos Morales", "+593 99 621 9631", "doctor", "quito", None, "active"),
            ("usr_doc_quito_2", "dra.castro@cranium.fit", "1710000003", "doc123", "Dra. Valeria Castro", "+593 99 621 9632", "doctor", "quito", None, "active"),
            ("usr_doc_lima_1", "dr.castillo@cranium.fit", "1710000004", "doc123", "Dr. Miguel Castillo", "+51 940 012 644", "doctor", "lima", None, "active"),
            ("usr_sec_quito", "recepcion.quito@cranium.fit", "1710000005", "sec123", "Ana Belén Pérez", "+593 99 621 9630", "secretary", "quito", '["doc_q1", "doc_q2"]', "active"),
            ("usr_sec_lima", "recepcion.lima@cranium.fit", "1710000006", "sec123", "Lucía Mendoza", "+51 940 012 643", "secretary", "lima", '["doc_l1"]', "active"),
            ("usr_parent_1", "familia.torres@gmail.com", "1718899221", "padre123", "María Fernanda López", "+593 98 765 4321", "parent", "quito", None, "active")
        ])
    else:
        # Asegurar cédulas y asignaciones para usuarios existentes
        seed_updates = [
            ("usr_admin", "1710000001", '["doc_q1", "doc_q2", "doc_l1"]'),
            ("usr_doc_quito_1", "1710000002", None),
            ("usr_doc_quito_2", "1710000003", None),
            ("usr_doc_lima_1", "1710000004", None),
            ("usr_sec_quito", "1710000005", '["doc_q1", "doc_q2"]'),
            ("usr_sec_lima", "1710000006", '["doc_l1"]'),
            ("usr_parent_1", "1718899221", None)
        ]
        for uid, ced, doc_ids in seed_updates:
            c.execute("UPDATE global_users SET cedula = COALESCE(cedula, ?), assigned_doctor_ids = COALESCE(assigned_doctor_ids, ?), status = COALESCE(status, 'active') WHERE id = ?", (ced, doc_ids, uid))

    # Semillas de Solicitudes de Tele-Triaje Craneofacial
    c.execute("SELECT COUNT(*) FROM photo_triages")
    if c.fetchone()[0] == 0:
        c.executemany("""
        INSERT INTO photo_triages (id, triage_code, parent_name, parent_email, parent_phone, parent_city, baby_name, baby_age_months, photo_vertex_url, photo_right_url, photo_left_url, photo_posterior_url, parent_notes, status, doctor_id, doctor_name, target_branch, argenta_estimated, estimated_condition, urgency_level, doctor_notes, recommendation, evaluated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (
                "trg_cuenca_1", "TRG-2026-001", "Gabriela Cordero", "gaby.cordero@gmail.com", "+593 99 123 4567", "Cuenca",
                "Emiliano Vázquez", 5.2,
                "https://images.unsplash.com/photo-1544126592-807ade215a0b?w=600&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1519689680058-324335c77eba?w=600&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1555252333-9f8e92e65df9?w=600&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1502086223501-7ea6ecd79368?w=600&auto=format&fit=crop&q=80",
                "Vivimos en Cuenca. Notamos la cabecita de Emiliano aplanada en la parte de atrás derecha desde los 3 meses. El pediatra local nos recomendó consultar en CraniumFit.",
                "pending_review", None, None, "quito", None, None, "moderada", None, None, None
            ),
            (
                "trg_manta_1", "TRG-2026-002", "Jorge Macías", "jorge.macias@hotmail.com", "+593 98 444 8899", "Manta",
                "Thiago Macías", 4.5,
                "https://images.unsplash.com/photo-1544126592-807ade215a0b?w=600&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1519689680058-324335c77eba?w=600&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1555252333-9f8e92e65df9?w=600&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1502086223501-7ea6ecd79368?w=600&auto=format&fit=crop&q=80",
                "Nació por cesárea. Siempre duerme cargado hacia su lado derecho y la oreja derecha se ve más adelantada que la izquierda.",
                "evaluated", "doc_q1", "Dr. Carlos Morales", "quito", 3, "Plagiocefalia Posicional Severa Derecha", "alta",
                "Evidente asimetría cuadrante posterior derecho con adelantamiento de pabellón auricular y compensación frontal. Por edad (4.5 meses) es el momento óptimo para corrección ortésica dinámica.",
                "Candidato prioritario para escaneo 3D fotogramétrico y fabricación de casco en sede Quito. Se recomienda coordinar cita en próximos 7 a 10 días.",
                "2026-10-21 16:40:00"
            ),
            (
                "trg_machala_1", "TRG-2026-003", "Patricia Aguilar", "p.aguilar@yahoo.com", "+593 97 222 3311", "Machala",
                "Mia Romero", 3.2,
                "https://images.unsplash.com/photo-1544126592-807ade215a0b?w=600&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1519689680058-324335c77eba?w=600&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1555252333-9f8e92e65df9?w=600&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1502086223501-7ea6ecd79368?w=600&auto=format&fit=crop&q=80",
                "Sospecha leve de aplanamiento. Queremos saber si requiere casco o solo ejercicios.",
                "evaluated", "doc_q2", "Dra. Valeria Castro", "quito", 1, "Asimetría Leve Transitoria", "baja",
                "Asimetría leve menor a 5mm sin desviación biauricular. Excelente pronóstico con terapia física.",
                "Protocolo de Tummy Time supervisado 15 min x 4 veces al día y cojín ergonómico. Control fotográfico en 30 días sin requerir desplazamiento inicial.",
                "2026-10-21 14:15:00"
            )
        ])

    conn.commit()
    conn.close()

def _init_branch_db(branch_id: str, branch_name: str):
    conn = get_branch_connection(branch_id)
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS doctors (
        id TEXT PRIMARY KEY,
        global_user_id TEXT NOT NULL,
        full_name TEXT NOT NULL,
        specialty TEXT NOT NULL,
        medical_license TEXT,
        consultation_fee REAL DEFAULT 50.00,
        appointment_duration_min INTEGER DEFAULT 30,
        bio TEXT,
        avatar_url TEXT,
        signature_p12_path TEXT,
        signature_p12_filename TEXT,
        signature_issuer TEXT,
        signature_serial_number TEXT,
        signature_valid_until TEXT,
        signature_status TEXT DEFAULT 'not_configured',
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS doctor_schedules (
        id TEXT PRIMARY KEY,
        doctor_id TEXT REFERENCES doctors(id),
        day_of_week INTEGER NOT NULL, -- 1=Lunes a 6=Sábado
        start_time TEXT NOT NULL,     -- '08:30'
        end_time TEXT NOT NULL,       -- '17:00'
        slot_duration_min INTEGER DEFAULT 30
    );

    CREATE TABLE IF NOT EXISTS patients (
        id TEXT PRIMARY KEY,
        parent_user_id TEXT NOT NULL,
        parent_cedula TEXT,
        parent_name TEXT NOT NULL,
        parent_phone TEXT NOT NULL,
        parent_email TEXT NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        birth_date TEXT NOT NULL,
        sex TEXT DEFAULT 'M',
        gestational_weeks INTEGER DEFAULT 40,
        delivery_type TEXT DEFAULT 'Parto Vaginal',
        primary_doctor_id TEXT REFERENCES doctors(id),
        diagnosis TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS appointments (
        id TEXT PRIMARY KEY,
        patient_id TEXT REFERENCES patients(id),
        doctor_id TEXT REFERENCES doctors(id),
        appointment_date TEXT NOT NULL, -- YYYY-MM-DD
        start_time TEXT NOT NULL,       -- HH:MM
        end_time TEXT NOT NULL,         -- HH:MM
        appointment_type TEXT NOT NULL, -- 'evaluacion_3d', 'control_quincenal', 'fisioterapia'
        status TEXT NOT NULL,           -- 'pending_payment', 'confirmed', 'in_waiting_room', 'in_consultation', 'completed', 'cancelled'
        amount REAL NOT NULL,
        payment_method TEXT,            -- 'tarjeta_online', 'transferencia', 'efectivo'
        payment_status TEXT NOT NULL,   -- 'unpaid', 'paid', 'verified'
        payment_ref TEXT,
        clinical_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS cranial_scans (
        id TEXT PRIMARY KEY,
        patient_id TEXT REFERENCES patients(id),
        session_number INTEGER NOT NULL,
        scan_date TEXT NOT NULL,
        cvai REAL NOT NULL,               -- Cranial Vault Asymmetry Index (%)
        cephalic_index REAL NOT NULL,     -- Índice Cefálico (%)
        argenta_grade INTEGER NOT NULL,   -- 1 a 5
        diagonal_a_mm REAL NOT NULL,
        diagonal_b_mm REAL NOT NULL,
        circumference_mm REAL NOT NULL,
        width_mm REAL NOT NULL,
        length_mm REAL NOT NULL,
        clinical_summary TEXT,
        mesh_url TEXT,
        report_pdf_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS treatments (
        id TEXT PRIMARY KEY,
        patient_id TEXT REFERENCES patients(id),
        doctor_id TEXT REFERENCES doctors(id),
        helmet_model TEXT NOT NULL,       -- 'CraniumFit Pro-Dynamic 3D'
        manufacturing_status TEXT NOT NULL, -- 'scan_approved', 'cad_design', 'in_3d_print', 'fitting', 'delivered'
        start_date TEXT,
        target_wear_hours_daily INTEGER DEFAULT 23,
        total_cost REAL NOT NULL,
        installments_count INTEGER DEFAULT 3,
        installments_paid INTEGER DEFAULT 1,
        balance_due REAL NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS wear_time_logs (
        id TEXT PRIMARY KEY,
        patient_id TEXT REFERENCES patients(id),
        log_date TEXT NOT NULL,
        hours_worn REAL NOT NULL,
        pauses_count INTEGER DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS medical_consultations (
        id TEXT PRIMARY KEY,
        patient_id TEXT REFERENCES patients(id),
        doctor_id TEXT REFERENCES doctors(id),
        consultation_date TEXT NOT NULL,
        reason_for_visit TEXT NOT NULL,
        vital_signs TEXT,
        cranial_eval TEXT,
        diagnosis TEXT NOT NULL,
        clinical_evolution TEXT,
        treatment_plan TEXT,
        next_appointment_rec TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS medical_exams (
        id TEXT PRIMARY KEY,
        patient_id TEXT REFERENCES patients(id),
        doctor_id TEXT REFERENCES doctors(id),
        exam_date TEXT NOT NULL,
        exam_type TEXT NOT NULL,
        cvai REAL,
        cephalic_index REAL,
        argenta_grade INTEGER,
        measurements TEXT,
        results_summary TEXT NOT NULL,
        recommendations TEXT,
        file_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS medical_prescriptions (
        id TEXT PRIMARY KEY,
        prescription_number TEXT,
        patient_id TEXT REFERENCES patients(id),
        doctor_id TEXT REFERENCES doctors(id),
        consultation_id TEXT,
        prescription_date TEXT NOT NULL,
        medications_rx TEXT,
        orthotic_prescription TEXT,
        physical_therapy_orders TEXT,
        special_instructions TEXT,
        valid_until TEXT,
        signed_electronically INTEGER DEFAULT 1,
        signature_hash TEXT,
        signature_timestamp TEXT,
        signature_certificate_info TEXT,
        signature_qr_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS medical_certificates (
        id TEXT PRIMARY KEY,
        certificate_number TEXT NOT NULL,
        patient_id TEXT REFERENCES patients(id),
        doctor_id TEXT REFERENCES doctors(id),
        consultation_id TEXT,
        issue_date TEXT NOT NULL,
        certificate_type TEXT NOT NULL, -- 'reposo_medico', 'aptitud_escolar', 'uso_ortesis_aerolinea', 'constancia_atencion'
        diagnosis_cie10 TEXT NOT NULL,
        clinical_findings TEXT,
        rest_days INTEGER DEFAULT 0,
        valid_until TEXT,
        formal_statement TEXT NOT NULL,
        signed_electronically INTEGER DEFAULT 1,
        signature_hash TEXT,
        signature_timestamp TEXT,
        signature_certificate_info TEXT,
        signature_qr_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS uploaded_scans (
        id TEXT PRIMARY KEY,
        patient_id TEXT REFERENCES patients(id),
        session_number INTEGER NOT NULL,
        scan_name TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_url TEXT NOT NULL,
        file_type TEXT NOT NULL, -- 'stl', 'obj', 'ply'
        file_size_bytes INTEGER DEFAULT 0,
        cvai REAL,
        cephalic_index REAL,
        argenta_grade INTEGER,
        scan_date TEXT NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS insurance_dossiers (
        id TEXT PRIMARY KEY,
        dossier_number TEXT NOT NULL,
        patient_id TEXT REFERENCES patients(id),
        doctor_id TEXT REFERENCES doctors(id),
        insurance_company TEXT NOT NULL,
        policy_number TEXT,
        diagnosis_cie10 TEXT NOT NULL,
        cvai_initial REAL,
        cvai_current REAL,
        argenta_grade INTEGER,
        clinical_justification TEXT NOT NULL,
        estimated_cost REAL DEFAULT 1850.00,
        status TEXT DEFAULT 'issued', -- 'issued', 'submitted', 'approved', 'rejected'
        signed_electronically INTEGER DEFAULT 1,
        signature_hash TEXT,
        signature_timestamp TEXT,
        signature_certificate_info TEXT,
        signature_qr_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS billing_invoices (
        id TEXT PRIMARY KEY,
        invoice_number TEXT NOT NULL,
        patient_id TEXT REFERENCES patients(id),
        parent_user_id TEXT,
        parent_name TEXT NOT NULL,
        parent_cedula TEXT,
        doctor_id TEXT REFERENCES doctors(id),
        invoice_date TEXT NOT NULL,
        due_date TEXT,
        items_json TEXT NOT NULL,
        subtotal REAL NOT NULL,
        tax_percent REAL DEFAULT 15.0,
        tax_amount REAL NOT NULL,
        total_amount REAL NOT NULL,
        payment_method TEXT DEFAULT 'transferencia', -- 'transferencia', 'tarjeta', 'efectivo'
        payment_status TEXT DEFAULT 'pending',       -- 'paid', 'partial', 'pending', 'cancelled'
        payment_reference TEXT,
        notes TEXT,
        sri_access_key TEXT,
        sri_authorization_number TEXT,
        sri_authorization_date TEXT,
        sri_environment TEXT DEFAULT '1',
        sri_emission_type TEXT DEFAULT '1',
        sri_xml_content TEXT,
        sri_status TEXT DEFAULT 'pending',           -- 'pending', 'signed', 'AUTORIZADO', 'rejected'
        sri_qr_data TEXT,
        client_id TEXT,
        client_identification TEXT,
        client_name TEXT,
        client_address TEXT,
        client_email TEXT,
        client_phone TEXT,
        payment_receipt_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS billing_clients (
        id TEXT PRIMARY KEY,
        client_type TEXT DEFAULT 'natural', -- 'natural', 'juridica'
        identification_type TEXT DEFAULT '05', -- '05' Cédula, '04' RUC, '06' Pasaporte
        identification_number TEXT NOT NULL,
        name_or_business_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        address TEXT,
        associated_patient_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS billing_items (
        id TEXT PRIMARY KEY,
        code TEXT NOT NULL UNIQUE,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        unit_price REAL NOT NULL,
        tax_percent REAL DEFAULT 15.0,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Migración de columnas en patients si la tabla ya existía
    c.execute("PRAGMA table_info(patients)")
    p_cols = [row[1] for row in c.fetchall()]
    if "parent_cedula" not in p_cols:
        c.execute("ALTER TABLE patients ADD COLUMN parent_cedula TEXT")
    if "sex" not in p_cols:
        c.execute("ALTER TABLE patients ADD COLUMN sex TEXT DEFAULT 'M'")
    if "patient_dni" not in p_cols:
        c.execute("ALTER TABLE patients ADD COLUMN patient_dni TEXT")
    if "photo_url" not in p_cols:
        c.execute("ALTER TABLE patients ADD COLUMN photo_url TEXT")
    
    c.execute("UPDATE patients SET parent_cedula = '1718899221' WHERE id = 'pat_lucas' AND parent_cedula IS NULL")
    c.execute("UPDATE patients SET parent_cedula = '1719944332' WHERE id = 'pat_sofia' AND parent_cedula IS NULL")
    c.execute("UPDATE patients SET parent_cedula = '1720055119' WHERE id = 'pat_mateo' AND parent_cedula IS NULL")
    c.execute("UPDATE patients SET parent_cedula = '1799999999' WHERE parent_cedula IS NULL")

    c.execute("UPDATE patients SET patient_dni = '1758921104', photo_url = 'https://images.unsplash.com/photo-1544126592-807ade215a0b?w=200&auto=format&fit=crop&q=80' WHERE id = 'pat_lucas' AND (patient_dni IS NULL OR photo_url IS NULL)")
    c.execute("UPDATE patients SET patient_dni = '1759932215', photo_url = 'https://images.unsplash.com/photo-1519689680058-324335c77eba?w=200&auto=format&fit=crop&q=80' WHERE id = 'pat_sofia' AND (patient_dni IS NULL OR photo_url IS NULL)")
    c.execute("UPDATE patients SET patient_dni = '1760043326', photo_url = 'https://images.unsplash.com/photo-1502086223501-7ea6ecd79368?w=200&auto=format&fit=crop&q=80' WHERE id = 'pat_mateo' AND (patient_dni IS NULL OR photo_url IS NULL)")

    # Migración de columnas en doctors (Firma Electrónica .p12)
    c.execute("PRAGMA table_info(doctors)")
    d_cols = [row[1] for row in c.fetchall()]
    if "signature_p12_path" not in d_cols:
        c.execute("ALTER TABLE doctors ADD COLUMN signature_p12_path TEXT")
    if "signature_p12_filename" not in d_cols:
        c.execute("ALTER TABLE doctors ADD COLUMN signature_p12_filename TEXT")
    if "signature_issuer" not in d_cols:
        c.execute("ALTER TABLE doctors ADD COLUMN signature_issuer TEXT")
    if "signature_serial_number" not in d_cols:
        c.execute("ALTER TABLE doctors ADD COLUMN signature_serial_number TEXT")
    if "signature_valid_until" not in d_cols:
        c.execute("ALTER TABLE doctors ADD COLUMN signature_valid_until TEXT")
    if "signature_status" not in d_cols:
        c.execute("ALTER TABLE doctors ADD COLUMN signature_status TEXT DEFAULT 'not_configured'")

    # Migración de columnas en medical_prescriptions
    c.execute("PRAGMA table_info(medical_prescriptions)")
    rx_cols = [row[1] for row in c.fetchall()]
    if "prescription_number" not in rx_cols:
        c.execute("ALTER TABLE medical_prescriptions ADD COLUMN prescription_number TEXT")
    if "signed_electronically" not in rx_cols:
        c.execute("ALTER TABLE medical_prescriptions ADD COLUMN signed_electronically INTEGER DEFAULT 1")
    if "signature_hash" not in rx_cols:
        c.execute("ALTER TABLE medical_prescriptions ADD COLUMN signature_hash TEXT")
    if "signature_timestamp" not in rx_cols:
        c.execute("ALTER TABLE medical_prescriptions ADD COLUMN signature_timestamp TEXT")
    if "signature_certificate_info" not in rx_cols:
        c.execute("ALTER TABLE medical_prescriptions ADD COLUMN signature_certificate_info TEXT")
    if "signature_qr_url" not in rx_cols:
        c.execute("ALTER TABLE medical_prescriptions ADD COLUMN signature_qr_url TEXT")

    # Migración de columnas MES (Manufacturing Execution System) y Control de Calidad en treatments
    c.execute("PRAGMA table_info(treatments)")
    t_cols = [row[1] for row in c.fetchall()]
    if "material_lot_shell" not in t_cols:
        c.execute("ALTER TABLE treatments ADD COLUMN material_lot_shell TEXT")
    if "material_lot_foam" not in t_cols:
        c.execute("ALTER TABLE treatments ADD COLUMN material_lot_foam TEXT")
    if "material_lot_straps" not in t_cols:
        c.execute("ALTER TABLE treatments ADD COLUMN material_lot_straps TEXT")
    if "qc_passed" not in t_cols:
        c.execute("ALTER TABLE treatments ADD COLUMN qc_passed INTEGER DEFAULT 0")
    if "qc_inspector_name" not in t_cols:
        c.execute("ALTER TABLE treatments ADD COLUMN qc_inspector_name TEXT")
    if "qc_caliper_thickness_mm" not in t_cols:
        c.execute("ALTER TABLE treatments ADD COLUMN qc_caliper_thickness_mm REAL DEFAULT 4.0")
    if "qc_weight_grams" not in t_cols:
        c.execute("ALTER TABLE treatments ADD COLUMN qc_weight_grams REAL DEFAULT 190.0")
    if "qc_smooth_edges" not in t_cols:
        c.execute("ALTER TABLE treatments ADD COLUMN qc_smooth_edges INTEGER DEFAULT 1")
    if "qc_relief_chambers_ok" not in t_cols:
        c.execute("ALTER TABLE treatments ADD COLUMN qc_relief_chambers_ok INTEGER DEFAULT 1")
    if "qc_notes" not in t_cols:
        c.execute("ALTER TABLE treatments ADD COLUMN qc_notes TEXT")
    if "qc_approved_at" not in t_cols:
        c.execute("ALTER TABLE treatments ADD COLUMN qc_approved_at TEXT")
    if "helmet_serial_code" not in t_cols:
        c.execute("ALTER TABLE treatments ADD COLUMN helmet_serial_code TEXT")

    # Migración de columnas de Facturación SRI en billing_invoices
    c.execute("PRAGMA table_info(billing_invoices)")
    bi_cols = [row[1] for row in c.fetchall()]
    if "sri_access_key" not in bi_cols:
        c.execute("ALTER TABLE billing_invoices ADD COLUMN sri_access_key TEXT")
    if "sri_authorization_number" not in bi_cols:
        c.execute("ALTER TABLE billing_invoices ADD COLUMN sri_authorization_number TEXT")
    if "sri_authorization_date" not in bi_cols:
        c.execute("ALTER TABLE billing_invoices ADD COLUMN sri_authorization_date TEXT")
    if "sri_environment" not in bi_cols:
        c.execute("ALTER TABLE billing_invoices ADD COLUMN sri_environment TEXT DEFAULT '1'")
    if "sri_emission_type" not in bi_cols:
        c.execute("ALTER TABLE billing_invoices ADD COLUMN sri_emission_type TEXT DEFAULT '1'")
    if "sri_xml_content" not in bi_cols:
        c.execute("ALTER TABLE billing_invoices ADD COLUMN sri_xml_content TEXT")
    if "sri_status" not in bi_cols:
        c.execute("ALTER TABLE billing_invoices ADD COLUMN sri_status TEXT DEFAULT 'pending'")
    if "sri_qr_data" not in bi_cols:
        c.execute("ALTER TABLE billing_invoices ADD COLUMN sri_qr_data TEXT")
    if "client_id" not in bi_cols:
        c.execute("ALTER TABLE billing_invoices ADD COLUMN client_id TEXT")
    if "client_identification" not in bi_cols:
        c.execute("ALTER TABLE billing_invoices ADD COLUMN client_identification TEXT")
    if "client_name" not in bi_cols:
        c.execute("ALTER TABLE billing_invoices ADD COLUMN client_name TEXT")
    if "client_address" not in bi_cols:
        c.execute("ALTER TABLE billing_invoices ADD COLUMN client_address TEXT")
    if "client_email" not in bi_cols:
        c.execute("ALTER TABLE billing_invoices ADD COLUMN client_email TEXT")
    if "client_phone" not in bi_cols:
        c.execute("ALTER TABLE billing_invoices ADD COLUMN client_phone TEXT")
    if "payment_receipt_url" not in bi_cols:
        c.execute("ALTER TABLE billing_invoices ADD COLUMN payment_receipt_url TEXT")

    # Semillas de Doctores por Sucursal
    c.execute("SELECT COUNT(*) FROM doctors")
    if c.fetchone()[0] == 0:
        if branch_id == "quito":
            c.executemany("""
            INSERT INTO doctors (id, global_user_id, full_name, specialty, medical_license, consultation_fee, appointment_duration_min, bio, avatar_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                ("doc_q1", "usr_doc_quito_1", "Dr. Carlos Morales", "Ortopedia Craneofacial Pediátrica", "MSP-EC-10948", 50.00, 30, "Especialista en deformidades craneales posicionales y corrección con órtesis 3D.", "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=300&auto=format&fit=crop&q=80"),
                ("doc_q2", "usr_doc_quito_2", "Dra. Valeria Castro", "Fisioterapia Pediátrica & Tortícolis", "MSP-EC-23091", 40.00, 30, "Certificada en rehabilitación cervical y estimulación temprana neurosensorial.", "https://images.unsplash.com/photo-1594824813511-209e5e796033?w=300&auto=format&fit=crop&q=80")
            ])
            # Horarios de Doctores en Quito (Lunes a Viernes 08:30 - 17:00, Sábados 09:00 - 13:00)
            for doc_id in ["doc_q1", "doc_q2"]:
                for day in range(1, 6): # Lunes a Viernes
                    c.execute("""
                    INSERT INTO doctor_schedules (id, doctor_id, day_of_week, start_time, end_time, slot_duration_min)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (f"sch_{doc_id}_{day}", doc_id, day, "08:30", "17:00", 30))
                # Sábado
                c.execute("""
                INSERT INTO doctor_schedules (id, doctor_id, day_of_week, start_time, end_time, slot_duration_min)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (f"sch_{doc_id}_6", doc_id, 6, "09:00", "13:00", 30))

        elif branch_id == "lima":
            c.executemany("""
            INSERT INTO doctors (id, global_user_id, full_name, specialty, medical_license, consultation_fee, appointment_duration_min, bio, avatar_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                ("doc_l1", "usr_doc_lima_1", "Dr. Miguel Castillo", "Ortopedia & Neurocirugía Pediátrica", "CMP-PE-48201", 60.00, 30, "Pionero en modelado craneal 3D y tratamiento conservador de plagiocefalia.", "https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=300&auto=format&fit=crop&q=80")
            ])
            for day in range(1, 6):
                c.execute("""
                INSERT INTO doctor_schedules (id, doctor_id, day_of_week, start_time, end_time, slot_duration_min)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (f"sch_doc_l1_{day}", "doc_l1", day, "09:00", "18:00", 30))

    # Semillas de Pacientes y Casos de Demostración
    c.execute("SELECT COUNT(*) FROM patients")
    if c.fetchone()[0] == 0:
        if branch_id == "quito":
            today = date.today()
            bday_lucas = (today - timedelta(days=150)).isoformat()
            bday_sofia = (today - timedelta(days=120)).isoformat()
            bday_mateo = (today - timedelta(days=180)).isoformat()

            c.executemany("""
            INSERT INTO patients (id, parent_user_id, parent_name, parent_phone, parent_email, first_name, last_name, birth_date, gestational_weeks, delivery_type, primary_doctor_id, diagnosis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                ("pat_lucas", "usr_parent_1", "María Fernanda López", "+593 98 765 4321", "familia.torres@gmail.com", "Lucas", "Torres López", bday_lucas, 39, "Cesárea Programada", "doc_q1", "Plagiocefalia Posicional Severa Derecha (Argenta Grado III)"),
                ("pat_sofia", "usr_parent_2", "Andrés Paredes", "+593 99 888 7777", "andres.paredes@outlook.com", "Sofía", "Paredes Ruiz", bday_sofia, 38, "Parto Natural con fórceps", "doc_q1", "Braquicefalia Posicional Moderada (Argenta Grado II)"),
                ("pat_mateo", "usr_parent_3", "Elena Salazar", "+593 98 333 4444", "elena.salazar@gmail.com", "Mateo", "Salazar Viteri", bday_mateo, 40, "Parto Natural", "doc_q2", "Tortícolis Muscular Congénita Izquierda + Plagiocefalia Leve")
            ])

            # Historial de Escaneos 3D de Lucas (Muestra la evolución antes y ahora)
            c.executemany("""
            INSERT INTO cranial_scans (id, patient_id, session_number, scan_date, cvai, cephalic_index, argenta_grade, diagonal_a_mm, diagonal_b_mm, circumference_mm, width_mm, length_mm, clinical_summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                ("scan_lucas_1", "pat_lucas", 1, (today - timedelta(days=60)).isoformat(), 11.2, 86.4, 3, 142.5, 126.5, 428.0, 126.2, 146.0, "Evaluación inicial: Aplanamiento occipital derecho notable con compensación frontal anterior ipsilateral."),
                ("scan_lucas_2", "pat_lucas", 2, (today - timedelta(days=30)).isoformat(), 8.1, 85.0, 2, 141.0, 129.5, 436.5, 127.5, 150.0, "Control Mes 1: Respuesta rápida favorable a la órtesis dinámica. Expansión parietal observada."),
                ("scan_lucas_3", "pat_lucas", 3, today.isoformat(), 5.4, 83.8, 1, 142.0, 134.3, 444.0, 129.0, 154.0, "Control Mes 2: Simetría craneal recuperada en un 52%. El CVAI se sitúa en rango leve, próximo a normocefalia.")
            ])

            # Tratamiento Activo con Casco
            c.execute("""
            INSERT INTO treatments (id, patient_id, doctor_id, helmet_model, manufacturing_status, start_date, target_wear_hours_daily, total_cost, installments_count, installments_paid, balance_due, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("trt_lucas", "pat_lucas", "doc_q1", "CraniumFit Pro-Dynamic 3D", "delivered", (today - timedelta(days=55)).isoformat(), 23, 1200.00, 3, 2, 400.00, "Casco color azul cielo personalizado con orificios de ventilación bio-mesh."))

            # Logs de uso diario (últimos 7 días)
            for i in range(7):
                log_day = (today - timedelta(days=i)).isoformat()
                hours = 22.8 if i != 2 else 21.5 # un día con 21.5h por paseo
                c.execute("""
                INSERT INTO wear_time_logs (id, patient_id, log_date, hours_worn, pauses_count, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (f"wear_lucas_{i}", "pat_lucas", log_day, hours, 2, "Higiene matutina y baño nocturno."))

            # Citas pasadas y próximas de Lucas
            c.executemany("""
            INSERT INTO appointments (id, patient_id, doctor_id, appointment_date, start_time, end_time, appointment_type, status, amount, payment_method, payment_status, payment_ref)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                ("apt_l1", "pat_lucas", "doc_q1", (today - timedelta(days=60)).isoformat(), "10:00", "10:45", "evaluacion_3d", "completed", 50.00, "tarjeta_online", "paid", "PAY-ONLINE-9812"),
                ("apt_l2", "pat_lucas", "doc_q1", (today - timedelta(days=30)).isoformat(), "11:00", "11:30", "control_quincenal", "completed", 30.00, "tarjeta_online", "paid", "PAY-ONLINE-1049"),
                ("apt_l3", "pat_lucas", "doc_q1", (today + timedelta(days=5)).isoformat(), "10:30", "11:00", "control_quincenal", "confirmed", 30.00, "transferencia", "paid", "TRF-PICHINCHA-5521")
            ])

        elif branch_id == "lima":
            today = date.today()
            bday_camila = (today - timedelta(days=100)).isoformat()
            c.execute("""
            INSERT INTO patients (id, parent_user_id, parent_name, parent_phone, parent_email, first_name, last_name, birth_date, gestational_weeks, delivery_type, primary_doctor_id, diagnosis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("pat_camila", "usr_parent_lima", "Renato Vega", "+51 988 111 222", "renato.vega@gmail.com", "Camila", "Vega Prado", bday_camila, 40, "Parto Natural", "doc_l1", "Plagiocefalia Posicional Moderada Izquierda"))

    # Semillas de Historial Clínico: Consultas Médicas (Independientes)
    c.execute("SELECT COUNT(*) FROM medical_consultations")
    if c.fetchone()[0] == 0:
        today = date.today()
        if branch_id == "quito":
            c.executemany("""
            INSERT INTO medical_consultations (id, patient_id, doctor_id, consultation_date, reason_for_visit, vital_signs, cranial_eval, diagnosis, clinical_evolution, treatment_plan, next_appointment_rec)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                ("mc_lucas_1", "pat_lucas", "doc_q1", (today - timedelta(days=60)).isoformat() + " 10:15",
                 "Madre nota aplanamiento unilateral pronunciado en zona occipital derecha desde el 2do mes. Dificultad para girar la cabeza hacia la izquierda.",
                 '{"weight_kg": 6.8, "height_cm": 62.5, "head_circumference_cm": 42.0, "temp_c": 36.6}',
                 "Asimetría occipital posterior derecha marcada con adelantamiento de pabellón auricular ipsilateral y abombamiento frontal compensatorio. Tensión moderada en ECOM izquierdo.",
                 "Plagiocefalia Posicional Severa Derecha (Argenta Grado III) secundaria a preferencia postural",
                 "Primera valoración clínica especializada. Se realiza escaneo fotogramétrico 3D y antropometría craneal computarizada.",
                 "1. Prescripción de Órtesis Dinámica CraniumFit Pro-Dynamic 3D (23 hrs/día).\n2. Derivación a Fisioterapia Pediátrica para liberación cervical.\n3. Pautas de reposicionamiento durante vigilia.",
                 "En 3 semanas para prueba, calibración y entrega de órtesis craneal"),
                
                ("mc_lucas_2", "pat_lucas", "doc_q2", (today - timedelta(days=30)).isoformat() + " 11:15",
                 "Control de adaptación de órtesis y reevaluación fisioterapéutica cervical.",
                 '{"weight_kg": 7.4, "height_cm": 65.0, "head_circumference_cm": 43.2, "temp_c": 36.5}',
                 "Piel con excelente tolerancia sin eritemas persistentes en puntos de contacto. Rango articular cervical izquierdo aumentado en 70%.",
                 "Evolución favorable de Plagiocefalia Derecha (Argenta Grado II en remisión). Tortícolis postural compensada.",
                 "Adherencia estricta de 22.8 horas/día comprobada en telemetría de la app. Crecimiento craneal guiado hacia zona receptora de descompresión.",
                 "1. Micro-ajuste en zona parietal para optimizar vector de crecimiento.\n2. Continuar ejercicios de tummy time 15 min x 4 al día.",
                 "Control en 30 días con nuevo escaneo 3D"),

                ("mc_lucas_3", "pat_lucas", "doc_q1", today.isoformat() + " 09:30",
                 "Control evolutivo de 60 días de tratamiento con órtesis craneal activa.",
                 '{"weight_kg": 8.0, "height_cm": 67.2, "head_circumference_cm": 44.1, "temp_c": 36.7}',
                 "Simetría biauricular prácticamente normalizada. Fontanela anterior normotensa de 2.0 x 1.5 cm. Desalineación diagonal reducida a rango leve.",
                 "Plagiocefalia Posicional Leve Residual (Argenta Grado I - Próxima a Normocefalia)",
                 "Excelente respuesta biológica. El CVAI ha descendido de 11.2% inicial a 5.4%. Se planifica última fase de retención antes del destete ortésico.",
                 "Mantener uso de 23h/día por 3 semanas más, luego iniciar protocolo de retiro progresivo (18h/día la 4ta semana).",
                 "En 30 días para evaluación de alta médica y escaneo 3D final"),

                ("mc_sofia_1", "pat_sofia", "doc_q1", (today - timedelta(days=45)).isoformat() + " 15:00",
                 "Evaluación por aplanamiento occipital bilateral simétrico y aumento de anchura parietal.",
                 '{"weight_kg": 6.2, "height_cm": 60.5, "head_circumference_cm": 41.5, "temp_c": 36.5}',
                 "Cráneo corto y ancho. Índice Cefálico de 94% compatible con braquicefalia severa.",
                 "Braquicefalia Posicional Severa (Argenta Grado II-III)",
                 "Se prescribe órtesis de remodelado con cámaras de descompresión posterior biparietal.",
                 "Inicio de casco ortopédico y protocolo de porteo ergonómico.",
                 "Control quincenal"),

                ("mc_mateo_1", "pat_mateo", "doc_q2", (today - timedelta(days=20)).isoformat() + " 16:30",
                 "Lactante de 6 meses con inclinación cefálica derecha y rotación restringida hacia la derecha.",
                 '{"weight_kg": 7.9, "height_cm": 66.0, "head_circumference_cm": 43.8, "temp_c": 36.6}',
                 "Nódulo palpable en tercio medio de ECM derecho. Plagiocefalia leve compensatoria ipsilateral.",
                 "Tortícolis Muscular Congénita Derecha + Plagiocefalia Leve Secundaria",
                 "Inicio inmediato de fisioterapia motora y terapia manual pediátrica.",
                 "1. Estiramientos pasivos del ECM derecho.\n2. Estimulación visual en cuna y coche hacia el lado contrario.\n3. Cojín de posicionamiento ergonómico.",
                 "Sesiones bisemanales de fisioterapia en clínica")
            ])
        elif branch_id == "lima":
            c.execute("""
            INSERT INTO medical_consultations (id, patient_id, doctor_id, consultation_date, reason_for_visit, vital_signs, cranial_eval, diagnosis, clinical_evolution, treatment_plan, next_appointment_rec)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("mc_camila_1", "pat_camila", "doc_l1", (today - timedelta(days=15)).isoformat() + " 10:00",
                  "Evaluación inicial por asimetría craneal izquierda y postura preferente.",
                  '{"weight_kg": 6.5, "height_cm": 61.0, "head_circumference_cm": 41.8, "temp_c": 36.6}',
                  "Aplanamiento occipital izquierdo moderado. Pabellón auricular ligeramente adelantado.",
                  "Plagiocefalia Posicional Moderada Izquierda",
                  "Se solicita escaneo 3D y se inicia programa de reposicionamiento.",
                  "1. Pautas de reposicionamiento diurno y tummy time.\n2. Valoración para diseño de órtesis 3D.",
                  "En 15 días"))

    # Semillas de Historial Clínico: Exámenes y Diagnósticos (Independientes)
    c.execute("SELECT COUNT(*) FROM medical_exams")
    if c.fetchone()[0] == 0:
        today = date.today()
        if branch_id == "quito":
            c.executemany("""
            INSERT INTO medical_exams (id, patient_id, doctor_id, exam_date, exam_type, cvai, cephalic_index, argenta_grade, measurements, results_summary, recommendations, file_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                ("exam_lucas_1", "pat_lucas", "doc_q1", (today - timedelta(days=60)).isoformat(),
                 "Escaneo 3D Fotogramétrico de Superficie Craneal",
                 11.2, 86.4, 3,
                 '{"diagonal_a_mm": 142.5, "diagonal_b_mm": 126.5, "diff_mm": 16.0, "circumference_mm": 428.0, "width_mm": 126.2, "length_mm": 146.0}',
                 "Aplanamiento occipital derecho severo con desplazamiento anterior de oreja derecha en 8mm y prominencia frontal ipsilateral. CVAI: 11.2% (Severo).",
                 "Indicación formal de tratamiento ortésico con casco dinámico.", "https://cranium.fit/reports/scan_lucas_1.pdf"),

                ("exam_lucas_2", "pat_lucas", "doc_q1", (today - timedelta(days=30)).isoformat(),
                 "Escaneo 3D y Cefalometría de Control Mes 1",
                 8.1, 85.0, 2,
                 '{"diagonal_a_mm": 141.0, "diagonal_b_mm": 129.5, "diff_mm": 11.5, "circumference_mm": 436.5, "width_mm": 127.5, "length_mm": 150.0}',
                 "Reducción de 4.5 mm en la asimetría diagonal. El CVAI disminuye a 8.1% (Moderado). Expansión parietal simétrica en curso.",
                 "Mantener uso estricto de 23 horas diarias.", "https://cranium.fit/reports/scan_lucas_2.pdf"),

                ("exam_lucas_3", "pat_lucas", "doc_q1", today.isoformat(),
                 "Escaneo 3D Fotogramétrico de Control Mes 2",
                 5.4, 83.8, 1,
                 '{"diagonal_a_mm": 142.0, "diagonal_b_mm": 134.3, "diff_mm": 7.7, "circumference_mm": 444.0, "width_mm": 129.0, "length_mm": 154.0}',
                 "Recuperación simétrica del 51.8%. Índice CVAI actual en 5.4% (Leve). Relación ancho/largo cefálico normalizada (83.8%).",
                 "Iniciar fase de consolidación y preparación para destete ortésico.", "https://cranium.fit/reports/scan_lucas_3.pdf"),

                ("exam_sofia_1", "pat_sofia", "doc_q1", (today - timedelta(days=45)).isoformat(),
                 "Cefalometría Digital y Escaneo 3D",
                 3.2, 94.2, 3,
                 '{"circumference_mm": 415.0, "width_mm": 138.0, "length_mm": 146.5, "cephalic_index": 94.2}',
                 "Índice cefálico marcadamente elevado (94.2%) con aplanamiento occipital global. Ausencia de sinostosis craneal por suturas abiertas.",
                 "Órtesis de remodelado para braquicefalia activa.", "https://cranium.fit/reports/scan_sofia_1.pdf"),

                ("exam_mateo_1", "pat_mateo", "doc_q2", (today - timedelta(days=20)).isoformat(),
                 "Ecografía de Partes Blandas Cervicales",
                 None, None, None,
                 '{"ecm_thickness_right_mm": 7.2, "ecm_thickness_left_mm": 4.1, "pseudotumor_detected": true}',
                 "Engrosamiento fusiforme del músculo esternocleidomastoideo derecho sin calcificaciones, característico de tortícolis congénita.",
                 "Fisioterapia inmediata para prevenir progresión de asimetría craneofacial.", "https://cranium.fit/reports/eco_mateo_1.pdf")
            ])
        elif branch_id == "lima":
            c.execute("""
            INSERT INTO medical_exams (id, patient_id, doctor_id, exam_date, exam_type, cvai, cephalic_index, argenta_grade, measurements, results_summary, recommendations, file_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("exam_camila_1", "pat_camila", "doc_l1", (today - timedelta(days=15)).isoformat(),
                  "Escaneo 3D Fotogramétrico Inicial", 7.8, 87.2, 2,
                  '{"diagonal_a_mm": 138.0, "diagonal_b_mm": 127.5, "diff_mm": 10.5}',
                  "Asimetría craneal moderada izquierda con CVAI de 7.8%.",
                  "Prescripción de tratamiento ortésico modelado por escaneo 3D.", "https://cranium.fit/reports/scan_camila_1.pdf"))

    # Semillas de Historial Clínico: Recetas Médicas & Órdenes (Independientes)
    c.execute("SELECT COUNT(*) FROM medical_prescriptions")
    if c.fetchone()[0] == 0:
        today = date.today()
        if branch_id == "quito":
            c.executemany("""
            INSERT INTO medical_prescriptions (id, patient_id, doctor_id, consultation_id, prescription_date, medications_rx, orthotic_prescription, physical_therapy_orders, special_instructions, valid_until)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                ("rx_lucas_1", "pat_lucas", "doc_q1", "mc_lucas_1", (today - timedelta(days=60)).isoformat(),
                 "1. Crema protectora de Óxido de Zinc + Caléndula (aplicar capa fina en áreas de apoyo 2 veces al día).\n2. Vitamina D3 gotas 400 UI (2 gotas vía oral al día en la mañana).",
                 "ÓRTESIS CRANEAL DINÁMICA CRANIUMFIT PRO-DYNAMIC 3D:\n- Uso continuo de 23 horas diarias.\n- Protocolo de inicio: Día 1 (2h), Día 2 (4h), Día 3 (8h), Día 4 (23h).\n- Retirar únicamente 1 hora al día para el baño y aseo del casco.",
                 "1. Tummy time supervisado: 10 minutos 3 a 4 veces al día.\n2. Colocar juguetes y móviles hacia el lado izquierdo de la cuna para incentivar la rotación activa.",
                 "Verificar piel al retirar el casco. Si hay manchas rojas que duren más de 30 minutos, retirar y llamar a la clínica.",
                 (today + timedelta(days=60)).isoformat()),

                ("rx_lucas_2", "pat_lucas", "doc_q2", "mc_lucas_2", (today - timedelta(days=30)).isoformat(),
                 "1. Continuar Vitamina D3 gotas 400 UI (2 gotas al día).\n2. Loción limpiadora con pH neutro para desinfección interna del casco con alcohol isopropílico al 70%.",
                 "Mantener uso estricto de 23 horas diarias de casco ortésico. Calibración de almohadilla interna realizada en consulta.",
                 "1. Estiramientos suaves del ECM izquierdo: mantener 10 segundos x 5 repeticiones x 3 veces al día.\n2. Masaje suave miofascial en cuello y cintura escapular.",
                 "No usar almohadas dentro de la cuna. Registrar horas en la app móvil.",
                 (today + timedelta(days=60)).isoformat()),

                ("rx_sofia_1", "pat_sofia", "doc_q1", "mc_sofia_1", (today - timedelta(days=45)).isoformat(),
                 "1. Vitamina D3 pediátrica 400 UI al día.\n2. Gel emoliente para zonas de apoyo temporal.",
                 "Órtesis Craneal para Braquicefalia Simétrica: 23 horas de uso diario.",
                 "Porteo ergonómico en fular o mochila certificada M-position para descargar presión occipital.",
                 "Limpieza diaria del casco con paño húmedo y secado total al aire antes de recolocar.",
                 (today + timedelta(days=60)).isoformat()),

                ("rx_mateo_1", "pat_mateo", "doc_q2", "mc_mateo_1", (today - timedelta(days=20)).isoformat(),
                 "1. Aceite de almendras dulces para masaje terapéutico cervical.\n2. Gel analgésico tópico suave si hay molestia post-fisioterapia.",
                 "Por el momento no requiere casco ortésico. Se reevaluará tras 6 semanas de fisioterapia.",
                 "Plan de Fisioterapia Intensiva de Cuello: 3 sesiones semanales en clínica + ejercicios diarios guiados en el hogar (rotación e inclinación).",
                 "Cambiar de posición en la cuna para que la luz y los estímulos provengan de su lado derecho.",
                 (today + timedelta(days=45)).isoformat())
            ])
        elif branch_id == "lima":
            c.execute("""
            INSERT INTO medical_prescriptions (id, patient_id, doctor_id, consultation_id, prescription_date, medications_rx, orthotic_prescription, physical_therapy_orders, special_instructions, valid_until)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("rx_camila_1", "pat_camila", "doc_l1", "mc_camila_1", (today - timedelta(days=15)).isoformat(),
                  "1. Vitamina D3 400 UI al día.",
                  "Preparación para órtesis craneal 3D: tomar medidas de control.",
                  "Ejercicios diarios de posicionamiento en decúbito prono asistido.",
                  "Evitar largos periodos en asiento para auto (huevito).",
                  (today + timedelta(days=30)).isoformat()))

    # Semillas de Escaneos 3D Reales (.STL / .OBJ)
    c.execute("SELECT COUNT(*) FROM uploaded_scans")
    if c.fetchone()[0] == 0:
        today = date.today()
        if branch_id == "quito":
            c.executemany("""
            INSERT INTO uploaded_scans (id, patient_id, session_number, scan_name, file_name, file_url, file_type, file_size_bytes, cvai, cephalic_index, argenta_grade, scan_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                ("scan_lucas_t0", "pat_lucas", 1, "Escaneo Inicial T0 - Diagnóstico Base", "lucas_torres_t0_scan.stl", "/uploads/scans/pat_lucas/lucas_torres_t0_scan.stl", "stl", 559104, 11.2, 86.4, 3, (today - timedelta(days=60)).isoformat(), "Escaneo fotogramétrico 3D inicial. Deformidad occipital derecha severa previa al tratamiento ortésico."),
                ("scan_lucas_t2", "pat_lucas", 3, "Escaneo Control Mes 2 T2 - Evolución Actual", "lucas_torres_t2_scan.stl", "/uploads/scans/pat_lucas/lucas_torres_t2_scan.stl", "stl", 559104, 5.4, 83.8, 1, today.isoformat(), "Control de 60 días de tratamiento con Casco CraniumFit Pro. Corrección de 5.8 puntos en CVAI."),
                ("scan_sofia_t0", "pat_sofia", 1, "Escaneo Inicial T0 - Braquicefalia Simétrica", "sofia_paredes_t0_scan.stl", "/uploads/scans/pat_sofia/sofia_paredes_t0_scan.stl", "stl", 559104, 3.2, 94.2, 3, (today - timedelta(days=45)).isoformat(), "Aplanamiento occipital bilateral marcado. Índice cefálico 94.2%.")
            ])
        elif branch_id == "lima":
            c.execute("""
            INSERT INTO uploaded_scans (id, patient_id, session_number, scan_name, file_name, file_url, file_type, file_size_bytes, cvai, cephalic_index, argenta_grade, scan_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("scan_camila_t0", "pat_camila", 1, "Escaneo Inicial T0 - Sede Lima", "lucas_torres_t0_scan.stl", "/uploads/scans/pat_lucas/lucas_torres_t0_scan.stl", "stl", 559104, 7.8, 87.2, 2, (today - timedelta(days=15)).isoformat(), "Escaneo fotogramétrico 3D inicial en San Isidro."))

    # Semillas de Facturación, Cobros y Presupuestos
    c.execute("SELECT COUNT(*) FROM billing_invoices")
    if c.fetchone()[0] == 0:
        today = date.today()
        if branch_id == "quito":
            c.executemany("""
            INSERT INTO billing_invoices (id, invoice_number, patient_id, parent_user_id, parent_name, parent_cedula, doctor_id, invoice_date, due_date, items_json, subtotal, tax_percent, tax_amount, total_amount, payment_method, payment_status, payment_reference, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                ("inv_lucas_1", "INV-UIO-2026-001", "pat_lucas", "usr_parent_1", "María Fernanda López", "1718899221", "doc_q1", (today - timedelta(days=58)).isoformat(), (today - timedelta(days=58)).isoformat(),
                 json.dumps([
                     {"description": "Consulta de Diagnóstico y Escaneo Fotogramétrico 3D", "quantity": 1, "unit_price": 60.00, "total": 60.00},
                     {"description": "Tratamiento Integral: Casco Ortésico CraniumFit Pro-Dynamic 3D", "quantity": 1, "unit_price": 1850.00, "total": 1850.00}
                 ]), 1910.00, 15.0, 286.50, 2196.50, "transferencia", "paid", "TRF-PICHINCHA-881290", "Cancelación total de tratamiento y escaneo de alta precisión."),

                ("inv_sofia_1", "INV-UIO-2026-002", "pat_sofia", "usr_parent_sofia", "Valeria Paredes", "1719944332", "doc_q1", (today - timedelta(days=43)).isoformat(), (today + timedelta(days=15)).isoformat(),
                 json.dumps([
                     {"description": "Evaluación Craniométrica 3D y Consulta Especializada", "quantity": 1, "unit_price": 60.00, "total": 60.00},
                     {"description": "Órtesis de Remodelado Craneal CraniumFit Active", "quantity": 1, "unit_price": 1750.00, "total": 1750.00}
                 ]), 1810.00, 15.0, 271.50, 2081.50, "tarjeta", "partial", "TARJ-VISA-4491 (Abono 50%: $1,040.75)", "Abono inicial 50% para inicio de manufactura 3D. Saldo pendiente a la entrega del casco."),

                ("inv_mateo_1", "INV-UIO-2026-003", "pat_mateo", "usr_parent_mateo", "David Salazar", "1720055119", "doc_q2", (today - timedelta(days=18)).isoformat(), (today - timedelta(days=18)).isoformat(),
                 json.dumps([
                     {"description": "Paquete Fisioterapia Cervical y Neurorehabilitación Pediátrica (10 Sesiones)", "quantity": 1, "unit_price": 350.00, "total": 350.00}
                 ]), 350.00, 15.0, 52.50, 402.50, "efectivo", "paid", "REC-CAJA-00412", "Pago en efectivo en recepción Citimed.")
            ])
        elif branch_id == "lima":
            c.execute("""
            INSERT INTO billing_invoices (id, invoice_number, patient_id, parent_user_id, parent_name, parent_cedula, doctor_id, invoice_date, due_date, items_json, subtotal, tax_percent, tax_amount, total_amount, payment_method, payment_status, payment_reference, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("inv_camila_1", "INV-LIM-2026-001", "pat_camila", "usr_parent_lima", "Renato Vega", "0921884411", "doc_l1", (today - timedelta(days=14)).isoformat(), (today + timedelta(days=10)).isoformat(),
                 json.dumps([
                     {"description": "Consulta Médica y Escaneo 3D San Isidro", "quantity": 1, "unit_price": 70.00, "total": 70.00},
                     {"description": "Anticipo Fabricación Órtesis CraniumFit Pro", "quantity": 1, "unit_price": 1000.00, "total": 1000.00}
                 ]), 1070.00, 18.0, 192.60, 1262.60, "transferencia", "paid", "BCP-TRANSF-19283", "Anticipo de tratamiento recibido vía BCP."))

    # Semillas de Catálogo de Ítems (Productos & Servicios Médicos)
    c.execute("SELECT COUNT(*) FROM billing_items")
    if c.fetchone()[0] == 0:
        c.executemany("""
        INSERT INTO billing_items (id, code, description, category, unit_price, tax_percent, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            ("item_1", "CF-001", "Consulta de Diagnóstico y Escaneo Fotogramétrico 3D", "Consulta & Diagnóstico", 60.00, 15.0, "active"),
            ("item_2", "CF-002", "Tratamiento Integral: Casco Ortésico CraniumFit Pro-Dynamic 3D", "Órtesis Craneal", 1850.00, 15.0, "active"),
            ("item_3", "CF-003", "Órtesis de Remodelado Craneal CraniumFit Active", "Órtesis Craneal", 1750.00, 15.0, "active"),
            ("item_4", "CF-004", "Paquete Fisioterapia Cervical y Neurorehabilitación (10 Sesiones)", "Fisioterapia", 350.00, 15.0, "active"),
            ("item_5", "CF-005", "Control Quincenal de Remodelación Craneal 3D", "Control Médico", 60.00, 15.0, "active"),
            ("item_6", "CF-006", "Reemplazo de Acolchado Hipoalergénico Plastazote LD45 (Par)", "Insumos & Repuestos", 45.00, 15.0, "active"),
            ("item_7", "CF-007", "Kit de Correas BioStrap y Mantenimiento", "Insumos & Repuestos", 25.00, 15.0, "active"),
            ("item_8", "CF-008", "Certificado Médico Especializado / Informe Aseguradora Privada", "Documentación Médica", 30.00, 0.0, "active")
        ])

    # Semillas del Directorio de Clientes (Personas Naturales y Empresas con RUC)
    c.execute("SELECT COUNT(*) FROM billing_clients")
    if c.fetchone()[0] == 0:
        c.executemany("""
        INSERT INTO billing_clients (id, client_type, identification_type, identification_number, name_or_business_name, email, phone, address, associated_patient_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            ("cli_lucas", "natural", "05", "1718899221", "María Fernanda López", "familia.torres@gmail.com", "+593 98 765 4321", "Av. González Suárez N27-142, Quito", "pat_lucas"),
            ("cli_sofia", "natural", "05", "1719944332", "Valeria Paredes", "valeria.paredes@outlook.com", "+593 99 888 7777", "Cumbayá, Urb. La Primavera, Casa 12", "pat_sofia"),
            ("cli_mateo", "natural", "05", "1720055119", "David Salazar", "david.salazar@gmail.com", "+593 98 333 4444", "Av. República del Salvador 890, Quito", "pat_mateo"),
            ("cli_saludsa", "juridica", "04", "1791234567001", "SaludSA Medicina Prepagada S.A.", "reembolsos@saludsa.com.ec", "+593 2 398 9000", "Av. Amazonas y República, Edif. SaludSA, Quito", None),
            ("cli_corp_pediatrica", "juridica", "04", "1792987654001", "Consorcio Pediátrico Pichincha Cía. Ltda.", "contabilidad@pediatricapichincha.ec", "+593 2 245 6789", "Av. 10 de Agosto N34-89, Quito", None)
        ])

    # Configuración de Firma Electrónica Semilla para Dr. Carlos Morales
    try:
        from signature_service import create_demo_p12_for_doctor
        if branch_id == "quito":
            demo_sig = create_demo_p12_for_doctor("doc_q1", "Dr. Carlos Morales", "1710948210")
            c.execute("""
            UPDATE doctors
            SET signature_p12_path = ?,
                signature_p12_filename = ?,
                signature_issuer = ?,
                signature_serial_number = ?,
                signature_valid_until = ?,
                signature_status = 'active'
            WHERE id = 'doc_q1'
            """, (
                demo_sig["file_path"],
                demo_sig["file_name"],
                demo_sig["issuer"],
                demo_sig["serial_number"],
                demo_sig["valid_until"]
            ))
    except Exception as e:
        print(f"Nota: Configuración de firma demo para doctor: {e}")

    # Actualizar recetas con número y firma electrónica
    today = date.today()
    c.execute("""
    UPDATE medical_prescriptions
    SET prescription_number = 'RX-UIO-2026-001',
        signed_electronically = 1,
        signature_hash = '8f3b892a0194821cd90fa12b88192a54e90141b7c124a9194d9b01438921fa41',
        signature_timestamp = '2026-08-22 10:45:00 ECT',
        signature_certificate_info = '{"signer_name": "Dr. Carlos Morales", "medical_license": "MSP-EC-10948", "issuer": "Security Data Seguridad en Datos y Firma Digital S.A.", "serial_number": "SD-EC-2026-09412A", "valid_until": "2028-11-15"}',
        signature_qr_url = 'https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https%3A%2F%2Fcranium.fit%2Fvalidar-receta%3Fnum%3DRX-UIO-2026-001'
    WHERE id = 'rx_lucas_1' AND (prescription_number IS NULL OR prescription_number = '')
    """)

    c.execute("""
    UPDATE medical_prescriptions
    SET prescription_number = 'RX-UIO-2026-002',
        signed_electronically = 1,
        signature_hash = 'a71e4492bf0194d8123cba99104fae1014299b871c552019482bfacde0192841',
        signature_timestamp = '2026-09-21 11:30:00 ECT',
        signature_certificate_info = '{"signer_name": "Dra. Valeria Castro", "medical_license": "MSP-EC-23091", "issuer": "Banco Central del Ecuador (BCE)", "serial_number": "BCE-EC-2026-44109B", "valid_until": "2027-10-30"}',
        signature_qr_url = 'https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https%3A%2F%2Fcranium.fit%2Fvalidar-receta%3Fnum%3DRX-UIO-2026-002'
    WHERE id = 'rx_lucas_2' AND (prescription_number IS NULL OR prescription_number = '')
    """)

    # Semillas de Certificados Médicos (Independientes)
    c.execute("SELECT COUNT(*) FROM medical_certificates")
    if c.fetchone()[0] == 0:
        if branch_id == "quito":
            c.executemany("""
            INSERT INTO medical_certificates (id, certificate_number, patient_id, doctor_id, consultation_id, issue_date, certificate_type, diagnosis_cie10, clinical_findings, rest_days, valid_until, formal_statement, signed_electronically, signature_hash, signature_timestamp, signature_certificate_info, signature_qr_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                ("cert_lucas_1", "CERT-UIO-2026-001", "pat_lucas", "doc_q1", "mc_lucas_1", (today - timedelta(days=58)).isoformat(),
                 "reposo_medico", "Q67.3 Plagiocefalia Posicional Severa",
                 "Lactante de 5 meses presenta asimetría craneofacial derecha moderada a severa (CVAI 11.2%, Argenta III). En tratamiento de remodelación craneal dinámica 3D.",
                 3, (today + timedelta(days=90)).isoformat(),
                 "CERTIFICO QUE: El paciente Lucas Torres López se encuentra bajo tratamiento médico especializado para corrección craneal ortésica activa, requiriendo reposo domiciliario de adaptación los primeros 3 días y cuidados ergonómicos por parte de sus progenitores durante la colocación de la órtesis 23 horas al día.",
                 1, "b41982a74c019d45e8812fa91024bc0192e48fa1b8c194d8761a0194821cfba9",
                 (today - timedelta(days=58)).isoformat() + " 11:15:00 ECT",
                 json.dumps({
                     "signer_name": "Dr. Carlos Morales",
                     "medical_license": "MSP-EC-10948 (Libro 4, Folio 22)",
                     "specialty": "Ortopedia Craneofacial Pediátrica",
                     "issuer": "Security Data Seguridad en Datos y Firma Digital S.A.",
                     "serial_number": "SD-EC-2026-09412A",
                     "valid_until": "2028-11-15"
                 }),
                 "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https%3A%2F%2Fcranium.fit%2Fvalidar-certificado%3Fnum%3DCERT-UIO-2026-001"),

                ("cert_lucas_2", "CERT-UIO-2026-002", "pat_lucas", "doc_q1", "mc_lucas_3", today.isoformat(),
                 "uso_ortesis_aerolinea", "Q67.3 Plagiocefalia Posicional en Tratamiento Activo",
                 "Paciente portador de Casco Ortésico Craneal Dinámico CraniumFit Pro (modelo termoplástico bio-compatible con sensores).",
                 0, (today + timedelta(days=180)).isoformat(),
                 "CERTIFICACIÓN PARA TRÁNSITO Y TRANSPORTE AÉREO: Se hace constar a las autoridades aeroportuarias y aerolíneas que el lactante Lucas Torres López debe portar de manera continua (23 horas/día) su órtesis craneofacial CraniumFit Pro por indicación médica estricta, no debiendo ser retirada durante el vuelo ni en los controles de seguridad rutinarios salvo inspección visual de sus padres.",
                 1, "c89012fa1b894d0194e82bca90124fe019421b8c10948d21bf901248ba12049e",
                 today.isoformat() + " 10:30:00 ECT",
                 json.dumps({
                     "signer_name": "Dr. Carlos Morales",
                     "medical_license": "MSP-EC-10948 (Libro 4, Folio 22)",
                     "specialty": "Ortopedia Craneofacial Pediátrica",
                     "issuer": "Security Data Seguridad en Datos y Firma Digital S.A.",
                     "serial_number": "SD-EC-2026-09412A",
                     "valid_until": "2028-11-15"
                 }),
                 "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https%3A%2F%2Fcranium.fit%2Fvalidar-certificado%3Fnum%3DCERT-UIO-2026-002")
            ])
        elif branch_id == "lima":
            c.execute("""
            INSERT INTO medical_certificates (id, certificate_number, patient_id, doctor_id, consultation_id, issue_date, certificate_type, diagnosis_cie10, clinical_findings, rest_days, valid_until, formal_statement, signed_electronically, signature_hash, signature_timestamp, signature_certificate_info, signature_qr_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("cert_camila_1", "CERT-LIM-2026-001", "pat_camila", "doc_l1", "mc_camila_1", (today - timedelta(days=14)).isoformat(),
                  "constancia_atencion", "Q67.3 Plagiocefalia Izquierda",
                  "Evaluación clínica y cefalométrica inicial realizada en Sede San Isidro.", 0, (today + timedelta(days=60)).isoformat(),
                  "Se deja constancia de atención médica ortopédica para prescripción de órtesis craneal 3D.", 1,
                  "d1904128ba019482bcf01248ba19024fca8901248901248fa10948201948bc01",
                  (today - timedelta(days=14)).isoformat() + " 11:00:00 PET",
                  json.dumps({
                      "signer_name": "Dr. Miguel Castillo",
                      "medical_license": "CMP-PE-48201",
                      "specialty": "Ortopedia & Neurocirugía Pediátrica",
                      "issuer": "RENIEC / Entidad de Certificación del Estado Peruano",
                      "serial_number": "CMP-PE-2026-00192",
                      "valid_until": "2027-08-30"
                  }),
                  "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https%3A%2F%2Fcranium.fit%2Fvalidar-certificado%3Fnum%3DCERT-LIM-2026-001"))

    # Semillas de Dossiers de Aseguradora / Cobertura Médica
    c.execute("SELECT COUNT(*) FROM insurance_dossiers")
    if c.fetchone()[0] == 0:
        if branch_id == "quito":
            c.execute("""
            INSERT INTO insurance_dossiers (id, dossier_number, patient_id, doctor_id, insurance_company, policy_number, diagnosis_cie10, cvai_initial, cvai_current, argenta_grade, clinical_justification, estimated_cost, status, signed_electronically, signature_hash, signature_timestamp, signature_certificate_info, signature_qr_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "dos_lucas_1",
                "DOS-UIO-2026-001",
                "pat_lucas",
                "doc_q1",
                "SaludSA Medicina Prepagada",
                "POL-SALUDSA-89410-VIP",
                "Q67.3 Plagiocefalia Posicional Severa Derecha (Argenta Grado III)",
                11.2,
                5.4,
                3,
                "INFORME MÉDICO DE JUSTIFICACIÓN BIOMECÁNICA Y COBERTURA:\nSe certifica que el paciente lactante Lucas Torres López (5 meses) presenta deformidad craneofacial posicional severa con CVAI de 11.2% y desviación diagonal de 16.0 mm. Este cuadro NO constituye una condición estética, sino una deformidad ósea funcional que genera asimetría mandibular, alteración en los cóndilos temporomandibulares y riesgo de desalineación oclusal futura. El tratamiento con Órtesis Craneal Dinámica CraniumFit Pro (código orthotic L0100 / L0110) es de estricta necesidad médica para guiar el crecimiento neurocraneal antes del cierre de fontanelas.",
                1850.00,
                "issued",
                1,
                "f90241b8c019284fae1094821cfba901248ba12049ec89012fa1b894d0194e82",
                (today - timedelta(days=58)).isoformat() + " 15:45:00 ECT",
                json.dumps({
                    "signer_name": "Dr. Carlos Morales",
                    "medical_license": "MSP-EC-10948 (Libro 4, Folio 22)",
                    "specialty": "Ortopedia Craneofacial Pediátrica",
                    "issuer": "Security Data Seguridad en Datos y Firma Digital S.A.",
                    "serial_number": "SD-EC-2026-09412A",
                    "valid_until": "2028-11-15"
                }),
                "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https%3A%2F%2Fcranium.fit%2Fvalidar-dossier%3Fnum%3DDOS-UIO-2026-001"
            ))

    # Actualizar trazabilidad MES y Control de Calidad en tratamientos existentes
    c.execute("""
    UPDATE treatments
    SET material_lot_shell = 'LOTE-PETG-VIVAK-2026-A1',
        material_lot_foam = 'LOTE-PLASTAZOTE-LD45-09',
        material_lot_straps = 'LOTE-VELCRO-BIO-12',
        qc_passed = 1,
        qc_inspector_name = 'Ing. Roberto Silva (Técnico Ortoprotesista Certificado)',
        qc_caliper_thickness_mm = 4.15,
        qc_weight_grams = 188.5,
        qc_smooth_edges = 1,
        qc_relief_chambers_ok = 1,
        qc_notes = 'Conformidad total de fabricación. Espesor homogéneo en bóveda. Cámara de descompresión parietal derecha verificada sin aristas cortantes.',
        qc_approved_at = '2026-08-27 16:30:00',
        helmet_serial_code = 'CF-HELM-UIO-2026-089'
    WHERE id = 'trt_lucas' AND (helmet_serial_code IS NULL OR helmet_serial_code = '')
    """)

    # Actualizar factura de Lucas con Facturación Electrónica SRI Autorizada
    access_key_demo = "2208202601179234567800110010010000000011234567817"
    c.execute("""
    UPDATE billing_invoices
    SET sri_access_key = ?,
        sri_authorization_number = ?,
        sri_authorization_date = '2026-08-22 11:32:15',
        sri_environment = '1',
        sri_emission_type = '1',
        sri_status = 'AUTORIZADO',
        sri_qr_data = ?
    WHERE id = 'inv_lucas_1' AND (sri_access_key IS NULL OR sri_access_key = '')
    """, (access_key_demo, access_key_demo, f"https://sri.gob.ec/comprobantes-electronicos/consultas?claveAcceso={access_key_demo}"))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_all_databases()
