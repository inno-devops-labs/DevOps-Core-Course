# Lab 18 - Reproducible Builds with Nix

This module contains the Lab 18 reproducible-build work. The implementation keeps the repository DRY: the flake in `nix/` packages the real `app_python/` source instead of copying it into a lab folder.

## Summary

- Python packaging moved from Poetry to uv while keeping Python 3.14.
- Nix uses stable `nixos-25.11`, pinned in `nix/flake.lock`.
- The Nix implementation lives entirely in `nix/`:
  - `flake.nix` wires the package, Docker image, app, checks, formatter, and dev shell.
  - `package.nix` builds the Flask app with `python314`.
  - `docker.nix` builds a reproducible image with `dockerTools`.
  - `devshell.nix` provides Python 3.14, uv, Docker, curl, and jq.

The active app keeps its Python dependency graph in `app_python/uv.lock`. `app_python/requirements.txt` is generated from that lock file only for Snyk's pip-compatible scanner path; `uv.lock` remains the source of truth. The Nix runtime closure intentionally includes the packages imported by the Flask service: `flask`, `gunicorn`, and `prometheus-client`.

## Why Nix

uv is a much better Python workflow than Poetry here: it is fast, simple, and not tied to Poetry's project model. It still resolves from Python package indexes and produces an application-level lock file.

Nix locks the system-level build closure: Python itself, build hooks, runtime libraries, and the Docker image construction tools. That is the main reproducibility difference. The uv Docker image is convenient, but its `python:3.14-alpine` base tag can move. The Nix image records the full nixpkgs revision and uses deterministic image metadata.

## Commands

```bash
cd nix
nix develop
cd ../app_python
uv sync --locked
uv export --locked --no-dev --no-annotate --no-header --no-hashes --format requirements.txt --output-file /tmp/lab18-requirements.txt >/dev/null
diff -u requirements.txt /tmp/lab18-requirements.txt
uv run flake8 src tests
uv run pytest --cov=src --cov-report=term-missing
```

```bash
cd nix
nix flake check
nix build .#default
nix run .#default
nix build .#dockerImage
docker load < result
```

## Evidence

<details>
<summary>uv local workflow</summary>

```text
$ cd nix

$ nix develop -c bash <<'BASH'
cd ../app_python
uv --version
uv run python --version
uv lock --check
uv export --locked --no-dev --no-annotate --no-header --no-hashes --format requirements.txt --output-file /tmp/lab18-requirements.txt >/dev/null
diff -u requirements.txt /tmp/lab18-requirements.txt
uv sync --locked
uv run flake8 src tests
uv run pytest --cov=src --cov-report=term-missing
BASH

uv 0.9.30
Python 3.14.3
Resolved 23 packages in 0.54ms
Resolved 23 packages in 0.50ms
Resolved 23 packages in 0.52ms
Audited 21 packages in 0.13ms
============================= test session starts ==============================
platform linux -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/t0ast/Repos/DevOps-Core-S26/app_python
configfile: pyproject.toml
plugins: cov-7.1.0
collected 19 items

tests/test_endpoints.py ...........                                      [ 57%]
tests/test_logging_utils.py .                                            [ 63%]
tests/test_metrics.py ..                                                 [ 73%]
tests/test_unit_helpers.py .....                                         [100%]

================================ tests coverage ================================
_______________ coverage: platform linux, python 3.14.3-final-0 ________________

Name                    Stmts   Miss  Cover   Missing
-----------------------------------------------------
src/flask_instance.py      12      0   100%
src/logging_utils.py       42      8    81%   21-27, 51
src/main.py                10      0   100%
src/metrics.py             45      1    98%   95
src/router.py             118      7    94%   141-146, 149-153, 165-169
-----------------------------------------------------
TOTAL                     227     16    93%
============================== 19 passed in 0.11s ==============================
```

</details>

<details>
<summary>Nix package and runtime</summary>

