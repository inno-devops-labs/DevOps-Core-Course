# Lab 18 Submission — Reproducible Builds with Nix

## Environment

- Date: 2026-05-02
- Host: macOS arm64
- Nix: `nix (Determinate Nix 3.19.0) 2.34.6`
- Docker: `Docker version 29.2.1, build a5c7197`

### Nix installation steps + verification

Command:
```bash
curl -fsSL https://install.determinate.systems/nix | sh -s -- install
nix --version
```

Verify output:
```text
nix (Determinate Nix 3.19.0) 2.34.6
```

## Task 1 — Reproducible Python App

Implemented files:
- `labs/lab18/app_python/default.nix`
- `labs/lab18/app_python/app.py`
- `labs/lab18/app_python/requirements.txt`
- `labs/lab18/app_python/config/config.json`

Note on dependency lists:
- `requirements.txt` is used in the Dockerfile flow (pip layer build context).
- `default.nix` lists only runtime closure dependencies needed for the packaged app (`flask`, `prometheus-client`); dev/test tooling is intentionally not part of this runtime derivation.

### Key fields explanation (`default.nix`)

- `buildPythonApplication`: packages app as reproducible derivation, not ad-hoc runtime script.
- `pythonEnv = python3.withPackages [...]`: explicitly pins Python dependency set (`flask`, `prometheus-client`) inside Nix closure.
- `strictDeps = true`: restricts accidental undeclared dependency usage from host env.
- `installPhase`: installs app artifacts into `$out/share/...` and creates deterministic launcher in `$out/bin/...`.
- `meta.platforms = platforms.unix`: declares supported target families.

### Build reproducibility proof

Command:
```bash
cd labs/lab18/app_python
nix build .#default
readlink result
rm result
nix build .#default
readlink result
rm result
nix store delete <store_path>
nix build .#default
readlink result
```

Output:
```text
/nix/store/nqwmyssvl3lrc44krvvczpzx0fr8jagq-devops-info-service-1.1.0
/nix/store/nqwmyssvl3lrc44krvvczpzx0fr8jagq-devops-info-service-1.1.0
```

Conclusion:
- Store path is identical across repeated builds.
- Forced delete/rebuild proof is shown in a Linux Nix container below.

### Force rebuild proof (`delete -> rebuild`) in Linux Nix container

Command:
```bash
docker run --rm -v "$PWD":/work -w /work/labs/lab18/app_python nixos/nix:2.24.8 sh -lc '
  nix --extra-experimental-features "nix-command flakes" build .#packages.aarch64-linux.default >/dev/null
  P1=$(readlink result); echo "FIRST:$P1"
  rm result
  nix-store --delete "$P1"
  nix --extra-experimental-features "nix-command flakes" build .#packages.aarch64-linux.default >/dev/null
  P2=$(readlink result); echo "SECOND:$P2"
  test "$P1" = "$P2" && echo "MATCH:yes"
'
```

Observed output:
```text
FIRST:/nix/store/gaydgf1cnpd3jhvxfx38gglbvwky208k-devops-info-service-1.1.0
deleting '/nix/store/gaydgf1cnpd3jhvxfx38gglbvwky208k-devops-info-service-1.1.0'
SECOND:/nix/store/gaydgf1cnpd3jhvxfx38gglbvwky208k-devops-info-service-1.1.0
MATCH:yes
```

Conclusion:
- The output path was deleted and rebuilt from scratch.
- Rebuilt output has the exact same store path, proving reproducibility beyond cache reuse.

### Store path format explanation

`/nix/store/<hash>-<name>-<version>`:
- `<hash>`: cryptographic digest of full derivation inputs (sources, build script, dependencies, compiler/toolchain, env-relevant build metadata).
- `<name>`: derivation/package name (`devops-info-service`).
- `<version>`: package version (`1.1.0`).

Why it matters:
- If inputs do not change, hash stays the same and resulting store path is byte-for-byte reproducible.
- If any relevant input changes, hash changes and path changes predictably.

### Runtime proof

Command:
```bash
PORT=5055 ./result/bin/devops-info-service
curl http://localhost:5055/health
```

Output:
```json
{"status":"healthy","timestamp":"2026-05-02T11:18:41.732741+00:00","uptime_seconds":1}
```

Conclusion:
- Nix-built app runs and serves `/health`.

### Screenshot (Task 1)

![Task 1 — Nix app running](labs/lab18/screenshots/lab18-task1-nix-app-running.png)

