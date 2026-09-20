# maternanalytics (frontend)

React 18 + TypeScript + Vite. Documentación general, variables de entorno y ejecución del proyecto completo en el [README de la raíz](../../README.md); arquitectura del frontend en [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).

```bash
pnpm install
pnpm dev         # http://localhost:5173 (proxy de /api hacia localhost:8000)
pnpm build       # tsc -b && vite build
pnpm lint
pnpm test        # vitest (unitarias; e2e/ lo ejecuta Playwright)
```
