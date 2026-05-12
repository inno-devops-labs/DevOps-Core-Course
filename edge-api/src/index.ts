export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  LAB_ID: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

type JsonBody = Record<string, unknown>;

const jsonHeaders = {
  "content-type": "application/json;charset=UTF-8",
  "cache-control": "no-store",
};

function json(body: JsonBody, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body, null, 2), {
    ...init,
    headers: {
      ...jsonHeaders,
      ...init.headers,
    },
  });
}

function notFound(pathname: string): Response {
  return json(
    {
      error: "not_found",
      message: `No route registered for ${pathname}`,
      routes: ["/", "/health", "/edge", "/config", "/counter"],
    },
    { status: 404 },
  );
}

function getSecretStatus(env: Env): JsonBody {
  return {
    apiTokenConfigured: Boolean(env.API_TOKEN),
    adminEmailConfigured: Boolean(env.ADMIN_EMAIL),
    adminEmailDomain: env.ADMIN_EMAIL?.includes("@")
      ? env.ADMIN_EMAIL.split("@").at(1)
      : null,
  };
}

async function handleCounter(env: Env): Promise<Response> {
  const key = "visits";
  const current = Number((await env.SETTINGS.get(key)) ?? "0");
  const visits = Number.isFinite(current) ? current + 1 : 1;

  await env.SETTINGS.put(key, String(visits), {
    metadata: {
      updatedBy: env.APP_NAME,
      updatedAt: new Date().toISOString(),
    },
  });

  return json({
    key,
    visits,
    persistedIn: "Workers KV",
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    console.log(
      JSON.stringify({
        path: url.pathname,
        method: request.method,
        colo: request.cf?.colo ?? "local",
        country: request.cf?.country ?? "local",
      }),
    );

    if (request.method !== "GET") {
      return json(
        {
          error: "method_not_allowed",
          allowedMethods: ["GET"],
        },
        {
          status: 405,
          headers: { allow: "GET" },
        },
      );
    }

    if (url.pathname === "/health") {
      return json({
        status: "ok",
        app: env.APP_NAME,
        timestamp: new Date().toISOString(),
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
        timezone: request.cf?.timezone ?? null,
      });
    }

    if (url.pathname === "/config") {
      return json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        lab: env.LAB_ID,
        plaintextVars: ["APP_NAME", "COURSE_NAME", "LAB_ID"],
        secrets: getSecretStatus(env),
        note: "Plaintext vars are committed in wrangler.jsonc; secret values are only stored in Cloudflare and are never returned by this API.",
      });
    }

    if (url.pathname === "/counter") {
      return handleCounter(env);
    }

    if (url.pathname === "/") {
      return json({
        app: env.APP_NAME,
        message: "Hello from Cloudflare Workers",
        deployment: {
          platform: "Cloudflare Workers",
          urlType: "workers.dev",
          runtime: "edge serverless",
        },
        routes: ["/health", "/edge", "/config", "/counter"],
        timestamp: new Date().toISOString(),
      });
    }

    return notFound(url.pathname);
  },
} satisfies ExportedHandler<Env>;

