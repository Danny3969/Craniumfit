import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useProAuth } from '../context/AuthContext';
import {
  TrendingUp,
  Users,
  ShieldCheck,
  Building2,
  DollarSign,
  AlertTriangle,
  Phone,
  Sparkles,
  LogOut,
  Layers,
} from 'lucide-react-native';

export default function AdminKpiScreen() {
  const { user, activeBranch, setBranch, logout } = useProAuth();

  const [selectedKpiBranch, setSelectedKpiBranch] = useState<'all' | 'quito' | 'lima'>('all');

  const branches = [
    {
      id: 'quito-norte',
      name: 'Sede Quito Norte',
      city: 'Ecuador',
      activePatients: 74,
      helmetsInLab: 9,
      complianceRate: '94.8%',
      revenue: '$24,800',
    },
    {
      id: 'quito-cumbaya',
      name: 'Sede Quito Cumbayá',
      city: 'Ecuador',
      activePatients: 38,
      helmetsInLab: 4,
      complianceRate: '93.1%',
      revenue: '$12,450',
    },
    {
      id: 'lima-miraflores',
      name: 'Sede Lima Miraflores',
      city: 'Perú',
      activePatients: 36,
      helmetsInLab: 5,
      complianceRate: '91.7%',
      revenue: '$11,000',
    },
  ];

  const atRiskPatients = [
    {
      id: 'risk-01',
      babyName: 'Emilio Andrade (4 meses)',
      parentName: 'Carla Viteri',
      phone: '+593 99 333 4455',
      avgWear: '15.2h / día',
      issue: 'Bajo cumplimiento en últimas 72 horas (meta 23h). Posible molestia en zona temporal.',
      branch: 'Sede Quito Norte',
    },
    {
      id: 'risk-02',
      babyName: 'Mia Salazar (6 meses)',
      parentName: 'Fernando Salazar',
      phone: '+51 987 654 321',
      avgWear: '16.8h / día',
      issue: 'Retirado por sospecha de dermatitis de contacto.',
      branch: 'Sede Lima Miraflores',
    },
  ];

  const handleCallFollowUp = (p: any) => {
    Alert.alert(
      'Llamada de Acompañamiento',
      `Iniciando llamada con ${p.parentName} (${p.phone}) para soporte clínico inmediato en ${p.babyName}.`
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.topHeader}>
          <View>
            <Text style={styles.title}>{user?.full_name}</Text>
            <Text style={styles.subtitle}>SuperAdmin & Dirección Médica Regional</Text>
          </View>
          <TouchableOpacity style={styles.logoutBtn} onPress={logout}>
            <LogOut size={18} color="#64748B" />
          </TouchableOpacity>
        </View>

        {/* Global KPI Cards Grid */}
        <View style={styles.kpiGrid}>
          <View style={styles.kpiCard}>
            <View style={styles.kpiIconBoxTeal}>
              <Users size={18} color="#0D9488" />
            </View>
            <Text style={styles.kpiValue}>148</Text>
            <Text style={styles.kpiLabel}>Bebés Activos en Tratamiento</Text>
          </View>

          <View style={styles.kpiCard}>
            <View style={styles.kpiIconBoxBlue}>
              <Layers size={18} color="#0284C7" />
            </View>
            <Text style={styles.kpiValue}>18</Text>
            <Text style={styles.kpiLabel}>Ortesis en Impresión 3D</Text>
          </View>
        </View>

        <View style={styles.kpiGrid}>
          <View style={styles.kpiCard}>
            <View style={styles.kpiIconBoxGreen}>
              <TrendingUp size={18} color="#15803D" />
            </View>
            <Text style={[styles.kpiValue, { color: '#15803D' }]}>93.4%</Text>
            <Text style={styles.kpiLabel}>Adherencia Media (Meta 23h)</Text>
          </View>

          <View style={styles.kpiCard}>
            <View style={styles.kpiIconBoxPurple}>
              <DollarSign size={18} color="#7C3AED" />
            </View>
            <Text style={styles.kpiValue}>$48,250</Text>
            <Text style={styles.kpiLabel}>Facturación Mes Corriente</Text>
          </View>
        </View>

        {/* Multi-Branch Performance */}
        <Text style={styles.sectionTitle}>Rendimiento por Sede Pediátrica</Text>
        {branches.map((b) => (
          <View key={b.id} style={styles.branchCard}>
            <View style={styles.branchHeader}>
              <View style={styles.branchIconBox}>
                <Building2 size={18} color="#0D9488" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.branchName}>{b.name}</Text>
                <Text style={styles.branchCity}>{b.city}</Text>
              </View>
              <View style={styles.complianceBadge}>
                <Text style={styles.complianceBadgeText}>{b.complianceRate} uso</Text>
              </View>
            </View>

            <View style={styles.branchMetricsRow}>
              <View style={styles.branchMetricCol}>
                <Text style={styles.branchMetricLab}>Pacientes</Text>
                <Text style={styles.branchMetricVal}>{b.activePatients}</Text>
              </View>
              <View style={styles.branchDivider} />
              <View style={styles.branchMetricCol}>
                <Text style={styles.branchMetricLab}>En Laboratorio</Text>
                <Text style={styles.branchMetricVal}>{b.helmetsInLab}</Text>
              </View>
              <View style={styles.branchDivider} />
              <View style={styles.branchMetricCol}>
                <Text style={styles.branchMetricLab}>Ingresos</Text>
                <Text style={[styles.branchMetricVal, { color: '#0F766E' }]}>
                  {b.revenue}
                </Text>
              </View>
            </View>
          </View>
        ))}

        {/* Clinical Alert Section: Low Adherence / Risk Cases */}
        <View style={styles.alertSectionHeader}>
          <AlertTriangle size={18} color="#DC2626" />
          <Text style={styles.alertSectionTitle}>
            Casos con Desviación de Protocolo (&lt;18h de uso)
          </Text>
        </View>

        {atRiskPatients.map((r) => (
          <View key={r.id} style={styles.riskCard}>
            <View style={styles.riskTop}>
              <Text style={styles.riskBabyName}>{r.babyName}</Text>
              <View style={styles.riskBadge}>
                <Text style={styles.riskBadgeText}>{r.avgWear}</Text>
              </View>
            </View>
            <Text style={styles.riskIssue}>{r.issue}</Text>
            <Text style={styles.riskBranch}>{r.branch} · Contacto: {r.parentName}</Text>

            <TouchableOpacity
              style={styles.btnFollowUp}
              onPress={() => handleCallFollowUp(r)}
            >
              <Phone size={14} color="#FFFFFF" />
              <Text style={styles.btnFollowUpText}>Coordinar Soporte Clínico</Text>
            </TouchableOpacity>
          </View>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  scrollContent: {
    paddingHorizontal: 18,
    paddingTop: 12,
    paddingBottom: 40,
    maxWidth: 600,
    width: '100%',
    alignSelf: 'center',
  },
  topHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: '800',
    color: '#0F172A',
  },
  subtitle: {
    fontSize: 11,
    color: '#0D9488',
    fontWeight: '600',
    marginTop: 2,
  },
  logoutBtn: {
    padding: 8,
    backgroundColor: '#F1F5F9',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  kpiGrid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  kpiCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2,
  },
  kpiIconBoxTeal: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#CCFBF1',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  kpiIconBoxBlue: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#E0F2FE',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  kpiIconBoxGreen: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#DCFCE7',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  kpiIconBoxPurple: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#F3E8FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  kpiValue: {
    fontSize: 22,
    fontWeight: '900',
    color: '#0F172A',
  },
  kpiLabel: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 2,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
    marginTop: 10,
    marginBottom: 10,
  },
  branchCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 12,
  },
  branchHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 12,
  },
  branchIconBox: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#CCFBF1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  branchName: {
    fontSize: 14,
    fontWeight: '800',
    color: '#0F172A',
  },
  branchCity: {
    fontSize: 11,
    color: '#64748B',
  },
  complianceBadge: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  complianceBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#15803D',
  },
  branchMetricsRow: {
    flexDirection: 'row',
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    padding: 10,
  },
  branchMetricCol: {
    flex: 1,
    alignItems: 'center',
  },
  branchDivider: {
    width: 1,
    height: 20,
    backgroundColor: '#E2E8F0',
    alignSelf: 'center',
  },
  branchMetricLab: {
    fontSize: 10,
    color: '#64748B',
  },
  branchMetricVal: {
    fontSize: 14,
    fontWeight: '800',
    color: '#0F172A',
    marginTop: 1,
  },
  alertSectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 16,
    marginBottom: 10,
  },
  alertSectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#DC2626',
  },
  riskCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1.5,
    borderColor: '#FECACA',
    marginBottom: 10,
  },
  riskTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  riskBabyName: {
    fontSize: 14,
    fontWeight: '800',
    color: '#0F172A',
  },
  riskBadge: {
    backgroundColor: '#FEE2E2',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  riskBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#DC2626',
  },
  riskIssue: {
    fontSize: 12,
    color: '#475569',
    marginTop: 2,
    lineHeight: 16,
  },
  riskBranch: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 4,
  },
  btnFollowUp: {
    backgroundColor: '#DC2626',
    borderRadius: 8,
    paddingVertical: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 10,
  },
  btnFollowUpText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
  },
});
