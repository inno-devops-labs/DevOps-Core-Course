interface Env {
  APP_NAME: string;
  ENVIRONMENT: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  COUNTER_KV: KVNamespace;
}

const COUNTER_KEY = "global:counter";
const COUNTER_CONCURRENCY_NOTE =
  "KV read-modify-write increment is non-atomic; concurrent POST /counter requests may drop increments. For strict monotonic increments use Durable Objects or another atomic primitive.";

function json(data: unknown, init: ResponseInit = {}): Response {
  return Response.json(data, {
    headers: {
      "cache-control": "no-store"
    },
    ...init
  });
}

async function readCounter(kv: KVNamespace): Promise<number> {
  const raw = await kv.get(COUNTER_KEY);
  if (!raw) {
    return 0;
  }

  const parsed = Number.parseInt(raw, 10);
  return Number.isNaN(parsed) ? 0 : parsed;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    console.log("request", {
      method: request.method,
      path: url.pathname,
      colo: request.cf?.colo ?? "unknown"
    });

    if (url.pathname === "/") {
      return json({
        app: env.APP_NAME,
        environment: env.ENVIRONMENT,
        message: "Hello from Cloudflare Workers",
        routes: ["/", "/health", "/edge", "/counter"],
        secrets: {
          apiTokenConfigured: Boolean(env.API_TOKEN),
          adminEmailConfigured: Boolean(env.ADMIN_EMAIL)
        },
        timestamp: new Date().toISOString()
      });
    }

    if (url.pathname === "/health") {
      return json({
        status: "ok",
        service: env.APP_NAME,
        secrets: {
          apiTokenConfigured: Boolean(env.API_TOKEN),
          adminEmailConfigured: Boolean(env.ADMIN_EMAIL)
        },
        timestamp: new Date().toISOString()
      });
    }

    if (url.pathname === "/edge") {
      const cf = request.cf ?? {};
      return json({
        colo: cf.colo ?? null,
        country: cf.country ?? null,
        city: cf.city ?? null,
        asn: cf.asn ?? null,
        httpProtocol: cf.httpProtocol ?? null,
        tlsVersion: cf.tlsVersion ?? null,
        timestamp: new Date().toISOString()
      });
    }

    if (url.pathname === "/counter") {
      if (request.method === "GET") {
        const value = await readCounter(env.COUNTER_KV);
        return json({ key: COUNTER_KEY, value, note: COUNTER_CONCURRENCY_NOTE });
      }

      if (request.method === "POST") {
        // Contract: increment here is best-effort only because KV lacks atomic increment.
        const current = await readCounter(env.COUNTER_KV);
        const next = current + 1;
        await env.COUNTER_KV.put(COUNTER_KEY, String(next));
        return json(
          { key: COUNTER_KEY, value: next, note: COUNTER_CONCURRENCY_NOTE },
          { status: 201 }
        );
      }

      if (request.method === "DELETE") {
        await env.COUNTER_KV.delete(COUNTER_KEY);
        return json({ key: COUNTER_KEY, value: 0, reset: true });
      }

      return json({ error: "Method Not Allowed" }, { status: 405 });
    }

    return json({ error: "Not Found", path: url.pathname }, { status: 404 });
  }
};
