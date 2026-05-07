# Lab 18 — Reproducible Builds with Nix

## Task 1

### 1.1: Install Nix Package Manager

```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/edge-api$ curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
info: downloading the Determinate Nix Installer
 INFO nix-installer v3.19.1
`nix-installer` needs to run as `root`, attempting to escalate now via `sudo`...
 INFO nix-installer v3.19.1
Nix install plan (v3.19.1)
Planner: linux (with default settings)

Planned actions:
* Create directory `/nix`
* Install Determinate Nixd
* Extract the bundled Nix (originally from /nix/store/phhf0y76rhrh6c5wa95agsznxjwgabh4-nix-binary-tarball-3.19.1/nix-3.19.1-x86_64-linux.tar.xz) to `/nix/temp-install-dir`
* Create a directory tree in `/nix`
* Synchronize /nix and /nix/var ownership
* Move the downloaded Nix into `/nix`
* Synchronize /nix/store ownership
* Create build users (UID 30001-30032) and group (GID 30000)
* Setup the default Nix profile
* Place the Nix configuration in `/etc/nix/nix.conf`
* Configure the shell profiles
* Configure the Determinate Nix daemon
* Cleanup


Proceed? ([Y]es/[n]o/[e]xplain): y
 INFO Step: Create directory `/nix`
 INFO Step: Install Determinate Nixd
 INFO Step: Provision Nix
 INFO Step: Create build users (UID 30001-30032) and group (GID 30000)
 INFO Step: Configure Nix
 INFO Step: Create directory `/etc/tmpfiles.d`
 INFO Step: Configure the Determinate Nix daemon
 INFO Step: Cleanup
 INFO Running self test for shell sh
 INFO Running self test for shell bash
Nix was installed successfully!
To get started using Nix, open a new shell or run `. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh`

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/edge-api$ nix --version
nix (Determinate Nix 3.19.1) 2.34.6

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/edge-api$ nix run nixpkgs#hello
warning: unable to download 'https://install.determinate.systems/flake-registry/stable/flake-registry.json': Timeout was reached (28) Connection timed out after 15002 milliseconds; retrying in 252 ms (attempt 1/5)
Hello, world!
```

### 1.2: Prepare Your Python Application

```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/edge-api$ cd ..

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ mkdir -p app_python_lab18

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ cp app_python/app.py app_python_lab18/app.py

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ cp app_python/requirements.txt app_python_lab18/requirements.txt

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ cd app_python_lab18/

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ ls
app.py  requirements.txt
```

### 1.3: Write a Nix Derivation for Your Python App

`default.nix`:
```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.python312Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;
  format = "other";

  propagatedBuildInputs = with pkgs.python312Packages; [
    flask
    prometheus-client
    portalocker
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

| Field | Meaning |
|---|---|
| `python312Packages.buildPythonApplication` | Build the app using Nix-managed Python 3.12 dependency set. |
| `pname` / `version` | Package identity that using in store path name. |
| `src = ./.` | Src of the app that will be used |
| `format = "other"` | Application have other default format |
| `propagatedBuildInputs` | Python dependencies: Flask, Prometheus client and portalocker. |
| `makeWrapper` | Creates a runnable `devops-info-service` command that invokes the pinned Python interpreter. |
| `installPhase` | Commands to install the app |


Build:
```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ nix-build
this derivation will be built:
  /nix/store/v9yx6arg5nkkycc7n2s2g7j5gmw13sbw-devops-info-service-1.0.0.drv
building '/nix/store/v9yx6arg5nkkycc7n2s2g7j5gmw13sbw-devops-info-service-1.0.0.drv'...
Sourcing python-remove-tests-dir-hook
Sourcing python-catch-conflicts-hook.sh
Sourcing python-remove-bin-bytecode-hook.sh
Sourcing python-imports-check-hook.sh
Using pythonImportsCheckPhase
Sourcing python-namespaces-hook
Running phase: unpackPhase
unpacking source archive /nix/store/f1fyrc0rvy26pha4s6hd59al6xp316j3-app_python_lab18
source root is app_python_lab18
setting SOURCE_DATE_EPOCH to timestamp 315619200 of file "app_python_lab18/requirements.txt"
Running phase: patchPhase
Running phase: updateAutotoolsGnuConfigScriptsPhase
Running phase: configurePhase
no configure script, doing nothing
Running phase: buildPhase
no Makefile or custom buildPhase, doing nothing
Running phase: installPhase
Running phase: fixupPhase
shrinking RPATHs of ELF executables and libraries in /nix/store/mfn36cykawy8r5w3rq1zd1vz2icfn4ai-devops-info-service-1.0.0
checking for references to /build/ in /nix/store/mfn36cykawy8r5w3rq1zd1vz2icfn4ai-devops-info-service-1.0.0...
patching script interpreter paths in /nix/store/mfn36cykawy8r5w3rq1zd1vz2icfn4ai-devops-info-service-1.0.0
/nix/store/mfn36cykawy8r5w3rq1zd1vz2icfn4ai-devops-info-service-1.0.0/bin/.devops-info-service-wrapped: interpreter directive changed from "#!/usr/bin/env python3" to "/nix/store/h3q2g9wq4x3q84164qsfm3lz5djj0bf3-python3-3.12.13/bin/python3"
stripping (with command strip and flags -S -p) in  /nix/store/mfn36cykawy8r5w3rq1zd1vz2icfn4ai-devops-info-service-1.0.0/bin
Rewriting #!/nix/store/h3q2g9wq4x3q84164qsfm3lz5djj0bf3-python3-3.12.13/bin/python3 to #!/nix/store/h3q2g9wq4x3q84164qsfm3lz5djj0bf3-python3-3.12.13
wrapping `/nix/store/mfn36cykawy8r5w3rq1zd1vz2icfn4ai-devops-info-service-1.0.0/bin/.devops-info-service-wrapped'...
Rewriting #! /nix/store/i27rhb3nr65rkrwz36bchkwmav6ggsmn-bash-5.3p9/bin/bash -e to #!/nix/store/h3q2g9wq4x3q84164qsfm3lz5djj0bf3-python3-3.12.13
Executing pythonRemoveTestsDir
Finished executing pythonRemoveTestsDir
Running phase: pythonCatchConflictsPhase
Running phase: pythonRemoveBinBytecodePhase
Running phase: pythonImportsCheckPhase
Executing pythonImportsCheckPhase
/nix/store/mfn36cykawy8r5w3rq1zd1vz2icfn4ai-devops-info-service-1.0.0


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ ./result/bin/devops-info-service
 * Serving Flask app '..devops-info-service-wrapped-wrapped'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://172.18.3.124:5000
Press CTRL+C to quit
127.0.0.1 - - [07/May/2026 13:20:53] "GET / HTTP/1.1" 200 -
{"timestamp": "2026-05-07T10:20:53.704129+00:00", "level": "WARNING", "message": "Not found", "logger": "devops-info-service", "function": "not_found", "line": 209, "path": "/favicon.ico", "client_addr": "127.0.0.1"}
127.0.0.1 - - [07/May/2026 13:20:53] "GET /favicon.ico HTTP/1.1" 404 -
```

Visit `http://localhost:5000`:
```json
{
  "endpoints": [
    {
      "description": "Service information",
      "method": "GET",
      "path": "/"
    },
    {
      "description": "Health check",
      "method": "GET",
      "path": "/health"
    },
    {
      "description": "Endpoint that raises an error for testing",
      "method": "GET",
      "path": "/raise-error"
    },
    {
      "description": "Metrics endpoint",
      "method": "GET",
      "path": "/metrics"
    },
    {
      "description": "Visits endpoint",
      "method": "GET",
      "path": "/visits"
    }
  ],
  "request": {
    "client_ip": "127.0.0.1",
    "method": "GET",
    "path": "/",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
  },
  "runtime": {
    "current_time": "2026-05-07T10:20:53.253418+00:00",
    "timezone": "UTC",
    "uptime_human": "0.0h 0.0m",
    "uptime_seconds": 3.866281
  },
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "x86_64",
    "cpu_count": 12,
    "hostname": "chale",
    "platform": "Linux",
    "platform_version": "#1 SMP Tue Nov 5 00:21:55 UTC 2024",
    "python_version": "3.12.13"
  }
}
```

