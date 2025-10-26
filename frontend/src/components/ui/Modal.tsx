'use client';

import FocusTrap from 'focus-trap-react';
import { AnimatePresence, motion } from 'framer-motion';
import type { HTMLAttributes, ReactNode } from 'react';
import { useCallback, useEffect, useId, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { MotionBox } from '@components/motion/MotionBox';
import { useMotionPreferences } from '@lib/motion';
import { durations, easings } from '@lib/motion/tokens';

export interface ModalProps extends Omit<HTMLAttributes<HTMLDivElement>, 'title'> {
  open: boolean;
  onClose: () => void;
  title?: ReactNode;
  description?: ReactNode;
  footer?: ReactNode;
}

export const Modal = ({
  open,
  onClose,
  title,
  description,
  footer,
  children,
  ...rest
}: ModalProps) => {
  const [mounted, setMounted] = useState(false);
  const { shouldReduceMotion } = useMotionPreferences();
  const headingId = useId();
  const descriptionId = useId();

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

  // Extract HTML event handlers to avoid conflict with Framer Motion
  const {
    onAnimationStart,
    onAnimationEnd,
    onAnimationIteration,
    onDragStart,
    onDragEnd,
    onDrag,
    ...htmlProps
  } = rest;

  if (!mounted) return null;

  const labelledBy = title ? headingId : undefined;
  const describedBy = description ? descriptionId : undefined;

  return createPortal(
    <AnimatePresence initial={false} mode="wait">
      {open && (
        <FocusTrap focusTrapOptions={{ allowOutsideClick: true }}>
          <div
            className="fixed inset-0 z-[var(--z-modal)] flex items-center justify-center px-6 py-10"
            role="presentation"
          >
            <motion.div
              className="absolute inset-0 bg-black/40 backdrop-blur-sm"
              onClick={onClose}
              {...overlayMotion}
            />
            <MotionBox
              preset="springy"
              className="relative z-10 w-full max-w-lg rounded-2xl bg-surface p-6 text-text shadow-strong"
              role="dialog"
              aria-modal="true"
              aria-labelledby={labelledBy}
              aria-describedby={describedBy}
              {...htmlProps}
            >
              {(title || description) && (
                <header className="space-y-2">
                  {title && (
                    <h2 id={headingId} className="text-xl font-semibold">
                      {title}
                    </h2>
                  )}
                  {description && (
                    <p id={descriptionId} className="text-sm text-text-muted">
                      {description}
                    </p>
                  )}
                </header>
              )}
              <div className="mt-4 space-y-4 text-sm leading-relaxed text-text-muted">{children}</div>
              {footer && <footer className="mt-6 flex justify-end gap-3">{footer}</footer>}
            </MotionBox>
          </div>
        </FocusTrap>
      )}
    </AnimatePresence>,
    document.body,
  );
};

export default Modal;
