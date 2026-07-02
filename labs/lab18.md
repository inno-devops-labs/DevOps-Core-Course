# Lab 18 — Reproducible Builds with Nix

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Nix%20%26%20Reproducibility-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![type](https://img.shields.io/badge/type-Exam%20Alternative-purple)

> **Goal:** Build your Lab 1 service and a container image with Nix flakes, then prove two independent builds land on the **identical `/nix/store` path** — the bit-for-bit reproducibility that a `Dockerfile` cannot deliver.
> **Deliverable:** A PR from `lab18` adding `labs/lab18/` (your flake + sources) and `labs/submission18.md`. The PR description must include the store path you reproduced.

---

## Overview

A `Dockerfile` and a `requirements.txt` *look* reproducible. They drift:

- `FROM python:3.13-slim` points to different content over time — the tag is mutable
- `pip install -r requirements.txt` lets transitive deps move even with `==` pins on direct ones
- Docker layers embed build timestamps, so the same `Dockerfile` produces a different image SHA every build

Nix fixes this by treating the build as a **pure function of its inputs**. Every input — sources, dependencies, compiler, build flags — is hashed into the output path `/nix/store/<sha256>-<name>-<version>`. Same inputs → same hash → identical output, on any machine, today and in 2036. The same hash also means a cache hit on `cache.nixos.org` skips the rebuild entirely.

In this lab you will practice:

- Writing a **flake** by hand — outer shape, inputs, outputs — choosing the right derivation builder for what you're packaging
- Pinning the full dependency closure with `flake.lock` (the anchor of reproducibility)
- Building a container image with `dockerTools` — no `FROM`, no `apt-get`, no layer timestamps
- **Proving** two independent builds produce the **identical store path** — the bit-for-bit headline

> ⚠️ **Scope:** No Kubernetes, no CI. One service, one flake, two `nix build` runs, one hash comparison. Reproducibility is the whole point — don't get clever.

**This is an Exam Alternative Lab.** Complete both Lab 17 (Cloudflare Workers) and Lab 18 (Nix) to the required bar to replace the final exam. See Lab 17 for the exam-alternative deadline and minimum-score rules. Taken on its own, Lab 18 is a **bonus** lab: **10 pts** of main tasks (6 + 4) + a **2 pt** bonus = **12 pts max**.

**Tech stack (May 2026):** Nix **2.25+** (flakes stable since 2.18; Determinate / official installer) · `nixos/nix` container as the WSL-friendly path · nixpkgs `nixos-25.11` (release branch, pinned via flake input) · `dockerTools.buildLayeredImage` · Docker (to `docker load` the resulting image)

> **Lix:** a community fork of Nix (forked March 2024) is a drop-in `nix` replacement with faster evaluation and friendlier governance. Either Nix 2.25+ or current Lix works for this lab.

> **Note on outputs:** every command output, hash, and store path shown below is **illustrative** — yours will differ. What must be reproducible is that **your own** two builds produce the **identical** path.

---

## Project State

**You should have from previous labs:**

- `app_python/` — the Flask / FastAPI service from Lab 1 with `GET /` and `GET /health`
- `app_python/Dockerfile` from Lab 2 (you'll contrast it against `dockerTools` in Task 2)

> If you no longer have Lab 1/2 artifacts, a one-route Flask app (`app.py` with `/health`) plus a one-line `requirements.txt` is enough to complete every task. The skill being graded is *the flake*, not the app.

**This lab adds:**

- `labs/lab18/flake.nix` — your flake (Task 1)
- `labs/lab18/flake.lock` — the lock file pinning the full closure (Task 1, committed)
- `labs/lab18/app/` — sources for your derivation
- `labs/submission18.md` — your submission report

---

## Setup

Nix installs to `/nix` at the system root and needs `root` to do so. On WSL2 (and on locked-down hosts) the cleanest path is the **`nixos/nix` Docker image** — it ships Nix with flakes pre-enabled and leaves your host filesystem untouched. The reference submission was built that way.

**Path A — `nixos/nix` container (recommended on WSL / locked-down hosts):**

```bash
# Pinned image tag — do NOT use :latest (mutable). 2.34 or any 2.25+ is fine.
docker run --rm -it \
  -v "$PWD":/work -w /work \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --entrypoint /bin/sh \
  nixos/nix:2.34.0

# inside the container — flakes need the experimental feature flag explicit
nix --version
nix --extra-experimental-features 'nix-command flakes' eval --expr '1 + 1'
```

The `docker.sock` mount lets `docker load < result` work from inside the Nix container in Task 2.

**Path B — host install (Linux / macOS with sudo):**

```bash
# Determinate Systems installer — flakes on by default, clean uninstall
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
nix --version            # expect 2.25.x or newer
```

<details>
<summary>🐧 Alternative: official Nix installer — use this if `install.determinate.systems` is unreachable or times out from your network (flakes must be enabled by hand)</summary>

```bash
sh <(curl -L https://nixos.org/nix/install) --daemon
```

Then add to `~/.config/nix/nix.conf` and restart your terminal:

```
experimental-features = nix-command flakes
```

</details>

Sanity check (either path) — run a package without installing it:

```bash
nix run nixpkgs#hello   # downloads + runs `hello`, installs nothing permanent
```

Create the layout:

```
labs/lab18/
├── flake.nix          # YOU WRITE — Task 1
├── flake.lock         # generated by `nix flake update`, committed
├── app/               # your Lab 1 sources (or the minimal stub)
│   ├── app.py
│   └── requirements.txt
└── (submission18.md lives one level up at labs/submission18.md)
```

---

## Task 1 — Write a flake that builds the Lab 1 app (6 pts)

**Objective:** Hand-write `flake.nix` from a structural skeleton, build the Lab 1 service through it, and commit `flake.lock` so the closure is pinned.

### 1.1 — Outer shape of the flake

A flake is a Nix expression with three top-level fields: `description`, `inputs`, `outputs`. **What's inside each is yours.** The skeleton below shows only the **shape** — the choices that make this *your* reproducible build are blank.

```nix
# labs/lab18/flake.nix
{
  description = ___;                       # YOUR TASK: one short string describing what this flake builds

  inputs = {
    # YOUR TASK: pick a NIXPKGS REVISION AND PIN IT.
    # The lab tests `nixos-25.11` (the Nov-2024 release branch). NOT `nixpkgs-unstable`
    # — unstable means non-reproducible across days. Use a release tag.
    # Format: github:NixOS/nixpkgs/<branch-or-rev>
    nixpkgs.url = ___;
  };

  outputs = { self, nixpkgs }:
    let
      # YOUR TASK: pick the system you're building for.
      #   x86_64-linux  — WSL2 / most Linux laptops / CI
      #   aarch64-linux — Linux on Apple Silicon under Docker / Asahi
      #   aarch64-darwin — Apple Silicon macOS native
      #   x86_64-darwin  — Intel macOS
      system = ___;
      pkgs   = ___;                        # YOUR TASK: legacyPackages for the chosen system
    in {
      packages.${system}.default = ___;    # YOUR TASK: a derivation that builds your app — see 1.2
      # Task 2 will add a second output here: packages.${system}.dockerImg
    };
}
```

**Why each line is a rubric line:**

- **`description`** — one sentence; appears in `nix flake show` and `nix flake metadata`. Make it useful.
- **`inputs.nixpkgs.url`** — *the* reproducibility anchor. A release tag (`nixos-25.11`) or a specific commit SHA freezes the entire dependency tree. **`nixpkgs-unstable` is wrong here** — its tip moves daily and is the most common "reproducible build that isn't" mistake.
- **`system`** — flake outputs are per-system. Pick the one you'll demo on; classmates on other systems can add their own to your flake.
- **`pkgs`** — `nixpkgs.legacyPackages.${system}` is the canonical handle for "the package set, evaluated for this system." Memorise it.
- **`packages.${system}.default`** — what `nix build` (no `.#attr`) builds. This is your service.

### 1.2 — Pick a derivation and fill its body

The Nix store has dozens of builder functions (`mkDerivation`, `writeShellApplication`, `buildPythonApplication`, `buildGoModule`, …). Each one makes different assumptions about what it's packaging. Pick the one that matches your Lab 1 stack:

| Builder | Best for | Key inputs |
|---|---|---|
| `pkgs.writeShellApplication` | A wrapper script that calls something else (the reference submission uses this) | `name`, `runtimeInputs`, `text` |
| `pkgs.stdenv.mkDerivation` | Generic — you supply `buildPhase` / `installPhase` | `src`, `buildInputs`, `installPhase` |
| `pkgs.python3Packages.buildPythonApplication` | A Python app with `pyproject.toml` / `setup.py` | `pname`, `version`, `src`, `propagatedBuildInputs`, `format` |
| `pkgs.buildGoModule` | A Go program (Lab 1 bonus) | `pname`, `src`, `vendorHash` |

**`YOUR TASK`**: in the `default = ___` blank from 1.1, call the builder that fits your app. Examples of the **shape only** (the inside is still yours):

```nix
# Shape 1 — writeShellApplication (good if your "app" is a thin shell entrypoint
# that calls into python/curl/whatever from the pinned closure)
packages.${system}.default = pkgs.writeShellApplication {
  name         = ___;                       # YOUR TASK: the binary name produced under result/bin/
  runtimeInputs = with pkgs; [ ___ ];       # YOUR TASK: every command your text uses (python3, curl, …)
  text         = ___;                       # YOUR TASK: the shell body. Single-quoted ''…'' multiline OK
};
```

```nix
# Shape 2 — buildPythonApplication (if you have a real Python package)
packages.${system}.default = pkgs.python3Packages.buildPythonApplication {
  pname   = ___;                            # YOUR TASK
  version = ___;                            # YOUR TASK
  src     = ___;                            # YOUR TASK — usually ./app
  format  = ___;                            # YOUR TASK — "other" if no pyproject/setup
  propagatedBuildInputs = with pkgs.python3Packages; [ ___ ]; # YOUR TASK — flask, etc.
  nativeBuildInputs     = [ pkgs.makeWrapper ];
  installPhase = ___;                       # YOUR TASK — copy app.py → $out/bin, wrapProgram with PYTHONPATH
};
```

```nix
# Shape 3 — buildGoModule (if you did the Lab 1 Go bonus)
packages.${system}.default = pkgs.buildGoModule {
  pname      = ___;                         # YOUR TASK
  version    = ___;                         # YOUR TASK
  src        = ___;                         # YOUR TASK
  vendorHash = ___;                         # YOUR TASK — null if no deps; else a sha256 from lib.fakeHash discovery
};
```

> **Why no PyPI?** A Nix build is **sandboxed with no network** by default. Nix pulls packages from the pinned nixpkgs revision (`Flask` → `pkgs.python3Packages.flask`). That's *the* reason the closure is reproducible: every dep is itself a fixed `/nix/store/...` path, not a `pip resolve` away.

<details>
<summary>📚 Where to learn the derivation syntax</summary>

- [nix.dev — Building and running Python apps](https://nix.dev/tutorials/nixos/building-and-running-python-apps)
- [nixpkgs Python manual](https://nixos.org/manual/nixpkgs/stable/#python)
- [`writeShellApplication`](https://nixos.org/manual/nixpkgs/stable/#trivial-builder-writeShellApplication) — the lightest builder, shellcheck-validated
- [Nix Pills — Our first derivation](https://nixos.org/guides/nix-pills/our-first-derivation.html)

Pick **one** builder and defend the choice in `submission18.md` — TA grading docks for builder choices that don't match what's actually being packaged.

</details>

### 1.3 — Generate `flake.lock` and commit it

`flake.lock` records the exact git SHA of every flake input. Without it, `nixpkgs/nixos-25.11` resolves to *whatever the branch tip is today* — fine for a few weeks, drifting silently over months. The lock file is what makes "build in 2026" identical to "build in 2036".

```bash
cd labs/lab18
git add flake.nix app/                    # flakes only see git-tracked files — see Pitfalls
nix flake update                           # writes flake.lock; pins each input to a specific rev
git add flake.lock                         # MUST be committed
nix build                                  # builds packages.${system}.default
./result/bin/<your-name>                   # runs your app
```

`YOUR TASK`: open `flake.lock` and **answer in `submission18.md`**:

- What field pins the exact `nixpkgs` revision? (Hint: it's not `ref`. Look at `locked.rev` and `locked.narHash`.)
- Why does committing `flake.lock` matter, given you already pinned `nixpkgs-24.11` in `flake.nix`?

### 1.4 — Proof of work

**Paste into `labs/submission18.md`:**

- Your `flake.nix` contents (it's short — paste the whole thing) with a one-line note per `___` you filled in
- The first 20 lines of your `flake.lock` (specifically, the `nixpkgs` node showing `locked.rev` + `locked.narHash`)
- The output of:

  ```bash
  nix build .#default
  readlink result                            # /nix/store/<hash>-<name>  ← capture this exact path
  ./result/bin/<your-name>                   # proves the binary runs
  ```

- Your one-paragraph answer to 1.3's "what does the lock pin?" question

---

## Task 2 — Reproducible Docker image with `dockerTools` (4 pts)

**Objective:** Build a container image **from your flake** using `dockerTools.buildLayeredImage`, then contrast it with your Lab 2 Dockerfile (whose hash changes every build).

### 2.1 — Show your Lab 2 image is not reproducible

```bash
docker build -t lab2-app:v1 ./app_python && docker save lab2-app:v1 | sha256sum
docker build -t lab2-app:v2 ./app_python && docker save lab2-app:v2 | sha256sum
```

`YOUR TASK`: capture both SHA256 sums and confirm they differ. They do — Docker writes build timestamps into the layers, and `python:3.13-slim` can move under you between the two builds. Paste both sums into `submission18.md`.

### 2.2 — Add a `dockerImg` output to your flake

Add a second package output to the flake from Task 1. The skeleton below shows the **shape** of `buildLayeredImage` — every body field is yours. There is **no fully-formed example** — by the time you see one whole, it's typing practice, not learning.

```nix
# Inside the same outputs = { … } block from Task 1, alongside packages.${system}.default
packages.${system}.dockerImg = pkgs.dockerTools.buildLayeredImage {
  name = ___;          # YOUR TASK: the image name (becomes `docker images` REPOSITORY).
                       # Not "latest" — that's a tag, not a name. Pick something self-explanatory.

  tag  = ___;          # YOUR TASK: a SemVer / CalVer / git-SHA tag. NOT "latest" (slide 20 of Lec 2).

  contents = [ ___ ];  # YOUR TASK: what goes inside the image filesystem.
                       # At minimum, your Task-1 package (referenced by `self.packages.${system}.default`
                       # OR a local `let app = … in app` binding). Add pkgs.coreutils / pkgs.cacert
                       # only if your binary needs `ls`/`cat` or HTTPS at runtime.

  config = {
    Cmd          = [ ___ ];          # YOUR TASK: the command that runs at container start. Exec form.
                                     # Point at the binary your Task-1 derivation produced —
                                     # e.g. "${app}/bin/<name>". Shell form would re-introduce the PID-1 trap
                                     # you learned to avoid in Lab 2.
    ExposedPorts = { ___ = {}; };    # YOUR TASK: the port your service listens on (Lab 1 default: 5000/tcp;
                                     # Lab 2's container overrode this via PORT=8080 env var, but a fresh Nix
                                     # build with writeShellApplication honors Lab 1's PORT default).
                                     # The key is a string like "5000/tcp". If you want 8080, also add
                                     # `Env = [ "PORT=8080" ];` to this config block.
  };

  # THE reproducibility trick. Nix gives you a knob most container builders don't:
  # the embedded creation timestamp. Set it to a FIXED epoch instead of "now".
  created = ___;       # YOUR TASK: a fixed RFC-3339 timestamp string. NOT "now" — that re-introduces
                       # non-determinism (every build differs). NOT 1970-01-01T00:00:00Z either
                       # (Docker tooling sometimes rejects the literal Unix epoch). The accepted convention
                       # is `1970-01-01T00:00:01Z` — one second after the epoch.
};
```

> **`buildLayeredImage`** produces an efficient, content-addressed layered tarball — no `FROM` base image, no `apt-get`, no `RUN`. The pinned `created` epoch is what removes the last source of non-determinism.

<details>
<summary>📚 Where to learn dockerTools</summary>

- [nix.dev — Building and running Docker images](https://nix.dev/tutorials/nixos/building-and-running-docker-images.html)
- [nixpkgs `dockerTools` reference](https://nixos.org/manual/nixpkgs/stable/#sec-pkgs-dockerTools) — `buildImage` vs `buildLayeredImage` vs `streamLayeredImage`
- [pkgs.cacert](https://search.nixos.org/packages?show=cacert) — if your app calls HTTPS

</details>

### 2.3 — Build, load, run

```bash
nix build .#dockerImg                  # → result is an image tarball, not a symlink to a binary
file result                            # confirms it's a gzip'd tar

# From inside the Nix container, the docker.sock mount lets this work; on host, you have docker directly
docker load < result                   # loads <your-name>:<your-tag>
docker run -d -p 5001:5000 --name lab18 <your-name>:<your-tag>      # if you exposed 5000/tcp
# or, if you set Env = [ "PORT=8080" ] AND ExposedPorts = { "8080/tcp" = {}; }:
# docker run -d -p 5001:8080 --name lab18 <your-name>:<your-tag>
curl http://localhost:5001/health      # behaves like the Lab 2 container
```

### 2.4 — Compare against the Lab 2 image

```bash
docker images --format '{{.Repository}}\t{{.Tag}}\t{{.Size}}' | grep -E 'lab2-app|<your-name>'
docker history <your-name>:<your-tag>
```

`YOUR TASK`: read your own `docker history`. The Nix image typically:

- Has **layers whose hashes are content-addressed** (same content → same layer hash, across builds and machines)
- Ships **only the closure** — no Debian base, no `apt` cache, often smaller than the slim-based image
- Has a `CREATED` timestamp that's **the epoch you set**, not `now`

In `submission18.md`, write a one-paragraph finding comparing your Lab 2 image to the `dockerTools` image: size, layer count, and the `CREATED` column.

### 2.5 — Proof of work

**Paste into `labs/submission18.md`:**

- The `dockerImg` block of your `flake.nix` (the contents + config you wrote)
- The two **differing** `docker save | sha256sum` outputs from 2.1
- The `docker load` log line showing the loaded image name + tag
- A real `curl` against `/health` proving the loaded image runs
- The `docker images` + `docker history` rows comparing Lab 2 vs your Nix image
- A two-sentence analysis: *why* a plain `Dockerfile` can't reach bit-for-bit reproducibility (the epoch trick, the base-image drift, the `apt-get` non-determinism). Reference the lecture, slides 15 and 18.

---

## Bonus Task — Prove the build is bit-for-bit reproducible (2 pts)

**Objective:** Run **two** independent `nix build` invocations and show they land on the **identical `/nix/store` path**. This is the headline of the entire lab — a successful build by itself isn't proof; *two builds that match* is.

The reference submission's proof is **two `nix build .#default` runs, the second with `--rebuild`, both producing the same store path** plus an explicit hash equality. Nix's `--rebuild` flag forces a real rebuild (not a cache hit) and then **verifies that the output of the new build matches the existing store path bit-for-bit** — if anything differed, Nix would report it loudly.

`YOUR TASK`: design and execute the proof yourself. The lab does NOT give you the commands. You will need to:

1. Build `packages.${system}.default` once, capture the resulting store path
2. Force Nix to do a **real, full rebuild** (not a cache hit) and capture the path the rebuild lands on
3. Show that both paths are **identical** — and that Nix itself validates this in step 2 ("identical store path both builds" / "checking outputs of …")
4. Repeat the same proof for `packages.${system}.dockerImg` (the image tarball) — `sha256sum result` from two clean builds must match
5. Explain in `submission18.md` *why* this works: the role of the input hash, why `flake.lock` is the precondition, why `--rebuild` is the right command (`nix-store --delete` alone is brittle)

Hints (not commands):

- The flag you want forces a rebuild and verifies output equality automatically. Search `nix build --help` for the option whose description mentions "rebuild ... and check that the result is the same."
- `readlink result` gives you the path. `sha256sum result` gives you the tarball hash for the Docker image.
- If your two paths differ, your build has a non-determinism. Common causes: a `created = "now"` you forgot to fix, a `mkDerivation` with an unpinned `fetch*` input, or a missing `flake.lock`.

**Paste into `labs/submission18.md`:**

- The two commands you ran (the order matters — you'll figure out the right ones from `nix build --help`)
- The captured `readlink result` from both runs of `default` — same string
- The captured `sha256sum result` from two clean rebuilds of `dockerImg` — same digest
- Nix's own confirmation line (something like `checking outputs of '/nix/store/<drv>'... IDENTICAL store path both builds`)
- A short paragraph answering: how does `flake.lock` prevent the "works on my machine" failure mode that `requirements.txt` (Lab 1) and a Helm image tag (Lab 10) cannot?

> 🏆 **This is the whole point of the lab.** A flake that builds isn't enough. A flake that builds **the same store path twice** is what "reproducible" actually means.

---

## How to Submit

```bash
git switch -c lab18
git add labs/lab18/flake.nix labs/lab18/flake.lock labs/lab18/app/
git add labs/submission18.md
git commit -m "feat(lab18): Nix reproducible build with flake + dockerTools"
git push -u origin lab18
```

Open **two** PRs:

- `your-fork:lab18` → `course-repo:master` *(reviewed)*
- `your-fork:lab18` → `your-fork:master` *(merges into your own main when done)*

PR checklist:

```text
- [ ] Task 1 — flake.nix written by hand, flake.lock committed, app builds
- [ ] Task 2 — dockerImg output added; image loads and runs; comparison to Lab 2 Dockerfile documented
- [ ] Bonus — two independent builds land on the identical store path; sha256sum equality proven for the image
```

Include in the PR description: **the store path** you reproduced (`/nix/store/<hash>-<name>`) and the **tarball sha256** from two `dockerImg` builds. Those two strings are the artifact of this lab.

---

## Acceptance Criteria

### Task 1 — Flake builds the app (6 pts)
- ✅ `labs/lab18/flake.nix` written from the skeleton (`description`, `inputs`, `outputs` all filled)
- ✅ `inputs.nixpkgs.url` pinned to a **release tag** (e.g. `nixos-25.11`) — **not** `nixpkgs-unstable`
- ✅ `packages.${system}.default` builds with one of `writeShellApplication`, `mkDerivation`, `buildPythonApplication`, or `buildGoModule` — choice defended in `submission18.md`
- ✅ `flake.lock` present, **committed**, and shown in the submission with the `locked.rev` field highlighted
- ✅ `nix build` produces a working binary at `result/bin/<name>` that runs the Lab 1 service logic

### Task 2 — `dockerTools` image (4 pts)
- ✅ `packages.${system}.dockerImg` added to the flake
- ✅ `buildLayeredImage` `contents` includes the Task-1 package
- ✅ `config.Cmd` points at the binary in exec form
- ✅ `config.ExposedPorts` set
- ✅ `created` is a **fixed epoch string** (not `"now"`) — typically `"1970-01-01T00:00:01Z"`
- ✅ `nix build .#dockerImg` produces a tarball; `docker load < result` succeeds; the loaded image runs and serves `/health`
- ✅ Two `docker build` runs of the Lab 2 Dockerfile show **differing** `docker save | sha256sum` outputs, captured in `submission18.md`

### Bonus — Bit-for-bit proof (2 pts)
- ✅ Two independent `nix build .#default` runs (the second forcing a real rebuild) produce the **identical** `/nix/store/<hash>-<name>` path
- ✅ Two independent `nix build .#dockerImg` runs produce the **identical** `sha256sum result` digest
- ✅ Nix's own "identical store path / checking outputs" confirmation captured
- ✅ Paragraph in `submission18.md` explaining the role of `flake.lock` vs `requirements.txt` / Helm image tag

---

## Rubric

| Task | Points | Criteria |
|------|-------:|----------|
| **Task 1** — Flake + lock + build | **6** | Outer shape filled, nixpkgs pinned to a release tag, derivation builder chosen correctly, `flake.lock` committed, binary runs |
| **Task 2** — `dockerTools` image | **4** | Image output added, `created` epoch trick applied, image loads & runs, contrast vs Lab 2 documented with both `sha256sum`s |
| **Bonus** — Bit-for-bit proof | **2** | Two builds → identical store path AND identical image sha256; Nix's own equality check captured |
| **Total** | **12** | 10 main + 2 bonus |

**Grading guidance:**
- **10/10 main** — Flake builds, image loads, proof of reproducibility is clean, `flake.lock` discussion shows understanding of *why* it matters
- **8–9/10** — Builds work; reproducibility claim shown but missing one of the headline artifacts (store path **or** image sha256)
- **6–7/10** — Task 1 works; Task 2 image builds but the `created` epoch isn't applied, or the Lab-2 contrast isn't measured
- **<6/10** — Flake doesn't build, `flake.lock` missing, or `nixpkgs-unstable` used (reproducibility not actually achieved)

---

## Resources

<details>
<summary>📚 Nix fundamentals</summary>

- [nix.dev](https://nix.dev/) — official tutorials
- [Zero to Nix](https://zero-to-nix.com/) — Determinate Systems' beginner track (flakes-first)
- [Nix Pills](https://nixos.org/guides/nix-pills/) — deep dive for the curious
- [NixOS package search](https://search.nixos.org/) — find the `pkgs.<name>` you need

</details>

<details>
<summary>📦 Flakes, dockerTools, and proof</summary>

- [Flakes — NixOS Wiki](https://wiki.nixos.org/wiki/Flakes)
- [Practical Nix Flakes — Serokell](https://serokell.io/blog/practical-nix-flakes)
- [FlakeHub](https://flakehub.com/) — SemVer flakes registry
- [`dockerTools` reference](https://nixos.org/manual/nixpkgs/stable/#sec-pkgs-dockerTools)
- [`nix build --help`](https://nix.dev/manual/nix/stable/command-ref/new-cli/nix3-build.html) — the flag you want for the Bonus lives here
- [Reproducible Builds project](https://reproducible-builds.org/) — why this matters beyond Nix

</details>

<details>
<summary>🐧 Container-Nix vs host-Nix</summary>

- [`nixos/nix` Docker images](https://hub.docker.com/r/nixos/nix) — pinned tags (use `2.34.0` or any 2.25+)
- [Determinate Nix](https://determinate.systems/) — host installer with flakes-on-default
- [Lix](https://lix.systems/) — community fork, drop-in `nix` replacement

</details>

<details>
<summary>⚠️ Common Pitfalls (from real dry-runs)</summary>

- **Flakes only see git-tracked files** — if you `nix build` before `git add flake.nix flake.lock app/`, Nix reports `path 'flake.nix' does not exist` or evaluates against an empty source tree. **Always `git add` first**, then build. This is THE most common Lab-18 mistake. (Reference dry-run hit it.)
- **`safe.directory` inside the `nixos/nix` container** — the container runs as `root` (uid 0); your bind-mounted repo on the host is owned by your uid. `nix build` invokes libgit2, which refuses with `repository path '/work/' is not owned by current user`. Fix once: `git config --global --add safe.directory /work` inside the container. This is a **containerized-Nix artifact**, not a flake defect; host-Nix doesn't hit it.
- **`dockerTools.buildLayeredImage` with `created = "now"` defeats reproducibility** — every build will produce a different image hash. Reading the docs you'll see `"now"` mentioned as the default for `buildImage`; that's exactly what you must override. Use `"1970-01-01T00:00:01Z"` (one second past the epoch — the literal epoch is rejected by some tooling).
- **`inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable"`** — the branch tip moves daily, so today's build won't match next week's. The whole point of reproducibility is gone. Use a release tag (`nixos-25.11`) or pin a specific commit SHA.
- **`nix flake update` rewrites `flake.lock`** — don't run it casually before a proof of reproducibility, or you'll change the closure under your own feet. Run it once after writing `flake.nix`, commit `flake.lock`, then leave it alone for the rest of the lab.
- **`writeShellApplication` rejects unset variables** — it injects `set -euo pipefail` for you. If your script reads `$HOSTNAME` and you forgot to add `runtimeInputs = [ pkgs.inetutils ];` (or set the variable explicitly), the build passes but the script fails at runtime. Cleaner to use a Nix-resolved value.
- **`nix-store --delete` to "force a rebuild" is brittle** — Nix may legitimately recover the cached output from elsewhere. Use `nix build --rebuild` for the Bonus proof; it explicitly does what you want (real rebuild + output-equality check).
- **`format = "other"` in `buildPythonApplication`** — required when your source has no `pyproject.toml` / `setup.py`. Without it, Nix tries to invoke `pip install .` and fails. Single-file Flask apps almost always need `format = "other"`.
- **`USER` in `dockerTools` config is a string, not a number** — `config.User = "1000:1000"` works; `config.User = 1000` evaluates fine but Docker may complain on `docker run`. Use the `"uid:gid"` form.

</details>

<details>
<summary>💡 Tips</summary>

1. Store paths are content-addressed: same inputs → same output hash. Always.
2. `nix-shell -p <pkg>` (classic CLI) or `nix shell nixpkgs#<pkg>` (new CLI) drops you into a shell with that package on `$PATH` — great for testing a dep before adding it to your derivation.
3. `nix-collect-garbage -d` frees disk space taken by old builds.
4. Builds are sandboxed with **no network** — every dependency must be declared. If the build mysteriously needs internet, you're missing an input.
5. Use a **release branch** for `nixpkgs` (`nixos-25.11`, `nixos-24.05`) — *not* unstable. The release tag is what makes "build today and in 2036" make sense.
6. `nix flake show` lists every output your flake exposes. Useful when your `packages.${system}` block grows.

</details>

---

## Looking Ahead

Nix is **orthogonal** to the orchestration you spent the rest of the course mastering — it solves reproducibility, not scheduling. Where you'll meet it again:

| Domain | What Nix adds |
|---|---|
| CI | One-line `nix build` instead of "install N tools" pre-steps; build cache via Cachix |
| Dev shells | `nix develop` gives every contributor identical Python/Node/Go versions — no `venv`/`asdf`/`nvm` drift |
| Image builds | `dockerTools` images plug into the same registries / Helm charts you used in Labs 10-13 |
| Security audit | The closure is the artifact; SBOM is by construction |
| NixOS | If you ever want the same purity at the **OS** level |

---

**Hot take:** containers solved *deployment*. Nix solves *the build*. Two different problems, two different tools — and the only way to know yours actually ships what you wrote is to build it twice and watch the hashes match. ❄️
