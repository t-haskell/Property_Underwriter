'use client';

import dynamic from 'next/dynamic';
import type { FC } from 'react';

export interface ShaderLayerProps {
  intensity: number;
  hueShift: number;
  speed: number;
}

const ShaderLayerCanvas = dynamic(
  () => import('./ShaderLayerCanvas').then((mod) => mod.ShaderLayerCanvas),
  { ssr: false, loading: () => null },
);

export const ShaderLayer: FC<ShaderLayerProps> = (props) => {
  return <ShaderLayerCanvas {...props} />;
};

export default ShaderLayer;
