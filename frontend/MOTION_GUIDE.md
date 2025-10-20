# Motion & Visual Systems Guide

## Principles
- **Calm and intentional** – Prefer gentle easing, limited overshoot, and short distances (16–24px) to keep focus on underwriting data.
- **Responsive to context** – Respect `prefers-reduced-motion`, high-contrast modes, and bfcache restores to avoid jarring transitions.
- **Composable** – Build animations through shared tokens (`durations`, `easings`, `distances`) and variants so components stay consistent.
- **Performant** – Animate transforms/opacity only, throttle background work on low-power devices, and guard GPU work with capability checks.

## Tokens & Utilities
- `src/lib/motion/tokens.ts` – Duration (`xs–l`), easing curves (`standard`, `entrance`, `exit`, spring config), and travel distances.
- `src/lib/motion/variants.ts` – Reusable Framer Motion blueprints: `fade`, `rise`, `scale`, directional `slide`, `springyEnter`, and `staggerContainer`.
- `src/lib/motion/hooks.ts` –
  - `useMotionPreferences()` exposes `reducedMotion`, `prefersContrast`, `forcedColors`, and `shouldReduceMotion` and syncs the `data-reduced-motion` attribute.
  - `useStagger(count, delayBase)` composes container variants with capped stagger timing.
- `src/components/motion/MotionBox.tsx` – A typed wrapper around `motion.div` with preset selection, reduced-motion handling, and transform safety.

## Background System
- `src/components/visuals/BackgroundLayer.tsx` – Animated gradient + optional noise and GPU shader layer.
  - Props: `variant` (`calm`, `vibrant`, `glass`), `intensity`, `hueShift`, `speed`, `grain`, `theme`, `disableShader`.
  - Detects reduced motion, contrast, forced colors, and device capability before activating shader (`ShaderLayer`).
  - Gradients animate via CSS custom properties throttled to 60/30fps depending on `navigator.connection.saveData`.
- `src/components/visuals/ShaderLayer.tsx` (code-split) – Three.js blob rendered only when capability checks pass.
- Tokens live in `src/styles/tokens.css`; Tailwind config maps them to utilities.

## Usage Patterns
```tsx
import BackgroundLayer from '@components/visuals/BackgroundLayer';
import { MotionBox } from '@components/motion/MotionBox';

export function Hero() {
  return (
    <div className="relative overflow-hidden">
      <BackgroundLayer variant="calm" intensity={0.85} />
      <MotionBox preset="rise" className="relative mx-auto max-w-2xl p-10">
        <h1 className="text-4xl font-semibold text-text">Underwrite confidently.</h1>
      </MotionBox>
    </div>
  );
}
```

## Accessibility & Performance
- Reduced motion disables continuous gradients/shaders and swaps MotionBox to static renders.
- High contrast / forced colors collapse gradients to solid surfaces and lighten noise.
- Modals/Drawers keep focus trapped, respect Escape, and avoid layout shifts.
- Route transitions skip animation for bfcache restores.
- Performance budget: transform/opacity only, no continuous `filter`/`box-shadow` animation, shader disabled on low-end hardware.

## Trade-offs
- Shader layer adds `three.js` as an optional chunk; guarded by capability checks to maintain <10KB CSS overhead.
- Storybook toggles reduced-motion and theme via globals; ensure new stories hook into the shared decorators.
- Existing legacy pages reuse new tokenized styles via Tailwind component layer; migrate to MotionBox/Button when time allows for full parity.

## Capturing demos
- Run `npm run storybook` and open the "Visuals/BackgroundLayer" or "Motion/MotionBox" stories to preview interactive states.
- Use Storybook's built-in toolbar screenshot (camera icon) or your browser's capture shortcuts to grab stills; for motion clips, record the canvas with your OS screen recorder while toggling presets.
- When recording, demonstrate both full-motion and reduced-motion toolbar toggles so reviewers can compare behaviours.
