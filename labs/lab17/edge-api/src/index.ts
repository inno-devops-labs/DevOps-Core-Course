type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

type Handler = (request: Request, env: Env) => Promise<Response> | Response;

const json = (body: JsonValue, init: ResponseInit = {}): Response =>
  Response.json(body, {
    headers: {
      "cache-control": "no-store",
      ...init.headers,
    },
    ...init,
  });

const notFound = (path: string): Response =>
  json(
    {
      error: "not_found",
      message: `No route registered for ${path}`,
    },
    { status: 404 },
  );

const getRouteList = (): JsonValue[] => [
  { path: "/", method: "GET", description: "API summary and routes" },
  { path: "/health", method: "GET", description: "Health check" },
  { path: "/edge", method: "GET", description: "Cloudflare edge request metadata" },
  { path: "/config", method: "GET", description: "Plaintext Worker vars" },
  { path: "/secrets", method: "GET", description: "Secret binding presence check" },
  { path: "/counter", method: "GET", description: "KV-backed persistent counter" },
];

const textOrNull = (value: unknown): string | null =>
  typeof value === "string" ? value : null;

const numberOrNull = (value: unknown): number | null =>
  typeof value === "number" ? value : null;

const root: Handler = (_request, env) =>
  json({
    app: env.APP_NAME,
    course: env.COURSE_NAME,
    environment: env.DEPLOYMENT_ENV,
    runtime: "cloudflare-workers",
    routes: getRouteList(),
    timestamp: new Date().toISOString(),
  });

const health: Handler = () =>
  json({
    status: "ok",
    service: "devops-edge-api",
    timestamp: new Date().toISOString(),
  });

const edge: Handler = (request) => {
  const cf = request.cf;

  return json({
    colo: textOrNull(cf?.colo) ?? "local",
    country: textOrNull(cf?.country) ?? "local",
    city: textOrNull(cf?.city),
    asn: numberOrNull(cf?.asn),
    httpProtocol: textOrNull(cf?.httpProtocol),
    tlsVersion: textOrNull(cf?.tlsVersion),
    timezone: textOrNull(cf?.timezone),
  });
};

const config: Handler = (_request, env) =>
  json({
    app: env.APP_NAME,
    course: env.COURSE_NAME,
    deploymentEnvironment: env.DEPLOYMENT_ENV,
    note: "These values are plaintext Worker vars. Secrets are checked by presence only.",
  });

const secrets: Handler = (_request, env) =>
  json({
    apiTokenConfigured: Boolean(env.API_TOKEN),
    adminEmailConfigured: Boolean(env.ADMIN_EMAIL),
  });

const counter: Handler = async (_request, env) => {
  const key = "visits";
  const current = Number((await env.SETTINGS.get(key)) ?? "0");
  const visits = Number.isFinite(current) ? current + 1 : 1;

  await env.SETTINGS.put(key, String(visits));

  return json({
    key,
    visits,
    persistedIn: "Workers KV",
  });
};

const routes = new Map<string, Handler>([
  ["/", root],
  ["/health", health],
  ["/edge", edge],
  ["/config", config],
  ["/secrets", secrets],
  ["/counter", counter],
]);

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const handler = routes.get(url.pathname);

    console.log("request", {
      path: url.pathname,
      method: request.method,
      colo: request.cf?.colo ?? "local",
    });

    if (request.method !== "GET") {
      return json(
        {
          error: "method_not_allowed",
          allowedMethods: ["GET"],
        },
        { status: 405, headers: { allow: "GET" } },
      );
    }

    return handler ? handler(request, env) : notFound(url.pathname);
  },
};
