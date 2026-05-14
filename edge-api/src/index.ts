export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

const VISITS_KEY = "visits";

export default {
  async fetch(
    request: Request,
    env: Env,
    _ctx: ExecutionContext,
  ): Promise<Response> {
    const url = new URL(request.url);
    console.log("path", url.pathname, "colo", request.cf?.colo);
    console.log("method", request.method);

    if (url.pathname === "/health") {
      return Response.json({ status: "ok" });
    }

    if (url.pathname === "/") {
      return Response.json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "edge-api worker",
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/deploy-info") {
      return Response.json({
        worker: env.APP_NAME,
        course: env.COURSE_NAME,
        runtime: "cloudflare-workers",
        compatibilityDate: "2025-05-01",
        observedAt: new Date().toISOString(),
      });
    }

    if (url.pathname === "/edge") {
      const cf = request.cf;
      return Response.json({
        colo: cf?.colo ?? null,
        country: cf?.country ?? null,
        city: cf?.city ?? null,
        asn: cf?.asn ?? null,
        httpProtocol: cf?.httpProtocol ?? null,
        tlsVersion: cf?.tlsVersion ?? null,
      });
    }

    if (url.pathname === "/secrets-status") {
      return Response.json({
        apiTokenConfigured: Boolean(env.API_TOKEN?.length),
        adminEmailConfigured: Boolean(env.ADMIN_EMAIL?.length),
        apiTokenLength: env.API_TOKEN?.length ?? 0,
      });
    }

    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get(VISITS_KEY);
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put(VISITS_KEY, String(visits));
      return Response.json({ visits, key: VISITS_KEY });
    }

    return new Response("Not Found", { status: 404 });
  },
};
