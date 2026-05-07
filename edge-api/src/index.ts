export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  APP_ENV: string;
  API_TOKEN?: string;
  ADMIN_EMAIL?: string;
  SETTINGS: SettingsStore;
}

type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

interface SettingsStore {
  get(key: string): Promise<string | null>;
  put(key: string, value: string): Promise<void>;
}

interface RouteContext {
  request: Request;
  env: Env;
  url: URL;
}

const securityHeaders = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
  "x-content-type-options": "nosniff",
};

function jsonResponse(payload: JsonValue, init?: ResponseInit): Response {
  return new Response(JSON.stringify(payload, null, 2), {
    ...init,
    headers: {
      ...securityHeaders,
      ...init?.headers,
    },
  });
}

function notFound(pathname: string): Response {
  const payload = {
    error: "Not Found",
    message: `No route matches ${pathname}`,
  };
  return jsonResponse(payload, { status: 404 });
}

function getClientIp(request: Request): string | null {
  return request.headers.get("cf-connecting-ip") ?? request.headers.get("x-forwarded-for");
}

function getEdgeMetadata(request: Request): JsonValue {
  const cf = request.cf;
  return {
    colo: typeof cf?.colo === "string" ? cf.colo : null,
    country: typeof cf?.country === "string" ? cf.country : null,
    city: typeof cf?.city === "string" ? cf.city : null,
    asn: typeof cf?.asn === "number" ? cf.asn : null,
    httpProtocol: typeof cf?.httpProtocol === "string" ? cf.httpProtocol : null,
    tlsVersion: typeof cf?.tlsVersion === "string" ? cf.tlsVersion : null,
  };
}

function buildRootResponse({ request, env, url }: RouteContext): Response {
  return jsonResponse({
    app: {
      name: env.APP_NAME,
      environment: env.APP_ENV,
      course: env.COURSE_NAME,
    },
    runtime: {
      platform: "Cloudflare Workers",
      timestamp: new Date().toISOString(),
      url: url.origin,
    },
    request: {
      method: request.method,
      path: url.pathname,
      clientIp: getClientIp(request),
    },
    routes: [
      { method: "GET", path: "/" },
      { method: "GET", path: "/health" },
      { method: "GET", path: "/edge" },
      { method: "GET", path: "/counter" },
      { method: "POST", path: "/counter/reset" },
      { method: "GET", path: "/config" },
    ],
  });
}

function buildHealthResponse(env: Env): Response {
  return jsonResponse({
    status: "ok",
    app: env.APP_NAME,
    environment: env.APP_ENV,
    timestamp: new Date().toISOString(),
  });
}

function buildEdgeResponse(request: Request): Response {
  return jsonResponse({
    edge: getEdgeMetadata(request),
    request: {
      clientIp: getClientIp(request),
      userAgent: request.headers.get("user-agent"),
    },
  });
}

async function buildCounterResponse(env: Env): Promise<Response> {
  const rawVisits = await env.SETTINGS.get("visits");
  const currentVisits = Number.parseInt(rawVisits ?? "0", 10);
  const visits = Number.isFinite(currentVisits) && currentVisits >= 0 ? currentVisits + 1 : 1;
  await env.SETTINGS.put("visits", String(visits));
  return jsonResponse({
    key: "visits",
    visits,
    persisted: true,
  });
}

async function resetCounter(env: Env): Promise<Response> {
  await env.SETTINGS.put("visits", "0");
  return jsonResponse({
    key: "visits",
    visits: 0,
    persisted: true,
  });
}

function buildConfigResponse(env: Env): Response {
  return jsonResponse({
    appName: env.APP_NAME,
    courseName: env.COURSE_NAME,
    environment: env.APP_ENV,
    secrets: {
      apiTokenConfigured: Boolean(env.API_TOKEN),
      adminEmailConfigured: Boolean(env.ADMIN_EMAIL),
    },
  });
}

async function handleRequest(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  console.log("request", request.method, url.pathname, request.cf?.colo ?? "local");

  if (request.method === "GET" && url.pathname === "/") {
    return buildRootResponse({ request, env, url });
  }

  if (request.method === "GET" && url.pathname === "/health") {
    return buildHealthResponse(env);
  }

  if (request.method === "GET" && url.pathname === "/edge") {
    return buildEdgeResponse(request);
  }

  if (request.method === "GET" && url.pathname === "/counter") {
    return buildCounterResponse(env);
  }

  if (request.method === "POST" && url.pathname === "/counter/reset") {
    return resetCounter(env);
  }

  if (request.method === "GET" && url.pathname === "/config") {
    return buildConfigResponse(env);
  }

  return notFound(url.pathname);
}

export default {
  fetch(request: Request, env: Env): Promise<Response> {
    return handleRequest(request, env);
  },
};
