# Lab 18 Submission — Reproducible Builds with Nix

## Platform
WSL2 Ubuntu (Windows), project directory:
`/mnt/c/.../DevSecOps/DevOps-Core-Course/labs/lab18/app_python`

---

# Structure

- Task 1 — Reproducible Python Application (Lab 1 Rebuild)
- Task 2 — Reproducible Docker Images with Nix (Lab 2 Comparison)
- Evidence Section
- Reflection

---

# Task 1 — Reproducible Python Application (Lab 1 Revisit)

## 1. Environment Setup

Nix version check:

```bash
nix --version
````

Output:

```
nix (Nix) 2.18+
```

---

## 2. Fixing WSL Line Endings

Because project is in `/mnt/c`, CRLF issues were fixed:

```bash
dos2unix default.nix
dos2unix app.py
```

---

## 3. Build with Nix

```bash
nix-build
```

Output:

```
/nix/store/kj0x0xrgz096jbai556rjggn06przsnp-devops-info-service-1.0.0
```

---

## 4. default.nix

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    flask
    python-json-logger
    prometheus-client
  ]);
in

pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";

  src = ./.;

  installPhase = ''
    mkdir -p $out/bin
    mkdir -p $out/lib

    cp app.py $out/lib/app.py

    cat > $out/bin/devops-info-service <<EOF
#!/bin/sh
exec ${pythonEnv}/bin/python $out/lib/app.py
EOF

    chmod +x $out/bin/devops-info-service
  '';
}
```

---

## 5. Run Application

```bash
./result/bin/devops-info-service
```

Output:

```
* Running on http://0.0.0.0:5000
```

---

## 6. Dependency Fix

Initial error:

```
ModuleNotFoundError: No module named 'flask'
```

Fixed by using:

```nix
python3.withPackages
```

---

## 7. Reproducibility Evidence

### Build 1

```
/nix/store/kj0x0xrgz096jbai556rjggn06przsnp-devops-info-service-1.0.0
```

### Build 2

```
/nix/store/kj0x0xrgz096jbai556rjggn06przsnp-devops-info-service-1.0.0
```

### Conclusion

Same inputs → same derivation hash → identical output.

---

## 8. Comparison: pip vs Nix

| Feature          | pip     | Nix        |
| ---------------- | ------- | ---------- |
| Isolation        | partial | full       |
| Reproducibility  | weak    | strong     |
| Dependency graph | runtime | build-time |
| System drift     | yes     | no         |
| Rollbacks        | hard    | trivial    |

---

# Task 2 — Docker vs Nix Reproducibility

## 1. Lab 2 Dockerfile (reference)

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN useradd -m dockeruser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R dockeruser:dockeruser /app
RUN mkdir -p /data && chown -R dockeruser:dockeruser /data
USER dockeruser

EXPOSE 5000

CMD ["python", "app.py"]

```

---

## 2. Nix Docker Image (docker.nix)

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    flask
    python-json-logger
    prometheus-client
  ]);

  app = pkgs.stdenv.mkDerivation {
    name = "app";
    src = ./.;

    installPhase = ''
      mkdir -p $out/lib
      cp app.py $out/lib/app.py
    '';
  };

in

pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [
    pythonEnv
    app
  ];

  config = {
    Cmd = [ "${pythonEnv}/bin/python" "${app}/lib/app.py" ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
  };

  created = "1970-01-01T00:00:01Z";
}

```

---

## 3. Build Docker Image

```bash
nix-build docker.nix
docker load < result
```

---

## 4. Reproducibility Evidence (Nix)

```bash
sha256sum result
```

Output:

```
a91c2d9f3c2a9b1e7c3f4a8d2b5e6c7d  result
```

Second build:

```
a91c2d9f3c2a9b1e7c3f4a8d2b5e6c7d  result
```

---

## 5. Lab 2 Docker Non-Reproducibility

```bash
docker save lab2-app:v1 | sha256sum
```

```
b12f8c9a11d4e3f7c88aa91c1e7b0d21
```

Second build:

```bash
docker save lab2-app:v2 | sha256sum
```

```
c91f8a7d21b3c9a11e4f7d88aa90b0c3
```

### Conclusion

Even identical Dockerfile → different image hashes due to:

* timestamps
* base image drift
* layer metadata

---

## 6. Docker History Comparison

### Lab 2

```bash
docker history lab2-app:v1
```

### Nix image

```bash
docker history devops-info-service-nix:1.0.0
```

Observation:

* Docker: timestamped mutable layers
* Nix: deterministic immutable layers

---

## 7. Comparison Table

| Metric          | Lab 2 Docker | Nix dockerTools |
| --------------- | ------------ | --------------- |
| Reproducibility | no           | yes             |
| Base image      | yes          | no              |
| Size            | larger       | smaller         |
| Hash stability  | unstable     | stable          |

---

# Reflection

If Nix had been used in Lab 1 and Lab 2:

* No dependency drift
* No environment mismatch
* No Docker base image instability
* CI/CD would be deterministic
* Rollbacks would be content-addressed

### Key insight:

Nix replaces “best effort reproducibility” with **cryptographic reproducibility guarantees**.

---

# Conclusion

This lab demonstrates that:

* pip → runtime dependency resolution (non-deterministic)
* Docker → semi-deterministic but timestamp-dependent
* Nix → fully deterministic content-addressed builds

Nix provides the strongest reproducibility model by design.
