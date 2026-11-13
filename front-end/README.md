# React + Vite

## API configuration

Copy `.env.example` to `.env.development` in `front-end/` and adjust it for
your environment. Restart `npm run dev` after changing environment values.

- `VITE_API_BASE_URL` is the browser-facing API path. It defaults to
  `/api/v1`; browser requests stay on the frontend origin and use Django
  session cookies and CSRF headers.
- `API_PROXY_TARGET` is read only by Vite and controls where its `/api`
  development proxy forwards requests. It defaults to
  `http://127.0.0.1:8000` and is not exposed to browser code.

For local Django development, independently copy the repository root
`.env.example` to the root `.env`. Set `DJANGO_ALLOWED_HOSTS` and
`DJANGO_CSRF_TRUSTED_ORIGINS` there for the frontend origin, including its
scheme and port (for example `http://localhost:5173`). The Vite proxy keeps
browser requests same-origin, but Django still validates the request's Origin
against `CSRF_TRUSTED_ORIGINS` for unsafe requests.

In production, set `VITE_API_BASE_URL` to the API path served by the same-origin
reverse proxy. Configure Django's trusted origins for the actual browser origin.
The Vite proxy is for development only.

Environment variables are read when Vite starts or builds. Do not put secrets
in variables prefixed with `VITE_`; Vite embeds those values in browser assets.

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
