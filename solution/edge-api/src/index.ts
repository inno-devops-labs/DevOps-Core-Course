export interface Env {
	APP_NAME: string;
	COURSE_NAME: string;
	ENVIRONMENT: string;
	API_VERSION: string;
	API_TOKEN: string;
	ADMIN_EMAIL: string;
	SETTINGS: KVNamespace;
}

type JsonBody = Record<string, unknown>;

function json(body: JsonBody, init: ResponseInit = {}): Response {
	return Response.json(body, {
		headers: {
			"cache-control": "no-store",
			...init.headers,
		},
		status: init.status,
		statusText: init.statusText,
	});
}

function routeList(baseUrl: string): string[] {
	const base = new URL(baseUrl);
	return ["/", "/health", "/edge", "/config", "/counter", "/settings"].map((path) => `${base.origin}${path}`);
}

async function readJson(request: Request): Promise<JsonBody> {
	try {
		const body = await request.json<JsonBody>();
		return body && typeof body === "object" ? body : {};
	} catch {
		return {};
	}
}

export default {
	async fetch(request, env): Promise<Response> {
		const url = new URL(request.url);
		const cf = request.cf;

		console.log(
			JSON.stringify({
				event: "request",
				path: url.pathname,
				method: request.method,
				colo: cf?.colo ?? "local",
				country: cf?.country ?? "local",
			}),
		);

		if (url.pathname === "/" && request.method === "GET") {
			return json({
				app: env.APP_NAME,
				course: env.COURSE_NAME,
				environment: env.ENVIRONMENT,
				version: env.API_VERSION,
				message: "Cloudflare Workers edge API for DevOps Core Lab 17",
				routes: routeList(request.url),
				timestamp: new Date().toISOString(),
			});
		}

		if (url.pathname === "/health" && request.method === "GET") {
			return json({
				status: "ok",
				app: env.APP_NAME,
				version: env.API_VERSION,
				kv: Boolean(env.SETTINGS),
				timestamp: new Date().toISOString(),
			});
		}

		if (url.pathname === "/edge" && request.method === "GET") {
			return json({
				colo: cf?.colo ?? "local-dev",
				country: cf?.country ?? "local-dev",
				city: cf?.city ?? "local-dev",
				asn: cf?.asn ?? "local-dev",
				httpProtocol: cf?.httpProtocol ?? "local-dev",
				tlsVersion: cf?.tlsVersion ?? "local-dev",
				timezone: cf?.timezone ?? "local-dev",
				workerGlobal: true,
			});
		}

		if (url.pathname === "/config" && request.method === "GET") {
			return json({
				app: env.APP_NAME,
				course: env.COURSE_NAME,
				environment: env.ENVIRONMENT,
				version: env.API_VERSION,
				secrets: {
					API_TOKEN: env.API_TOKEN ? "configured" : "missing",
					ADMIN_EMAIL: env.ADMIN_EMAIL ? "configured" : "missing",
				},
				note: "Plaintext vars are visible in wrangler.jsonc; secret values are supplied through Cloudflare bindings.",
			});
		}

		if (url.pathname === "/counter" && request.method === "GET") {
			const raw = await env.SETTINGS.get("visits");
			const visits = Number.parseInt(raw ?? "0", 10) + 1;
			await env.SETTINGS.put("visits", String(visits));
			return json({
				key: "visits",
				visits,
				persistedIn: "Workers KV",
			});
		}

		if (url.pathname === "/settings" && request.method === "GET") {
			const value = await env.SETTINGS.get("lab17-note");
			return json({
				key: "lab17-note",
				value,
				found: value !== null,
			});
		}

		if (url.pathname === "/settings" && request.method === "POST") {
			const body = await readJson(request);
			const value = typeof body.value === "string" && body.value.length > 0 ? body.value : "persisted after redeploy";
			await env.SETTINGS.put("lab17-note", value);
			return json(
				{
					key: "lab17-note",
					value,
					persistedIn: "Workers KV",
				},
				{ status: 201 },
			);
		}

		return json(
			{
				error: "not_found",
				message: `No route for ${request.method} ${url.pathname}`,
				availableRoutes: ["/", "/health", "/edge", "/config", "/counter", "/settings"],
			},
			{ status: 404 },
		);
	},
} satisfies ExportedHandler<Env>;
