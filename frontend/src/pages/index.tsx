import type { ReactElement } from 'react';
import { useRouter } from 'next/router';
import { useEffect } from 'react';

export default function Home(): ReactElement | null {
  const router = useRouter();
  
  useEffect(() => {
    router.replace('/dashboard');
  }, [router]);
  
  return null;
} 