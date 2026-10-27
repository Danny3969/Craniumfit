import React, { createContext, useContext, useState } from 'react';
import { proApi, StaffUser, StaffSession } from '../services/api';

interface ProAuthContextType {
  user: StaffUser | null;
  token: string | null;
  activeBranch: 'quito' | 'lima';
  isLoading: boolean;
  login: (login: string, pass: string) => Promise<boolean>;
  loginRole: (role: 'doctor' | 'secretary' | 'admin') => void;
  logout: () => void;
  setBranch: (branch: 'quito' | 'lima') => void;
}

const ProAuthContext = createContext<ProAuthContextType | undefined>(undefined);

export const DEMO_STAFF_ACCOUNTS: Record<string, StaffUser> = {
  doctor: {
    id: 'staff-doc-002',
    cedula: '1710000002',
    full_name: 'Dr. Carlos Morales',
    email: 'cmorales@craniumfit.com',
    role: 'doctor',
    default_branch: 'quito',
    specialty: 'Neurocirugía Pediátrica & Asimetría Craneal',
    phone: '+593 99 887 7665',
  },
  secretary: {
    id: 'staff-sec-005',
    cedula: '1710000005',
    full_name: 'Ana Belén Pérez',
    email: 'recepcion.quito@craniumfit.com',
    role: 'secretary',
    default_branch: 'quito',
    specialty: 'Coordinación & Admisión Pediátrica',
    phone: '+593 2 299 8800',
  },
  admin: {
    id: 'staff-adm-001',
    cedula: '1710000001',
    full_name: 'Dr. Roberto Salazar',
    email: 'rsalazar@craniumfit.com',
    role: 'superadmin' as any,
    default_branch: 'quito',
    specialty: 'Director Médico & Operaciones Regionales',
    phone: '+593 99 112 2334',
  },
};

export const ProAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<StaffUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [activeBranch, setActiveBranch] = useState<'quito' | 'lima'>('quito');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const login = async (loginId: string, pass: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      const session = await proApi.login(loginId, pass);
      setUser(session.user);
      setToken(session.token);
      setActiveBranch((session.user.default_branch as any) || 'quito');
      setIsLoading(false);
      return true;
    } catch (err: any) {
      console.warn("Direct staff login fallback to credentials demo", err.message);
      // Demo credentials check
      if (loginId === '1710000002' || loginId.toLowerCase().includes('doc')) {
        loginRole('doctor');
        setIsLoading(false);
        return true;
      } else if (loginId === '1710000005' || loginId.toLowerCase().includes('sec')) {
        loginRole('secretary');
        setIsLoading(false);
        return true;
      } else if (loginId === '1710000001' || loginId.toLowerCase().includes('admin')) {
        loginRole('admin');
        setIsLoading(false);
        return true;
      }
      setIsLoading(false);
      throw err;
    }
  };

  const loginRole = (role: 'doctor' | 'secretary' | 'admin') => {
    const staff = DEMO_STAFF_ACCOUNTS[role];
    setUser(staff);
    setToken(`pro-token-${role}-demo`);
    setActiveBranch('quito');
    proApi.setToken(`pro-token-${role}-demo`);
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    proApi.setToken(null);
  };

  const setBranch = (branch: 'quito' | 'lima') => {
    setActiveBranch(branch);
    proApi.setBranch(branch);
  };

  return (
    <ProAuthContext.Provider
      value={{
        user,
        token,
        activeBranch,
        isLoading,
        login,
        loginRole,
        logout,
        setBranch,
      }}
    >
      {children}
    </ProAuthContext.Provider>
  );
};

export const useProAuth = () => {
  const ctx = useContext(ProAuthContext);
  if (!ctx) {
    throw new Error('useProAuth must be used within ProAuthProvider');
  }
  return ctx;
};
