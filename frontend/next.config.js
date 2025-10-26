/** @type {import('next').NextConfig} */
const rawBasePath = process.env.NEXT_PUBLIC_BASE_PATH;
const normalizedBasePath =
  rawBasePath && rawBasePath !== '/'
    ? `/${rawBasePath.replace(/^\/+|\/+$/g, '')}`
    : '';

const nextConfig = {
  reactStrictMode: true,
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  output: 'export',
  images: { unoptimized: true },
  ...(normalizedBasePath
    ? { basePath: normalizedBasePath, assetPrefix: normalizedBasePath }
    : {}),
  webpack: (config) => {
    config.resolve.alias = {
      ...(config.resolve.alias ?? {}),
      '@': require('path').join(__dirname, 'src'),
    };
    return config;
  },
};

module.exports = nextConfig;