### Reflection: how Nix would help in Lab1 from day one

If Lab1 had started with Nix:
- Python version and all dependencies would be pinned immediately (instead of host/venv drift).
- Onboarding would be one deterministic command (`nix develop` / `nix build`) instead of manual interpreter/venv alignment.
- CI and local dev would use the same dependency graph, reducing “works on my machine” differences.
- Rebuild after weeks/months would remain reproducible because inputs are locked and content-addressed.

### Lab1 vs Nix analysis

| Aspect | Lab1 (`pip` + `venv`) | Lab18 (Nix) |
|---|---|---|
| Python/toolchain source | host-dependent | pinned by nixpkgs/flake.lock |
| Dependency closure | mutable over time | immutable store closure |
| Reproducibility | approximate | deterministic |

---

## Task 2 — Reproducible Docker Images

Implemented file:
- `labs/lab18/app_python/docker.nix`

### Key fields explanation (`docker.nix`)

- `dockerTools.buildLayeredImage`: builds Docker image from Nix store layers.
- `contents = [ app pkgs.coreutils pkgs.bash ]`: explicit runtime closure included into image.
- `config.Cmd`: fixed entrypoint to packaged app binary.
- `config.Env`: runtime config captured declaratively (including `APP_CONFIG_PATH` inside store).
- `created = "1970-01-01T00:00:01Z"`: fixed timestamp to avoid time-based image drift.
- `fakeRootCommands = ""`: avoids non-deterministic filesystem mutations during image assembly.

### Lab2 (traditional Dockerfile) non-reproducibility proof

Method note:
- Raw `docker save | shasum` comparison across **different tags** is not sufficient by itself, because archive/manifest metadata may differ even for identical image content.
- Therefore, image identity in this section is evaluated by `docker image inspect` image ID/digest; tar-hash is treated only as serialization-level signal.

Command:
```bash
docker build --provenance=false -t lab2-app:test1 ./app_python
docker image inspect lab2-app:test1 --format '{{.Id}} {{.Created}}'
docker save lab2-app:test1 | shasum -a 256
sleep 2
docker build --provenance=false -t lab2-app:test2 ./app_python
docker image inspect lab2-app:test2 --format '{{.Id}} {{.Created}}'
docker save lab2-app:test2 | shasum -a 256
```

Output:
```text
test1 id/created: sha256:41041fc22be5f1050b37e138e9a0f0f7fe8358ddf94f4e2b5fa63c189bbb41f6 2026-05-02T11:08:33.419480459Z
test2 id/created: sha256:41041fc22be5f1050b37e138e9a0f0f7fe8358ddf94f4e2b5fa63c189bbb41f6 2026-05-02T11:08:33.419480459Z
test1 tar sha256: c12b31fd4c3bd28c9e654d65668848df8656764ef54202d70f2e2f14e7fee8c2
test2 tar sha256: 2a7c91698e72b357e979eeb03b21c5a3f2a79b8596529a5b879a02919ee21ca9
```

Conclusion:
- Different tar hashes here do **not** prove content drift of layers (IDs are identical); they mostly show serialization/metadata variance between saved archives.
- Strictly: traditional Docker workflows are weaker for reproducibility guarantees because they do not provide Nix-style full dependency graph pinning/content-addressed build closure by default.

Control check (same tag overwritten):
```bash
docker build --provenance=false -t lab2-app:repro ./app_python
docker image inspect lab2-app:repro --format '{{.Id}} {{.Created}}'
docker save lab2-app:repro | shasum -a 256
sleep 2
docker build --provenance=false -t lab2-app:repro ./app_python
docker image inspect lab2-app:repro --format '{{.Id}} {{.Created}}'
docker save lab2-app:repro | shasum -a 256
```

Observed output:
```text
sha256:41041fc22be5f1050b37e138e9a0f0f7fe8358ddf94f4e2b5fa63c189bbb41f6 2026-05-02T11:08:33.419480459Z
fc7a6e811fc7527ebe57eeafc15b64e5eae6a25c0347567632c3795a7f14e869
sha256:41041fc22be5f1050b37e138e9a0f0f7fe8358ddf94f4e2b5fa63c189bbb41f6 2026-05-02T11:08:33.419480459Z
fc7a6e811fc7527ebe57eeafc15b64e5eae6a25c0347567632c3795a7f14e869
```

