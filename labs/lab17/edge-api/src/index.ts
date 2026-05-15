/**
 * Welcome to Cloudflare Workers! This is your first worker.
 *
 * - Run `npm run dev` in your terminal to start a development server
 * - Open a browser tab at http://localhost:8787/ to see your worker in action
 * - Run `npm run deploy` to publish your worker
 *
 * Bind resources to your worker in `wrangler.jsonc`. After adding bindings, a type definition for the
 * `Env` object can be regenerated with `npm run cf-typegen`.
 *
 * Learn more at https://developers.cloudflare.com/workers/
 */

export interface Env {
  APP_NAME: string;
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

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    console.log("request", {
      path: url.pathname,
      colo: request.cf?.colo,
      country: request.cf?.country,
    });

    if (url.pathname === "/") {
      return json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers",
        timestamp: new Date().toISOString(),
        routes: [
          "/",
          "/health",
          "/edge",
          "/config",
          "/counter",
          "/kv"
        ],
      });
    }

    if (url.pathname === "/health") {
      return json({
        status: "ok",
        service: env.APP_NAME,
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
        appName: env.APP_NAME,
        courseName: env.COURSE_NAME,
        adminEmailConfigured: Boolean(env.ADMIN_EMAIL),
        apiTokenConfigured: Boolean(env.API_TOKEN),
        note: "Secrets are configured through Wrangler.",
      });
    }

    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;

      await env.SETTINGS.put("visits", String(visits));

      return json({
        visits,
        persisted: true,
        storage: "Workers KV",
      });
    }

    if (url.pathname === "/kv") {
      const value = await env.SETTINGS.get("visits");

      return json({
        key: "visits",
        value: value ?? "not-set",
      });
    }

    return json(
      {
        error: "Not Found",
        path: url.pathname,
      },
      404,
    );
  },
};
