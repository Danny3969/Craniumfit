import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../context/AuthContext';
import {
  TrendingDown,
  Activity,
  Layers,
  Award,
  Calendar,
  CheckCircle2,
  FileCheck2,
  Eye,
  Sparkles,
} from 'lucide-react-native';

export default function EvolutionScreen() {
  const { dashboard } = useAuth();
  const evolution = dashboard?.evolution || {
    baseline_cvai: 11.2,
    current_cvai: 4.8,
    delta: -6.4,
    reduction_pct: 57.1,
    sessions_count: 4,
    scans: [
      { session_number: 1, scan_date: '2024-08-01', cvai: 11.2, ci: 88.5, status: 'Severo' },
      { session_number: 2, scan_date: '2024-08-29', cvai: 8.9, ci: 85.3, status: 'Moderado' },
      { session_number: 3, scan_date: '2024-09-26', cvai: 6.4, ci: 83.1, status: 'Leve' },
      { session_number: 4, scan_date: '2024-10-24', cvai: 4.8, ci: 81.2, status: 'Normal / Leve' },
    ],
  };

  const [scanView, setScanView] = useState<'after' | 'before'>('after');

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Evolución Biométrica 3D</Text>
          <Text style={styles.subtitle}>
            Mediciones antropométricas por escáner de luz estructurada
          </Text>
        </View>

        {/* CVAI Hero Card */}
        <View style={styles.heroCard}>
          <View style={styles.heroHeader}>
            <View style={styles.heroIconBox}>
              <TrendingDown size={24} color="#0D9488" />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.heroTag}>ÍNDICE DE ASIMETRÍA DE LA BÓVEDA CRANEAL</Text>
              <Text style={styles.heroTitle}>CVAI actual: {evolution.current_cvai}%</Text>
            </View>
            <View style={styles.reductionBadge}>
              <Text style={styles.reductionBadgeText}>
                {evolution.delta}% ({evolution.reduction_pct}%)
              </Text>
            </View>
          </View>

          {/* Comparison numbers */}
          <View style={styles.comparisonGrid}>
            <View style={styles.comparisonCol}>
              <Text style={styles.colLabel}>Escaneo Inicial</Text>
              <Text style={styles.colValue}>{evolution.baseline_cvai}%</Text>
              <View style={[styles.colBadge, { backgroundColor: '#FEE2E2' }]}>
                <Text style={[styles.colBadgeText, { color: '#DC2626' }]}>Severo</Text>
              </View>
            </View>

            <View style={styles.arrowCol}>
              <Text style={styles.arrowText}>➔</Text>
            </View>

            <View style={styles.comparisonCol}>
              <Text style={styles.colLabel}>Último Control</Text>
              <Text style={[styles.colValue, { color: '#0D9488' }]}>
                {evolution.current_cvai}%
              </Text>
              <View style={[styles.colBadge, { backgroundColor: '#DCFCE7' }]}>
                <Text style={[styles.colBadgeText, { color: '#166534' }]}>Normal / Leve</Text>
              </View>
            </View>
          </View>

          {/* Severity bar */}
          <View style={styles.scaleContainer}>
            <Text style={styles.scaleTitle}>Escala Pediátrica de Asimetría (CHOP / Children's Hospital):</Text>
            <View style={styles.scaleBar}>
              <View style={[styles.scaleSegment, { flex: 3.5, backgroundColor: '#10B981' }]} />
              <View style={[styles.scaleSegment, { flex: 2.75, backgroundColor: '#FBBF24' }]} />
              <View style={[styles.scaleSegment, { flex: 2.5, backgroundColor: '#FB923C' }]} />
              <View style={[styles.scaleSegment, { flex: 5, backgroundColor: '#F87171' }]} />
            </View>
            <View style={styles.scaleLabels}>
              <Text style={styles.scaleLabelText}>Normal (&lt;3.5%)</Text>
              <Text style={styles.scaleLabelText}>Leve (3.5-6.25%)</Text>
              <Text style={styles.scaleLabelText}>Mod (6.25-8.75%)</Text>
              <Text style={styles.scaleLabelText}>Sev (&gt;8.75%)</Text>
            </View>
          </View>

          <View style={styles.successCallout}>
            <Sparkles size={16} color="#0F766E" />
            <Text style={styles.successCalloutText}>
              ¡Meta clínica alcanzada! La asimetría diagonal se redujo más de 6 milímetros desde el inicio.
            </Text>
          </View>
        </View>

        {/* Cephalic Index Card */}
        <View style={styles.ciCard}>
          <View style={styles.ciHeader}>
            <Activity size={20} color="#0284C7" />
            <Text style={styles.ciTitle}>Índice Cefálico (Proporción Ancho / Largo)</Text>
          </View>
          <View style={styles.ciBody}>
            <View style={styles.ciNumberBox}>
              <Text style={styles.ciNumber}>81.2%</Text>
              <Text style={styles.ciStatus}>Rango Normocefálico Óptimo</Text>
            </View>
            <View style={styles.ciInfoBox}>
              <Text style={styles.ciInfoText}>
                Inicial: 88.5% (Braquicefalia leve) {'\n'}
                Rango estándar: 75% a 85% {'\n'}
                Proporción armónica simétrica recuperada.
              </Text>
            </View>
          </View>
        </View>

        {/* 3D Scan Visual Simulation Card */}
        <View style={styles.scanVisualCard}>
          <View style={styles.scanVisualHeader}>
            <View style={{ flex: 1 }}>
              <Text style={styles.scanVisualTag}>RECONSTRUCCIÓN CRANEAL 3D</Text>
              <Text style={styles.scanVisualTitle}>Topografía del Cuero Cabelludo</Text>
            </View>

            {/* Toggle */}
            <View style={styles.viewToggle}>
              <TouchableOpacity
                style={[styles.toggleBtn, scanView === 'before' && styles.toggleBtnActive]}
                onPress={() => setScanView('before')}
              >
                <Text
                  style={[
                    styles.toggleBtnText,
                    scanView === 'before' && styles.toggleBtnTextActive,
                  ]}
                >
                  Antes
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.toggleBtn, scanView === 'after' && styles.toggleBtnActive]}
                onPress={() => setScanView('after')}
              >
                <Text
                  style={[
                    styles.toggleBtnText,
                    scanView === 'after' && styles.toggleBtnTextActive,
                  ]}
                >
                  Actual
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Cranial Mesh Representation */}
          <View style={styles.meshCanvas}>
            <View style={styles.cranialOvalWrapper}>
              <View
                style={[
                  styles.cranialOval,
                  scanView === 'before' ? styles.ovalAsymmetric : styles.ovalSymmetric,
                ]}
              >
                <Text style={styles.ovalFrontLabel}>Frente (Glabela)</Text>
                <View style={styles.diagonalLines}>
                  <View
                    style={[
                      styles.diagLineA,
                      scanView === 'before' && { backgroundColor: '#EF4444', height: 2 },
                    ]}
                  />
                  <View
                    style={[
                      styles.diagLineB,
                      scanView === 'before' && { backgroundColor: '#3B82F6', height: 2 },
                    ]}
                  />
                </View>
                <Text style={styles.ovalBackLabel}>Occipucio</Text>
              </View>
            </View>

            <View style={styles.meshDetails}>
              <Text style={styles.meshDetailsTitle}>
                {scanView === 'before'
                  ? 'Escaneo Inicial (01 de Agosto de 2024)'
                  : 'Escaneo de Control Nº 4 (24 de Octubre de 2024)'}
              </Text>
              <Text style={styles.meshDetailsText}>
                {scanView === 'before'
                  ? 'Aplanamiento occipital derecho severo con abombamiento frontal ipsilateral. CVAI: 11.2%'
                  : 'Redondez occipital simétrica recuperada con expansión controlada en zona de descompresión. CVAI: 4.8%'}
              </Text>
            </View>
          </View>
        </View>

        {/* Scans Timeline */}
        <Text style={styles.timelineHeader}>Historial de Escaneos 3D de Control</Text>
        {evolution.scans?.map((s: any, idx: number) => (
          <View key={idx} style={styles.timelineCard}>
            <View style={styles.timelineIconBox}>
              <CheckCircle2 size={16} color="#0D9488" />
            </View>
            <View style={{ flex: 1 }}>
              <View style={styles.timelineRow}>
                <Text style={styles.timelineSession}>Sesión Nº {s.session_number}</Text>
                <Text style={styles.timelineDate}>{s.scan_date}</Text>
              </View>
              <View style={styles.timelineMetrics}>
                <Text style={styles.timelineMetricsText}>
                  CVAI: <Text style={{ fontWeight: '700', color: '#0F172A' }}>{s.cvai}%</Text> · CI: {s.ci}% · Estado: {s.status}
                </Text>
              </View>
            </View>
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
  heroCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 3,
  },
  heroHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 16,
  },
  heroIconBox: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#CCFBF1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  heroTag: {
    fontSize: 10,
    fontWeight: '800',
    color: '#0D9488',
    letterSpacing: 0.5,
  },
  heroTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: '#0F172A',
  },
  reductionBadge: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  reductionBadgeText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#15803D',
  },
  comparisonGrid: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderRadius: 14,
    padding: 14,
    marginBottom: 16,
  },
  comparisonCol: {
    flex: 1,
    alignItems: 'center',
  },
  arrowCol: {
    paddingHorizontal: 8,
  },
  arrowText: {
    fontSize: 18,
    color: '#94A3B8',
  },
  colLabel: {
    fontSize: 11,
    color: '#64748B',
    marginBottom: 4,
  },
  colValue: {
    fontSize: 22,
    fontWeight: '800',
    color: '#0F172A',
  },
  colBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    marginTop: 4,
  },
  colBadgeText: {
    fontSize: 10,
    fontWeight: '700',
  },
  scaleContainer: {
    marginBottom: 14,
  },
  scaleTitle: {
    fontSize: 11,
    fontWeight: '600',
    color: '#475569',
    marginBottom: 6,
  },
  scaleBar: {
    flexDirection: 'row',
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 4,
  },
  scaleSegment: {
    height: '100%',
  },
  scaleLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  scaleLabelText: {
    fontSize: 9,
    color: '#94A3B8',
  },
  successCallout: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FDFA',
    borderWidth: 1,
    borderColor: '#99F6E4',
    borderRadius: 12,
    padding: 10,
    gap: 8,
  },
  successCalloutText: {
    fontSize: 12,
    color: '#0F766E',
    flex: 1,
    fontWeight: '500',
  },
  ciCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 16,
  },
  ciHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  ciTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  ciBody: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ciNumberBox: {
    alignItems: 'center',
    paddingRight: 16,
    borderRightWidth: 1,
    borderRightColor: '#E2E8F0',
  },
  ciNumber: {
    fontSize: 24,
    fontWeight: '800',
    color: '#0284C7',
  },
  ciStatus: {
    fontSize: 10,
    fontWeight: '600',
    color: '#059669',
    marginTop: 2,
  },
  ciInfoBox: {
    flex: 1,
    paddingLeft: 16,
  },
  ciInfoText: {
    fontSize: 11,
    color: '#64748B',
    lineHeight: 16,
  },
  scanVisualCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 16,
  },
  scanVisualHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  scanVisualTag: {
    fontSize: 10,
    fontWeight: '800',
    color: '#64748B',
    letterSpacing: 0.5,
  },
  scanVisualTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  viewToggle: {
    flexDirection: 'row',
    backgroundColor: '#F1F5F9',
    borderRadius: 10,
    padding: 3,
  },
  toggleBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  toggleBtnActive: {
    backgroundColor: '#0D9488',
  },
  toggleBtnText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#64748B',
  },
  toggleBtnTextActive: {
    color: '#FFFFFF',
  },
  meshCanvas: {
    backgroundColor: '#F8FAFC',
    borderRadius: 14,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  cranialOvalWrapper: {
    width: 180,
    height: 180,
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 10,
  },
  cranialOval: {
    width: 140,
    height: 170,
    borderRadius: 70,
    borderWidth: 3,
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 10,
    position: 'relative',
  },
  ovalAsymmetric: {
    borderColor: '#EF4444',
    transform: [{ skewX: '-8deg' }],
    backgroundColor: 'rgba(239, 68, 68, 0.05)',
  },
  ovalSymmetric: {
    borderColor: '#10B981',
    transform: [{ skewX: '0deg' }],
    backgroundColor: 'rgba(16, 185, 129, 0.05)',
  },
  ovalFrontLabel: {
    fontSize: 9,
    fontWeight: '700',
    color: '#64748B',
  },
  ovalBackLabel: {
    fontSize: 9,
    fontWeight: '700',
    color: '#64748B',
  },
  diagonalLines: {
    position: 'absolute',
    width: 120,
    height: 120,
    top: 25,
    left: 10,
  },
  diagLineA: {
    position: 'absolute',
    width: 120,
    height: 1,
    backgroundColor: '#CBD5E1',
    top: 60,
    transform: [{ rotate: '45deg' }],
  },
  diagLineB: {
    position: 'absolute',
    width: 120,
    height: 1,
    backgroundColor: '#CBD5E1',
    top: 60,
    transform: [{ rotate: '-45deg' }],
  },
  meshDetails: {
    marginTop: 10,
    alignItems: 'center',
  },
  meshDetailsTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#0F172A',
  },
  meshDetailsText: {
    fontSize: 11,
    color: '#64748B',
    textAlign: 'center',
    marginTop: 2,
    paddingHorizontal: 10,
  },
  timelineHeader: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 10,
  },
  timelineCard: {
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
  timelineIconBox: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#CCFBF1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  timelineRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  timelineSession: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F172A',
  },
  timelineDate: {
    fontSize: 11,
    color: '#64748B',
  },
  timelineMetrics: {
    marginTop: 2,
  },
  timelineMetricsText: {
    fontSize: 11,
    color: '#475569',
  },
});
