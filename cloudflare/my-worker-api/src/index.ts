export interface Env {
  APP_NAME: string;
  DEPLOYMENT_TIME?: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    if (path === "/health") {
      return Response.json({
        status: "ok",
        timestamp: new Date().toISOString(),
      });
    }

    if (path === "/") {
      return Response.json({
        app: env.APP_NAME || "My Worker API",
        version: "1.0.0",
        message: "Hello from Cloudflare Workers",
        environment: "workers.dev",
        timestamp: new Date().toISOString(),
      });
    }

    if (path === "/metadata") {
      return Response.json({
        workerName: "my-worker-api",
        deployedAt: new Date().toISOString(),
        runtime: "Cloudflare Workers",
        bindings: {
          APP_NAME: env.APP_NAME,
          DEPLOYMENT_TIME: env.DEPLOYMENT_TIME || "not set",
        },
      });
    }

    if (path.startsWith("/hello/")) {
      const name = path.slice(7);
      return Response.json({
        message: `Hello, ${name || "stranger"}!`,
      });
    }

    return new Response("Not Found", { status: 404 });
  },
};