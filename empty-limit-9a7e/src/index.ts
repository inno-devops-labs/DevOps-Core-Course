export default {
  async fetch(request: Request, env: any): Promise<Response> {
    const url = new URL(request.url);

	console.log("Request received:", url.pathname);

    // /edge — главный endpoint для Task 3
    if (url.pathname === "/edge") {
      return new Response(
        JSON.stringify({
          colo: request.cf?.colo,
          country: request.cf?.country,
          city: request.cf?.city,
          asn: request.cf?.asn,
          httpProtocol: request.cf?.httpProtocol,
          tlsVersion: request.cf?.tlsVersion,
        }),
        { headers: { "Content-Type": "application/json" } }
      );
    }

    // остальные endpoints (оставь из Task 2)
    if (url.pathname === "/health") {
      return new Response(JSON.stringify({ status: "ok" }), {
        headers: { "Content-Type": "application/json" },
      });
    }

    if (url.pathname === "/meta") {
      return new Response(
        JSON.stringify({
          deployedAt: new Date().toISOString(),
        }),
        { headers: { "Content-Type": "application/json" } }
      );
    }

	if (url.pathname === "/config") {
		return new Response(
			JSON.stringify({
			env: env.ENVIRONMENT,
			}),
			{ headers: { "Content-Type": "application/json" } }
		);
	}

	if (url.pathname === "/secrets") {
		return new Response(
			JSON.stringify({
			apiKeyExists: !!env.API_KEY,
			dbPasswordExists: !!env.DB_PASSWORD,
			}),
			{ headers: { "Content-Type": "application/json" } }
		);
	}

	if (url.pathname === "/kv-set") {
		await env.MY_KV.put("message", "Hello KV storage!");
		return new Response("Stored!");
	}

	// получить значение
	if (url.pathname === "/kv-get") {
		const value = await env.MY_KV.get("message");
		return new Response(
			JSON.stringify({ value }),
			{ headers: { "Content-Type": "application/json" } }
		);
	}

    return new Response("Not Found", { status: 404 });
  },
};