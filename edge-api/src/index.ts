export interface Env {
	APP_NAME: string;
	COURSE_NAME: string;
	ENVIRONMENT: string;
	API_TOKEN: string;
	ADMIN_EMAIL: string;
	SETTINGS: KVNamespace;
}

type JsonValue = Record<string, unknown>;

function json(body: JsonValue, init: ResponseInit = {}): Response {
	return Response.json(body, {
		headers: {
			"cache-control": "no-store",
			...init.headers,
		},
		...init,
	});
}

function getSecretSummary(env: Env): JsonValue {
	return {
		apiTokenConfigured: Boolean(env.API_TOKEN),
		adminEmailConfigured: Boolean(env.ADMIN_EMAIL),
		adminEmailDomain: env.ADMIN_EMAIL?.includes("@") ? env.ADMIN_EMAIL.split("@").at(1) : "not-set",
	};
}

export default {
	async fetch(request, env): Promise<Response> {
		const url = new URL(request.url);
		const startedAt = Date.now();

		console.log(
			JSON.stringify({
				message: "request",
				path: url.pathname,
				method: request.method,
				colo: request.cf?.colo ?? "local",
				country: request.cf?.country ?? "local",
			}),
		);

		if (url.pathname === "/health") {
			return json({
				status: "ok",
				app: env.APP_NAME,
				timestamp: new Date().toISOString(),
			});
		}

		if (url.pathname === "/edge") {
			return json({
				app: env.APP_NAME,
				deployment: {
					platform: "cloudflare-workers",
					environment: env.ENVIRONMENT,
					workersDev: true,
				},
				edge: {
					colo: request.cf?.colo ?? "local-dev",
					country: request.cf?.country ?? "local-dev",
					city: request.cf?.city ?? "local-dev",
					asn: request.cf?.asn ?? "local-dev",
					httpProtocol: request.cf?.httpProtocol ?? "local-dev",
					tlsVersion: request.cf?.tlsVersion ?? "local-dev",
				},
				request: {
					method: request.method,
					path: url.pathname,
					userAgent: request.headers.get("user-agent") ?? "unknown",
				},
			});
		}

		if (url.pathname === "/config") {
			return json({
				app: env.APP_NAME,
				course: env.COURSE_NAME,
				environment: env.ENVIRONMENT,
				secrets: getSecretSummary(env),
				note: "Plaintext vars are safe for non-sensitive values only. Secrets are injected by Wrangler and are not committed.",
			});
		}

		if (url.pathname === "/counter") {
			const rawVisits = await env.SETTINGS.get("visits");
			const visits = Number(rawVisits ?? "0") + 1;
			await env.SETTINGS.put("visits", String(visits));

			return json({
				key: "visits",
				visits,
				persistedIn: "Workers KV",
			});
		}

		if (url.pathname === "/") {
			return json({
				app: env.APP_NAME,
				course: env.COURSE_NAME,
				message: "Hello from Cloudflare Workers edge API",
				environment: env.ENVIRONMENT,
				timestamp: new Date().toISOString(),
				durationMs: Date.now() - startedAt,
				routes: [
					{ path: "/", method: "GET", description: "Service metadata" },
					{ path: "/health", method: "GET", description: "Health check" },
					{ path: "/edge", method: "GET", description: "Cloudflare edge request metadata" },
					{ path: "/config", method: "GET", description: "Vars and secret presence" },
					{ path: "/counter", method: "GET", description: "KV-backed persisted counter" },
				],
			});
		}

		return json(
			{
				error: "not_found",
				message: "Route does not exist",
				path: url.pathname,
			},
			{ status: 404 },
		);
	},
} satisfies ExportedHandler<Env>;
