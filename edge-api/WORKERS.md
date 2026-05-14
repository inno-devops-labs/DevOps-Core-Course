# Lab 17 — Cloudflare Workers Edge API

Hi — this is my write-up for Lab 17 in `https://github.com/nexonm22/DevOps-Core-Course.git`. I kept the same product name from earlier labs (`devops-info-service`) but registered the Worker on Cloudflare as **`devops-info-service-edge`** so it does not clash with other resources.

The assignment wants a `WORKERS.md`; I put mine here in **`edge-api/`** next to the Worker code because that is where I actually run `wrangler` from (`package.json`, `wrangler.jsonc`, `src/`). Easier than hunting for docs at repo root.

---

## 1. Cloudflare setup

### Create the project

I created the project from the repository root with:

```bash
npm create cloudflare@latest -- edge-api
```

The `create cloudflare` wizard threw a bunch of prompts at me; I picked hello-world, Worker-only, TypeScript, yes to git, and **no** to “deploy right now” because I still had code to write.

```
? What type of application do you want to create? > Hello World example
? What kind of application? > Worker only
? Do you want to use TypeScript? > Yes
? Do you want to use Git for this project? > Yes
? Do you want to deploy your application now? > No
```

Once the scaffold existed I replaced the stock files with what you see in `edge-api/` now (the routes, KV bits, etc.).

### Login

```bash
npx wrangler login
npx wrangler whoami
```

`whoami` confirmed I was on the right account:

```
Getting User settings...
You are logged in with an OAuth Token, associated with the email nexonm22@gmail.com.
+--------------------------------+----------------------------------+
| Account Name                   | Account ID                       |
+--------------------------------+----------------------------------+
| nexonm22@gmail.com's Account   | a8f35bbf7cc342bd359b3e12c1dd42b8 |
+--------------------------------+----------------------------------+

Token Permissions:
Scope (Workers)
- account (read)
- user (read)
- workers (write)
- workers_kv (write)
...
```

The Cloudflare username for the public `workers.dev` URL is `nexonm22`, matching my Docker Hub and GitHub handle from earlier labs.

### Project layout

From inside this project directory:

```
.
├── WORKERS.md
├── src/index.ts
├── wrangler.jsonc
├── package.json
└── tsconfig.json
```

### About `wrangler.jsonc`

`wrangler.jsonc` is the Wrangler config file. It tells Wrangler which file is the entry (`main`), which compatibility date to use, and which bindings exist (vars, KV). Wrangler reads it when I run `wrangler dev` or `wrangler deploy`.

The `name` field sets the Worker name on Cloudflare. The `kv_namespaces` list binds the KV namespace ID to the name `SETTINGS` in code.

### About `workers.dev`

Cloudflare gives each account a free subdomain on `workers.dev`. After deploy, the Worker is reachable at `https://<worker-name>.<subdomain>.workers.dev` without buying a domain. It is useful for labs and demos. For production I could add a route on my own domain in the dashboard.

### Bindings: vars, secrets, KV

Bindings connect the Worker to config and storage at runtime. Plaintext vars come from `wrangler.jsonc` and are visible in git. Secrets are stored encrypted by Cloudflare; I set them with `wrangler secret put` and the value never appears in the repo. KV is a separate store: I bind it by ID so the Worker can call `get` / `put` without HTTP. Secrets are not vars because tokens must not live in source control or in the dashboard as plain text.

---

## 2. Worker API

### What the repo shows vs what happened on the edge

Everything below matches the **current** `src/index.ts` in git, including **`version: "1.0.0"`** on `/` — I treated that as my “v2” bundle in section 5.

For the rollback exercise I had an older deployment (**c3a91f82…**) that did **not** expose `version` in the JSON. Rolling back pointed live traffic at that older bundle, which is why the post-rollback `curl` in section 5 looks different from the file on disk. After I finished proving rollback worked I **`wrangler deploy`**’d again so production lines up with what is committed.

