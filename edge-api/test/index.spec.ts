import {
	env,
	createExecutionContext,
	waitOnExecutionContext,
} from "cloudflare:test";
import { describe, it, expect } from "vitest";
import worker from "../src/index";

const IncomingRequest = Request<unknown, IncomingRequestCfProperties>;

describe("edge-api worker", () => {
	it("GET / returns JSON with app info", async () => {
		const req = new IncomingRequest("http://example.com/");
		const ctx = createExecutionContext();
		const res = await worker.fetch(req, env, ctx);
		await waitOnExecutionContext(ctx);
		expect(res.status).toBe(200);
		const body = await res.json() as Record<string, unknown>;
		expect(body.app).toBe("devops-edge-api");
		expect(body.message).toBe("Hello from Cloudflare Workers edge");
	});

	it("GET /health returns status ok", async () => {
		const req = new IncomingRequest("http://example.com/health");
		const ctx = createExecutionContext();
		const res = await worker.fetch(req, env, ctx);
		await waitOnExecutionContext(ctx);
		expect(res.status).toBe(200);
		const body = await res.json() as Record<string, unknown>;
		expect(body.status).toBe("ok");
	});

	it("GET /info returns route list", async () => {
		const req = new IncomingRequest("http://example.com/info");
		const ctx = createExecutionContext();
		const res = await worker.fetch(req, env, ctx);
		await waitOnExecutionContext(ctx);
		expect(res.status).toBe(200);
		const body = await res.json() as Record<string, unknown>;
		expect(Array.isArray(body.routes)).toBe(true);
		expect(body.routes).toContain("/health");
	});

	it("GET /edge returns cf metadata fields", async () => {
		const req = new IncomingRequest("http://example.com/edge");
		const ctx = createExecutionContext();
		const res = await worker.fetch(req, env, ctx);
		await waitOnExecutionContext(ctx);
		expect(res.status).toBe(200);
		const body = await res.json() as Record<string, unknown>;
		expect(Object.keys(body)).toEqual(
			expect.arrayContaining(["colo", "country", "httpProtocol", "tlsVersion"])
		);
	});

	it("GET /unknown returns 404", async () => {
		const req = new IncomingRequest("http://example.com/unknown");
		const ctx = createExecutionContext();
		const res = await worker.fetch(req, env, ctx);
		await waitOnExecutionContext(ctx);
		expect(res.status).toBe(404);
	});
});
