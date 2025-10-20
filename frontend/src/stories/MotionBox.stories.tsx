import type { Meta, StoryObj } from '@storybook/react';
import { MotionBox } from '@components/motion/MotionBox';
import { Button } from '@components/ui/Button';

const meta: Meta<typeof MotionBox> = {
  title: 'Motion/MotionBox',
  component: MotionBox,
  args: {
    preset: 'rise',
    children: 'Motion box content',
  },
  argTypes: {
    preset: {
      control: 'select',
      options: ['fade', 'rise', 'scale', 'slideUp', 'slideDown', 'slideLeft', 'slideRight', 'springy'],
    },
    distance: {
      control: { type: 'number', min: 0, max: 120, step: 4 },
    },
  },
};

export default meta;

type Story = StoryObj<typeof MotionBox>;

export const Playground: Story = {
  render: (args) => (
    <MotionBox
      {...args}
      className="flex min-h-[120px] min-w-[280px] flex-col items-center justify-center gap-4 rounded-xl border border-border bg-surface-alt/80 p-6 text-center shadow-subtle"
    >
      <span className="text-sm text-text-muted">
        Experiment with different presets, adjust distance, and toggle reduced motion from the toolbar.
      </span>
      <Button variant="secondary">Action</Button>
    </MotionBox>
  ),
};
