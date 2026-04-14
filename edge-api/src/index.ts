export interface Env {
  APP_NAME: string;
  COUNTER: KVNamespace;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // Эндпоинт для проверки здоровья
    if (url.pathname === "/health") {
      return Response.json({ status: "ok" });
    }

    // Главная страница с информацией о проекте (счётчик увеличивается, но не показывается)
    if (url.pathname === "/") {
      // Увеличиваем счётчик только на запросы к главной странице
      const raw = await env.COUNTER.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.COUNTER.put("visits", String(visits));  // Сохраняем новое значение

      return Response.json({
        app: env.APP_NAME || "edge-api",
        message: "Hello from Cloudflare Workers",
        timestamp: new Date().toISOString(),
      });
    }

    // Эндпоинт для работы с метаданными Cloudflare
    if (url.pathname === "/edge") {
      return Response.json({
        colo: request.cf?.colo,
        country: request.cf?.country,
        city: request.cf?.city,
        asn: request.cf?.asn,
        httpProtocol: request.cf?.httpProtocol,
        tlsVersion: request.cf?.tlsVersion,
      });
    }

    // Эндпоинт для счётчика с использованием KV
    if (url.pathname === "/counter") {
      // Возвращаем количество посещений с KV
      const raw = await env.COUNTER.get("visits");
      const visits = Number(raw ?? "0");
      return Response.json({ visits });
    }

    return new Response("Not Found", { status: 404 });
  },
} satisfies ExportedHandler<Env>;