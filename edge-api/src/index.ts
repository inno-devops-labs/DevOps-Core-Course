export default {
	async fetch(request, env, ctx): Promise<Response> {
		const url = new URL(request.url);
		const colo = request.cf?.colo ?? "local";
		console.log("[edge-api]", request.method, url.pathname, "colo=", colo);

		if (url.pathname === "/health") {
			return Response.json({ status: "ok" });
		}

		if (url.pathname === "/edge") {
			const cf = request.cf;
			return Response.json({
				colo: cf?.colo ?? null,
				country: cf?.country ?? null,
				city: cf?.city ?? null,
				asn: cf?.asn ?? null,
				httpProtocol: cf?.httpProtocol ?? null,
				tlsVersion: cf?.tlsVersion ?? null,
			});
		}

		if (url.pathname === "/counter") {
			const raw = await env.SETTINGS.get("visits");
			const visits = Number(raw ?? "0") + 1;
			await env.SETTINGS.put("visits", String(visits));
			return Response.json({ visits, key: "visits" });
		}

		if (url.pathname === "/config") {
			return Response.json({
				appName: env.APP_NAME,
				courseName: env.COURSE_NAME,
				deploymentNote: env.DEPLOYMENT_NOTE,
				secretsConfigured: {
					API_TOKEN: Boolean(env.API_TOKEN),
					ADMIN_EMAIL: Boolean(env.ADMIN_EMAIL),
				},
			});
		}

		if (url.pathname === "/") {
			return Response.json({
				app: env.APP_NAME,
				course: env.COURSE_NAME,
				message: "Hello from Cloudflare Workers",
				timestamp: new Date().toISOString(),
				deploymentNote: env.DEPLOYMENT_NOTE,
			});
		}

		return new Response("Not Found", { status: 404 });
	},
} satisfies ExportedHandler<Env>;
