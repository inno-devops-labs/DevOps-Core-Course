export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

type JsonValue = Record<string, unknown>;

const routes = [
  { path: "/", description: "Deployment summary and available routes" },
  { path: "/health", description: "Health check" },
  { path: "/edge", description: "Cloudflare edge request metadata" },
  { path: "/config", description: "Plaintext configuration and secret presence check" },
  { path: "/counter", description: "KV-backed persistent visit counter" },
  { path: "/admin", description: "Secret-protected endpoint using API_TOKEN" }
];

function json(data: JsonValue, init: ResponseInit = {}): Response {
  const headers = new Headers(init.headers);
  headers.set("cache-control", "no-store");

  return Response.json(data, {
    ...init,
    headers
  });
}

function getBearerToken(request: Request): string | null {
  const header = request.headers.get("authorization");

  if (!header?.startsWith("Bearer ")) {
    return null;
  }

  return header.slice("Bearer ".length).trim();
}

async function handleCounter(env: Env): Promise<Response> {
  const key = "visits";
  const rawVisits = await env.SETTINGS.get(key);
  const visits = Number.parseInt(rawVisits ?? "0", 10) + 1;

  await env.SETTINGS.put(key, String(visits));

  return json({
    key,
    visits,
    persistedIn: "Workers KV",
    note: "The value remains in the KV namespace after Worker redeploys."
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    console.log("request", {
      method: request.method,
      path: url.pathname,
      colo: request.cf?.colo,
      country: request.cf?.country
    });

    if (url.pathname === "/") {
      return json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers",
        runtime: "Cloudflare Workers edge runtime",
        routes,
        timestamp: new Date().toISOString()
      });
    }

    if (url.pathname === "/health") {
      return json({
        status: "ok",
        app: env.APP_NAME,
        timestamp: new Date().toISOString()
      });
    }

    if (url.pathname === "/edge") {
      return json({
        colo: request.cf?.colo ?? null,
        country: request.cf?.country ?? null,
        city: request.cf?.city ?? null,
        asn: request.cf?.asn ?? null,
        httpProtocol: request.cf?.httpProtocol ?? null,
        tlsVersion: request.cf?.tlsVersion ?? null,
        workersDevHost: url.hostname,
        timestamp: new Date().toISOString()
      });
    }

    if (url.pathname === "/config") {
      return json({
        appName: env.APP_NAME,
        courseName: env.COURSE_NAME,
        plaintextVarsSource: "wrangler.jsonc vars",
        apiTokenConfigured: Boolean(env.API_TOKEN),
        adminEmailConfigured: Boolean(env.ADMIN_EMAIL),
        secretValuesExposed: false,
        note: "Plaintext vars are committed in wrangler.jsonc. Secret values are read from env but never returned."
      });
    }

    if (url.pathname === "/counter") {
      return handleCounter(env);
    }

    if (url.pathname === "/admin") {
      if (getBearerToken(request) !== env.API_TOKEN) {
        return json({ error: "Unauthorized" }, { status: 401 });
      }

      return json({
        status: "authorized",
        adminEmailConfigured: Boolean(env.ADMIN_EMAIL),
        message: "The API_TOKEN secret matched the request bearer token."
      });
    }

    return json(
      {
        error: "Not Found",
        path: url.pathname,
        availableRoutes: routes.map((route) => route.path)
      },
      { status: 404 }
    );
  }
} satisfies ExportedHandler<Env>;
