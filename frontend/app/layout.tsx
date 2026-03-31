'use client';

import { Inter } from 'next/font/google';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode } from 'react';
import { ThemeProvider, useTheme } from '@/lib/theme';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

// Navigation items
const navItems = [
  { href: '/', label: 'Dashboard', icon: '📊' },
  { href: '/elections', label: 'Elections', icon: '🗳️' },
  { href: '/results', label: 'Results', icon: '📋' },
  { href: '/aggregation', label: 'Aggregation', icon: '📈' },
];

function Navigation() {
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();

  return (
    <nav className="bg-card border-b border-border">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link href="/" className="flex items-center space-x-2">
              <span className="text-2xl">🇳🇬</span>
              <span className="font-bold text-lg text-foreground">INEC Results</span>
            </Link>
            <div className="hidden md:flex items-center space-x-4">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    pathname === item.href
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  }`}
                >
                  <span>{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              ))}
            </div>
          </div>
          <button
            onClick={toggleTheme}
            className="p-2 rounded-md hover:bg-accent transition-colors"
            aria-label="Toggle theme"
          >
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
        </div>
      </div>
    </nav>
  );
}

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <title>INEC Election Results Dashboard</title>
        <meta name="description" content="AI-powered election results extraction and aggregation system" />
      </head>
      <body className={inter.className}>
        <ThemeProvider>
          <div className="min-h-screen bg-background">
            <Navigation />
            {children}
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
