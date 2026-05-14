import { Hono } from "hono";

type WorkerEnv = {
	APP_NAME: string;
	COURSE_NAME: string;
	APP_VERSION: string;
	ENVIRONMENT: string;
	API_TOKEN?: string;
	ADMIN_EMAIL?: string;
	SETTINGS: KVNamespace;
};

type CloudflareRequest = Request & {
	cf?: Record<string, unknown>;
};

const counterKey = "lab17-counter";
const routes = [
	{ method: "GET", path: "/", description: "Application metadata and route index" },
	{ method: "GET", path: "/health", description: "Health probe for uptime checks" },
	{ method: "GET", path: "/edge", description: "Selected Cloudflare edge request metadata" },
	{ method: "GET", path: "/config", description: "Plaintext config and redacted secret status" },
	{ method: "GET", path: "/counter", description: "Read the KV-backed counter" },
	{ method: "POST", path: "/counter", description: "Increment the KV-backed counter" },
] as const;

const app = new Hono<{ Bindings: WorkerEnv }>();

const cfString = (cf: Record<string, unknown>, key: string): string | null => {
	const value = cf[key];

	return typeof value === "string" ? value : null;
};

const cfNumber = (cf: Record<string, unknown>, key: string): number | null => {
	const value = cf[key];

	return typeof value === "number" ? value : null;
};

const secretStatus = (value: string | undefined) => ({
	configured: Boolean(value),
	value: value ? "[redacted]" : null,
});

app.use("*", async (c, next) => {
	const request = c.req.raw as CloudflareRequest;
	const cf = request.cf ?? {};
	const path = new URL(c.req.url).pathname;

	console.log(
		JSON.stringify({
			event: "request",
			method: c.req.method,
			path,
			colo: cfString(cf, "colo"),
			country: cfString(cf, "country"),
		}),
	);

	await next();
});

app.get("/", (c) => {
	return c.json({
		app: c.env.APP_NAME,
		course: c.env.COURSE_NAME,
		version: c.env.APP_VERSION,
		environment: c.env.ENVIRONMENT,
		routes,
	});
});

app.get("/health", (c) => {
	return c.json({
		status: "ok",
		service: c.env.APP_NAME,
		version: c.env.APP_VERSION,
		timestamp: new Date().toISOString(),
	});
});

app.get("/edge", (c) => {
	const request = c.req.raw as CloudflareRequest;
	const cf = request.cf ?? {};

	return c.json({
		colo: cfString(cf, "colo"),
		country: cfString(cf, "country"),
		city: cfString(cf, "city"),
		region: cfString(cf, "region"),
		postalCode: cfString(cf, "postalCode"),
		timezone: cfString(cf, "timezone"),
		asn: cfNumber(cf, "asn"),
		asOrganization: cfString(cf, "asOrganization"),
		httpProtocol: cfString(cf, "httpProtocol"),
		tlsVersion: cfString(cf, "tlsVersion"),
	});
});

app.get("/config", (c) => {
	return c.json({
		vars: {
			APP_NAME: c.env.APP_NAME,
			COURSE_NAME: c.env.COURSE_NAME,
			APP_VERSION: c.env.APP_VERSION,
			ENVIRONMENT: c.env.ENVIRONMENT,
		},
		secrets: {
			API_TOKEN: secretStatus(c.env.API_TOKEN),
			ADMIN_EMAIL: secretStatus(c.env.ADMIN_EMAIL),
		},
		kv: {
			binding: "SETTINGS",
			counterKey,
		},
	});
});

app.get("/counter", async (c) => {
	const rawValue = await c.env.SETTINGS.get(counterKey);
	const value = Number.parseInt(rawValue ?? "0", 10);

	return c.json({
		key: counterKey,
		value: Number.isFinite(value) ? value : 0,
		persisted: rawValue !== null,
	});
});

app.post("/counter", async (c) => {
	const rawValue = await c.env.SETTINGS.get(counterKey);
	const currentValue = Number.parseInt(rawValue ?? "0", 10);
	const previous = Number.isFinite(currentValue) ? currentValue : 0;
	const value = previous + 1;

	await c.env.SETTINGS.put(counterKey, value.toString());

	return c.json({
		key: counterKey,
		previous,
		value,
		persisted: true,
	});
});

app.notFound((c) => {
	return c.json(
		{
			error: "not_found",
			path: new URL(c.req.url).pathname,
			routes,
		},
		404,
	);
});

app.onError((error, c) => {
	console.error(
		JSON.stringify({
			event: "error",
			message: error.message,
			path: new URL(c.req.url).pathname,
		}),
	);

	return c.json(
		{
			error: "internal_error",
			message: "Unexpected Worker error",
		},
		500,
	);
});

export default app;
