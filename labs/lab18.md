# Lab 18 — Reproducible Builds with Nix

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Nix%20%26%20Reproducibility-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![type](https://img.shields.io/badge/type-Exam%20Alternative-purple)

> Use Nix to turn your Lab 1 Python app and your Lab 2 Docker image into **bit-for-bit reproducible** builds — the same hash on any machine, today and in ten years.

## Overview

A `Dockerfile` and a `requirements.txt` *look* reproducible, but they drift:
- `FROM python:3.13-slim` points to different content over time
- `pip install -r requirements.txt` lets transitive deps move even with `==` pins
- Docker layers embed build timestamps, so the same `Dockerfile` produces a different image SHA on every build

Nix fixes this by treating the build as a **pure function of its inputs**: it hashes every input — sources, dependencies, compiler, flags — into the output path `/nix/store/<sha256>-<name>-<version>`. Same inputs → same hash → identical output, on any machine, today and in 2036. The same hash also means a cache hit on `cache.nixos.org` skips the rebuild entirely.

**This is an Exam Alternative Lab** — complete both Lab 17 (Cloudflare Workers, 20 pts) and Lab 18 (Nix, 12 pts) to replace the final exam. See Lab 17 for the exam-alternative deadline and minimum-score rules.

**What You'll Learn:**
- The Nix philosophy: pure, sandboxed, content-addressed builds
- Writing a Nix derivation to build a Python app (revisiting Lab 1)
- Building a reproducible container image with `dockerTools` (revisiting Lab 2)
- Flakes + `flake.lock` for locking the full dependency closure
- Proving reproducibility with `nix-hash` / `sha256sum`

**Building on your work:** You will rebuild the **DevOps Info Service from Lab 1** and re-containerize the image from **Lab 2**, then compare reproducibility guarantees side by side.

**Tech Stack:** Nix **2.25+** (classic CLI + flakes) | nixpkgs (pinned) | `dockerTools` | Docker (to load the resulting image)

> **Note on outputs:** Every command output and hash shown in this lab is **illustrative** — your real store paths, image sizes, and hashes will differ. What must be *reproducible* is that **your own** repeated builds produce identical hashes.

---

## Prerequisites

- Completed **Lab 1** (Python DevOps Info Service) and **Lab 2** (Docker) — you reuse their artifacts
- Linux, macOS, or WSL2 with `sudo`/admin access (Nix installs to `/nix` at the system root)
- Docker installed and running (for Task 2)
- Your `app_python/` directory (`app.py` + `requirements.txt`) available

> If you no longer have your Lab 1/2 files, a minimal Flask `app.py` (one `/health` route) plus a one-line `requirements.txt` (`flask`) is enough to complete every task.

---

## Tasks

### Task 1 — Reproducible Python Build (revisiting Lab 1) (6 pts)

**Objective:** Install Nix, write a derivation that builds your Lab 1 Python app, and prove the build is reproducible — something `pip install -r requirements.txt` cannot guarantee.

#### 1.1 Install Nix (2.25+)

Use the **Determinate Systems installer** (recommended — enables flakes by default, clean uninstall):

```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

<details>
<summary>🐧 Alternative: official Nix installer</summary>

```bash
sh <(curl -L https://nixos.org/nix/install) --daemon
```

Then enable flakes (needed for Task with bonus) in `~/.config/nix/nix.conf`:
```
experimental-features = nix-command flakes
```
</details>

Restart your terminal, then verify you have **Nix 2.25 or newer** and run a package without installing it:

```bash
nix --version          # expect 2.25.x or newer (illustrative)
nix run nixpkgs#hello   # downloads + runs `hello`, installs nothing permanent
```

> **Lix:** A community fork of Nix (forked March 2024) is a drop-in `nix` replacement with faster evaluation. Either Nix 2.25+ or current Lix works for this lab.

#### 1.2 Prepare your app

```bash
mkdir -p labs/lab18/app_python
cp -r app_python/* labs/lab18/app_python/
cd labs/lab18/app_python
```

You should have at least `app.py` and `requirements.txt`. Recall the Lab 1 workflow (`venv` + `pip install -r requirements.txt`): it pins *what you install*, not what Flask installs — transitive deps still drift across machines and time.

#### 1.3 Write a derivation

Create `default.nix`. A skeleton is below — **you** fill in the `YOUR-TASK` markers.

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname   = "devops-info-service";
  version = "1.0.0";
  src     = ./.;
  format  = "other";              # app without setup.py / pyproject.toml

  # YOUR-TASK: list the Python deps your app imports (from nixpkgs, not PyPI)
  # e.g. flask, or [ fastapi uvicorn ] for the FastAPI variant
  propagatedBuildInputs = with pkgs.python3Packages; [ /* YOUR-TASK */ ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service
    # YOUR-TASK: wrap the script so it runs with the right interpreter + PYTHONPATH
    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$PYTHONPATH"
  '';
}
```

> **Why nixpkgs versions, not PyPI?** Nix pulls packages from a pinned nixpkgs revision (`Flask==3.1.0` → `pkgs.python3Packages.flask`). That pin is what makes the closure reproducible.

<details>
<summary>📚 Where to learn the derivation syntax</summary>

- [nix.dev — Building and running Python apps](https://nix.dev/tutorials/nixos/building-and-running-python-apps)
- [nixpkgs Python manual](https://nixos.org/manual/nixpkgs/stable/#python)
- [Nix Pills — Our first derivation](https://nixos.org/guides/nix-pills/our-first-derivation.html)

Key fields: `buildPythonApplication`, `propagatedBuildInputs` (runtime deps), `makeWrapper` (wraps the script), `format = "other"`, `src = ./.`.
</details>

Build and run it:

```bash
nix-build                          # → ./result symlink into /nix/store/<hash>-...
./result/bin/devops-info-service   # behaves exactly like your Lab 1 app
```

#### 1.4 Prove reproducibility

```bash
STORE_PATH=$(readlink result)
echo "$STORE_PATH"                 # /nix/store/<hash>-devops-info-service-1.0.0 (illustrative)

nix-store --delete "$STORE_PATH"   # force a real rebuild, not a cache hit
rm result && nix-build
readlink result                    # same store path returns → same hash → bit-for-bit identical

nix-hash --type sha256 result      # this hash is the same on any machine, forever
```

Contrast with `pip`. An unpinned (or even pinned-but-only-direct) `requirements.txt` can resolve different transitive versions over time, so two `pip install` runs can yield different environments. Demonstrate the drift:

```bash
echo flask > requirements-unpinned.txt          # no version → "whatever is latest"

python -m venv venv1 && source venv1/bin/activate
pip install -r requirements-unpinned.txt && pip freeze | grep -i flask > freeze1.txt
deactivate

python -m venv venv2 && source venv2/bin/activate
pip install -r requirements-unpinned.txt && pip freeze | grep -i flask > freeze2.txt
deactivate

diff freeze1.txt freeze2.txt   # same machine → may match; over weeks/machines it drifts
```

The point: `requirements.txt` pins *what you install*, not what Flask installs (Werkzeug, Click, …). Nix pins the **entire** tree, so the closure is identical everywhere.

**Comparison table to reproduce in your submission:**

| Aspect | Lab 1 (`pip` + `venv`) | Lab 18 (Nix) |
|--------|------------------------|--------------|
| Python version | system-dependent | pinned in derivation |
| Dependency resolution | runtime (`pip install`) | build-time (pure) |
| Transitive deps | can drift | fully pinned |
| Reproducibility | approximate | bit-for-bit identical |
| Portability | needs same OS + Python | any machine running Nix |
| Storage model | flat `venv` | content-addressed store path |

<details>
<summary>🎁 Optional: build a compiled-language app (Lab 1 bonus)</summary>

If you built the Go version in the Lab 1 bonus, `default.nix` for it is just as reproducible:

```nix
{ pkgs ? import <nixpkgs> {} }:
pkgs.buildGoModule {
  pname      = "devops-info-service-go";
  version    = "1.0.0";
  src        = ./.;
  vendorHash = null;   # or a sha256 if you have module deps (use pkgs.lib.fakeHash to discover it)
}
```

Build with `nix-build` and compare the binary size to your Lab 2 multi-stage Docker image.
</details>

**Document in `submission18.md`:**
- Nix install + `nix --version` output (≥2.25)
- Your `default.nix` with a one-line note on each field
- Store path / hash from a forced rebuild proving it is identical
- Why `requirements.txt` gives weaker guarantees than a Nix derivation
- The `pip + venv` vs Nix comparison table

---

### Task 2 — Reproducible Docker Image (revisiting Lab 2) (4 pts)

**Objective:** Build a container image with Nix's `dockerTools`, then prove it is reproducible where your Lab 2 `Dockerfile` is not.

#### 2.1 Show the Lab 2 image is not reproducible

```bash
docker build -t lab2-app:v1 ./app_python && docker save lab2-app:v1 | sha256sum
docker build -t lab2-app:v2 ./app_python && docker save lab2-app:v2 | sha256sum
```

The two SHA256 sums differ even though the source is identical — Docker writes build timestamps into the layers, and the base image tag can move under you.

#### 2.2 Build the image with `dockerTools`

Create `labs/lab18/app_python/docker.nix` from this skeleton:

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };   # reuse your Task 1 derivation
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag  = "1.0.0";

  contents = [ app ];

  config = {
    # YOUR-TASK: point Cmd at the binary your installPhase produced
    Cmd          = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = { "5000/tcp" = {}; };
  };

  # THE reproducibility trick: a fixed epoch instead of the build time.
  # `created = "now"` would make every build differ — do NOT use it.
  created = "1970-01-01T00:00:01Z";
}
```

> **`buildLayeredImage`** produces an efficient, content-addressed layered tarball — no `FROM` base image, no `apt-get`. The pinned `created` epoch is what removes the last source of non-determinism.

<details>
<summary>📚 Where to learn dockerTools</summary>

- [nix.dev — Building and running Docker images](https://nix.dev/tutorials/nixos/building-and-running-docker-images.html)
- [nixpkgs dockerTools reference](https://nixos.org/manual/nixpkgs/stable/#sec-pkgs-dockerTools)
</details>

Build, load, and run:

```bash
cd labs/lab18/app_python
nix-build docker.nix        # → result is an image tarball
docker load < result        # loads devops-info-service-nix:1.0.0
docker run -d -p 5001:5000 --name nix-app devops-info-service-nix:1.0.0
curl http://localhost:5001/health   # behaves like the Lab 2 container
```

#### 2.3 Prove the Nix image is reproducible

```bash
rm result && nix-build docker.nix && sha256sum result
rm result && nix-build docker.nix && sha256sum result
```

Both SHA256 sums are **identical** — the tarball is bit-for-bit reproducible, unlike the `docker build` output in 2.1.

Also compare image size and layers (`docker images`, `docker history devops-info-service-nix:1.0.0`). The Nix image is typically smaller because it ships only the closure, with no base-image layer, and its layers are content-addressed (same content → same layer hash).

**Comparison table to reproduce in your submission:**

| Aspect | Lab 2 `Dockerfile` | Lab 18 Nix `dockerTools` |
|--------|--------------------|--------------------------|
| Base image | `python:3.13-slim` (moves over time) | none — pure store paths |
| Timestamps | written into each layer | pinned to the epoch |
| Package install | `pip install` at build time | immutable Nix store paths |
| Same input, repeated build | different image SHA | **identical** SHA |
| Caching | layer-based (breaks on timestamp) | content-addressed |

**Document in `submission18.md`:**
- Your `docker.nix` with a note on `created` and why it matters
- The two **differing** `docker save` hashes from 2.1
- The two **identical** `sha256sum result` hashes from 2.3
- Image-size / `docker history` comparison (Lab 2 Dockerfile vs Nix `dockerTools`)
- A short analysis: why can't a plain `Dockerfile` reach bit-for-bit reproducibility?

---

### Bonus Task — Modern Nix with Flakes (2 pts)

**Objective:** Wrap your derivations in a flake so `flake.lock` pins the **entire** dependency closure, and verify cross-machine reproducibility.

> **Why flakes?** Pre-flake Nix was reproducible only if you were disciplined about pinning nixpkgs. A flake makes it the default: `flake.lock` records the exact nixpkgs git SHA — like `package-lock.json`, but for everything down to libc.

#### B.1 Add a flake

Create `labs/lab18/app_python/flake.nix`:

```nix
{
  description = "DevOps Info Service — reproducible build";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";

  outputs = { self, nixpkgs }:
    let
      # x86_64-linux / WSL2. Mac Intel: "x86_64-darwin"; Apple Silicon: "aarch64-darwin"
      system = "x86_64-linux";
      pkgs   = nixpkgs.legacyPackages.${system};
    in {
      packages.${system}.default   = import ./default.nix { inherit pkgs; };
      packages.${system}.dockerImg = import ./docker.nix  { inherit pkgs; };

      # YOUR-TASK: a dev shell with the pinned Python + your app's deps
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [ python313 /* YOUR-TASK: python313Packages.flask, etc. */ ];
      };
    };
}
```

Generate the lock file and build through the flake (Nix 2.25 flake commands):

```bash
git add flake.nix default.nix docker.nix   # flakes only see git-tracked files
nix flake update            # writes flake.lock pinning the exact nixpkgs revision
nix build                   # builds packages.<system>.default
nix build .#dockerImg       # builds the image output
./result/bin/devops-info-service
```

#### B.2 Dev shell vs Lab 1 `venv`

```bash
nix develop                 # isolated shell with the pinned Python + deps
python --version            # exact pinned version, same on every machine
python -c "import flask; print(flask.__version__)"
```

Exit and re-enter — identical versions every time, with no `venv` to activate.

> **Flakes vs Lab 10 Helm pinning:** In Lab 10 you pinned an image *tag* in `values.yaml` (`image.tag: "1.0.0"`). That locks only the container reference — not the Python deps inside it, and the tag can be re-pushed to point at different content. `flake.lock` locks the whole closure cryptographically. The two compose well: build a reproducible image with `nix build .#dockerImg`, load and tag it by content hash, then reference that immutable tag from Helm.

#### B.3 Cross-machine reproducibility

Commit `flake.lock`, push, then on another machine (or a classmate's) build directly from your repo and compare store paths:

```bash
nix build "github:<you>/DevOps-Core-Course?dir=labs/lab18/app_python#default"
readlink result            # identical store path on both machines = same hash, same content
```

**Document in `submission18.md`:**
- Your `flake.nix` and the `flake.lock` snippet showing the locked nixpkgs `rev`
- `nix build` / `nix develop` output
- Proof that the store path is identical across two machines (or two clean builds)
- One short paragraph: how does `flake.lock` prevent a "works on my machine" problem that `requirements.txt` (Lab 1) or a Helm image tag (Lab 10) does not?

---

## Troubleshooting

<details>
<summary>🔧 "command not found" when running the built app</summary>

`app.py` isn't wrapped with an interpreter. Ensure `makeWrapper` is in `nativeBuildInputs` and `wrapProgram` runs in `installPhase`, or add `#!/usr/bin/env python3` to `app.py`.
</details>

<details>
<summary>🔧 "experimental features" error on flake commands</summary>

Flakes aren't enabled. Add `experimental-features = nix-command flakes` to `~/.config/nix/nix.conf` and restart your terminal. (The Determinate installer enables this for you.)
</details>

<details>
<summary>🔧 Flake can't see your files / "path does not exist"</summary>

Flakes only evaluate **git-tracked** files. Run `git add flake.nix default.nix docker.nix` before `nix build`.
</details>

<details>
<summary>🔧 "unsupported system" on macOS</summary>

Change `system` in `flake.nix`: `"x86_64-darwin"` (Mac Intel) or `"aarch64-darwin"` (Apple Silicon).
</details>

<details>
<summary>🔧 Docker load fails</summary>

Confirm `result` is a tarball (`file result`), the Docker daemon is running (`docker info`), and try `docker load -i result`. Check `config.Cmd` points at the binary your `installPhase` actually produced.
</details>

---

## How to Submit

1. Create a branch and add your work:

   ```bash
   git switch -c feature/lab18
   git add labs/lab18/ labs/submission18.md
   git commit -m "feat: lab18 Nix reproducible builds"
   git push -u origin feature/lab18
   ```

2. Open a **PR (GitHub) or MR (GitLab)** from `feature/lab18` → **course repository main branch**.

3. In the PR/MR description, include:

   ```text
   Platform: [GitHub / GitLab]

   - [x] Task 1 — Reproducible Python Build (6 pts)
   - [x] Task 2 — Reproducible Docker Image (4 pts)
   - [ ] Bonus — Modern Nix with Flakes (2 pts)  [if completed]
   ```

4. Submit the PR/MR URL via **Moodle before the deadline**.

---

## Acceptance Criteria

- ✅ Branch `feature/lab18` with `labs/lab18/` (app + Nix expressions) and `labs/submission18.md`
- ✅ Nix **2.25+** installed; `default.nix` builds the Lab 1 app and runs
- ✅ Reproducibility proven for the Python build (identical store path / hash after a forced rebuild)
- ✅ `docker.nix` builds an image with `dockerTools`; two builds give **identical** `sha256sum`
- ✅ The Lab 2 `Dockerfile` is shown to produce **differing** hashes for comparison
- ✅ **Bonus (if attempted):** `flake.nix` + `flake.lock` present; `nix build` / `nix develop` work; cross-machine store path matches
- ✅ PR/MR open against the course repo main branch, link submitted via Moodle

---

## Rubric

| Criterion | Points |
| --------- | -----: |
| Task 1 — Reproducible Python Build (derivation + proof) | **6** |
| Task 2 — Reproducible Docker Image (`dockerTools` + hash proof) | **4** |
| Bonus — Modern Nix with Flakes (`flake.lock` + cross-machine) | **2** |
| **Total** | **12** |

**Grading:**
- **10/10:** Both derivations build, reproducibility proven with hashes, clear comparison vs Lab 1/2
- **8-9/10:** Builds work, reproducibility shown, minor gaps in analysis
- **6-7/10:** Python build works; Docker or proof incomplete
- **<6/10:** Derivation does not build or reproducibility not demonstrated

---

## Resources

<details>
<summary>📚 Nix fundamentals</summary>

- [nix.dev](https://nix.dev/) — official tutorials
- [Zero to Nix](https://zero-to-nix.com/) — Determinate Systems' beginner track
- [Nix Pills](https://nixos.org/guides/nix-pills/) — deep dive
- [NixOS package search](https://search.nixos.org/)
</details>

<details>
<summary>📦 Docker + Flakes</summary>

- [Building Docker images — nix.dev](https://nix.dev/tutorials/nixos/building-and-running-docker-images.html)
- [dockerTools reference](https://nixos.org/manual/nixpkgs/stable/#sec-pkgs-dockerTools)
- [Flakes — NixOS Wiki](https://wiki.nixos.org/wiki/Flakes)
- [Practical Nix Flakes — Serokell](https://serokell.io/blog/practical-nix-flakes)
- [FlakeHub](https://flakehub.com/) — semver flakes registry
</details>

<details>
<summary>💡 Tips</summary>

1. Store paths are content-addressed: same inputs → same output hash.
2. Use `nix-shell -p <pkg>` to test a package before adding it to a derivation.
3. `nix-collect-garbage -d` frees unused builds.
4. Builds are sandboxed with no network — declare every dependency.
5. Pin nixpkgs (flake input or fixed rev) for maximum reproducibility.
</details>

---

**Good luck!** ❄️

> **Remember:** Nix solves *reproducibility*, not orchestration — it's orthogonal to Kubernetes, not a replacement. The payoff is the same hash on every machine, today and in 2036.
