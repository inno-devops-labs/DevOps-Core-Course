export interface Env {
  APP_NAME: string;
  APP_VERSION: string;
  COURSE_NAME: string;

  API_TOKEN: string;
  ADMIN_EMAIL: string;

  SETTINGS: KVNamespace;
}

function json(data: unknown, status = 200): Response {
  return Response.json(data, {
    status,
    headers: {
      "Cache-Control": "no-store",
    },
  });
}

function notFound(pathname: string): Response {
  return json(
    {
      error: "Not Found",
      path: pathname,
      availableRoutes: ["/", "/health", "/edge", "/counter"],
    },
    404,
  );
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    console.log(
      "request",
      JSON.stringify({
        path: url.pathname,
        method: request.method,
        colo: request.cf?.colo,
        country: request.cf?.country,
      }),
    );

    if (request.method !== "GET") {
      return json(
        {
          error: "Method Not Allowed",
          allowedMethods: ["GET"],
        },
        405,
      );
    }

    if (url.pathname === "/health") {
      return json({ status: "ok" });
    }

    if (url.pathname === "/") {
      return json({
        app: env.APP_NAME,
        version: env.APP_VERSION,
        course: env.COURSE_NAME,
        runtime: "Cloudflare Workers",
        timestamp: new Date().toISOString(),
        config: {
          plaintextVarsConfigured: {
            APP_NAME: Boolean(env.APP_NAME),
            APP_VERSION: Boolean(env.APP_VERSION),
            COURSE_NAME: Boolean(env.COURSE_NAME),
          },
          secretsConfigured: {
            API_TOKEN: Boolean(env.API_TOKEN),
            ADMIN_EMAIL: Boolean(env.ADMIN_EMAIL),
          },
          kvBindingConfigured: Boolean(env.SETTINGS),
        },
      });
    }

    if (url.pathname === "/edge") {
      return json({
        colo: request.cf?.colo ?? null,
        country: request.cf?.country ?? null,
        city: request.cf?.city ?? null,
        asn: request.cf?.asn ?? null,
        asOrganization: request.cf?.asOrganization ?? null,
        httpProtocol: request.cf?.httpProtocol ?? null,
        tlsVersion: request.cf?.tlsVersion ?? null,
        timezone: request.cf?.timezone ?? null,
      });
    }

    if (url.pathname === "/counter") {
      const key = "visits";

      const raw = await env.SETTINGS.get(key);
      const previous = Number(raw ?? "0");
      const visits = previous + 1;

      await env.SETTINGS.put(key, String(visits));

      return json({
        key,
        previous,
        visits,
        persistedIn: "Workers KV",
        timestamp: new Date().toISOString(),
      });
    }

    return notFound(url.pathname);
  },
};
