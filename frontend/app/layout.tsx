import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import '../styles/globals.css';
import RootClient from '@components/layout/RootClient';

export const metadata: Metadata = {
  title: 'Property Underwriter',
  description: 'Calm, intentional underwriting intelligence.',
  viewport: {
    width: 'device-width',
    initialScale: 1,
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <RootClient>{children}</RootClient>
      </body>
    </html>
  );
}
