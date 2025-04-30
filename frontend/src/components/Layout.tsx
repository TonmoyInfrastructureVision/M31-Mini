import React, { ReactNode } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import clsx from 'clsx';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import * as Avatar from '@radix-ui/react-avatar';
import * as Tooltip from '@radix-ui/react-tooltip';
import { Theme } from '@radix-ui/themes';
import { themeConfig } from '../styles/theme';

interface LayoutProps {
  children: ReactNode;
  title?: string;
}

export default function Layout({ children, title = 'M31-Mini' }: LayoutProps): React.ReactElement {
  const router = useRouter();
  
  const navLinks = [
    { href: '/dashboard', label: 'Dashboard', icon: '📊', matchExact: true },
    { href: '/agents', label: 'Agents', icon: '🤖' },
    { href: '/tasks', label: 'Tasks', icon: '📋' },
  ];
  
  const isActiveLink = (href: string, matchExact = false): boolean => {
    if (matchExact) {
      return router.pathname === href;
    }
    return router.pathname.startsWith(href);
  };

  return (
    <Theme accentColor={themeConfig.accentColor} grayColor={themeConfig.grayColor} radius={themeConfig.radius} scaling={themeConfig.scaling}>
      <Tooltip.Provider>
        <div className="min-h-screen bg-gray-50 flex flex-col">
          <Head>
            <title>{title} | M31-Mini Agent Framework</title>
            <meta name="description" content="M31-Mini Autonomous Agent Framework" />
            <link rel="icon" href="/favicon.ico" />
          </Head>
          
          <header className="bg-white shadow-sm border-b border-slate-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex items-center">
                  <div className="flex-shrink-0 flex items-center">
                    <Link href="/dashboard" className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-purple-600">
                      M31-Mini
                    </Link>
                  </div>
                  <nav className="ml-8 flex space-x-6">
                    {navLinks.map((link) => (
                      <Tooltip.Root key={link.href}>
                        <Tooltip.Trigger asChild>
                          <Link
                            href={link.href}
                            className={clsx(
                              'inline-flex items-center px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ease-in-out',
                              isActiveLink(link.href, link.matchExact)
                                ? 'bg-indigo-50 text-indigo-700 border-indigo-500'
                                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                            )}
                          >
                            <span className="mr-2">{link.icon}</span>
                            {link.label}
                          </Link>
                        </Tooltip.Trigger>
                        <Tooltip.Portal>
                          <Tooltip.Content className="bg-slate-900 text-white px-3 py-1 rounded text-xs" sideOffset={5}>
                            {link.label}
                            <Tooltip.Arrow className="fill-slate-900" />
                          </Tooltip.Content>
                        </Tooltip.Portal>
                      </Tooltip.Root>
                    ))}
                  </nav>
                </div>
                
                <div className="flex items-center">
                  <DropdownMenu.Root>
                    <DropdownMenu.Trigger asChild>
                      <button className="flex items-center space-x-2 bg-gray-50 p-1.5 rounded-full hover:bg-gray-100 transition-colors">
                        <Avatar.Root className="bg-slate-800 inline-flex h-8 w-8 select-none items-center justify-center overflow-hidden rounded-full align-middle">
                          <Avatar.Fallback className="text-white text-sm leading-none font-medium">M31</Avatar.Fallback>
                        </Avatar.Root>
                      </button>
                    </DropdownMenu.Trigger>
                    <DropdownMenu.Portal>
                      <DropdownMenu.Content className="bg-white rounded-lg shadow-lg p-2 min-w-[200px] border border-slate-200" sideOffset={5}>
                        <DropdownMenu.Item className="text-sm px-2 py-1.5 outline-none cursor-pointer rounded hover:bg-slate-100">
                          Settings
                        </DropdownMenu.Item>
                        <DropdownMenu.Item className="text-sm px-2 py-1.5 outline-none cursor-pointer rounded hover:bg-slate-100">
                          Help & Support
                        </DropdownMenu.Item>
                        <DropdownMenu.Separator className="h-px bg-slate-200 my-1" />
                        <DropdownMenu.Item className="text-sm px-2 py-1.5 outline-none cursor-pointer rounded hover:bg-red-50 text-red-600">
                          Sign Out
                        </DropdownMenu.Item>
                      </DropdownMenu.Content>
                    </DropdownMenu.Portal>
                  </DropdownMenu.Root>
                </div>
              </div>
            </div>
          </header>
          
          <main className="flex-grow">
            <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
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
      </Tooltip.Provider>
    </Theme>
  );
} 