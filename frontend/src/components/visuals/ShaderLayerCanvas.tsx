'use client';

import { Canvas, useFrame } from '@react-three/fiber';
import type { FC } from 'react';
import { Suspense, useMemo, useRef } from 'react';
import type { BufferGeometry, Mesh, MeshStandardMaterial } from 'three';
import { Color, Vector3 } from 'three';
import type { ShaderLayerProps } from './ShaderLayer';

type BlobMesh = Mesh<BufferGeometry, MeshStandardMaterial>;

const Blob: FC<ShaderLayerProps> = ({ intensity, hueShift, speed }) => {
  const meshRef = useRef<BlobMesh>(null);
  const materialColor = useMemo(() => new Color(`hsl(${210 + hueShift}, 70%, 60%)`), [hueShift]);

  useFrame(({ clock }) => {
    const mesh = meshRef.current;
    if (!mesh) return;
    const material = mesh.material as MeshStandardMaterial;
    const t = clock.getElapsedTime() * speed * 0.15;
    const wobble = Math.sin(t) * 0.4 * intensity;
    mesh.rotation.x = wobble * 0.4;
    mesh.rotation.y = Math.cos(t) * 0.35 * intensity;
    mesh.scale.setScalar(3 + Math.sin(t * 0.5) * 0.2 * intensity);
    material.emissiveIntensity = 0.5 + Math.abs(Math.sin(t)) * 0.3 * intensity;
    material.color.lerp(materialColor, 0.08);
  });

  useFrame(({ clock, camera }) => {
    const t = clock.getElapsedTime() * speed * 0.12;
    const targetZ = 3 + Math.sin(t) * 0.5 * intensity;
    camera.position.lerp(new Vector3(0, 0, targetZ), 0.05);
  });

  return (
    <mesh ref={meshRef}>
      <icosahedronGeometry args={[1, 4]} />
      <meshStandardMaterial
        color={`hsl(${210 + hueShift}, 70%, 65%)`}
        transparent
        opacity={0.68 + intensity * 0.1}
        metalness={0.35}
        roughness={0.18}
        emissive={`hsl(${210 + hueShift}, 80%, 72%)`}
      />
    </mesh>
  );
};

export const ShaderLayerCanvas: FC<ShaderLayerProps> = ({ intensity, hueShift, speed }) => {
  return (
    <Suspense fallback={null}>
      <Canvas
        gl={{ antialias: false, powerPreference: 'high-performance' }}
        dpr={[1, 1.5]}
        style={{ position: 'absolute', inset: 0 }}
        camera={{ position: [0, 0, 3], fov: 45 }}
      >
        <color attach="background" args={[`hsl(${210 + hueShift}, 75%, 8%)`]} />
        <ambientLight intensity={0.5} />
        <directionalLight position={[4, 6, 4]} intensity={0.9} />
        <Blob intensity={intensity} hueShift={hueShift} speed={speed} />
      </Canvas>
    </Suspense>
  );
};

export default ShaderLayerCanvas;
