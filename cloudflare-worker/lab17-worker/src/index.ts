export interface Env {
  MY_VARIABLE?: string;
  MY_SECRET?: string;
  MY_KV?: KVNamespace;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    console.log(`Request received: ${request.method} ${path}`);

    // GET /health - Health check endpoint
    if (path === '/health') {
      return Response.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        service: 'cloudflare-worker-api'
      });
    }

    // GET /metadata - Edge metadata from Cloudflare
    if (path === '/metadata') {
      const cf = request.cf as any;
      return Response.json({
        colo: cf?.colo || 'unknown',
        country: cf?.country || 'unknown',
        city: cf?.city || 'unknown',
        asn: cf?.asn || 'unknown',
        httpProtocol: cf?.httpProtocol || 'unknown',
        tlsVersion: cf?.tlsVersion || 'unknown',
        timezone: cf?.timezone || 'unknown',
        regionCode: cf?.regionCode || 'unknown'
      });
    }

    // GET /config - Show configuration status
    if (path === '/config') {
      return Response.json({
        plaintextVariable: env.MY_VARIABLE || 'not set',
        secretConfigured: !!env.MY_SECRET,
        kvConfigured: !!env.MY_KV
      });
    }

    // GET /kv/read - Read from KV storage
    if (path === '/kv/read') {
      try {
        if (!env.MY_KV) {
          return Response.json({ error: 'KV namespace not configured' }, { status: 500 });
        }
        const value = await env.MY_KV.get('my-key');
        return Response.json({
          key: 'my-key',
          value: value || 'not found',
          kvWorks: true
        });
      } catch (err) {
        return Response.json({ 
          error: 'KV read failed', 
          details: String(err) 
        }, { status: 500 });
      }
    }

    // POST /kv/write - Write to KV storage
    if (path === '/kv/write' && request.method === 'POST') {
      try {
        if (!env.MY_KV) {
          return Response.json({ error: 'KV namespace not configured' }, { status: 500 });
        }
        const body = await request.json() as { value?: string };
        if (!body.value) {
          return Response.json({ error: 'Missing value in request body' }, { status: 400 });
        }
        await env.MY_KV.put('my-key', body.value);
        const verified = await env.MY_KV.get('my-key');
        return Response.json({
          success: true,
          key: 'my-key',
          value: body.value,
          verified: verified === body.value
        });
      } catch (err) {
        return Response.json({ 
          error: 'KV write failed', 
          details: String(err) 
        }, { status: 500 });
      }
    }

    // GET / - Root endpoint with API information
    if (path === '/') {
      return Response.json({
        name: 'Cloudflare Worker API',
        version: '1.0.0',
        endpoints: [
          { path: '/', method: 'GET', description: 'API information' },
          { path: '/health', method: 'GET', description: 'Health check' },
          { path: '/metadata', method: 'GET', description: 'Edge metadata (colo, country, city)' },
          { path: '/config', method: 'GET', description: 'Configuration status' },
          { path: '/kv/read', method: 'GET', description: 'Read from KV storage' },
          { path: '/kv/write', method: 'POST', description: 'Write to KV storage' }
        ]
      });
    }

    // 404 for unknown routes
    return Response.json({ error: 'Not Found' }, { status: 404 });
  },
};