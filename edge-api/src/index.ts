export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  DEPLOYMENT_LABEL: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

const VISITS_KEY = "visits";

async function deploymentChecksum(env: Env): Promise<string> {
  const apiToken = env.API_TOKEN ?? "";
  const adminEmail = env.ADMIN_EMAIL ?? "";
  const data = new TextEncoder().encode(
    `${env.APP_NAME}|${env.COURSE_NAME}|${apiToken.length}|${adminEmail.length}`,
  );
  const buf = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(buf)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("")
    .slice(0, 16);
}

export default {
  async fetch(request: Request, env: Env, _ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    console.log("request", {
      path: url.pathname,
      method: request.method,
      colo: request.cf?.colo,
    });

    if (url.pathname === "/health") {
      return Response.json({ status: "ok", timestamp: new Date().toISOString() });
    }

    if (url.pathname === "/") {
      return Response.json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers",
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/meta") {
      const secretsConfigured = Boolean(env.API_TOKEN && env.ADMIN_EMAIL);
      return Response.json({
        worker: "edge-api",
        appName: env.APP_NAME,
        course: env.COURSE_NAME,
        deploymentLabel: env.DEPLOYMENT_LABEL,
        secretsConfigured,
        deploymentChecksum: await deploymentChecksum(env),
        timestamp: new Date().toISOString(),
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

    if (url.pathname === "/counter" && request.method === "GET") {
      const raw = await env.SETTINGS.get(VISITS_KEY);
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put(VISITS_KEY, String(visits));
      return Response.json({ visits, key: VISITS_KEY });
    }

    return Response.json({ error: "Not Found" }, { status: 404 });
  },
};
