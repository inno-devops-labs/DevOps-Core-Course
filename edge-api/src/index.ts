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
    console.log("path", url.pathname, "colo", request.cf?.colo);

    if (url.pathname === "/health") {
      return Response.json({
        status: "ok",
        app: env.APP_NAME,
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/") {
      return Response.json({
        app: env.APP_NAME,
        version: "1.1.0",
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers",
        admin: env.ADMIN_EMAIL ? maskEmail(env.ADMIN_EMAIL) : null,
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/version") {
      return Response.json({ app: env.APP_NAME, version: "1.1.0" });
    }

    if (url.pathname === "/edge") {
      return Response.json({
        colo: request.cf?.colo,
        country: request.cf?.country,
        city: request.cf?.city,
        asn: request.cf?.asn,
        httpProtocol: request.cf?.httpProtocol,
        tlsVersion: request.cf?.tlsVersion,
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));
      return Response.json({ visits, app: env.APP_NAME });
    }

    if (url.pathname === "/admin") {
      const auth = request.headers.get("authorization") ?? "";
      const provided = auth.replace(/^Bearer\s+/i, "");
      if (!env.API_TOKEN || provided !== env.API_TOKEN) {
        return Response.json({ error: "unauthorized" }, { status: 401 });
      }
      return Response.json({
        admin: env.ADMIN_EMAIL,
        app: env.APP_NAME,
      });
    }

    return Response.json({ error: "Not Found", path: url.pathname }, { status: 404 });
  },
} satisfies ExportedHandler<Env>;

function maskEmail(email: string): string {
  const [user, domain] = email.split("@");
  if (!domain) return "***";
  const head = user.slice(0, 1);
  return `${head}***@${domain}`;
}
