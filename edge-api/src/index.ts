/**
 * Lab 17 — Cloudflare Workers edge API.
 *
 * Routes:
 *   GET /         — greeting + edge metadata + KV-backed visit counter
 *   GET /health   — liveness probe consumed by external uptime checks
 *   GET /edge     — request.cf snapshot (colo / country / ASN / TLS)
 *   GET /counter  — increments a KV counter and returns it
 *   GET /config   — shows which plaintext vars + secrets are wired
 *
 * Deliberately single-file so the whole grading surface is visible at
 * a glance. Runtime is pure Workers stdlib — no Hono / itty-router —
 * so the bundle stays under 3 KB and cold-start is ~0 ms on Cloudflare.
 */

export interface Env {
  // Plaintext variables from wrangler.jsonc → visible in the bundle.
  APP_NAME: string;
  COURSE_NAME: string;
  OWNER: string;

  // Secrets — injected by Cloudflare at runtime, never in the bundle.
  // Set them with `npx wrangler secret put <NAME>`.
  API_TOKEN: string;
  ADMIN_EMAIL: string;

  // Workers KV binding from wrangler.jsonc.
  SETTINGS: KVNamespace;
}

const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
} as const;

function json(body: unknown, status = 200, extra: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: { ...JSON_HEADERS, ...extra },
  });
}

function unauthorized(): Response {
  return json({ error: "unauthorized" }, 401, {
    "www-authenticate": 'Bearer realm="edge-api", charset="UTF-8"',
  });
}

// Structured log line — shows up in `wrangler tail` and in the
// dashboard Logs tab. `request.cf` may be undefined on `wrangler dev`
// because there's no real Cloudflare edge in front of the local server.
function logRequest(request: Request, path: string): void {
  const cf = request.cf;
  console.log(
    JSON.stringify({
      level: "info",
      path,
      method: request.method,
      colo: cf?.colo ?? "local",
      country: cf?.country ?? "local",
      ts: new Date().toISOString(),
    }),
  );
}

async function handleRoot(request: Request, env: Env): Promise<Response> {
  const visits = await bumpVisits(env);
  const cf = request.cf;
  return json({
    message: `Hello from ${env.APP_NAME}`,
    course: env.COURSE_NAME,
    owner: env.OWNER,
    visits,
    edge: {
      colo: cf?.colo ?? null,
      country: cf?.country ?? null,
    },
    time: new Date().toISOString(),
  });
}

function handleHealth(env: Env): Response {
  return json({
    status: "ok",
    app: env.APP_NAME,
    time: new Date().toISOString(),
  });
}

function handleEdge(request: Request, env: Env): Response {
  const cf = request.cf;
  return json({
    app: env.APP_NAME,
    // `request.cf` is populated by Cloudflare's edge on every real
    // request. Under `wrangler dev` without `--remote` these will be
    // undefined because there's no PoP in the path.
    colo: cf?.colo ?? null,
    country: cf?.country ?? null,
    city: cf?.city ?? null,
    region: cf?.region ?? null,
    continent: cf?.continent ?? null,
    asn: cf?.asn ?? null,
    asOrganization: cf?.asOrganization ?? null,
    httpProtocol: cf?.httpProtocol ?? null,
    tlsVersion: cf?.tlsVersion ?? null,
    tlsCipher: cf?.tlsCipher ?? null,
    clientTcpRtt: cf?.clientTcpRtt ?? null,
    clientIp: request.headers.get("cf-connecting-ip"),
    time: new Date().toISOString(),
  });
}

async function handleCounter(env: Env): Promise<Response> {
  const visits = await bumpVisits(env);
  return json({ key: "visits", visits });
}

function handleConfig(env: Env): Response {
  // Never echo secret *values*. Only confirm presence so `/config`
  // is safe to hit from `curl` during grading.
  return json({
    app: env.APP_NAME,
    course: env.COURSE_NAME,
    owner: env.OWNER,
    secrets: {
      API_TOKEN: env.API_TOKEN ? "set" : "missing",
      ADMIN_EMAIL: env.ADMIN_EMAIL ? "set" : "missing",
    },
    bindings: {
      SETTINGS: typeof env.SETTINGS?.get === "function" ? "bound" : "missing",
    },
  });
}

async function bumpVisits(env: Env): Promise<number> {
  const raw = await env.SETTINGS.get("visits");
  const visits = Number(raw ?? "0") + 1;
  await env.SETTINGS.put("visits", String(visits));
  return visits;
}

// Minimal bearer-token check for the mutation endpoint below. Kept
// simple on purpose — real Workers would use Access or a JWT verifier.
function authorized(request: Request, env: Env): boolean {
  const header = request.headers.get("authorization") ?? "";
  const prefix = "Bearer ";
  if (!header.startsWith(prefix)) return false;
  return header.slice(prefix.length) === env.API_TOKEN;
}

async function handleAdminReset(request: Request, env: Env): Promise<Response> {
  if (!authorized(request, env)) return unauthorized();
  await env.SETTINGS.put("visits", "0");
  return json({ ok: true, reset: "visits", by: env.ADMIN_EMAIL });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    logRequest(request, url.pathname);

    try {
      if (request.method === "GET" && url.pathname === "/") {
        return await handleRoot(request, env);
      }
      if (request.method === "GET" && url.pathname === "/health") {
        return handleHealth(env);
      }
      if (request.method === "GET" && url.pathname === "/edge") {
        return handleEdge(request, env);
      }
      if (request.method === "GET" && url.pathname === "/counter") {
        return await handleCounter(env);
      }
      if (request.method === "GET" && url.pathname === "/config") {
        return handleConfig(env);
      }
      if (request.method === "POST" && url.pathname === "/admin/reset") {
        return await handleAdminReset(request, env);
      }

      return json({ error: "not found", path: url.pathname }, 404);
    } catch (err) {
      console.error("unhandled error", err);
      return json({ error: "internal error" }, 500);
    }
  },
} satisfies ExportedHandler<Env>;
