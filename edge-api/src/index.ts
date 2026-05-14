/**
 * DevOps Edge API — Cloudflare Worker
 *
 * Routes:
 *   GET /        — app information and endpoint listing
 *   GET /health  — health check with timestamp
 *   GET /edge    — edge metadata from request.cf
 *   GET /counter — KV-backed visit counter (persisted)
 *   GET /config  — configuration info (vars and secrets status)
 */

export default {
	async fetch(request, env, ctx): Promise<Response> {
		const url = new URL(request.url);
		console.log("path", url.pathname, "colo", request.cf?.colo);

		if (url.pathname === "/health") {
			return Response.json({
				status: "ok",
				timestamp: new Date().toISOString(),
			});
		}

		if (url.pathname === "/edge") {
			return Response.json({
				colo: request.cf?.colo ?? "unknown",
				country: request.cf?.country ?? "unknown",
				city: request.cf?.city ?? "unknown",
				asn: request.cf?.asn ?? "unknown",
				httpProtocol: request.cf?.httpProtocol ?? "unknown",
				tlsVersion: request.cf?.tlsVersion ?? "unknown",
			});
		}

		if (url.pathname === "/counter") {
			const raw = await env.SETTINGS.get("visits");
			const visits = Number(raw ?? "0") + 1;
			await env.SETTINGS.put("visits", String(visits));
			return Response.json({ visits });
		}

		if (url.pathname === "/config") {
			return Response.json({
				app_name: env.APP_NAME,
				course_name: env.COURSE_NAME,
				admin_email_set: !!env.ADMIN_EMAIL,
				api_token_set: !!env.API_TOKEN,
			});
		}

		if (url.pathname === "/") {
			return Response.json({
				app: env.APP_NAME,
				course: env.COURSE_NAME,
				message: "Hello from Cloudflare Workers",
				timestamp: new Date().toISOString(),
				endpoints: [
					{ path: "/", method: "GET", description: "App information" },
					{ path: "/health", method: "GET", description: "Health check" },
					{ path: "/edge", method: "GET", description: "Edge metadata" },
					{ path: "/counter", method: "GET", description: "KV-backed visit counter" },
					{ path: "/config", method: "GET", description: "Configuration info" },
				],
			});
		}

		return new Response("Not Found", { status: 404 });
	},
} satisfies ExportedHandler<Env>;
