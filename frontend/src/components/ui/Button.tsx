'use client';

import clsx from 'clsx';
import { motion } from 'framer-motion';
import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { forwardRef, useMemo } from 'react';
import { useMotionPreferences } from '@lib/motion';
import { durations, easings } from '@lib/motion/tokens';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost';
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  fullWidth?: boolean;
  icon?: ReactNode;
}

const baseClasses =
  'relative inline-flex items-center justify-center gap-2 rounded-md border px-4 py-2 font-medium text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-60';

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'bg-primary text-white border-transparent shadow-subtle hover:bg-primary/90 dark:hover:bg-primary/80',
  secondary:
    'bg-surface-alt text-text border-border hover:border-primary hover:text-primary',
  ghost:
    'border-transparent bg-transparent text-text hover:bg-primary/10 dark:hover:bg-primary/20',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', fullWidth, icon, children, className, disabled, ...rest }, ref) => {
    const { shouldReduceMotion } = useMotionPreferences();

    const motionProps = useMemo(
      () =>
        shouldReduceMotion
          ? {}
          : {
              whileHover: { translateY: -2, boxShadow: 'var(--shadow-medium)' },
              whileTap: { scale: 0.98, boxShadow: 'var(--shadow-subtle)' },
              transition: { duration: durations.s, ease: easings.entrance },
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

    return (
      <motion.button
        ref={ref}
        type="button"
        className={clsx(baseClasses, variantClasses[variant], fullWidth && 'w-full', className)}
        disabled={disabled}
        style={{ willChange: shouldReduceMotion ? undefined : 'transform' }}
        {...motionProps}
        {...htmlProps}
      >
        {icon && <span aria-hidden className="inline-flex h-4 w-4 items-center justify-center">{icon}</span>}
        <span>{children}</span>
      </motion.button>
    );
  },
);

Button.displayName = 'Button';

export default Button;
