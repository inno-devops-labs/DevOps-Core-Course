import { describe, expect, it } from "vitest";
import worker from "./index";

const settings = new Map<string, string>();

const env = {
	APP_NAME: "devops-lab17",
	COURSE_NAME: "devops-core",
	DEPLOYMENT_NOTE: "test",
	API_TOKEN: "token",
	ADMIN_EMAIL: "k.nosov@innopolis.university",
	SETTINGS: {
		async get(key: string) {
			return settings.get(key) ?? null;
		},
		async put(key: string, value: string) {
			settings.set(key, value);
		},
	},
} as unknown as Env;

describe("devops-lab17 worker", () => {
	it("returns health status", async () => {
		const response = await worker.fetch(new Request("https://devops-lab17.k-nosov.workers.dev/health"), env, {} as ExecutionContext);

		expect(response.status).toBe(200);
		expect(await response.json()).toEqual({ status: "ok" });
	});

	it("returns config without exposing secret values", async () => {
		const response = await worker.fetch(new Request("https://devops-lab17.k-nosov.workers.dev/config"), env, {} as ExecutionContext);
		const body = await response.json() as {
			appName: string;
			secretsConfigured: { API_TOKEN: boolean; ADMIN_EMAIL: boolean };
		};

		expect(body.appName).toBe("devops-lab17");
		expect(body.secretsConfigured).toEqual({ API_TOKEN: true, ADMIN_EMAIL: true });
		expect(JSON.stringify(body)).not.toContain("token");
		expect(JSON.stringify(body)).not.toContain("k.nosov@innopolis.university");
	});

	it("increments the KV-backed counter", async () => {
		settings.clear();

		const first = await worker.fetch(new Request("https://devops-lab17.k-nosov.workers.dev/counter"), env, {} as ExecutionContext);
		const second = await worker.fetch(new Request("https://devops-lab17.k-nosov.workers.dev/counter"), env, {} as ExecutionContext);

		expect(await first.json()).toEqual({ visits: 1, key: "visits" });
		expect(await second.json()).toEqual({ visits: 2, key: "visits" });
	});
});
