export interface Env {
  APP_NAME: string;
  APP_VERSION: string;
  COURSE_NAME: string;

  // Secrets (set via `wrangler secret put ...`)
  API_TOKEN: string;
  ADMIN_EMAIL: string;

  // KV namespace binding (configured in `wrangler.jsonc`)
  SETTINGS: KVNamespace;
}

function json(data: unknown, init?: ResponseInit) {
  return Response.json(data, {
    headers: {
      "cache-control": "no-store",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
}

function methodNotAllowed(allowed: string[]) {
  return json(
    { error: "method_not_allowed", allowed },
    { status: 405, headers: { allow: allowed.join(", ") } },
  );
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";

    console.log("request", {
      method: request.method,
      path,
      colo: request.cf?.colo,
      country: request.cf?.country,
      httpProtocol: request.cf?.httpProtocol,
    });

    if (path === "/health") {
      if (request.method !== "GET") return methodNotAllowed(["GET"]);
      return json({ status: "ok", timestamp: new Date().toISOString() });
    }

    if (path === "/") {
      if (request.method !== "GET") return methodNotAllowed(["GET"]);
      return json({
        app: env.APP_NAME,
        version: env.APP_VERSION,
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers",
        routes: ["/", "/health", "/meta", "/edge", "/counter", "/settings/:key"],
        timestamp: new Date().toISOString(),
      });
    }

    if (path === "/meta") {
      if (request.method !== "GET") return methodNotAllowed(["GET"]);
      return json({
        app: env.APP_NAME,
        version: env.APP_VERSION,
        course: env.COURSE_NAME,
        url: request.url,
        method: request.method,
        now: new Date().toISOString(),
        runtime: "cloudflare-workers",
      });
    }

    if (path === "/edge") {
      if (request.method !== "GET") return methodNotAllowed(["GET"]);
      return json({
        colo: request.cf?.colo,
        country: request.cf?.country,
        city: request.cf?.city,
        asn: request.cf?.asn,
        asOrganization: request.cf?.asOrganization,
        httpProtocol: request.cf?.httpProtocol,
        tlsVersion: request.cf?.tlsVersion,
        timezone: request.cf?.timezone,
        region: request.cf?.region,
      });
    }

    if (path === "/counter") {
      if (request.method !== "POST" && request.method !== "GET") {
        return methodNotAllowed(["GET", "POST"]);
      }

      const key = "visits";
      if (request.method === "GET") {
        const raw = await env.SETTINGS.get(key);
        return json({ key, value: Number(raw ?? "0") });
      }

      const raw = await env.SETTINGS.get(key);
      const next = Number(raw ?? "0") + 1;
      ctx.waitUntil(env.SETTINGS.put(key, String(next)));
      return json({ visits: next });
    }

    const settingsMatch = path.match(/^\/settings\/([^/]+)$/);
    if (settingsMatch) {
      const key = decodeURIComponent(settingsMatch[1]);

      if (request.method === "GET") {
        const value = await env.SETTINGS.get(key);
        return json({ key, value });
      }

      if (request.method === "PUT") {
        const token = request.headers.get("authorization")?.replace(/^Bearer\s+/i, "") ?? "";
        if (!token || token !== env.API_TOKEN) {
          return json({ error: "unauthorized" }, { status: 401 });
        }

        const contentType = request.headers.get("content-type") ?? "";
        const value =
          contentType.includes("application/json")
            ? JSON.stringify(await request.json())
            : await request.text();

        await env.SETTINGS.put(key, value);
        return json({ ok: true, key });
      }

      return methodNotAllowed(["GET", "PUT"]);
    }

    if (path === "/debug/secrets") {
      if (request.method !== "GET") return methodNotAllowed(["GET"]);
      return json({
        adminEmailConfigured: Boolean(env.ADMIN_EMAIL),
        apiTokenConfigured: Boolean(env.API_TOKEN),
      });
    }

    return json({ error: "not_found", path }, { status: 404 });
  },
};
