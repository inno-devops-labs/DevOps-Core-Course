export interface Env {
	APP_NAME: string;
	COURSE_NAME: string;
	API_TOKEN?: string;
	ADMIN_EMAIL?: string;
	SETTINGS?: KVNamespace;
}

function json(data: unknown, status = 200): Response {
	return Response.json(data, {
		status,
		headers: {
			"cache-control": "no-store",
		},
	});
}

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		const url = new URL(request.url);

		console.log("request", {
			path: url.pathname,
			colo: request.cf?.colo,
			country: request.cf?.country,
		});

		if (url.pathname === "/") {
			return json({
				app: env.APP_NAME,
				course: env.COURSE_NAME,
				message: "Hello from Cloudflare Workers",
				timestamp: new Date().toISOString(),
				routes: ["/", "/health", "/edge", "/config", "/counter"],
			});
		}

		if (url.pathname === "/health") {
			return json({
				status: "ok",
				service: env.APP_NAME,
				timestamp: new Date().toISOString(),
			});
		}

		if (url.pathname === "/edge") {
			return json({
				colo: request.cf?.colo ?? null,
				country: request.cf?.country ?? null,
				city: request.cf?.city ?? null,
				asn: request.cf?.asn ?? null,
				httpProtocol: request.cf?.httpProtocol ?? null,
				tlsVersion: request.cf?.tlsVersion ?? null,
			});
		}

		if (url.pathname === "/config") {
			return json({
				appName: env.APP_NAME,
				courseName: env.COURSE_NAME,
				hasApiToken: Boolean(env.API_TOKEN),
				hasAdminEmail: Boolean(env.ADMIN_EMAIL),
				hasKV: Boolean(env.SETTINGS),
			});
		}

		if (url.pathname === "/counter") {
			if (!env.SETTINGS) {
				return json({ error: "KV namespace SETTINGS is not configured" }, 503);
			}

			const raw = await env.SETTINGS.get("visits");
			const visits = Number(raw ?? "0") + 1;
			await env.SETTINGS.put("visits", String(visits));

			return json({
				visits,
				persisted: true,
			});
		}

		return json(
			{
				error: "Not Found",
				path: url.pathname,
			},
			404,
		);
	},
} satisfies ExportedHandler<Env>;