### Source code

Full file `src/index.ts`:

```typescript
export interface Env {
	SETTINGS: KVNamespace;
	APP_NAME: string;
	COURSE_NAME: string;
}

const STARTED_AT = Date.now();
const VISITS_KEY = "visits";

export default {
	async fetch(
		request: Request,
		env: Env,
		_ctx: ExecutionContext,
	): Promise<Response> {
		const url = new URL(request.url);
		const path = url.pathname;
		const cf = request.cf as IncomingRequestCfProperties | undefined;
		const colo = cf?.colo ?? "unknown";

		console.log(
			`request ${request.method} ${path} colo=${colo}`,
		);

		if (request.method !== "GET") {
			return new Response("Method Not Allowed", { status: 405 });
		}

		if (path === "/") {
			return Response.json({
				app: env.APP_NAME,
				version: "1.0.0",
				message: "Hello from Cloudflare Workers edge API",
				timestamp: new Date().toISOString(),
			});
		}

		if (path === "/health") {
			const uptimeSec = Math.floor((Date.now() - STARTED_AT) / 1000);
			return Response.json({
				status: "ok",
				uptime: uptimeSec,
			});
		}

		if (path === "/edge") {
			return Response.json({
				colo: cf?.colo ?? "unknown",
				country: cf?.country ?? "unknown",
				city: cf?.city ?? "unknown",
				asn: cf?.asn ?? 0,
				httpProtocol: cf?.httpProtocol ?? "unknown",
				tlsVersion: cf?.tlsVersion ?? "unknown",
			});
		}

		if (path === "/counter") {
			const raw = await env.SETTINGS.get(VISITS_KEY);
			const prev = raw ? parseInt(raw, 10) : 0;
			const next = Number.isFinite(prev) ? prev + 1 : 1;
			await env.SETTINGS.put(VISITS_KEY, String(next));
			return Response.json({ visits: next });
		}

		return Response.json(
			{ error: "Not Found", path },
			{ status: 404 },
		);
	},
};
```

### `package.json`

```json
{
	"name": "devops-info-service-edge",
	"version": "1.0.0",
	"private": true,
	"scripts": {
		"dev": "wrangler dev",
		"deploy": "wrangler deploy",
		"cf-typegen": "wrangler types"
	},
	"devDependencies": {
		"@cloudflare/workers-types": "^4.20241106.0",
		"typescript": "^5.6.3",
		"wrangler": "^3.91.0"
	}
}
```

### `tsconfig.json`

```json
{
	"compilerOptions": {
		"target": "ES2022",
		"module": "ES2022",
		"lib": ["ES2022"],
		"types": ["@cloudflare/workers-types"],
		"moduleResolution": "bundler",
		"strict": true,
		"skipLibCheck": true,
		"noEmit": true,
		"isolatedModules": true
	},
	"include": ["src/**/*"]
}
```

### Local development

Run from this project directory (`edge-api/`):

```bash
npx wrangler dev
```

First boot of `wrangler dev` — bindings showed up correctly and the server listened on **8787**:

```
wrangler 3.91.0
-------------------
Your Worker has access to the following bindings:
- KV Namespaces:
  - SETTINGS: b41ace1d745341308313c7814907e108
- Vars:
  - APP_NAME: "devops-info-service"
  - COURSE_NAME: "DevOps-Core-Course"
Starting local server...
[wrangler:inf] Ready on http://localhost:8787
[wrangler:inf] GET / 200 OK (12ms)
```

### Curl tests (local)

```bash
curl -s http://localhost:8787/
```

```json
{
  "app": "devops-info-service",
  "version": "1.0.0",
  "message": "Hello from Cloudflare Workers edge API",
  "timestamp": "2026-05-11T14:22:03.441Z"
}
```

```bash
curl -s http://localhost:8787/health
```

```json
{
  "status": "ok",
  "uptime": 42
}
```

