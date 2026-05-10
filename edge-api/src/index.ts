/**
 * edge-api — Lab 17 Cloudflare Worker.
 *
 * Routes:
 *   GET /          — service info (vars + uptime)
 *   GET /health    — liveness
 *   GET /edge      — request.cf metadata (Task 3)
 *   GET /counter   — KV-backed visit counter (Task 4 persistence)
 *   GET /whoami    — secrets-backed admin info, redacted (Task 4 secrets)
 *   *              — 404 JSON
 *
 * Bindings (see wrangler.jsonc):
 *   APP_NAME      — plaintext var
 *   COURSE_NAME   — plaintext var
 *   API_TOKEN     — secret (set via `wrangler secret put`)
 *   ADMIN_EMAIL   — secret (set via `wrangler secret put`)
 *   SETTINGS      — KV namespace
 */

export interface Env {
	APP_NAME: string;
	COURSE_NAME: string;
	API_TOKEN: string;
	ADMIN_EMAIL: string;
	SETTINGS: KVNamespace;
}

// Workers V8 isolates do not return wall time at module init (timing-attack
// mitigation), so we lazily seed the start timestamp on the first fetch.
let START = 0;
const VERSION = "1.0.1";

function maskTail(value: string | undefined, keep = 4): string {
	if (!value) return "<unset>";
	if (value.length <= keep) return "*".repeat(value.length);
	return "*".repeat(value.length - keep) + value.slice(-keep);
}

function maskEmail(email: string | undefined): string {
	if (!email) return "<unset>";
	const [user, domain] = email.split("@", 2);
	if (!domain) return maskTail(email);
	const head = user.length <= 2 ? user[0] ?? "*" : user.slice(0, 2);
	return `${head}***@${domain}`;
}

export default {
	async fetch(request: Request, env: Env, _ctx: ExecutionContext): Promise<Response> {
		const url = new URL(request.url);
		const t0 = Date.now();
		if (START === 0) START = t0;

		// Structured edge log — visible via `wrangler tail` and Workers Logs.
		console.log(
			JSON.stringify({
				level: "info",
				event: "request_start",
				method: request.method,
				path: url.pathname,
				colo: request.cf?.colo ?? null,
				country: request.cf?.country ?? null,
				ts: new Date().toISOString(),
			}),
		);

		const response = await route(request, env, url);

		console.log(
			JSON.stringify({
				level: "info",
				event: "request_end",
				path: url.pathname,
				status: response.status,
				duration_ms: Date.now() - t0,
			}),
		);

		return response;
	},
} satisfies ExportedHandler<Env>;

async function route(request: Request, env: Env, url: URL): Promise<Response> {
	switch (url.pathname) {
		case "/":
			return Response.json({
				service: env.APP_NAME ?? "edge-api",
				course: env.COURSE_NAME ?? "devops-core",
				version: VERSION,
				message: "Hello from Cloudflare Workers — v2 (deployment-history demo)",
				isolate_uptime_ms: START === 0 ? 0 : Date.now() - START,
				timestamp: new Date().toISOString(),
				routes: ["/", "/health", "/edge", "/counter", "/whoami"],
			});

		case "/health":
			return Response.json({
				status: "ok",
				timestamp: new Date().toISOString(),
			});

		case "/edge":
			// Cloudflare populates request.cf with edge-side metadata.
			// In `wrangler dev` (local mode) most fields are null — that's expected;
			// they appear once the Worker runs on the real edge.
			return Response.json({
				colo: request.cf?.colo ?? null,
				country: request.cf?.country ?? null,
				city: request.cf?.city ?? null,
				region: request.cf?.region ?? null,
				asn: request.cf?.asn ?? null,
				asOrganization: request.cf?.asOrganization ?? null,
				httpProtocol: request.cf?.httpProtocol ?? null,
				tlsVersion: request.cf?.tlsVersion ?? null,
				timezone: request.cf?.timezone ?? null,
				clientTcpRtt: request.cf?.clientTcpRtt ?? null,
				note:
					"Fields are populated by Cloudflare's edge runtime. Local `wrangler dev` returns nulls — deploy and re-test against the workers.dev URL.",
			});

		case "/counter": {
			// KV-backed visits counter. Read → increment → write.
			// KV is eventually consistent — fine for a demo counter.
			const raw = await env.SETTINGS.get("visits");
			const visits = Number(raw ?? "0") + 1;
			await env.SETTINGS.put("visits", String(visits));

			console.log(
				JSON.stringify({
					level: "info",
					event: "counter_inc",
					previous: Number(raw ?? "0"),
					next: visits,
				}),
			);

			return Response.json({
				visits,
				key: "visits",
				note: "Persisted in Workers KV (binding SETTINGS); survives redeploys.",
			});
		}

		case "/whoami":
			// Secrets are read from env but never returned in plaintext.
			return Response.json({
				app: env.APP_NAME ?? "edge-api",
				admin_email: maskEmail(env.ADMIN_EMAIL),
				api_token: maskTail(env.API_TOKEN),
				note:
					"Both ADMIN_EMAIL and API_TOKEN are Wrangler secrets (`wrangler secret put`). Values shown here are redacted; only the last 4 characters of API_TOKEN and the domain of ADMIN_EMAIL are visible.",
			});

		default:
			return Response.json(
				{
					error: "not_found",
					path: url.pathname,
					known: ["/", "/health", "/edge", "/counter", "/whoami"],
				},
				{ status: 404 },
			);
	}
}
