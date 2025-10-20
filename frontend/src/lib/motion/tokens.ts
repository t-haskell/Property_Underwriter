export const durations = {
  xs: 0.12,
  s: 0.2,
  m: 0.36,
  l: 0.6,
} as const;

export const easings = {
  standard: [0.2, 0, 0, 1] as const,
  entrance: [0.16, 1, 0.3, 1] as const,
  exit: [0.4, 0, 1, 1] as const,
  spring: {
    stiffness: 180,
    damping: 24,
    mass: 1,
  },
} as const;

export const distances = {
  micro: 4,
  tiny: 8,
  small: 16,
  medium: 24,
  large: 40,
} as const;

export type MotionDurations = typeof durations;
export type MotionEasings = typeof easings;
export type MotionDistances = typeof distances;
