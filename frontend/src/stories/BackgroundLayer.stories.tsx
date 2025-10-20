import type { Meta, StoryObj } from '@storybook/react';
import BackgroundLayer from '@components/visuals/BackgroundLayer';

const meta: Meta<typeof BackgroundLayer> = {
  title: 'Visuals/BackgroundLayer',
  component: BackgroundLayer,
  parameters: {
    layout: 'fullscreen',
  },
  args: {
    intensity: 0.9,
    hueShift: 0,
    speed: 0.6,
    grain: 0.12,
    variant: 'calm',
    theme: 'system',
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['calm', 'vibrant', 'glass'],
    },
    theme: {
      control: 'select',
      options: ['system', 'light', 'dark'],
    },
    intensity: {
      control: { type: 'range', min: 0.1, max: 1, step: 0.05 },
    },
    hueShift: {
      control: { type: 'range', min: -60, max: 60, step: 5 },
    },
    speed: {
      control: { type: 'range', min: 0, max: 1.4, step: 0.1 },
    },
    grain: {
      control: { type: 'range', min: 0, max: 0.4, step: 0.02 },
    },
  },
};

export default meta;

type Story = StoryObj<typeof BackgroundLayer>;

export const Playground: Story = {
  render: (args) => (
    <div className="relative flex h-[70vh] w-full items-center justify-center overflow-hidden">
      <BackgroundLayer {...args}>
        <div className="pointer-events-auto rounded-2xl bg-white/60 px-6 py-4 text-center text-text shadow-subtle backdrop-blur">
          Adjust the controls to see the gradient respond in real-time.
        </div>
      </BackgroundLayer>
    </div>
  ),
};