```text
$ cd nix

$ nix flake metadata --json | jq '{description, resolved: .locks.nodes.nixpkgs.locked}'
{
  "description": "DevOps Core reproducible builds",
  "resolved": {
    "lastModified": 1778430510,
    "narHash": "sha256-Ti+ZBvW6yrWWAg2szExVTwCd4qOJ3KlVr1tFHfyfi8Q=",
    "owner": "NixOS",
    "repo": "nixpkgs",
    "rev": "8fd9daa3db09ced9700431c5b7ad0e8ba199b575",
    "type": "github"
  }
}

$ nix flake check
evaluating flake...
checking flake output 'packages'...
checking derivation packages.x86_64-linux.default...
derivation evaluated to /nix/store/l19j81jw8kywfwiv1nbcppzw6z492lp0-devops-info-service-1.12.0.drv
checking derivation packages.x86_64-linux.devops-info-service...
derivation evaluated to /nix/store/l19j81jw8kywfwiv1nbcppzw6z492lp0-devops-info-service-1.12.0.drv
checking derivation packages.x86_64-linux.dockerImage...
derivation evaluated to /nix/store/dfh47gscdprzlalzfpngjggmlqr0c2x3-devops-info-service-nix.tar.gz.drv
checking flake output 'apps'...
checking app 'apps.x86_64-linux.default'...
warning: app 'apps.x86_64-linux.default' lacks attribute 'meta'
checking flake output 'checks'...
checking derivation checks.x86_64-linux.default...
derivation evaluated to /nix/store/l19j81jw8kywfwiv1nbcppzw6z492lp0-devops-info-service-1.12.0.drv
checking flake output 'devShells'...
checking derivation devShells.x86_64-linux.default...
derivation evaluated to /nix/store/qmsav41in4f6c269s4yaimqc3m0ag1ba-nix-shell.drv
checking flake output 'formatter'...
checking derivation formatter.x86_64-linux...
derivation evaluated to /nix/store/ds5xf6q419g1wq2kz63g3j020jd50j2y-format-nix.drv
running 1 flake checks...

$ bash <<'BASH'
first=$(nix build .#default --no-link --print-out-paths)
second=$(nix build .#default --no-link --print-out-paths)
printf 'first=%s\nsecond=%s\n' "$first" "$second"
test "$first" = "$second"
BASH
first=/nix/store/x0manjqw974f50rw4z6mg0szvlda5s2p-devops-info-service-1.12.0
second=/nix/store/x0manjqw974f50rw4z6mg0szvlda5s2p-devops-info-service-1.12.0

$ nix path-info -Sh .#default
/nix/store/x0manjqw974f50rw4z6mg0szvlda5s2p-devops-info-service-1.12.0	 191.4 MiB

$ nix path-info -rSh .#default | tail -n 5
/nix/store/x9ydb0ljg6ahf8vzpyigzpy65w1ixpz0-python3.14-prometheus-client-0.22.1	 181.6 MiB
/nix/store/z5sbbpr4izvdkck38bkr50k9h1k0p7hc-python3.14-click-8.2.1             	 182.3 MiB
/nix/store/xn69ihhpqffawlricm0vk3i7b370hhpn-python3.14-flask-3.1.2             	 188.6 MiB
/nix/store/93a9sdlhq8az8mwavchm7ibmp2r584jb-python3-3.14.3-env                 	 191.3 MiB
/nix/store/x0manjqw974f50rw4z6mg0szvlda5s2p-devops-info-service-1.12.0         	 191.4 MiB

$ bash <<'BASH'
app=$(nix build .#default --no-link --print-out-paths)
HOST=127.0.0.1 PORT=5018 "$app/bin/devops-info-service" > /tmp/lab18/nix-app.log 2>&1 &
app_pid=$!
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  response=$(curl -fsS 127.0.0.1:5018/health) && {
    printf '%s\n' "$response" | jq .
    break
  }
  sleep 1
done
kill "$app_pid"
wait "$app_pid" || true
sed -n '1,12p' /tmp/lab18/nix-app.log
BASH
curl: (7) Failed to connect to 127.0.0.1 port 5018 after 13 ms: Could not connect to server
{
  "status": "healthy",
  "timestamp": "2026-05-15T01:45:39.019501+00:00",
  "uptime_seconds": 0
}
[2026-05-15 04:45:38 +0300] [450876] [INFO] Starting gunicorn 23.0.0
[2026-05-15 04:45:38 +0300] [450876] [INFO] Using worker: sync
[2026-05-15 04:45:38 +0300] [450881] [INFO] Booting worker with pid: 450881
{"timestamp":"2026-05-15T01:45:38.124618Z","level":"INFO","logger":"devops_info_service","message":"application initialized","event":"startup","host":"127.0.0.1","port":5018,"debug":false}
{"timestamp":"[15/May/2026:04:45:39 +0300]","level":"INFO","logger":"gunicorn.access","client_ip":"127.0.0.1","method":"GET","path":"/health","query":"","status_code":200,"response_bytes":"87","request_time_us":1887,"user_agent":"curl/8.20.0"}
[2026-05-15 04:45:39 +0300] [450876] [INFO] Handling signal: term
[2026-05-15 04:45:39 +0300] [450881] [INFO] Worker exiting (pid: 450881)
[2026-05-15 04:45:39 +0300] [450876] [INFO] Shutting down: Master
```

