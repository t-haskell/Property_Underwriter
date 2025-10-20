'use client';

import clsx from 'clsx';
import type { CSSProperties, FC, ReactNode } from 'react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useMotionPreferences } from '@lib/motion';
import { noiseDataUri } from '@lib/visuals/noise';
import ShaderLayer from './ShaderLayer';

export type BackgroundVariant = 'calm' | 'vibrant' | 'glass';
export type BackgroundTheme = 'light' | 'dark' | 'system';

export interface BackgroundLayerProps {
  children?: ReactNode;
  intensity?: number;
  hueShift?: number;
  speed?: number;
  grain?: number;
  variant?: BackgroundVariant;
  theme?: BackgroundTheme;
  className?: string;
  disableShader?: boolean;
}

type NavigatorWithMemory = Navigator & {
  deviceMemory?: number;
  connection?: { saveData?: boolean };
};

const isLowEndDevice = () => {
  if (typeof navigator === 'undefined') return false;
  const enhancedNavigator = navigator as NavigatorWithMemory;
  const cores = enhancedNavigator.hardwareConcurrency ?? 8;
  const memory = enhancedNavigator.deviceMemory ?? 4;
  const saveData = enhancedNavigator.connection?.saveData;
  return cores <= 4 || memory <= 2 || Boolean(saveData);
};

const useShaderEligibility = (
  disabled: boolean,
  shouldReduceMotion: boolean,
  prefersContrast: boolean,
  forcedColors: boolean,
) => {
  const [eligible, setEligible] = useState(false);

  useEffect(() => {
    if (disabled || shouldReduceMotion || prefersContrast || forcedColors) {
      setEligible(false);
      return;
    }
    setEligible(!isLowEndDevice());
  }, [disabled, shouldReduceMotion, prefersContrast, forcedColors]);

  return eligible;
};

const variantTokens: Record<BackgroundVariant, { saturation: number; lightness: number; contrast: number }> = {
  calm: { saturation: 65, lightness: 82, contrast: 0.12 },
  vibrant: { saturation: 80, lightness: 70, contrast: 0.2 },
  glass: { saturation: 55, lightness: 88, contrast: 0.08 },
};

const gradientStyles = (
  variant: BackgroundVariant,
  intensity: number,
  hueShift: number,
  prefersContrast: boolean,
  forcedColors: boolean,
): CSSProperties => {
  if (forcedColors || prefersContrast) {
    return {
      background: 'var(--color-surface)',
    } as CSSProperties;
  }

  const { saturation, lightness, contrast } = variantTokens[variant];
  const stops = [
    `hsla(${210 + hueShift}, ${saturation}%, ${lightness}%, ${0.18 + intensity * contrast})`,
    `hsla(${260 + hueShift}, ${Math.min(100, saturation + 10)}%, ${Math.max(
      18,
      lightness - 18,
    )}%, ${0.32 + intensity * (contrast + 0.1)})`,
    `hsla(${330 + hueShift}, ${saturation}%, ${lightness + 6}%, ${0.22 + intensity * contrast})`,
  ];

  return {
    backgroundImage: `radial-gradient(circle at 15% 20%, ${stops[0]}, transparent 55%), radial-gradient(circle at 85% 25%, ${stops[1]}, transparent 60%), linear-gradient(var(--bg-angle, 120deg), ${stops[0]} 0%, ${stops[1]} 50%, ${stops[2]} 100%)`,
    filter: variant === 'glass' ? 'saturate(1.05) blur(0px)' : undefined,
  } satisfies CSSProperties;
};

export const BackgroundLayer: FC<BackgroundLayerProps> = ({
  children,
  intensity = 0.9,
  hueShift = 0,
  speed = 1,
  grain = 0.12,
  variant = 'calm',
  theme = 'system',
  className,
  disableShader = false,
}) => {
  const gradientRef = useRef<HTMLDivElement>(null);
  const { prefersContrast, forcedColors, shouldReduceMotion } = useMotionPreferences();
  const shaderEligible = useShaderEligibility(disableShader, shouldReduceMotion, prefersContrast, forcedColors);

  const themeAttrs = useMemo(() => {
    if (theme === 'system') return {};
    return { 'data-theme': theme };
  }, [theme]);

  useEffect(() => {
    const gradientEl = gradientRef.current;
    if (!gradientEl || shouldReduceMotion) {
      gradientEl?.style.removeProperty('--bg-angle');
      return;
    }

    let frameId = 0;
    let lastTime = 0;
    const enhancedNavigator = (typeof navigator !== 'undefined'
      ? (navigator as NavigatorWithMemory)
      : undefined);
    const frameInterval = 1000 / (enhancedNavigator?.connection?.saveData ? 30 : 60);

    const animate = (time: number) => {
      if (time - lastTime < frameInterval) {
        frameId = window.requestAnimationFrame(animate);
        return;
      }
      lastTime = time;
      const angle = (time / 1000) * (6 * speed) + 120;
      gradientEl.style.setProperty('--bg-angle', `${angle % 360}deg`);
      frameId = window.requestAnimationFrame(animate);
    };

    frameId = window.requestAnimationFrame(animate);
    return () => {
      window.cancelAnimationFrame(frameId);
    };
  }, [speed, shouldReduceMotion]);

  const gradientStyle = useMemo(
    () => ({
      '--bg-intensity': String(intensity),
      '--bg-hue-shift': `${hueShift}`,
      '--bg-speed': `${speed}`,
      ...gradientStyles(variant, intensity, hueShift, prefersContrast, forcedColors),
    }),
    [forcedColors, hueShift, intensity, prefersContrast, speed, variant],
  );

  return (
    <div
      className={clsx(
        'pointer-events-none absolute inset-0 overflow-hidden transition-colors duration-500 ease-standard',
        className,
      )}
      aria-hidden
      {...themeAttrs}
    >
      <div
        ref={gradientRef}
        className={clsx(
          'absolute inset-0 opacity-90 will-change-[background-image,filter]',
          prefersContrast || forcedColors ? 'opacity-100' : '',
        )}
        style={gradientStyle as CSSProperties}
      />
      {grain > 0 && !forcedColors && (
        <div
          className="absolute inset-0 mix-blend-soft-light"
          style={{
            backgroundImage: `url(${noiseDataUri})`,
            opacity: prefersContrast ? Math.min(0.08, grain) : grain,
          }}
        />
      )}
      {shaderEligible && variant !== 'glass' && (
        <div className="absolute inset-0" style={{ mixBlendMode: 'screen' }}>
          <ShaderLayer intensity={intensity} hueShift={hueShift} speed={speed} />
        </div>
      )}
      {children}
    </div>
  );
};

export default BackgroundLayer;
