import { createRequire } from 'node:module';
import { copyFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const require = createRequire(import.meta.url);
const target = fileURLToPath(new URL('./gsap.min.js', import.meta.url));
copyFileSync(require.resolve('gsap/dist/gsap.min.js'), target);
console.log('Prepared local GSAP runtime.');
