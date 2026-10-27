/**
 * CRANIUMFIT FAMILIAS — Cliente de API & Conexión al Backend
 * Conecta la aplicación móvil de padres con el backend FastAPI de CraniumFit.
 */

// URL base del backend: preferir túnel Cloudflare seguro o IP local según entorno
export const API_BASE_URL = "https://tar-prep-evanescence-bullet.trycloudflare.com";
export const API_LOCAL_FALLBACK = "http://127.0.0.1:8096";

export interface UserSession {
  token: string;
  user: {
    id: string;
    cedula: string;
    full_name: string;
    phone: string;
    email: string;
    role: string;
    default_branch: string;
  };
}

export interface BabySummary {
  id: string;
  first_name: string;
  last_name: string;
  birth_date: string;
  sex: string;
  diagnosis: string;
  photo_url?: string;
  patient_dni?: string;
  doctor_name?: string;
  doctor_specialty?: string;
}

export interface BabyDashboardData {
  baby: BabySummary;
  treatment?: any;
  today_wear: {
    hours_worn: number;
    target_hours: number;
    completion_pct: number;
    status: string;
    streak_days: number;
  };
  recent_wear_logs: Array<{
    log_date: string;
    hours_worn: number;
    pauses_count: number;
    notes?: string;
  }>;
  evolution: {
    baseline_cvai: number;
    current_cvai: number;
    delta: number;
    reduction_pct: number;
    sessions_count: number;
    baseline_scan?: any;
    latest_scan?: any;
    scans: any[];
  };
  active_prescription?: any;
  next_appointment?: any;
  dossiers: any[];
}

class CraniumApi {
  private baseUrl: string =
    typeof window !== 'undefined' && window.location && window.location.origin && !window.location.origin.includes(':8081')
      ? window.location.origin
      : API_BASE_URL;
  private currentBranch: string = "quito";
  private token: string | null = null;

  constructor() {}

  setBranch(branch: string) {
    this.currentBranch = branch;
  }

  setToken(token: string | null) {
    this.token = token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "X-Branch-ID": this.currentBranch,
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    try {
      const res = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers,
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Error en servidor (${res.status})`);
      }

      return (await res.json()) as T;
    } catch (err: any) {
      // Fallback a URL local si falla la conexión primaria
      if (err.message.includes("Network") && this.baseUrl !== API_LOCAL_FALLBACK) {
        this.baseUrl = API_LOCAL_FALLBACK;
        return this.request<T>(endpoint, options);
      }
      throw err;
    }
  }

  // ── AUTENTICACIÓN & REGISTRO OTP POR WHATSAPP ─────────────────────────────

  async resendOtp(cedula: string): Promise<{ success: boolean; message: string; otp_simulated?: string }> {
    return this.request("/api/auth/resend-otp", {
      method: "POST",
      body: JSON.stringify({ cedula: cedula.trim() }),
    });
  }

  async verifyOtp(cedula: string, code: string): Promise<{ success: boolean; message: string; user: any }> {
    return this.request("/api/auth/verify-otp", {
      method: "POST",
      body: JSON.stringify({ cedula: cedula.trim(), code: code.trim() }),
    });
  }

  async setPassword(cedula: string, newPassword: string): Promise<{ success: boolean; token: string; user: any }> {
    return this.request("/api/auth/set-password", {
      method: "POST",
      body: JSON.stringify({ cedula: cedula.trim(), new_password: newPassword.trim() }),
    });
  }

  async login(login: string, password: string): Promise<UserSession> {
    const data = await this.request<UserSession>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ login: login.trim(), password: password.trim() }),
    });
    if (data.token) {
      this.setToken(data.token);
    }
    return data;
  }

  // ── DATOS DEL PACIENTE Y DASHBOARD ────────────────────────────────────────

  async getMyBabies(parentCedula?: string): Promise<{ babies: BabySummary[]; count: number }> {
    const query = parentCedula ? `?parent_id=${encodeURIComponent(parentCedula)}` : "";
    return this.request(`/api/parent/my-babies${query}`);
  }

  async getBabyDashboard(babyId: string): Promise<BabyDashboardData> {
    return this.request(`/api/parent/baby/${babyId}/dashboard`);
  }

  async logWearTime(babyId: string, hours: number, pauses: number = 0, notes: string = ""): Promise<any> {
    return this.request(`/api/parent/baby/${babyId}/log-wear`, {
      method: "POST",
      body: JSON.stringify({
        hours_worn: hours,
        pauses_count: pauses,
        notes,
      }),
    });
  }

  async getMedicalHistory(patientId: string): Promise<any> {
    return this.request(`/api/patients/${patientId}/medical-history`);
  }

  async getDoctors(): Promise<any> {
    return this.request(`/api/doctors`);
  }

  async createAppointmentRequest(payload: {
    patient_id: string;
    doctor_id: string;
    appointment_date: string;
    start_time: string;
    reason: string;
  }): Promise<any> {
    return this.request(`/api/appointments`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }
}

export const api = new CraniumApi();
