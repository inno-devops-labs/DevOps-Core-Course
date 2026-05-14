export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

export default {
  async fetch(
    request: Request,
    env: Env,
    ctx: ExecutionContext,
  ): Promise<Response> {
    const url = new URL(request.url);

    console.log(
      "request",
      request.method,
      url.pathname,
      "colo",
      request.cf?.colo,
    );

    // CORS headers for all responses
    const headers = {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
    };

    // ── GET / ────────────────────────────────────────────────────────────────
    if (url.pathname === "/") {
      return Response.json(
        {
          app: env.APP_NAME,
          course: env.COURSE_NAME,
          message: "Hello from Cloudflare Workers edge!",
          author: "Mikhail Panteleev",
          version: "2",
          timestamp: new Date().toISOString(),
          routes: ["/", "/health", "/edge", "/counter", "/info"],
        },
        { headers },
      );
    }

    // ── GET /health ──────────────────────────────────────────────────────────
    if (url.pathname === "/health") {
      return Response.json(
        {
          status: "ok",
          timestamp: new Date().toISOString(),
        },
        { headers },
      );
    }

    // ── GET /edge ────────────────────────────────────────────────────────────
    if (url.pathname === "/edge") {
      return Response.json(
        {
          colo: request.cf?.colo,
          country: request.cf?.country,
          city: request.cf?.city,
          asn: request.cf?.asn,
          httpProtocol: request.cf?.httpProtocol,
          tlsVersion: request.cf?.tlsVersion,
          clientTrustScore: request.cf?.clientTrustScore,
        },
        { headers },
      );
    }

    // ── GET /info ────────────────────────────────────────────────────────────
    if (url.pathname === "/info") {
      return Response.json(
        {
          app: env.APP_NAME,
          course: env.COURSE_NAME,
          admin: env.ADMIN_EMAIL,
          // API_TOKEN is deliberately not exposed — just confirms it's set
          apiTokenConfigured: Boolean(env.API_TOKEN),
          runtime: "Cloudflare Workers",
          region: "Global (auto-distributed)",
        },
        { headers },
      );
    }

    // ── GET /counter ─────────────────────────────────────────────────────────
    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));

      console.log("counter incremented to", visits);

      return Response.json({ visits }, { headers });
    }

    // ── GET /counter/reset ───────────────────────────────────────────────────
    if (url.pathname === "/counter/reset" && request.method === "POST") {
      await env.SETTINGS.put("visits", "0");
      return Response.json({ visits: 0, reset: true }, { headers });
    }

    // ── 404 ──────────────────────────────────────────────────────────────────
    return Response.json(
      { error: "Not Found", path: url.pathname },
      { status: 404, headers },
    );
  },
};
