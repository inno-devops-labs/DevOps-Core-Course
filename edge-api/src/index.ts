export interface Env {
	APP_NAME: string;
	COURSE_NAME: string;
	API_TOKEN: string;
	ADMIN_EMAIL: string;
	SETTINGS: KVNamespace;
}

const VERSION = "v1";

const routes = [
	"GET /",
	"GET /health",
	"GET /edge",
	"GET /config",
	"GET /counter",
];

export default {
	async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
		const url = new URL(request.url);
		const path = url.pathname;

		console.log("request", {
			method: request.method,
			path,
			colo: request.cf?.colo,
			country: request.cf?.country,
		});

		if (request.method !== "GET") {
			return Response.json(
				{
					error: "Method Not Allowed",
					allowedMethods: ["GET"],
				},
				{
					status: 405,
					headers: {
						Allow: "GET",
					},
				},
			);
		}

		if (path === "/") {
			return Response.json({
				app: env.APP_NAME,
				course: env.COURSE_NAME,
				version: VERSION,
				message: "Hello from Cloudflare Workers",
				platform: "Cloudflare Workers",
				runtime: "serverless edge runtime",
				routes,
				timestamp: new Date().toISOString(),
			});
		}

		if (path === "/health") {
			return Response.json({
				status: "ok",
				app: env.APP_NAME,
				version: VERSION,
				timestamp: new Date().toISOString(),
			});
		}

		if (path === "/edge") {
			return Response.json({
				app: env.APP_NAME,
				version: VERSION,
				edge: {
					colo: request.cf?.colo ?? null,
					country: request.cf?.country ?? null,
					city: request.cf?.city ?? null,
					region: request.cf?.region ?? null,
					asn: request.cf?.asn ?? null,
					httpProtocol: request.cf?.httpProtocol ?? null,
					tlsVersion: request.cf?.tlsVersion ?? null,
					timezone: request.cf?.timezone ?? null,
				},
				note: "These fields are provided by Cloudflare at the edge. In local dev some values may be null.",
				timestamp: new Date().toISOString(),
			});
		}

		if (path === "/config") {
			return Response.json({
				appNameFromPlaintextVar: env.APP_NAME,
				courseNameFromPlaintextVar: env.COURSE_NAME,
				secrets: {
					apiTokenConfigured: Boolean(env.API_TOKEN),
					adminEmailConfigured: Boolean(env.ADMIN_EMAIL),
				},
				note: "Secret values are used through env but are not returned in the response.",
			});
		}

		if (path === "/counter") {
			if (!env.SETTINGS) {
				return Response.json(
					{
						error: "KV binding SETTINGS is not configured",
					},
					{ status: 500 },
				);
			}

			const rawVisits = await env.SETTINGS.get("visits");
			const visits = Number(rawVisits ?? "0") + 1;

			await env.SETTINGS.put("visits", String(visits));

			return Response.json({
				app: env.APP_NAME,
				key: "visits",
				visits,
				persistedIn: "Workers KV",
				timestamp: new Date().toISOString(),
			});
		}

		return Response.json(
			{
				error: "Not Found",
				path,
				availableRoutes: routes,
			},
			{ status: 404 },
		);
	},
} satisfies ExportedHandler<Env>;
