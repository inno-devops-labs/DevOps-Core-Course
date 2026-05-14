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
    const start = Date.now();

    try {
      switch (url.pathname) {
        case "/":
          return handleRoot(env);
        case "/health":
          return handleHealth();
        case "/edge":
          return handleEdge(request);
        case "/counter":
          return handleCounter(env);
        default:
          return new Response(JSON.stringify({
            error: "Not Found",
            path: url.pathname,
          }), {
            status: 404,
            headers: { "Content-Type": "application/json" },
          });
      }
    } catch (err) {
      console.error("Worker error:", err);
      return Response.json({ error: "Internal Server Error" }, { status: 500 });
    } finally {
      console.log("request", url.pathname, "duration_ms", Date.now() - start);
    }
  },
};

async function handleRoot(env: Env): Promise<Response> {
  return Response.json({
    app: env.APP_NAME,
    course: env.COURSE_NAME,
    message: "Hello from Cloudflare Workers edge network",
    timestamp: new Date().toISOString(),
    uptime_ms: Date.now(),
    deployment: "global",
    version: "1.0.0",
  });
}

function handleHealth(): Response {
  return Response.json({
    status: "ok",
    timestamp: new Date().toISOString(),
  });
}

function handleEdge(request: Request): Response {
  return Response.json({
    colo: request.cf?.colo ?? "unknown",
    country: request.cf?.country ?? "unknown",
    city: request.cf?.city ?? "unknown",
    asn: request.cf?.asn ?? 0,
    httpProtocol: request.cf?.httpProtocol ?? "unknown",
    tlsVersion: request.cf?.tlsVersion ?? "unknown",
    timezone: request.cf?.timezone ?? "unknown",
    botScore: request.cf?.botManagement?.score ?? -1,
    timestamp: new Date().toISOString(),
  });
}

async function handleCounter(env: Env): Promise<Response> {
  const raw = await env.SETTINGS.get("visits");
  const visits = Number(raw ?? "0") + 1;
  await env.SETTINGS.put("visits", String(visits));

  return Response.json({
    visits,
    storage: "KV",
    namespace: "SETTINGS",
    timestamp: new Date().toISOString(),
  });
}
