export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

type CfData = {
  colo?: string;
  country?: string;
  city?: string;
  asn?: number;
  httpProtocol?: string;
  tlsVersion?: string;
};

const json = (body: unknown, status = 200) =>
  Response.json(body, {
    status,
    headers: {
      "cache-control": "no-store",
    },
  });

const getCfData = (request: Request): CfData => {
  const cf = (request as Request & { cf?: CfData }).cf;

  return {
    colo: cf?.colo,
    country: cf?.country,
    city: cf?.city,
    asn: cf?.asn,
    httpProtocol: cf?.httpProtocol,
    tlsVersion: cf?.tlsVersion,
  };
};

const getAdminEmailDomain = (adminEmail: string) => {
  const parts = adminEmail.split("@");
  return parts.length === 2 ? parts[1] : null;
};

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const timestamp = new Date().toISOString();
    const cf = getCfData(request);

    console.log("request", request.method, url.pathname, cf.colo ?? "unknown", cf.country ?? "unknown");

    if (url.pathname === "/") {
      return json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers",
        timestamp,
        routes: ["/", "/health", "/edge", "/counter", "/config"],
      });
    }

    if (url.pathname === "/health") {
      return json({
        status: "ok",
        service: env.APP_NAME,
        timestamp,
      });
    }

    if (url.pathname === "/edge") {
      return json({
        path: url.pathname,
        method: request.method,
        timestamp,
        colo: cf.colo ?? "unknown",
        country: cf.country ?? "unknown",
        city: cf.city ?? "unknown",
        asn: cf.asn ?? null,
        httpProtocol: cf.httpProtocol ?? "unknown",
        tlsVersion: cf.tlsVersion ?? "unknown",
      });
    }

    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;

      await env.SETTINGS.put("visits", String(visits));

      return json({
        counter: "visits",
        visits,
        persisted: true,
        timestamp,
      });
    }

    if (url.pathname === "/config") {
      return json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        hasApiToken: env.API_TOKEN.length > 0,
        adminEmailDomain: getAdminEmailDomain(env.ADMIN_EMAIL),
        kvNamespace: "SETTINGS",
        timestamp,
      });
    }

    return json(
      {
        error: "Not Found",
        availableRoutes: ["/", "/health", "/edge", "/counter", "/config"],
        timestamp,
      },
      404,
    );
  },
};
