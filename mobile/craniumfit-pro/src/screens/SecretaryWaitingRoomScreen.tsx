import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Modal,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useProAuth } from '../context/AuthContext';
import {
  UserCheck,
  Clock,
  Search,
  CheckCircle2,
  Phone,
  QrCode,
  CalendarPlus,
  ChevronRight,
  LogOut,
  Building2,
} from 'lucide-react-native';

export default function SecretaryWaitingRoomScreen() {
  const { user, activeBranch, logout } = useProAuth();

  const [searchDni, setSearchDni] = useState('');
  const [waitingList, setWaitingList] = useState([
    {
      id: 'wait-01',
      patientName: 'Lucas Torres',
      age: '5 meses',
      parentName: 'María Fernanda López',
      parentPhone: '+593 99 887 7665',
      doctor: 'Dr. Carlos Morales',
      room: 'Sala Biométrica 2',
      checkInTime: '09:48 AM',
      status: 'waiting',
      reason: 'Control mensual y escaneo 3D',
    },
    {
      id: 'wait-02',
      patientName: 'Mateo Benítez',
      age: '4 meses',
      parentName: 'David Benítez',
      parentPhone: '+593 98 443 2211',
      doctor: 'Dr. Carlos Morales',
      room: 'Sala Biométrica 2',
      checkInTime: '10:15 AM',
      status: 'waiting',
      reason: 'Primera consulta / Diagnóstico antropométrico',
    },
  ]);

  const [upcomingList, setUpcomingList] = useState([
    {
      id: 'up-01',
      time: '11:30 AM',
      patientName: 'Sofía Cárdenas (6m)',
      doctor: 'Dr. Carlos Morales',
      parentName: 'Valeria Gómez',
      phone: '+593 99 555 1234',
    },
    {
      id: 'up-02',
      time: '12:15 PM',
      patientName: 'Joaquín Mora (7m)',
      doctor: 'Dr. Carlos Morales',
      parentName: 'Carolina Mora',
      phone: '+593 99 222 9988',
    },
  ]);

  const handleCallPatient = (item: any) => {
    Alert.alert(
      'Paciente Notificado',
      `Se ha enviado una notificación sonora y a la pantalla de la sala de espera para ${item.patientName} -> Pasar a ${item.room}.`,
      [{ text: 'Entendido' }]
    );
  };

  const handleCheckInManual = () => {
    if (!searchDni.trim()) {
      Alert.alert('Atención', 'Ingresa la cédula del paciente para realizar el check-in.');
      return;
    }
    const newEntry = {
      id: `wait-${Date.now()}`,
      patientName: `Paciente DNI ${searchDni}`,
      age: '6 meses',
      parentName: 'Representante Registrado',
      parentPhone: '+593 99 000 0000',
      doctor: 'Dr. Carlos Morales',
      room: 'Consultorio 1',
      checkInTime: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      status: 'waiting',
      reason: 'Control rutinario',
    };
    setWaitingList([newEntry, ...waitingList]);
    setSearchDni('');
    Alert.alert('Check-in Exitoso', 'El paciente ha sido ingresado a la sala de espera.');
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
            <Text style={styles.userName}>{user?.full_name}</Text>
            <Text style={styles.userRole}>
              Admisión & Sala de Espera · Sede {activeBranch.toUpperCase()}
            </Text>
          </View>
          <TouchableOpacity style={styles.logoutBtn} onPress={logout}>
            <LogOut size={18} color="#64748B" />
          </TouchableOpacity>
        </View>

        {/* Check-in Bar */}
        <View style={styles.checkInCard}>
          <Text style={styles.checkInTitle}>Check-in Rápido de Pacientes</Text>
          <View style={styles.searchRow}>
            <TextInput
              style={styles.searchInput}
              placeholder="Ingresa Cédula del bebé o padre..."
              placeholderTextColor="#94A3B8"
              value={searchDni}
              onChangeText={setSearchDni}
              keyboardType="numeric"
            />
            <TouchableOpacity style={styles.btnSearch} onPress={handleCheckInManual}>
              <UserCheck size={18} color="#FFFFFF" />
              <Text style={styles.btnSearchText}>Registrar Llegada</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Waiting Room Live List */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>
            En Sala de Espera ({waitingList.length} presentes)
          </Text>
          <View style={styles.livePulse}>
            <View style={styles.pulseDot} />
            <Text style={styles.liveText}>En Vivo</Text>
          </View>
        </View>

        {waitingList.map((item) => (
          <View key={item.id} style={styles.waitingCard}>
            <View style={styles.cardHeader}>
              <View style={styles.checkInTimeBox}>
                <Clock size={12} color="#0D9488" />
                <Text style={styles.checkInTimeText}>Llegó: {item.checkInTime}</Text>
              </View>
              <View style={styles.waitingBadge}>
                <Text style={styles.waitingBadgeText}>En Espera</Text>
              </View>
            </View>

            <Text style={styles.patientTitle}>
              {item.patientName} <Text style={styles.patientSub}>({item.age})</Text>
            </Text>
            <Text style={styles.reasonText}>{item.reason}</Text>
            <Text style={styles.doctorText}>
              Asignado a: <Text style={{ fontWeight: '700' }}>{item.doctor}</Text> ({item.room})
            </Text>
            <Text style={styles.contactText}>
              Acompaña: {item.parentName} · {item.parentPhone}
            </Text>

            <View style={styles.cardActions}>
              <TouchableOpacity
                style={styles.btnCall}
                onPress={() => handleCallPatient(item)}
              >
                <UserCheck size={16} color="#FFFFFF" />
                <Text style={styles.btnCallText}>Llamar a Consultorio</Text>
              </TouchableOpacity>
            </View>
          </View>
        ))}

        {/* Upcoming appointments for today */}
        <Text style={[styles.sectionTitle, { marginTop: 16 }]}>
          Próximas Citas por Llegar Hoy
        </Text>

        {upcomingList.map((up) => (
          <View key={up.id} style={styles.upcomingCard}>
            <View style={styles.timeBox}>
              <Text style={styles.timeBoxText}>{up.time}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.upcomingName}>{up.patientName}</Text>
              <Text style={styles.upcomingDoc}>Atiende: {up.doctor}</Text>
              <Text style={styles.upcomingParent}>{up.parentName} · {up.phone}</Text>
            </View>
            <TouchableOpacity
              style={styles.btnConfirmArrival}
              onPress={() => {
                setWaitingList([
                  ...waitingList,
                  {
                    id: `wait-${Date.now()}`,
                    patientName: up.patientName,
                    age: 'Edad',
                    parentName: up.parentName,
                    parentPhone: up.phone,
                    doctor: up.doctor,
                    room: 'Sala Biométrica 2',
                    checkInTime: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    status: 'waiting',
                    reason: 'Cita programada',
                  },
                ]);
                setUpcomingList(upcomingList.filter((x) => x.id !== up.id));
              }}
            >
              <Text style={styles.btnConfirmArrivalText}>Llegó</Text>
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
    marginBottom: 14,
  },
  userName: {
    fontSize: 20,
    fontWeight: '800',
    color: '#0F172A',
  },
  userRole: {
    fontSize: 11,
    color: '#0D9488',
    fontWeight: '600',
  },
  logoutBtn: {
    padding: 8,
    backgroundColor: '#F1F5F9',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  checkInCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 16,
  },
  checkInTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 8,
  },
  searchRow: {
    flexDirection: 'row',
    gap: 8,
  },
  searchInput: {
    flex: 1,
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 13,
    color: '#0F172A',
  },
  btnSearch: {
    backgroundColor: '#0D9488',
    borderRadius: 10,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  btnSearchText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  livePulse: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
    gap: 6,
  },
  pulseDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#16A34A',
  },
  liveText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#15803D',
  },
  waitingCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1.5,
    borderColor: '#BAE6FD',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  checkInTimeBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  checkInTimeText: {
    fontSize: 11,
    color: '#0D9488',
    fontWeight: '600',
  },
  waitingBadge: {
    backgroundColor: '#FFF7ED',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  waitingBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#EA580C',
  },
  patientTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0F172A',
  },
  patientSub: {
    fontSize: 13,
    fontWeight: '500',
    color: '#64748B',
  },
  reasonText: {
    fontSize: 12,
    color: '#475569',
    marginTop: 2,
  },
  doctorText: {
    fontSize: 11,
    color: '#0F766E',
    marginTop: 4,
  },
  contactText: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 2,
  },
  cardActions: {
    marginTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
    paddingTop: 10,
  },
  btnCall: {
    backgroundColor: '#0284C7',
    borderRadius: 10,
    paddingVertical: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  btnCallText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  upcomingCard: {
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
  timeBox: {
    backgroundColor: '#F1F5F9',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 6,
    alignItems: 'center',
    justifyContent: 'center',
  },
  timeBoxText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#334155',
  },
  upcomingName: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F172A',
  },
  upcomingDoc: {
    fontSize: 11,
    color: '#64748B',
  },
  upcomingParent: {
    fontSize: 10,
    color: '#94A3B8',
  },
  btnConfirmArrival: {
    backgroundColor: '#F0FDFA',
    borderWidth: 1,
    borderColor: '#99F6E4',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  btnConfirmArrivalText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#0D9488',
  },
});
