export default {
	async fetch(request, env, _ctx): Promise<Response> {
		const url = new URL(request.url);
		const colo = request.cf?.colo;
		console.log("request", { pathname: url.pathname, method: request.method, colo });

		if (request.method === "OPTIONS") {
			return new Response(null, { status: 204 });
		}

		if (url.pathname === "/health") {
			return Response.json({ status: "ok" });
		}

		if (url.pathname === "/") {
			return Response.json({
				app: env.APP_NAME,
				course: env.COURSE_NAME,
				deploymentLabel: env.DEPLOYMENT_LABEL,
				message: "Hello from Cloudflare Workers",
				timestamp: new Date().toISOString(),
			});
		}

		if (url.pathname === "/meta") {
			return Response.json({
				workerName: "edge-api",
				appName: env.APP_NAME,
				courseName: env.COURSE_NAME,
				deploymentLabel: env.DEPLOYMENT_LABEL,
				compatibilityDate: "2026-05-10",
			});
		}

		if (url.pathname === "/edge") {
			const cf = request.cf;
			return Response.json({
				colo: cf?.colo,
				country: cf?.country,
				city: cf?.city,
				asn: cf?.asn,
				httpProtocol: cf?.httpProtocol,
				tlsVersion: cf?.tlsVersion,
			});
		}

		if (url.pathname === "/counter") {
			const raw = await env.SETTINGS.get("visits");
			const visits = Number(raw ?? "0") + 1;
			await env.SETTINGS.put("visits", String(visits));
			return Response.json({ visits });
		}

		if (url.pathname === "/admin/whoami") {
			const auth = request.headers.get("Authorization");
			const expected = `Bearer ${env.API_TOKEN}`;
			if (!env.API_TOKEN || auth !== expected) {
				return Response.json({ error: "unauthorized" }, { status: 401 });
			}
			return Response.json({ admin: env.ADMIN_EMAIL });
		}

		return new Response("Not Found", { status: 404 });
	},
} satisfies ExportedHandler<Env>;