### Prove Reproducibility (Compare with Lab 1 approach)

Record the Nix store path:
```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ readlink result
/nix/store/xq34yn50cdxdmflgy6bmmh8d7v8fckpb-devops-info-service-1.0.0
```

Build again and compare:
```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ rm result
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ nix-build
/nix/store/xq34yn50cdxdmflgy6bmmh8d7v8fckpb-devops-info-service-1.0.0
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ readlink result
/nix/store/xq34yn50cdxdmflgy6bmmh8d7v8fckpb-devops-info-service-1.0.0
```

Force an actual rebuild to prove reproducibility:
```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ STORE_PATH=$(readlink result)
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ echo "Original store path: $STORE_PATH"
Original store path: /nix/store/xq34yn50cdxdmflgy6bmmh8d7v8fckpb-devops-info-service-1.0.0
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ nix-store --delete $STORE_PATH
finding garbage collector roots...
removing stale temporary roots file "/nix/var/nix/temproots/11059"
removing stale temporary roots file "/nix/var/nix/temproots/11057"
removing stale temporary roots file "/nix/var/nix/temproots/10541"
removing stale temporary roots file "/nix/var/nix/temproots/10799"
removing stale temporary roots file "/nix/var/nix/temproots/10801"
removing stale temporary roots file "/nix/var/nix/temproots/10543"
removing stale temporary roots file "/nix/var/nix/temproots/10958"
removing stale temporary roots file "/nix/var/nix/temproots/10287"
removing stale temporary roots file "/nix/var/nix/temproots/10960"
removing stale temporary roots file "/nix/var/nix/temproots/10289"
removing stale temporary roots file "/nix/var/nix/temproots/11106"
removing stale temporary roots file "/nix/var/nix/temproots/11104"
0 store paths deleted, 0.0 KiB freed
error: Cannot delete path '/nix/store/xq34yn50cdxdmflgy6bmmh8d7v8fckpb-devops-info-service-1.0.0' because it's referenced by the GC root '/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18/result'.
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ rm result
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ nix-store --delete $STORE_PATH
finding garbage collector roots...
removing stale link from "/nix/var/nix/gcroots/auto/3rcxl2mbx2ar85vrmsypn2s8zslmd3gy" to "/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18/result"
deleting '/nix/store/xq34yn50cdxdmflgy6bmmh8d7v8fckpb-devops-info-service-1.0.0'
deleting unused links...
note: hard linking is currently saving -4.0 KiB
1 store paths deleted, 14.5 KiB freed
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ nix-build
this derivation will be built:
  /nix/store/qcpgc9iqb28mc2jb063vyddyhpbvw9ll-devops-info-service-1.0.0.drv
building '/nix/store/qcpgc9iqb28mc2jb063vyddyhpbvw9ll-devops-info-service-1.0.0.drv'...
Sourcing python-remove-tests-dir-hook
Sourcing python-catch-conflicts-hook.sh
Sourcing python-remove-bin-bytecode-hook.sh
Sourcing python-imports-check-hook.sh
Using pythonImportsCheckPhase
Sourcing python-namespaces-hook
Running phase: unpackPhase
unpacking source archive /nix/store/y50dk55c2pmb8n3iawbdpaq8d6dpi1sc-app_python_lab18
source root is app_python_lab18
setting SOURCE_DATE_EPOCH to timestamp 315619200 of file "app_python_lab18/requirements.txt"
Running phase: patchPhase
Running phase: updateAutotoolsGnuConfigScriptsPhase
Running phase: configurePhase
no configure script, doing nothing
Running phase: buildPhase
no Makefile or custom buildPhase, doing nothing
Running phase: installPhase
Running phase: fixupPhase
shrinking RPATHs of ELF executables and libraries in /nix/store/xq34yn50cdxdmflgy6bmmh8d7v8fckpb-devops-info-service-1.0.0
checking for references to /build/ in /nix/store/xq34yn50cdxdmflgy6bmmh8d7v8fckpb-devops-info-service-1.0.0...
patching script interpreter paths in /nix/store/xq34yn50cdxdmflgy6bmmh8d7v8fckpb-devops-info-service-1.0.0
/nix/store/xq34yn50cdxdmflgy6bmmh8d7v8fckpb-devops-info-service-1.0.0/bin/.devops-info-service-wrapped: interpreter directive changed from "#!/usr/bin/env python3" to "/nix/store/h3q2g9wq4x3q84164qsfm3lz5djj0bf3-python3-3.12.13/bin/python3"
stripping (with command strip and flags -S -p) in  /nix/store/xq34yn50cdxdmflgy6bmmh8d7v8fckpb-devops-info-service-1.0.0/bin
Rewriting #!/nix/store/h3q2g9wq4x3q84164qsfm3lz5djj0bf3-python3-3.12.13/bin/python3 to #!/nix/store/h3q2g9wq4x3q84164qsfm3lz5djj0bf3-python3-3.12.13
wrapping `/nix/store/xq34yn50cdxdmflgy6bmmh8d7v8fckpb-devops-info-service-1.0.0/bin/.devops-info-service-wrapped'...
Rewriting #! /nix/store/i27rhb3nr65rkrwz36bchkwmav6ggsmn-bash-5.3p9/bin/bash -e to #!/nix/store/h3q2g9wq4x3q84164qsfm3lz5djj0bf3-python3-3.12.13
Executing pythonRemoveTestsDir
Finished executing pythonRemoveTestsDir
Running phase: pythonCatchConflictsPhase
Running phase: pythonRemoveBinBytecodePhase
Running phase: pythonImportsCheckPhase
Executing pythonImportsCheckPhase
/nix/store/xq34yn50cdxdmflgy6bmmh8d7v8fckpb-devops-info-service-1.0.0
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ readlink result
/nix/store/xq34yn50cdxdmflgy6bmmh8d7v8fckpb-devops-info-service-1.0.0
```

Compare with traditional pip approach:
```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ echo "flask" > requirements-unpinned.txt
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ python -m venv venv1
Command 'python' not found, did you mean:
  command 'python3' from deb python3
  command 'python' from deb python-is-python3
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ python3 -m venv venv1
source venv1/bin/activate
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ source venv1/bin/activate
(venv1) andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ pip install -r requirements-unpinned.txt
Collecting flask (from -r requirements-unpinned.txt (line 1))
  Downloading flask-3.1.3-py3-none-any.whl.metadata (3.2 kB)
Collecting blinker>=1.9.0 (from flask->-r requirements-unpinned.txt (line 1))
  Downloading blinker-1.9.0-py3-none-any.whl.metadata (1.6 kB)
Collecting click>=8.1.3 (from flask->-r requirements-unpinned.txt (line 1))
  Downloading click-8.3.3-py3-none-any.whl.metadata (2.6 kB)
Collecting itsdangerous>=2.2.0 (from flask->-r requirements-unpinned.txt (line 1))
  Downloading itsdangerous-2.2.0-py3-none-any.whl.metadata (1.9 kB)
Collecting jinja2>=3.1.2 (from flask->-r requirements-unpinned.txt (line 1))
  Downloading jinja2-3.1.6-py3-none-any.whl.metadata (2.9 kB)
Collecting markupsafe>=2.1.1 (from flask->-r requirements-unpinned.txt (line 1))
  Downloading markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (2.7 kB)
Collecting werkzeug>=3.1.0 (from flask->-r requirements-unpinned.txt (line 1))
  Downloading werkzeug-3.1.8-py3-none-any.whl.metadata (4.0 kB)
