/**
 * CRANIUMFIT PRO — API Service
 * Cliente de conexión para Médicos, Secretarias y Administradores.
 */

export const API_BASE_URL = "https://tar-prep-evanescence-bullet.trycloudflare.com";
export const API_LOCAL_FALLBACK = "http://127.0.0.1:8096";

export interface StaffUser {
  id: string;
  cedula: string;
  full_name: string;
  email: string;
  role: 'doctor' | 'secretary' | 'admin' | 'superadmin';
  default_branch: string;
  specialty?: string;
  phone?: string;
}

export interface StaffSession {
  token: string;
  user: StaffUser;
}

class CraniumProApi {
  private baseUrl: string =
    typeof window !== 'undefined' && window.location && window.location.origin && !window.location.origin.includes(':8081')
      ? window.location.origin
      : API_BASE_URL;
  private currentBranch: string = "quito";
  private token: string | null = null;

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
      if (err.message.includes("Network") && this.baseUrl !== API_LOCAL_FALLBACK) {
        this.baseUrl = API_LOCAL_FALLBACK;
        return this.request<T>(endpoint, options);
      }
      throw err;
    }
  }

  // Login de Staff (Médico, Secretaria, Administrador - Sin OTP)
  async login(login: string, pass: string): Promise<StaffSession> {
    const data = await this.request<StaffSession>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ login: login.trim(), password: pass.trim() }),
    });
    if (data.token) {
      this.setToken(data.token);
    }
    return data;
  }

  // Obtener lista de pacientes
  async getPatients(): Promise<any> {
    return this.request("/api/patients");
  }

  // Obtener citas del día
  async getAppointments(): Promise<any> {
    return this.request("/api/appointments");
  }

  // Obtener estadísticas y KPIs
  async getKpis(): Promise<any> {
    return this.request("/api/kpis");
  }

  // Crear prescripción
  async createPrescription(payload: any): Promise<any> {
    return this.request("/api/prescriptions", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // Firmar certificado con .p12
  async signCertificate(payload: any): Promise<any> {
    return this.request("/api/certificates/sign", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }
}

export const proApi = new CraniumProApi();
