export default {
  async fetch(request: Request, env: any): Promise<Response> {
    const url = new URL(request.url);

    // /health
    if (url.pathname === "/health") {
      return new Response(
        JSON.stringify({
          status: "ok",
          uptime: Date.now(),
        }),
        { headers: { "Content-Type": "application/json" } }
      );
    }

    // /meta (информация о деплое)
    if (url.pathname === "/meta") {
      return new Response(
        JSON.stringify({
          app: "lab17-api",
          version: "1.0.0",
          deployedAt: new Date().toISOString(),
          region: request.cf?.colo || "unknown",
        }),
        { headers: { "Content-Type": "application/json" } }
      );
    }

    // /hello (любой кастомный endpoint)
    if (url.pathname === "/hello") {
      return new Response(
        JSON.stringify({
          message: "Hello from Cloudflare Workers 🚀",
        }),
        { headers: { "Content-Type": "application/json" } }
      );
    }

    return new Response("Not Found", { status: 404 });
  },
};