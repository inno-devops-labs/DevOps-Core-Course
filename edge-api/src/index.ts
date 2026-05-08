export interface Env {
	APP_NAME: string;
	COURSE_NAME: string;
	API_TOKEN: string;
	ADMIN_EMAIL: string;
	SETTINGS: KVNamespace;
}

const json = (data: unknown, init?: ResponseInit): Response => {
	return Response.json(data, init);
};

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		const url = new URL(request.url);
		const colo = request.cf?.colo ?? null;
		console.log("request", { path: url.pathname, method: request.method, colo });
		console.log("chacged to new version");
		if (url.pathname === "/health") {
			return json({ status: "ok", timestamp: new Date().toISOString() });
		}

		if (url.pathname === "/") {
			return json({
				app: env.APP_NAME,
				course: env.COURSE_NAME,
				message: "Hello from Cloudflare Workers",
				routes: ["/", "/health", "/edge", "/counter"],
				timestamp: new Date().toISOString(),
			});
		}

		if (url.pathname === "/edge") {
			const cf = request.cf ?? {};
			return json({
				colo: cf.colo ?? null,
				country: cf.country ?? null,
				city: cf.city ?? null,
				asn: cf.asn ?? null,
				httpProtocol: cf.httpProtocol ?? null,
				tlsVersion: cf.tlsVersion ?? null,
			});
		}

		if (url.pathname === "/counter") {
			if (!env.SETTINGS) {
				return json({ error: "KV binding SETTINGS is missing" }, { status: 500 });
			}
			const raw = await env.SETTINGS.get("visits");
			const visits = Number(raw ?? "0") + 1;
			await env.SETTINGS.put("visits", String(visits));
			return json({
				visits,
				secretsConfigured: {
					apiToken: Boolean(env.API_TOKEN),
					adminEmail: Boolean(env.ADMIN_EMAIL),
				},
			});
		}

		return json({ error: "Not Found" }, { status: 404 });
	},
} satisfies ExportedHandler<Env>;
