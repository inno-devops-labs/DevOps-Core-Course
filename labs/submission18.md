# Submission 18 — Reproducible Builds with Nix

## 0) Environment

```bash
$ nix --version
nix (Nix) 2.34.6
```

## 1) Task 1 — Reproducible Python app build with Nix

### Nix derivation (`labs/lab18/app_python/default.nix`)

```nix
{ pkgs ? import <nixpkgs> {} }:
let
  lib = pkgs.lib;
  pythonEnv = pkgs.python313.withPackages (ps: with ps; [
    blinker
    click
    flask
    itsdangerous
    jinja2
    markupsafe
    werkzeug
  ]);
  srcClean = lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let
        relPath = lib.removePrefix (toString ./. + "/") (toString path);
      in
        # Exclude runtime / local artifacts that can change between runs
        !(relPath == "data/visits"
          || lib.hasPrefix "result" relPath
          || lib.hasPrefix "venv1" relPath
          || lib.hasPrefix "venv2" relPath
          || lib.hasPrefix ".venv" relPath
          || lib.hasPrefix "__pycache__" relPath
          || lib.hasPrefix ".pytest_cache" relPath);
  };
in pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0";

  src = srcClean;

  nativeBuildInputs = [pkgs.makeWrapper];

  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/.devops-info-service

    makeWrapper ${pythonEnv}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/bin/.devops-info-service" \
  '';
}
```

### Build + reproducibility evidence (store path)

Built twice from `labs/lab18/app_python/` and compared the resulting store path (via `readlink result`).

```bash
$ rm -f result
$ nix-build && readlink result
this derivation will be built:
  /nix/store/9v428rffi0mgva1pa1r1sswz7dmi1xqr-devops-info-service-1.0.drv
building '/nix/store/9v428rffi0mgva1pa1r1sswz7dmi1xqr-devops-info-service-1.0.drv'...
...
/nix/store/chkzlk5da6nbrwgy5nyc9l8gy109p52l-devops-info-service-1.0
/nix/store/chkzlk5da6nbrwgy5nyc9l8gy109p52l-devops-info-service-1.0

$ rm -f result
$ nix-build && readlink result
/nix/store/chkzlk5da6nbrwgy5nyc9l8gy109p52l-devops-info-service-1.0
/nix/store/chkzlk5da6nbrwgy5nyc9l8gy109p52l-devops-info-service-1.0
```

### Note on why this matters

Reproducibility depends on the **entire derivation input** being stable. A mutable runtime state file like `data/visits` can change between builds and would change the derivation hash. To keep builds stable, the derivation uses `cleanSourceWith` to exclude `data/visits` (and other local build artifacts like `result/` and virtual env folders).

## 2) Task 1 — Comparison vs pip (limitations)

### Pinned requirements

```text
blinker==1.9.0
click==8.3.1
Flask==3.1.2
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.3
Werkzeug==3.1.5
```

### Unpinned demo input + freezes

`requirements-unpinned.txt`:

```text
flask # No version specified
```

`freeze1.txt`:

```text
Flask==3.1.3
```

`freeze2.txt`:

```text
Flask==3.1.3
```

### Explanation (why pip is weaker than Nix)

- `pip` (even with pinned direct dependencies) doesn’t cryptographically pin the **entire transitive dependency tree** and the **toolchain** in a single content-addressed output the way Nix does.
- With unpinned requirements, you can get whatever is newest at install time. Even with pins, other factors (index state, wheels vs source builds, platform-specific dependencies) can cause drift.
- Nix computes the output path from all declared inputs and build instructions; same inputs produce the same store path and can be shared/cached safely.

#### Note about my run

In my run, `freeze1.txt` and `freeze2.txt` ended up identical (`Flask==3.1.3`). This can happen if PyPI served the same version both times (no new release in between), or if caches/index state did not change enough to show drift on that day.

## 3) Task 2 — Reproducible Docker image with Nix `dockerTools`

### Nix Docker image definition (`labs/lab18/app_python/docker.nix`)

```nix
{ pkgs ? import <nixpkgs> {} }:
let app = import ./default.nix { inherit pkgs; }; in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [app];

  config = {
    ExposedPorts = {
      "5000/tcp" = {};
    };
    Cmd = ["${app}/bin/devops-info-service"];
  };
  created = "1970-01-01T00:00:01Z";  # Reproducible timestamp
}
```

### Bit-for-bit reproducibility proof (tarball SHA256)

Built the image twice and hashed the resulting tarball (`result`). Hashes match:

```bash
$ rm -f result
$ nix-build docker.nix && sha256sum result
...
/nix/store/nsb4l1jiyriahs6741rnxx796pfvzibj-devops-info-service-nix.tar.gz
456387808e4ed304b1936f1058507cf5860e4f06f3db362ce2f807cd4a29899e  result

$ rm -f result
$ nix-build docker.nix && sha256sum result
...
/nix/store/nsb4l1jiyriahs6741rnxx796pfvzibj-devops-info-service-nix.tar.gz
456387808e4ed304b1936f1058507cf5860e4f06f3db362ce2f807cd4a29899e  result
```

### Runtime evidence (Docker)

```bash
# Load the tarball into Docker
docker load < result

# Run on host port 5001 (container listens on 5000 by default)
docker run --rm -p 5001:5000 devops-info-service-nix:1.0.0

# In another terminal
curl http://localhost:5001/health
```

If your app is configured to listen on a different port, run with:

```bash
docker run --rm -e PORT=5000 -p 5001:5000 devops-info-service-nix:1.0.0
```

## 4) Bonus — Flakes (implemented)

Flake exists in `labs/lab18/app_python/flake.nix` and pins inputs via `flake.lock`.

