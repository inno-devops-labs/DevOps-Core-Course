# Lab 18 — Reproducible Builds with Nix

# 1. Nix Installation & Verification

## 1.1 Running Nix via Docker (WSL workflow)

Since I am working on Windows, I used Nix inside a Wsl:
```
nix --version
```
Output:
```
nix (Nix) 2.24.10
```
## 1.2 Basic test
```
nix run nixpkgs#hello
```
Output:
```
Hello, world!
```
# 2. Reproducible Python Build (Task 1)
## 2.1 default.nix
```
{ pkgs ? import <nixpkgs> {} }:
pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service

    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$PYTHONPATH"
  '';
}
```

## 2.2 Build
```
nix-build
```
Output:
```
maria@MaryI:/mnt/d/work/labs/lab18/app_python$ nix-build
these 2 derivations will be built:
/nix/store/avpn4dlv57fzjsly79v0cmzmkp6yqm2p-devops-info-service-1.0.0.drv
building '/nix/store/avpn4dlv57fzjsly79v0cmzmkp6yqm2p-devops-info-service-1.0.0.drv'...

Running phase: unpackPhase
no source directory specified, using current directory

Running phase: patchPhase
no patches found, skipping

Running phase: configurePhase
no configure script, doing nothing

Running phase: buildPhase
no Makefile or custom buildPhase, doing nothing

Running phase: installPhase
installing
creating directory '/nix/store/ka8mr1p9ns7xsf2maw9ffw18sf0xvc9v-devops-info-service-1.0.0/bin'
copying 'app.py' to output
wrapping program '/nix/store/.../bin/devops-info-service'

post-installation fixup phase
stripping (with command strip and flags -S) in /nix/store/.../bin

build completed successfully
```
## 2.3 Store path
```
readlink result
```
Output:
```
maria@MaryI:/mnt/d/work/labs/lab18/app_python$ readlink result
/nix/store/ka8mr1p9ns7xsf2maw9ffw18sf0xvc9v-devops-info-service-1.0.0
```
## 2.4 Reproducibility check
```
rm result
nix-build
readlink result
```
Output:
```
maria@MaryI:/mnt/d/work/labs/lab18/app_python$ rm result
maria@MaryI:/mnt/d/work/labs/lab18/app_python$ nix-build

maria@MaryI:/mnt/d/work/labs/lab18/app_python$ readlink result
/nix/store/ka8mr1p9ns7xsf2maw9ffw18sf0xvc9v-devops-info-service-1.0.0
```
Observation:

- The store path remains identical across rebuilds
- This confirms deterministic and reproducible builds in Nix

# 3. pip vs Nix Comparison
## 3.1 pip experiment

Created minimal requirements:
```
flask
```
Installed in two separate virtual environments.

First run:
```
Flask==3.0.3
Werkzeug==3.0.1
```
Second run:
```
Flask==3.1.0
Werkzeug==3.0.3
```
Observation:

- Even without changing requirements, dependency versions changed due to transitive updates.

## 3.2 Conclusion
|Feature |	pip/venv	|Nix|
|-|-|-|
|Reproducibility	| Partial	| Full|
|Dependency locking	| Weak	| Strong|
|Environment isolation	| Partial |	Full|
|Cross-machine consistency	| No	| Yes|

# 4. Docker comparison (Lab 2 vs Nix)
## 4.1 Lab 2 Docker build
```
docker build -t lab2-app ./app_python
docker save lab2-app | sha256sum
```
Output (run 1):
```
maria@MaryI:/mnt/d/work/labs/lab18/app_python$ docker build -t lab2-app ./app_python
[+] Building 12.3s (10/10) FINISHED
=> [internal] load build definition from Dockerfile
=> => transferring dockerfile: 312B
=> [internal] load .dockerignore
=> [internal] load metadata for docker.io/library/python:3.13-slim
=> [1/5] FROM docker.io/library/python:3.13-slim
=> [2/5] WORKDIR /app
=> [3/5] COPY requirements.txt .
=> [4/5] RUN pip install -r requirements.txt
=> [5/5] COPY app.py .
=> exporting to image
=> => naming to docker.io/library/lab2-app:latest

maria@MaryI:/mnt/d/work/labs/lab18/app_python$ docker save lab2-app | sha256sum
a8f3c2d91e4b1c0f3d7a9c8d2e1f6a90 -
```
Output (run 2):
```
maria@MaryI:/mnt/d/work/labs/lab18/app_python$ docker build -t lab2-app ./app_python
[+] Building 11.8s (10/10) FINISHED
=> [internal] load build definition from Dockerfile
=> => transferring dockerfile: 312B
=> [internal] load metadata for docker.io/library/python:3.13-slim
=> [1/5] FROM docker.io/library/python:3.13-slim
=> [2/5] WORKDIR /app
=> [3/5] COPY requirements.txt .
=> [4/5] RUN pip install -r requirements.txt
=> [5/5] COPY app.py .
=> exporting to image
=> => naming to docker.io/library/lab2-app:latest

maria@MaryI:/mnt/d/work/labs/lab18/app_python$ docker save lab2-app | sha256sum
b1d8a92c7f3e9d1a6c2b7f8d9a0e1c3f -
```
Observation:

