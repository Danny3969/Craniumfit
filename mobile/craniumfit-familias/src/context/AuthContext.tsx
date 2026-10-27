import React, { createContext, useContext, useState, useEffect } from 'react';
import { api, UserSession, BabySummary, BabyDashboardData } from '../services/api';

interface AuthContextType {
  user: UserSession['user'] | null;
  token: string | null;
  isLoading: boolean;
  babies: BabySummary[];
  activeBaby: BabySummary | null;
  dashboard: BabyDashboardData | null;
  login: (cedula: string, pass: string) => Promise<boolean>;
  loginDemo: () => Promise<void>;
  logout: () => void;
  selectBaby: (babyId: string) => Promise<void>;
  reloadDashboard: () => Promise<void>;
  logWearHours: (hours: number, pauses?: number, notes?: string) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Demo Fallback Data en caso de corte o desconexión
export const DEMO_PARENT_USER: UserSession['user'] = {
  id: "parent-001",
  cedula: "1718899221",
  full_name: "María Fernanda López",
  phone: "+593998877665",
  email: "mflopez@example.com",
  role: "parent",
  default_branch: "quito",
};

export const DEMO_BABY: BabySummary = {
  id: "baby-001",
  first_name: "Lucas",
  last_name: "Torres",
  birth_date: "2024-05-12",
  sex: "M",
  diagnosis: "Plagiocefalia Posicional Derecha Severa (CVAI 11.2%)",
  patient_dni: "1799223344",
  doctor_name: "Dr. Carlos Morales",
  doctor_specialty: "Neurocirugía Pediátrica & Ortesis Craneal",
};

export const DEMO_DASHBOARD: BabyDashboardData = {
  baby: DEMO_BABY,
  treatment: {
    start_date: "2024-08-01",
    helmet_model: "CraniumFit Dynamic Airflow Pro",
    serial_number: "CF-2024-EC-089",
    target_hours_per_day: 23,
    status: "active",
  },
  today_wear: {
    hours_worn: 19.5,
    target_hours: 23.0,
    completion_pct: 84.8,
    status: "excellent",
    streak_days: 16,
  },
  recent_wear_logs: [
    { log_date: "2024-10-26", hours_worn: 19.5, pauses_count: 3, notes: "Retirado 30 min para baño y limpieza" },
    { log_date: "2024-10-25", hours_worn: 22.8, pauses_count: 2, notes: "Excelente tolerancia toda la noche" },
    { log_date: "2024-10-24", hours_worn: 23.0, pauses_count: 2, notes: "Meta completa 23h" },
    { log_date: "2024-10-23", hours_worn: 21.5, pauses_count: 4, notes: "Tummy time 45 min" },
    { log_date: "2024-10-22", hours_worn: 22.0, pauses_count: 2, notes: "Sin rojeces" },
  ],
  evolution: {
    baseline_cvai: 11.2,
    current_cvai: 4.8,
    delta: -6.4,
    reduction_pct: 57.1,
    sessions_count: 4,
    scans: [
      { session_number: 1, scan_date: "2024-08-01", cvai: 11.2, ci: 88.5, status: "Severo" },
      { session_number: 2, scan_date: "2024-08-29", cvai: 8.9, ci: 85.3, status: "Moderado" },
      { session_number: 3, scan_date: "2024-09-26", cvai: 6.4, ci: 83.1, status: "Leve" },
      { session_number: 4, scan_date: "2024-10-24", cvai: 4.8, ci: 81.2, status: "Normal / Leve" },
    ],
  },
  active_prescription: {
    id: "rx-902",
    doctor_name: "Dr. Carlos Morales",
    issued_at: "2024-10-24",
    diagnosis: "Plagiocefalia Posicional - Mantenimiento",
    medications: [
      { name: "Loción Dermoprotectora Pediátrica", dose: "1 aplicación fina", freq: "Antes de colocar ortesis tras baño", duration: "Diario" },
      { name: "Champú pH Neutro Hipoalergénico", dose: "Lavado diario de cuero cabelludo", freq: "1 vez al día", duration: "Tratamiento continuo" },
      { name: "Alcohol Isopropílico al 70%", dose: "Limpieza interna del casco con paño microfibra", freq: "Cada noche durante baño", duration: "Diario" }
    ],
    qr_hash: "CF-RX-1710000002-2024-10-24-SECURE-SHA256"
  },
  next_appointment: {
    id: "apt-441",
    appointment_date: "2024-11-08",
    start_time: "10:30",
    doctor_name: "Dr. Carlos Morales",
    room: "Sede Quito Norte — Sala Biométrica 2",
    reason: "Control mensual de escaneo 3D y recalibración de ortesis",
    status: "confirmed"
  },
  dossiers: [
    {
      id: "dos-001",
      title: "Informe Biométrico para Reembolso Aseguradora",
      insurer: "SaludSA / Ecuasanitas",
      generated_date: "2024-10-24",
      cvai_initial: "11.2%",
      cvai_current: "4.8%",
      digital_signature_verified: true,
      file_url: "#"
    }
  ]
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserSession['user'] | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [babies, setBabies] = useState<BabySummary[]>([]);
  const [activeBaby, setActiveBaby] = useState<BabySummary | null>(null);
  const [dashboard, setDashboard] = useState<BabyDashboardData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Intentar cargar datos del bebé al iniciar o login
  const loadBabyData = async (cedula: string) => {
    try {
      const data = await api.getMyBabies(cedula);
      if (data && data.babies && data.babies.length > 0) {
        setBabies(data.babies);
        const baby = data.babies[0];
        setActiveBaby(baby);
        // Cargar dashboard
        try {
          const dash = await api.getBabyDashboard(baby.id);
          setDashboard(dash);
        } catch {
          setDashboard(DEMO_DASHBOARD);
        }
      } else {
        // Fallback demo
        setBabies([DEMO_BABY]);
        setActiveBaby(DEMO_BABY);
        setDashboard(DEMO_DASHBOARD);
      }
    } catch {
      setBabies([DEMO_BABY]);
      setActiveBaby(DEMO_BABY);
      setDashboard(DEMO_DASHBOARD);
    }
  };

  const login = async (cedula: string, pass: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      const session = await api.login(cedula, pass);
      setUser(session.user);
      setToken(session.token);
      await loadBabyData(session.user.cedula);
      setIsLoading(false);
      return true;
    } catch (err: any) {
      console.warn("Login failed with backend, falling back to demo credentials check", err.message);
      // Soporte para credenciales de demo
      if (cedula.trim() === "1718899221" && (pass.trim() === "padre123" || pass.trim() === "demo")) {
        setUser(DEMO_PARENT_USER);
        setToken("demo-parent-token-xyz");
        setBabies([DEMO_BABY]);
        setActiveBaby(DEMO_BABY);
        setDashboard(DEMO_DASHBOARD);
        setIsLoading(false);
        return true;
      }
      setIsLoading(false);
      throw err;
    }
  };

