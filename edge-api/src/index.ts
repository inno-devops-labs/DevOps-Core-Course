export interface Env {
	APP_NAME: string;
	COURSE_NAME: string;
	API_TOKEN: string;
	ADMIN_EMAIL: string;
	SETTINGS: KVNamespace;
}

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		const url = new URL(request.url);

		console.log("request", request.method, url.pathname, "colo", (request as any).cf?.colo);

		if (url.pathname === "/") {
			return Response.json({
				app: env.APP_NAME,
				course: env.COURSE_NAME,
				message: "Hello from Cloudflare Workers edge",
				timestamp: new Date().toISOString(),
				routes: ["/", "/health", "/edge", "/counter"],
			});
		}

		if (url.pathname === "/health") {
			return Response.json({
				status: "ok",
				app: env.APP_NAME,
				timestamp: new Date().toISOString(),
			});
		}

		if (url.pathname === "/edge") {
			const cf = (request as any).cf ?? {};
			return Response.json({
				colo: cf.colo,
				country: cf.country,
				city: cf.city,
				asn: cf.asn,
				httpProtocol: cf.httpProtocol,
				tlsVersion: cf.tlsVersion,
			});
		}

		if (url.pathname === "/counter") {
			const raw = await env.SETTINGS.get("visits");
			const visits = Number(raw ?? "0") + 1;
			await env.SETTINGS.put("visits", String(visits));
			return Response.json({ visits });
		}

		return new Response("Not Found", { status: 404 });
	},
};
