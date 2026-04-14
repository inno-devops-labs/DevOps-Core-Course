export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  COUNTER: KVNamespace;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return Response.json({ status: "ok" });
    }

    if (url.pathname === "/") {
      const raw = await env.COUNTER.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.COUNTER.put("visits", String(visits));

      return Response.json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers",
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/edge") {
      return Response.json({
        colo: request.cf?.colo,
        country: request.cf?.country,
        city: request.cf?.city,
        asn: request.cf?.asn,
        httpProtocol: request.cf?.httpProtocol,
        tlsVersion: request.cf?.tlsVersion,
      });
    }

    if (url.pathname === "/counter") {
      const raw = await env.COUNTER.get("visits");
      const visits = Number(raw ?? "0");
      return Response.json({ visits });
    }

    if (url.pathname === "/config") {
      return Response.json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        secretsConfigured: {
          apiTokenPresent: Boolean(env.API_TOKEN),
          adminEmailPresent: Boolean(env.ADMIN_EMAIL),
        },
      });
    }

    return new Response("Not Found", { status: 404 });
  },
} satisfies ExportedHandler<Env>;