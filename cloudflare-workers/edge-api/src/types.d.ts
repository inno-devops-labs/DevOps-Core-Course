export {};

declare global {
  interface KVNamespace {
    get(key: string): Promise<string | null>;
    put(key: string, value: string): Promise<void>;
  }

  interface CloudflareRequestMetadata {
    colo?: string;
    country?: string;
    city?: string;
    asn?: number;
    httpProtocol?: string;
    tlsVersion?: string;
  }

  interface Request {
    cf?: CloudflareRequestMetadata;
  }
}
