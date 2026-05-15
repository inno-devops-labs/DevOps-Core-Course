interface KVBinding {
  get(key: string): Promise<string | null>;
  put(key: string, value: string): Promise<void>;
}

export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  APP_VERSION: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVBinding;
}

interface RequestCfMetadata {
  asn?: number;
  city?: string | null;
  colo?: string;
  country?: string;
  httpProtocol?: string;
  tlsVersion?: string;
}

type CloudflareRequest = Request & {
  cf?: RequestCfMetadata;
};

type JsonRecord = Record<string, unknown>;

const COUNTER_KEY = "visits";

const ROUTES = [
  {
    path: "/",
    method: "GET",
    description: "Course-service style metadata for the Worker deployment"
  },
  {
    path: "/health",
    method: "GET",
    description: "Health check with UTC timestamp"
  },
  {
    path: "/edge",
    method: "GET",
    description: "Cloudflare edge request metadata from request.cf"
  },
  {
    path: "/counter",
    method: "GET",
    description: "KV-backed visit counter for persistence validation"
  },
  {
    path: "/admin",
    method: "GET",
    description: "Secret-backed route protected by x-api-token"
  }
];

function json(data: JsonRecord, init: ResponseInit = {}): Response {
  return Response.json(data, {
    status: init.status ?? 200,
    headers: init.headers
  });
}

function notFound(path: string): Response {
  return json(
    {
      error: "Not Found",
      message: "Endpoint does not exist",
      path
    },
    { status: 404 }
  );
}

function methodNotAllowed(method: string, path: string): Response {
  return json(
    {
      error: "Method Not Allowed",
      message: "Only GET is supported by this lab Worker",
      method,
      path
    },
    { status: 405 }
  );
}

function unauthorized(path: string): Response {
  return json(
    {
      error: "Unauthorized",
      message: "Provide a valid x-api-token header",
      path
    },
    { status: 401 }
  );
}

function configurationError(message: string): Response {
  return json(
    {
      error: "Configuration Error",
      message
    },
    { status: 500 }
  );
}

function utcTimestamp(): string {
  return new Date().toISOString();
}

function maskEmail(email: string): string {
  const [localPart, domain] = email.split("@");

  if (!localPart || !domain) {
    return "invalid-email-format";
  }

  if (localPart.length === 1) {
    return `*@${domain}`;
  }

  if (localPart.length === 2) {
    return `${localPart[0]}*@${domain}`;
  }

  return `${localPart.slice(0, 2)}***${localPart.slice(-1)}@${domain}`;
}

function getRequestInfo(request: Request): JsonRecord {
  return {
    method: request.method,
    path: new URL(request.url).pathname,
    userAgent: request.headers.get("user-agent") ?? "unknown",
    cfRay: request.headers.get("cf-ray") ?? null
  };
}

function getRuntimeInfo(request: CloudflareRequest): JsonRecord {
  return {
    runtime: "cloudflare-workers",
    timestamp: utcTimestamp(),
    colo: request.cf?.colo ?? null,
    country: request.cf?.country ?? null
  };
}

async function handleCounter(env: Env): Promise<Response> {
  const raw = await env.SETTINGS.get(COUNTER_KEY);
  const current = Number(raw ?? "0");
  const visits = Number.isFinite(current) ? current + 1 : 1;

  await env.SETTINGS.put(COUNTER_KEY, String(visits));

  return json({
    counterKey: COUNTER_KEY,
    visits,
    storage: "workers-kv",
    persistence: "survives Worker redeploys as long as the KV namespace stays bound",
    note: "Workers KV is eventually consistent, so this counter is a persistence demo rather than a strong-consistency design."
  });
}

function handleIndex(request: CloudflareRequest, env: Env): Response {
  return json({
    service: {
      name: env.APP_NAME,
      version: env.APP_VERSION,
      description: "Cloudflare Workers port of the DevOps course info service",
      course: env.COURSE_NAME,
      runtime: "cloudflare-workers"
    },
    request: getRequestInfo(request),
    runtime: getRuntimeInfo(request),
    configuration: {
      plaintextVars: ["APP_NAME", "COURSE_NAME", "APP_VERSION"],
      secretBindings: ["API_TOKEN", "ADMIN_EMAIL"],
      kvBinding: "SETTINGS",
      observability: "enabled in wrangler.jsonc"
    },
    endpoints: ROUTES
  });
}

function handleHealth(request: CloudflareRequest): Response {
  return json({
    status: "healthy",
    timestamp: utcTimestamp(),
    runtime: "cloudflare-workers",
    request: {
      path: new URL(request.url).pathname,
      colo: request.cf?.colo ?? null
    }
  });
}

function handleEdge(request: CloudflareRequest): Response {
  return json({
    runtime: "cloudflare-workers",
    metadata: {
      colo: request.cf?.colo ?? null,
      country: request.cf?.country ?? null,
      city: request.cf?.city ?? null,
      asn: request.cf?.asn ?? null,
      httpProtocol: request.cf?.httpProtocol ?? null,
      tlsVersion: request.cf?.tlsVersion ?? null
    },
    note: "request.cf metadata is only populated by the Workers runtime, so verify this endpoint against the deployed workers.dev URL."
  });
}

function handleAdmin(request: Request, env: Env): Response {
  if (!env.API_TOKEN || !env.ADMIN_EMAIL) {
    return configurationError(
      "Missing required secrets. Set API_TOKEN and ADMIN_EMAIL before testing /admin."
    );
  }

  const providedToken = request.headers.get("x-api-token");

  if (!providedToken || providedToken !== env.API_TOKEN) {
    return unauthorized(new URL(request.url).pathname);
  }

  return json({
    status: "authorized",
    message: "Secret-backed route verified without exposing raw secret values",
    adminEmailMasked: maskEmail(env.ADMIN_EMAIL)
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const cfRequest = request as CloudflareRequest;

    console.log("request", {
      path: url.pathname,
      method: request.method,
      colo: cfRequest.cf?.colo ?? null,
      country: cfRequest.cf?.country ?? null
    });

    if (request.method !== "GET") {
      return methodNotAllowed(request.method, url.pathname);
    }

    switch (url.pathname) {
      case "/":
        return handleIndex(cfRequest, env);
      case "/health":
        return handleHealth(cfRequest);
      case "/edge":
        return handleEdge(cfRequest);
      case "/counter":
        return handleCounter(env);
      case "/admin":
        return handleAdmin(request, env);
      default:
        return notFound(url.pathname);
    }
  }
};
