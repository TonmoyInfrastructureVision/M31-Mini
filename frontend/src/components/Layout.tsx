import React, { ReactNode } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import clsx from 'clsx';

interface LayoutProps {
  children: ReactNode;
  title?: string;
}

export default function Layout({ children, title = 'M31-Mini' }: LayoutProps) {
  const router = useRouter();
  
  const navLinks = [
    { href: '/', label: 'Dashboard', matchExact: true },
    { href: '/dashboard', label: 'Monitoring', matchExact: true },
    { href: '/agents', label: 'Agents' },
    { href: '/tasks', label: 'Tasks' },
  ];
  
  const isActiveLink = (href: string, matchExact = false) => {
    if (matchExact) {
      return router.pathname === href;
    }
    return router.pathname.startsWith(href);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Head>
        <title>{title} | M31-Mini Agent Framework</title>
        <meta name="description" content="M31-Mini Autonomous Agent Framework" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <Link href="/" className="text-2xl font-bold text-primary-600">
                  M31-Mini
                </Link>
              </div>
              <nav className="ml-8 flex space-x-8">
                {navLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={clsx(
                      'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium',
                      isActiveLink(link.href, link.matchExact)
                        ? 'border-primary-500 text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    )}
                  >
                    {link.label}
                  </Link>
                ))}
              </nav>
            </div>
          </div>
        </div>
      </header>
      
      <main className="flex-grow">
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
      
      <footer className="bg-white border-t border-gray-200 py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            M31-Mini Autonomous Agent Framework &copy; {new Date().getFullYear()}
          </p>
        </div>
      </footer>
    </div>
  );
} 