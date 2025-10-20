'use client';

import clsx from 'clsx';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, useMotionValueEvent, useScroll, useTransform } from 'framer-motion';
import type { ReactNode } from 'react';
import { useMemo, useState } from 'react';
import BackgroundLayer from '@components/visuals/BackgroundLayer';
import { useMotionPreferences } from '@lib/motion';

export interface HeaderLink {
  href: string;
  label: string;
}

export interface HeaderProps {
  links?: HeaderLink[];
  actions?: ReactNode;
  className?: string;
}

export const Header = ({
  links = [
    { href: '/', label: 'Home' },
    { href: '/examples/motion', label: 'Motion' },
  ],
  actions,
  className,
}: HeaderProps) => {
  const pathname = usePathname();
  const { shouldReduceMotion } = useMotionPreferences();
  const { scrollY } = useScroll();
  const tilt = useTransform(scrollY, [0, 400], [0, -2]);
  const offset = useTransform(scrollY, [0, 400], [0, -24]);
  const [elevated, setElevated] = useState(false);

  useMotionValueEvent(scrollY, 'change', (latest) => {
    setElevated(latest > 16);
  });

  const linkClass = useMemo(
    () =>
      clsx(
        'relative inline-flex items-center text-sm font-medium transition-colors text-text/80 hover:text-text focus-visible:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 rounded-md px-2 py-1',
        'after:absolute after:inset-x-1 after:bottom-0 after:h-0.5 after:origin-left after:scale-x-0 after:rounded-full after:bg-primary after:transition-transform after:duration-300 after:ease-entrance hover:after:scale-x-100 focus-visible:after:scale-x-100',
      ),
    [],
  );

  return (
    <motion.header
      className={clsx(
        'sticky top-0 z-[var(--z-header)] w-full overflow-hidden bg-surface/80 backdrop-blur-md transition-shadow',
        elevated ? 'shadow-subtle' : 'shadow-none',
        className,
      )}
      style={shouldReduceMotion ? undefined : { perspective: 1200, rotateX: tilt }}
    >
      <div className="absolute inset-0">
        <BackgroundLayer intensity={0.7} speed={0.4} grain={0.08} variant="glass" disableShader />
      </div>
      <motion.div
        className="relative mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-4"
        style={shouldReduceMotion ? undefined : { y: offset }}
      >
        <div className="flex items-center gap-3">
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-primary/15 text-primary">
            PU
          </span>
          <div className="flex flex-col">
            <span className="text-sm font-semibold text-text">Property Underwriter</span>
            <span className="text-xs text-text-muted">Calm intelligence for property risk</span>
          </div>
        </div>
        <nav className="flex items-center gap-4">
          {links.map((link) => {
            const active = pathname === link.href;
            return (
              <Link key={link.href} href={link.href} className={linkClass} data-active={active}>
                <span
                  className={clsx(
                    'transition-colors',
                    active ? 'text-text after:scale-x-100' : '',
                  )}
                >
                  {link.label}
                </span>
              </Link>
            );
          })}
        </nav>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </motion.div>
    </motion.header>
  );
};

export default Header;
