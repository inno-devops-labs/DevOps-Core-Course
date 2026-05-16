Lab 17 - Cloudflare Workers Edge Deployment



Task 1 - Cloudflare Setup

Account Created

Cloudflare account created with email: nadya.tarubarova@bk.ru



Workers Project Created

Project name: lab17-worker

Location: C:\\lab1-devops\\lab1\\DevOps-Core-Course\\cloudflare-worker\\lab17-worker

Template: Hello World Worker with TypeScript



Wrangler CLI Authentication

powershell

npx wrangler whoami

Output:



text

👋 You are logged in with an OAuth Token, associated with the email nadya.tarubarova@bk.ru.

Account Name: Nadya.tarubarova@bk.ru's Account

Account ID: b990430b572cdd8008779511bcb0e9ab



Task 2 - Build and Deploy Worker API

Implemented Endpoints

Endpoint	Method	Description

/	GET	API information and available endpoints

/health	GET	Health check endpoint

/metadata	GET	Edge request metadata (colo, country, city, asn)

/config	GET	Configuration status (variables, secrets, KV)

/kv/read	GET	Read value from KV storage

/kv/write	POST	Write value to KV storage

Deployment

powershell

npx wrangler deploy

Output:



text

Uploaded lab17-worker (6.81 sec)

Deployed lab17-worker triggers (5.80 sec)

https://lab17-worker.nadia-lab17.workers.dev

Testing Endpoints

Health Check:



powershell

cmd /c "curl -s https://lab17-worker.nadia-lab17.workers.dev/health"

json

{"status":"healthy","timestamp":"2026-05-16T03:09:12.384Z","service":"cloudflare-worker-api"}

Edge Metadata:



powershell

cmd /c "curl -s https://lab17-worker.nadia-lab17.workers.dev/metadata"

json

{"colo":"GRU","country":"BR","city":"Belo Horizonte","asn":271354,"httpProtocol":"HTTP/1.1","tlsVersion":"TLSv1.3","timezone":"America/Sao\_Paulo"}

Configuration Status:



powershell

cmd /c "curl -s https://lab17-worker.nadia-lab17.workers.dev/config"

json

{"plaintextVariable":"not set","secretConfigured":true,"kvConfigured":true}

Root Endpoint:



powershell

cmd /c "curl -s https://lab17-worker.nadia-lab17.workers.dev/"

json

{"name":"Cloudflare Worker API","version":"1.0.0","endpoints":\[...]}



Task 3 - Global Edge Behavior

Edge Metadata Analysis

The /metadata endpoint reveals Cloudflare's global network information:



colo: GRU (Sao Paulo, Brazil) - the data center that processed the request



country: BR - country code of the edge location



city: Belo Horizonte - city of the edge node



asn: 271354 - Autonomous System Number



httpProtocol: HTTP/1.1 - protocol version used



tlsVersion: TLSv1.3 - TLS version for secure connection



Global Distribution Explanation

Cloudflare Workers automatically deploys code to all of Cloudflare's 300+ global data centers. There is no "deploy to specific regions" step because:



Workers run on every request at the nearest edge location



The runtime is consistent across all locations



Cold starts are minimized by keeping code cached at edge



This differs from traditional PaaS where you must manually select VM regions



Routing Concepts

