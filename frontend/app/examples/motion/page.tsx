'use client';

import { motion } from 'framer-motion';
import { useMemo, useState } from 'react';
import { MotionBox } from '@components/motion/MotionBox';
import BackgroundLayer from '@components/visuals/BackgroundLayer';
import { Button } from '@components/ui/Button';
import Card from '@components/ui/Card';
import Drawer from '@components/ui/Drawer';
import Modal from '@components/ui/Modal';
import { useMotionPreferences, useStagger } from '@lib/motion';
import type { BackgroundTheme, BackgroundVariant } from '@components/visuals/BackgroundLayer';

const cards = [
  {
    title: 'LTV Snapshot',
    description: 'Monitor loan-to-value targets with live underwriting baselines.',
  },
  {
    title: 'Cashflow Confidence',
    description: 'Scenario modeling with volatility-aware guardrails.',
  },
  {
    title: 'Neighborhood Pulse',
    description: 'Micro-market sentiment and comp velocity updates every hour.',
  },
];

export default function MotionShowcase() {
  const { reducedMotion, prefersContrast } = useMotionPreferences();
  const [variant, setVariant] = useState<BackgroundVariant>('calm');
  const [theme, setTheme] = useState<BackgroundTheme>('system');
  const [intensity, setIntensity] = useState(0.9);
  const [hueShift, setHueShift] = useState(0);
  const [speed, setSpeed] = useState(0.6);
  const [grain, setGrain] = useState(0.12);
  const [modalOpen, setModalOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const stagger = useStagger(cards.length, 0.08);

  const controls = useMemo(
    () => [
      {
        label: 'Variant',
        value: variant,
        onChange: (value: string) => setVariant(value as BackgroundVariant),
        options: [
          { label: 'Calm', value: 'calm' },
          { label: 'Vibrant', value: 'vibrant' },
          { label: 'Glass', value: 'glass' },
        ],
      },
      {
        label: 'Theme',
        value: theme,
        onChange: (value: string) => setTheme(value as BackgroundTheme),
        options: [
          { label: 'System', value: 'system' },
          { label: 'Light', value: 'light' },
          { label: 'Dark', value: 'dark' },
        ],
      },
    ],
    [theme, variant],
  );

  return (
    <div className="relative isolate overflow-hidden">
      <div className="absolute inset-0">
        <BackgroundLayer
          variant={variant}
          intensity={intensity}
          hueShift={hueShift}
          speed={speed}
          grain={grain}
          theme={theme}
        />
      </div>
      <div className="relative mx-auto flex min-h-[calc(100vh-5rem)] max-w-6xl flex-col gap-16 px-6 py-16">
        <section className="max-w-3xl space-y-6 text-balance">
          <MotionBox preset="rise" className="inline-flex rounded-full border border-white/20 bg-white/10 px-4 py-1 text-xs uppercase tracking-[0.24em] text-text/70">
            Motion system · Intentional & calm
          </MotionBox>
          <MotionBox preset="fade" className="space-y-3">
            <h1 className="text-4xl font-semibold text-text md:text-5xl">
              Motion primitives for confident underwriting experiences
            </h1>
            <p className="text-lg text-text-muted md:text-xl">
              Tokens, variants, and backgrounds that respond to intent, respect accessibility, and keep focus on the data that matters.
            </p>
          </MotionBox>
          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={() => setModalOpen(true)}>Open modal</Button>
            <Button variant="secondary" onClick={() => setDrawerOpen(true)}>
              Peek drawer
            </Button>
            <span className="text-xs text-text-muted">
              {reducedMotion ? 'Reduced motion enabled' : 'Full motion experience'}
              {prefersContrast && ' · High contrast mode'}
            </span>
          </div>
        </section>
        <section className="grid gap-6 md:grid-cols-[320px_1fr]">
          <div className="space-y-5 rounded-2xl bg-surface/80 p-6 shadow-subtle backdrop-blur">
            <h2 className="text-sm font-semibold text-text">Background controls</h2>
            {controls.map((control) => (
              <label key={control.label} className="flex flex-col gap-1 text-xs font-medium text-text">
                {control.label}
                <select
                  value={control.value}
                  onChange={(event) => control.onChange(event.target.value)}
                  className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text shadow-subtle focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                >
                  {control.options.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            ))}
            <label className="flex flex-col gap-1 text-xs font-medium text-text">
              Intensity
              <input
                type="range"
                min={0.1}
                max={1}
                step={0.05}
                value={intensity}
                onChange={(event) => setIntensity(Number(event.target.value))}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs font-medium text-text">
              Hue shift
              <input
                type="range"
                min={-60}
                max={60}
                step={5}
                value={hueShift}
                onChange={(event) => setHueShift(Number(event.target.value))}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs font-medium text-text">
              Speed
              <input
                type="range"
                min={0}
                max={1.4}
                step={0.1}
                value={speed}
                onChange={(event) => setSpeed(Number(event.target.value))}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs font-medium text-text">
              Grain
              <input
                type="range"
                min={0}
                max={0.4}
                step={0.02}
                value={grain}
                onChange={(event) => setGrain(Number(event.target.value))}
              />
            </label>
          </div>
          <motion.div
            className="grid gap-4 md:grid-cols-3"
            variants={stagger}
            initial="hidden"
            animate="show"
          >
            {cards.map((card) => (
              <Card key={card.title} heading={card.title} description={card.description} interactive variant="glass">
                <div className="text-sm text-text-muted">
                  Minimal, responsive hover lifts paired with subtle glassmorphism keep focus on critical signals.
                </div>
              </Card>
            ))}
          </motion.div>
        </section>
      </div>
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Underwriting checklist"
        description="Transitions respect focus and reduced-motion preferences."
        footer={
          <div className="flex gap-2">
            <Button variant="ghost" onClick={() => setModalOpen(false)}>
              Close
            </Button>
            <Button onClick={() => setModalOpen(false)}>Acknowledge</Button>
          </div>
        }
      >
        <ul className="space-y-2 text-left">
          <li>• Verify rent roll assumptions within ±5%.</li>
          <li>• Confirm rehab budget allowances for material volatility.</li>
          <li>• Align exit cap scenarios with macro sensitivity.</li>
        </ul>
      </Modal>
      <Drawer open={drawerOpen} onClose={() => setDrawerOpen(false)} title="Quick actions">
        <div className="space-y-3">
          <Button fullWidth onClick={() => setModalOpen(true)}>
            Review terms
          </Button>
          <Button fullWidth variant="secondary" onClick={() => setDrawerOpen(false)}>
            Dismiss
          </Button>
        </div>
      </Drawer>
    </div>
  );
}
