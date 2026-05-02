# Edge API (Lab 17)

Учебный проект для Lab 17: Cloudflare Workers Edge Deployment.

## What is included

- TypeScript Worker в `src/index.ts`
- Маршруты: `/`, `/health`, `/edge`, `/counter`
- KV-backed counter (`GET`, `POST`, `DELETE`)
- Конфигурация в `wrangler.jsonc` с `vars` и `kv_namespaces`
- Секреты через Cloudflare Secrets: `API_TOKEN`, `ADMIN_EMAIL`

## Prerequisites

- Node.js 18+
- npm
- Cloudflare account
- Wrangler CLI (локально через `npx`)

## Install and run locally

```bash
cd edge-api
npm install
npm run dev
```

## API routes

- `GET /` - общая информация о сервисе
- `GET /health` - health-check
- `GET /edge` - edge metadata (`colo`, `country`, `city`, `asn`, `httpProtocol`, `tlsVersion`)
- `GET /counter` - получить значение счётчика из KV
- `POST /counter` - увеличить счётчик на 1
- `DELETE /counter` - сбросить счётчик

## KV namespace setup

Создайте KV namespace и подставьте реальные ID в `wrangler.jsonc`:

```bash
npx wrangler kv namespace create COUNTER_KV
npx wrangler kv namespace create COUNTER_KV --preview
```

После этого замените:
- `kv_namespaces[0].id`
- `kv_namespaces[0].preview_id`

## Secrets setup

Создайте обязательные секреты (не хранить в `wrangler.jsonc` и git):

```bash
cd edge-api
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

Проверить список имён секретов:

```bash
npx wrangler secret list
```

Ожидаемо вы увидите имена секретов, но не их значения.

## Safe secret verification

После `npm run dev` или деплоя проверьте:

```bash
curl http://127.0.0.1:8787/
curl http://127.0.0.1:8787/health
```

Что должно быть в ответах:
- В `/` поле `security.apiToken` только в маскированном виде (например `abcd...yz`), а `security.adminEmail` в частично скрытом виде.
- В `/health` только булевы флаги `secrets.apiTokenConfigured` и `secrets.adminEmailConfigured`.
- Полные значения секретов нигде не возвращаются.

## Deploy

```bash
npm run deploy
```

После деплоя Worker будет доступен по URL вида:

```text
https://<worker-name>.<your-subdomain>.workers.dev
```
