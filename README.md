# 🩺 CraniumFit — Plataforma Clínica & ERP Pediátrico Craneofacial

Plataforma integral de gestión clínica y administrativa especializada en **ortopedia craneofacial infantil, plagiocefalia, braquiocefalia y seguimiento de órtesis dinámicas** con arquitectura multi-sede (Quito Citimed & Lima San Isidro).

---

## 🌟 Características Principales

### 👶 Gestión Clínica Pediátrica Especializada
- **Ficha Integral de Lactantes y Tutores:** Registro clínico completo de pacientes pediátricos, percentiles de perímetro cefálico y antecedentes gestacionales/natales.
- **Biometría Craneofacial Computarizada:** Cálculo automático del índice de asimetría de bóveda craneal (**CVAI**) e índice cefálico (**CI**) según estándares antropométricos pediátricos internacionales.
- **Visualizador & Exportador 3D:** Carga, procesamiento e inspección de escaneos craneales en mallas 3D (`.obj`, `.stl`) con trazado de evolución por etapas de modelado ortésico (T0, T1, T2...).

### 🏥 Arquitectura Multi-Sede (Database-per-Branch)
- **Sedes Independientes:** Base de datos aislada por sede (`cranium_quito.db`, `cranium_lima.db`) y base global federada (`cranium_core.db`) para control de accesos, doctores y secretarias.
- **Roles y Permisos Granulares:**
  - *Superadministrador:* Gestión de sedes, doctores, secretarias, configuración de empresa y facturación.
  - *Doctor Especialista:* Agenda quirúrgica/clínica, historiales médicos, diagnósticos 3D y emisión de recetas firmadas digitalmente.
  - *Secretaria:* Recepción, activación por WhatsApp OTP, triaje y emisión de cobros/recibos.

### ✍️ Firma Electrónica Oficial MSP (Ecuador / Perú)
- Compatibilidad nativa con certificados PKCS#12 (`.p12` / `.pfx`) emitidos por Security Data, Banco Central del Ecuador, ANF, Uanataca y Consejo de la Judicatura.
- Firma criptográfica SHA-256 con sellado de tiempo para recetas médicas, informes de asimetría y consentimientos informados.

### 🧾 Facturación Electrónica Transfronteriza (SRI & SUNAT)
- **Ecuador (SRI):** Generación de comprobantes XML v1.1.0, esquema RIDE, firma XAdES-BES y validación de claves de acceso de 49 dígitos.
- **Perú (SUNAT):** Emisión de Facturas (serie `F001`) y Boletas (serie `B001`) con cálculo de IGV y detracción.

### 🎨 Experiencia de Usuario & Neuromarketing Clínico
- **Diseño Ergonómico Light:** Paleta de colores basada en psicología médica pediátrica (índigo suave de confianza clínica, toques ámbar cálidos y esmeralda de sanación).
- **Cero Polución Visual:** Formularios limpios sin placeholders redundantes, contraste WCAG AAA para legibilidad hospitalaria sin fatiga visual.

---

## 🚀 Puesta en Marcha Local

### Prerrequisitos
- Python 3.10+
- Navegador web moderno (Chrome, Edge, Safari, Firefox)

### Instalación y Ejecución

```bash
# 1. Clonar el repositorio
git clone git@github.com:Danny3969/CraniumFit.git
cd CraniumFit

# 2. Configurar el entorno virtual Python
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install fastapi uvicorn cryptography pydantic python-multipart pyopenssl

# 4. Iniciar servicios con PM2 o script nativo
./start.sh
# O ejecutar manualmente el backend:
# uvicorn backend.main:app --host 0.0.0.0 --port 8096 --reload
```

El aplicativo estará disponible en:
- **ERP Clínico:** `http://localhost:8096`
- **Documentación OpenAPI / Swagger:** `http://localhost:8096/docs`

---

## 📂 Estructura del Proyecto

```text
CraniumFit/
├── backend/
│   ├── main.py                  # API Gateway FastAPI y enrutamiento REST
│   ├── database.py              # Motor multi-sede SQLite (Core, Quito, Lima)
│   ├── craniometrics.py         # Algoritmos de cálculo CVAI y diagnóstico
│   ├── mesh_exporter.py         # Procesamiento y visualización de mallas 3D
│   ├── signature_service.py     # Motor PKCS#12 para firma electrónica médica
│   ├── sri_service.py           # Integración tributaria SRI / SUNAT
│   ├── whatsapp_service.py      # Servicio de mensajería y OTP
│   └── uploads/                 # Almacenamiento local de mallas y firmas
├── frontend/
│   ├── index.html               # Single Page Application (SPA) médica ergonómica
│   └── assets/                  # Logos e iconografía clínica
├── ecosystem.config.js          # Orquestador PM2 para producción
├── cranium_tunnel_daemon.py     # Demonio de túnel seguro Cloudflare
└── start.sh                     # Script unificado de inicio de servicios
```

---

## 🔒 Privacidad y Cumplimiento Normativo
Cumple con las normativas locales de protección de datos de salud infantil y leyes de expedientes médicos electrónicos (MSP Ecuador / MINSA Perú).
