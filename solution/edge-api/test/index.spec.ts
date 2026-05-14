import { createExecutionContext, waitOnExecutionContext, SELF } from "cloudflare:test";
import { describe, it, expect } from "vitest";
import worker from "../src/index";
import type { Env } from "../src/index";

const IncomingRequest = Request<unknown, IncomingRequestCfProperties>;

function createKvMock(): KVNamespace {
	const data = new Map<string, string>();
	return {
		async get(key: string) {
			return data.get(key) ?? null;
		},
		async put(key: string, value: string) {
			data.set(key, value);
		},
	} as unknown as KVNamespace;
}

function createEnv(): Env {
	return {
		APP_NAME: "edge-api",
		COURSE_NAME: "devops-core",
		ENVIRONMENT: "test",
		API_VERSION: "test",
		API_TOKEN: "test-token",
		ADMIN_EMAIL: "admin@example.test",
		SETTINGS: createKvMock(),
	};
}

describe("edge-api worker", () => {
	it("returns health information", async () => {
		const request = new IncomingRequest("http://example.com/health");
		const ctx = createExecutionContext();
		const response = await worker.fetch(request, createEnv(), ctx);

		await waitOnExecutionContext(ctx);

		expect(response.status).toBe(200);
		expect(await response.json()).toMatchObject({
			status: "ok",
			app: "edge-api",
			kv: true,
		});
	});

	it("increments a KV-backed counter", async () => {
		const env = createEnv();
		const request = new IncomingRequest("http://example.com/counter");
		const ctx = createExecutionContext();

		const response = await worker.fetch(request, env, ctx);
		const secondResponse = await worker.fetch(request, env, ctx);

		await waitOnExecutionContext(ctx);

		expect(await response.json()).toMatchObject({ visits: 1 });
		expect(await secondResponse.json()).toMatchObject({ visits: 2 });
	});

	it("stores and reads a setting from KV", async () => {
		const env = createEnv();
		const ctx = createExecutionContext();
		const write = new IncomingRequest("http://example.com/settings", {
			method: "POST",
			body: JSON.stringify({ value: "persisted after redeploy" }),
			headers: { "content-type": "application/json" },
		});
		const read = new IncomingRequest("http://example.com/settings");

		const writeResponse = await worker.fetch(write, env, ctx);
		const readResponse = await worker.fetch(read, env, ctx);

		await waitOnExecutionContext(ctx);

		expect(writeResponse.status).toBe(201);
		expect(await readResponse.json()).toMatchObject({
			key: "lab17-note",
			value: "persisted after redeploy",
			found: true,
		});
	});

	it("responds through the worker test runtime", async () => {
		const response = await SELF.fetch("https://example.com/health");

		expect(response.status).toBe(200);
	});
});
