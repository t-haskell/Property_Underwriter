import { renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useMotionPreferences, useStagger } from '../hooks';

const createMatchMedia = () => {
  let listeners: Array<(event: MediaQueryListEvent) => void> = [];
  const createQuery = (matches: boolean) => {
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
    matchMedia: vi.fn((query: string) => {
      if (query.includes('prefers-reduced-motion')) {
        return createQuery(true);
      }
      return createQuery(false);
    }),
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
