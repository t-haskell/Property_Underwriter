import type { Decorator, Preview } from '@storybook/react';
import { useEffect } from 'react';
import '../styles/globals.css';

const withTheme: Decorator = (Story, context) => {
  const theme = context.globals.theme as 'light' | 'dark' | 'system';

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'system') {
      root.removeAttribute('data-theme');
      return;
    }
    root.setAttribute('data-theme', theme);
  }, [theme]);

  return (
    <div className="min-h-screen bg-surface text-text">
      <Story />
    </div>
  );
};

const preview: Preview = {
  parameters: {
    layout: 'centered',
    controls: { expanded: true },
    actions: { argTypesRegex: '^on.*' },
  },
  globalTypes: {
    theme: {
      description: 'Theme mode',
      defaultValue: 'system',
      toolbar: {
        icon: 'circlehollow',
        items: [
          { value: 'system', title: 'System' },
          { value: 'light', title: 'Light' },
          { value: 'dark', title: 'Dark' },
        ],
      },
    },
    motion: {
      description: 'Reduced motion',
      defaultValue: 'full',
      toolbar: {
        icon: 'transfer',
        items: [
          { value: 'full', title: 'Full motion' },
          { value: 'reduced', title: 'Reduced motion' },
        ],
      },
    },
  },
  decorators: [withTheme, (Story, context) => {
    const prefersReduced = context.globals.motion === 'reduced';
    useEffect(() => {
      const root = document.documentElement;
      root.dataset.reducedMotion = prefersReduced ? 'true' : 'false';
    }, [prefersReduced]);

    return <Story />;
  }],
};

export default preview;
