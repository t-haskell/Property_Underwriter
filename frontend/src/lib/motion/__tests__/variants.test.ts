import { describe, expect, it } from 'vitest';
import { fade, rise, scale, slide, springyEnter, staggerContainer } from '../variants';

const snapshot = (value: unknown) => expect(value).toMatchSnapshot();

describe('motion variants', () => {
  it('matches expected fade blueprint', () => {
    snapshot(fade);
  });

  it('matches expected rise blueprint', () => {
    snapshot(rise);
  });

  it('provides slide variants per direction', () => {
    snapshot(slide('up', 16));
    snapshot(slide('right', 20));
  });

  it('creates springy entrance variant', () => {
    snapshot(springyEnter);
  });

  it('stagger container scales with delay', () => {
    snapshot(staggerContainer(0.08, 0.12));
  });

  it('scale variant respects provided factor', () => {
    snapshot(scale(0.9));
  });
});