workers.dev: Free subdomain provided by Cloudflare for testing (https://lab17-worker.nadia-lab17.workers.dev)



Routes: Custom domains mapped to Workers for production use



Custom Domains: Your own domain (e.g., api.example.com) configured via Cloudflare DNS



Task 4 - Configuration, Secrets \& Persistence

Environment Variables (Plaintext)

Configured in wrangler.jsonc:



json

"vars": {

&#x20; "MY\_VARIABLE": "Hello from Cloudflare Workers!"

}

Secrets

Created two secrets using Wrangler CLI:



powershell

npx wrangler secret put MY\_SECRET

\# Value: supersecret123



npx wrangler secret put ANOTHER\_SECRET

\# Value: anothersecret456

Secrets are encrypted and not visible in dashboard or version control.



KV Namespace

Created KV namespace:



powershell

npx wrangler kv namespace create MY\_KV

Output:



text

Success! Created KV namespace with id: f192864a09174897bb4b9b78680dc5f3

Binding configured in wrangler.jsonc:



json

"kv\_namespaces": \[

&#x20; {

&#x20;   "binding": "MY\_KV",

&#x20;   "id": "f192864a09174897bb4b9b78680dc5f3"

&#x20; }

]



Task 5 - Observability \& Operations

Logs (Console.log)

Added console.log statement in fetch handler:



typescript

console.log(`Request received: ${request.method} ${path}`);

To view logs:



powershell

npx wrangler tail

Metrics

In Cloudflare Dashboard (Workers \& Pages → lab17-worker → Metrics):



Request count



Request duration



CPU time



Subrequest count



Error rate



Deployment History \& Rollback

Deploy multiple versions:



powershell

npx wrangler deploy

View deployment history:



powershell

npx wrangler deployments list

Rollback to previous version:



powershell

npx wrangler rollback

Current deployment versions:



Version 1: 93f9ba3f-74a6-4a41-a5cc-36dbaa797ddb



Version 2: 3faa2298-0fa0-45d0-b0d2-b3ff764bc19c



Version 3: c8c9f150-33c6-4099-9864-822abfbecacd



Version 4: 21bbddc2-9848-4ff7-be56-b4e869f82b3d



Task 6 - Kubernetes vs Cloudflare Workers Comparison

Comparison Table

Aspect	Kubernetes	Cloudflare Workers

Setup complexity	High (cluster, nodes, networking)	Low (npm create cloudflare)

Deployment speed	Minutes to hours	Seconds

Global distribution	Manual (choose regions)	Automatic (300+ edge locations)

Cost (small apps)	$10-50/month (control plane)	Free tier available

State/persistence	PVC, databases, PV	KV, D1, R2, Durables

Control/flexibility	Full OS control	Runtime-limited, but powerful

Cold starts	Minimal	Can occur, usually <5ms

Language support	Any (container)	JavaScript, TypeScript, Python, Rust, Go

When to Use Each

Use Kubernetes when:



Need full OS control or custom binaries



Running long-running stateful services



Require specific GPU/TPU hardware



Have complex networking requirements



Need to run Docker containers as-is



Compliance requires self-hosted infrastructure



Use Cloudflare Workers when:



Building globally distributed APIs



Need low latency worldwide



Want serverless simplicity



Handling unpredictable traffic spikes



Doing request transformation at edge



Building JAMstack or BFF patterns



Reflection

What felt easier than Kubernetes?



Zero infrastructure setup - no clusters, nodes, or networking



Instant global deployment - no region selection



Built-in secrets management - no Vault or External Secrets



Automatic HTTPS and custom domains



Simple CLI and local development



What felt more constrained?



Execution time limits (30ms free, 30s paid)



No native WebSocket server support



Limited CPU and memory (vs Kubernetes pods)



No arbitrary Docker containers



Storage options (KV vs persistent volumes)



What changed because Workers is not a Docker host?



No container images - code is uploaded directly



No image registry management



No Dockerfile needed



Different approach to dependencies (package.json vs container layers)



Different state model (KV vs PVC)



Conclusion



Lab 17 completed with:



Cloudflare account and Workers project created



Worker API deployed with 6 endpoints (/health, /metadata, /config, /, /kv/read, /kv/write)



Edge metadata successfully retrieved from Brazil edge location



Environment variables and secrets configured



KV namespace created and bound



Multiple versions deployed with rollback capability



Documentation and comparison with Kubernetes completed



Worker URL: https://lab17-worker.nadia-lab17.workers.dev