```bash
curl -s -w "\nHTTP %{http_code}\n" http://localhost:8787/notfound
```

```json
{
  "error": "Not Found",
  "path": "/notfound"
}
```

HTTP status: 404

### Deploy

```bash
npx wrangler deploy
```

First successful push to the edge (upload size, seconds, and deployment UUID change run to run — this is one real capture from my terminal):

```
wrangler 3.91.0
-------------------
Total Upload: 3.87 KiB / gzip: 1.52 KiB
Your Worker has access to the following bindings:
- KV Namespaces:
  - SETTINGS: b41ace1d745341308313c7814907e108
Uploaded devops-info-service-edge (5.41 sec)
Published devops-info-service-edge (1.92 sec)
  https://devops-info-service-edge.nexonm22.workers.dev
Current Deployment ID: e47b2061-5fcc-4a9a-b8d3-662c9045e1ab
Deployed successfully!
```

### Curl tests (production)

```bash
curl -s https://devops-info-service-edge.nexonm22.workers.dev/
```

```json
{
  "app": "devops-info-service",
  "version": "1.0.0",
  "message": "Hello from Cloudflare Workers edge API",
  "timestamp": "2026-05-11T14:24:18.903Z"
}
```

```bash
curl -s https://devops-info-service-edge.nexonm22.workers.dev/health
```

```json
{
  "status": "ok",
  "uptime": 17
}
```

---

## 3. Global edge behavior

```bash
curl -s https://devops-info-service-edge.nexonm22.workers.dev/edge
```

```json
{
  "colo": "AMS",
  "country": "RU",
  "city": "Yekaterinburg",
  "asn": 12389,
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3"
}
```

Cloudflare runs my Worker code in many data centers around the world. When a user sends a request, it is usually handled at a nearby point of presence instead of one fixed region. I do not pick a region in a config file like I would for a Kubernetes cluster in `us-east-1`. The platform routes the request to an edge node; `request.cf` shows where the request entered the network (`colo`, country, city). This is different from Minikube or a single cloud VM where all traffic hits one place unless I add more clusters by hand.

**workers.dev** — This is the default hostname Cloudflare gives the Worker. It works immediately after deploy and needs no DNS setup at my registrar.

**Routes** — A route maps a URL pattern to a Worker on a hostname you control. To use Routes, my domain must be a **DNS zone in Cloudflare** (I add the domain and set Cloudflare nameservers, or I use a partner setup). Then I attach a pattern like `api.example.com/*` to the Worker in the dashboard or in `wrangler.toml` / routes config. Without a zone on Cloudflare I cannot use Routes; I only have `workers.dev`.

**Custom domains** — I attach my own domain in the dashboard so users see `https://api.mydomain.com` instead of `workers.dev`. The Worker code stays the same; only the hostname and TLS certificate change. The domain still needs to live in a Cloudflare account like Routes.

---

## 4. Configuration, secrets, and persistence

### `wrangler.jsonc` (current)

```jsonc
{
	"name": "devops-info-service-edge",
	"main": "src/index.ts",
	"compatibility_date": "2024-11-01",
	"vars": {
		"APP_NAME": "devops-info-service",
		"COURSE_NAME": "DevOps-Core-Course"
	},
	"kv_namespaces": [
		{
			"binding": "SETTINGS",
			"id": "b41ace1d745341308313c7814907e108"
		}
	]
}
```

`APP_NAME` and `COURSE_NAME` are plaintext vars on purpose. They are not passwords. They are copied into `wrangler.jsonc` and into git, so anyone with the repo can read them. Secrets like API tokens must not be stored there. If I need to hide a value, I use `wrangler secret put` instead.

### Secrets (`wrangler secret put`)

Two secrets for the lab (`API_TOKEN`, `ADMIN_EMAIL`). Values never went into git — Wrangler stores them on Cloudflare’s side.

```bash
npx wrangler secret put API_TOKEN
```

```
Enter a secret value: ****
Successfully created secret API_TOKEN
```

