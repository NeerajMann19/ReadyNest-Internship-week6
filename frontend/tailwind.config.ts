/**
 * NOTE FOR TAILWIND CSS V4:
 * In Tailwind CSS v4, all design tokens are defined via the `@theme` directive inside `src/index.css`.
 * `src/index.css` is the single source of truth for design tokens (colors, borders, radii, fonts).
 * This configuration file is retained as an empty shell for tooling compatibility only.
 */

import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
};

export default config;