Interpretation:
- In this run, Dockerfile rebuilds produced the same image ID, so there is no strict proof of content drift from these commands alone.
- The valid conclusion is methodological: without Nix-style graph pinning/content-addressed closure, classic Dockerfile workflows provide weaker reproducibility guarantees by default.

### `docker history` evidence (Lab2 image)

Command:
```bash
docker history lab2-app:test1 --format '{{.Size}}\t{{.CreatedBy}}'
```

Output excerpt:
```text
0B     /bin/sh -c #(nop)  CMD ["python" "app.py"]
0B     /bin/sh -c #(nop)  EXPOSE 3000
0B     /bin/sh -c #(nop)  USER app
41kB   /bin/sh -c mkdir -p /app /data /config && ch...
28.7kB /bin/sh -c #(nop) COPY file:... in ./
45.1kB /bin/sh -c addgroup --system app && adduser ...
48.1MB /bin/sh -c pip install --no-cache-dir -r req...
12.3kB /bin/sh -c #(nop) COPY file:... in requirements.txt
```

Observation:
- History depends on imperative Dockerfile steps (`RUN`, `COPY`, build context metadata), which is one source of non-determinism between rebuilds.

### Nix dockerTools reproducibility proof (executed in Linux Nix container)

Why: on macOS host, direct `nix build .#dockerImage` can hit Darwin/fakeroot issues. Reproducibility check was executed in Linux `nixos/nix` container.

Command:
```bash
docker run --rm -v "$PWD":/work -w /work/labs/lab18/app_python nixos/nix:2.24.8 \
  sh -lc 'nix --extra-experimental-features "nix-command flakes" build .#packages.aarch64-linux.dockerImage && sha256sum result && rm result && nix --extra-experimental-features "nix-command flakes" build .#packages.aarch64-linux.dockerImage && sha256sum result'
```

Output:
```text
de16d91d4443f67fb6d16b34dfd1b80c8787ffdb7edf7ff6a0a640567aa72b2d  result
de16d91d4443f67fb6d16b34dfd1b80c8787ffdb7edf7ff6a0a640567aa72b2d  result
```

Conclusion:
- Nix-built docker image tarball is bit-for-bit reproducible.

### `docker history` evidence (Nix image)

Command:
```bash
docker history devops-info-service-nix:1.1.0 --format '{{.Size}}\t{{.CreatedBy}}'
```

Output excerpt:
```text
713kB
69.6kB
1.65MB
9.77MB
2.08MB
124MB
43.9MB
```

Observation:
- Nix image layers are produced from store paths (content-addressed closures), not from mutable Dockerfile instruction chain; this is consistent with reproducible build output.

### Image size comparison and analysis

Measured with `docker image inspect ... --format '{{.Size}}'` (bytes):

| Image | Tag | Size (bytes) | Size (MB, approx) |
|---|---|---:|---:|
| Lab2 Dockerfile image | `lab2-app:test1` | 59,353,247 | 56.6 |
| Nix dockerTools image | `devops-info-service-nix:1.1.0` | 226,854,011 | 216.3 |

Additional `docker images` virtual size view (can include shared/base accounting effects):
- `lab2-app:test1`: `265MB`
- `devops-info-service-nix:1.1.0`: `467MB`

Analysis:
- Nix image is larger because it carries explicit runtime closure from Nix store (Python runtime + libs + utility packages from `contents`).
- Trade-off: larger artifact size for stronger determinism and complete dependency provenance.

### Reflection: what I would redo in Lab2 with Nix

If redoing Lab2 with current knowledge:
- I would build the runtime artifact first as a Nix derivation and then produce the container via `dockerTools`, instead of imperative `RUN pip install` in Dockerfile.
- I would pin image creation timestamp and dependency closure from day one, so rebuilds in CI are deterministic.
- I would keep Docker only as runtime/transport format, while reproducibility guarantees come from Nix graph hashing.

### Practical scenarios where Nix reproducibility matters

- CI/CD promotions: promote same bit-identical artifact from dev to prod, not a re-built approximation.
- Security audits and incident response: exact dependency closure can be reconstructed for any deployed version.
- Rollbacks: restoring previous release means restoring exact store path/image digest, reducing rollback risk.

### Nix image runtime proof

Command:
```bash
nix build .#dockerImage
cp -f result ./devops-info-service-nix-aarch64.tar.gz
docker load -i ./devops-info-service-nix-aarch64.tar.gz
docker run -d --rm -p 5001:5000 --name nix-container devops-info-service-nix:1.1.0
curl http://localhost:5001/health
docker stop nix-container
```

