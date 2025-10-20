import { renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useMotionPreferences, useStagger } from '../hooks';

type MediaQueryMatches = Record<string, boolean>;

const defaultMatches: MediaQueryMatches = {
  '(prefers-reduced-motion: reduce)': true,
  '(prefers-contrast: more)': false,
  '(forced-colors: active)': false,
};

const createMatchMedia = (overrides: MediaQueryMatches = {}) => {
  let listeners: Array<(event: MediaQueryListEvent) => void> = [];
  const matchesByQuery = { ...defaultMatches, ...overrides };

  const createQuery = (query: string) => {
    const matches = Boolean(matchesByQuery[query]);
    return {
      matches,
      media: '',
      addEventListener: vi.fn((_, handler: (event: MediaQueryListEvent) => void) => {
        listeners.push(handler);
      }),
      removeEventListener: vi.fn((_, handler: (event: MediaQueryListEvent) => void) => {
        listeners = listeners.filter((listener) => listener !== handler);
      }),
      dispatch: (matchesValue: boolean) => {
        listeners.forEach((listener) =>
          listener({ matches: matchesValue } as MediaQueryListEvent),
        );
      },
    } as MediaQueryList;
  };

  return {
    matchMedia: vi.fn((query: string) => createQuery(query)),
  };
};

describe('useMotionPreferences', () => {
  beforeEach(() => {
    delete document.documentElement.dataset.reducedMotion;
  });

  it('detects reduced motion preference', () => {
    const { matchMedia } = createMatchMedia();
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: matchMedia,
    });

    const { result } = renderHook(() => useMotionPreferences());
    expect(result.current.reducedMotion).toBe(true);
    expect(result.current.shouldReduceMotion).toBe(true);
  });

  it('preserves reduced motion attribute until last consumer unmounts', () => {
    const { matchMedia } = createMatchMedia();
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: matchMedia,
    });

    const first = renderHook(() => useMotionPreferences());
    const second = renderHook(() => useMotionPreferences());

    expect(document.documentElement.dataset.reducedMotion).toBe('true');

    first.unmount();
    expect(document.documentElement.dataset.reducedMotion).toBe('true');

    second.unmount();
    expect(document.documentElement.dataset.reducedMotion).toBeUndefined();
  });

  it('keeps reduced motion attribute when forced colors imply reduced motion', () => {
    const { matchMedia } = createMatchMedia({
      '(prefers-reduced-motion: reduce)': false,
      '(forced-colors: active)': true,
    });
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: matchMedia,
    });

    const { result } = renderHook(() => useMotionPreferences());

    expect(result.current.reducedMotion).toBe(false);
    expect(result.current.forcedColors).toBe(true);
    expect(result.current.shouldReduceMotion).toBe(true);
    expect(document.documentElement.dataset.reducedMotion).toBe('true');
  });
});

describe('useStagger', () => {
  it('returns stagger variants proportional to child count', () => {
    const { result, rerender } = renderHook(({ count }) => useStagger(count, 0.1), {
      initialProps: { count: 3 },
    });

    expect(result.current.show?.transition?.staggerChildren).toBeCloseTo(0.1);
    expect(result.current.show?.transition?.delayChildren).toBeGreaterThan(0);

    rerender({ count: 10 });
    expect(result.current.show?.transition?.delayChildren).toBeLessThanOrEqual(0.6);
  });
});
