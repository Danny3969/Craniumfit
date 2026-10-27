import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity, Text, Platform } from 'react-native';
import { useProAuth } from '../context/AuthContext';
import ProLoginScreen from '../screens/ProLoginScreen';
import DoctorAgendaScreen from '../screens/DoctorAgendaScreen';
import DoctorCvaiCalcScreen from '../screens/DoctorCvaiCalcScreen';
import DoctorPrescribeScreen from '../screens/DoctorPrescribeScreen';
import SecretaryWaitingRoomScreen from '../screens/SecretaryWaitingRoomScreen';
import AdminKpiScreen from '../screens/AdminKpiScreen';
import {
  Calendar,
  Calculator,
  FileCheck2,
  Users,
  Activity,
} from 'lucide-react-native';

export default function ProNavigationRoot() {
  const { user } = useProAuth();
  const [activeTab, setActiveTab] = useState<string>('tab1');

  if (!user) {
    return <ProLoginScreen />;
  }

  let tabs: Array<{ key: string; label: string; icon: any; screen: React.ReactNode }> = [];

  if (user.role === 'doctor') {
    tabs = [
      { key: 'agenda', label: 'Mi Agenda', icon: Calendar, screen: <DoctorAgendaScreen /> },
      { key: 'calc', label: 'Calc CVAI', icon: Calculator, screen: <DoctorCvaiCalcScreen /> },
      { key: 'rx', label: 'Recetas & .p12', icon: FileCheck2, screen: <DoctorPrescribeScreen /> },
    ];
  } else if (user.role === 'secretary') {
    tabs = [
      { key: 'waiting', label: 'Sala de Espera', icon: Users, screen: <SecretaryWaitingRoomScreen /> },
      { key: 'agenda', label: 'Agenda Médica', icon: Calendar, screen: <DoctorAgendaScreen /> },
      { key: 'calc', label: 'Mediciones', icon: Calculator, screen: <DoctorCvaiCalcScreen /> },
    ];
  } else {
    tabs = [
      { key: 'kpis', label: 'KPIs & Sedes', icon: Activity, screen: <AdminKpiScreen /> },
      { key: 'agenda', label: 'Agenda Global', icon: Calendar, screen: <DoctorAgendaScreen /> },
      { key: 'calc', label: 'Calculadora', icon: Calculator, screen: <DoctorCvaiCalcScreen /> },
    ];
  }

  const currentTab = tabs.find((t) => t.key === activeTab) || tabs[0];

  return (
    <View style={styles.container}>
      <View style={styles.screenContainer}>{currentTab.screen}</View>

      <View style={styles.bottomBar}>
        {tabs.map((t) => {
          const Icon = t.icon;
          const isActive = currentTab.key === t.key;
          return (
            <TouchableOpacity
              key={t.key}
              style={[styles.tabItem, isActive && styles.tabItemActive]}
              onPress={() => setActiveTab(t.key)}
            >
              <Icon size={20} color={isActive ? '#0D9488' : '#64748B'} />
              <Text style={[styles.tabLabel, isActive && styles.tabLabelActive]}>
                {t.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  screenContainer: {
    flex: 1,
  },
  bottomBar: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
    paddingVertical: 8,
    paddingBottom: Platform.OS === 'ios' ? 24 : 10,
    paddingHorizontal: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 8,
    maxWidth: 600,
    width: '100%',
    alignSelf: 'center',
  },
  tabItem: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 4,
    borderRadius: 10,
  },
  tabItemActive: {
    backgroundColor: '#F0FDFA',
  },
  tabLabel: {
    fontSize: 10,
    color: '#64748B',
    marginTop: 3,
    fontWeight: '600',
  },
  tabLabelActive: {
    color: '#0D9488',
    fontWeight: '800',
  },
});
