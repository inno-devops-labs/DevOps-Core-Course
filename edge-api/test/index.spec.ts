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
	it("returns deployment metadata from the root route", async () => {
		const request = new IncomingRequest("http://example.com");
		const ctx = createExecutionContext();
		const response = await worker.fetch(request, env, ctx);
		await waitOnExecutionContext(ctx);

		expect(response.status).toBe(200);
		const body = await response.json<{
			app: string;
			runtime: string;
			routes: Array<{ path: string }>;
		}>();
		expect(body.app).toBe("edge-api");
		expect(body.runtime).toBe("cloudflare-workers");
		expect(body.routes.map((route) => route.path)).toContain("/health");
	});

	it("returns a health response", async () => {
		const response = await SELF.fetch("https://example.com/health");

		expect(response.status).toBe(200);
		await expect(response.json()).resolves.toMatchObject({
			status: "ok",
			app: "edge-api",
		});
	});

	it("returns edge metadata with local fallbacks", async () => {
		const response = await SELF.fetch("https://example.com/edge");

		expect(response.status).toBe(200);
		await expect(response.json()).resolves.toMatchObject({
			colo: "local-dev",
			country: "local-dev",
		});
	});

	it("persists and increments the counter in KV", async () => {
		const first = await SELF.fetch("https://example.com/counter");
		const second = await SELF.fetch("https://example.com/counter");

		expect(first.status).toBe(200);
		expect(second.status).toBe(200);
		await expect(first.json()).resolves.toMatchObject({ key: "visits", visits: 1 });
		await expect(second.json()).resolves.toMatchObject({ key: "visits", visits: 2 });
	});

	it("returns 404 JSON for unknown routes", async () => {
		const response = await SELF.fetch("https://example.com/missing");

		expect(response.status).toBe(404);
		await expect(response.json()).resolves.toMatchObject({
			error: "Not Found",
			path: "/missing",
		});
	});
});
