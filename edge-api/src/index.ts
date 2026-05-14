const WORKER_NAME = "edge-api";
const API_VERSION = "task-2";

const routes = ["/", "/health", "/edge", "/metadata"];

function json(data: unknown, init: ResponseInit = {}): Response {
	const headers = new Headers(init.headers);
	headers.set("content-type", "application/json; charset=utf-8");
	headers.set("cache-control", "no-store");

	return Response.json(data, {
		...init,
		headers,
	});
}

export default {
	async fetch(request): Promise<Response> {
		const url = new URL(request.url);
		const timestamp = new Date().toISOString();

		if (request.method !== "GET") {
			return json(
				{
					error: "method_not_allowed",
					allowedMethods: ["GET"],
				},
				{
					status: 405,
					headers: {
						allow: "GET",
					},
				},
			);
		}

		if (url.pathname === "/") {
			return json({
				app: WORKER_NAME,
				message: "Hello from Cloudflare Workers",
				version: API_VERSION,
				routes,
				timestamp,
			});
		}

		if (url.pathname === "/health") {
			return json({
				status: "ok",
				service: WORKER_NAME,
				timestamp,
			});
		}

		if (url.pathname === "/edge") {
			return json({
				app: WORKER_NAME,
				colo: request.cf?.colo ?? null,
				country: request.cf?.country ?? null,
				city: request.cf?.city ?? null,
				asn: request.cf?.asn ?? null,
				httpProtocol: request.cf?.httpProtocol ?? null,
				tlsVersion: request.cf?.tlsVersion ?? null,
				timestamp,
			});
		}

		if (url.pathname === "/metadata") {
			return json({
				app: WORKER_NAME,
				version: API_VERSION,
				runtime: "cloudflare-workers",
				workerUrlPattern: `https://${WORKER_NAME}.neilzvest.workers.dev`,
				compatibilityDate: "2026-05-14",
				timestamp,
			});
		}

		return json(
			{
				error: "not_found",
				routes,
			},
			{ status: 404 },
		);
	},
} satisfies ExportedHandler<Env>;
