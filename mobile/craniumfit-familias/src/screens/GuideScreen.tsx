import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Linking,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  BookOpen,
  Calendar,
  Sparkles,
  AlertTriangle,
  MessageSquare,
  CheckCircle2,
  Clock,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
} from 'lucide-react-native';

export default function GuideScreen() {
  const [selectedDay, setSelectedDay] = useState<number>(5);

  const adaptationDays = [
    {
      day: 1,
      title: 'Día 1: Primer Contacto',
      wearTime: '1h uso / 1h descanso',
      total: '4 horas totales',
      sleep: 'No usar para dormir',
      instructions:
        'Coloca la ortesis 1 hora mientras el bebé está despierto. Retíralo 1 hora e inspecciona la piel. Repite 2 veces en el día. No colocar durante la noche.',
    },
    {
      day: 2,
      title: 'Día 2: Adaptación Diurna',
      wearTime: '2h uso / 1h descanso',
      total: '6 a 8 horas totales',
      sleep: 'No usar para dormir',
      instructions:
        'Aumenta a periodos de 2 horas continuas con 1 hora de descanso para revisar puntos de presión. No usar para dormir todavía.',
    },
    {
      day: 3,
      title: 'Día 3: Primera Siesta',
      wearTime: '4h uso / 1h descanso',
      total: '10 a 12 horas totales',
      sleep: 'Incluye siesta diurna',
      instructions:
        'El bebé ya puede usar el casco durante una siesta diurna. Al despertar, retira el casco y verifica que no queden marcas rojas fijas.',
    },
    {
      day: 4,
      title: 'Día 4: Primera Noche',
      wearTime: 'Uso continuo diurno y nocturno',
      total: '18 a 20 horas totales',
      sleep: 'Uso durante toda la noche',
      instructions:
        'Coloca el casco para el sueño nocturno. El bebé comenzará a acostumbrarse a la postura de sueño con la ortesis.',
    },
    {
      day: 5,
      title: 'Día 5+: Protocolo Completo 23 Horas',
      wearTime: '23 horas continuas',
      total: '23h día / 1h descanso',
      sleep: 'Todas las siestas y noches',
      instructions:
        '¡Meta alcanzada! El casco debe usarse 23 horas continuas. La única hora de pausa es para el baño diario del bebé y la desinfección interna del casco.',
    },
  ];

  const handleWhatsAppSOS = () => {
    const phone = "+593998877665";
    const msg = encodeURIComponent(
      "Hola Dr. Carlos Morales / Equipo CraniumFit, soy mamá de Lucas Torres. Tengo una consulta sobre el uso de la ortesis craneal."
    );
    const url = `https://wa.me/${phone}?text=${msg}`;
    Linking.openURL(url).catch(() => {
      Alert.alert(
        'WhatsApp no disponible',
        'Puedes comunicarte al teléfono directo de guardia pediátrica: +593 99 887 7665'
      );
    });
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Guía de Cuidados & Protocolo</Text>
          <Text style={styles.subtitle}>
            Instrucciones clínicas oficiales para la correcta adaptación y uso del casco
          </Text>
        </View>

        {/* SOS WhatsApp Button */}
        <TouchableOpacity style={styles.btnSos} onPress={handleWhatsAppSOS}>
          <MessageSquare size={20} color="#FFFFFF" />
          <View style={{ flex: 1 }}>
            <Text style={styles.btnSosTitle}>¿Dudas o Emergencia Cutánea?</Text>
            <Text style={styles.btnSosSubtitle}>
              Chat directo con el Dr. Carlos Morales y guardia médica
            </Text>
          </View>
        </TouchableOpacity>

        {/* 5-Day Adaptation Schedule */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Calendar size={20} color="#0D9488" />
            <Text style={styles.cardTitle}>Protocolo de Adaptación de 5 Días</Text>
          </View>

          {/* Day Pills */}
          <View style={styles.dayPillsRow}>
            {adaptationDays.map((d) => (
              <TouchableOpacity
                key={d.day}
                style={[
                  styles.dayPill,
                  selectedDay === d.day && styles.dayPillActive,
                ]}
                onPress={() => setSelectedDay(d.day)}
              >
                <Text
                  style={[
                    styles.dayPillText,
                    selectedDay === d.day && styles.dayPillTextActive,
                  ]}
                >
                  Día {d.day}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Selected Day Details */}
          {(() => {
            const current = adaptationDays.find((d) => d.day === selectedDay)!;
            return (
              <View style={styles.dayDetails}>
                <Text style={styles.dayTitle}>{current.title}</Text>

                <View style={styles.dayMetaGrid}>
                  <View style={styles.dayMetaItem}>
                    <Clock size={14} color="#0D9488" />
                    <Text style={styles.dayMetaText}>{current.wearTime}</Text>
                  </View>
                  <View style={styles.dayMetaItem}>
                    <Sparkles size={14} color="#0284C7" />
                    <Text style={styles.dayMetaText}>{current.total}</Text>
                  </View>
                </View>

                <View style={styles.sleepBadge}>
                  <Text style={styles.sleepBadgeText}>Sueño: {current.sleep}</Text>
                </View>

                <Text style={styles.dayInstructions}>{current.instructions}</Text>
              </View>
            );
          })()}
        </View>

        {/* Hygiene & Cleaning Protocol */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Sparkles size={20} color="#0284C7" />
            <Text style={styles.cardTitle}>Protocolo Diario de Higiene</Text>
          </View>

          <View style={styles.hygieneStep}>
            <View style={styles.stepNum}>
              <Text style={styles.stepNumText}>1</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.stepTitle}>Limpieza con Alcohol Isopropílico 70%</Text>
              <Text style={styles.stepDesc}>
                Aplica alcohol al 70% en una toalla de microfibra limpia y frota cuidadosamente el interior de espuma del casco para eliminar grasa y bacterias.
              </Text>
            </View>
          </View>

          <View style={styles.hygieneStep}>
            <View style={styles.stepNum}>
              <Text style={styles.stepNumText}>2</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.stepTitle}>Secado Exclusivo al Aire</Text>
              <Text style={styles.stepDesc}>
                Deja secar el casco al aire durante los 45 minutos que dura el baño del bebé. <Text style={{ fontWeight: '700', color: '#DC2626' }}>NUNCA</Text> uses secador de pelo ni lo expongas a estufas (deformaría la ortesis).
              </Text>
            </View>
          </View>

          <View style={styles.hygieneStep}>
            <View style={styles.stepNum}>
              <Text style={styles.stepNumText}>3</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.stepTitle}>Baño y Lavado del Bebé</Text>
              <Text style={styles.stepDesc}>
                Lava el cuero cabelludo del bebé con champú neutro hipoalergénico. Seca completamente el cabello antes de volver a colocar el casco.
              </Text>
            </View>
          </View>
        </View>

        {/* Warning Signs */}
        <View style={[styles.card, { borderColor: '#FECACA' }]}>
          <View style={styles.cardHeader}>
            <ShieldAlert size={20} color="#DC2626" />
            <Text style={[styles.cardTitle, { color: '#B91C1C' }]}>
              Diferenciar Normal vs Signo de Alerta
            </Text>
          </View>

          <View style={styles.alertRow}>
            <CheckCircle2 size={16} color="#15803D" />
            <View style={{ flex: 1 }}>
              <Text style={styles.alertLabelGreen}>Normal:</Text>
              <Text style={styles.alertText}>
                Enrojecimiento rosado parejo que desaparece antes de 30 a 45 minutos tras retirar el casco. Sudoración en la primera semana.
              </Text>
            </View>
          </View>

          <View style={styles.alertRow}>
            <AlertTriangle size={16} color="#DC2626" />
            <View style={{ flex: 1 }}>
              <Text style={styles.alertLabelRed}>Signo de Alerta (Suspender y Consultar):</Text>
              <Text style={styles.alertText}>
                Marcas rojas oscuras o moradas que persisten más de 45 minutos, ampollas, grietas o piel levantada. En este caso, retira el casco y avisa de inmediato.
              </Text>
            </View>
          </View>
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
  btnSos: {
    backgroundColor: '#16A34A',
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
    shadowColor: '#16A34A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  btnSosTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  btnSosSubtitle: {
    fontSize: 11,
    color: '#DCFCE7',
    marginTop: 1,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 16,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 14,
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  dayPillsRow: {
    flexDirection: 'row',
    gap: 6,
    marginBottom: 14,
  },
  dayPill: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 10,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  dayPillActive: {
    backgroundColor: '#0D9488',
    borderColor: '#0F766E',
  },
  dayPillText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#64748B',
  },
  dayPillTextActive: {
    color: '#FFFFFF',
  },
  dayDetails: {
    backgroundColor: '#F8FAFC',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  dayTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
    marginBottom: 8,
  },
  dayMetaGrid: {
    flexDirection: 'row',
    gap: 14,
    marginBottom: 8,
  },
  dayMetaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  dayMetaText: {
    fontSize: 12,
    color: '#334155',
    fontWeight: '600',
  },
  sleepBadge: {
    backgroundColor: '#E0F2FE',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    alignSelf: 'flex-start',
    marginBottom: 8,
  },
  sleepBadgeText: {
    fontSize: 11,
    color: '#0369A1',
    fontWeight: '700',
  },
  dayInstructions: {
    fontSize: 12,
    color: '#475569',
    lineHeight: 18,
  },
  hygieneStep: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  stepNum: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: '#E0F2FE',
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepNumText: {
    fontSize: 12,
    fontWeight: '800',
    color: '#0284C7',
  },
  stepTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F172A',
  },
  stepDesc: {
    fontSize: 12,
    color: '#64748B',
    lineHeight: 17,
    marginTop: 2,
  },
  alertRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 10,
    backgroundColor: '#F8FAFC',
    padding: 10,
    borderRadius: 10,
  },
  alertLabelGreen: {
    fontSize: 12,
    fontWeight: '700',
    color: '#15803D',
  },
  alertLabelRed: {
    fontSize: 12,
    fontWeight: '700',
    color: '#DC2626',
  },
  alertText: {
    fontSize: 11,
    color: '#475569',
    marginTop: 2,
    lineHeight: 16,
  },
});
