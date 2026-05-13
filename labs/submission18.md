# Lab 18 Documentation

## Task 1

### Installation steps and verification output

```bash
(devops) fountainer@Veronicas-MacBook-Air DevOps-Core-Course % curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
info: downloading the Determinate Nix Installer
 INFO nix-installer v3.20.0
`nix-installer` needs to run as `root`, attempting to escalate now via `sudo`...
Password:
 INFO nix-installer v3.20.0
 INFO For a more robust Nix installation, use the Determinate package for macOS: https://dtr.mn/determinate-nix
Nix install plan (v3.20.0)
Planner: macos (with default settings)

Planned actions:
* Install Determinate Nixd
* Create an encrypted APFS volume `Nix Store` for Nix on `disk3` and add it to `/etc/fstab` mounting on `/nix`
* Extract the bundled Nix (originally from /nix/store/4gf15cbjsjrhkv08aq4i8ndj0rhfdnl8-nix-binary-tarball-3.20.0/nix-3.20.0-aarch64-darwin.tar.xz) to `/nix/temp-install-dir`
* Create a directory tree in `/nix`
* Synchronize /nix and /nix/var ownership
* Move the downloaded Nix into `/nix`
* Synchronize /nix/store ownership
* Create build users (UID 351-382) and group (GID 350)
* Configure Time Machine exclusions
* Setup the default Nix profile
* Place the Nix configuration in `/etc/nix/nix.conf`
* Configure the shell profiles
* Configuring zsh to support using Nix in non-interactive shells
* Create a `launchctl` plist to put Nix into your PATH
* Configure the Determinate Nix daemon
* Remove directory `/nix/temp-install-dir`


Proceed? ([Y]es/[n]o/[e]xplain): 
 INFO Step: Install Determinate Nixd
 INFO Step: Create an encrypted APFS volume `Nix Store` for Nix on `disk3` and add it to `/etc/fstab` mounting on `/nix`
 INFO Step: Provision Nix
 INFO Step: Create build users (UID 351-382) and group (GID 350)
 INFO Step: Configure Time Machine exclusions
 INFO Step: Configure Nix
 INFO Step: Configuring zsh to support using Nix in non-interactive shells
 INFO Step: Create a `launchctl` plist to put Nix into your PATH
 INFO Step: Configure the Determinate Nix daemon
 INFO Step: Remove directory `/nix/temp-install-dir`
 INFO Running self test for shell sh
 INFO Running self test for shell bash
 INFO Running self test for shell zsh
Nix was installed successfully!
To get started using Nix, open a new shell or run `. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh`
```

```bash
fountainer@Veronicas-MacBook-Air DevOps-Core-Course % nix --version                            
nix (Determinate Nix 3.20.0) 2.34.6
fountainer@Veronicas-MacBook-Air DevOps-Core-Course % nix run nixpkgs#hello
Hello, world!
```

### Your default.nix file with explanations of each field

```bash
# import nix package repo by default if no specific parameter is provided
{ pkgs ? import <nixpkgs> {} }:

# this function is used to build a python app
pkgs.python3Packages.buildPythonApplication rec {
  # the name of the package
  pname = "devops-info-service";
  # package version
  version = "1.0.0";

  # source directory with code of the app
  src = ./.;

  # other since I don't use setup.py
  format = "other";

  # all dependencies (versions come from pinned nixpkgs, not from PyPy)
  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
    pytest
    python-json-logger
    python-dotenv
    prometheus-client
  ];

  nativeBuildInputs = [
    pkgs.makeWrapper # wraps script with interpreter
  ];

  # installation
  installPhase = ''
    mkdir -p $out/bin

    cp app.py $out/bin/devops-info-service

    # give execution permission
    chmod +x $out/bin/devops-info-service

    # wrap with interpreter
    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$PYTHONPATH"
  '';
}
```

### Store path from multiple builds (prove they're identical)

First try: Nix reused the cached build

```bash
(devops) fountainer@Veronicas-MacBook-Air app_python % readlink result
/nix/store/7aq0qmnzjaaghpzinv5s62g07jayl5jn-devops-info-service-1.0.0
(devops) fountainer@Veronicas-MacBook-Air app_python % rm result
(devops) fountainer@Veronicas-MacBook-Air app_python % nix-build
/nix/store/7aq0qmnzjaaghpzinv5s62g07jayl5jn-devops-info-service-1.0.0
(devops) fountainer@Veronicas-MacBook-Air app_python % readlink result
/nix/store/7aq0qmnzjaaghpzinv5s62g07jayl5jn-devops-info-service-1.0.0
```
Second try: actual rebuild

