import { describe, expect, it } from 'vitest';
import { distances, durations, easings } from '../tokens';

describe('motion tokens', () => {
  it('exposes duration tokens in ascending order', () => {
    expect(durations.xs).toBeLessThan(durations.s);
    expect(durations.s).toBeLessThan(durations.m);
    expect(durations.m).toBeLessThan(durations.l);
  });

  it('provides easing curves within expected range', () => {
    expect(easings.standard).toHaveLength(4);
    expect(easings.entrance[0]).toBeLessThan(1);
    expect(easings.exit[2]).toBeGreaterThan(0.9);
    expect(easings.spring.stiffness).toBeGreaterThanOrEqual(140);
    expect(easings.spring.damping).toBeGreaterThanOrEqual(18);
  });

  it('defines motion distances for typical UI affordances', () => {
    expect(distances.micro).toBeLessThan(distances.tiny);
    expect(distances.medium).toBeGreaterThan(distances.small);
  });
});
