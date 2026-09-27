import path from 'node:path'
import { webpack, type WebpackOverrideFn } from '@remotion/bundler'
import { enableTailwind } from '@remotion/tailwind'

// The product app's root (where its tsconfig "@/*" alias points). Edit per product.
const repo = '/abs/path/to/product/app'
const here = process.cwd()

// Public env vars the product validates at import time. Placeholders only: a film never calls the backend.
const env: Record<string, string> = {
  NEXT_PUBLIC_API_URL: 'http://127.0.0.1:9',
  NEXT_PUBLIC_ENV: 'development',
}

export const webpackOverride: WebpackOverrideFn = (config) =>
  enableTailwind(
    {
      ...config,
      resolve: {
        ...config.resolve,
        alias: {
          ...(config.resolve?.alias ?? {}),
          '@': repo,
          'next/link': path.join(here, 'src/stubs/next-link.tsx'),
          'next/navigation': path.join(here, 'src/stubs/next-navigation.ts'),
          'next/image': path.join(here, 'src/stubs/next-image.tsx'),
          // Telemetry SDKs that import Next internals or phone home: no-ops.
          '@sentry/nextjs': path.join(here, 'src/stubs/noop-module.cjs'),
          // Workspace packages the product imports from source, e.g.:
          // '@acme/shared': path.join(repo, '../packages/shared/src'),
        },
        modules: ['node_modules', path.join(here, 'node_modules'), path.join(repo, 'node_modules'), path.join(repo, '../node_modules')],
      },
      plugins: [
        ...(config.plugins ?? []),
        // Next injects React into every module; some product files rely on it without importing it.
        new webpack.ProvidePlugin({ React: 'react' }),
        new webpack.DefinePlugin(Object.fromEntries(Object.entries(env).map(([key, value]) => [`process.env.${key}`, JSON.stringify(value)]))),
      ],
    },
    { configLocation: path.join(here, 'tailwind.config.ts') },
  )