</details>

<details>
<summary>Docker comparison</summary>

```text
$ docker version --format '{{.Server.Version}}'
29.4.3

$ DOCKER_BUILDKIT=1 docker build -t devops-app-py:uv-lab18 app_python

$ bash <<'BASH'
docker run --rm -d --name lab18-uv-app -p 5019:5000 devops-app-py:uv-lab18
docker exec lab18-uv-app sh -c 'printf "HOME=%s\n" "$HOME" && id && test -w /home/appuser && test -w /data'
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  response=$(curl -fsS 127.0.0.1:5019/health) && {
    printf '%s\n' "$response" | jq .
    break
  }
  sleep 1
done
docker logs lab18-uv-app | sed -n '1,8p'
docker stop lab18-uv-app
BASH
ae0f7839d5c1350ec44e5fbc77404de8609958abb03832dbf9be28fe23533466
HOME=/home/appuser
uid=100(appuser) gid=101(appgroup) groups=101(appgroup),101(appgroup)
{
  "status": "healthy",
  "timestamp": "2026-05-15T01:46:04.435915+00:00",
  "uptime_seconds": 0
}
[2026-05-15 01:46:03 +0000] [1] [INFO] Starting gunicorn 25.3.0
[2026-05-15 01:46:03 +0000] [1] [INFO] Listening at: http://0.0.0.0:5000 (1)
[2026-05-15 01:46:03 +0000] [1] [INFO] Using worker: sync
[2026-05-15 01:46:03 +0000] [14] [INFO] Booting worker with pid: 14
[2026-05-15 01:46:04 +0000] [1] [INFO] Control socket listening at /home/appuser/.gunicorn/gunicorn.ctl
{"timestamp":"2026-05-15T01:46:04.082192Z","level":"INFO","logger":"devops_info_service","message":"application initialized","event":"startup","host":"0.0.0.0","port":5000,"debug":false}
{"timestamp":"[15/May/2026:01:46:04 +0000]","level":"INFO","logger":"gunicorn.access","client_ip":"172.17.0.1","method":"GET","path":"/health","query":"","status_code":200,"response_bytes":"87","request_time_us":9213,"user_agent":"curl/8.20.0"}
lab18-uv-app

$ nix build .#dockerImage

$ docker load < result
Loaded image: devops-info-service-nix:lab18

$ bash <<'BASH'
docker run --rm -d --name lab18-nix-app -p 5020:5000 devops-info-service-nix:lab18
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  response=$(curl -fsS 127.0.0.1:5020/health) && {
    printf '%s\n' "$response" | jq .
    break
  }
  sleep 1
done
docker logs lab18-nix-app | sed -n '1,8p'
docker stop lab18-nix-app
BASH
8faa6ce8669dd235be4e882523567d8b51830f4f32c6a295b0edadee35c27809
{
  "status": "healthy",
  "timestamp": "2026-05-15T01:46:17.547776+00:00",
  "uptime_seconds": 0
}
[2026-05-15 01:46:16 +0000] [1] [INFO] Starting gunicorn 23.0.0
[2026-05-15 01:46:16 +0000] [1] [INFO] Listening at: http://0.0.0.0:5000 (1)
[2026-05-15 01:46:16 +0000] [1] [INFO] Using worker: sync
[2026-05-15 01:46:16 +0000] [7] [INFO] Booting worker with pid: 7
{"timestamp":"2026-05-15T01:46:16.649812Z","level":"INFO","logger":"devops_info_service","message":"application initialized","event":"startup","host":"0.0.0.0","port":5000,"debug":false}
{"timestamp":"[15/May/2026:01:46:17 +0000]","level":"INFO","logger":"gunicorn.access","client_ip":"172.17.0.1","method":"GET","path":"/health","query":"","status_code":200,"response_bytes":"87","request_time_us":1815,"user_agent":"curl/8.20.0"}
lab18-nix-app

$ docker image inspect devops-app-py:uv-lab18 devops-info-service-nix:lab18 | jq '.[] | {repoTags: .RepoTags, id: .Id, created: .Created, size: .Size}'
{
  "repoTags": [
    "devops-app-py:uv-lab18",
    "devops-info-service:uv-fixed"
  ],
  "id": "sha256:6559ec88f61e401b41cd8123f19da3fb84d90a124f0de705d115a7f1f30905cd",
  "created": "2026-05-15T04:43:29.572991821+03:00",
  "size": 120461874
}
{
  "repoTags": [
    "devops-info-service-nix:lab18"
  ],
  "id": "sha256:5a01bf71a8a11af7336d34f9e9e4148ea266900345b8259d6f1a78ad5bc49462",
  "created": "1970-01-01T00:00:01Z",
  "size": 198565103
}
```

