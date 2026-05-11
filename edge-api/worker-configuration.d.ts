interface Env {
	APP_NAME: string;
	COURSE_NAME: string;
	DEPLOYMENT_ENV: string;
	API_TOKEN?: string;
	ADMIN_EMAIL?: string;
	SETTINGS?: KVNamespace;
}

interface IncomingRequestCfProperties {
	colo?: string;
	country?: string;
	city?: string;
	asn?: number;
	httpProtocol?: string;
	tlsVersion?: string;
}

interface Request {
	readonly cf?: IncomingRequestCfProperties;
}

interface KVNamespace {
	get(key: string): Promise<string | null>;
	put(key: string, value: string): Promise<void>;
}

interface ExecutionContext {
	waitUntil(promise: Promise<unknown>): void;
	passThroughOnException(): void;
}

interface ExportedHandler<Environment = unknown> {
	fetch(
		request: Request,
		env: Environment,
		ctx: ExecutionContext,
	): Response | Promise<Response>;
}
