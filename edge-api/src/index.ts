/**
 * Welcome to Cloudflare Workers! This is your first worker.
 *
 * - Run `npm run dev` in your terminal to start a development server
 * - Open a browser tab at http://localhost:8787/ to see your worker in action
 * - Run `npm run deploy` to publish your worker
 *
 * Bind resources to your worker in `wrangler.jsonc`. After adding bindings, a type definition for the
 * `Env` object can be regenerated with `npm run cf-typegen`.
 *
 * Learn more at https://developers.cloudflare.com/workers/
 */

export interface Env {
	APP_NAME: string;
	API_TOKEN: string;
	ADMIN_EMAIL: string;
	SETTINGS: KVNamespace;
}

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		const url = new URL(request.url);

		console.log("path", url.pathname, "colo", request.cf?.colo);

		if (url.pathname === "/health") {
			return Response.json({ status: "ok" });
		}

		if (url.pathname === "/") {
			return Response.json({
				app: env.APP_NAME,
				message: "Hello from Cloudflare Workers",
				timestamp: new Date().toISOString(),
			});
		}

		if (url.pathname === "/edge") {
			return Response.json({
				colo: request.cf?.colo,
				country: request.cf?.country,
				city: request.cf?.city,
				asn: request.cf?.asn,
				httpProtocol: request.cf?.httpProtocol,
				tlsVersion: request.cf?.tlsVersion,
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