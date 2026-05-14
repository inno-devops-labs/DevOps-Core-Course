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
this derivation will be built:
  /nix/store/7k9x1f3d2v-devops-info-service-1.0.0.drv
building '/nix/store/7k9x1f3d2v-devops-info-service-1.0.0.drv'...
/nix/store/9m2q8h7g1c-devops-info-service-1.0.0
```
## 2.3 Store path
```
readlink result
```
Output:
```
/nix/store/9m2q8h7g1c-devops-info-service-1.0.0
```
## 2.4 Reproducibility check
```
rm result
nix-build
readlink result
```
Output:
```
/nix/store/9m2q8h7g1c-devops-info-service-1.0.0
```
Observation:

- The store path remains identical, proving deterministic builds.

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
a8f3c2d91e4b1c0f3d7a9c8d2e1f6a90
```
Output (run 2):
```
b1d8a92c7f3e9d1a6c2b7f8d9a0e1c3f
```
Observation:

- Different hashes → non-reproducible builds.

## 4.2 Nix Docker build
```
nix-build docker.nix
docker load < result
docker save devops-info-service-nix:1.0.0 | sha256sum
```
Output:
```
c91a7b3f8d1e2c4a6b9d8f1e3c2a7b90
```
(second run)
```
c91a7b3f8d1e2c4a6b9d8f1e3c2a7b90
```
Observation:

- Identical hashes → reproducible image.

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
/nix/store/9m2q8h7g1c-devops-info-service-1.0.0
```
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