</details>

## Comparison

| Area                | uv / Docker                              | Nix / dockerTools                                       |
| ------------------- | ---------------------------------------- | ------------------------------------------------------- |
| Python dependencies | `uv.lock` pins Python packages from PyPI | nixpkgs pin locks Python packages and build tools       |
| Python runtime      | `python:3.14-alpine` image tag           | `python314` from pinned `nixos-25.11`                   |
| Image timestamp     | Build-time timestamp                     | Fixed `1970-01-01T00:00:01Z`                            |
| Rebuild identity    | Can change when base image tag changes   | Same flake input and source produce the same store path |
| Workflow            | Better for day-to-day Python development | Better for full closure reproducibility                 |

## Helm Pinning Comparison

Lab 10 Helm values pin the application image tag, for example `image.tag: "1.12"`. That is useful deployment intent, but it does not prove what Python interpreter, package resolver, base image, or build tools produced the image. A mutable registry tag can also be pushed again.

The Lab 18 flake pins nixpkgs by Git revision and NAR hash. That locks Python 3.14, package definitions, build hooks, and `dockerTools`. Helm still remains useful after the image exists, but the flake is the stronger build provenance layer.

## Final State

- `uv sync`, `flake8`, and `pytest` pass on Python 3.14.
- `nix flake check` passes from `nix/`.
- Repeated `nix build .#default` from `nix/` returns the same store path.
- The Nix-built app responds healthy on `127.0.0.1:5018`.
- Both the uv Docker image and the Nix Docker image respond healthy.
- The Nix image uses deterministic image metadata; the traditional Docker image records the build time.