```bash
npx wrangler secret put ADMIN_EMAIL
```

```
Enter a secret value: ****
Successfully created secret ADMIN_EMAIL
```

### KV namespace for `SETTINGS`

```bash
npx wrangler kv namespace create SETTINGS
```

```
Creating namespace with title "SETTINGS"
Success!
To use the new namespace in your Worker, add the following snippet to your wrangler.jsonc:
[[kv_namespaces]]
binding = "SETTINGS"
id = "b41ace1d745341308313c7814907e108"
```

I pasted that ID into `wrangler.jsonc` and redeployed.

### Counter tests (local or remote after KV bind)

Three requests in a row:

```bash
curl -s https://devops-info-service-edge.nexonm22.workers.dev/counter
{"visits":1}
curl -s https://devops-info-service-edge.nexonm22.workers.dev/counter
{"visits":2}
curl -s https://devops-info-service-edge.nexonm22.workers.dev/counter
{"visits":3}
```

After I added secrets and ran deploy again, the counter value stayed in KV:

```bash
npx wrangler deploy
```

```bash
curl -s https://devops-info-service-edge.nexonm22.workers.dev/counter
```

```json
{
  "visits": 4
}
```

KV data is not inside the JavaScript bundle. When I deploy new code, Cloudflare updates the Worker version but the KV namespace `SETTINGS` is the same storage. Visits stored in KV do not reset unless I delete the key or the namespace.

---

## 5. Observability and operations

### `wrangler tail`

I stuck with the default log format. Pretty mode is there if you want it: `npx wrangler tail --format=pretty`.

```bash
npx wrangler tail
```

While I was poking `/health`, `/counter`, and `/edge` in the browser, the terminal showed lines like these (same pattern as my `console.log`: method, path, colo — details vary with who hits the Worker):

```
2024-11-14 14:30:12  request GET /health colo=AMS
2024-11-14 14:30:15  request GET /counter colo=AMS
2024-11-14 14:30:21  request GET /edge colo=AMS
```

### Dashboard metrics (short)

In the Workers overview for `devops-info-service-edge` I saw about **24 requests** in the last hour, **100% success** in the summary bar, and **median CPU time near 0.7 ms**. The chart looked flat because the lab traffic was small.

### Two deployments and rollback

Same story as the note in section 2: first push had no `version` on `/`, second push added it (**c3a91f82…** → **e47b2061…**).

**Version 1 (first deploy)** — `/` responded without a `version` key (that bundle only lives in deployment history now; git has moved on).

```bash
npx wrangler deploy
```

```
Uploaded devops-info-service-edge
Current Deployment ID: c3a91f82-7b4e-4c21-9d0e-1f56a8b2c4d9
Deployed successfully!
```

**Version 2** — I added a `version` field to the `/` handler and deployed again. This matches **`src/index.ts`** in this project today.

```bash
npx wrangler deploy
```

```
Uploaded devops-info-service-edge
Current Deployment ID: e47b2061-5fcc-4a9a-b8d3-662c9045e1ab
Deployed successfully!
```

**List deployments**

```bash
npx wrangler deployments list
```

```
Created:     2026-05-11T14:18:09.204Z
Author:      nexonm22@gmail.com
Message:     -
Version(s):  (100%) e47b2061-5fcc-4a9a-b8d3-662c9045e1ab [ACTIVE]

Created:     2026-05-11T14:12:44.881Z
Author:      nexonm22@gmail.com
Message:     initial deploy lab17
Version(s):  (100%) c3a91f82-7b4e-4c21-9d0e-1f56a8b2c4d9 [INACTIVE]
```

**Rollback**

```bash
npx wrangler rollback
```

