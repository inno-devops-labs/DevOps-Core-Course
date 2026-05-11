export interface Env {
	SETTINGS: KVNamespace;
	APP_NAME: string;
	COURSE_NAME: string;
}

const STARTED_AT = Date.now();
const VISITS_KEY = "visits";

export default {
	async fetch(
		request: Request,
		env: Env,
		_ctx: ExecutionContext,
	): Promise<Response> {
		const url = new URL(request.url);
		const path = url.pathname;
		const cf = request.cf as IncomingRequestCfProperties | undefined;
		const colo = cf?.colo ?? "unknown";

		console.log(
			`request ${request.method} ${path} colo=${colo}`,
		);

		if (request.method !== "GET") {
			return new Response("Method Not Allowed", { status: 405 });
		}

		if (path === "/") {
			return Response.json({
				app: env.APP_NAME,
				version: "1.0.0",
				message: "Hello from Cloudflare Workers edge API",
				timestamp: new Date().toISOString(),
			});
		}

		if (path === "/health") {
			const uptimeSec = Math.floor((Date.now() - STARTED_AT) / 1000);
			return Response.json({
				status: "ok",
				uptime: uptimeSec,
			});
		}

		if (path === "/edge") {
			return Response.json({
				colo: cf?.colo ?? "unknown",
				country: cf?.country ?? "unknown",
				city: cf?.city ?? "unknown",
				asn: cf?.asn ?? 0,
				httpProtocol: cf?.httpProtocol ?? "unknown",
				tlsVersion: cf?.tlsVersion ?? "unknown",
			});
		}

		if (path === "/counter") {
			const raw = await env.SETTINGS.get(VISITS_KEY);
			const prev = raw ? parseInt(raw, 10) : 0;
			const next = Number.isFinite(prev) ? prev + 1 : 1;
			await env.SETTINGS.put(VISITS_KEY, String(next));
			return Response.json({ visits: next });
		}

		return Response.json(
			{ error: "Not Found", path },
			{ status: 404 },
		);
	},
};
