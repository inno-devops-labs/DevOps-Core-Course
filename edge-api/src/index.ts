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

    console.log("request", url.pathname, request.cf?.colo);

    // ROOT
    if (url.pathname === "/") {
      return Response.json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
		version: "v2",
    	status: "running-v2",
        timestamp: new Date().toISOString(),
      });
    }

    // HEALTH
    if (url.pathname === "/health") {
      return Response.json({
        status: "ok",
      });
    }

    // EDGE METADATA
    if (url.pathname === "/meta") {
      return Response.json({
        colo: request.cf?.colo,
        country: request.cf?.country,
        city: request.cf?.city,
        asn: request.cf?.asn,
        httpProtocol: request.cf?.httpProtocol,
        tlsVersion: request.cf?.tlsVersion,
      });
    }

    // SECRET CHECK
    if (url.pathname === "/secrets") {
      return Response.json({
        tokenConfigured: !!env.API_TOKEN,
        adminConfigured: !!env.ADMIN_EMAIL,
      });
    }

    // KV COUNTER
    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get("visits");

      const visits = Number(raw ?? "0") + 1;

      await env.SETTINGS.put("visits", String(visits));

      return Response.json({
        visits,
      });
    }

    return new Response("Not Found", {
      status: 404,
    });
  },
};