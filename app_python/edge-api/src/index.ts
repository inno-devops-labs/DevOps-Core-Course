export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  VERSION: string;
  API_TOKEN?: string;
  ADMIN_EMAIL?: string;
  SETTINGS: KVNamespace;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    console.log("incoming request", {
      method: request.method,
      path: url.pathname,
      colo: request.cf?.colo,
      country: request.cf?.country,
      timestamp: new Date().toISOString(),
    });

    // Health check endpoint
    if (url.pathname === "/health") {
      return Response.json(
        {
          status: "ok",
          timestamp: new Date().toISOString(),
          colo: request.cf?.colo,
        },
        { status: 200 },
      );
    }

    // Home endpoint
    if (url.pathname === "/") {
      return Response.json(
        {
          app: env.APP_NAME,
          version: env.VERSION,
          course: env.COURSE_NAME,
          message: "Hello from Cloudflare Workers Edge",
          timestamp: new Date().toISOString(),
        },
        { status: 200 },
      );
    }

    // App info endpoint
    if (url.pathname === "/app-info") {
      return Response.json(
        {
          app: env.APP_NAME,
          version: env.VERSION,
          course: env.COURSE_NAME,
          environment: "production",
          runtime: "cloudflare-workers",
          timestamp: new Date().toISOString(),
        },
        { status: 200 },
      );
    }

    // Edge metadata endpoint
    if (url.pathname === "/edge") {
      return Response.json(
        {
          colo: request.cf?.colo,
          country: request.cf?.country,
          city: request.cf?.city,
          asn: request.cf?.asn,
          httpProtocol: request.cf?.httpProtocol,
          tlsVersion: request.cf?.tlsVersion,
          continent: request.cf?.continent,
          latitude: request.cf?.latitude,
          longitude: request.cf?.longitude,
        },
        { status: 200 },
      );
    }

    // Admin endpoint (with secret check)
    if (url.pathname === "/admin") {
      return Response.json(
        {
          admin: env.ADMIN_EMAIL || "admin@example.com",
          hasToken: !!env.API_TOKEN,
          message: "Admin endpoint - protected by secret",
          timestamp: new Date().toISOString(),
        },
        { status: 200 },
      );
    }

    // Persistent counter using KV
    if (url.pathname === "/counter") {
      try {
        const raw = await env.SETTINGS.get("visits");
        const visits = Number(raw ?? "0") + 1;
        await env.SETTINGS.put("visits", String(visits));

        return Response.json(
          {
            visits,
            message: "Counter persisted in KV",
            timestamp: new Date().toISOString(),
          },
          { status: 200 },
        );
      } catch (error) {
        console.error("Counter error:", error);
        return Response.json(
          {
            error: "KV not available in local development",
            visits: 0,
          },
          { status: 200 },
        );
      }
    }

    // 404 for unknown routes
    return Response.json(
      {
        error: "Not found",
        path: url.pathname,
        available: ["/", "/health", "/app-info", "/edge", "/counter", "/admin"],
      },
      { status: 404 },
    );
  },
};
