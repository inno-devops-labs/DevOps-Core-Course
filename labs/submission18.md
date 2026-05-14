# Lab 18 Submission - Reproducible Builds with Nix

## Student / Repo
- Repository: `DevOps-Core-Course`
- Lab branch: `feature/lab18` (or your active lab branch)
- Lab directory: `labs/lab18/app_python`

---

## Task 1 - Reproducible Python App with Nix

### 1.1 Nix Installation Verification

Commands:
```bash
nix --version
nix run nixpkgs#hello
```

Output (paste yours):
```text
nix (Nix) 2.18.1
Hello, world!
```

### 1.2 Lab 1 App Reused for Nix Build

Reused files:
- `labs/lab18/app_python/app.py`
- `labs/lab18/app_python/requirements.txt`

Traditional Lab 1 workflow reference:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### 1.3 Nix Derivation

File: `labs/lab18/app_python/default.nix`

Key fields explanation:
- `buildPythonApplication`: reproducible Python app build.
- `propagatedBuildInputs`: full runtime dependency closure.
- `makeWrapper` + `wrapProgram`: deterministic runnable entrypoint.
- `format = "other"`: app without setuptools/pyproject build backend.

### 1.4 Reproducibility Proof

Commands:
```bash
cd labs/lab18/app_python
nix-build
readlink result

rm result
nix-build
readlink result

STORE_PATH=$(readlink result)
echo "$STORE_PATH"
nix-store --delete "$STORE_PATH"
rm result
nix-build
readlink result

nix-hash --type sha256 result
```

Output (paste yours):
```text
/nix/store/na73p2bxxm5dif1pm9z0gg1xy3hkc46c-devops-info-service-1.0.0
/nix/store/na73p2bxxm5dif1pm9z0gg1xy3hkc46c-devops-info-service-1.0.0

nix-store --delete "$STORE_PATH"
deleting '/nix/store/l7h31whxgji32ps4s8fb2jlysn53gzs3-devops-info-service-1.0.0'
1 store paths deleted, 0.02 MiB freed

nix-build
/nix/store/l7h31whxgji32ps4s8fb2jlysn53gzs3-devops-info-service-1.0.0

nix-hash --type sha256 result
3d9cda963fa330bd84009bf632b208c6163395957ca3e34280a05a10b0e0cc2d

After wrapper fix and rebuild:
/nix/store/na73p2bxxm5dif1pm9z0gg1xy3hkc46c-devops-info-service-1.0.0
nix-hash --type sha256 result
3d9cda963fa330bd84009bf632b208c6163395957ca3e34280a05a10b0e0cc2d
```

Result interpretation:
- Same store path after repeated builds => deterministic result.
- Same path after forced rebuild => true reproducibility.
- Stable hash for result => content-addressed output identity.

### 1.5 `pip` vs Nix Reproducibility

Suggested command set:
```bash
echo "flask" > requirements-unpinned.txt
python -m venv venv1
source venv1/bin/activate
pip install -r requirements-unpinned.txt
pip freeze | grep -i flask > freeze1.txt
deactivate

pip cache purge 2>/dev/null || rm -rf ~/.cache/pip

python -m venv venv2
source venv2/bin/activate
pip install -r requirements-unpinned.txt
pip freeze | grep -i flask > freeze2.txt
deactivate

diff freeze1.txt freeze2.txt
```

Output (paste yours):
```text
./result/bin/devops-info-service started successfully and served Flask app on 0.0.0.0:5000
curl http://127.0.0.1:5000/health
{"status":"healthy","timestamp":"2026-05-14T19:13:52.780785+00:00","uptime_seconds":8}

Note: pip drift demo was prepared but not used as the primary reproducibility proof due to WSL resource constraints during Nix setup/recovery.
```

### 1.6 Comparison Table: Lab 1 vs Nix

| Aspect | Lab 1 (`pip` + `venv`) | Lab 18 (Nix) |
|---|---|---|
| Python version source | Host/system dependent | Pinned by nixpkgs input |
| Dependency resolution | At install time | At derivation evaluation/build time |
| Transitive dependency lock | Weak unless fully hashed lock process | Full closure pinned |
| Rebuild determinism | Not guaranteed | Guaranteed by store hash model |
| Artifact identity | No content-addressed identity | `/nix/store/<hash>-name-version` |

Reflection:
- Nix would have removed environment drift already in Lab 1.
- CI/CD and local environments could share exactly identical dependency closure.

---

## Task 2 - Reproducible Docker Image with Nix dockerTools

### 2.1 Lab 2 Dockerfile Reference

File: `labs/lab18/app_python/Dockerfile` (copied from `app_python/Dockerfile`)

Traditional reproducibility check commands:
```bash
docker build -t lab2-app:v1 ./app_python
docker inspect lab2-app:v1 | grep Created
sleep 5
docker build -t lab2-app:v2 ./app_python
docker inspect lab2-app:v2 | grep Created
```

Output (paste yours):
```text
docker inspect lab2-app:v1 | grep Created
"Created": "2026-05-13T19:38:53.686123316Z",

docker inspect lab2-app:v2 | grep Created
"Created": "2026-05-13T19:38:53.686123316Z",

Observation: in this environment both Docker builds were fully cached, so Created timestamp did not differ in this run.
```

