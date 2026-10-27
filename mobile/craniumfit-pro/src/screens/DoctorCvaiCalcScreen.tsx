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
import {
  Calculator,
  Activity,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  BookmarkPlus,
} from 'lucide-react-native';

export default function DoctorCvaiCalcScreen() {
  const [diagA, setDiagA] = useState('142');
  const [diagB, setDiagB] = useState('128');
  const [width, setWidth] = useState('126');
  const [length, setLength] = useState('154');
  const [circ, setCirc] = useState('42.5');

  // Math Calculations
  const a = parseFloat(diagA) || 0;
  const b = parseFloat(diagB) || 0;
  const w = parseFloat(width) || 0;
  const l = parseFloat(length) || 0;

  const diffMm = Math.abs(a - b);
  const maxDiag = Math.max(a, b);
  const cvai = maxDiag > 0 ? (diffMm / maxDiag) * 100 : 0;
  const ci = l > 0 ? (w / l) * 100 : 0;

  // Severity Classification
  const getCvaiSeverity = (val: number) => {
    if (val < 3.5) return { label: 'Normal / Fisiológico', color: '#10B981', bg: '#DCFCE7', textCol: '#15803D' };
    if (val < 6.25) return { label: 'Plagiocefalia Leve (Nivel 1-2)', color: '#FBBF24', bg: '#FEF3C7', textCol: '#B45309' };
    if (val < 8.75) return { label: 'Plagiocefalia Moderada (Nivel 3)', color: '#F97316', bg: '#FFEDD5', textCol: '#C2410C' };
    return { label: 'Plagiocefalia Severa (Nivel 4-5)', color: '#EF4444', bg: '#FEE2E2', textCol: '#B91C1C' };
  };

  const getCiClassification = (val: number) => {
    if (val < 75) return { label: 'Dolicocéfalo / Escafocefalia', color: '#0284C7' };
    if (val <= 85) return { label: 'Normocéfalo / Mesocefalia', color: '#10B981' };
    return { label: 'Braquicéfalo / Aplanamiento Bilateral', color: '#F97316' };
  };

  const cvaiSev = getCvaiSeverity(cvai);
  const ciClass = getCiClassification(ci);

  const applyPreset = (presetA: number, presetB: number, presetW: number, presetL: number) => {
    setDiagA(presetA.toString());
    setDiagB(presetB.toString());
    setWidth(presetW.toString());
    setLength(presetL.toString());
  };

  const handleSaveToPatient = () => {
    Alert.alert(
      'Cálculo Registrado',
      `Mediciones guardadas: CVAI ${cvai.toFixed(1)}% (${cvaiSev.label}), CI ${ci.toFixed(1)}% en la ficha clínica del paciente.`,
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
          <Text style={styles.title}>Calculadora Biométrica CVAI & CI</Text>
          <Text style={styles.subtitle}>
            Índice de Asimetría Craneal (Children's Healthcare of Atlanta / CHOP)
          </Text>
        </View>

        {/* Results Banner */}
        <View style={styles.resultBanner}>
          <View style={styles.resultCol}>
            <Text style={styles.resultLabel}>CVAI Resultante</Text>
            <Text style={[styles.resultVal, { color: cvaiSev.color }]}>
              {cvai.toFixed(1)}%
            </Text>
            <View style={[styles.sevBadge, { backgroundColor: cvaiSev.bg }]}>
              <Text style={[styles.sevBadgeText, { color: cvaiSev.textCol }]}>
                {cvaiSev.label}
              </Text>
            </View>
          </View>

          <View style={styles.resultDivider} />

          <View style={styles.resultCol}>
            <Text style={styles.resultLabel}>Índice Cefálico (CI)</Text>
            <Text style={[styles.resultVal, { color: ciClass.color }]}>
              {ci.toFixed(1)}%
            </Text>
            <Text style={styles.ciLabelText}>{ciClass.label}</Text>
          </View>
        </View>

        {/* Asymmetry Metrics details */}
        <View style={styles.asymCard}>
          <Text style={styles.asymCardTitle}>Diferencia Diagonal de Bóveda:</Text>
          <Text style={styles.asymMmText}>
            Δ = |{a}mm - {b}mm| = <Text style={{ fontWeight: '800', color: '#0F172A' }}>{diffMm.toFixed(1)} mm</Text>
          </Text>
          <Text style={styles.asymNote}>
            {diffMm >= 10
              ? '⚠️ Indicación clara para ortesis de remodelación dinámica (desviación ≥ 10mm).'
              : diffMm >= 6
              ? '🟡 Rango moderado: Tratamiento postural y ortesis según edad (meses 4-8).'
              : '🟢 Asimetría fisiológica leve o resuelta.'}
          </Text>
        </View>

        {/* Inputs Grid */}
        <View style={styles.card}>
          <Text style={styles.cardSectionTitle}>Mediciones de Calibre / Escáner (mm):</Text>

          <View style={styles.inputRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.inputLabel}>Diagonal A (Mayor, mm)</Text>
              <TextInput
                style={styles.input}
                value={diagA}
                onChangeText={setDiagA}
                keyboardType="numeric"
              />
            </View>

            <View style={{ flex: 1, marginLeft: 12 }}>
              <Text style={styles.inputLabel}>Diagonal B (Menor, mm)</Text>
              <TextInput
                style={styles.input}
                value={diagB}
                onChangeText={setDiagB}
                keyboardType="numeric"
              />
            </View>
          </View>

          <View style={[styles.inputRow, { marginTop: 12 }]}>
            <View style={{ flex: 1 }}>
              <Text style={styles.inputLabel}>Ancho Cefálico (Eu-Eu, mm)</Text>
              <TextInput
                style={styles.input}
                value={width}
                onChangeText={setWidth}
                keyboardType="numeric"
              />
            </View>

            <View style={{ flex: 1, marginLeft: 12 }}>
              <Text style={styles.inputLabel}>Largo Cefálico (G-Op, mm)</Text>
              <TextInput
                style={styles.input}
                value={length}
                onChangeText={setLength}
                keyboardType="numeric"
              />
            </View>
          </View>

          <View style={{ marginTop: 12 }}>
            <Text style={styles.inputLabel}>Perímetro Cefálico (cm)</Text>
            <TextInput
              style={styles.input}
              value={circ}
              onChangeText={setCirc}
              keyboardType="numeric"
            />
          </View>

          {/* Quick Presets */}
          <Text style={styles.presetTitle}>Casos Típicos Clínicos:</Text>
          <View style={styles.presetGrid}>
            <TouchableOpacity
              style={styles.presetBtn}
              onPress={() => applyPreset(145, 126, 128, 152)}
            >
              <Text style={styles.presetBtnText}>Severa (13.1%)</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.presetBtn}
              onPress={() => applyPreset(139, 129, 125, 150)}
            >
              <Text style={styles.presetBtnText}>Moderada (7.2%)</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.presetBtn}
              onPress={() => applyPreset(135, 130, 124, 151)}
            >
              <Text style={styles.presetBtnText}>Leve (3.7%)</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.presetBtn}
              onPress={() => applyPreset(132, 131, 123, 152)}
            >
              <Text style={styles.presetBtnText}>Simétrico (0.8%)</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={styles.btnSave}
            onPress={handleSaveToPatient}
          >
            <BookmarkPlus size={18} color="#FFFFFF" />
            <Text style={styles.btnSaveText}>Guardar Cálculo en Ficha de Paciente</Text>
          </TouchableOpacity>
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
  resultBanner: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 3,
  },
  resultCol: {
    flex: 1,
    alignItems: 'center',
  },
  resultDivider: {
    width: 1,
    height: 60,
    backgroundColor: '#E2E8F0',
    alignSelf: 'center',
  },
  resultLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#64748B',
    marginBottom: 2,
  },
  resultVal: {
    fontSize: 28,
    fontWeight: '900',
    letterSpacing: -1,
  },
  sevBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    marginTop: 4,
  },
  sevBadgeText: {
    fontSize: 10,
    fontWeight: '700',
  },
  ciLabelText: {
    fontSize: 10,
    color: '#475569',
    marginTop: 4,
    textAlign: 'center',
    fontWeight: '600',
  },
  asymCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 14,
  },
  asymCardTitle: {
    fontSize: 11,
    fontWeight: '600',
    color: '#64748B',
  },
  asymMmText: {
    fontSize: 15,
    color: '#0F172A',
    marginTop: 2,
  },
  asymNote: {
    fontSize: 11,
    color: '#475569',
    marginTop: 4,
    lineHeight: 16,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  cardSectionTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 12,
  },
  inputRow: {
    flexDirection: 'row',
  },
  inputLabel: {
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
    fontSize: 14,
    color: '#0F172A',
    fontWeight: '600',
  },
  presetTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#334155',
    marginTop: 16,
    marginBottom: 8,
  },
  presetGrid: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  presetBtn: {
    flex: 1,
    backgroundColor: '#F1F5F9',
    borderRadius: 8,
    paddingVertical: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  presetBtnText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#475569',
  },
  btnSave: {
    backgroundColor: '#0D9488',
    borderRadius: 12,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  btnSaveText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
});
