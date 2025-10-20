'use client';

import clsx from 'clsx';
import FocusTrap from 'focus-trap-react';
import { AnimatePresence, motion } from 'framer-motion';
import type { HTMLAttributes, ReactNode } from 'react';
import { useCallback, useEffect, useId, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { useMotionPreferences } from '@lib/motion';
import { durations, easings } from '@lib/motion/tokens';

export type DrawerSide = 'left' | 'right';

export interface DrawerProps extends HTMLAttributes<HTMLDivElement> {
  open: boolean;
  onClose: () => void;
  side?: DrawerSide;
  title?: ReactNode;
}

export const Drawer = ({
  open,
  onClose,
  side = 'right',
  title,
  children,
  ...rest
}: DrawerProps) => {
  const { shouldReduceMotion } = useMotionPreferences();
  const [mounted, setMounted] = useState(false);
  const headingId = useId();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!open) return;
    const original = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = original;
    };
  }, [open]);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    },
    [onClose],
  );

  useEffect(() => {
    if (!open) return;
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown, open]);

  const panelMotion = useMemo(() => {
    if (shouldReduceMotion) {
      return {
        initial: false,
        animate: { x: 0 },
      };
    }
    return {
      initial: { x: side === 'left' ? '-100%' : '100%' },
      animate: { x: 0 },
      exit: { x: side === 'left' ? '-100%' : '100%' },
      transition: {
        type: 'spring',
        stiffness: 210,
        damping: 26,
      },
    };
  }, [shouldReduceMotion, side]);

  const overlayMotion = useMemo(
    () =>
      shouldReduceMotion
        ? {}
        : {
            initial: { opacity: 0 },
            animate: { opacity: 1 },
            exit: { opacity: 0 },
            transition: { duration: durations.m, ease: easings.standard },
          },
    [shouldReduceMotion],
  );

  if (!mounted) return null;

  const labelledBy = typeof title === 'string' ? headingId : undefined;

  return createPortal(
    <AnimatePresence initial={false} mode="wait">
      {open && (
        <FocusTrap focusTrapOptions={{ allowOutsideClick: true }}>
          <div className="fixed inset-0 z-[var(--z-modal)]" role="presentation">
            <motion.div
              className="absolute inset-0 bg-black/30"
              onClick={onClose}
              {...overlayMotion}
            />
            <motion.aside
              className={clsx(
                'absolute top-0 flex h-full w-full max-w-sm flex-col gap-4 bg-surface p-6 text-text shadow-strong',
                side === 'left' ? 'left-0' : 'right-0',
              )}
              role="dialog"
              aria-modal="true"
              aria-labelledby={labelledBy}
              {...panelMotion}
              {...rest}
            >
              {title && (
                <h2 id={headingId} className="text-lg font-semibold">
                  {title}
                </h2>
              )}
              <div className="flex-1 overflow-y-auto text-sm text-text-muted">{children}</div>
            </motion.aside>
          </div>
        </FocusTrap>
      )}
    </AnimatePresence>,
    document.body,
  );
};

export default Drawer;