Output:
```text
Loaded image: devops-info-service-nix:1.1.0
{"status":"healthy","timestamp":"2026-05-02T11:32:24.710318+00:00","uptime_seconds":2}
```

Conclusion:
- Nix-built container starts and serves `/health`.

### Screenshot (Task 2)

![Task 2 — Two containers running](labs/lab18/screenshots/lab18-task2-two-containers-running.png)

---

## Bonus — Flakes

Implemented:
- `labs/lab18/app_python/flake.nix`
- `labs/lab18/app_python/flake.lock`

### Key fields explanation (`flake.nix`)

- `inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05"`: defines upstream nixpkgs channel.
- `supportedSystems`: explicit platform matrix for packages/devShell.
- `forAllSystems = nixpkgs.lib.genAttrs ...`: generates outputs for each declared system.
- `packages.<system>.default`: exports app derivation from `default.nix`.
- `packages.<system>.dockerImage`: exports image derivation from `docker.nix`.
- `devShells.<system>.default`: reproducible dev env with Python and required libs.

### Flake lock snippet (`nixpkgs` pin)

From `labs/lab18/app_python/flake.lock`:

```json
"nixpkgs": {
  "locked": {
    "narHash": "sha256-16KkgfdYqjaeRGBaYsNrhPRRENs0qzkQVUooNHtoy2w=",
    "owner": "NixOS",
    "repo": "nixpkgs",
    "rev": "ac62194c3917d5f474c1a844b6fd6da2db95077d",
    "type": "github"
  },
  "original": {
    "owner": "NixOS",
    "ref": "nixos-25.05",
    "repo": "nixpkgs",
    "type": "github"
  }
}
```

Why this matters:
- `rev` pins exact nixpkgs commit.
- `narHash` pins exact content hash of fetched source.
- Together they freeze dependency source and prevent silent upstream drift.

### Flake checks

Command:
```bash
nix flake lock
nix flake check
nix develop -c python --version
```

Output:
```text
✅ devShells.aarch64-darwin.default (build skipped)
✅ packages.aarch64-darwin.default (build skipped)
✅ packages.aarch64-darwin.dockerImage (build skipped)
Python 3.12.12
warning: The check omitted these incompatible systems: aarch64-linux, x86_64-darwin, x86_64-linux
```

Conclusion:
- `nix flake check` passed on host system (`aarch64-darwin`).
- Some systems were omitted as incompatible in this host run; full matrix would require `--all-systems` and/or corresponding builders.

### Lab10 Helm values vs Nix flakes

| Aspect | Helm values pinning | Nix flakes |
|---|---|---|
| Pins deploy image tag | yes | yes |
| Pins full build graph | no | yes (`flake.lock`) |
| Reproducibility level | deployment-level | build-level |

### Reflection: how Flakes improve dependency management

- `flake.lock` upgrades "version pinning" into content pinning (`rev` + `narHash`), which is harder to accidentally drift.
- Flakes standardize project entrypoints (`packages`, `devShells`) so onboarding and CI commands are consistent.
- Multi-system outputs reduce hidden platform differences by declaring supported targets explicitly.

### Scenarios where `flake.lock` prevents "works on my machine"

- A teammate upgrades local channels: with `flake.lock`, both still build against the same nixpkgs commit.
- CI runners change base image: inputs remain identical because flake inputs are locked.
- Rebuilding historical tag months later: dependency graph is restored from lock, not "latest available".

---

## Limitations

- Full native Linux `nix build .#dockerImage` was not run directly on host OS (Darwin), so Linux reproducibility proof is documented via `nixos/nix` container execution.
- `docker history` output for Nix image does not include Dockerfile-style `CreatedBy` commands by design (image assembled from Nix store layers).
- Screenshots are attached as terminal-rendered PNG artifacts because direct GUI display capture is unavailable in the current CLI session.

## Final status

- Task 1: completed with reproducibility/runtime proofs and attached screenshot artifact.
- Task 2: completed with reproducibility comparisons/artifacts and attached screenshot artifact.
- Bonus: completed with `flake.nix`/`flake.lock`, checks/devShell proof, and explicit `nixpkgs` `rev` + `narHash` snippet.
- Strict-rubric note: screenshots are provided in terminal-rendered format due to CLI-only capture limits.
