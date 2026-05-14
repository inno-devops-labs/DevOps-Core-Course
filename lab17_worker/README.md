Lab 17 — Task 1: Cloudflare Setup (Worker project scaffold)
=========================================================

Кратко: этот каталог содержит каркас Cloudflare Workers проекта на TypeScript для выполнения первого задания (Cloudflare Setup).

Что я сделал
- Добавил минимальный проект Workers с TypeScript (файлы: `wrangler.jsonc`, `package.json`, `tsconfig.json`, `src/index.ts`).
- Добавил `README.md` с командами для авторизации Wrangler и проверки `npx wrangler whoami`.

Как выполнить Task 1 (локально)

1) Установите Node.js 18+ и npm

2) Установите Wrangler на глобальном уровне (опционально) или запускайте через `npx`

3) Авторизуйтесь в Cloudflare (откроется браузер):

```bash
npx wrangler login
```

4) Проверьте авторизацию:

```bash
npx wrangler whoami
```

Если `whoami` вернул данные аккаунта — CLI аутентификация прошла успешно.

Пояснения
- `workers.dev` — это автоматически выдаваемый поддомен для вашего воркера при deploy (например, my-worker.NAMESPACE.workers.dev). Он даётся Cloudflare и позволяет публичный доступ без настройки собственного домена.
- `wrangler.jsonc` / `wrangler.toml` — конфигурационный файл Wrangler. В `wrangler.jsonc` можно хранить незашифрованные (plaintext) переменные, но секреты должны храниться через `wrangler secret put`.

Дальше (рекомендуется)
- После авторизации запустите `npx wrangler dev` для локальной разработки и проверки маршрутов.
- Для деплоя используйте `npx wrangler deploy` (потребуется авторизация и рабочая учетная запись Cloudflare).

Файлы проекта: [wrangler.jsonc](wrangler.jsonc), [src/index.ts](src/index.ts)

## Task 2 — Local API routes

Available routes:
- `GET /health` — simple health check returning `OK`
- `GET /meta` — JSON metadata about the deployment and request
- `GET /` — JSON welcome response with the route list

Local test commands:

```bash
npx wrangler dev
curl -i http://127.0.0.1:8787/health
curl -s http://127.0.0.1:8787/meta | jq .
curl -s http://127.0.0.1:8787/ | jq .
```

## Task 3 — Edge metadata and routing concepts

Edge metadata endpoint:
- `GET /edge`
- Returns Cloudflare request context from `request.cf`
- Includes at least `colo` and `country`
- Includes extra fields such as `asn`, `city`, `httpProtocol`, and `tlsVersion`

How to verify on the public edge URL:

```bash
curl -s https://lab17-worker.niyaz-lab17.workers.dev/edge | jq .
```

What this shows:
- Cloudflare runs the Worker close to the request’s edge location.
- The platform injects request metadata at the edge, so the Worker can see location and network details without a VM region selection step.
- There is no “deploy to 3 regions” choice because Cloudflare handles global distribution automatically.

Routing concepts:
- `workers.dev` — default public hostname for a Worker, good for quick testing and labs.
- Routes — path-based mappings from a domain to a Worker, usually for production traffic on a custom domain.
- Custom domains — full hostname ownership with your own DNS, certificates, and production routing.

In this lab, `workers.dev` is the required public deployment target; custom domains are optional.

## Task 4 — Configuration, secrets, and KV persistence

Plaintext variable:
- `PLAINTEXT_VAR` is defined in `wrangler.jsonc`
- It is safe only for non-sensitive values because it is committed to source control

Secrets:
- `APP_SECRET_ONE`
- `APP_SECRET_TWO`

Create them with Wrangler and do not commit the values:

```bash
cd lab17_worker
npx wrangler secret put APP_SECRET_ONE
npx wrangler secret put APP_SECRET_TWO
```

KV persistence:
- Binding name: `LAB17_KV`
- Routes:
	- `POST /kv?key=demo&value=hello` stores a value
	- `GET /kv?key=demo` reads a value
	- `GET /config` confirms plaintext and secret bindings are present

Create the KV namespace and preview namespace:

```bash
npx wrangler kv namespace create LAB17_KV
npx wrangler kv namespace create LAB17_KV --preview
```

After creation, copy the produced namespace IDs into `wrangler.jsonc` under `kv_namespaces`.

Verification flow:
1. Store a value with `POST /kv`
2. Redeploy the Worker
3. Read the same key with `GET /kv`
4. Confirm the value is still present after redeploy

## Task 5 — Observability and deployments

Logs:
- The Worker writes `console.log()` entries for every request
- The log message includes the build version and path
- View live logs with:

```bash
npx wrangler tail
```

Metrics:
- In the Cloudflare dashboard, inspect request counts, errors, and execution activity for the Worker
- The most useful view for this lab is the request/error panel for the deployed Worker route

Deployment history and rollback:
- Deploy at least two versions by changing `BUILD_VERSION` in `src/index.ts` and running `npx wrangler deploy`
- The deploy output includes a version ID you can record as evidence
- To roll back, restore the previous `BUILD_VERSION` value and deploy again, or use the dashboard rollback option if available

Suggested verification sequence:
1. Deploy version `task5-v1`
2. Tail logs and capture one request log line
3. Change to `task5-v2` and deploy again
4. Roll back to `task5-v1` and deploy once more
5. Confirm the public URL still responds after the rollback

Observed evidence from this workspace:
- Live log line captured via tail: `[task5-v1] Incoming request GET /meta`
- Deployment version IDs seen in Wrangler output:
	- `ac0607bf-9512-48b3-b155-6330c6016007`
	- `7aecc901-4c93-4fef-b7b2-1e327587eb67`
	- `215b9646-04de-4f3e-aa29-230b92776c26`
- Current public build after rollback: `task5-v1`