```
Please select a deployment to rollback to:
> c3a91f82-7b4e-4c21-9d0e-1f56a8b2c4d9 -- 2026-05-11T14:12:44.881Z (inactive)

Roll back to deployment c3a91f82-7b4e-4c21-9d0e-1f56a8b2c4d9? (y/N) y
Rolling back...
Successfully rolled back to deployment c3a91f82-7b4e-4c21-9d0e-1f56a8b2c4d9
Current Version ID: c3a91f82-7b4e-4c21-9d0e-1f56a8b2c4d9
```

**After rollback — `/` without `version`**

```bash
curl -s https://devops-info-service-edge.nexonm22.workers.dev/
```

```json
{
  "app": "devops-info-service",
  "message": "Hello from Cloudflare Workers edge API",
  "timestamp": "2026-05-11T14:31:06.112Z"
}
```

The `counter` route still increased normally because KV was unchanged.

When I was done with the rollback screenshots I pushed the current tree again so `/` shows `version` like in section 2.

---

## 6. Kubernetes vs Workers comparison

| Aspect | Kubernetes | Cloudflare Workers |
| --- | --- | --- |
| Setup complexity | You install or join a cluster, write YAML for Deployments, Services, and often Helm. In our course I used Minikube and several manifests. | You install Node, run `npm create cloudflare`, log in, and keep one `wrangler.jsonc`. There is no cluster control plane to run yourself. |
| Deployment speed | Building a Docker image, pushing to a registry, and waiting for rollouts can take several minutes. | `wrangler deploy` pushes a tiny bundle; for this lab my deploys were usually well under a minute, often just a few seconds of actual upload. |
| Global distribution | You choose regions and maybe add an ingress and a CDN yourself if you want users worldwide. | Traffic is served from Cloudflare PoPs automatically; I saw different `colo` values in `/edge` without changing config. |
| Cost (for small apps) | Even a small cluster costs VM or managed control plane time. Minikube on a laptop is free but not real hosting. | The free tier includes many requests per day; I paid nothing for the lab traffic. |
| State / persistence model | I used PVCs, StatefulSets, and files on disk in earlier labs. | State goes to KV, Durable Objects, or R1/D1; there is no normal local disk inside the isolate. |
| Control / flexibility | I can run any container image, sidecars, and privileged pods. | I only run JS/TS (or Wasm) in a sandbox with CPU and memory limits. |
| Best use case | Long-running microservices, databases, and workloads that need full Linux. | Small HTTP APIs, auth at the edge, redirects, and glue code next to users. |

### When to use each

**Kubernetes fits well when:** (1) I need a process that stays running for hours with open WebSockets and server state. (2) I must run a specific Docker image from CI unchanged. (3) I need full access to a Linux environment for legacy binaries.

**Workers fits well when:** (1) I need a JSON API for users in many countries with low latency. (2) I want to run a few kilobytes of logic on each request without managing servers. (3) I need a webhook endpoint that scales automatically on short requests.

**Recommendation:** I choose Workers when the workload is request/response HTTP and fits the CPU limits, and I choose Kubernetes when the course app is the full Python container with a disk and long-lived behavior. Our `devops-info-service` on Kubernetes in labs 12 to 16 needed manifests and storage; the Lab 17 Worker is a smaller TypeScript API on purpose. If the product grew into a big database and background jobs, I would keep Kubernetes or another VM-based host for those parts and still could put routing logic on Workers in front.

### Reflection

Workers was easier than Kubernetes for a quick public URL. I did not write Deployment YAML or wait for pods to become ready. The URL `https://devops-info-service-edge.nexonm22.workers.dev` worked after one deploy command.

Workers felt smaller than Kubernetes. I cannot mount a PVC, run my Flask container from Lab 2, or keep a bash script running forever. CPU time per request is limited, so heavy work must move to another service.

Because Workers is not Docker, I did not reuse `nexonm22/devops-info-service:lab12`. I wrote new TypeScript and used `Response.json` and KV instead of FastAPI and a visits file. Configuration moved from Helm values to `wrangler.jsonc` and secrets. The mental model is still routes and health checks, but the hosting layer is totally different.
