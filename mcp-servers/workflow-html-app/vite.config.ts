import { defineConfig } from 'vite';
import { viteSingleFile } from 'vite-plugin-singlefile';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [viteSingleFile()],
  root: 'ui',
  build: {
    outDir: '../dist/ui',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        'plan-viewer': resolve(__dirname, 'ui/plan-viewer.html'),
      },
    },
  },
});
