export interface Env {
  APP_NAME: string;
  DEPLOYMENT_TIME?: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

	console.log(`[${new Date().toISOString()}] path: ${path}, colo: ${request.cf?.colo || 'local'}`);

    if (path === "/health") {
      return Response.json({
        status: "ok",
        timestamp: new Date().toISOString(),
      });
    }

    if (path === "/") {
		return Response.json({
			app: env.APP_NAME,
			course: env.COURSE_NAME,
			version: "1.0.0",
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

	if (path === "/edge") {
	return Response.json({
		colo: request.cf?.colo || "unknown",
		country: request.cf?.country || "unknown",
		city: request.cf?.city || "unknown",
		httpProtocol: request.cf?.httpProtocol || "unknown",
		tlsVersion: request.cf?.tlsVersion || "unknown",
		asn: request.cf?.asn || "unknown",
		timezone: request.cf?.timezone || "unknown",
	});
	}

	if (path === "/secrets") {
	return Response.json({
		hasApiToken: !!env.API_TOKEN,
		hasAdminEmail: !!env.ADMIN_EMAIL,
	});
	}

	if (path === "/counter") {
	let visits = await env.SETTINGS.get("visits", "json");
	if (visits === null) {
		visits = { count: 0 };
	}
	visits.count++;
	await env.SETTINGS.put("visits", JSON.stringify(visits));
	return Response.json({
		visits: visits.count,
		storedAt: new Date().toISOString()
	});
	}

    return new Response("Not Found", { status: 404 });
  },
};