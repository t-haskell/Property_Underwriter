'use client';

import clsx from 'clsx';
import { motion } from 'framer-motion';
import type { HTMLMotionProps, Variants } from 'framer-motion';
import { forwardRef, useMemo } from 'react';
import { fade, rise, scale, slide, springyEnter } from '@lib/motion';
import { useMotionPreferences } from '@lib/motion/hooks';

export type MotionPreset =
  | 'fade'
  | 'rise'
  | 'scale'
  | 'slideUp'
  | 'slideDown'
  | 'slideLeft'
  | 'slideRight'
  | 'springy';

export interface MotionBoxProps extends HTMLMotionProps<'div'> {
  preset?: MotionPreset;
  distance?: number;
  className?: string;
}

const variantsForPreset = (preset: MotionPreset, distance?: number): Variants => {
  switch (preset) {
    case 'rise':
      return rise;
    case 'scale':
      return scale();
    case 'slideUp':
      return slide('up', distance);
    case 'slideDown':
      return slide('down', distance);
    case 'slideLeft':
      return slide('left', distance);
    case 'slideRight':
      return slide('right', distance);
    case 'springy':
      return springyEnter;
    case 'fade':
    default:
      return fade;
  }
};

export const MotionBox = forwardRef<HTMLDivElement, MotionBoxProps>(
  ({ preset = 'fade', distance, className, style, initial = 'hidden', animate = 'show', exit = 'exit', ...rest }, ref) => {
    const { shouldReduceMotion } = useMotionPreferences();

    const variants = useMemo(() => variantsForPreset(preset, distance), [distance, preset]);

    const resolvedInitial = shouldReduceMotion ? false : initial;
    const resolvedAnimate = shouldReduceMotion ? undefined : animate;
    const motionStyle = shouldReduceMotion
      ? style
      : {
          ...style,
          willChange: style?.willChange ?? 'transform, opacity',
        };

    return (
      <motion.div
        ref={ref}
        className={clsx('motion-box', className)}
        variants={variants}
        initial={resolvedInitial}
        animate={resolvedAnimate}
        exit={shouldReduceMotion ? undefined : exit}
        style={motionStyle}
        {...rest}
      />
    );
  },
);

MotionBox.displayName = 'MotionBox';

export default MotionBox;
