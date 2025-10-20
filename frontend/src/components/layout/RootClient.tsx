'use client';

import { AnimatePresence, motion } from 'framer-motion';
import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';
import { useEffect, useMemo, useState } from 'react';
import Header from '@components/ui/Header';
import { durations, easings, distances } from '@lib/motion/tokens';

const routeVariants = {
  hidden: { opacity: 0, y: distances.medium },
  enter: {
    opacity: 1,
    y: 0,
    transition: {
      duration: durations.m,
      ease: easings.entrance,
    },
  },
  exit: {
    opacity: 0,
    y: -distances.tiny,
    transition: {
      duration: durations.s,
      ease: easings.exit,
    },
  },
};

export interface RootClientProps {
  children: ReactNode;
}

export const RootClient = ({ children }: RootClientProps) => {
  const pathname = usePathname();
  const [instant, setInstant] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const entries = performance.getEntriesByType('navigation') as PerformanceNavigationTiming[];
    const latest = entries.at(-1);
    if (latest?.type === 'back_forward') {
      setInstant(true);
    } else {
      setInstant(false);
    }
  }, [pathname]);

  const motionProps = useMemo(
    () =>
      instant
        ? { initial: false, animate: 'enter', exit: undefined, transition: { duration: 0 } }
        : { initial: 'hidden', animate: 'enter', exit: 'exit' },
    [instant],
  );

  return (
    <div className="relative flex min-h-screen flex-col">
      <Header />
      <AnimatePresence mode="wait" initial={false}>
        <motion.main
          key={pathname}
          variants={routeVariants}
          {...motionProps}
          className="relative flex-1"
        >
          {children}
        </motion.main>
      </AnimatePresence>
    </div>
  );
};

export default RootClient;
