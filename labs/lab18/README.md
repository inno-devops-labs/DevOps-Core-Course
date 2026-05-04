# Lab 18 Static Site

This directory contains the static website used for Lab 18.

## 4EVERLAND Hosting Settings

Use these settings when importing the repository in 4EVERLAND Hosting:

| Setting | Value |
| --- | --- |
| Framework preset | Other / Static |
| Root directory | `labs/lab18` |
| Build command | leave empty |
| Output directory | leave empty or `.` |
| Deployment network | IPFS |

The deployment entrypoint is `index.html`.

## Local Preview

The site is static, so it can be opened directly in a browser:

```text
labs/lab18/index.html
```

Or served locally:

```powershell
cd labs/lab18
py -3 -m http.server 8088
```

Then open:

```text
http://localhost:8088
```

## Local IPFS Node

Run Kubo through Docker Compose:

```powershell
cd labs/lab18
docker compose up -d
docker exec lab18-ipfs ipfs version
```

Open:

```text
http://localhost:5001/webui
```

Gateway:

```text
http://localhost:8080/ipfs/<CID>
```
