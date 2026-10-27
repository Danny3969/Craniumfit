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
import { useAuth } from '../context/AuthContext';
import {
  FileText,
  ShieldCheck,
  Download,
  Share2,
  Pill,
  Award,
  CheckCircle2,
  Lock,
  Building,
  QrCode,
} from 'lucide-react-native';

export default function DocumentsScreen() {
  const { dashboard } = useAuth();
  const [docTab, setDocTab] = useState<'prescriptions' | 'certificates' | 'dossiers'>('prescriptions');

  const prescription = dashboard?.active_prescription || {
    id: 'rx-902',
    doctor_name: 'Dr. Carlos Morales',
    issued_at: '2024-10-24',
    diagnosis: 'Plagiocefalia Posicional - Mantenimiento',
    medications: [
      { name: 'Loción Dermoprotectora Pediátrica', dose: '1 aplicación fina', freq: 'Antes de colocar ortesis tras baño', duration: 'Diario' },
      { name: 'Champú pH Neutro Hipoalergénico', dose: 'Lavado diario de cuero cabelludo', freq: '1 vez al día', duration: 'Tratamiento continuo' },
      { name: 'Alcohol Isopropílico al 70%', dose: 'Limpieza interna del casco con paño microfibra', freq: 'Cada noche durante baño', duration: 'Diario' }
    ],
    qr_hash: 'CF-RX-1710000002-2024-10-24-SECURE-SHA256'
  };

  const certificates = [
    {
      id: 'cert-101',
      title: 'Certificado Médico de Necesidad de Ortesis Craneal',
      type: 'Justificación Clínica Terapéutica',
      issued_date: '2024-08-01',
      doctor: 'Dr. Carlos Morales (Reg. Med. 17-9844)',
      digital_signature: 'Firmado Digitalmente (.p12 / BCE)',
      hash: 'SHA256: 4a8f9c2d1e0b...78a2',
      status: 'Válido & Vigente',
    },
    {
      id: 'cert-102',
      title: 'Certificado de Evolución y Reducción Biométrica',
      type: 'Informe de Reducción CVAI 11.2% -> 4.8%',
      issued_date: '2024-10-24',
      doctor: 'Dr. Carlos Morales (Reg. Med. 17-9844)',
      digital_signature: 'Firmado Digitalmente (.p12 / BCE)',
      hash: 'SHA256: 9e3c1b7a5f2d...33c1',
      status: 'Válido & Vigente',
    },
  ];

  const dossiers = [
    {
      id: 'dos-001',
      title: 'Expediente Técnico para Reembolso Aseguradora',
      insurer: 'SaludSA / Ecuasanitas / Pacífico EPS',
      generated_date: '2024-10-24',
      pages: '8 páginas con escaneos 3D y gráficos antropométricos',
      ready_for_claim: true,
    },
  ];

  const handleDownload = (docName: string) => {
    Alert.alert(
      'Documento Descargado',
      `El archivo "${docName}" ha sido generado con firma digital verificada y guardado en tu dispositivo.`,
      [{ text: 'OK' }]
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Documentos & Recetas</Text>
          <Text style={styles.subtitle}>
            Recetas activas, certificados con firma digital .p12 y dossiers para aseguradoras
          </Text>
        </View>

        {/* Tab Switcher */}
        <View style={styles.tabContainer}>
          <TouchableOpacity
            style={[styles.tabBtn, docTab === 'prescriptions' && styles.tabBtnActive]}
            onPress={() => setDocTab('prescriptions')}
          >
            <Text
              style={[
                styles.tabBtnText,
                docTab === 'prescriptions' && styles.tabBtnTextActive,
              ]}
            >
              Recetas
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tabBtn, docTab === 'certificates' && styles.tabBtnActive]}
            onPress={() => setDocTab('certificates')}
          >
            <Text
              style={[
                styles.tabBtnText,
                docTab === 'certificates' && styles.tabBtnTextActive,
              ]}
            >
              Certificados .p12
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tabBtn, docTab === 'dossiers' && styles.tabBtnActive]}
            onPress={() => setDocTab('dossiers')}
          >
            <Text
              style={[
                styles.tabBtnText,
                docTab === 'dossiers' && styles.tabBtnTextActive,
              ]}
            >
              Aseguradoras
            </Text>
          </TouchableOpacity>
        </View>

        {/* Tab 1: Prescriptions */}
        {docTab === 'prescriptions' && (
          <View>
            <View style={styles.rxCard}>
              <View style={styles.rxHeader}>
                <View style={styles.rxIconBox}>
                  <Pill size={22} color="#0D9488" />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.rxTag}>RECETA PEDIÁTRICA DIGITAL</Text>
                  <Text style={styles.rxDoctor}>{prescription.doctor_name}</Text>
                  <Text style={styles.rxDate}>Emitida el: {prescription.issued_at}</Text>
                </View>
                <View style={styles.activePill}>
                  <Text style={styles.activePillText}>Activa</Text>
                </View>
              </View>

              <View style={styles.rxDivider} />

              <Text style={styles.rxSectionTitle}>Medicaciones e Indicaciones Cutáneas:</Text>
              {prescription.medications?.map((m: any, idx: number) => (
                <View key={idx} style={styles.medItem}>
                  <Text style={styles.medName}>• {m.name}</Text>
                  <Text style={styles.medDose}>Dosis: {m.dose}</Text>
                  <Text style={styles.medFreq}>Frecuencia: {m.freq}</Text>
                </View>
              ))}

              <View style={styles.securityRow}>
                <QrCode size={18} color="#0F766E" />
                <View style={{ flex: 1 }}>
                  <Text style={styles.securityHash}>Hash Verificación Digital:</Text>
                  <Text style={styles.securityCode}>{prescription.qr_hash}</Text>
                </View>
              </View>

              <TouchableOpacity
                style={styles.btnDownload}
                onPress={() => handleDownload('Receta_Pediatrica_Lucas_Torres.pdf')}
              >
                <Download size={16} color="#FFFFFF" />
                <Text style={styles.btnDownloadText}>Descargar Receta en PDF</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Tab 2: Signed Certificates (.p12) */}
        {docTab === 'certificates' && (
          <View>
            {certificates.map((cert) => (
              <View key={cert.id} style={styles.certCard}>
                <View style={styles.certHeader}>
                  <View style={styles.certIconBox}>
                    <ShieldCheck size={22} color="#0D9488" />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.certTag}>{cert.type}</Text>
                    <Text style={styles.certTitle}>{cert.title}</Text>
                  </View>
                </View>

                <View style={styles.certBody}>
                  <Text style={styles.certDetail}>Médico: {cert.doctor}</Text>
                  <Text style={styles.certDetail}>Fecha de emisión: {cert.issued_date}</Text>

                  {/* Digital Signature Badge */}
                  <View style={styles.sigBadge}>
                    <Lock size={12} color="#15803D" />
                    <Text style={styles.sigBadgeText}>{cert.digital_signature}</Text>
                  </View>

                  <Text style={styles.certHash}>{cert.hash}</Text>
                </View>

                <View style={styles.certActions}>
                  <TouchableOpacity
                    style={styles.btnDownloadOutline}
                    onPress={() => handleDownload(`${cert.title}.pdf`)}
                  >
                    <Download size={14} color="#0D9488" />
                    <Text style={styles.btnDownloadOutlineText}>Descargar PDF Firmado</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.btnShare}
                    onPress={() => Alert.alert('Compartir', 'Enlace seguro copiado al portapapeles.')}
                  >
                    <Share2 size={14} color="#64748B" />
                  </TouchableOpacity>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* Tab 3: Insurance Dossiers */}
        {docTab === 'dossiers' && (
          <View>
            {dossiers.map((dos) => (
              <View key={dos.id} style={styles.dossierCard}>
                <View style={styles.dossierHeader}>
                  <View style={styles.dossierIconBox}>
                    <Building size={22} color="#0284C7" />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.dossierTag}>EXPEDIENTE MÉDICO PARA COBERTURA</Text>
                    <Text style={styles.dossierTitle}>{dos.title}</Text>
                  </View>
                </View>

                <View style={styles.dossierBody}>
                  <Text style={styles.dossierDetail}>Aseguradoras compatibles: {dos.insurer}</Text>
                  <Text style={styles.dossierDetail}>Contenido: {dos.pages}</Text>
                  <Text style={styles.dossierDetail}>Fecha de generación: {dos.generated_date}</Text>

                  <View style={styles.readyBadge}>
                    <CheckCircle2 size={13} color="#059669" />
                    <Text style={styles.readyBadgeText}>Listo para trámite de reembolso o carta de garantía</Text>
                  </View>
                </View>

                <TouchableOpacity
                  style={styles.btnDownload}
                  onPress={() => handleDownload('Dossier_Aseguradora_Lucas_Torres.pdf')}
                >
                  <Download size={16} color="#FFFFFF" />
                  <Text style={styles.btnDownloadText}>Descargar Dossier Completo (PDF)</Text>
                </TouchableOpacity>
              </View>
            ))}
          </View>
        )}
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
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#E2E8F0',
    borderRadius: 12,
    padding: 3,
    marginBottom: 16,
  },
  tabBtn: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 9,
  },
  tabBtnActive: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  tabBtnText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748B',
  },
  tabBtnTextActive: {
    color: '#0D9488',
    fontWeight: '700',
  },
  rxCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 2,
  },
  rxHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  rxIconBox: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#CCFBF1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  rxTag: {
    fontSize: 10,
    fontWeight: '800',
    color: '#0D9488',
    letterSpacing: 0.5,
  },
  rxDoctor: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  rxDate: {
    fontSize: 11,
    color: '#64748B',
  },
  activePill: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  activePillText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#15803D',
  },
  rxDivider: {
    height: 1,
    backgroundColor: '#E2E8F0',
    marginVertical: 12,
  },
  rxSectionTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#334155',
    marginBottom: 8,
  },
  medItem: {
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    padding: 10,
    marginBottom: 8,
  },
  medName: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F172A',
  },
  medDose: {
    fontSize: 11,
    color: '#475569',
    marginTop: 2,
  },
  medFreq: {
    fontSize: 11,
    color: '#0D9488',
    marginTop: 1,
    fontWeight: '600',
  },
  securityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#F0FDFA',
    borderRadius: 10,
    padding: 10,
    marginTop: 6,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#CCFBF1',
  },
  securityHash: {
    fontSize: 10,
    fontWeight: '700',
    color: '#0F766E',
  },
  securityCode: {
    fontSize: 10,
    color: '#0D9488',
    fontFamily: 'monospace',
  },
  btnDownload: {
    backgroundColor: '#0D9488',
    borderRadius: 12,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  btnDownloadText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  certCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 12,
  },
  certHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 10,
  },
  certIconBox: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#CCFBF1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  certTag: {
    fontSize: 10,
    fontWeight: '700',
    color: '#64748B',
    letterSpacing: 0.5,
  },
  certTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  certBody: {
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    padding: 10,
    gap: 4,
    marginBottom: 12,
  },
  certDetail: {
    fontSize: 11,
    color: '#475569',
  },
  sigBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    alignSelf: 'flex-start',
    gap: 4,
    marginTop: 4,
  },
  sigBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#15803D',
  },
  certHash: {
    fontSize: 9,
    color: '#94A3B8',
    fontFamily: 'monospace',
    marginTop: 2,
  },
  certActions: {
    flexDirection: 'row',
    gap: 8,
  },
  btnDownloadOutline: {
    flex: 1,
    borderWidth: 1.5,
    borderColor: '#0D9488',
    borderRadius: 10,
    paddingVertical: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  btnDownloadOutlineText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#0D9488',
  },
  btnShare: {
    width: 42,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F8FAFC',
  },
  dossierCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#BAE6FD',
    marginBottom: 12,
  },
  dossierHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 10,
  },
  dossierIconBox: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#E0F2FE',
    alignItems: 'center',
    justifyContent: 'center',
  },
  dossierTag: {
    fontSize: 10,
    fontWeight: '800',
    color: '#0284C7',
    letterSpacing: 0.5,
  },
  dossierTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  dossierBody: {
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    padding: 10,
    gap: 4,
    marginBottom: 12,
  },
  dossierDetail: {
    fontSize: 11,
    color: '#475569',
  },
  readyBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ECFDF5',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    gap: 4,
    marginTop: 4,
  },
  readyBadgeText: {
    fontSize: 11,
    color: '#059669',
    fontWeight: '600',
  },
});
