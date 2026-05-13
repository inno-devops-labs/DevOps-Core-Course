export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    console.log("path", url.pathname, "colo", request.cf?.colo, "country", request.cf?.country);

    if (url.pathname === "/") {
      return Response.json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers edge",
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/health") {
      return Response.json({ status: "ok" });
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
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));
      return Response.json({ visits });
    }

    if (url.pathname === "/info") {
      return Response.json({
        app: env.APP_NAME,
        admin: env.ADMIN_EMAIL,
        runtime: "Cloudflare Workers",
        routes: ["/", "/health", "/edge", "/counter", "/info"],
      });
    }

    return new Response("Not Found", { status: 404 });
  },
};
