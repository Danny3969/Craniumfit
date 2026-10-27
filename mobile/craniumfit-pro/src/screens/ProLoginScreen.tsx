import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useProAuth } from '../context/AuthContext';
import {
  Stethoscope,
  ShieldCheck,
  UserCheck,
  Building2,
  Lock,
  CalendarCheck,
  Activity,
} from 'lucide-react-native';

export default function ProLoginScreen() {
  const { login, loginRole, isLoading } = useProAuth();
  const [loginId, setLoginId] = useState('1710000002');
  const [password, setPassword] = useState('doc123');
  const [errorMsg, setErrorMsg] = useState('');

  const handleLogin = async () => {
    if (!loginId.trim() || !password.trim()) {
      setErrorMsg('Ingresa tu cédula/usuario y contraseña asignada por consola');
      return;
    }
    setErrorMsg('');
    try {
      await login(loginId, password);
    } catch (err: any) {
      setErrorMsg(err.message || 'Credenciales no válidas. Consulta con el Administrador.');
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.keyboardContainer}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.logoBadge}>
              <Stethoscope size={32} color="#0D9488" />
            </View>
            <View style={styles.proTag}>
              <Text style={styles.proTagText}>PORTAL CLÍNICO PRO</Text>
            </View>
            <Text style={styles.title}>CraniumFit Pro</Text>
            <Text style={styles.subtitle}>
              Gestión Médica, Admisión & Control de Ortesis Craneales
            </Text>

            <View style={styles.trustBadge}>
              <Lock size={12} color="#0D9488" />
              <Text style={styles.trustText}>
                Acceso con credenciales de consola (Sin OTP requerido)
              </Text>
            </View>
          </View>

          {/* Error Alert */}
          {errorMsg ? (
            <View style={styles.alertError}>
              <Text style={styles.alertErrorText}>{errorMsg}</Text>
            </View>
          ) : null}

          {/* Login Card */}
          <View style={styles.card}>
            <Text style={styles.formTitle}>Identificación del Personal</Text>
            <Text style={styles.formDesc}>
              Ingresa con tu usuario asignado para acceder a tus herramientas clínicas según tu rol.
            </Text>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Cédula / Usuario de Consola</Text>
              <TextInput
                style={styles.input}
                placeholder="Ej. 1710000002"
                placeholderTextColor="#94A3B8"
                value={loginId}
                onChangeText={setLoginId}
                autoCapitalize="none"
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Contraseña</Text>
              <TextInput
                style={styles.input}
                placeholder="••••••••"
                placeholderTextColor="#94A3B8"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
              />
            </View>

            <TouchableOpacity
              style={styles.btnPrimary}
              onPress={handleLogin}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.btnPrimaryText}>Ingresar al Sistema</Text>
              )}
            </TouchableOpacity>

            {/* Quick-Role Selectors for Instant Evaluation */}
            <View style={styles.demoDivider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>o selecciona un rol de prueba</Text>
              <View style={styles.dividerLine} />
            </View>

            <TouchableOpacity
              style={[styles.btnRole, styles.btnRoleDoc]}
              onPress={() => loginRole('doctor')}
            >
              <Stethoscope size={18} color="#0D9488" />
              <View style={{ flex: 1 }}>
                <Text style={styles.btnRoleTitle}>Dr. Carlos Morales · Médico Especialista</Text>
                <Text style={styles.btnRoleSub}>Agenda, Pacientes, Calculadora CVAI, Recetas .p12</Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.btnRole, styles.btnRoleSec]}
              onPress={() => loginRole('secretary')}
            >
              <CalendarCheck size={18} color="#0284C7" />
              <View style={{ flex: 1 }}>
                <Text style={styles.btnRoleTitle}>Ana Belén Pérez · Secretaría / Admisión</Text>
                <Text style={styles.btnRoleSub}>Sala de Espera, Check-in, Agendamiento</Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.btnRole, styles.btnRoleAdm]}
              onPress={() => loginRole('admin')}
            >
              <Activity size={18} color="#7C3AED" />
              <View style={{ flex: 1 }}>
                <Text style={styles.btnRoleTitle}>Dr. Roberto Salazar · SuperAdmin / Director</Text>
                <Text style={styles.btnRoleSub}>KPIs multi-sede (Quito / Lima), Auditoría</Text>
              </View>
            </TouchableOpacity>
          </View>

          <View style={styles.footer}>
            <Text style={styles.footerText}>CraniumFit Medical Technologies © 2026</Text>
            <Text style={styles.footerSub}>Sedes Quito Norte · Cumbayá · Lima Miraflores</Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  keyboardContainer: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 40,
    maxWidth: 520,
    width: '100%',
    alignSelf: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 20,
  },
  logoBadge: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#CCFBF1',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
    borderWidth: 2,
    borderColor: '#99F6E4',
  },
  proTag: {
    backgroundColor: '#0F172A',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
    marginBottom: 6,
  },
  proTagText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#38BDF8',
    letterSpacing: 1,
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    color: '#0F172A',
  },
  subtitle: {
    fontSize: 13,
    color: '#64748B',
    textAlign: 'center',
    marginTop: 2,
  },
  trustBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FDFA',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#CCFBF1',
    marginTop: 10,
    gap: 6,
  },
  trustText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#0F766E',
  },
  alertError: {
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
  },
  alertErrorText: {
    color: '#DC2626',
    fontSize: 13,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 20,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 3,
  },
  formTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 4,
  },
  formDesc: {
    fontSize: 12,
    color: '#64748B',
    lineHeight: 17,
    marginBottom: 16,
  },
  inputGroup: {
    marginBottom: 14,
  },
  label: {
    fontSize: 12,
    fontWeight: '600',
    color: '#334155',
    marginBottom: 4,
  },
  input: {
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: '#0F172A',
  },
  btnPrimary: {
    backgroundColor: '#0D9488',
    borderRadius: 10,
    paddingVertical: 13,
    alignItems: 'center',
    marginTop: 6,
  },
  btnPrimaryText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  demoDivider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 18,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#E2E8F0',
  },
  dividerText: {
    paddingHorizontal: 10,
    fontSize: 11,
    color: '#94A3B8',
  },
  btnRole: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    gap: 12,
    marginBottom: 10,
  },
  btnRoleDoc: {
    backgroundColor: '#F0FDFA',
    borderColor: '#99F6E4',
  },
  btnRoleSec: {
    backgroundColor: '#F0F9FF',
    borderColor: '#BAE6FD',
  },
  btnRoleAdm: {
    backgroundColor: '#FAF5FF',
    borderColor: '#E9D5FF',
  },
  btnRoleTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F172A',
  },
  btnRoleSub: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 2,
  },
  footer: {
    marginTop: 24,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '600',
  },
  footerSub: {
    fontSize: 10,
    color: '#94A3B8',
    marginTop: 2,
  },
});
