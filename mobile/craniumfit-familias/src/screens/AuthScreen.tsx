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
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Colors, Spacing } from '../constants/theme';
import { ShieldCheck, MessageSquare, Lock, UserCheck, Baby, HeartHandshake, CheckCircle2 } from 'lucide-react-native';

export default function AuthScreen() {
  const { login, loginDemo, isLoading } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>('login');

  // Login form state
  const [cedula, setCedula] = useState('1718899221');
  const [password, setPassword] = useState('padre123');
  const [errorMsg, setErrorMsg] = useState('');

  // Register / OTP form state
  const [regCedula, setRegCedula] = useState('');
  const [otpStep, setOtpStep] = useState<1 | 2 | 3>(1);
  const [otpCode, setOtpCode] = useState('');
  const [simulatedOtp, setSimulatedOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [otpLoading, setOtpLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const handleLogin = async () => {
    if (!cedula.trim() || !password.trim()) {
      setErrorMsg('Por favor ingresa tu número de cédula y contraseña');
      return;
    }
    setErrorMsg('');
    try {
      await login(cedula, password);
    } catch (err: any) {
      setErrorMsg(err.message || 'Credenciales no válidas. Verifica tu cédula o activa tu cuenta.');
    }
  };

  const handleRequestOtp = async () => {
    if (!regCedula.trim()) {
      setErrorMsg('Ingresa el número de cédula registrado en la clínica');
      return;
    }
    setErrorMsg('');
    setOtpLoading(true);
    try {
      const res = await api.resendOtp(regCedula);
      setOtpStep(2);
      if (res.otp_simulated) {
        setSimulatedOtp(res.otp_simulated);
      }
      setSuccessMsg(res.message || 'Código OTP enviado con éxito');
    } catch (err: any) {
      setErrorMsg(err.message || 'No se encontró un paciente registrado con esa cédula');
    } finally {
      setOtpLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (!otpCode.trim() || otpCode.trim().length < 6) {
      setErrorMsg('Ingresa el código OTP de 6 dígitos');
      return;
    }
    setErrorMsg('');
    setOtpLoading(true);
    try {
      await api.verifyOtp(regCedula, otpCode);
      setOtpStep(3);
      setSuccessMsg('Código validado correctamente. Define tu contraseña de acceso.');
    } catch (err: any) {
      setErrorMsg(err.message || 'Código OTP inválido o expirado');
    } finally {
      setOtpLoading(false);
    }
  };

  const handleSetPassword = async () => {
    if (!newPassword || newPassword.length < 6) {
      setErrorMsg('La contraseña debe tener al menos 6 caracteres');
      return;
    }
    if (newPassword !== confirmPassword) {
      setErrorMsg('Las contraseñas no coinciden');
      return;
    }
    setErrorMsg('');
    setOtpLoading(true);
    try {
      await api.setPassword(regCedula, newPassword);
      // Auto login
      await login(regCedula, newPassword);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al guardar la contraseña');
    } finally {
      setOtpLoading(false);
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
          {/* Brand Header */}
          <View style={styles.header}>
            <View style={styles.logoBadge}>
              <Baby size={34} color="#0D9488" />
            </View>
            <Text style={styles.appTitle}>CraniumFit Familias</Text>
            <Text style={styles.appSubtitle}>
              Ortesis Craneal Pediátrica & Seguimiento Biométrico
            </Text>

            <View style={styles.trustBadge}>
              <ShieldCheck size={14} color="#0D9488" />
              <Text style={styles.trustText}>Acceso Seguro Cifrado Pediátrico</Text>
            </View>
          </View>

          {/* Mode Switcher */}
          <View style={styles.modeTabs}>
            <TouchableOpacity
              style={[styles.modeTab, mode === 'login' && styles.modeTabActive]}
              onPress={() => {
                setMode('login');
                setErrorMsg('');
              }}
            >
              <Text style={[styles.modeTabText, mode === 'login' && styles.modeTabTextActive]}>
                Iniciar Sesión
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.modeTab, mode === 'register' && styles.modeTabActive]}
              onPress={() => {
                setMode('register');
                setErrorMsg('');
              }}
            >
              <Text style={[styles.modeTabText, mode === 'register' && styles.modeTabTextActive]}>
                Activar con WhatsApp OTP
              </Text>
            </TouchableOpacity>
          </View>

          {/* Error / Success message */}
          {errorMsg ? (
            <View style={styles.alertError}>
              <Text style={styles.alertErrorText}>{errorMsg}</Text>
            </View>
          ) : null}

          {successMsg ? (
            <View style={styles.alertSuccess}>
              <CheckCircle2 size={16} color="#059669" />
              <Text style={styles.alertSuccessText}>{successMsg}</Text>
            </View>
          ) : null}

          {/* Form Content */}
          {mode === 'login' ? (
            <View style={styles.card}>
              <Text style={styles.formTitle}>Bienvenido, Familia CraniumFit</Text>
              <Text style={styles.formDescription}>
                Ingresa con tu número de cédula y la contraseña que activaste.
              </Text>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Cédula del Padre / Madre</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Ej. 1718899221"
                  placeholderTextColor="#94A3B8"
                  value={cedula}
                  onChangeText={setCedula}
                  keyboardType="numeric"
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
                  <Text style={styles.btnPrimaryText}>Ingresar a la Aplicación</Text>
                )}
              </TouchableOpacity>

              {/* Demo 1-Click Access Button */}
              <View style={styles.demoDivider}>
                <View style={styles.dividerLine} />
                <Text style={styles.dividerText}>o prueba inmediata</Text>
                <View style={styles.dividerLine} />
              </View>

              <TouchableOpacity
                style={styles.btnDemo}
                onPress={loginDemo}
                disabled={isLoading}
              >
                <HeartHandshake size={18} color="#0D9488" />
                <Text style={styles.btnDemoText}>
                  👶 Acceso Rápido Demo (Lucas Torres — 5 meses)
                </Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.card}>
              <Text style={styles.formTitle}>Activa tu Cuenta de Papá / Mamá</Text>
              <Text style={styles.formDescription}>
                Validación instantánea y automática a través del WhatsApp registrado en tu primera consulta.
              </Text>

              {/* Step indicator */}
              <View style={styles.stepIndicator}>
                <View style={[styles.stepDot, otpStep >= 1 && styles.stepDotActive]}>
                  <Text style={[styles.stepDotText, otpStep >= 1 && styles.stepDotTextActive]}>1</Text>
                </View>
                <View style={[styles.stepLine, otpStep >= 2 && styles.stepLineActive]} />
                <View style={[styles.stepDot, otpStep >= 2 && styles.stepDotActive]}>
                  <Text style={[styles.stepDotText, otpStep >= 2 && styles.stepDotTextActive]}>2</Text>
                </View>
                <View style={[styles.stepLine, otpStep >= 3 && styles.stepLineActive]} />
                <View style={[styles.stepDot, otpStep >= 3 && styles.stepDotActive]}>
                  <Text style={[styles.stepDotText, otpStep >= 3 && styles.stepDotTextActive]}>3</Text>
                </View>
              </View>

              {/* Step 1: Request OTP */}
              {otpStep === 1 && (
                <View>
                  <View style={styles.inputGroup}>
                    <Text style={styles.label}>Cédula registrada en la clínica</Text>
                    <TextInput
                      style={styles.input}
                      placeholder="Ej. 1718899221"
                      placeholderTextColor="#94A3B8"
                      value={regCedula}
                      onChangeText={setRegCedula}
                      keyboardType="numeric"
                    />
                    <Text style={styles.inputHint}>
                      Enviaremos un código OTP de 6 dígitos a tu WhatsApp.
                    </Text>
                  </View>

                  <TouchableOpacity
                    style={styles.btnWhatsApp}
                    onPress={handleRequestOtp}
                    disabled={otpLoading}
                  >
                    {otpLoading ? (
                      <ActivityIndicator color="#FFFFFF" />
                    ) : (
                      <>
                        <MessageSquare size={18} color="#FFFFFF" />
                        <Text style={styles.btnWhatsAppText}>Enviar Código por WhatsApp</Text>
                      </>
                    )}
                  </TouchableOpacity>
                </View>
              )}

              {/* Step 2: Verify OTP */}
              {otpStep === 2 && (
                <View>
                  <View style={styles.inputGroup}>
                    <Text style={styles.label}>Código de Verificación (OTP)</Text>
                    <TextInput
                      style={[styles.input, styles.otpInput]}
                      placeholder="123456"
                      placeholderTextColor="#94A3B8"
                      value={otpCode}
                      onChangeText={setOtpCode}
                      keyboardType="numeric"
                      maxLength={6}
                    />
                    {simulatedOtp ? (
                      <View style={styles.simulatedBox}>
                        <Text style={styles.simulatedTitle}>📱 Mensaje WhatsApp Simulado:</Text>
                        <Text style={styles.simulatedCode}>
                          Tu código CraniumFit es: <Text style={{ fontWeight: 'bold' }}>{simulatedOtp}</Text>
                        </Text>
                      </View>
                    ) : null}
                  </View>

                  <TouchableOpacity
                    style={styles.btnPrimary}
                    onPress={handleVerifyOtp}
                    disabled={otpLoading}
                  >
                    {otpLoading ? (
                      <ActivityIndicator color="#FFFFFF" />
                    ) : (
                      <Text style={styles.btnPrimaryText}>Validar Código</Text>
                    )}
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.btnLink}
                    onPress={handleRequestOtp}
                    disabled={otpLoading}
                  >
                    <Text style={styles.btnLinkText}>Reenviar código</Text>
                  </TouchableOpacity>
                </View>
              )}

              {/* Step 3: Set Password */}
              {otpStep === 3 && (
                <View>
                  <View style={styles.inputGroup}>
                    <Text style={styles.label}>Crea tu Contraseña</Text>
                    <TextInput
                      style={styles.input}
                      placeholder="Mínimo 6 caracteres"
                      placeholderTextColor="#94A3B8"
                      value={newPassword}
                      onChangeText={setNewPassword}
                      secureTextEntry
                    />
                  </View>

                  <View style={styles.inputGroup}>
                    <Text style={styles.label}>Confirma tu Contraseña</Text>
                    <TextInput
                      style={styles.input}
                      placeholder="Repite tu contraseña"
                      placeholderTextColor="#94A3B8"
                      value={confirmPassword}
                      onChangeText={setConfirmPassword}
                      secureTextEntry
                    />
                  </View>

                  <TouchableOpacity
                    style={styles.btnPrimary}
                    onPress={handleSetPassword}
                    disabled={otpLoading}
                  >
                    {otpLoading ? (
                      <ActivityIndicator color="#FFFFFF" />
                    ) : (
                      <Text style={styles.btnPrimaryText}>Guardar y Acceder</Text>
                    )}
                  </TouchableOpacity>
                </View>
              )}
            </View>
          )}

          {/* Footer note */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>
              ¿Necesitas ayuda con el registro de tu bebé?
            </Text>
            <Text style={styles.footerPhone}>
              Llámanos a Sede Quito: (02) 299-8800 o Sede Lima: (01) 445-9922
            </Text>
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
    maxWidth: 500,
    width: '100%',
    alignSelf: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
  },
  logoBadge: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: '#CCFBF1',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
    borderWidth: 2,
    borderColor: '#99F6E4',
  },
  appTitle: {
    fontSize: 26,
    fontWeight: '800',
    color: '#0F172A',
    letterSpacing: -0.5,
  },
  appSubtitle: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 4,
    textAlign: 'center',
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
  modeTabs: {
    flexDirection: 'row',
    backgroundColor: '#E2E8F0',
    borderRadius: 12,
    padding: 4,
    marginBottom: 16,
  },
  modeTab: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 8,
  },
  modeTabActive: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  modeTabText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
  },
  modeTabTextActive: {
    color: '#0D9488',
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
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
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 4,
  },
  formDescription: {
    fontSize: 13,
    color: '#64748B',
    lineHeight: 18,
    marginBottom: 20,
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: '#334155',
    marginBottom: 6,
  },
  input: {
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    color: '#0F172A',
  },
  inputHint: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 4,
  },
  otpInput: {
    fontSize: 22,
    letterSpacing: 8,
    textAlign: 'center',
    fontWeight: '700',
  },
  simulatedBox: {
    backgroundColor: '#F0FDF4',
    borderWidth: 1,
    borderColor: '#BBF7D0',
    borderRadius: 8,
    padding: 10,
    marginTop: 10,
  },
  simulatedTitle: {
    fontSize: 11,
    fontWeight: '700',
    color: '#166534',
  },
  simulatedCode: {
    fontSize: 13,
    color: '#15803D',
    marginTop: 2,
  },
  btnPrimary: {
    backgroundColor: '#0D9488',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 8,
  },
  btnPrimaryText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  btnWhatsApp: {
    backgroundColor: '#16A34A',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    marginTop: 8,
  },
  btnWhatsAppText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  btnLink: {
    alignItems: 'center',
    marginTop: 12,
    padding: 6,
  },
  btnLinkText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#0D9488',
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
    fontSize: 12,
    color: '#94A3B8',
  },
  btnDemo: {
    backgroundColor: '#F0FDFA',
    borderWidth: 1.5,
    borderColor: '#99F6E4',
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 12,
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
  },
  btnDemoText: {
    color: '#0F766E',
    fontSize: 13,
    fontWeight: '700',
  },
  stepIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  stepDot: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#E2E8F0',
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepDotActive: {
    backgroundColor: '#0D9488',
  },
  stepDotText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#64748B',
  },
  stepDotTextActive: {
    color: '#FFFFFF',
  },
  stepLine: {
    width: 40,
    height: 3,
    backgroundColor: '#E2E8F0',
    marginHorizontal: 4,
  },
  stepLineActive: {
    backgroundColor: '#0D9488',
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
  alertSuccess: {
    backgroundColor: '#F0FDF4',
    borderWidth: 1,
    borderColor: '#BBF7D0',
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  alertSuccessText: {
    color: '#15803D',
    fontSize: 13,
    fontWeight: '500',
    flex: 1,
  },
  footer: {
    marginTop: 28,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#64748B',
  },
  footerPhone: {
    fontSize: 11,
    color: '#94A3B8',
    marginTop: 2,
    textAlign: 'center',
  },
});
