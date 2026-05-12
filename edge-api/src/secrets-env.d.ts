/** Wrangler secrets (not in wrangler.jsonc); set with `wrangler secret put`. */
declare namespace Cloudflare {
	interface Env {
		API_TOKEN: string;
		ADMIN_EMAIL: string;
	}
}
