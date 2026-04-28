export interface Env {}

type JsonBody = Record<string, unknown>;

function jsonResponse(body: JsonBody, status = 200): Response {
	return Response.json(body, {
		status,
		headers: {
			"content-type": "application/json; charset=utf-8",
		},
	});
}

function notFound(pathname: string): Response {
	return jsonResponse(
		{
			error: "Not Found",
			message: "Endpoint does not exist",
			path: pathname,
			availableRoutes: ["/", "/health", "/deployment", "/edge"],
		},
		404,
	);
}

export default {
	async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
		const url = new URL(request.url);
		const timestamp = new Date().toISOString();

		console.log("request", {
			method: request.method,
			path: url.pathname,
			timestamp,
		});

		if (request.method !== "GET") {
			return jsonResponse(
				{
					error: "Method Not Allowed",
					method: request.method,
					allowedMethods: ["GET"],
				},
				405,
			);
		}

		if (url.pathname === "/") {
			return jsonResponse({
				service: {
					name: "edge-api",
					description: "Cloudflare Workers API for DevOps Core Course",
					runtime: "Cloudflare Workers",
				},
				message: "Hello from Cloudflare Workers",
				routes: ["/", "/health", "/deployment", "/edge"],
				timestamp,
			});
		}

		if (url.pathname === "/health") {
			return jsonResponse({
				status: "healthy",
				service: "edge-api",
				timestamp,
			});
		}

		if (url.pathname === "/deployment") {
			return jsonResponse({
				application: "edge-api",
				platform: "Cloudflare Workers",
				language: "TypeScript",
				environment: "workers.dev",
				version: "lab17-task2",
				deployedWith: "Wrangler",
				publicUrlFormat: "https://<worker-name>.<subdomain>.workers.dev",
				timestamp,
			});
		}

		if (url.pathname === "/edge") {
			return jsonResponse({
				colo: request.cf?.colo ?? "local-dev",
				country: request.cf?.country ?? "local-dev",
				city: request.cf?.city ?? "local-dev",
				asn: request.cf?.asn ?? "local-dev",
				httpProtocol: request.cf?.httpProtocol ?? "local-dev",
				tlsVersion: request.cf?.tlsVersion ?? "local-dev",
				note: "Cloudflare edge metadata is available after deployment.",
				timestamp,
			});
		}

		return notFound(url.pathname);
	},
} satisfies ExportedHandler<Env>;
