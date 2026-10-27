import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity, Text, Platform } from 'react-native';
import { useAuth } from '../context/AuthContext';
import AuthScreen from '../screens/AuthScreen';
import HomeScreen from '../screens/HomeScreen';
import EvolutionScreen from '../screens/EvolutionScreen';
import AppointmentsScreen from '../screens/AppointmentsScreen';
import DocumentsScreen from '../screens/DocumentsScreen';
import GuideScreen from '../screens/GuideScreen';
import { Home, TrendingDown, Calendar, FileText, BookOpen } from 'lucide-react-native';

type TabKey = 'home' | 'evolution' | 'appointments' | 'documents' | 'guide';

export default function NavigationRoot() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<TabKey>('home');

  if (!user) {
    return <AuthScreen />;
  }

  const renderActiveScreen = () => {
    switch (activeTab) {
      case 'home':
        return <HomeScreen />;
      case 'evolution':
        return <EvolutionScreen />;
      case 'appointments':
        return <AppointmentsScreen />;
      case 'documents':
        return <DocumentsScreen />;
      case 'guide':
        return <GuideScreen />;
      default:
        return <HomeScreen />;
    }
  };

  const tabs: Array<{ key: TabKey; label: string; icon: any }> = [
    { key: 'home', label: 'Inicio', icon: Home },
    { key: 'evolution', label: 'Evolución', icon: TrendingDown },
    { key: 'appointments', label: 'Citas', icon: Calendar },
    { key: 'documents', label: 'Documentos', icon: FileText },
    { key: 'guide', label: 'Guía', icon: BookOpen },
  ];

  return (
    <View style={styles.container}>
      <View style={styles.screenContainer}>{renderActiveScreen()}</View>

      {/* Bottom Clinical Tab Bar */}
      <View style={styles.bottomBar}>
        {tabs.map((t) => {
          const Icon = t.icon;
          const isActive = activeTab === t.key;
          return (
            <TouchableOpacity
              key={t.key}
              style={[styles.tabItem, isActive && styles.tabItemActive]}
              onPress={() => setActiveTab(t.key)}
            >
              <Icon size={20} color={isActive ? '#0D9488' : '#64748B'} />
              <Text style={[styles.tabLabel, isActive && styles.tabLabelActive]}>
                {t.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  screenContainer: {
    flex: 1,
  },
  bottomBar: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
    paddingVertical: 8,
    paddingBottom: Platform.OS === 'ios' ? 24 : 10,
    paddingHorizontal: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 8,
    maxWidth: 600,
    width: '100%',
    alignSelf: 'center',
  },
  tabItem: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 4,
    borderRadius: 10,
  },
  tabItemActive: {
    backgroundColor: '#F0FDFA',
  },
  tabLabel: {
    fontSize: 10,
    color: '#64748B',
    marginTop: 3,
    fontWeight: '600',
  },
  tabLabelActive: {
    color: '#0D9488',
    fontWeight: '800',
  },
});
