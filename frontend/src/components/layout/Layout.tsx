/**
 * Axiom Lens - Layout wrapper component.
 */
import { ReactNode } from 'react';
import { Navbar } from './Navbar';
import { clsx } from 'clsx';

interface LayoutProps {
  children: ReactNode;
  className?: string;
}

export function Layout({ children, className }: LayoutProps) {
  return (
    <div className={clsx('min-h-screen bg-gray-50', className)}>
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>
      <footer className="border-t border-gray-200 bg-white">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-gray-500">
          <p>Axiom Lens — AI-assisted Reverse Engineering Analysis Platform</p>
          <p className="mt-1">© 2024 Alan Vo. MIT License.</p>
        </div>
      </footer>
    </div>
  );
}