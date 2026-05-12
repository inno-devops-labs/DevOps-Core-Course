/**
 * Lab 17 edge API — routes, health, deployment metadata, edge CF metadata, KV counter, secrets (redacted).
 */

export default {
	async fetch(request, env, _ctx): Promise<Response> {
		const url = new URL(request.url);
		const cf = request.cf;

		console.log("request", {
			path: url.pathname,
			method: request.method,
			colo: cf?.colo,
			country: cf?.country,
		});

		if (url.pathname === "/health") {
			return Response.json({ status: "ok" });
		}

		if (url.pathname === "/") {
			return Response.json({
				app: env.APP_NAME,
				course: env.COURSE_NAME,
				message: "Hello from Cloudflare Workers (Lab 17) — v2",
				timestamp: new Date().toISOString(),
			});
		}

		if (url.pathname === "/deploy") {
			return Response.json({
				app: env.APP_NAME,
				course: env.COURSE_NAME,
				runtime: "cloudflare-workers",
				compatibilityDate: "2026-03-10",
				deployment: {
					note: "Metadata about this deployment surface; version id is available in dashboard / wrangler deployments.",
					timestamp: new Date().toISOString(),
				},
			});
		}

		if (url.pathname === "/edge") {
			return Response.json({
				colo: cf?.colo ?? null,
				country: cf?.country ?? null,
				city: cf?.city ?? null,
				asn: cf?.asn ?? null,
				httpProtocol: cf?.httpProtocol ?? null,
				tlsVersion: cf?.tlsVersion ?? null,
			});
		}

		if (url.pathname === "/secrets") {
			const tokenTail =
				env.API_TOKEN && env.API_TOKEN.length > 4
					? `…${env.API_TOKEN.slice(-4)}`
					: "(unset)";
			return Response.json({
				apiTokenTail: tokenTail,
				adminEmailDomain: env.ADMIN_EMAIL?.includes("@")
					? env.ADMIN_EMAIL.split("@")[1] ?? "redacted"
					: "(redacted)",
			});
		}

		if (url.pathname === "/counter") {
			const raw = await env.SETTINGS.get("visits");
			const visits = Number(raw ?? "0") + 1;
			await env.SETTINGS.put("visits", String(visits));
			return Response.json({ visits, storedKey: "visits" });
		}

		return new Response("Not Found", { status: 404 });
	},
} satisfies ExportedHandler<Env>;
