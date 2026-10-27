import '@/global.css';
import { Platform } from 'react-native';

export const Colors = {
  light: {
    text: '#0F172A', // Slate 900
    textSecondary: '#64748B', // Slate 500
    textMuted: '#94A3B8', // Slate 400
    background: '#F8FAFC', // Slate 50
    surface: '#FFFFFF', // Pure White
    backgroundElement: '#F1F5F9', // Slate 100
    backgroundSelected: '#E2E8F0', // Slate 200
    border: '#E2E8F0', // Slate 200
    borderLight: '#F1F5F9',

    // CraniumFit Brand Clinical Palette
    primary: '#0D9488', // Teal 600
    primaryDark: '#0F766E', // Teal 700
    primaryLight: '#CCFBF1', // Teal 100
    primarySurface: '#F0FDFA', // Teal 50

    accent: '#0284C7', // Sky 600
    accentLight: '#E0F2FE', // Sky 100
    accentSurface: '#F0F9FF', // Sky 50

    success: '#10B981', // Emerald 500
    successLight: '#D1FAE5', // Emerald 100
    successSurface: '#ECFDF5',

    warning: '#F59E0B', // Amber 500
    warningLight: '#FEF3C7', // Amber 100
    warningSurface: '#FFFBEB',

    danger: '#EF4444', // Red 500
    dangerLight: '#FEE2E2', // Red 100
    dangerSurface: '#FEF2F2',
  },
  dark: {
    text: '#F8FAFC',
    textSecondary: '#94A3B8',
    textMuted: '#64748B',
    background: '#0F172A',
    surface: '#1E293B',
    backgroundElement: '#334155',
    backgroundSelected: '#475569',
    border: '#334155',
    borderLight: '#1E293B',

    primary: '#14B8A6',
    primaryDark: '#0D9488',
    primaryLight: '#134E4A',
    primarySurface: '#042F2E',

    accent: '#38BDF8',
    accentLight: '#075985',
    accentSurface: '#0C4A6E',

    success: '#34D399',
    successLight: '#065F46',
    successSurface: '#064E3B',

    warning: '#FBBF24',
    warningLight: '#78350F',
    warningSurface: '#451A03',

    danger: '#F87171',
    dangerLight: '#7F1D1D',
    dangerSurface: '#450A0A',
  },
} as const;

export type ThemeColor = keyof typeof Colors.light;

export const Fonts = Platform.select({
  ios: {
    sans: 'system-ui',
    serif: 'ui-serif',
    rounded: 'ui-rounded',
    mono: 'ui-monospace',
  },
  default: {
    sans: 'normal',
    serif: 'serif',
    rounded: 'normal',
    mono: 'monospace',
  },
  web: {
    sans: 'Inter, system-ui, -apple-system, sans-serif',
    serif: 'Georgia, serif',
    rounded: 'system-ui',
    mono: 'monospace',
  },
});

export const Spacing = {
  half: 2,
  one: 4,
  two: 8,
  three: 16,
  four: 24,
  five: 32,
  six: 48,
  seven: 64,
} as const;

export const BottomTabInset = Platform.select({ ios: 60, android: 75 }) ?? 60;
export const MaxContentWidth = 720;
