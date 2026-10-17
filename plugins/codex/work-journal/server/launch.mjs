import { fileURLToPath } from 'node:url';
process.chdir(fileURLToPath(new URL('.', import.meta.url)));
await import('./dist/index.js');