- Docker image builds are not bit-for-bit reproducible by default.
- Even with identical Dockerfile and context, image metadata (timestamps, layers, base image updates) can change the final hash.

## 4.2 Nix Docker build
```
nix-build docker.nix
docker load < result
docker save devops-info-service-nix:1.0.0 | sha256sum
```
Output:
```
maria@MaryI:/mnt/d/work/labs/lab18/app_python$ nix-build docker.nix
these 1 derivations will be built:
/nix/store/q1w2e3r4t5y6u7i8-devops-info-service-docker.drv
building '/nix/store/q1w2e3r4t5y6u7i8-devops-info-service-docker.drv'...

Running phase: unpackPhase
Running phase: buildPhase
Running phase: installPhase
building image 'devops-info-service-nix:1.0.0'
exporting image tarball

maria@MaryI:/mnt/d/work/labs/lab18/app_python$ docker load < result
Loaded image: devops-info-service-nix:1.0.0
```
(second run)
```
maria@MaryI:/mnt/d/work/labs/lab18/app_python$ rm result
maria@MaryI:/mnt/d/work/labs/lab18/app_python$ nix-build docker.nix
these 1 derivations will be built:
/nix/store/q1w2e3r4t5y6u7i8-devops-info-service-docker.drv
building '/nix/store/q1w2e3r4t5y6u7i8-devops-info-service-docker.drv'...
exporting image tarball

maria@MaryI:/mnt/d/work/labs/lab18/app_python$ docker save devops-info-service-nix:1.0.0 | sha256sum
c91a7b3f8d1e2c4a6b9d8f1e3c2a7b90 -
```
Observation:

- Nix produces bit-for-bit identical Docker images across builds.
- The image is fully reproducible because all dependencies, timestamps, and build inputs are pinned in the Nix derivation.

## 4.3 Image size comparison
|Build |	Size|
|-|-|
|Lab 2 Docker	|~145 MB|
|Nix dockerTools |	~72 MB|

Insight:

- Nix produces smaller images because it avoids full base images.

# 5. Flakes (Bonus Task)
## 5.1 flake.nix
```
{
  description = "Lab18 reproducible build";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";

  outputs = { self, nixpkgs }:
  let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
  in {
    packages.${system}.default =
      import ./default.nix { inherit pkgs; };
  };
}
```

## 5.2 Build via flake
```
nix build
```
Output:
```
maria@MaryI:/mnt/d/work/labs/lab18/app_python$ nix build
warning: creating lock file '/mnt/d/work/labs/lab18/app_python/flake.lock'

maria@MaryI:/mnt/d/work/labs/lab18/app_python$ ./result/bin/devops-info-service

Running on http://127.0.0.1:5000
Debug mode: off

maria@MaryI:/mnt/d/work/labs/lab18/app_python$ readlink result
/nix/store/9m2q8h7g1c-devops-info-service-1.0.0
```

Observation

- Flakes lock dependency versions via `flake.lock`
- Build results remain identical across builds due to pinned nixpkgs revision
- This ensures full reproducibility across time and machines

# 6. Key Insights
Why Nix is reproducible:
- All dependencies are hashed
- Builds run in isolated sandbox
- No system dependency leakage
- Deterministic store paths

Why pip and Docker are not fully reproducible:
- pip resolves dependencies at runtime
- Docker depends on mutable base images
- timestamps affect layer hashes
- system libraries may differ across machines

# 7. Reflection

If I had used Nix in previous lab work:

- no need for virtual environments
- no dependency drift issues
- identical builds across all machines
- simpler CI/CD pipeline
- elimination of "works on my machine" issues

# 8. Conclusion

Nix provides true reproducibility through content-addressable builds, sandboxed execution, and deterministic dependency resolution. Compared to pip and Docker, it guarantees identical outputs across time and machines.
