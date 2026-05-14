Lab 17 — Cloudflare Workers Edge Deployment

difficulty topic points type

    Build and deploy a serverless HTTP API on Cloudflare's global edge network using Cloudflare Workers.

Overview

Cloudflare Workers is a serverless edge platform for running code close to users worldwide without managing servers or choosing VM regions manually. Unlike Kubernetes or Docker-based PaaS platforms, Workers uses a lightweight runtime, automatic global distribution, built-in workers.dev URLs, and platform bindings for configuration, secrets, and state.

This is an Exam Alternative Lab — Complete both Lab 17 and Lab 18 to replace the final exam.

What You'll Learn:

    Edge computing concepts
    Serverless deployment workflows
    Cloudflare Workers and Wrangler CLI
    Global request metadata and routing
    Secrets, environment variables, and KV persistence
    Rollbacks and observability
    Kubernetes vs Workers trade-offs

Prerequisites:

    Git
    Node.js 18+ and npm
    Basic HTTP/JSON familiarity

Important: This lab does not deploy your Docker image from Lab 2. Cloudflare Workers is a serverless runtime, not a Docker host. You will build a Workers-native API that preserves similar operational concerns: routes, health checks, configuration, state, logs, deployments, and public access.

    Regional connectivity note: In some countries and networks, including Russia, Cloudflare services may be partially restricted. If commands such as npx wrangler whoami or npx wrangler deploy fail with vague network errors, the problem may be your network path rather than your code. If you use a VPN, prefer full-tunnel or global-routing mode. Proxy or split-tunnel setups can allow Node.js and Wrangler traffic to bypass the VPN and still hit the restricted network.

Tech Stack: Cloudflare Workers | Wrangler | TypeScript | Workers KV | workers.dev
Exam Alternative Requirements
Requirement 	Details
Deadline 	1 week before exam date
Minimum Score 	16/20 points
Must Complete 	Both Lab 17 AND Lab 18
Total Points 	40 pts (replaces 40 pt exam)
Tasks
Task 1 — Cloudflare Setup (3 pts)

Objective: Set up your Cloudflare account and Workers tooling.

Requirements:

    Create Account
        Sign up for a Cloudflare account
        Confirm you can access Workers from the dashboard
        Understand what a workers.dev subdomain is

    Create Project
        Create a new Workers project using C3 (create-cloudflare)
        Choose the Worker only template
        Use TypeScript for the required path in this lab

    Authenticate CLI
        Log in with Wrangler
        Verify your account with npx wrangler whoami
        Understand the role of wrangler.jsonc

    Explore Platform Concepts
        Understand the Workers runtime
        Understand workers.dev URLs
        Understand bindings: vars, secrets, and KV namespaces

💡 Hints

Task 2 — Build and Deploy a Worker API (4 pts)

Objective: Build a small HTTP API and deploy it to Cloudflare's edge.

Requirements:

    Implement Routes
        Create at least 3 HTTP endpoints
        Include /health
        Include one endpoint that returns JSON metadata about the deployment

    Run Locally
        Start local development with npx wrangler dev
        Test routes in the browser or with curl
        Verify correct status codes and JSON responses

    Deploy
        Deploy with npx wrangler deploy
        Access the public workers.dev URL
        Confirm the deployed Worker responds correctly

    Use Versioned Source Control
        Commit your Worker project to Git
        Keep a clean deployment history you can refer to later

💡 Hints

Task 3 — Global Edge Behavior (4 pts)

Objective: Inspect how your Worker behaves on Cloudflare's global network.

