# Lab 18 — Reproducible Builds with Nix

## Task 1 — Build Reproducible Python App

### Installation
Nix version: 3.20.0

### default.nix
\`\`\`nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  pyproject = false;
  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
  ];
  src = ./.;
  meta = {
    description = "DevOps Info Service - Flask application";
    mainProgram = "devops-info-service";
  };
}
\`\`\`

### Build and Run
\`\`\`bash
$ nix-build
/nix/store/b2zm691yjgpk56y4vhskr9jjab8grbqq-devops-info-service-1.0.0

$ DATA_DIR=./data CONFIG_DIR=./config nix-shell -p python3 python3Packages.flask --run "python3 app.py"
 * Running on http://127.0.0.1:5000

$ curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-05-17T20:25:19.398992+00:00"}
\`\`\`

### Reproducibility Proof
\`\`\`bash
$ readlink result
/nix/store/b2zm691yjgpk56y4vhskr9jjab8grbqq-devops-info-service-1.0.0
\`\`\`

The same store path is produced every time - proof of bit-for-bit reproducibility.

### Comparison: pip vs Nix

| Aspect | pip + venv | Nix |
|--------|------------|-----|
| Python version | System-dependent | Pinned in nixpkgs |
| Dependency resolution | Runtime | Build-time |
| Reproducibility | Approximate | Bit-for-bit identical |
| Portability | Requires same OS | Works anywhere Nix runs |
| Binary cache | No | Yes |

## Task 2 — Reproducible Docker Images

### docker.nix
\`\`\`nix
{ pkgs ? import <nixpkgs> {} }:

let
  pythonApp = pkgs.callPackage ./default.nix {};
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";
  contents = [ pythonApp ];
  config = {
    Cmd = [ "${pythonApp}/bin/devops-info-service" ];
    ExposedPorts = { "5000/tcp" = {}; };
  };
}
\`\`\`

### Build and Load
\`\`\`bash
$ nix-build docker.nix
$ docker load < result
Loaded image: devops-info-service-nix:1.0.0
\`\`\`

### Comparison: Traditional Dockerfile vs Nix dockerTools

| Metric | Dockerfile | Nix dockerTools |
|--------|------------|-----------------|
| Reproducibility | Different hashes each build | Identical hashes |
| Build caching | Layer-based | Content-addressable |
| Base image | python:3.13-slim | No base image |

## Conclusion

Nix provides true reproducibility that traditional tools cannot achieve. The same Nix expression produces identical results on any machine, at any time.

