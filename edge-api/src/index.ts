const WORKER_NAME = "edge-api";
const API_VERSION = "task-5";

interface WorkerEnv {
	APP_NAME: string;
	COURSE_NAME: string;
	API_TOKEN?: string;
	ADMIN_EMAIL?: string;
	SETTINGS: KVNamespace;
}

const routes = ["/", "/health", "/edge", "/metadata", "/config", "/counter"];

function json(data: unknown, init: ResponseInit = {}): Response {
	const headers = new Headers(init.headers);
	headers.set("content-type", "application/json; charset=utf-8");
	headers.set("cache-control", "no-store");

	return Response.json(data, {
		...init,
		headers,
	});
}

function secretStatus(env: WorkerEnv) {
	const adminEmailDomain = env.ADMIN_EMAIL?.includes("@")
		? env.ADMIN_EMAIL.split("@").at(-1)
		: null;

	return {
		apiTokenConfigured: Boolean(env.API_TOKEN),
		adminEmailConfigured: Boolean(env.ADMIN_EMAIL),
		adminEmailDomain,
	};
}

export default {
	async fetch(request, env): Promise<Response> {
		const url = new URL(request.url);
		const timestamp = new Date().toISOString();
		const app = env.APP_NAME || WORKER_NAME;

		console.log("request", {
			method: request.method,
			path: url.pathname,
			colo: request.cf?.colo ?? "local",
			country: request.cf?.country ?? "local",
			version: API_VERSION,
		});

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
				app,
				message: "Hello from Cloudflare Workers",
				course: env.COURSE_NAME,
				version: API_VERSION,
				routes,
				timestamp,
			});
		}

		if (url.pathname === "/health") {
			return json({
				status: "ok",
				service: app,
				timestamp,
			});
		}

		if (url.pathname === "/edge") {
			return json({
				app,
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
				app,
				version: API_VERSION,
				runtime: "cloudflare-workers",
				workerUrlPattern: `https://${WORKER_NAME}.neilzvest.workers.dev`,
				compatibilityDate: "2026-05-14",
				configuration: {
					course: env.COURSE_NAME,
					...secretStatus(env),
				},
				timestamp,
			});
		}

		if (url.pathname === "/config") {
			return json({
				app,
				course: env.COURSE_NAME,
				plaintextVars: ["APP_NAME", "COURSE_NAME"],
				secrets: secretStatus(env),
				note: "Secret values are read from env but are not returned.",
				timestamp,
			});
		}

		if (url.pathname === "/counter") {
			const key = "visits";
			const rawVisits = await env.SETTINGS.get(key);
			const visits = Number(rawVisits ?? "0") + 1;

			await env.SETTINGS.put(key, String(visits));

			return json({
				key,
				visits,
				persistedIn: "Workers KV",
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
} satisfies ExportedHandler<WorkerEnv>;
