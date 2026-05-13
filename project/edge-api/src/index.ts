export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

const VERSION = "1.0.0";
const COLD_START_MS = Date.now();

const ROUTES = [
  { method: "GET", path: "/", description: "App info + plaintext vars" },
  { method: "GET", path: "/health", description: "Health check" },
  { method: "GET", path: "/edge", description: "Edge metadata from request.cf" },
  { method: "GET", path: "/counter", description: "KV-backed visit counter" },
  {
    method: "GET",
    path: "/secret-check",
    description: "Reports secret presence (length only, never values)",
  },
];

function json(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body, null, 2), {
    ...init,
    headers: {
      "content-type": "application/json; charset=utf-8",
      ...(init.headers ?? {}),
    },
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;
    const cf = request.cf;

    console.log(
      JSON.stringify({
        msg: "request",
        method,
        path,
        colo: cf?.colo ?? null,
        country: cf?.country ?? null,
      }),
    );

    if (method !== "GET") {
      return json({ error: "method not allowed", method }, { status: 405 });
    }

    if (path === "/health") {
      return json({
        status: "ok",
        uptimeMs: Date.now() - COLD_START_MS,
        timestamp: new Date().toISOString(),
      });
    }

    if (path === "/") {
      return json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        version: VERSION,
        message: "Hello from Cloudflare Workers",
        timestamp: new Date().toISOString(),
        routes: ROUTES,
      });
    }

    if (path === "/edge") {
      return json({
        colo: cf?.colo ?? null,
        country: cf?.country ?? null,
        city: cf?.city ?? null,
        region: cf?.region ?? null,
        asn: cf?.asn ?? null,
        httpProtocol: cf?.httpProtocol ?? null,
        tlsVersion: cf?.tlsVersion ?? null,
      });
    }

    if (path === "/counter") {
      const previousRaw = await env.SETTINGS.get("visits");
      const previous = Number(previousRaw ?? "0");
      const next = previous + 1;
      await env.SETTINGS.put("visits", String(next));
      return json({
        visits: next,
        storedIn: "Workers KV (binding=SETTINGS, key=visits)",
        survivesRedeploy: true,
      });
    }

    if (path === "/secret-check") {
      const apiToken = env.API_TOKEN ?? "";
      const adminEmail = env.ADMIN_EMAIL ?? "";
      return json({
        apiToken: {
          configured: apiToken.length > 0,
          length: apiToken.length,
        },
        adminEmail: {
          configured: adminEmail.length > 0,
          length: adminEmail.length,
        },
        note: "values are never returned; this endpoint only proves the bindings exist",
      });
    }

    return json(
      {
        error: "not found",
        path,
        hint: "Try /, /health, /edge, /counter, or /secret-check",
      },
      { status: 404 },
    );
  },
} satisfies ExportedHandler<Env>;
