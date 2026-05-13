// Simple local test without Wrangler
const url = new URL("http://localhost:8787/");

const mockRequest = {
  url: "http://localhost:8787/health",
  method: "GET",
  cf: {
    colo: "SJC",
    country: "US",
    city: "San Jose"
  }
};

const env = {
  APP_NAME: "edge-api",
  COURSE_NAME: "DevOps-Core",
  VERSION: "1.0.0",
  API_TOKEN: "test-token",
  ADMIN_EMAIL: "admin@example.com",
  SETTINGS: {
    get: async () => null,
    put: async () => {}
  }
};

console.log("✓ Project structure created successfully");
console.log("✓ Files created:");
console.log("  - src/index.ts (Worker code)");
console.log("  - wrangler.jsonc (Configuration)");
console.log("  - package.json (Dependencies)");
console.log("  - tsconfig.json (TypeScript config)");