Requirements:

    Add Edge Metadata Endpoint
        Return information from the incoming request context
        Include at least colo and country
        Include at least 1 additional field such as asn, city, httpProtocol, or tlsVersion

    Verify Public Edge Execution
        Call your deployed Worker using the public URL
        Capture the JSON response from the metadata endpoint
        Show evidence that Cloudflare provides request metadata at the edge

    Explain Global Distribution
        Briefly explain how Workers distributes execution globally
        Compare this with manually choosing regions in VM or PaaS platforms
        Explain why there is no deploy to 3 regions step in Workers

    Document Routing Concepts
        Explain the difference between workers.dev, Routes, and Custom Domains
        Use workers.dev for the required deployment
        Custom domain setup is optional

💡 Hints

Task 4 — Configuration, Secrets & Persistence (3 pts)

Objective: Configure your Worker with variables, secrets, and persistent state.

Requirements:

    Add Environment Variables
        Define at least 1 plaintext variable in wrangler.jsonc
        Use it in your Worker response
        Explain why plaintext vars are not suitable for secrets

    Add Secrets
        Create at least 2 secrets with Wrangler
        Use the values through the env object
        Do not commit secret values to Git

    Add Persistence with Workers KV
        Create a KV namespace
        Bind it to your Worker
        Store and retrieve at least 1 value through your API

    Verify Persistence
        Confirm the stored value still exists after a redeploy
        Document what you stored and how you verified it

💡 Hints

Task 5 — Observability & Operations (3 pts)

Objective: Observe your Worker in production and manage deployments.

Requirements:

    Inspect Logs
        Add at least 1 console.log() statement
        View logs with npx wrangler tail or in the dashboard
        Capture an example log entry

    Inspect Metrics
        Open the Worker in the Cloudflare dashboard
        Review request counts, errors, or execution metrics
        Briefly explain what metric you looked at

    Manage Deployments
        Deploy at least 2 versions of your Worker
        View deployment history
        Perform or describe a rollback to a previous version

💡 Hints

Task 6 — Documentation & Comparison (3 pts)

Objective: Document your deployment and compare Workers with Kubernetes.

Create WORKERS.md with:

    Deployment Summary
        Worker URL
        Main routes
        Configuration used

    Evidence
        Screenshot of Cloudflare dashboard
        Example /edge JSON response
        Example log or metrics screenshot

    Kubernetes vs Cloudflare Workers Comparison

Aspect 	Kubernetes 	Cloudflare Workers
Setup complexity 		
Deployment speed 		
Global distribution 		
Cost (for small apps) 		
State/persistence model 		
Control/flexibility 		
Best use case 		

    When to Use Each
        Scenarios favoring Kubernetes
        Scenarios favoring Workers
        Your recommendation

    Reflection
        What felt easier than Kubernetes?
        What felt more constrained?
        What changed because Workers is not a Docker host?

Checklist

    Cloudflare account created
    Workers project initialized
    Wrangler authenticated
    Worker deployed to workers.dev
    /health endpoint working
    Edge metadata endpoint implemented
    At least 1 plaintext variable configured
    At least 2 secrets configured
    KV namespace created and bound
    Persistence verified after redeploy
    Logs or metrics reviewed
    Deployment history viewed
    WORKERS.md documentation complete
    Kubernetes comparison documented

Rubric
Criteria 	Points
Setup 	3 pts
Worker API 	4 pts
Edge Behavior 	4 pts
Configuration & Persistence 	3 pts
Operations 	3 pts
Documentation 	3 pts
Total 	20 pts

Grading:

    18-20: Excellent deployment, strong edge analysis, thorough comparison
    16-17: Working Worker, good documentation, minor gaps
    14-15: Basic deployment works, missing KV, observability, or analysis detail
    <14: Incomplete implementation

Resources
📚 Core Cloudflare Workers Docs

🌍 Edge Runtime & Routing

🔐 Config, Secrets & State

📊 Observability & Deployments

🐍 Optional Python Track

Good luck! 🌍

    Remember: Cloudflare Workers is excellent for globally distributed APIs and lightweight edge logic. Kubernetes gives you more control, broader runtime flexibility, and stronger patterns for long-running container workloads. Choose the right model for the workload.
