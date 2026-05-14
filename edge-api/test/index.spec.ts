import {
	env,
	createExecutionContext,
	waitOnExecutionContext,
	SELF,
} from "cloudflare:test";
import { describe, it, expect } from "vitest";
import worker from "../src/index";

// For now, you'll need to do something like this to get a correctly-typed
// `Request` to pass to `worker.fetch()`.
const IncomingRequest = Request<unknown, IncomingRequestCfProperties>;

describe("edge-api worker", () => {
	it("responds with application metadata at / (unit style)", async () => {
		const request = new IncomingRequest("http://example.com");
		// Create an empty context to pass to `worker.fetch()`.
		const ctx = createExecutionContext();
		const response = await worker.fetch(request, env, ctx);
		// Wait for all `Promise`s passed to `ctx.waitUntil()` to settle before running test assertions
		await waitOnExecutionContext(ctx);
		expect(response.status).toBe(200);
		await expect(response.json()).resolves.toMatchObject({
			app: "edge-api",
			message: "Hello from Cloudflare Workers",
			course: "devops-core",
			version: "task-5",
		});
	});

	it("responds with health status", async () => {
		const response = await SELF.fetch("https://example.com/health");
		expect(response.status).toBe(200);
		await expect(response.json()).resolves.toMatchObject({
			status: "ok",
			service: "edge-api",
		});
	});

	it("responds with deployment metadata", async () => {
		const response = await SELF.fetch("https://example.com/metadata");
		expect(response.status).toBe(200);
		await expect(response.json()).resolves.toMatchObject({
			app: "edge-api",
			version: "task-5",
			runtime: "cloudflare-workers",
		});
	});

	it("responds with safe configuration metadata", async () => {
		const response = await SELF.fetch("https://example.com/config");
		expect(response.status).toBe(200);
		await expect(response.json()).resolves.toMatchObject({
			app: "edge-api",
			course: "devops-core",
			plaintextVars: ["APP_NAME", "COURSE_NAME"],
			note: "Secret values are read from env but are not returned.",
		});
	});

	it("persists a counter in KV", async () => {
		const first = await SELF.fetch("https://example.com/counter");
		const second = await SELF.fetch("https://example.com/counter");

		expect(first.status).toBe(200);
		expect(second.status).toBe(200);

		const firstBody = await first.json<{ visits: number }>();
		const secondBody = await second.json<{ visits: number }>();

		expect(secondBody.visits).toBe(firstBody.visits + 1);
		expect(secondBody).toMatchObject({
			key: "visits",
			persistedIn: "Workers KV",
		});
	});

	it("responds with edge metadata fields", async () => {
		const response = await SELF.fetch("https://example.com/edge");
		expect(response.status).toBe(200);
		const body = await response.json<Record<string, unknown>>();
		expect(body).toMatchObject({
			app: "edge-api",
		});
		expect(body).toHaveProperty("colo");
		expect(body).toHaveProperty("country");
		expect(body).toHaveProperty("asn");
		expect(body).toHaveProperty("httpProtocol");
		expect(body).toHaveProperty("tlsVersion");
	});

	it("returns 404 for unknown routes", async () => {
		const response = await SELF.fetch("https://example.com/missing");
		expect(response.status).toBe(404);
	});
});