Downloading flask-3.1.3-py3-none-any.whl (103 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 103.4/103.4 kB 979.7 kB/s eta 0:00:00
Downloading blinker-1.9.0-py3-none-any.whl (8.5 kB)
Downloading click-8.3.3-py3-none-any.whl (110 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 110.5/110.5 kB 4.1 MB/s eta 0:00:00
Downloading itsdangerous-2.2.0-py3-none-any.whl (16 kB)
Downloading jinja2-3.1.6-py3-none-any.whl (134 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 134.9/134.9 kB 5.7 MB/s eta 0:00:00
Downloading markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (22 kB)
Downloading werkzeug-3.1.8-py3-none-any.whl (226 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 226.5/226.5 kB 7.7 MB/s eta 0:00:00
Installing collected packages: markupsafe, itsdangerous, click, blinker, werkzeug, jinja2, flask
Successfully installed blinker-1.9.0 click-8.3.3 flask-3.1.3 itsdangerous-2.2.0 jinja2-3.1.6 markupsafe-3.0.3 werkzeug-3.1.8
(venv1) andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ pip freeze | grep -i flask > freeze1.txt
(venv1) andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ deactivate
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ pip cache purge 2>/dev/null || rm -rf ~/.cache/pip
Files removed: 318
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ python3 -m venv venv2
source venv2/bin/activate
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ source venv2/bin/activate
(venv2) andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ pip install -r requirements-unpinned.txt
Collecting flask (from -r requirements-unpinned.txt (line 1))
  Downloading flask-3.1.3-py3-none-any.whl.metadata (3.2 kB)
Collecting blinker>=1.9.0 (from flask->-r requirements-unpinned.txt (line 1))
  Downloading blinker-1.9.0-py3-none-any.whl.metadata (1.6 kB)
Collecting click>=8.1.3 (from flask->-r requirements-unpinned.txt (line 1))
  Downloading click-8.3.3-py3-none-any.whl.metadata (2.6 kB)
Collecting itsdangerous>=2.2.0 (from flask->-r requirements-unpinned.txt (line 1))
  Downloading itsdangerous-2.2.0-py3-none-any.whl.metadata (1.9 kB)
Collecting jinja2>=3.1.2 (from flask->-r requirements-unpinned.txt (line 1))
  Downloading jinja2-3.1.6-py3-none-any.whl.metadata (2.9 kB)
Collecting markupsafe>=2.1.1 (from flask->-r requirements-unpinned.txt (line 1))
  Downloading markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (2.7 kB)
Collecting werkzeug>=3.1.0 (from flask->-r requirements-unpinned.txt (line 1))
  Downloading werkzeug-3.1.8-py3-none-any.whl.metadata (4.0 kB)
Downloading flask-3.1.3-py3-none-any.whl (103 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 103.4/103.4 kB 777.5 kB/s eta 0:00:00
Downloading blinker-1.9.0-py3-none-any.whl (8.5 kB)
Downloading click-8.3.3-py3-none-any.whl (110 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 110.5/110.5 kB 1.7 MB/s eta 0:00:00
Downloading itsdangerous-2.2.0-py3-none-any.whl (16 kB)
Downloading jinja2-3.1.6-py3-none-any.whl (134 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 134.9/134.9 kB 1.8 MB/s eta 0:00:00
Downloading markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (22 kB)
Downloading werkzeug-3.1.8-py3-none-any.whl (226 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 226.5/226.5 kB 2.4 MB/s eta 0:00:00
Installing collected packages: markupsafe, itsdangerous, click, blinker, werkzeug, jinja2, flask
Successfully installed blinker-1.9.0 click-8.3.3 flask-3.1.3 itsdangerous-2.2.0 jinja2-3.1.6 markupsafe-3.0.3 werkzeug-3.1.8
(venv2) andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ pip freeze | grep -i flask > freeze2.txt
(venv2) andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ deactivate
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ diff freeze1.txt freeze2.txt
```

Nix's guarantee:
```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ nix-hash --type sha256 result
cafa7b2be79494d22bc3e7426d7c090335d21df06ce259274e086f753da33619
```

### Comparison Table - Lab 1 vs Lab 18

| Aspect | Lab 1 (pip + venv) | Lab 18 (Nix) |
|--------|-------------------|--------------|
| Python version | System-dependent | Pinned in derivation |
| Dependency resolution | Runtime (`pip install`) | Build-time (pure) |
| Reproducibility | Approximate (with lockfiles) | Bit-for-bit identical |
| Portability | Requires same OS + Python | Works anywhere Nix runs |
| Binary cache | No | Yes (cache.nixos.org) |
| Isolation | Virtual environment | Sandboxed build |
| Store path | N/A | Content-addressable hash |

### Why requirements.txt Provides Weaker Guarantees

**Problem 1: Transitive Dependencies Are Not Pinned**

`requirements.txt` only pins **direct** dependencies:
```
Flask==3.1.2
prometheus-client==0.23.1
portalocker==3.1.1
```

But it doesn't pin what Flask depends on (transitive deps):
- Flask depends on Werkzeug, Jinja2, Click, etc.
- Those have their own dependencies
- `pip install -r requirements.txt` can resolve to **different versions** of transitive deps over time

**Problem 2: System-Level Dependencies**

- Python version itself is system-dependent (venv uses system python).
- System libraries (glibc, openssl) are not controlled by `requirements.txt`.
- Nix ensures both are pinned in the derivation closure.

**Problem 3: Timestamps and Build Artifacts**

- Virtual environments contain build timestamps and intermediate files.
- `pip` cache can affect reproducibility.
- Nix store paths are **content-addressable** — same inputs always produce same hash, regardless of when/where built.

### Explanation of the Nix store path format and what each part means

```
/nix/store/<hash>-<name>-<version>
```
`hash` - hash of build that computed from source code, all dependencies and other items.
`name` - name that writen in pname in default.nix
`version` - version that writen in pname in default.nix

### How would Nix have helped in Lab 1 if you had used it from the start?

**Key Benefits:**

1. **No "works on my machine" problem** — Exact same `default.nix` builds identically on any Linux/WSL.
   - In Lab 1, venv worked on your machine but might have failed for others (different Python versions, missing system libraries).
   - With Nix, same derivation = guaranteed same output forever.

2. **No virtual environment headaches** — No need to:
   - Manually create/activate venv
   - Deal with broken symlinks across OS
   - Nix handles all of this automatically with content-addressable store.

3. **CI/CD reliability** — Docker containers and CI pipelines would be **guaranteed** to build identically:
   - No more "but it worked in Docker" → different runtime results.
   - Binary caches (cache.nixos.org) would speed up builds instead of rebuilding everything.
---

## Task 2 — Reproducible Docker Images (Revisiting Lab 2)

### 2.1: Review Your Lab 2 Dockerfile

Find your Dockerfile from Lab 2:
```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ cat ../app_python/Dockerfi
le
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser /app

USER appuser

EXPOSE 5000

ENV HOST=0.0.0.0 PORT=5000

CMD ["python", "-u", "app.py"]
```

Test Lab 2 Dockerfile reproducibility:
```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ docker build -t lab2-app:v1 ../app_python
[+] Building 13.0s (11/11) FINISHED                                                           docker:default
 => [internal] load build definition from Dockerfile                                                    0.1s
 => => transferring dockerfile: 332B                                                                    0.0s
 => [internal] load metadata for docker.io/library/python:3.12-slim                                     1.0s
 => [internal] load .dockerignore                                                                       0.1s
 => => transferring context: 170B                                                                       0.1s
 => [1/6] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f87  0.0s
 => [internal] load build context                                                                       0.2s
 => => transferring context: 775B                                                                       0.2s
 => CACHED [2/6] WORKDIR /app                                                                           0.0s
 => CACHED [3/6] COPY requirements.txt .                                                                0.0s
 => [4/6] RUN pip install --no-cache-dir -r requirements.txt                                           10.0s
 => [5/6] COPY . .                                                                                      0.1s 
 => [6/6] RUN useradd --create-home --shell /bin/bash appuser     && chown -R appuser /app              0.8s 
 => exporting to image                                                                                  0.6s
 => => exporting layers                                                                                 0.6s
 => => writing image sha256:81b3b5ec9330768e94daf739d1a5cc41c2a5e96bbb98c04e26afa6cedf5c37e7            0.0s
 => => naming to docker.io/library/lab2-app:v1                                                          0.0s
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ docker inspect lab2-app:v1 | grep Created
        "Created": "2026-05-07T13:59:00.899717399+03:00",
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ sleep 5
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ docker build -t lab2-app:v2 ../app_python
[+] Building 1.0s (11/11) FINISHED                                                            docker:default
 => [internal] load build definition from Dockerfile                                                    0.1s
 => => transferring dockerfile: 332B                                                                    0.0s
 => [internal] load metadata for docker.io/library/python:3.12-slim                                     0.7s
 => [internal] load .dockerignore                                                                       0.0s
 => => transferring context: 170B                                                                       0.0s
 => [1/6] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f87  0.0s
 => [internal] load build context                                                                       0.1s
 => => transferring context: 775B                                                                       0.1s
 => CACHED [2/6] WORKDIR /app                                                                           0.0s
 => CACHED [3/6] COPY requirements.txt .                                                                0.0s
 => CACHED [4/6] RUN pip install --no-cache-dir -r requirements.txt                                     0.0s
 => CACHED [5/6] COPY . .                                                                               0.0s
 => CACHED [6/6] RUN useradd --create-home --shell /bin/bash appuser     && chown -R appuser /app       0.0s
 => exporting to image                                                                                  0.0s
 => => exporting layers                                                                                 0.0s
 => => writing image sha256:81b3b5ec9330768e94daf739d1a5cc41c2a5e96bbb98c04e26afa6cedf5c37e7            0.0s
 => => naming to docker.io/library/lab2-app:v2                                                          0.0s
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ docker inspect lab2-app:v2 | grep Created
        "Created": "2026-05-07T13:59:00.899717399+03:00",
```
But i get same timestamps. Dockerfile used CACHED stages, because in file was no changes.

### 2.2: Build Docker Image with Nix

`docker.nix`:
```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [ app ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
    Env = [
      "HOST=0.0.0.0"
      "PORT=5000"
    ];
  };

  created = "1970-01-01T00:00:01Z";  # Reproducible timestamp
}
```

| Field | Purpose |
|-------|---------|
| `name` | Docker image name |
| `tag` | Image tag |
| `contents` | Included packages |
| `config` | Configs for this docker |
| `config.Cmd` | Command to run |
| `config.ExposedPorts` | Port configuration |
| `config.ExposedPorts` | Envirement configuration |
| `created` | Fixed timestamp for reproducibility |


build:
```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ nix-build docker.nix
unpacking 'https://flakehub.com/f/DeterminateSystems/nixpkgs-weekly/%2A.tar.gz' into the Git cache...
these 8 derivations will be built:
  /nix/store/1iz5mh9b9dxlc3cbirq52i0y93icv65y-devops-info-service-1.0.0.drv
  /nix/store/nf5w0mqsw6fh5mnnf49w49y1i90qc5xg-devops-info-service-nix-base.json.drv
  /nix/store/ziv950nj1py5z4fx99wp4ykvnd94q4gq-devops-info-service-nix-customisation-layer.drv
  /nix/store/fr2ki79zpcnw80rds08jfagw7f7xg5nk-excludePaths.drv
  /nix/store/g9p68534by8wjxgz87cdva0jqpkfgb4p-layers.json.drv
  /nix/store/ivydv94knhg03m2qadn3idz2s0p0fnp3-devops-info-service-nix-conf.json.drv
  /nix/store/mfnrb51456g8cs39c9r7k6j8bn577f78-stream-devops-info-service-nix.drv
  /nix/store/pzaj1iy1mhhqlbp312xjj183apragp1a-devops-info-service-nix.tar.gz.drv
these 12 paths will be fetched (178.1 KiB download, 128.4 MiB unpacked):
  /nix/store/dpayvg17ysv6kdb31j80wpbsqly9zgpz-fakeroot-1.37.2
  /nix/store/drm3hgigwg5rdxzgjxhnh8vsdpb11ia7-getopt-1.1.6
  /nix/store/09bq2i0kb008ccg3qdbyxv81ggxxnn09-jq-1.8.1
  /nix/store/v5c3inhfq6xshmwg1c254vfbcy4jp3k9-jq-1.8.1-bin
  /nix/store/p8x5zv9s9qg3ld8b7jdm03hkpdqybjl9-jq-1.8.1-dev
  /nix/store/xagd1mnqfib9dzrnh9ihwgjs1rs8pmwd-lndir-1.0.5
  /nix/store/ic9dmcfd2pbvvrd8sbw0h8x9mfb0wll0-oniguruma-6.9.10-lib
  /nix/store/zj6qyrs4nyvav1nn3yalh78wgjc9qb8c-pigz-2.8
  /nix/store/0r6k8xa2kgqyp3r4v2w7yrb80ma2iawm-python3-3.13.12
  /nix/store/74ma22y9kdxjvvrrgz3q1dqnm8r4d99d-stdenv-linux
  /nix/store/i4vy30696ml3plirh2jzf9f50f9i7qv1-stream
  /nix/store/wj5213f7a28sla3cnpzhdfi8cpc6b1g6-stream
copying path '/nix/store/zj6qyrs4nyvav1nn3yalh78wgjc9qb8c-pigz-2.8' from 'https://cache.nixos.org'...
copying path '/nix/store/74ma22y9kdxjvvrrgz3q1dqnm8r4d99d-stdenv-linux' from 'https://install.determinate.systems'...
copying path '/nix/store/0r6k8xa2kgqyp3r4v2w7yrb80ma2iawm-python3-3.13.12' from 'https://install.determinate.systems'...
copying path '/nix/store/ic9dmcfd2pbvvrd8sbw0h8x9mfb0wll0-oniguruma-6.9.10-lib' from 'https://install.determinate.systems'...
copying path '/nix/store/drm3hgigwg5rdxzgjxhnh8vsdpb11ia7-getopt-1.1.6' from 'https://cache.nixos.org'...
copying path '/nix/store/xagd1mnqfib9dzrnh9ihwgjs1rs8pmwd-lndir-1.0.5' from 'https://install.determinate.systems'...
building '/nix/store/1iz5mh9b9dxlc3cbirq52i0y93icv65y-devops-info-service-1.0.0.drv'...
Sourcing python-remove-tests-dir-hook
Sourcing python-catch-conflicts-hook.sh
Sourcing python-remove-bin-bytecode-hook.sh
Sourcing python-imports-check-hook.sh
Using pythonImportsCheckPhase
Sourcing python-namespaces-hook
Running phase: unpackPhase
copying path '/nix/store/dpayvg17ysv6kdb31j80wpbsqly9zgpz-fakeroot-1.37.2' from 'https://cache.nixos.org'...
unpacking source archive /nix/store/7v63z7w10ar6p5vw3hs6imp7q20zwaxq-app_python_lab18
source root is app_python_lab18
setting SOURCE_DATE_EPOCH to timestamp 315619200 of file "app_python_lab18/requirements.txt"
Running phase: patchPhase
Running phase: updateAutotoolsGnuConfigScriptsPhase
Running phase: configurePhase
no configure script, doing nothing
Running phase: buildPhase
no Makefile or custom buildPhase, doing nothing
Running phase: installPhase
Running phase: fixupPhase
shrinking RPATHs of ELF executables and libraries in /nix/store/pgd2c9c9ni4r5nqv4ddfxv83sk4chs06-devops-info-service-1.0.0
checking for references to /build/ in /nix/store/pgd2c9c9ni4r5nqv4ddfxv83sk4chs06-devops-info-service-1.0.0...
patching script interpreter paths in /nix/store/pgd2c9c9ni4r5nqv4ddfxv83sk4chs06-devops-info-service-1.0.0
/nix/store/pgd2c9c9ni4r5nqv4ddfxv83sk4chs06-devops-info-service-1.0.0/bin/.devops-info-service-wrapped: interpreter directive changed from "#!/usr/bin/env python3" to "/nix/store/h3q2g9wq4x3q84164qsfm3lz5djj0bf3-python3-3.12.13/bin/python3"
stripping (with command strip and flags -S -p) in  /nix/store/pgd2c9c9ni4r5nqv4ddfxv83sk4chs06-devops-info-service-1.0.0/bin
Rewriting #!/nix/store/h3q2g9wq4x3q84164qsfm3lz5djj0bf3-python3-3.12.13/bin/python3 to #!/nix/store/h3q2g9wq4x3q84164qsfm3lz5djj0bf3-python3-3.12.13
wrapping `/nix/store/pgd2c9c9ni4r5nqv4ddfxv83sk4chs06-devops-info-service-1.0.0/bin/.devops-info-service-wrapped'...
Rewriting #! /nix/store/i27rhb3nr65rkrwz36bchkwmav6ggsmn-bash-5.3p9/bin/bash -e to #!/nix/store/h3q2g9wq4x3q84164qsfm3lz5djj0bf3-python3-3.12.13
Executing pythonRemoveTestsDir
Finished executing pythonRemoveTestsDir
Running phase: pythonCatchConflictsPhase
Running phase: pythonRemoveBinBytecodePhase
Running phase: pythonImportsCheckPhase
Executing pythonImportsCheckPhase
building '/nix/store/nf5w0mqsw6fh5mnnf49w49y1i90qc5xg-devops-info-service-nix-base.json.drv'...
building '/nix/store/ziv950nj1py5z4fx99wp4ykvnd94q4gq-devops-info-service-nix-customisation-layer.drv'...
copying path '/nix/store/09bq2i0kb008ccg3qdbyxv81ggxxnn09-jq-1.8.1' from 'https://install.determinate.systems'...
building '/nix/store/fr2ki79zpcnw80rds08jfagw7f7xg5nk-excludePaths.drv'...
copying path '/nix/store/v5c3inhfq6xshmwg1c254vfbcy4jp3k9-jq-1.8.1-bin' from 'https://install.determinate.systems'...
copying path '/nix/store/p8x5zv9s9qg3ld8b7jdm03hkpdqybjl9-jq-1.8.1-dev' from 'https://install.determinate.systems'...
copying path '/nix/store/i4vy30696ml3plirh2jzf9f50f9i7qv1-stream' from 'https://cache.nixos.org'...
building '/nix/store/g9p68534by8wjxgz87cdva0jqpkfgb4p-layers.json.drv'...
structuredAttrs is enabled
copying path '/nix/store/wj5213f7a28sla3cnpzhdfi8cpc6b1g6-stream' from 'https://cache.nixos.org'...
building '/nix/store/ivydv94knhg03m2qadn3idz2s0p0fnp3-devops-info-service-nix-conf.json.drv'...
{
  "architecture": "amd64",
  "config": {
    "Cmd": [
      "/nix/store/pgd2c9c9ni4r5nqv4ddfxv83sk4chs06-devops-info-service-1.0.0/bin/devops-info-service"
    ],
    "Env": [
      "HOST=0.0.0.0",
      "PORT=5000"
    ],
    "ExposedPorts": {
      "5000/tcp": {}
    }
  },
  "os": "linux",
  "store_dir": "/nix/store",
  "from_image": null,
  "store_layers": [
    [
      "/nix/store/b73wvf83q4cjwzz99pdanbl8qpfawr69-mailcap-2.1.54"
    ],
    [
      "/nix/store/0minj1ypl50k4zl85gsngfw0z0y9ddg0-util-linux-minimal-2.42"
    ],
    [
      "/nix/store/xx0z77494lfxr8qjwpck246fry05n3nm-xgcc-15.2.0-libgcc"
    ],
    [
      "/nix/store/wrxyd3k2f4bmh52pr5rpdjxxsm5r2qxm-gcc-15.2.0-libgcc"
    ],
    [
      "/nix/store/i4gg1f526vl5psg5nqniflj4v77vc1kd-libunistring-1.4.2"
    ],
    [
      "/nix/store/cxjmhdbpy3bk12jc6lwpmcvlas76a7zm-tzdata-2026a"
    ],
    [
      "/nix/store/sgswwrxkhdlfskklqp4gsbi2cskfg07c-libidn2-2.3.8"
    ],
    [
      "/nix/store/fjkx1l5cnskzrqacf08z7i8z17256w0j-glibc-2.42-61"
    ],
    [
      "/nix/store/hyai3q7gvdfppw4ky7s2mvhxvfyp5bh7-libffi-3.5.2"
    ],
    [
      "/nix/store/2amncb4zvr32gm5d2i8m6gz29c02cn61-bzip2-1.0.8"
    ],
    [
      "/nix/store/ixhlv41i2wpl84xgjcks061dz4yssbg3-zlib-1.3.2"
    ],
    [
      "/nix/store/0ksa3i39aqkwdrh2q0s1svwymhc1w3dm-libxcrypt-4.5.2"
    ],
    [
      "/nix/store/yw0fl2v8g35w2dii8phnr0fjb9nr1b0b-mpdecimal-4.0.1"
    ],
    [
      "/nix/store/pa6n8nrmgq8jswk2pkrl5qprcls1r0ch-expat-2.7.5"
    ],
    [
      "/nix/store/rnaq5b0la7pcq6hyf86iy8ihazgcamg6-gdbm-1.26-lib"
    ],
    [
      "/nix/store/hmslvsxvs2ijb7iw5krdckai2im6vp2y-xz-5.8.3"
    ],
    [
      "/nix/store/i27rhb3nr65rkrwz36bchkwmav6ggsmn-bash-5.3p9"
    ],
    [
      "/nix/store/291rd5nk7hkhcpzbh7pxqiz75xikdll3-util-linux-minimal-2.42-lib"
    ],
    [
      "/nix/store/2iaawa9vbqas51lgpn4cjnnfdv74x8fn-ncurses-6.6"
    ],
    [
      "/nix/store/47h2ny0j1xbz879a9s7s55fyv3zawr3r-readline-8.3p3"
    ],
    [
      "/nix/store/5087xk8l09k90gddzw8y9b4yypyn23a5-sqlite-3.51.2"
    ],
    [
      "/nix/store/wbyqkb1vpm41s4jb8pv0i9h4jv08xdrv-openssl-3.6.1"
    ],
    [
      "/nix/store/si4q3zks5mn5jhzzyri9hhd3cv789vlm-gcc-15.2.0-lib"
    ],
    [
      "/nix/store/h3q2g9wq4x3q84164qsfm3lz5djj0bf3-python3-3.12.13"
    ],
    [
      "/nix/store/ahc88fjf9k2dbh9r3rr3amnn6y0335mz-python3.12-blinker-1.9.0"
    ],
    [
      "/nix/store/cgjxsl9fvvm4qwizzjxzcpylskc1pj0z-python3.12-markupsafe-3.0.3"
    ],
    [
      "/nix/store/0g60yhdn0wspl1mp8v9z7w4iawmb179a-python3.12-itsdangerous-2.2.0"
    ],
    [
      "/nix/store/ywbcbgfc7dxbyb99vqa7jrnxbgbgfghf-python3.12-typing-extensions-4.15.0"
    ],
    [
      "/nix/store/6jldwqd2i3ldh9r2wrsrvyyhhi8fpd79-python3.12-asgiref-3.11.0"
    ],
    [
      "/nix/store/x43ni2qi5w977j5rs0pn6i1jj47i7i66-python3.12-click-8.3.1"
    ],
    [
      "/nix/store/z75h5j332gxwn4h7csyvwpcd101v28qh-python3.12-prometheus-client-0.24.1"
    ],
    [
      "/nix/store/ibpswnyvm31xywa97i5r7g756dl1inds-python3.12-jinja2-3.1.6"
    ],
    [
      "/nix/store/hh2mxvvfqq9n6g1a287bz2livmc293wv-python3.12-werkzeug-3.1.6"
    ],
    [
      "/nix/store/ippax0jv4ksrvl89jqibg6alk6p58h0h-python3.12-redis-7.4.0"
    ],
    [
      "/nix/store/z7mlm1g0pqsn7h18m5xhjphk15xc7d8c-python3.12-portalocker-3.2.0"
    ],
    [
      "/nix/store/llsx09vh6jlgkhgl61zvmchvxsbin72d-python3.12-flask-3.1.2"
    ],
    [
      "/nix/store/pgd2c9c9ni4r5nqv4ddfxv83sk4chs06-devops-info-service-1.0.0"
    ]
  ],
  "customisation_layer": "/nix/store/zj3gkrskpanssrbghm6rxaz25wib53gi-devops-info-service-nix-customisation-layer",
  "repo_tag": "devops-info-service-nix:1.0.0",
  "created": "1970-01-01T00:00:01+00:00",
  "mtime": "1970-01-01T00:00:01+00:00",
  "uid": "0",
  "gid": "0",
  "uname": "root",
  "gname": "root"
}
building '/nix/store/mfnrb51456g8cs39c9r7k6j8bn577f78-stream-devops-info-service-nix.drv'...
building '/nix/store/pzaj1iy1mhhqlbp312xjj183apragp1a-devops-info-service-nix.tar.gz.drv'...
No 'fromImage' provided
Creating layer 1 from paths: ['/nix/store/b73wvf83q4cjwzz99pdanbl8qpfawr69-mailcap-2.1.54']
Creating layer 2 from paths: ['/nix/store/0minj1ypl50k4zl85gsngfw0z0y9ddg0-util-linux-minimal-2.42']
Creating layer 3 from paths: ['/nix/store/xx0z77494lfxr8qjwpck246fry05n3nm-xgcc-15.2.0-libgcc']
Creating layer 4 from paths: ['/nix/store/wrxyd3k2f4bmh52pr5rpdjxxsm5r2qxm-gcc-15.2.0-libgcc']
Creating layer 5 from paths: ['/nix/store/i4gg1f526vl5psg5nqniflj4v77vc1kd-libunistring-1.4.2']
Creating layer 6 from paths: ['/nix/store/cxjmhdbpy3bk12jc6lwpmcvlas76a7zm-tzdata-2026a']
Creating layer 7 from paths: ['/nix/store/sgswwrxkhdlfskklqp4gsbi2cskfg07c-libidn2-2.3.8']
Creating layer 8 from paths: ['/nix/store/fjkx1l5cnskzrqacf08z7i8z17256w0j-glibc-2.42-61']
Creating layer 9 from paths: ['/nix/store/hyai3q7gvdfppw4ky7s2mvhxvfyp5bh7-libffi-3.5.2']
Creating layer 10 from paths: ['/nix/store/2amncb4zvr32gm5d2i8m6gz29c02cn61-bzip2-1.0.8']
Creating layer 11 from paths: ['/nix/store/ixhlv41i2wpl84xgjcks061dz4yssbg3-zlib-1.3.2']
Creating layer 12 from paths: ['/nix/store/0ksa3i39aqkwdrh2q0s1svwymhc1w3dm-libxcrypt-4.5.2']
Creating layer 13 from paths: ['/nix/store/yw0fl2v8g35w2dii8phnr0fjb9nr1b0b-mpdecimal-4.0.1']
Creating layer 14 from paths: ['/nix/store/pa6n8nrmgq8jswk2pkrl5qprcls1r0ch-expat-2.7.5']
Creating layer 15 from paths: ['/nix/store/rnaq5b0la7pcq6hyf86iy8ihazgcamg6-gdbm-1.26-lib']
Creating layer 16 from paths: ['/nix/store/hmslvsxvs2ijb7iw5krdckai2im6vp2y-xz-5.8.3']
Creating layer 17 from paths: ['/nix/store/i27rhb3nr65rkrwz36bchkwmav6ggsmn-bash-5.3p9']
Creating layer 18 from paths: ['/nix/store/291rd5nk7hkhcpzbh7pxqiz75xikdll3-util-linux-minimal-2.42-lib']
Creating layer 19 from paths: ['/nix/store/2iaawa9vbqas51lgpn4cjnnfdv74x8fn-ncurses-6.6']
Creating layer 20 from paths: ['/nix/store/47h2ny0j1xbz879a9s7s55fyv3zawr3r-readline-8.3p3']
Creating layer 21 from paths: ['/nix/store/5087xk8l09k90gddzw8y9b4yypyn23a5-sqlite-3.51.2']
Creating layer 22 from paths: ['/nix/store/wbyqkb1vpm41s4jb8pv0i9h4jv08xdrv-openssl-3.6.1']
Creating layer 23 from paths: ['/nix/store/si4q3zks5mn5jhzzyri9hhd3cv789vlm-gcc-15.2.0-lib']
Creating layer 24 from paths: ['/nix/store/h3q2g9wq4x3q84164qsfm3lz5djj0bf3-python3-3.12.13']
Creating layer 25 from paths: ['/nix/store/ahc88fjf9k2dbh9r3rr3amnn6y0335mz-python3.12-blinker-1.9.0']
Creating layer 26 from paths: ['/nix/store/cgjxsl9fvvm4qwizzjxzcpylskc1pj0z-python3.12-markupsafe-3.0.3']
Creating layer 27 from paths: ['/nix/store/0g60yhdn0wspl1mp8v9z7w4iawmb179a-python3.12-itsdangerous-2.2.0']
Creating layer 28 from paths: ['/nix/store/ywbcbgfc7dxbyb99vqa7jrnxbgbgfghf-python3.12-typing-extensions-4.15.0']
Creating layer 29 from paths: ['/nix/store/6jldwqd2i3ldh9r2wrsrvyyhhi8fpd79-python3.12-asgiref-3.11.0']
Creating layer 30 from paths: ['/nix/store/x43ni2qi5w977j5rs0pn6i1jj47i7i66-python3.12-click-8.3.1']
Creating layer 31 from paths: ['/nix/store/z75h5j332gxwn4h7csyvwpcd101v28qh-python3.12-prometheus-client-0.24.1']
Creating layer 32 from paths: ['/nix/store/ibpswnyvm31xywa97i5r7g756dl1inds-python3.12-jinja2-3.1.6']
Creating layer 33 from paths: ['/nix/store/hh2mxvvfqq9n6g1a287bz2livmc293wv-python3.12-werkzeug-3.1.6']
Creating layer 34 from paths: ['/nix/store/ippax0jv4ksrvl89jqibg6alk6p58h0h-python3.12-redis-7.4.0']
Creating layer 35 from paths: ['/nix/store/z7mlm1g0pqsn7h18m5xhjphk15xc7d8c-python3.12-portalocker-3.2.0']
Creating layer 36 from paths: ['/nix/store/llsx09vh6jlgkhgl61zvmchvxsbin72d-python3.12-flask-3.1.2']
Creating layer 37 from paths: ['/nix/store/pgd2c9c9ni4r5nqv4ddfxv83sk4chs06-devops-info-service-1.0.0']
Creating layer 38 with customisation...
Adding manifests...
Done.
/nix/store/w4jdp32hlxy34iby4sg4sp9mvgamzy66-devops-info-service-nix.tar.gz
```

Load into Docker:
```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ docker load < result
f033cabae158: Loading layer  133.1kB/133.1kB
f0043dc5257f: Loading layer  327.7kB/327.7kB
541016de8053: Loading layer  204.8kB/204.8kB
e67a34301a94: Loading layer  204.8kB/204.8kB
692d7c38ef8e: Loading layer  2.089MB/2.089MB
1003e5e46e81: Loading layer  2.939MB/2.939MB
0dea27164515: Loading layer  419.8kB/419.8kB
d13ab8cba8b3: Loading layer   35.7MB/35.7MB
6a0bbbd96514: Loading layer  81.92kB/81.92kB
c64a0e7c04d5: Loading layer  102.4kB/102.4kB
9c4f6445e41e: Loading layer  143.4kB/143.4kB
bc1d7e66c59e: Loading layer  153.6kB/153.6kB
db7226b603c1: Loading layer  235.5kB/235.5kB
6e4c1daeeb2c: Loading layer  317.4kB/317.4kB
4bfe54c4b503: Loading layer  491.5kB/491.5kB
3f7f659e2096: Loading layer  901.1kB/901.1kB
bed8d747475b: Loading layer  1.894MB/1.894MB
3eb255a3eea5: Loading layer   2.12MB/2.12MB
85ee5e54ef34: Loading layer  5.284MB/5.284MB
39b908c2f3bb: Loading layer    512kB/512kB
3daeb357f7a3: Loading layer  5.878MB/5.878MB
9b093c29513e: Loading layer  9.318MB/9.318MB
3cbba788ed5c: Loading layer  10.34MB/10.34MB
9d8e30ef2585: Loading layer  137.3MB/137.3MB
971b5d454245: Loading layer  122.9kB/122.9kB
24cab5c8d0e3: Loading layer  133.1kB/133.1kB
6819c96058d4: Loading layer    215kB/215kB
270cd7e27d93: Loading layer  532.5kB/532.5kB
34f020490a50: Loading layer  307.2kB/307.2kB
af22aca3d825: Loading layer  1.393MB/1.393MB
7549e9dd8e16: Loading layer  911.4kB/911.4kB
7a56a370a16c: Loading layer  2.007MB/2.007MB
773865037bc0: Loading layer  2.908MB/2.908MB
91405e4644a1: Loading layer  6.707MB/6.707MB
65806609b5ea: Loading layer  276.5kB/276.5kB
04d51acf17fd: Loading layer   1.27MB/1.27MB
515b28600b4e: Loading layer  30.72kB/30.72kB
44d9b030db66: Loading layer  10.24kB/10.24kB
Loaded image: devops-info-service-nix:1.0.0
```

Run both containers side-by-side:
```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ docker stop lab2-container nix-container 2>/dev/null || true

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ docker rm lab2-container nix-container 2>/dev/null || true

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ docker run -d -p 5000:5000 --name lab2-container lab2-app:v1
5a78facb01339ca817e1c328907f9c93706573d2a9a7a8d92110bc8f0b19b10a

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0
ed8973a4cc107f62a9c160a61b6cc93a5d2b49034adc1d2557bb7e60d184aad1

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-05-07T11:18:21.159508+00:00","uptime_seconds":15.147861}

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ curl http://localhost:5001/health
{"status":"healthy","timestamp":"2026-05-07T11:18:26.302734+00:00","uptime_seconds":11.690798}
```

### 2.3: Compare Reproducibility - Lab 2 vs Lab 18

#### Test 1: Rebuild Reproducibility

Rebuild Nix image multiple times:
```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ rm -f result

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ nix-build docker.nix
...

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ sha256sum result
d1320fe223d306fb4b6ff062d0032820bb0b9b0fb13273b31873889591ac0ec4  result

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ rm -f result

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ nix-build docker.nix
/nix/store/wm9kb5i0r9kxqi94l24pg2h5h183lqwa-devops-info-service-nix.tar.gz

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ sha256sum result
d1320fe223d306fb4b6ff062d0032820bb0b9b0fb13273b31873889591ac0ec4  result
```

Compare with Lab 2 Dockerfile:
```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ docker build -t lab2-app:test1 ../app_python/
...

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ docker save lab2-app:test1 | sha256sum
e83bbb04d1c945c24f0ae9f5fc21c4ef91a111cc2ef37853e3e0643e00afe57e  -

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ sleep 2

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ docker build -t lab2-app:test2 ./app_python/
...

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ docker save lab2-app:test2 | sha256sum
622120a753b730c0fc78f3cd56b138ae4b151e71bf78d0c11f1aee3951e37a47  -
```

#### Test 2: Image Size Comparison

```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ docker images | grep -E "lab2-app|devops-info-service-nix"
WARNING: This output is designed for human readability. For machine-readable output, please use --format.
devops-info-service-nix:1.0.0              f6b736d2b763        222MB             0B   U    
lab2-app:test1                             81b3b5ec9330        146MB             0B   U    
lab2-app:test2                             81b3b5ec9330        146MB             0B   U    
lab2-app:v1                                81b3b5ec9330        146MB             0B   U    
lab2-app:v2                                81b3b5ec9330        146MB             0B   U 
```

| Metric | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
|--------|------------------|------------------------|
| Image size | ~146MB | ~222MB |
| Reproducibility | Not guaranteed (normal builds can vary; in this run tags were reused from cache) | Guaranteed for same inputs (`sha256sum result` identical on rebuild) |
| Build caching | Layer-based (timestamp-dependent) | Content-addressable |
| Base image dependency | Yes (`python:3.12-slim`) | No base image needed |

#### Test 3: Layer Analysis

Examine Lab 2 image layers:
```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ docker history lab2-app:v1
IMAGE          CREATED          CREATED BY                                      SIZE      COMMENT
81b3b5ec9330   34 minutes ago   CMD ["python" "-u" "app.py"]                    0B        buildkit.dockerfile.v0
<missing>      34 minutes ago   ENV HOST=0.0.0.0 PORT=5000                      0B        buildkit.dockerfile.v0
<missing>      34 minutes ago   EXPOSE [5000/tcp]                               0B        buildkit.dockerfile.v0
<missing>      34 minutes ago   USER appuser                                    0B        buildkit.dockerfile.v0
<missing>      34 minutes ago   RUN /bin/sh -c useradd --create-home --shell…   60.3kB    buildkit.dockerfile.v0
<missing>      34 minutes ago   COPY . . # buildkit                             51.4kB    buildkit.dockerfile.v0
<missing>      34 minutes ago   RUN /bin/sh -c pip install --no-cache-dir -r…   26.9MB    buildkit.dockerfile.v0
<missing>      3 days ago       COPY requirements.txt . # buildkit              85B       buildkit.dockerfile.v0
<missing>      3 days ago       WORKDIR /app                                    0B        buildkit.dockerfile.v0
<missing>      2 weeks ago      CMD ["python3"]                                 0B        buildkit.dockerfile.v0
<missing>      2 weeks ago      RUN /bin/sh -c set -eux;  for src in idle3 p…   36B       buildkit.dockerfile.v0
<missing>      2 weeks ago      RUN /bin/sh -c set -eux;   savedAptMark="$(a…   36.8MB    buildkit.dockerfile.v0
<missing>      2 weeks ago      ENV PYTHON_SHA256=c08bc65a81971c1dd578318282…   0B        buildkit.dockerfile.v0
<missing>      2 weeks ago      ENV PYTHON_VERSION=3.12.13                      0B        buildkit.dockerfile.v0
<missing>      2 weeks ago      ENV GPG_KEY=7169605F62C751356D054A26A821E680…   0B        buildkit.dockerfile.v0
<missing>      2 weeks ago      RUN /bin/sh -c set -eux;  apt-get update;  a…   3.81MB    buildkit.dockerfile.v0
<missing>      2 weeks ago      ENV LANG=C.UTF-8                                0B        buildkit.dockerfile.v0
<missing>      2 weeks ago      ENV PATH=/usr/local/bin:/usr/local/sbin:/usr…   0B        buildkit.dockerfile.v0
<missing>      2 weeks ago      # debian.sh --arch 'amd64' out/ 'trixie' '@1…   78.6MB    debuerreotype 0.17
```

Examine Nix image layers:
```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/app_python_lab18$ docker history devops-info-service-nix:1.0.0
IMAGE          CREATED   CREATED BY   SIZE      COMMENT
f6b736d2b763   N/A                    411B      store paths: ['/nix/store/zj3gkrskpanssrbghm6rxaz25wib53gi-devops-info-service-nix-customisation-layer']
<missing>      N/A                    14.9kB    store paths: ['/nix/store/pgd2c9c9ni4r5nqv4ddfxv83sk4chs06-devops-info-service-1.0.0']
<missing>      N/A                    1.1MB     store paths: ['/nix/store/llsx09vh6jlgkhgl61zvmchvxsbin72d-python3.12-flask-3.1.2']
<missing>      N/A                    202kB     store paths: ['/nix/store/z7mlm1g0pqsn7h18m5xhjphk15xc7d8c-python3.12-portalocker-3.2.0']
<missing>      N/A                    6.04MB    store paths: ['/nix/store/ippax0jv4ksrvl89jqibg6alk6p58h0h-python3.12-redis-7.4.0']
<missing>      N/A                    2.57MB    store paths: ['/nix/store/hh2mxvvfqq9n6g1a287bz2livmc293wv-python3.12-werkzeug-3.1.6']
<missing>      N/A                    1.85MB    store paths: ['/nix/store/ibpswnyvm31xywa97i5r7g756dl1inds-python3.12-jinja2-3.1.6']
<missing>      N/A                    706kB     store paths: ['/nix/store/z75h5j332gxwn4h7csyvwpcd101v28qh-python3.12-prometheus-client-0.24.1']
<missing>      N/A                    1.27MB    store paths: ['/nix/store/x43ni2qi5w977j5rs0pn6i1jj47i7i66-python3.12-click-8.3.1']
<missing>      N/A                    224kB     store paths: ['/nix/store/6jldwqd2i3ldh9r2wrsrvyyhhi8fpd79-python3.12-asgiref-3.11.0']
<missing>      N/A                    505kB     store paths: ['/nix/store/ywbcbgfc7dxbyb99vqa7jrnxbgbgfghf-python3.12-typing-extensions-4.15.0']
<missing>      N/A                    144kB     store paths: ['/nix/store/0g60yhdn0wspl1mp8v9z7w4iawmb179a-python3.12-itsdangerous-2.2.0']
<missing>      N/A                    82.1kB    store paths: ['/nix/store/cgjxsl9fvvm4qwizzjxzcpylskc1pj0z-python3.12-markupsafe-3.0.3']
<missing>      N/A                    75.1kB    store paths: ['/nix/store/ahc88fjf9k2dbh9r3rr3amnn6y0335mz-python3.12-blinker-1.9.0']
<missing>      N/A                    132MB     store paths: ['/nix/store/h3q2g9wq4x3q84164qsfm3lz5djj0bf3-python3-3.12.13']
<missing>      N/A                    10.3MB    store paths: ['/nix/store/si4q3zks5mn5jhzzyri9hhd3cv789vlm-gcc-15.2.0-lib']
<missing>      N/A                    9.3MB     store paths: ['/nix/store/wbyqkb1vpm41s4jb8pv0i9h4jv08xdrv-openssl-3.6.1']
<missing>      N/A                    5.86MB    store paths: ['/nix/store/5087xk8l09k90gddzw8y9b4yypyn23a5-sqlite-3.51.2']
<missing>      N/A                    505kB     store paths: ['/nix/store/47h2ny0j1xbz879a9s7s55fyv3zawr3r-readline-8.3p3']
<missing>      N/A                    3.3MB     store paths: ['/nix/store/2iaawa9vbqas51lgpn4cjnnfdv74x8fn-ncurses-6.6']
<missing>      N/A                    2.1MB     store paths: ['/nix/store/291rd5nk7hkhcpzbh7pxqiz75xikdll3-util-linux-minimal-2.42-lib']
<missing>      N/A                    1.85MB    store paths: ['/nix/store/i27rhb3nr65rkrwz36bchkwmav6ggsmn-bash-5.3p9']
<missing>      N/A                    843kB     store paths: ['/nix/store/hmslvsxvs2ijb7iw5krdckai2im6vp2y-xz-5.8.3']
<missing>      N/A                    449kB     store paths: ['/nix/store/rnaq5b0la7pcq6hyf86iy8ihazgcamg6-gdbm-1.26-lib']
<missing>      N/A                    307kB     store paths: ['/nix/store/pa6n8nrmgq8jswk2pkrl5qprcls1r0ch-expat-2.7.5']
<missing>      N/A                    224kB     store paths: ['/nix/store/yw0fl2v8g35w2dii8phnr0fjb9nr1b0b-mpdecimal-4.0.1']
<missing>      N/A                    142kB     store paths: ['/nix/store/0ksa3i39aqkwdrh2q0s1svwymhc1w3dm-libxcrypt-4.5.2']
<missing>      N/A                    131kB     store paths: ['/nix/store/ixhlv41i2wpl84xgjcks061dz4yssbg3-zlib-1.3.2']
<missing>      N/A                    87.7kB    store paths: ['/nix/store/2amncb4zvr32gm5d2i8m6gz29c02cn61-bzip2-1.0.8']
<missing>      N/A                    72.5kB    store paths: ['/nix/store/hyai3q7gvdfppw4ky7s2mvhxvfyp5bh7-libffi-3.5.2']
<missing>      N/A                    34.9MB    store paths: ['/nix/store/fjkx1l5cnskzrqacf08z7i8z17256w0j-glibc-2.42-61']
<missing>      N/A                    362kB     store paths: ['/nix/store/sgswwrxkhdlfskklqp4gsbi2cskfg07c-libidn2-2.3.8']
<missing>      N/A                    1.9MB     store paths: ['/nix/store/cxjmhdbpy3bk12jc6lwpmcvlas76a7zm-tzdata-2026a']
<missing>      N/A                    2.08MB    store paths: ['/nix/store/i4gg1f526vl5psg5nqniflj4v77vc1kd-libunistring-1.4.2']
<missing>      N/A                    197kB     store paths: ['/nix/store/wrxyd3k2f4bmh52pr5rpdjxxsm5r2qxm-gcc-15.2.0-libgcc']
<missing>      N/A                    197kB     store paths: ['/nix/store/xx0z77494lfxr8qjwpck246fry05n3nm-xgcc-15.2.0-libgcc']
<missing>      N/A                    121kB     store paths: ['/nix/store/0minj1ypl50k4zl85gsngfw0z0y9ddg0-util-linux-minimal-2.42']
<missing>      N/A                    118kB     store paths: ['/nix/store/b73wvf83q4cjwzz99pdanbl8qpfawr69-mailcap-2.1.54']
```

### Why can't traditional Dockerfiles achieve bit-for-bit reproducibility?

1. **Base image drift**: tags like `python:3.12-slim` may point to updated image manifests over time.
2. **Non-deterministic build context**: file metadata, timestamps, and layer creation time can differ between builds.
3. **Network-time dependency resolution**: `pip install` pulls packages from live indexes at build time.
4. **Layer caching side effects**: Docker can reuse cached layers (`CACHED`), masking real rebuild differences.

### If you could redo Lab 2 with Nix, what would you do differently?

1. Build the application artifact with `default.nix` first, not with runtime `pip install` in Docker.
2. Keep one declarative source of truth for dependencies and runtime environment.