```bash
(devops) fountainer@Veronicas-MacBook-Air app_python % STORE_PATH=$(readlink result)
(devops) fountainer@Veronicas-MacBook-Air app_python % echo "Original store path: $STORE_PATH"

Original store path: /nix/store/7aq0qmnzjaaghpzinv5s62g07jayl5jn-devops-info-service-1.0.0
(devops) fountainer@Veronicas-MacBook-Air app_python % rm result
(devops) fountainer@Veronicas-MacBook-Air app_python % nix-store --delete $STORE_PATH
finding garbage collector roots...
removing stale link from "/nix/var/nix/gcroots/auto/rkjlx0in1jkwyq7m8ywjzlrimkwzf0gs" to "/Users/fountainer/uni/devops/DevOps-Core-Course/labs/lab18/app_python/result"
deleting '/nix/store/7aq0qmnzjaaghpzinv5s62g07jayl5jn-devops-info-service-1.0.0'
deleting unused links...
note: hard linking is currently saving 0.0 KiB
1 store paths deleted, 19.1 KiB freed
```
```bash
(devops) fountainer@Veronicas-MacBook-Air app_python % nix-build
this derivation will be built:
  /nix/store/fgndcrl1y90cjp22s2w14qj2zxgz0fb0-devops-info-service-1.0.0.drv
building '/nix/store/fgndcrl1y90cjp22s2w14qj2zxgz0fb0-devops-info-service-1.0.0.drv'...
Sourcing python-remove-tests-dir-hook
Sourcing python-catch-conflicts-hook.sh
Sourcing python-remove-bin-bytecode-hook.sh
Sourcing python-imports-check-hook.sh
Using pythonImportsCheckPhase
Sourcing python-namespaces-hook
Running phase: unpackPhase
unpacking source archive /nix/store/qyjjx88sw1n992jk2za4rf53b5jyp31g-app_python
source root is app_python
setting SOURCE_DATE_EPOCH to timestamp 315619200 of file "app_python/tests/test_home_endpoint.py"
Running phase: patchPhase
Running phase: updateAutotoolsGnuConfigScriptsPhase
Running phase: configurePhase
no configure script, doing nothing
Running phase: buildPhase
no Makefile or custom buildPhase, doing nothing
Running phase: installPhase
Running phase: fixupPhase
checking for references to /nix/var/nix/builds/nix-41337-2424879527/ in /nix/store/7aq0qmnzjaaghpzinv5s62g07jayl5jn-devops-info-service-1.0.0...
patching script interpreter paths in /nix/store/7aq0qmnzjaaghpzinv5s62g07jayl5jn-devops-info-service-1.0.0
/nix/store/7aq0qmnzjaaghpzinv5s62g07jayl5jn-devops-info-service-1.0.0/bin/.devops-info-service-wrapped: interpreter directive changed from "#!/usr/bin/env python3" to "/nix/store/kwnbzccaiqi6iwdchcy6xc8br4x9hn0j-python3-3.13.12/bin/python3"
stripping (with command strip and flags -S) in  /nix/store/7aq0qmnzjaaghpzinv5s62g07jayl5jn-devops-info-service-1.0.0/bin
Rewriting #! /nix/store/f700nj7wlwg441h39gkq29qbviy99sgq-bash-5.3p9/bin/bash -e to #!/nix/store/kwnbzccaiqi6iwdchcy6xc8br4x9hn0j-python3-3.13.12
Rewriting #!/nix/store/kwnbzccaiqi6iwdchcy6xc8br4x9hn0j-python3-3.13.12/bin/python3 to #!/nix/store/kwnbzccaiqi6iwdchcy6xc8br4x9hn0j-python3-3.13.12
wrapping `/nix/store/7aq0qmnzjaaghpzinv5s62g07jayl5jn-devops-info-service-1.0.0/bin/.devops-info-service-wrapped'...
Executing pythonRemoveTestsDir
Finished executing pythonRemoveTestsDir
Running phase: installCheckPhase
no Makefile or custom installCheckPhase, doing nothing
Running phase: pythonCatchConflictsPhase
Running phase: pythonRemoveBinBytecodePhase
Running phase: pythonImportsCheckPhase
Executing pythonImportsCheckPhase
Running phase: pytestcachePhase
Running phase: pytestRemoveBytecodePhase
/nix/store/7aq0qmnzjaaghpzinv5s62g07jayl5jn-devops-info-service-1.0.0
(devops) fountainer@Veronicas-MacBook-Air app_python % 
```

We got the same path!!!!

```bash
(devops) fountainer@Veronicas-MacBook-Air app_python % readlink result
/nix/store/7aq0qmnzjaaghpzinv5s62g07jayl5jn-devops-info-service-1.0.0
```

### Comparison table: pip install vs Nix derivation

```bash
(devops) fountainer@Veronicas-MacBook-Air app_python % echo "flask" > requirements-unpinned.txt
(devops) fountainer@Veronicas-MacBook-Air app_python % python -m venv venv1
(devops) fountainer@Veronicas-MacBook-Air app_python % source venv1/bin/activate
(venv1) fountainer@Veronicas-MacBook-Air app_python % pip install -r requirements-unpinned.txt
Collecting flask (from -r requirements-unpinned.txt (line 1))
  Using cached flask-3.1.3-py3-none-any.whl.metadata (3.2 kB)
