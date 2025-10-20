'use client';

import clsx from 'clsx';
import type { HTMLAttributes, ReactNode } from 'react';
import { useMemo } from 'react';
import { MotionBox } from '@components/motion/MotionBox';
import { useMotionPreferences } from '@lib/motion';

export type CardVariant = 'surface' | 'elevated' | 'glass';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  heading?: ReactNode;
  description?: ReactNode;
  variant?: CardVariant;
  interactive?: boolean;
}

const variantClasses: Record<CardVariant, string> = {
  surface: 'bg-surface-alt/80 border border-border shadow-subtle',
  elevated: 'bg-white/90 dark:bg-surface-alt/90 border border-border shadow-medium',
  glass:
    'bg-white/40 dark:bg-white/10 border border-white/30 shadow-subtle backdrop-blur-md supports-[backdrop-filter]:backdrop-blur-xl',
};

export const Card = ({
  heading,
  description,
  children,
  variant = 'surface',
  interactive = false,
  className,
  ...rest
}: CardProps) => {
  const { shouldReduceMotion } = useMotionPreferences();

  const hoverProps = useMemo(
    () =>
      interactive && !shouldReduceMotion
        ? {
            whileHover: { translateY: -4, boxShadow: 'var(--shadow-medium)' },
            whileTap: { translateY: -1 },
          }
        : {},
    [interactive, shouldReduceMotion],
  );

  return (
    <MotionBox
      preset="rise"
      className={clsx(
        'group relative flex flex-col gap-3 rounded-xl p-6 transition-colors',
        variantClasses[variant],
        interactive && 'cursor-pointer',
        className,
      )}
      {...hoverProps}
      {...rest}
    >
      {(heading || description) && (
        <div className="space-y-1">
          {heading && <h3 className="text-base font-semibold text-text">{heading}</h3>}
          {description && <p className="text-sm text-text-muted">{description}</p>}
        </div>
      )}
      {children}
    </MotionBox>
  );
};

export default Card;
