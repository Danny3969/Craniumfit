import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Modal,
  TextInput,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useProAuth } from '../context/AuthContext';
import {
  Calendar,
  Clock,
  User,
  CheckCircle2,
  AlertCircle,
  FileText,
  Activity,
  LogOut,
  Building2,
  ChevronRight,
  TrendingDown,
  Stethoscope,
} from 'lucide-react-native';

export default function DoctorAgendaScreen() {
  const { user, activeBranch, setBranch, logout } = useProAuth();

  const [selectedPatient, setSelectedPatient] = useState<any | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [clinicalNotes, setClinicalNotes] = useState('');

  const todayAgenda = [
    {
      id: 'apt-01',
      time: '10:00 AM',
      patientName: 'Lucas Torres',
      age: '5 meses',
      diagnosis: 'Plagiocefalia Posicional Derecha',
      cvai: '4.8%',
      initialCvai: '11.2%',
      status: 'waiting',
      statusText: 'En Sala de Espera',
      reason: 'Control mensual de escaneo 3D y recalibración de zonas de expansión',
      parentName: 'María Fernanda López (Madre)',
      parentPhone: '+593 99 887 7665',
    },
    {
      id: 'apt-02',
      time: '10:45 AM',
      patientName: 'Mateo Benítez',
      age: '4 meses',
      diagnosis: 'Braquicefalia Moderada',
      cvai: '3.1%',
      ci: '91.4%',
      status: 'waiting',
      statusText: 'En Sala de Espera',
      reason: 'Evaluación antropométrica inicial y toma de molde fotogramétrico',
      parentName: 'David Benítez (Padre)',
      parentPhone: '+593 98 443 2211',
    },
    {
      id: 'apt-03',
      time: '11:30 AM',
      patientName: 'Sofía Cárdenas',
      age: '6 meses',
      diagnosis: 'Escafocefalia Leve / Posicional',
      cvai: '5.2%',
      ci: '72.1%',
      status: 'scheduled',
      statusText: 'Programada',
      reason: 'Entrega de ortesis CraniumFit Airflow Pro y prueba de tolerancia',
      parentName: 'Valeria Gómez (Madre)',
      parentPhone: '+593 99 555 1234',
    },
    {
      id: 'apt-04',
      time: '12:15 PM',
      patientName: 'Joaquín Mora',
      age: '7 meses',
      diagnosis: 'Plagiocefalia Posicional Izquierda',
      cvai: '2.8%',
      initialCvai: '9.4%',
      status: 'completed',
      statusText: 'Atendido (Alta Médica)',
      reason: 'Control final de simetría y certificación de alta médica',
      parentName: 'Carolina Mora (Madre)',
      parentPhone: '+593 99 222 9988',
    },
  ];

  const handleOpenPatient = (p: any) => {
    setSelectedPatient(p);
    setClinicalNotes(
      `Paciente ${p.patientName} (${p.age}). Diagnóstico: ${p.diagnosis}. CVAI actual: ${p.cvai}. Tolerancia adecuada. Sin puntos dolorosos ni úlceras por presión.`
    );
    setModalVisible(true);
  };

  const handleSaveConsultation = () => {
    Alert.alert(
      'Consulta Guardada',
      `Ficha clínica de ${selectedPatient?.patientName} actualizada con éxito en la base de datos de ${activeBranch.toUpperCase()}.`,
      [{ text: 'Aceptar', onPress: () => setModalVisible(false) }]
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Top Header */}
        <View style={styles.topHeader}>
          <View>
            <Text style={styles.doctorGreeting}>{user?.full_name}</Text>
            <Text style={styles.doctorSpec}>{user?.specialty}</Text>
          </View>
          <TouchableOpacity style={styles.logoutBtn} onPress={logout}>
            <LogOut size={18} color="#64748B" />
          </TouchableOpacity>
        </View>

        {/* Branch Switcher */}
        <View style={styles.branchRow}>
          <View style={styles.branchIcon}>
            <Building2 size={16} color="#0D9488" />
          </View>
          <Text style={styles.branchLabel}>Sede Activa:</Text>
          <TouchableOpacity
            style={[
              styles.branchPill,
              activeBranch === 'quito' && styles.branchPillActive,
            ]}
            onPress={() => setBranch('quito')}
          >
            <Text
              style={[
                styles.branchPillText,
                activeBranch === 'quito' && styles.branchPillTextActive,
              ]}
            >
              Quito Norte
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.branchPill,
              activeBranch === 'lima' && styles.branchPillActive,
            ]}
            onPress={() => setBranch('lima')}
          >
            <Text
              style={[
                styles.branchPillText,
                activeBranch === 'lima' && styles.branchPillTextActive,
              ]}
            >
              Lima Miraflores
            </Text>
          </TouchableOpacity>
        </View>

        {/* Quick Agenda Stats */}
        <View style={styles.statsRow}>
          <View style={styles.statBox}>
            <Text style={styles.statVal}>4</Text>
            <Text style={styles.statLab}>Pacientes Hoy</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statBox}>
            <Text style={[styles.statVal, { color: '#EA580C' }]}>2</Text>
            <Text style={styles.statLab}>En Espera</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statBox}>
            <Text style={[styles.statVal, { color: '#16A34A' }]}>1</Text>
            <Text style={styles.statLab}>Alta Médica</Text>
          </View>
        </View>

        <Text style={styles.sectionTitle}>Agenda de Consultas Pediátricas</Text>

        {/* Agenda Cards */}
        {todayAgenda.map((item) => (
          <TouchableOpacity
            key={item.id}
            style={styles.card}
            onPress={() => handleOpenPatient(item)}
          >
            <View style={styles.cardTop}>
              <View style={styles.timeBadge}>
                <Clock size={12} color="#0D9488" />
                <Text style={styles.timeText}>{item.time}</Text>
              </View>

              <View
                style={[
                  styles.statusBadge,
                  item.status === 'waiting'
                    ? styles.statusBadgeOrange
                    : item.status === 'completed'
                    ? styles.statusBadgeGreen
                    : styles.statusBadgeBlue,
                ]}
              >
                <Text
                  style={[
                    styles.statusBadgeText,
                    item.status === 'waiting'
                      ? styles.statusBadgeTextOrange
                      : item.status === 'completed'
                      ? styles.statusBadgeTextGreen
                      : styles.statusBadgeTextBlue,
                  ]}
                >
                  {item.statusText}
                </Text>
              </View>
            </View>

            <View style={styles.cardMain}>
              <Text style={styles.patientName}>
                {item.patientName} <Text style={styles.patientAge}>({item.age})</Text>
              </Text>
              <Text style={styles.patientDiag}>{item.diagnosis}</Text>
              <Text style={styles.reasonText}>{item.reason}</Text>

              <View style={styles.metricsPillRow}>
                <View style={styles.metricPill}>
                  <Text style={styles.metricPillText}>
                    CVAI: <Text style={{ fontWeight: '700' }}>{item.cvai}</Text>
                  </Text>
                </View>
                {item.initialCvai && (
                  <View style={styles.metricPillDelta}>
                    <TrendingDown size={12} color="#15803D" />
                    <Text style={styles.metricPillDeltaText}>
                      Inicial {item.initialCvai}
                    </Text>
                  </View>
                )}
              </View>
            </View>

            <View style={styles.cardFooter}>
              <Text style={styles.parentText}>Acompañante: {item.parentName}</Text>
              <View style={styles.btnActionRow}>
                <Text style={styles.btnActionText}>Abrir Ficha</Text>
                <ChevronRight size={14} color="#0D9488" />
              </View>
            </View>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Patient Consultation Modal */}
      <Modal
        visible={modalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.modalHeader}>
              <View>
                <Text style={styles.modalTitle}>
                  Consulta: {selectedPatient?.patientName}
                </Text>
                <Text style={styles.modalSub}>
                  {selectedPatient?.diagnosis} · {selectedPatient?.age}
                </Text>
              </View>
              <TouchableOpacity onPress={() => setModalVisible(false)}>
                <Text style={styles.modalClose}>Cerrar</Text>
              </TouchableOpacity>
            </View>

            <ScrollView showsVerticalScrollIndicator={false}>
              <View style={styles.modalStatsGrid}>
                <View style={styles.modalStatCol}>
                  <Text style={styles.modalStatLabel}>CVAI Actual</Text>
                  <Text style={styles.modalStatValue}>{selectedPatient?.cvai}</Text>
                </View>
                <View style={styles.modalStatCol}>
                  <Text style={styles.modalStatLabel}>CVAI Inicial</Text>
                  <Text style={styles.modalStatValue}>{selectedPatient?.initialCvai || '—'}</Text>
                </View>
                <View style={styles.modalStatCol}>
                  <Text style={styles.modalStatLabel}>Uso Promedio</Text>
                  <Text style={[styles.modalStatValue, { color: '#0D9488' }]}>21.8h / 23h</Text>
                </View>
              </View>

              <Text style={styles.inputTitle}>Notas Clínicas & Ajuste de Ortesis:</Text>
              <TextInput
                style={styles.textArea}
                value={clinicalNotes}
                onChangeText={setClinicalNotes}
                multiline
                numberOfLines={5}
                textAlignVertical="top"
              />

              <TouchableOpacity
                style={styles.btnSaveConsultation}
                onPress={handleSaveConsultation}
              >
                <CheckCircle2 size={18} color="#FFFFFF" />
                <Text style={styles.btnSaveConsultationText}>
                  Guardar Consulta & Actualizar Ficha
                </Text>
              </TouchableOpacity>
            </ScrollView>
          </View>
        </View>
      </Modal>
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
    marginBottom: 12,
  },
  doctorGreeting: {
    fontSize: 20,
    fontWeight: '800',
    color: '#0F172A',
  },
  doctorSpec: {
    fontSize: 11,
    color: '#0D9488',
    fontWeight: '600',
    marginTop: 1,
  },
  logoutBtn: {
    padding: 8,
    backgroundColor: '#F1F5F9',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  branchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 14,
    gap: 8,
  },
  branchIcon: {
    paddingLeft: 4,
  },
  branchLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748B',
  },
  branchPill: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
    backgroundColor: '#F1F5F9',
  },
  branchPillActive: {
    backgroundColor: '#0D9488',
  },
  branchPillText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#64748B',
  },
  branchPillTextActive: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  statsRow: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 16,
  },
  statBox: {
    flex: 1,
    alignItems: 'center',
  },
  statDivider: {
    width: 1,
    height: 24,
    backgroundColor: '#E2E8F0',
  },
  statVal: {
    fontSize: 18,
    fontWeight: '800',
    color: '#0F172A',
  },
  statLab: {
    fontSize: 10,
    color: '#64748B',
    marginTop: 1,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 10,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2,
  },
  cardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  timeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FDFA',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    gap: 4,
  },
  timeText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#0D9488',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  statusBadgeOrange: {
    backgroundColor: '#FFF7ED',
  },
  statusBadgeGreen: {
    backgroundColor: '#DCFCE7',
  },
  statusBadgeBlue: {
    backgroundColor: '#E0F2FE',
  },
  statusBadgeText: {
    fontSize: 10,
    fontWeight: '700',
  },
  statusBadgeTextOrange: {
    color: '#C2410C',
  },
  statusBadgeTextGreen: {
    color: '#15803D',
  },
  statusBadgeTextBlue: {
    color: '#0369A1',
  },
  cardMain: {
    marginBottom: 10,
  },
  patientName: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0F172A',
  },
  patientAge: {
    fontSize: 13,
    fontWeight: '500',
    color: '#64748B',
  },
  patientDiag: {
    fontSize: 12,
    color: '#475569',
    marginTop: 2,
    fontWeight: '500',
  },
  reasonText: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 4,
    lineHeight: 16,
  },
  metricsPillRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  metricPill: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  metricPillText: {
    fontSize: 11,
    color: '#334155',
  },
  metricPillDelta: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    gap: 4,
  },
  metricPillDeltaText: {
    fontSize: 11,
    color: '#15803D',
    fontWeight: '600',
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
    paddingTop: 8,
  },
  parentText: {
    fontSize: 11,
    color: '#64748B',
  },
  btnActionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  btnActionText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#0D9488',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalCard: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 20,
    maxHeight: '85%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#0F172A',
  },
  modalSub: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  modalClose: {
    fontSize: 14,
    color: '#64748B',
    fontWeight: '600',
  },
  modalStatsGrid: {
    flexDirection: 'row',
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
  },
  modalStatCol: {
    flex: 1,
    alignItems: 'center',
  },
  modalStatLabel: {
    fontSize: 10,
    color: '#64748B',
    marginBottom: 2,
  },
  modalStatValue: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0F172A',
  },
  inputTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#334155',
    marginBottom: 6,
  },
  textArea: {
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 10,
    padding: 12,
    fontSize: 13,
    color: '#0F172A',
    lineHeight: 18,
  },
  btnSaveConsultation: {
    backgroundColor: '#0D9488',
    borderRadius: 12,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 18,
    marginBottom: 10,
  },
  btnSaveConsultationText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
});
