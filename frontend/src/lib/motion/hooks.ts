import { useEffect, useMemo, useSyncExternalStore } from 'react';
import type { Variants } from 'framer-motion';
import { staggerContainer } from './variants';

const isBrowser = () => typeof window !== 'undefined';

const subscribe = (query: string, callback: () => void) => {
  if (!isBrowser() || typeof window.matchMedia !== 'function') {
    return () => undefined;
  }
  const mql = window.matchMedia(query);
  mql.addEventListener('change', callback);
  return () => mql.removeEventListener('change', callback);
};

const getSnapshot = (query: string) => () => {
  if (!isBrowser() || typeof window.matchMedia !== 'function') {
    return false;
  }
  return window.matchMedia(query).matches;
};

const getServerSnapshot = () => false;

let motionPreferenceConsumers = 0;

const useMediaQuery = (query: string) =>
  useSyncExternalStore(
    (listener) => subscribe(query, listener),
    getSnapshot(query),
    getServerSnapshot,
  );

export const useMotionPreferences = () => {
  const reducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');
  const prefersContrast = useMediaQuery('(prefers-contrast: more)');
  const forcedColors = useMediaQuery('(forced-colors: active)');

  useEffect(() => {
    if (!isBrowser()) return;
    const attrValue = reducedMotion ? 'true' : 'false';
    document.documentElement.dataset.reducedMotion = attrValue;
  }, [reducedMotion]);

  useEffect(() => {
    if (!isBrowser()) return;
    motionPreferenceConsumers += 1;

    return () => {
      motionPreferenceConsumers = Math.max(0, motionPreferenceConsumers - 1);
      if (motionPreferenceConsumers === 0) {
        delete document.documentElement.dataset.reducedMotion;
      }
    };
  }, []);

  return {
    reducedMotion,
    prefersContrast,
    forcedColors,
    shouldReduceMotion: reducedMotion || forcedColors,
  } as const;
};

export const useStagger = (
  childrenCount: number,
  delayBase = 0.08,
): Variants =>
  useMemo(() => {
    const cappedDelay = Math.min(delayBase, 0.14);
    const delayChildren = Math.min(childrenCount * cappedDelay * 0.25, 0.6);
    return staggerContainer(cappedDelay, delayChildren);
  }, [childrenCount, delayBase]);
