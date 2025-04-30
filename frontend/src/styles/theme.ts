import { Theme } from '@radix-ui/themes';

export const themeConfig = {
  accentColor: 'indigo' as const,
  grayColor: 'slate' as const,
  radius: 'medium' as const,
  scaling: '95%' as const,
};

export type AppThemeConfig = typeof themeConfig; 