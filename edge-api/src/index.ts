const ROUTES = [
	{ path: "/", method: "GET", description: "Deployment summary" },
	{ path: "/health", method: "GET", description: "Health check" },
	{ path: "/edge", method: "GET", description: "Cloudflare edge request metadata" },
	{ path: "/counter", method: "GET", description: "KV-backed persisted visit counter" },
	{ path: "/config", method: "GET", description: "Plaintext vars and secret binding status" },
] as const;

export default {
	async fetch(request, env, ctx): Promise<Response> {
		const url = new URL(request.url);

		console.log(
			JSON.stringify({
				event: "request",
				path: url.pathname,
				method: request.method,
				colo: request.cf?.colo ?? "local",
				country: request.cf?.country ?? "local",
			}),
		);

		if (request.method !== "GET" && request.method !== "HEAD") {
			return json({ error: "Method Not Allowed" }, { status: 405 });
		}

		switch (url.pathname) {
			case "/":
				return json({
					app: env.APP_NAME,
					course: env.COURSE_NAME,
					environment: env.DEPLOYMENT_ENV,
					message: "Hello from Cloudflare Workers",
					runtime: "cloudflare-workers",
					timestamp: new Date().toISOString(),
					routes: ROUTES,
				});

			case "/health":
				return json({
					status: "ok",
					app: env.APP_NAME,
					timestamp: new Date().toISOString(),
				});

			case "/edge":
				return json({
					colo: request.cf?.colo ?? "local-dev",
					country: request.cf?.country ?? "local-dev",
					city: request.cf?.city ?? "local-dev",
					asn: request.cf?.asn ?? "local-dev",
					httpProtocol: request.cf?.httpProtocol ?? "local-dev",
					tlsVersion: request.cf?.tlsVersion ?? "local-dev",
					workerUrl: url.origin,
				});

			case "/counter":
				return handleCounter(env);

			case "/config":
				return json({
					appName: env.APP_NAME,
					courseName: env.COURSE_NAME,
					deploymentEnvironment: env.DEPLOYMENT_ENV,
					secrets: {
						apiTokenConfigured: Boolean(env.API_TOKEN),
						adminEmailConfigured: Boolean(env.ADMIN_EMAIL),
					},
					kvBindingConfigured: Boolean(env.SETTINGS),
				});

			default:
				return json(
					{
						error: "Not Found",
						path: url.pathname,
						routes: ROUTES.map((route) => route.path),
					},
					{ status: 404 },
				);
		}
	},
} satisfies ExportedHandler<Env>;

async function handleCounter(env: Env): Promise<Response> {
	if (!env.SETTINGS) {
		return json(
			{
				error: "KV namespace SETTINGS is not bound",
				hint: "Create a Workers KV namespace and bind it as SETTINGS in wrangler.jsonc.",
			},
			{ status: 503 },
		);
	}

	const key = "visits";
	const rawVisits = await env.SETTINGS.get(key);
	const visits = Number.parseInt(rawVisits ?? "0", 10) + 1;
	await env.SETTINGS.put(key, String(visits));

	return json({
		key,
		visits,
		persisted: true,
	});
}

function json(body: unknown, init?: ResponseInit): Response {
	const headers = new Headers(init?.headers);
	headers.set("content-type", "application/json; charset=UTF-8");

	return Response.json(body, {
		...init,
		headers,
	});
}
