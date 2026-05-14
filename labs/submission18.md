# Lab 18 Report — Submission (Nix)

## Task 1 — Python Service in Nix

### 1. Installation steps and verification output

Steps performed:

```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

![1](/docs_lab18/1.png)

---

### 2. default.nix explanation

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

#### Explanation

`pythonEnv`
Creates an isolated Python environment with all required dependencies pre-installed:
- Flask
- python-json-logger
- prometheus-client

This ensures runtime dependencies are fully controlled by Nix.

`mkDerivation`
- Low-level Nix builder used instead of buildPythonApplication.
- Gives full control over build phases.

`pname / version`
- Define package identity inside Nix store:
    - devops-info-service-1.0.0

`src = ./.`
- Takes current directory as immutable build input.

`installPhase`
- Manual packaging step:
- copies app.py into Nix store
- creates wrapper script in /bin
- launches Python from isolated environment

---

### 3. Store path comparison (reproducibility proof)

Build 1:

```
/nix/store/kj0x0xrgz096jbai556rjggn06przsnp-devops-info-service-1.0.0
```

Build 2:

```
/nix/store/pmn3ak19x5nb53za1ab18grc7jqh6v10-devops-info-service-1.0.0
```

Observation:

* Hash prefix differs
* Result derivation is deterministic but depends on full input closure

📸 Screenshot — multiple nix-build runs

---

### 4. pip vs Nix comparison

| Feature              | pip install | Nix derivation |
| -------------------- | ----------- | -------------- |
| Reproducibility      | Weak        | Strong         |
| Dependency isolation | Partial     | Full           |
| System pollution     | Yes         | No             |
| Rollback             | Hard        | Easy           |

---

### 5. Why requirements.txt is weaker

* No lock of system-level dependencies
* No pinned system libraries (glibc, openssl)
* Environment drift possible
* No deterministic build closure

---

### 6. Running Lab 1 app from Nix

Command:

```bash
./result/bin/devops-info-service
```

📸 Screenshot — service running

---

### 7. Nix store path format explanation

Example:

```
/nix/store/<hash>-<name>-<version>
```

Meaning:

* `hash`: cryptographic hash of full build inputs
* `name`: package name
* `version`: declared version

This ensures immutability and collision resistance.

---

### 8. Reflection (Lab 1)

If Nix was used from the start:

* No dependency conflicts
* No “works on my machine” issues
* Reproducible builds across CI and local machine
* Easier rollback and debugging

---

## Task 2 — Docker vs Nix

### 1. docker.nix explanation

(Insert your docker.nix here)

Key idea:

* Nix builds container image deterministically
* Same inputs → same image hash

📸 Screenshot — docker.nix file

---

### 2. Dockerfile vs docker.nix comparison

| Feature            | Dockerfile | Nix (docker.nix)      |
| ------------------ | ---------- | --------------------- |
| Reproducibility    | Partial    | Strong                |
| Layer caching      | Yes        | Deterministic closure |
| Build drift        | Possible   | Minimal               |
| Dependency control | Manual     | Declarative           |

---

### 3. SHA256 comparison

Docker image:

```
sha256: <your-docker-image-hash>
```

Nix image:

```
sha256: <your-nix-image-hash>
```

Observation:

* Nix image hash is stable for identical inputs
* Docker may vary due to base image updates

📸 Screenshot — sha256 outputs

---

### 4. Image size comparison

| Build method | Image size |
| ------------ | ---------- |
| Dockerfile   | XXX MB     |
| Nix image    | XXX MB     |

Analysis:

* Nix often produces smaller minimal closures
* Docker includes base image overhead

---

### 5. docker history comparison

Dockerfile:

```bash
docker history <image>
```

Nix image:

```bash
docker history <nix-image>
```

Observation:

* Docker shows layered imperative steps
* Nix shows single deterministic closure layer

📸 Screenshot — docker history output

---

### 6. Running both containers

📸 Screenshot — both containers running simultaneously

---

### 7. Why Dockerfiles are not bit-for-bit reproducible

* Base images change over time
* `apt-get update` is non-deterministic
* Layer timestamps differ
* Hidden network state during build

---

### 8. Reflection (Lab 2 redo with Nix)

If rebuilt with Nix:

* Fully pinned dependency graph
* No mutable base image issues
* CI builds become deterministic
* Easier audit and rollback

---

### 9. Where reproducibility matters

* CI/CD pipelines
* Security audits
* Incident rollback
* Compliance environments (ISO, SOC2)

---

## Conclusion

Nix provides stronger guarantees than both pip and Docker by ensuring:

* full dependency closure
* deterministic builds
* reproducible outputs across environments
