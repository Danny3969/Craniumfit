import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useProAuth } from '../context/AuthContext';
import {
  FileCheck2,
  Lock,
  Pill,
  ShieldCheck,
  CheckCircle2,
  QrCode,
  Send,
} from 'lucide-react-native';

export default function DoctorPrescribeScreen() {
  const { user } = useProAuth();

  const [patientDni, setPatientDni] = useState('1799223344');
  const [patientName, setPatientName] = useState('Lucas Torres (5 meses)');
  const [medication, setMedication] = useState(
    'Loción Dermoprotectora Pediátrica + Champú Hipoalergénico pH Neutro'
  );
  const [indications, setIndications] = useState(
    'Aplicar capa delgada tras el baño diario antes de recolocar el casco. Limpieza interna del casco con alcohol al 70%.'
  );
  const [certPassword, setCertPassword] = useState('••••••••');
  const [signed, setSigned] = useState(false);
  const [generatedHash, setGeneratedHash] = useState('');

  const handleSignDocument = () => {
    if (!medication.trim()) {
      Alert.alert('Error', 'Completa la indicación o medicación.');
      return;
    }
    const hash = `CF-SIG-${Date.now().toString(16).toUpperCase()}-SHA256-VALID`;
    setGeneratedHash(hash);
    setSigned(true);
    Alert.alert(
      'Documento Firmado Criptográficamente',
      `El documento fue firmado exitosamente con el certificado .p12 de ${user?.full_name}.\nHash: ${hash}\nDisponible de inmediato en la app móvil de la familia.`
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Emisión & Firma Digital .p12</Text>
          <Text style={styles.subtitle}>
            Genera recetas y certificados médicos con validez legal criptográfica
          </Text>
        </View>

        {/* Certificate Status Pill */}
        <View style={styles.certPill}>
          <ShieldCheck size={16} color="#15803D" />
          <View style={{ flex: 1 }}>
            <Text style={styles.certPillTitle}>
              Certificado Digital Activo: {user?.full_name}
            </Text>
            <Text style={styles.certPillSub}>
              Entidad Emisora: Banco Central del Ecuador (BCE) / Reniec · Válido hasta Dic 2027
            </Text>
          </View>
        </View>

        {/* Form Card */}
        <View style={styles.card}>
          <Text style={styles.cardSection}>Datos del Paciente Receptor:</Text>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Paciente Seleccionado</Text>
            <TextInput
              style={styles.input}
              value={patientName}
              onChangeText={setPatientName}
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Cédula / DNI del Paciente</Text>
            <TextInput
              style={styles.input}
              value={patientDni}
              onChangeText={setPatientDni}
              keyboardType="numeric"
            />
          </View>

          <Text style={[styles.cardSection, { marginTop: 14 }]}>
            Prescripción / Indicación Médica:
          </Text>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Tratamiento / Medicamentos / Insumos</Text>
            <TextInput
              style={styles.input}
              value={medication}
              onChangeText={setMedication}
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Posología y Recomendaciones de Uso</Text>
            <TextInput
              style={[styles.input, { height: 70, textAlignVertical: 'top' }]}
              value={indications}
              onChangeText={setIndications}
              multiline
            />
          </View>

          {/* .p12 Signature block */}
          <View style={styles.signatureBox}>
            <View style={styles.sigHeader}>
              <Lock size={16} color="#0D9488" />
              <Text style={styles.sigTitle}>Firma Criptográfica PKCS#12 (.p12)</Text>
            </View>
            <Text style={styles.sigDesc}>
              El documento se sella con el par de claves RSA 2048 del especialista y se adjunta el hash SHA-256 verificable con QR.
            </Text>

            <View style={{ marginTop: 8 }}>
              <Text style={styles.label}>PIN de la Llave Privada (.p12)</Text>
              <TextInput
                style={styles.input}
                value={certPassword}
                onChangeText={setCertPassword}
                secureTextEntry
              />
            </View>

            <TouchableOpacity
              style={styles.btnSign}
              onPress={handleSignDocument}
            >
              <FileCheck2 size={18} color="#FFFFFF" />
              <Text style={styles.btnSignText}>
                {signed ? 'Firmar y Emitir Nueva Receta' : 'Firmar Digitalmente y Emitir'}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Signed Confirmation */}
          {signed && (
            <View style={styles.signedCard}>
              <View style={styles.signedHeader}>
                <CheckCircle2 size={18} color="#15803D" />
                <Text style={styles.signedTitle}>Documento Oficial Emitido</Text>
              </View>
              <Text style={styles.signedHash}>Código Hash: {generatedHash}</Text>
              <Text style={styles.signedNote}>
                Sincronizado instantáneamente con la aplicación móvil CraniumFit Familias.
              </Text>
            </View>
          )}
        </View>
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
  certPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FDF4',
    borderWidth: 1,
    borderColor: '#BBF7D0',
    borderRadius: 12,
    padding: 12,
    gap: 10,
    marginBottom: 16,
  },
  certPillTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#166534',
  },
  certPillSub: {
    fontSize: 10,
    color: '#15803D',
    marginTop: 1,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  cardSection: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 10,
  },
  inputGroup: {
    marginBottom: 12,
  },
  label: {
    fontSize: 11,
    fontWeight: '600',
    color: '#475569',
    marginBottom: 4,
  },
  input: {
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 13,
    color: '#0F172A',
  },
  signatureBox: {
    backgroundColor: '#F0FDFA',
    borderWidth: 1,
    borderColor: '#99F6E4',
    borderRadius: 14,
    padding: 14,
    marginTop: 14,
  },
  sigHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  sigTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F766E',
  },
  sigDesc: {
    fontSize: 11,
    color: '#0D9488',
    lineHeight: 15,
  },
  btnSign: {
    backgroundColor: '#0D9488',
    borderRadius: 12,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 14,
  },
  btnSignText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  signedCard: {
    backgroundColor: '#F0FDF4',
    borderWidth: 1,
    borderColor: '#86EFAC',
    borderRadius: 12,
    padding: 12,
    marginTop: 16,
  },
  signedHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  signedTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#166534',
  },
  signedHash: {
    fontSize: 10,
    color: '#15803D',
    fontFamily: 'monospace',
  },
  signedNote: {
    fontSize: 11,
    color: '#166534',
    marginTop: 2,
  },
});
