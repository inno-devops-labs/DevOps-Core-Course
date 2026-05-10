import {
  env,
  SELF,
} from "cloudflare:test";

import { describe, it, expect } from "vitest";
import worker from "../src/index";

const IncomingRequest = Request<unknown, IncomingRequestCfProperties>;

describe("Edge API worker", () => {
  it("responds from root endpoint", async () => {
    const request = new IncomingRequest("http://example.com");

    const response = await worker.fetch(request, env);

    expect(response.status).toBe(200);

    const text = await response.text();

    expect(text).toContain("Hello friend!");
  });

  it("responds from integration test", async () => {
    const response = await SELF.fetch("https://example.com");

    expect(response.status).toBe(200);

    const text = await response.text();

    expect(text).toContain("Hello friend!");
  });
});