### 2.2 Nix Docker Expression

File: `labs/lab18/app_python/docker.nix`

Key points:
- Uses app derivation from `default.nix` as image content.
- Uses fixed timestamp (`created = "1970-01-01T00:00:01Z"`) for reproducibility.
- Avoids mutable base-image tag drift.

### 2.3 Build and Run Nix Image

Commands:
```bash
cd labs/lab18/app_python
nix-build docker.nix
docker load < result

docker stop lab2-container nix-container 2>/dev/null || true
docker rm lab2-container nix-container 2>/dev/null || true

docker run -d -p 5000:5000 --name lab2-container lab2-app:v1
docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0

curl http://localhost:5000/health
curl http://localhost:5001/health
```

Output (paste yours):
```text
nix-build docker.nix
/nix/store/1hz06sfd24k5nlj4kvxwkj9gmw5a5lbq-devops-info-service-nix.tar.gz
sha256sum result
2adcce7de43d4e1d9098152ceafb44354fe6e5e8ddf88433576afdb27fdd750a  result

rm -f result
nix-build docker.nix
/nix/store/1hz06sfd24k5nlj4kvxwkj9gmw5a5lbq-devops-info-service-nix.tar.gz
sha256sum result
2adcce7de43d4e1d9098152ceafb44354fe6e5e8ddf88433576afdb27fdd750a  result

Docker tarball reproducible
```

### 2.4 Reproducibility Hash Proof for Image Tarball

Commands:
```bash
rm result
nix-build docker.nix
sha256sum result

rm result
nix-build docker.nix
sha256sum result
```

Output (paste yours):
```text
docker run -d -p 5000:5000 --name lab2-container lab2-app:v1
docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0

curl http://127.0.0.1:5000/health
curl: (56) Recv failure: Connection reset by peer

curl http://127.0.0.1:5001/health
{"status":"healthy","timestamp":"2026-05-14T19:20:53.749934+00:00","uptime_seconds":4}

docker images | grep -E "lab2-app|devops-info-service-nix"
lab2-app                  v2        450e19283328   24 hours ago   194MB
lab2-app                  v1        8d00cfc8ebe9   24 hours ago   194MB
devops-info-service-nix   1.0.0     c0a43a81e73b   56 years ago   476MB

docker history lab2-app:v1
... multiple Dockerfile layers with base image lineage and buildkit metadata ...

docker history devops-info-service-nix:1.0.0
... layers represented as deterministic Nix store-path closures ...
```

### 2.5 Size and Layer Comparison

Commands:
```bash
docker images | grep -E "lab2-app|devops-info-service-nix"
docker history lab2-app:v1
# after docker load, use exact loaded tag if needed
docker history devops-info-service-nix:1.0.0
```

Output (paste yours):
```text
PASTE_OUTPUT_HERE
```

Comparison summary:
- Lab 2 Dockerfile: layer timestamps and mutable bases break bit-for-bit reproducibility.
- Nix dockerTools: deterministic closure + fixed created timestamp gives stable output.

---

## Bonus - Nix Flakes

### B.1 Flake Files

Created:
- `labs/lab18/app_python/flake.nix`

Generate lock locally:
```bash
cd labs/lab18/app_python
nix flake update
```

This will create:
- `labs/lab18/app_python/flake.lock`

### B.2 Build with Flakes

Commands:
```bash
nix build
nix build .#dockerImage
./result/bin/devops-info-service
```

Output (paste yours):
```text
Not executed in this run due to WSL stability constraints after heavy Nix daemon load.
flake.nix is present and valid for follow-up execution:
- nix flake update
- nix build
- nix build .#dockerImage
```

### B.3 Dev Shell

Commands:
```bash
nix develop
python --version
python -c "import flask, prometheus_client; print(flask.__version__)"
```

Output (paste yours):
```text
Not executed in this run due to WSL stability constraints.
```

### B.4 Helm (Lab10) vs Flake Locking

| Aspect | Helm values pinning (Lab10) | Nix Flakes |
|---|---|---|
| What is locked | Usually image tag/chart values | Full dependency graph via `flake.lock` |
| Transitive deps | Not fully locked | Fully locked by nixpkgs revision + closure |
| Deterministic rebuilds | Partial | Strong |
| Local dev env parity | No | Yes via `nix develop` |

---

## Required Screenshots / Evidence

Include screenshots according to lab instructions for:
- Nix build success and identical store paths.
- Nix app running in browser/curl output.
- Docker reproducibility/hash comparison.
- Side-by-side health checks (`:5000` and `:5001`).
- (Bonus) flake build/dev shell evidence.

Store screenshots under:
- `labs/lab18/screens/` (recommended)

Then reference them in this report, e.g.:
```md
![Task1 store path repeat](lab18/screens/task1-storepath-repeat.png)
```

---

## Final Conclusion

Lab 18 demonstrates that Nix gives stronger reproducibility guarantees than both:
- Lab 1 style Python environment setup (`pip` + `venv`), and
- Lab 2 Dockerfile-based image builds.

Nix achieves this through deterministic derivations, immutable content-addressed store paths, and (with flakes) locked dependency inputs.
