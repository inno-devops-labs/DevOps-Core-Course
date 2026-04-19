export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  APP_VERSION: string;
  DEFAULT_COUNTER_KEY: string;
  API_TOKEN?: string;
  ADMIN_EMAIL?: string;
  SETTINGS?: KVNamespace;
}

type JsonRecord = Record<string, unknown>;

function json(data: JsonRecord, init?: ResponseInit): Response {
  return Response.json(data, {
    headers: {
      "cache-control": "no-store",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
}

function notFound(pathname: string): Response {
  return json(
    {
      error: "Not Found",
      message: `No route defined for ${pathname}`,
    },
    { status: 404 },
  );
}

function methodNotAllowed(method: string): Response {
  return json(
    {
      error: "Method Not Allowed",
      method,
    },
    { status: 405 },
  );
}

function getCf(request: Request): Record<string, unknown> {
  return ((request as Request & { cf?: Record<string, unknown> }).cf ?? {}) as Record<
    string,
    unknown
  >;
}

function baseUrl(request: Request): string {
  return new URL(request.url).origin;
}

async function readJsonBody(request: Request): Promise<JsonRecord> {
  try {
    const body = await request.json<JsonRecord>();
    if (!body || Array.isArray(body)) {
      return {};
    }
    return body;
  } catch {
    return {};
  }
}

function kvAvailable(env: Env): env is Env & { SETTINGS: KVNamespace } {
  return typeof env.SETTINGS !== "undefined";
}

async function handleKv(request: Request, env: Env): Promise<Response> {
  if (!kvAvailable(env)) {
    return json(
      {
        error: "KV binding missing",
        message: "Bind SETTINGS in wrangler.jsonc before using persisted endpoints.",
      },
      { status: 503 },
    );
  }

  const url = new URL(request.url);

  if (request.method === "GET") {
    const key = url.searchParams.get("key") ?? env.DEFAULT_COUNTER_KEY;
    const value = await env.SETTINGS.get(key);
    return json({
      key,
      value,
      found: value !== null,
      persisted: true,
    });
  }

  if (request.method === "POST") {
    const body = await readJsonBody(request);
    const key = typeof body.key === "string" && body.key.length > 0 ? body.key : env.DEFAULT_COUNTER_KEY;
    const value =
      typeof body.value === "string" || typeof body.value === "number" || typeof body.value === "boolean"
        ? String(body.value)
        : null;

    if (value === null) {
      return json(
        {
          error: "Invalid payload",
          message: "Expected JSON with string/number/boolean value.",
        },
        { status: 400 },
      );
    }

    await env.SETTINGS.put(key, value);
    return json(
      {
        key,
        value,
        persisted: true,
      },
      { status: 201 },
    );
  }

  return methodNotAllowed(request.method);
}

async function handleCounter(env: Env): Promise<Response> {
  if (!kvAvailable(env)) {
    return json(
      {
        error: "KV binding missing",
        message: "Bind SETTINGS in wrangler.jsonc before using the counter endpoint.",
      },
      { status: 503 },
    );
  }

  const key = env.DEFAULT_COUNTER_KEY;
  const raw = await env.SETTINGS.get(key);
  const visits = Number(raw ?? "0") + 1;
  await env.SETTINGS.put(key, String(visits));

  return json({
    key,
    visits,
    persisted: true,
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const cf = getCf(request);

    console.log("edge-api request", {
      method: request.method,
      path: url.pathname,
      colo: cf.colo,
      country: cf.country,
    });

    if (request.method !== "GET" && request.method !== "POST") {
      return methodNotAllowed(request.method);
    }

    if (url.pathname === "/" && request.method === "GET") {
      return json({
        app: env.APP_NAME,
        message: "Hello from Cloudflare Workers",
        course: env.COURSE_NAME,
        timestamp: new Date().toISOString(),
        deployment: {
          platform: "Cloudflare Workers",
          version: env.APP_VERSION,
          runtime: "edge",
          workersDevUrlHint: `${baseUrl(request)}/`,
        },
        routes: [
          { method: "GET", path: "/" },
          { method: "GET", path: "/health" },
          { method: "GET", path: "/edge" },
          { method: "GET", path: "/config" },
          { method: "GET", path: "/counter" },
          { method: "GET", path: "/kv?key=visits" },
          { method: "POST", path: "/kv" },
        ],
      });
    }

    if (url.pathname === "/health" && request.method === "GET") {
      return json({
        status: "ok",
        app: env.APP_NAME,
        version: env.APP_VERSION,
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/edge" && request.method === "GET") {
      return json({
        colo: cf.colo ?? null,
        country: cf.country ?? null,
        city: cf.city ?? null,
        asn: cf.asn ?? null,
        region: cf.region ?? null,
        httpProtocol: cf.httpProtocol ?? null,
        tlsVersion: cf.tlsVersion ?? null,
        botManagementScore: cf.botManagement ? (cf.botManagement as Record<string, unknown>).score ?? null : null,
        request: {
          hostname: url.hostname,
          pathname: url.pathname,
          method: request.method,
          userAgent: request.headers.get("user-agent"),
        },
      });
    }

    if (url.pathname === "/config" && request.method === "GET") {
      return json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        version: env.APP_VERSION,
        defaults: {
          counterKey: env.DEFAULT_COUNTER_KEY,
        },
        secretsConfigured: {
          apiToken: Boolean(env.API_TOKEN),
          adminEmail: Boolean(env.ADMIN_EMAIL),
        },
        explanation: {
          plaintextVars: "Safe for non-sensitive configuration committed to Git.",
          secrets: "Sensitive values injected by Wrangler and not committed to the repository.",
        },
      });
    }

    if (url.pathname === "/kv") {
      return handleKv(request, env);
    }

    if (url.pathname === "/counter" && request.method === "GET") {
      return handleCounter(env);
    }

    return notFound(url.pathname);
  },
};