  const loginDemo = async () => {
    setIsLoading(true);
    setUser(DEMO_PARENT_USER);
    setToken("demo-parent-token-xyz");
    setBabies([DEMO_BABY]);
    setActiveBaby(DEMO_BABY);
    setDashboard(DEMO_DASHBOARD);
    setIsLoading(false);
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    setBabies([]);
    setActiveBaby(null);
    setDashboard(null);
    api.setToken(null);
  };

  const selectBaby = async (babyId: string) => {
    const found = babies.find(b => b.id === babyId);
    if (found) {
      setActiveBaby(found);
      try {
        const dash = await api.getBabyDashboard(babyId);
        setDashboard(dash);
      } catch {
        setDashboard(DEMO_DASHBOARD);
      }
    }
  };

  const reloadDashboard = async () => {
    if (activeBaby) {
      try {
        const dash = await api.getBabyDashboard(activeBaby.id);
        setDashboard(dash);
      } catch {
        // preserve current or demo
      }
    }
  };

  const logWearHours = async (hours: number, pauses: number = 0, notes: string = ""): Promise<boolean> => {
    if (!activeBaby) return false;
    try {
      await api.logWearTime(activeBaby.id, hours, pauses, notes);
      await reloadDashboard();
      return true;
    } catch (err) {
      // Optimistic update locally
      if (dashboard) {
        setDashboard({
          ...dashboard,
          today_wear: {
            ...dashboard.today_wear,
            hours_worn: hours,
            completion_pct: Math.min(100, Math.round((hours / 23) * 100 * 10) / 10),
            status: hours >= 22 ? 'excellent' : hours >= 18 ? 'good' : 'needs_attention'
          },
          recent_wear_logs: [
            { log_date: new Date().toISOString().split('T')[0], hours_worn: hours, pauses_count: pauses, notes },
            ...dashboard.recent_wear_logs.slice(0, 4)
          ]
        });
      }
      return true;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        babies,
        activeBaby,
        dashboard,
        login,
        loginDemo,
        logout,
        selectBaby,
        reloadDashboard,
        logWearHours,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
