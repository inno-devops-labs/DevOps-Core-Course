import {
	env,
	createExecutionContext,
	waitOnExecutionContext,
	SELF,
} from "cloudflare:test";
import { describe, it, expect } from "vitest";
import worker from "../src/index";

const IncomingRequest = Request<unknown, IncomingRequestCfProperties>;

describe("edge API worker", () => {
	it("responds to /health with JSON status", async () => {
		const request = new IncomingRequest("http://example.com/health");
		const ctx = createExecutionContext();
		const response = await worker.fetch(request, env, ctx);
		await waitOnExecutionContext(ctx);

		expect(response.status).toBe(200);
		expect(response.headers.get("content-type")).toContain("application/json");
		await expect(response.json()).resolves.toMatchObject({
			status: "ok",
			app: "edge-api",
		});
	});

	it("returns 404 JSON for unknown routes", async () => {
		const response = await SELF.fetch("https://example.com/unknown");

		expect(response.status).toBe(404);
		await expect(response.json()).resolves.toMatchObject({
			error: "not_found",
			path: "/unknown",
		});
	});
});
