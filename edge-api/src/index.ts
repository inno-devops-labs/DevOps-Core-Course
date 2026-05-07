export interface Env {
	APP_NAME?: string;
	COURSE_NAME?: string;
	ENVIRONMENT?: string;
	APP_VERSION?: string;
	API_TOKEN?: string;
	ADMIN_EMAIL?: string;
	SETTINGS: KVNamespace;
}

type JsonBody = Record<string, unknown>;

function jsonResponse(body: JsonBody, status = 200): Response {
	return Response.json(body, {
		status,
		headers: {
			"content-type": "application/json; charset=utf-8",
		},
	});
}

function configured(value: unknown): boolean {
	return typeof value === "string" && value.length > 0;
}

function getRoutes(): string[] {
	return [
		"/",
		"/health",
		"/deployment",
		"/edge",
		"/config",
		"/counter",
		"/counter/read",
	];
}

function notFound(pathname: string): Response {
	return jsonResponse(
		{
			error: "Not Found",
			message: "Endpoint does not exist",
			path: pathname,
			availableRoutes: getRoutes(),
		},
		404,
	);
}

async function readCounter(env: Env): Promise<number> {
	const raw = await env.SETTINGS.get("visits");
	const parsed = Number.parseInt(raw ?? "0", 10);
	return Number.isFinite(parsed) ? parsed : 0;
}

async function incrementCounter(env: Env): Promise<number> {
	const visits = (await readCounter(env)) + 1;
	await env.SETTINGS.put("visits", String(visits));
	return visits;
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
					name: env.APP_NAME ?? "edge-api",
					description: "Cloudflare Workers API for DevOps Core Course",
					runtime: "Cloudflare Workers",
				},
				course: env.COURSE_NAME ?? "DevOps Core Course",
				environment: env.ENVIRONMENT ?? "unknown",
				version: env.APP_VERSION ?? "unknown",
				message: "Hello from Cloudflare Workers",
				routes: getRoutes(),
				timestamp,
			});
		}

		if (url.pathname === "/health") {
			return jsonResponse({
				status: "healthy",
				service: env.APP_NAME ?? "edge-api",
				timestamp,
			});
		}

		if (url.pathname === "/deployment") {
			return jsonResponse({
				application: env.APP_NAME ?? "edge-api",
				platform: "Cloudflare Workers",
				language: "TypeScript",
				environment: env.ENVIRONMENT ?? "workers.dev",
				version: env.APP_VERSION ?? "lab17-task4",
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

		if (url.pathname === "/config") {
			return jsonResponse({
				appName: env.APP_NAME ?? null,
				courseName: env.COURSE_NAME ?? null,
				environment: env.ENVIRONMENT ?? null,
				version: env.APP_VERSION ?? null,
				secrets: {
					apiTokenConfigured: configured(env.API_TOKEN),
					adminEmailConfigured: configured(env.ADMIN_EMAIL),
				},
				kv: {
					settingsBindingAvailable: Boolean(env.SETTINGS),
				},
				note: "Secret values are not returned by this endpoint.",
				timestamp,
			});
		}

		if (url.pathname === "/counter") {
			const visits = await incrementCounter(env);

			return jsonResponse({
				key: "visits",
				visits,
				storage: "Workers KV",
				operation: "read-increment-write",
				timestamp,
			});
		}

		if (url.pathname === "/counter/read") {
			const visits = await readCounter(env);

			return jsonResponse({
				key: "visits",
				visits,
				storage: "Workers KV",
				operation: "read",
				timestamp,
			});
		}

		return notFound(url.pathname);
	},
} satisfies ExportedHandler<Env>;
