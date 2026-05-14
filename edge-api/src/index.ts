export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  APP_VERSION: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

function json(payload: JsonValue, init: ResponseInit = {}): Response {
  const headers = new Headers(init.headers);
  headers.set("content-type", "application/json; charset=utf-8");

  return new Response(JSON.stringify(payload, null, 2), {
    ...init,
    headers,
  });
}

function getClientIp(request: Request): string | null {
  return request.headers.get("cf-connecting-ip") ?? request.headers.get("x-forwarded-for");
}

function cfValue(value: unknown): JsonValue {
  if (
    value === null ||
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return value;
  }

  return null;
}

async function handleCounter(env: Env): Promise<Response> {
  const raw = await env.SETTINGS.get("visits");
  const visits = Number.parseInt(raw ?? "0", 10) + 1;

  await env.SETTINGS.put("visits", String(visits));

  return json({
    key: "visits",
    visits,
    persisted: true,
    storage: "Cloudflare Workers KV",
    timestamp: new Date().toISOString(),
  });
}

async function handleSettings(request: Request, env: Env): Promise<Response> {
  if (request.method === "GET") {
    const value = await env.SETTINGS.get("deployment-note");
    return json({
      key: "deployment-note",
      value,
      exists: value !== null,
    });
  }

  if (request.method === "PUT") {
    const body = await request.json<{ value?: unknown }>().catch(() => null);
    const value = typeof body?.value === "string" ? body.value : "";

    if (!value) {
      return json(
        {
          error: "Bad Request",
          message: "Expected JSON body with a non-empty string field: value",
        },
        { status: 400 },
      );
    }

    await env.SETTINGS.put("deployment-note", value);
    return json({
      key: "deployment-note",
      value,
      stored: true,
    });
  }

  return json(
    {
      error: "Method Not Allowed",
      allowed: ["GET", "PUT"],
    },
    {
      status: 405,
      headers: {
        allow: "GET, PUT",
      },
    },
  );
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    console.log("request", {
      method: request.method,
      path: url.pathname,
      colo: request.cf?.colo,
      country: request.cf?.country,
    });

    if (url.pathname === "/health") {
      return json({
        status: "ok",
        app: env.APP_NAME,
        version: env.APP_VERSION,
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/edge") {
      return json({
        colo: cfValue(request.cf?.colo),
        country: cfValue(request.cf?.country),
        city: cfValue(request.cf?.city),
        asn: cfValue(request.cf?.asn),
        httpProtocol: cfValue(request.cf?.httpProtocol),
        tlsVersion: cfValue(request.cf?.tlsVersion),
        clientIpPresent: getClientIp(request) !== null,
      });
    }

    if (url.pathname === "/counter") {
      return handleCounter(env);
    }

    if (url.pathname === "/settings") {
      return handleSettings(request, env);
    }

    if (url.pathname === "/config") {
      return json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        version: env.APP_VERSION,
        adminEmailConfigured: Boolean(env.ADMIN_EMAIL),
        apiTokenConfigured: Boolean(env.API_TOKEN),
        note: "Secret values are read from env bindings but are not returned.",
      });
    }

    if (url.pathname === "/") {
      ctx.waitUntil(env.SETTINGS.put("last-request-path", url.pathname));

      return json({
        service: {
          name: env.APP_NAME,
          version: env.APP_VERSION,
          course: env.COURSE_NAME,
          runtime: "Cloudflare Workers",
        },
        routes: [
          { path: "/", method: "GET", description: "Service metadata" },
          { path: "/health", method: "GET", description: "Health check" },
          { path: "/edge", method: "GET", description: "Cloudflare edge request metadata" },
          { path: "/config", method: "GET", description: "Plain vars and secret presence" },
          { path: "/counter", method: "GET", description: "KV-backed persistent counter" },
          { path: "/settings", method: "GET", description: "Read KV deployment note" },
          { path: "/settings", method: "PUT", description: "Store KV deployment note" },
        ],
        timestamp: new Date().toISOString(),
      });
    }

    return json(
      {
        error: "Not Found",
        path: url.pathname,
      },
      { status: 404 },
    );
  },
};
