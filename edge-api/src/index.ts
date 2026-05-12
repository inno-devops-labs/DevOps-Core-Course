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
	ENVIRONMENT: string;
	DEPLOYMENT_VERSION: string;
	API_TOKEN: string;
	ADMIN_EMAIL: string;
	SETTINGS: KVNamespace;
}

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		const url = new URL(request.url);
		console.log("Incoming request", {
			method: request.method,
			path: url.pathname,
		});

		if (request.method === "GET" && url.pathname === "/health") {
			return Response.json({ status: "ok" }, { status: 200 });
		}

		if (request.method === "GET" && url.pathname === "/") {
			return Response.json(
				{
					app: env.APP_NAME,
					environment: env.ENVIRONMENT,
					message: "Hello from Cloudflare Workers",
					timestamp: new Date().toISOString(),
				},
				{ status: 200 },
			);
		}

		if (request.method === "GET" && url.pathname === "/deployment") {
			return Response.json(
				{
					worker: env.APP_NAME,
					environment: env.ENVIRONMENT,
					deploymentVersion: env.DEPLOYMENT_VERSION,
					hasSecretsConfigured: Boolean(env.API_TOKEN) && Boolean(env.ADMIN_EMAIL),
				},
				{ status: 200 },
			);
		}

		if (request.method === "GET" && url.pathname === "/edge") {
			return Response.json(
				{
					colo: request.cf?.colo ?? null,
					country: request.cf?.country ?? null,
					city: request.cf?.city ?? null,
					asn: request.cf?.asn ?? null,
					httpProtocol: request.cf?.httpProtocol ?? null,
					tlsVersion: request.cf?.tlsVersion ?? null,
				},
				{ status: 200 },
			);
		}

		if (url.pathname === "/kv" && request.method === "POST") {
			const payload = (await request.json()) as { key?: string; value?: string };
			if (!payload?.key || typeof payload.value !== "string") {
				return Response.json({ error: "Provide JSON body with key and value" }, { status: 400 });
			}
			await env.SETTINGS.put(payload.key, payload.value);
			return Response.json({ stored: true, key: payload.key }, { status: 201 });
		}

		if (url.pathname === "/kv" && request.method === "GET") {
			const key = url.searchParams.get("key");
			if (!key) {
				return Response.json({ error: "Missing query parameter: key" }, { status: 400 });
			}
			const value = await env.SETTINGS.get(key);
			if (value === null) {
				return Response.json({ error: "Key not found", key }, { status: 404 });
			}
			return Response.json({ key, value }, { status: 200 });
		}

		return Response.json({ error: "Not Found", path: url.pathname }, { status: 404 });
	},
};
