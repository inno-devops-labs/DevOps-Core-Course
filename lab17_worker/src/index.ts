import type { KVNamespace } from '@cloudflare/workers-types';

const BUILD_VERSION = 'task5-v1';

type Env = {
  PLAINTEXT_VAR?: string;
  APP_SECRET_ONE?: string;
  APP_SECRET_TWO?: string;
  LAB17_KV: KVNamespace;
};

type CloudflareRequestMetadata = {
  colo?: string;
  country?: string;
  city?: string;
  asn?: number;
  httpProtocol?: string;
  tlsVersion?: string;
};

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });
}

async function readRequestValue(request: Request): Promise<string | null> {
  const contentType = request.headers.get('content-type') ?? '';

  if (contentType.includes('application/json')) {
    try {
      const body = (await request.json()) as { value?: unknown };
      if (typeof body.value === 'string') {
        return body.value;
      }
    } catch {
      return null;
    }
  }

  const text = await request.text();
  return text.trim() ? text : null;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;
    const requestWithCf = request as Request & { cf?: CloudflareRequestMetadata };
    const cf = requestWithCf.cf ?? {};

    console.log(`[${BUILD_VERSION}] Incoming request ${request.method} ${path}`);

    if (path === '/health') {
      return new Response('OK', { status: 200 });
    }

    if (path === '/meta') {
      return json({
        buildVersion: BUILD_VERSION,
        worker: 'lab17-worker',
        route: '/meta',
        method: request.method,
        url: url.toString(),
        plaintextVar: env.PLAINTEXT_VAR ?? null,
        secretsConfigured: Boolean(env.APP_SECRET_ONE) && Boolean(env.APP_SECRET_TWO),
      });
    }

    if (path === '/config') {
      return json({
        buildVersion: BUILD_VERSION,
        worker: 'lab17-worker',
        route: '/config',
        plaintextVar: env.PLAINTEXT_VAR ?? null,
        secretOneConfigured: Boolean(env.APP_SECRET_ONE),
        secretTwoConfigured: Boolean(env.APP_SECRET_TWO),
      });
    }

    if (path === '/kv' && request.method === 'GET') {
      const key = url.searchParams.get('key') ?? 'lab17-demo';
      const value = await env.LAB17_KV.get(key);
      return json({
        buildVersion: BUILD_VERSION,
        worker: 'lab17-worker',
        route: '/kv',
        key,
        value,
        found: value !== null,
      });
    }

    if (path === '/kv' && request.method === 'POST') {
      const key = url.searchParams.get('key') ?? 'lab17-demo';
      const value = url.searchParams.get('value') ?? (await readRequestValue(request));

      if (!value) {
        return json({ error: 'Provide a non-empty value in the query string or request body' }, 400);
      }

      await env.LAB17_KV.put(key, value);
      return json({
        buildVersion: BUILD_VERSION,
        worker: 'lab17-worker',
        route: '/kv',
        key,
        stored: true,
        value,
      });
    }

    if (path === '/edge') {
      return json({
        buildVersion: BUILD_VERSION,
        worker: 'lab17-worker',
        route: '/edge',
        colo: cf.colo ?? null,
        country: cf.country ?? null,
        city: cf.city ?? null,
        asn: cf.asn ?? null,
        httpProtocol: cf.httpProtocol ?? null,
        tlsVersion: cf.tlsVersion ?? null,
        userAgent: request.headers.get('user-agent'),
      });
    }

    if (path === '/') {
      return json({
        buildVersion: BUILD_VERSION,
        message: 'Cloudflare Worker is running',
        routes: ['/health', '/meta', '/edge', '/config', '/kv', '/'],
      });
    }

    return json({ error: 'Not found', path }, 404);
  },
};