Collecting blinker>=1.9.0 (from flask->-r requirements-unpinned.txt (line 1))
  Using cached blinker-1.9.0-py3-none-any.whl.metadata (1.6 kB)
Collecting click>=8.1.3 (from flask->-r requirements-unpinned.txt (line 1))
  Downloading click-8.3.3-py3-none-any.whl.metadata (2.6 kB)
Collecting itsdangerous>=2.2.0 (from flask->-r requirements-unpinned.txt (line 1))
  Using cached itsdangerous-2.2.0-py3-none-any.whl.metadata (1.9 kB)
Collecting jinja2>=3.1.2 (from flask->-r requirements-unpinned.txt (line 1))
  Using cached jinja2-3.1.6-py3-none-any.whl.metadata (2.9 kB)
Collecting markupsafe>=2.1.1 (from flask->-r requirements-unpinned.txt (line 1))
  Using cached markupsafe-3.0.3-cp311-cp311-macosx_11_0_arm64.whl.metadata (2.7 kB)
Collecting werkzeug>=3.1.0 (from flask->-r requirements-unpinned.txt (line 1))
  Downloading werkzeug-3.1.8-py3-none-any.whl.metadata (4.0 kB)
Using cached flask-3.1.3-py3-none-any.whl (103 kB)
Using cached blinker-1.9.0-py3-none-any.whl (8.5 kB)
Downloading click-8.3.3-py3-none-any.whl (110 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 110.5/110.5 kB 1.4 MB/s eta 0:00:00
Using cached itsdangerous-2.2.0-py3-none-any.whl (16 kB)
Using cached jinja2-3.1.6-py3-none-any.whl (134 kB)
Using cached markupsafe-3.0.3-cp311-cp311-macosx_11_0_arm64.whl (12 kB)
Downloading werkzeug-3.1.8-py3-none-any.whl (226 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 226.5/226.5 kB 4.1 MB/s eta 0:00:00
Installing collected packages: markupsafe, itsdangerous, click, blinker, werkzeug, jinja2, flask
Successfully installed blinker-1.9.0 click-8.3.3 flask-3.1.3 itsdangerous-2.2.0 jinja2-3.1.6 markupsafe-3.0.3 werkzeug-3.1.8

[notice] A new release of pip is available: 24.0 -> 26.1.1
[notice] To update, run: pip install --upgrade pip
(venv1) fountainer@Veronicas-MacBook-Air app_python % pip freeze | grep -i flask > freeze1.txt
(venv1) fountainer@Veronicas-MacBook-Air app_python % deactivate
```

```bash
(devops) fountainer@Veronicas-MacBook-Air app_python % pip cache purge 2>/dev/null || rm -rf ~/.cache/pip
```

```bash
(devops) fountainer@Veronicas-MacBook-Air app_python % python -m venv venv2
(devops) fountainer@Veronicas-MacBook-Air app_python % source venv2/bin/activate
(venv2) fountainer@Veronicas-MacBook-Air app_python % pip install -r requirements-unpinned.txt
Collecting flask (from -r requirements-unpinned.txt (line 1))
  Using cached flask-3.1.3-py3-none-any.whl.metadata (3.2 kB)
Collecting blinker>=1.9.0 (from flask->-r requirements-unpinned.txt (line 1))
  Using cached blinker-1.9.0-py3-none-any.whl.metadata (1.6 kB)
Collecting click>=8.1.3 (from flask->-r requirements-unpinned.txt (line 1))
  Using cached click-8.3.3-py3-none-any.whl.metadata (2.6 kB)
Collecting itsdangerous>=2.2.0 (from flask->-r requirements-unpinned.txt (line 1))
  Using cached itsdangerous-2.2.0-py3-none-any.whl.metadata (1.9 kB)
Collecting jinja2>=3.1.2 (from flask->-r requirements-unpinned.txt (line 1))
  Using cached jinja2-3.1.6-py3-none-any.whl.metadata (2.9 kB)
Collecting markupsafe>=2.1.1 (from flask->-r requirements-unpinned.txt (line 1))
  Using cached markupsafe-3.0.3-cp311-cp311-macosx_11_0_arm64.whl.metadata (2.7 kB)
Collecting werkzeug>=3.1.0 (from flask->-r requirements-unpinned.txt (line 1))
  Using cached werkzeug-3.1.8-py3-none-any.whl.metadata (4.0 kB)
Using cached flask-3.1.3-py3-none-any.whl (103 kB)
Using cached blinker-1.9.0-py3-none-any.whl (8.5 kB)
Using cached click-8.3.3-py3-none-any.whl (110 kB)
Using cached itsdangerous-2.2.0-py3-none-any.whl (16 kB)
Using cached jinja2-3.1.6-py3-none-any.whl (134 kB)
Using cached markupsafe-3.0.3-cp311-cp311-macosx_11_0_arm64.whl (12 kB)
Using cached werkzeug-3.1.8-py3-none-any.whl (226 kB)
Installing collected packages: markupsafe, itsdangerous, click, blinker, werkzeug, jinja2, flask
Successfully installed blinker-1.9.0 click-8.3.3 flask-3.1.3 itsdangerous-2.2.0 jinja2-3.1.6 markupsafe-3.0.3 werkzeug-3.1.8

[notice] A new release of pip is available: 24.0 -> 26.1.1
[notice] To update, run: pip install --upgrade pip
(venv2) fountainer@Veronicas-MacBook-Air app_python % pip freeze | grep -i flask > freeze2.txt
(venv2) fountainer@Veronicas-MacBook-Air app_python % deactivate
```

```bash
(devops) fountainer@Veronicas-MacBook-Air app_python % diff freeze1.txt freeze2.txt
(devops) fountainer@Veronicas-MacBook-Air app_python % 
```

We have no difference, but it is only because the tests were executed very close in time. If a lot of time passes, without the pinned version, pip will install the newest version available in PyPy. Also, all underlying packages in the tree (dependencies of the main dependency) can differ.

```bash
(devops) fountainer@Veronicas-MacBook-Air app_python % nix-hash --type sha256 result
da81bf46dac8fc2785d20d7d448f172ea8a2b78bf0a52447b3bdd9de022ca50f
```
On the other hand, Nix caches the entire envirinment: source code, dependency trees, build instructions, etc. Therfore, each machine will be able to reproduce this environment entirely.

Summary from the lab:

| Aspect | Lab 1 (pip + venv) | Lab 18 (Nix) |
|--------|-------------------|--------------|
| Python version | System-dependent | Pinned in derivation |
| Dependency resolution | Runtime (`pip install`) | Build-time (pure) |
| Reproducibility | Approximate (with lockfiles) | Bit-for-bit identical |
| Portability | Requires same OS + Python | Works anywhere Nix runs |
| Binary cache | No | Yes (cache.nixos.org) |
| Isolation | Virtual environment | Sandboxed build |
| Store path | N/A | Content-addressable hash |

### Why does requirements.txt provide weaker guarantees than Nix?

Because requirements.txt contain packages versions that can diverge with time. If they are not pinned, a newer build will just use the latest version, and even if pinned, some sub-dependencies of actual dependencies we declare can change as well. The environment will not be identical and, therefore, not fully reproducable. 

### Screenshot showing your Lab 1 app running from Nix-built version

![](./lab18/app_python/docs/screenshots/lab18-shots/app%20running.png)

### Explanation of the Nix store path format and what each part means

Nix store path is a reference to store object, a unique identifier. 

The format (example with my path):

```bash
/nix/store/7aq0qmnzjaaghpzinv5s62g07jayl5jn-devops-info-service-1.0.0

/nix/store: # store directory, it is a directory for Nix store on the local filesystems. 

7aq0qmnzjaaghpzinv5s62g07jayl5jn: # digest, for identification, it is a cache computed
# from all env info: source code, dependencies trees, build instructions, etc

- # hyphen for separation

devops-info-service-1.0.0: # human-readable name (+ version)
```

### Reflection: How would Nix have helped in Lab 1 if you had used it from the start?

Throughout the labs, I rebuilt the image a looot of times, so many dependencies could have changed. If I used Nix, I would get a more reproducable environment. At the same time, I don't feel that it is really important for this exact project since it runs on one machine and has few dependencies.

## Task 2

### Your docker.nix file with explanations of each field

### Side-by-side comparison: Lab 2 Dockerfile vs Nix docker.nix

### SHA256 hash comparison proving Nix reproducibility

### Image size comparison table with analysis

### docker history output for both approaches

### Screenshots showing both containers running simultaneously

### Analysis: Why can't traditional Dockerfiles achieve bit-for-bit reproducibility?

### Reflection: If you could redo Lab 2 with Nix, what would you do differently?

### Practical scenarios where Nix's reproducibility matters (CI/CD, security audits, rollbacks)