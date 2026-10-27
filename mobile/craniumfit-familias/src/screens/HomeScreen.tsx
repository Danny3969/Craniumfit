import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Modal,
  TextInput,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../context/AuthContext';
import {
  Baby,
  Clock,
  Flame,
  Calendar,
  CheckCircle2,
  AlertCircle,
  Plus,
  Stethoscope,
  ChevronRight,
  ShieldCheck,
  Sparkles,
  Info,
  LogOut,
} from 'lucide-react-native';

export default function HomeScreen() {
  const { user, activeBaby, dashboard, logWearHours, logout } = useAuth();

  // Log Wear Modal State
  const [modalVisible, setModalVisible] = useState(false);
  const [hoursInput, setHoursInput] = useState('22.5');
  const [pausesInput, setPausesInput] = useState('2');
  const [notesInput, setNotesInput] = useState('');
  const [saving, setSaving] = useState(false);

  const todayWear = dashboard?.today_wear || {
    hours_worn: 19.5,
    target_hours: 23.0,
    completion_pct: 84.8,
    status: 'excellent',
    streak_days: 16,
  };

  const baby = activeBaby || dashboard?.baby;
  const nextApt = dashboard?.next_appointment;

  const handleSaveWear = async () => {
    const hours = parseFloat(hoursInput);
    if (isNaN(hours) || hours < 0 || hours > 24) {
      Alert.alert('Error', 'Por favor ingresa un número de horas válido entre 0 y 24.');
      return;
    }
    setSaving(true);
    await logWearHours(hours, parseInt(pausesInput) || 0, notesInput);
    setSaving(false);
    setModalVisible(false);
  };

  // Preset hours helper
  const setPresetHours = (h: number) => {
    setHoursInput(h.toString());
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Top Bar with Parent Name & Logout */}
        <View style={styles.topBar}>
          <View>
            <Text style={styles.greetingText}>Hola, {user?.full_name?.split(' ')[0] || 'Familia'}</Text>
            <Text style={styles.subtitleText}>Seguimiento Pediátrico en Tiempo Real</Text>
          </View>
          <TouchableOpacity style={styles.logoutBtn} onPress={logout}>
            <LogOut size={18} color="#64748B" />
          </TouchableOpacity>
        </View>

        {/* Baby Profile Card */}
        <View style={styles.babyCard}>
          <View style={styles.babyAvatar}>
            <Baby size={28} color="#0D9488" />
          </View>
          <View style={styles.babyInfo}>
            <View style={styles.babyNameRow}>
              <Text style={styles.babyName}>
                {baby?.first_name} {baby?.last_name}
              </Text>
              <View style={styles.ageBadge}>
                <Text style={styles.ageBadgeText}>5 meses</Text>
              </View>
            </View>
            <Text style={styles.diagnosisText}>
              {baby?.diagnosis || 'Plagiocefalia Posicional Derecha (CVAI: 11.2% inicial)'}
            </Text>
            <View style={styles.doctorRow}>
              <Stethoscope size={13} color="#0F766E" />
              <Text style={styles.doctorName}>
                Especialista: {baby?.doctor_name || 'Dr. Carlos Morales'}
              </Text>
            </View>
          </View>
        </View>

        {/* 23h Wear Compliance Hero Gauge */}
        <View style={styles.gaugeCard}>
          <View style={styles.gaugeHeader}>
            <View style={styles.gaugeTitleRow}>
              <Clock size={20} color="#0D9488" />
              <Text style={styles.gaugeTitle}>Protocolo 23 Horas / Día</Text>
            </View>
            <View style={styles.streakBadge}>
              <Flame size={14} color="#EA580C" />
              <Text style={styles.streakText}>{todayWear.streak_days} días en racha</Text>
            </View>
          </View>

          {/* Large Progress Display */}
          <View style={styles.progressContainer}>
            <View style={styles.circleOuter}>
              <View style={styles.circleInner}>
                <Text style={styles.hoursNumber}>{todayWear.hours_worn}h</Text>
                <Text style={styles.hoursTarget}>de {todayWear.target_hours}h diarias</Text>
                <View style={styles.pctBadge}>
                  <Text style={styles.pctText}>{todayWear.completion_pct}% hoy</Text>
                </View>
              </View>
            </View>
          </View>

          {/* Status Message */}
          <View style={styles.statusBox}>
            <CheckCircle2 size={16} color="#15803D" />
            <Text style={styles.statusBoxText}>
              ¡Excelente adherencia! Lucas mantiene el ritmo óptimo de remodelación craneal.
            </Text>
          </View>

          {/* 3 Metrics Cards */}
          <View style={styles.metricsRow}>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Horas Hoy</Text>
              <Text style={styles.metricValue}>{todayWear.hours_worn}h</Text>
            </View>
            <View style={styles.metricDivider} />
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Pausas</Text>
              <Text style={styles.metricValue}>3 pausas</Text>
            </View>
            <View style={styles.metricDivider} />
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Cumplimiento</Text>
              <Text style={[styles.metricValue, { color: '#0D9488' }]}>94.8%</Text>
            </View>
          </View>

          {/* Log Wear Button */}
          <TouchableOpacity
            style={styles.btnLogWear}
            onPress={() => setModalVisible(true)}
          >
            <Plus size={18} color="#FFFFFF" />
            <Text style={styles.btnLogWearText}>Registrar Horas de Uso de Hoy</Text>
          </TouchableOpacity>
        </View>

        {/* Next Appointment Card */}
        {nextApt && (
          <View style={styles.aptCard}>
            <View style={styles.aptHeader}>
              <View style={styles.aptIconContainer}>
                <Calendar size={20} color="#0284C7" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.aptTag}>PRÓXIMO CONTROL CLÍNICO</Text>
                <Text style={styles.aptDate}>
                  {nextApt.appointment_date} · {nextApt.start_time}
                </Text>
              </View>
              <View style={styles.confirmedBadge}>
                <CheckCircle2 size={12} color="#059669" />
                <Text style={styles.confirmedText}>Confirmada</Text>
              </View>
            </View>

            <View style={styles.aptBody}>
              <Text style={styles.aptReason}>{nextApt.reason}</Text>
              <Text style={styles.aptLocation}>{nextApt.room}</Text>
              <Text style={styles.aptDoctor}>Atiende: {nextApt.doctor_name}</Text>
            </View>
          </View>
        )}

        {/* Clinical Skin Check Reminder Alert */}
        <View style={styles.tipCard}>
          <View style={styles.tipIcon}>
            <Info size={18} color="#0284C7" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.tipTitle}>Control de Piel Diario</Text>
            <Text style={styles.tipText}>
              Al retirar el casco para el baño (1 hora de pausa), inspecciona la piel. Si notas rojeces que duren más de 30 minutos, infórmalo a tu especialista.
            </Text>
          </View>
        </View>

        {/* Recent logs list */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Registro de los Últimos Días</Text>
        </View>

        {dashboard?.recent_wear_logs?.map((log, index) => (
          <View key={index} style={styles.logRow}>
            <View style={styles.logDateBox}>
              <Text style={styles.logDateDay}>{log.log_date.split('-')[2]}</Text>
              <Text style={styles.logDateMonth}>OCT</Text>
            </View>
            <View style={{ flex: 1 }}>
              <View style={styles.logStatsRow}>
                <Text style={styles.logHours}>{log.hours_worn} horas de uso</Text>
                <View
                  style={[
                    styles.logBadge,
                    log.hours_worn >= 22 ? styles.logBadgeGreen : styles.logBadgeAmber,
                  ]}
                >
                  <Text
                    style={[
                      styles.logBadgeText,
                      log.hours_worn >= 22 ? styles.logBadgeTextGreen : styles.logBadgeTextAmber,
                    ]}
                  >
                    {log.hours_worn >= 22 ? 'Meta Cumplida' : 'Aceptable'}
                  </Text>
                </View>
              </View>
              <Text style={styles.logNotes}>
                {log.notes || `${log.pauses_count} pausas registradas`}
              </Text>
            </View>
          </View>
        ))}
      </ScrollView>

      {/* Log Wear Modal */}
      <Modal
        visible={modalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Registrar Horas de Uso</Text>
              <TouchableOpacity onPress={() => setModalVisible(false)}>
                <Text style={styles.modalCloseText}>Cerrar</Text>
              </TouchableOpacity>
            </View>
            <Text style={styles.modalDescription}>
              La meta recomendada por neurocirugía pediátrica es de 23 horas diarias para una óptima remodelación.
            </Text>

            {/* Presets */}
            <Text style={styles.presetLabel}>Accesos Rápidos de Horas:</Text>
            <View style={styles.presetRow}>
              {[20, 21.5, 22.5, 23].map((val) => (
                <TouchableOpacity
                  key={val}
                  style={[
                    styles.presetBtn,
                    hoursInput === val.toString() && styles.presetBtnActive,
                  ]}
                  onPress={() => setPresetHours(val)}
                >
                  <Text
                    style={[
                      styles.presetBtnText,
                      hoursInput === val.toString() && styles.presetBtnTextActive,
                    ]}
                  >
                    {val}h
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Manual inputs */}
            <View style={styles.inputRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.inputLabel}>Horas totales usadas</Text>
                <TextInput
                  style={styles.modalInput}
                  value={hoursInput}
                  onChangeText={setHoursInput}
                  keyboardType="numeric"
                  placeholder="23.0"
                />
              </View>
              <View style={{ flex: 1, marginLeft: 12 }}>
                <Text style={styles.inputLabel}>Nº de Pausas (baño)</Text>
                <TextInput
                  style={styles.modalInput}
                  value={pausesInput}
                  onChangeText={setPausesInput}
                  keyboardType="numeric"
                  placeholder="2"
                />
              </View>
            </View>

            <View style={{ marginTop: 12 }}>
              <Text style={styles.inputLabel}>Observaciones (opcional)</Text>
              <TextInput
                style={[styles.modalInput, { height: 60, textAlignVertical: 'top' }]}
                value={notesInput}
                onChangeText={setNotesInput}
                placeholder="Ej. Buena adaptación, sin marcas ni rozaduras"
                multiline
              />
            </View>

            <TouchableOpacity
              style={styles.btnSaveWear}
              onPress={handleSaveWear}
              disabled={saving}
            >
              {saving ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.btnSaveWearText}>Guardar Registro de Hoy</Text>
              )}
            </TouchableOpacity>
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
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  greetingText: {
    fontSize: 22,
    fontWeight: '800',
    color: '#0F172A',
  },
  subtitleText: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  logoutBtn: {
    padding: 8,
    backgroundColor: '#F1F5F9',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  babyCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2,
  },
  babyAvatar: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: '#CCFBF1',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
    borderWidth: 1.5,
    borderColor: '#99F6E4',
  },
  babyInfo: {
    flex: 1,
  },
  babyNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  babyName: {
    fontSize: 17,
    fontWeight: '700',
    color: '#0F172A',
  },
  ageBadge: {
    backgroundColor: '#E0F2FE',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  ageBadgeText: {
    fontSize: 11,
    color: '#0369A1',
    fontWeight: '600',
  },
  diagnosisText: {
    fontSize: 12,
    color: '#475569',
    marginTop: 3,
  },
  doctorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 4,
  },
  doctorName: {
    fontSize: 11,
    color: '#0F766E',
    fontWeight: '600',
  },
  gaugeCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 3,
  },
  gaugeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  gaugeTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  gaugeTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0F172A',
  },
  streakBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF7ED',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#FFEDD5',
    gap: 4,
  },
  streakText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#C2410C',
  },
  progressContainer: {
    alignItems: 'center',
    marginVertical: 10,
  },
  circleOuter: {
    width: 170,
    height: 170,
    borderRadius: 85,
    borderWidth: 8,
    borderColor: '#CCFBF1',
    borderTopColor: '#0D9488',
    borderRightColor: '#0D9488',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F0FDFA',
  },
  circleInner: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  hoursNumber: {
    fontSize: 34,
    fontWeight: '900',
    color: '#0F766E',
    letterSpacing: -1,
  },
  hoursTarget: {
    fontSize: 12,
    color: '#64748B',
    marginTop: -2,
  },
  pctBadge: {
    backgroundColor: '#0D9488',
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 12,
    marginTop: 6,
  },
  pctText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '700',
  },
  statusBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FDF4',
    borderWidth: 1,
    borderColor: '#BBF7D0',
    borderRadius: 12,
    padding: 10,
    marginVertical: 14,
    gap: 8,
  },
  statusBoxText: {
    fontSize: 12,
    color: '#166534',
    flex: 1,
    fontWeight: '500',
  },
  metricsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    paddingVertical: 12,
    marginBottom: 16,
  },
  metricItem: {
    flex: 1,
    alignItems: 'center',
  },
  metricDivider: {
    width: 1,
    height: 24,
    backgroundColor: '#CBD5E1',
  },
  metricLabel: {
    fontSize: 11,
    color: '#64748B',
    marginBottom: 2,
  },
  metricValue: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  btnLogWear: {
    backgroundColor: '#0D9488',
    borderRadius: 12,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  btnLogWearText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  aptCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#BAE6FD',
    marginBottom: 16,
  },
  aptHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 10,
  },
  aptIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#E0F2FE',
    alignItems: 'center',
    justifyContent: 'center',
  },
  aptTag: {
    fontSize: 10,
    fontWeight: '800',
    color: '#0284C7',
    letterSpacing: 0.5,
  },
  aptDate: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  confirmedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ECFDF5',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
    gap: 4,
  },
  confirmedText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#059669',
  },
  aptBody: {
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    padding: 10,
  },
  aptReason: {
    fontSize: 13,
    fontWeight: '600',
    color: '#334155',
  },
  aptLocation: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  aptDoctor: {
    fontSize: 11,
    color: '#0284C7',
    marginTop: 4,
    fontWeight: '600',
  },
  tipCard: {
    backgroundColor: '#F0F9FF',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: '#BAE6FD',
    flexDirection: 'row',
    gap: 10,
    marginBottom: 16,
  },
  tipIcon: {
    paddingTop: 2,
  },
  tipTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0369A1',
    marginBottom: 2,
  },
  tipText: {
    fontSize: 12,
    color: '#0C4A6E',
    lineHeight: 17,
  },
  sectionHeader: {
    marginBottom: 10,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  logRow: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 12,
  },
  logDateBox: {
    width: 44,
    height: 44,
    borderRadius: 10,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logDateDay: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0F172A',
  },
  logDateMonth: {
    fontSize: 9,
    fontWeight: '700',
    color: '#64748B',
  },
  logStatsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  logHours: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  logBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  logBadgeGreen: {
    backgroundColor: '#DCFCE7',
  },
  logBadgeAmber: {
    backgroundColor: '#FEF3C7',
  },
  logBadgeText: {
    fontSize: 10,
    fontWeight: '700',
  },
  logBadgeTextGreen: {
    color: '#15803D',
  },
  logBadgeTextAmber: {
    color: '#B45309',
  },
  logNotes: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 2,
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
    marginBottom: 6,
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
  modalDescription: {
    fontSize: 12,
    color: '#64748B',
    marginBottom: 16,
  },
  presetLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#334155',
    marginBottom: 8,
  },
  presetRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  presetBtn: {
    flex: 1,
    paddingVertical: 10,
    backgroundColor: '#F1F5F9',
    borderRadius: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  presetBtnActive: {
    backgroundColor: '#0D9488',
    borderColor: '#0F766E',
  },
  presetBtnText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#475569',
  },
  presetBtnTextActive: {
    color: '#FFFFFF',
  },
  inputRow: {
    flexDirection: 'row',
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#334155',
    marginBottom: 6,
  },
  modalInput: {
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: '#0F172A',
  },
  btnSaveWear: {
    backgroundColor: '#0D9488',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 20,
  },
  btnSaveWearText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
});
