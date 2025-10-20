import type { Transition, Variants } from 'framer-motion';
import { distances, durations, easings } from './tokens';

const defaultTransition: Transition = {
  duration: durations.m,
  ease: easings.standard,
};

export const fade: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: defaultTransition },
  exit: { opacity: 0, transition: { ...defaultTransition, duration: durations.s } },
};

export const rise: Variants = {
  hidden: { opacity: 0, y: distances.small },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      duration: durations.m,
      ease: easings.entrance,
    },
  },
  exit: {
    opacity: 0,
    y: distances.tiny,
    transition: { duration: durations.s, ease: easings.exit },
  },
};

export const scale = (initialScale = 0.96): Variants => ({
  hidden: { opacity: 0, scale: initialScale },
  show: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: durations.m,
      ease: easings.entrance,
    },
  },
  exit: {
    opacity: 0,
    scale: initialScale - 0.02,
    transition: { duration: durations.s, ease: easings.exit },
  },
});

type SlideDirection = 'up' | 'down' | 'left' | 'right';

export const slide = (
  direction: SlideDirection,
  distance: number = distances.small,
): Variants => {
  const axis = direction === 'left' || direction === 'right' ? 'x' : 'y';
  const multiplier = direction === 'left' || direction === 'up' ? -1 : 1;

  return {
    hidden: {
      opacity: 0,
      [axis]: multiplier * distance,
    },
    show: {
      opacity: 1,
      [axis]: 0,
      transition: {
        duration: durations.m,
        ease: easings.entrance,
      },
    },
    exit: {
      opacity: 0,
      [axis]: multiplier * (distance / 2),
      transition: { duration: durations.s, ease: easings.exit },
    },
  } as Variants;
};

export const staggerContainer = (
  stagger = 0.08,
  delayChildren = 0.04,
): Variants => ({
  hidden: {},
  show: {
    transition: {
      staggerChildren: stagger,
      delayChildren,
    },
  },
});

export const springyEnter: Variants = {
  hidden: { opacity: 0, scale: 0.92, y: distances.tiny },
  show: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      type: 'spring',
      stiffness: easings.spring.stiffness,
      damping: easings.spring.damping,
      mass: easings.spring.mass,
    },
  },
  exit: {
    opacity: 0,
    scale: 0.96,
    y: distances.micro,
    transition: { duration: durations.s, ease: easings.exit },
  },
};
