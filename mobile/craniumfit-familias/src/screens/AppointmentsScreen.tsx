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
import { useAuth } from '../context/AuthContext';
import {
  Calendar,
  Clock,
  MapPin,
  Stethoscope,
  Plus,
  CheckCircle2,
  CalendarCheck,
  ChevronRight,
  Building2,
} from 'lucide-react-native';

export default function AppointmentsScreen() {
  const { dashboard } = useAuth();
  const nextApt = dashboard?.next_appointment;

  const [modalVisible, setModalVisible] = useState(false);
  const [selectedReason, setSelectedReason] = useState('Control y Escaneo 3D');
  const [selectedBranch, setSelectedBranch] = useState('Sede Quito Norte');
  const [prefDate, setPrefDate] = useState('2024-11-22');
  const [prefTime, setPrefTime] = useState('11:00 AM');
  const [confirmed, setConfirmed] = useState(false);

  const pastAppointments = [
    {
      id: 'apt-003',
      date: '2024-10-24',
      time: '10:00 AM',
      doctor: 'Dr. Carlos Morales',
      reason: 'Control mensual y escaneo 3D (CVAI 4.8%)',
      branch: 'Sede Quito Norte',
      status: 'Completada',
    },
    {
      id: 'apt-002',
      date: '2024-09-26',
      time: '11:30 AM',
      doctor: 'Dr. Carlos Morales',
      reason: 'Ajuste de zonas de crecimiento en casco',
      branch: 'Sede Quito Norte',
      status: 'Completada',
    },
    {
      id: 'apt-001',
      date: '2024-08-01',
      time: '09:00 AM',
      doctor: 'Dr. Carlos Morales',
      reason: 'Entrega inicial de ortesis y protocolo de 5 días',
      branch: 'Sede Quito Norte',
      status: 'Completada',
    },
  ];

  const handleBook = () => {
    Alert.alert(
      'Solicitud Enviada',
      `Hemos registrado tu solicitud para el ${prefDate} a las ${prefTime} en ${selectedBranch}. La secretaría se comunicará por WhatsApp para confirmar.`,
      [{ text: 'Entendido', onPress: () => setModalVisible(false) }]
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Citas Médicas & Controles</Text>
          <Text style={styles.subtitle}>
            Agenda y gestiona los controles quincenales y mensuales de tu bebé
          </Text>
        </View>

        {/* Action Button: Book Appointment */}
        <TouchableOpacity
          style={styles.btnNewApt}
          onPress={() => setModalVisible(true)}
        >
          <Plus size={18} color="#FFFFFF" />
          <Text style={styles.btnNewAptText}>Agendar Nueva Cita o Ajuste de Casco</Text>
        </TouchableOpacity>

        {/* Next Appointment Card */}
        {nextApt && (
          <View style={styles.nextCard}>
            <View style={styles.nextCardHeader}>
              <View style={styles.calendarIconBox}>
                <Calendar size={22} color="#0D9488" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.nextCardTag}>PRÓXIMA CITA PROGRAMADA</Text>
                <Text style={styles.nextCardDate}>
                  {nextApt.appointment_date} · {nextApt.start_time}
                </Text>
              </View>
              <View style={styles.confirmedPill}>
                <CheckCircle2 size={12} color="#059669" />
                <Text style={styles.confirmedPillText}>Confirmada</Text>
              </View>
            </View>

            <View style={styles.nextCardDetails}>
              <View style={styles.detailRow}>
                <Stethoscope size={15} color="#0F766E" />
                <Text style={styles.detailDoctor}>{nextApt.doctor_name}</Text>
              </View>
              <View style={styles.detailRow}>
                <MapPin size={15} color="#64748B" />
                <Text style={styles.detailText}>{nextApt.room}</Text>
              </View>
              <View style={styles.detailRow}>
                <Clock size={15} color="#64748B" />
                <Text style={styles.detailText}>{nextApt.reason}</Text>
              </View>
            </View>

            <TouchableOpacity
              style={[styles.btnConfirm, confirmed && styles.btnConfirmed]}
              onPress={() => setConfirmed(true)}
              disabled={confirmed}
            >
              <CheckCircle2 size={16} color={confirmed ? '#166534' : '#0F766E'} />
              <Text
                style={[
                  styles.btnConfirmText,
                  confirmed && { color: '#166534' },
                ]}
              >
                {confirmed ? '¡Asistencia Reconfirmada!' : 'Reconfirmar Asistencia'}
              </Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Past Appointments List */}
        <Text style={styles.sectionHeader}>Historial de Citas Anteriores</Text>
        {pastAppointments.map((apt) => (
          <View key={apt.id} style={styles.pastCard}>
            <View style={styles.pastDateBox}>
              <Text style={styles.pastDateDay}>{apt.date.split('-')[2]}</Text>
              <Text style={styles.pastDateMonth}>
                {apt.date.split('-')[1] === '10'
                  ? 'OCT'
                  : apt.date.split('-')[1] === '09'
                  ? 'SEP'
                  : 'AGO'}
              </Text>
            </View>
            <View style={{ flex: 1 }}>
              <View style={styles.pastTopRow}>
                <Text style={styles.pastReason}>{apt.reason}</Text>
                <View style={styles.completedBadge}>
                  <Text style={styles.completedBadgeText}>{apt.status}</Text>
                </View>
              </View>
              <Text style={styles.pastDoctor}>{apt.doctor} · {apt.branch}</Text>
              <Text style={styles.pastTime}>{apt.time}</Text>
            </View>
          </View>
        ))}
      </ScrollView>

      {/* Book Appointment Modal */}
      <Modal
        visible={modalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Agendar Cita Pediátrica</Text>
              <TouchableOpacity onPress={() => setModalVisible(false)}>
                <Text style={styles.modalCloseText}>Cerrar</Text>
              </TouchableOpacity>
            </View>

            <ScrollView showsVerticalScrollIndicator={false}>
              <Text style={styles.inputGroupTitle}>Motivo de la Cita:</Text>
              {[
                'Control y Escaneo 3D (Mensual)',
                'Ajuste o Calibración de Casco',
                'Revisión de Piel / Irritación',
                'Consulta con Pediatra Especialista',
              ].map((reason) => (
                <TouchableOpacity
                  key={reason}
                  style={[
                    styles.radioOption,
                    selectedReason === reason && styles.radioOptionActive,
                  ]}
                  onPress={() => setSelectedReason(reason)}
                >
                  <View
                    style={[
                      styles.radioCircle,
                      selectedReason === reason && styles.radioCircleActive,
                    ]}
                  />
                  <Text
                    style={[
                      styles.radioText,
                      selectedReason === reason && styles.radioTextActive,
                    ]}
                  >
                    {reason}
                  </Text>
                </TouchableOpacity>
              ))}

              <Text style={[styles.inputGroupTitle, { marginTop: 14 }]}>
                Selecciona la Sede:
              </Text>
              {['Sede Quito Norte', 'Sede Quito Cumbayá', 'Sede Lima Miraflores'].map(
                (branch) => (
                  <TouchableOpacity
                    key={branch}
                    style={[
                      styles.radioOption,
                      selectedBranch === branch && styles.radioOptionActive,
                    ]}
                    onPress={() => setSelectedBranch(branch)}
                  >
                    <Building2 size={16} color={selectedBranch === branch ? '#0D9488' : '#64748B'} />
                    <Text
                      style={[
                        styles.radioText,
                        selectedBranch === branch && styles.radioTextActive,
                      ]}
                    >
                      {branch}
                    </Text>
                  </TouchableOpacity>
                )
              )}

              <View style={{ flexDirection: 'row', gap: 10, marginTop: 14 }}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.inputLabel}>Fecha Preferida</Text>
                  <TextInput
                    style={styles.modalInput}
                    value={prefDate}
                    onChangeText={setPrefDate}
                    placeholder="YYYY-MM-DD"
                  />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.inputLabel}>Hora Preferida</Text>
                  <TextInput
                    style={styles.modalInput}
                    value={prefTime}
                    onChangeText={setPrefTime}
                    placeholder="10:00 AM"
                  />
                </View>
              </View>

              <TouchableOpacity style={styles.btnSubmitApt} onPress={handleBook}>
                <Text style={styles.btnSubmitAptText}>Enviar Solicitud de Cita</Text>
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
  header: {
    marginBottom: 16,
  },
  title: {
    fontSize: 22,
    fontWeight: '800',
    color: '#0F172A',
  },
  subtitle: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  btnNewApt: {
    backgroundColor: '#0D9488',
    borderRadius: 14,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 16,
  },
  btnNewAptText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  nextCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    borderWidth: 1.5,
    borderColor: '#99F6E4',
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 3,
  },
  nextCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  calendarIconBox: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#CCFBF1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  nextCardTag: {
    fontSize: 10,
    fontWeight: '800',
    color: '#0D9488',
    letterSpacing: 0.5,
  },
  nextCardDate: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0F172A',
  },
  confirmedPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
    gap: 4,
  },
  confirmedPillText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#15803D',
  },
  nextCardDetails: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 12,
    gap: 6,
    marginBottom: 12,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  detailDoctor: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F766E',
  },
  detailText: {
    fontSize: 12,
    color: '#475569',
  },
  btnConfirm: {
    backgroundColor: '#F0FDFA',
    borderWidth: 1,
    borderColor: '#99F6E4',
    borderRadius: 10,
    paddingVertical: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  btnConfirmed: {
    backgroundColor: '#DCFCE7',
    borderColor: '#86EFAC',
  },
  btnConfirmText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F766E',
  },
  sectionHeader: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 10,
  },
  pastCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 12,
  },
  pastDateBox: {
    width: 44,
    height: 44,
    borderRadius: 10,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  pastDateDay: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0F172A',
  },
  pastDateMonth: {
    fontSize: 9,
    fontWeight: '700',
    color: '#64748B',
  },
  pastTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  pastReason: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F172A',
    flex: 1,
  },
  completedBadge: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  completedBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#64748B',
  },
  pastDoctor: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 2,
  },
  pastTime: {
    fontSize: 10,
    color: '#94A3B8',
    marginTop: 1,
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
    padding: 22,
    maxHeight: '85%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#0F172A',
  },
  modalCloseText: {
    fontSize: 14,
    color: '#64748B',
    fontWeight: '600',
  },
  inputGroupTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#334155',
    marginBottom: 8,
  },
  radioOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 10,
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 6,
    gap: 10,
  },
  radioOptionActive: {
    borderColor: '#0D9488',
    backgroundColor: '#F0FDFA',
  },
  radioCircle: {
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: '#CBD5E1',
  },
  radioCircleActive: {
    borderColor: '#0D9488',
    backgroundColor: '#0D9488',
  },
  radioText: {
    fontSize: 13,
    color: '#334155',
  },
  radioTextActive: {
    fontWeight: '700',
    color: '#0F766E',
  },
  inputLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#475569',
    marginBottom: 4,
  },
  modalInput: {
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 13,
    color: '#0F172A',
  },
  btnSubmitApt: {
    backgroundColor: '#0D9488',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 10,
  },
  btnSubmitAptText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
});
