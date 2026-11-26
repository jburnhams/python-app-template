import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite-plus'

// `npm run build` writes into the Python package, so `./app serve` serves the built app.
// `npm run dev` runs the dev server with hot reload and proxies /api to a running `./app serve` (port 8360).
export default defineConfig({
  // Vite+ replaces Biome: `vp fmt` is Oxfmt, `vp lint` is Oxlint. The style is what the code was written in (single quotes,
  // no semicolons, 140 columns), so adopting the formatter does not change the look of the code.
  fmt: {
    printWidth: 140,
    singleQuote: true,
    semi: false,
    arrowParens: 'avoid',
    trailingComma: 'all',
    ignorePatterns: [
      'storybook-static',
      'dist-visual',
      'coverage',
      'tests/visual',
      '.storybook/public',
      'openapi.json',
      'src/api.generated.ts',
      'src/styles/theme.generated.css',
      'index.html',
      '*.json',
      '*.css',
      '*.md',
    ],
  },
  lint: {
    ignorePatterns: ['storybook-static', 'dist-visual', 'coverage', 'tests/visual', '.storybook/public', 'src/api.generated.ts'],
    options: { typeAware: true },
    // The type-aware rules the template has always enforced (Oxlint's default correctness rules stay on).
    rules: {
      'typescript/await-thenable': 'error',
      'typescript/no-floating-promises': 'error',
      'typescript/no-misused-promises': 'error',
      'typescript/require-await': 'error',
      'typescript/unbound-method': 'error',
      'typescript/prefer-promise-reject-errors': 'error',
      'typescript/restrict-template-expressions': 'error',
      'typescript/no-base-to-string': 'error',
      'typescript/no-redundant-type-constituents': 'error',
      'typescript/no-for-in-array': 'error',
      'typescript/only-throw-error': 'error',
      'typescript/no-implied-eval': 'error',
    },
  },
  base: './', // relative asset paths, so the app works at the server's root and behind a reverse proxy at a path (the server's <base> tag and api.ts BASE do the same for routes and the API)
  plugins: [react(), tailwindcss()],
  build: {
    outDir: '../src/app/server/static',
    emptyOutDir: true,
    // One bundle of about 800 kB (245 kB gzipped), most of it React, React Aria, React Router, TanStack and Strata. A local app loads it once; split routes with lazy() when that stops being true.
    chunkSizeWarningLimit: 1000,
  },
  server: { proxy: { '/api': 'http://127.0.0.1:8360' } },
})
