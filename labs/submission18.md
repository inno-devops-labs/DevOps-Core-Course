# Lab 18 — Reproducible Builds with Nix

## Student / Repository

Repository: `DevOps-Core-Course`  
Branch: `feature/lab18`  
Application used: `app_python` from Lab 1 / Lab 2  
Application framework: FastAPI  
Application port: `5000`  
Deliverable file: `labs/submission18.md`

---

## 1. Nix Installation and Verification

### 1.1 Installation

Nix was installed using the Determinate Systems installer:

```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

After installation, the terminal session was restarted so that the `nix` command was available in `PATH`.

### 1.2 Verification commands

```bash
nix --version
nix run nixpkgs#hello
```

### 1.3 Verification output

```bash
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ nix --version
nix (Determinate Nix 3.18.1) 2.33.4
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ nix run nixpkgs#hello
Hello, world!
```

The command `nix run nixpkgs#hello` proves that Nix can fetch and run a package without installing it globally into the operating system. This is different from a traditional package manager because the package is stored in the Nix store and addressed by its dependency inputs.

---

## 2. Application Preparation

The Python application from Lab 1 / Lab 2 was copied into the Lab 18 directory:

```bash
mkdir -p labs/lab18/app_python
rsync -av --delete \
  --exclude 'venv' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '.ruff_cache' \
  --exclude '.coverage' \
  app_python/ labs/lab18/app_python/
```

The resulting directory is:

```text
labs/lab18/app_python
```

The application contains the following important files:

```text
app.py
requirements.txt
Dockerfile
config/config.json
```

The application is a FastAPI service. It exposes several endpoints, including:

| Endpoint | Purpose |
|---|---|
| `/` | Main application information endpoint |
| `/health` | Health check endpoint |
| `/visits` | Persistent visits counter endpoint |
| `/metrics` | Prometheus metrics endpoint |
| `/debug/error` | Error simulation endpoint |
| `/debug/slow` | Slow request simulation endpoint |

The original Python dependency file contains:

```text
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-json-logger>=4.0.0
prometheus-client==0.23.1
```

The original Lab 1 local development workflow was:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

This workflow is convenient, but it is not a complete reproducibility mechanism. It depends on the system Python version, pip behavior, external package indexes, transitive dependency resolution, system libraries, and local cache state.

---

# Task 1 — Build Reproducible Python App

## 3. Nix Derivation

File created:

```text
labs/lab18/app_python/default.nix
```

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    fastapi
    uvicorn
    python-json-logger
    prometheus-client
  ]);

  cleanSrc = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let
        name = baseNameOf path;
      in
        !(name == "result"
          || name == ".git"
          || name == "venv"
          || name == "__pycache__"
          || name == ".pytest_cache"
          || name == ".ruff_cache"
          || name == ".coverage");
  };
in

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";

  src = cleanSrc;
  format = "other";

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  dontBuild = true;
  doCheck = false;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/share/devops-info-service
    mkdir -p $out/bin

    cp app.py $out/share/devops-info-service/app.py

    if [ -d config ]; then
      cp -r config $out/share/devops-info-service/config
    fi

    makeWrapper ${pythonEnv}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --set PYTHONUNBUFFERED "1" \
      --set-default HOST "0.0.0.0" \
      --set-default PORT "5000" \
      --set-default DATA_DIR "/tmp/devops-info-service" \
      --set-default VISITS_FILE "/tmp/devops-info-service/visits" \
      --set-default CONFIG_FILE "$out/share/devops-info-service/config/config.json"

    runHook postInstall
  '';

  meta = {
    description = "DevOps Info Service built reproducibly with Nix";
    mainProgram = "devops-info-service";
  };
}
```

### 3.1 Explanation of fields

| Field / expression | Explanation |
|---|---|
| `pkgs ? import <nixpkgs> {}` | Imports the Nix package set. |
| `pythonEnv` | Creates a Python interpreter with all runtime dependencies required by the FastAPI application. |
| `fastapi`, `uvicorn`, `python-json-logger`, `prometheus-client` | Nix equivalents of the dependencies from `requirements.txt`. |
| `cleanSrc` | Removes local artifacts from the build input, including `venv`, caches, coverage files, `.git`, and `result`. |
| `pname` | Package name used in the Nix store path. |
| `version` | Application version used in the Nix store path. |
| `format = "other"` | Used because the app is a standalone script rather than a Python package with `setup.py` or `pyproject.toml`. |
| `nativeBuildInputs = [ pkgs.makeWrapper ]` | Allows the derivation to create a wrapper executable. |
| `dontBuild = true` | No compile step is required for this script-based app. |
| `doCheck = false` | Nix package checks are disabled for this lab build. |
| `installPhase` | Copies application files into `$out` and creates the runnable command. |
| `DATA_DIR=/tmp/devops-info-service` | Prevents permission issues because the original app defaults to `/data`. |
| `CONFIG_FILE=.../config/config.json` | Ensures the Nix-built app can load the copied configuration file. |

---

## 4. Building the Application with Nix

### 4.1 Build command

```bash
cd labs/lab18/app_python
nix-build
readlink -f result
```

### 4.2 Build output

```bash
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ nix-build
these 2 derivations will be built:
  /nix/store/vjyw2m15r2vzwjgwsqdrb7hhf7nan42g-python3-3.13.12-env.drv
  /nix/store/p1h09b426slz41ayiavkgsf46d3j92fi-devops-info-service-1.0.0.drv
these 88 paths will be fetched (12.7 MiB download, 595.8 MiB unpacked):
  /nix/store/4sabfgpxkbv6w3mvk0wil50vdi37m9r8-acl-2.3.2
  /nix/store/p2yk6q3bhcz1d0wlmk907ysj4l95ak7y-attr-2.5.2
  /nix/store/v8sa6r6q037ihghxfbwzjj4p59v2x0pv-bash-5.3p9
  /nix/store/4ndrbqby52admlb4gf6dq1jm7kngnkqx-bin
  /nix/store/rfp8lhk4dl9syfn64rwb3h3c73426p08-binutils-2.44
  /nix/store/jg0wzzd657xyhhss3mfqqa1iv5s9r75i-binutils-2.44-lib
  /nix/store/x7ikkplbrv5dlihy1bqq32gp6lilkval-binutils-wrapper-2.44
  /nix/store/fcqldgczpc2v9w9fg5nkibc6km2d2k70-builder.pl
  /nix/store/vi21p90v3kj509rx00r101xcqa6za76b-bzip2-1.0.8
  /nix/store/by6npbc13ly5a1zgsqghv7wv5bklyiny-bzip2-1.0.8-bin
  /nix/store/74sind1d6vf2bfwd7yklg8chsvzqxmmq-coreutils-9.10
  /nix/store/jc6kzjc5hp19570p0ihnvrnbc13jgm7f-die-hook
  /nix/store/355mp4ns4042sb5p51rx3ys4mlliiwc5-diffutils-3.12
  /nix/store/nvllv8vnli7kqa9vsx5r9pzchrglnj7x-ed-1.22.5
  /nix/store/z6z3ysqf5hy6mkk4gs5w8gyijmixpp4m-ensure-newer-sources-hook
  /nix/store/68kslg4wrhdxz24saw62fzyqi1kjgcfs-expand-response-params
  /nix/store/cr8mzl7cj4s5mriwrqnf9cvadw1iai5m-expat-2.7.4
  /nix/store/kjg8z2k0zvsczaij78803g7imlfm1vfb-file-5.45
  /nix/store/c89zz4vh8v9dbs8169wk8ahwxvrdxgm5-findutils-4.10.0
  /nix/store/gg169kyil5vhsg5aqcpagyhs8fwl0r5r-gawk-5.3.2
  /nix/store/lvwga6ivl1d4lnw0zis9ajs0rqx9gp4i-gcc-15.2.0
  /nix/store/ab3753m6i7isgvzphlar0a8xb84gl96i-gcc-15.2.0-lib
  /nix/store/hbnbbbx1n96v1waiiaid9fmg4li4i1kp-gcc-15.2.0-libgcc
  /nix/store/hb2bs5fg5wkm04x565737qd5nh2hy5nk-gcc-wrapper-15.2.0
  /nix/store/q9wz2k88ksbv9d90hw27hsr08b8jdc2d-gdbm-1.26-lib
  /nix/store/jms7zxzm7w1whczwny5m3gkgdjghmi2r-glibc-2.42-51
  /nix/store/9hm3jdm6kk4m4ppwjcxz4s1dsdvd6fin-glibc-2.42-51-bin
  /nix/store/h0ip0h6qp7kc2wm7mwjaglkxxbzmjri4-glibc-2.42-51-dev
  /nix/store/cynwj0s5x0c84hyi879isn8pdpf1iihm-gmp-6.3.0
  /nix/store/dlr3cc27i1mjkqcm9jlp5bjmb0n57q01-gmp-with-cxx-6.3.0
  /nix/store/ikx8300mbv3pjf4602dm1dv43wyafff1-gnu-config-2024-01-01
  /nix/store/h6hdbgkfh59np7bi7h8qa76pq27ixz8r-gnugrep-3.12
  /nix/store/1fvcxyhg3i5fvw0j4l8wmyml10dnvm7q-gnumake-4.4.1
  /nix/store/jpsqy47rdl0j0dvyyzb4kw8gqajw8nx0-gnused-4.9
  /nix/store/kvmqv1jqv4792rsihf7yjc5kwk3d8z6x-gnutar-1.35
  /nix/store/pnxiz967z73a45f4x7c1icldjaaqmlcp-gzip-1.14
  /nix/store/scabrfc47i7h73kfp4yn7vkw3qkxv8gk-isl-0.20
  /nix/store/8zgy79sw0zjwfcfp78p883hkkdw0pdzs-libffi-3.5.2
  /nix/store/1ga782ml07vy0h503ac4cin0h8d7q6yh-libidn2-2.3.8
  /nix/store/zfv59aslcf318vjkjs8zw855cdjcjdvq-libmpc-1.3.1
  /nix/store/p7jg95rzvfalb95k3mskk0jqxc9d724n-libunistring-1.4.1
  /nix/store/g01r8955ar8skb2ngly2sqf8f1vj9yck-libxcrypt-4.5.2
  /nix/store/pg99pd2gbwqs9y6z0q2hmx46m3hw9bns-linux-headers-6.18.7
  /nix/store/a6kd5v5x97jnyyzbmiild0m1ikn5yfmg-mailcap-2.1.54
  /nix/store/fv820x1rylda1kfsrwfhg09m4am3dvcq-make-binary-wrapper-hook
  /nix/store/qmbai9ywd5lvigv0rq1i8ap5pf4b67ym-make-shell-wrapper-hook
  /nix/store/gac1a2359c62vgvy13d2i3asi6v00vfa-mpdecimal-4.0.1
  /nix/store/sjlfsbd2lk4a1iva4vjjgvp4r1hga1xg-mpfr-4.2.2
  /nix/store/4zmr3iw5s719y5zz7h2dnym67x2i6n23-ncurses-6.6
  /nix/store/bga5xf95jaypy385hvxm4h3yxl3m1566-openssl-3.6.1
  /nix/store/ca84rbhb0bhwdcci7q51dad20nkbn9xc-patch-2.8
  /nix/store/sj3f6y3j8m1831l0gqm1bsk1f46jzkfd-patchelf-0.15.2
  /nix/store/ygdgqjzw03k8d05zq3pigzf67b62j7vs-pcre2-10.46
  /nix/store/phnk1lwy8xs0yrbrcs6l2mb9yr9c2knp-perl-5.42.0
  /nix/store/hn6lg997pwqz4d0yfkp2a9szcgq6xcfv-python-catch-conflicts-hook
  /nix/store/zdfdm33w83a487awxj7ag9gs3ms567in-python-imports-check-hook.sh
  /nix/store/wpvq4vqvr5xy7agk48c3adjq5mcpl8hg-python-namespaces-hook.sh
  /nix/store/683y88dafxmzpsfbjn93li883g0fc30h-python-remove-bin-bytecode-hook
  /nix/store/sdy6v11p0d9hwbyw4h0lyrs6aybxnxkw-python-remove-tests-dir-hook
  /nix/store/pzdalg368npikvpq4ncz2saxnz19v53k-python3-3.13.12
  /nix/store/dm9slx7cs5wrmg1b6k2s07jqdza2zgrn-python3.13-annotated-doc-0.0.4
  /nix/store/xf5xdzi3qa32kghy5mmsl0955m211w79-python3.13-annotated-types-0.7.0
  /nix/store/q8a34i008kavznc3f4z0yrh9brgkk38g-python3.13-anyio-4.12.1
  /nix/store/3ihdwzv8wwvrdpixgrb0xiwc09asq8jb-python3.13-asgiref-3.11.0
  /nix/store/bjl4laiaspy4d4n1w2qj8knhi1iv9agg-python3.13-click-8.3.1
  /nix/store/kk0h2y5x6xrcwbmiy96zw8pxnjyr5xgj-python3.13-fastapi-0.128.0
  /nix/store/7f2qrs85aid2awk28p4dwn12sq69i7xm-python3.13-h11-0.16.0
  /nix/store/srb6n37b2ah22a9zxpqj2igxm9h3wpvf-python3.13-idna-3.11
  /nix/store/09f6k42d8zfxiadj2rc02gfpnmhlja7y-python3.13-prometheus-client-0.24.1
  /nix/store/29jcxy6ib2m084wrip51dm6wx7bvs3ff-python3.13-pydantic-2.12.5
  /nix/store/67qy5jzdxi1j6i47qjw703far7a17bip-python3.13-pydantic-core-2.41.5
  /nix/store/clyvnawy913aqrg3hy15jjlr9b67kym5-python3.13-python-json-logger-4.0.0
  /nix/store/i49gayd3b0n79l62rwx7zziyixkkwvb5-python3.13-starlette-0.52.1
  /nix/store/llv9b1i1c1j8dzkakysmgn99nicjlcs1-python3.13-typing-extensions-4.15.0
  /nix/store/wpsa573cm2kslka6l3i9lvcdsghmsryf-python3.13-typing-inspection-0.4.2
  /nix/store/5y6rxrmvj4qxzbzyl3dslyx72x5ckcbk-python3.13-uvicorn-0.40.0
  /nix/store/qq90p0xx02ydaqv2gv28mx4qx2vk98fq-readline-8.3p3
  /nix/store/yvh4iy0ab95dq2p6cfm1xfvs6j9m0gxy-sqlite-3.51.2
  /nix/store/gvq9hvvnmkvrk27mba0jjjppj068z55x-stdenv-linux
  /nix/store/s2grcjv8pklvkajk3mkh75aja5dppx6z-stdenv-linux
  /nix/store/h15ranlgwagilr6ajd7ich6d896kf9zd-tzdata-2026a
  /nix/store/yshg9z9pkqqq1aidgrryn6hcmzgys2hs-update-autotools-gnu-config-scripts-hook
  /nix/store/safgshpdshpq8v8ww406szddpfws3vml-util-linux-minimal-2.41.3-lib
  /nix/store/6jnxjzpyvmxc3zny5jsfgsn07iqhzf53-wrap-python-hook
  /nix/store/vpxblivamvic1p5r5zny934jvg33m50r-xgcc-15.2.0-libgcc
  /nix/store/x8x0bp6q9x80lr3lljkj7xr4lx2495si-xz-5.8.2
  /nix/store/g6mlwdvpg92rchq352ll7jbi0pz7h43r-xz-5.8.2-bin
  /nix/store/2kdz3m7ic8w226pcvkz1dlg169v91p6a-zlib-1.3.2
copying path '/nix/store/683y88dafxmzpsfbjn93li883g0fc30h-python-remove-bin-bytecode-hook' from 'https://cache.nixos.org'...
copying path '/nix/store/sdy6v11p0d9hwbyw4h0lyrs6aybxnxkw-python-remove-tests-dir-hook' from 'https://cache.nixos.org'...
copying path '/nix/store/jc6kzjc5hp19570p0ihnvrnbc13jgm7f-die-hook' from 'https://install.determinate.systems'...
copying path '/nix/store/a6kd5v5x97jnyyzbmiild0m1ikn5yfmg-mailcap-2.1.54' from 'https://install.determinate.systems'...
copying path '/nix/store/h15ranlgwagilr6ajd7ich6d896kf9zd-tzdata-2026a' from 'https://install.determinate.systems'...
copying path '/nix/store/hbnbbbx1n96v1waiiaid9fmg4li4i1kp-gcc-15.2.0-libgcc' from 'https://install.determinate.systems'...
copying path '/nix/store/ikx8300mbv3pjf4602dm1dv43wyafff1-gnu-config-2024-01-01' from 'https://install.determinate.systems'...
copying path '/nix/store/vpxblivamvic1p5r5zny934jvg33m50r-xgcc-15.2.0-libgcc' from 'https://install.determinate.systems'...
copying path '/nix/store/p7jg95rzvfalb95k3mskk0jqxc9d724n-libunistring-1.4.1' from 'https://install.determinate.systems'...
copying path '/nix/store/pg99pd2gbwqs9y6z0q2hmx46m3hw9bns-linux-headers-6.18.7' from 'https://install.determinate.systems'...
copying path '/nix/store/4ndrbqby52admlb4gf6dq1jm7kngnkqx-bin' from 'https://cache.nixos.org'...
copying path '/nix/store/fcqldgczpc2v9w9fg5nkibc6km2d2k70-builder.pl' from 'https://cache.nixos.org'...
copying path '/nix/store/yshg9z9pkqqq1aidgrryn6hcmzgys2hs-update-autotools-gnu-config-scripts-hook' from 'https://install.determinate.systems'...
copying path '/nix/store/1ga782ml07vy0h503ac4cin0h8d7q6yh-libidn2-2.3.8' from 'https://install.determinate.systems'...
copying path '/nix/store/jms7zxzm7w1whczwny5m3gkgdjghmi2r-glibc-2.42-51' from 'https://install.determinate.systems'...
copying path '/nix/store/p2yk6q3bhcz1d0wlmk907ysj4l95ak7y-attr-2.5.2' from 'https://install.determinate.systems'...
copying path '/nix/store/v8sa6r6q037ihghxfbwzjj4p59v2x0pv-bash-5.3p9' from 'https://install.determinate.systems'...
copying path '/nix/store/vi21p90v3kj509rx00r101xcqa6za76b-bzip2-1.0.8' from 'https://install.determinate.systems'...
copying path '/nix/store/nvllv8vnli7kqa9vsx5r9pzchrglnj7x-ed-1.22.5' from 'https://install.determinate.systems'...
copying path '/nix/store/68kslg4wrhdxz24saw62fzyqi1kjgcfs-expand-response-params' from 'https://install.determinate.systems'...
copying path '/nix/store/cr8mzl7cj4s5mriwrqnf9cvadw1iai5m-expat-2.7.4' from 'https://install.determinate.systems'...
copying path '/nix/store/gg169kyil5vhsg5aqcpagyhs8fwl0r5r-gawk-5.3.2' from 'https://install.determinate.systems'...
copying path '/nix/store/ab3753m6i7isgvzphlar0a8xb84gl96i-gcc-15.2.0-lib' from 'https://install.determinate.systems'...
copying path '/nix/store/q9wz2k88ksbv9d90hw27hsr08b8jdc2d-gdbm-1.26-lib' from 'https://install.determinate.systems'...
copying path '/nix/store/9hm3jdm6kk4m4ppwjcxz4s1dsdvd6fin-glibc-2.42-51-bin' from 'https://install.determinate.systems'...
copying path '/nix/store/cynwj0s5x0c84hyi879isn8pdpf1iihm-gmp-6.3.0' from 'https://install.determinate.systems'...
copying path '/nix/store/1fvcxyhg3i5fvw0j4l8wmyml10dnvm7q-gnumake-4.4.1' from 'https://install.determinate.systems'...
copying path '/nix/store/jpsqy47rdl0j0dvyyzb4kw8gqajw8nx0-gnused-4.9' from 'https://install.determinate.systems'...
copying path '/nix/store/8zgy79sw0zjwfcfp78p883hkkdw0pdzs-libffi-3.5.2' from 'https://install.determinate.systems'...
copying path '/nix/store/g01r8955ar8skb2ngly2sqf8f1vj9yck-libxcrypt-4.5.2' from 'https://cache.nixos.org'...
copying path '/nix/store/gac1a2359c62vgvy13d2i3asi6v00vfa-mpdecimal-4.0.1' from 'https://install.determinate.systems'...
copying path '/nix/store/4zmr3iw5s719y5zz7h2dnym67x2i6n23-ncurses-6.6' from 'https://install.determinate.systems'...
copying path '/nix/store/bga5xf95jaypy385hvxm4h3yxl3m1566-openssl-3.6.1' from 'https://install.determinate.systems'...
copying path '/nix/store/ygdgqjzw03k8d05zq3pigzf67b62j7vs-pcre2-10.46' from 'https://install.determinate.systems'...
copying path '/nix/store/safgshpdshpq8v8ww406szddpfws3vml-util-linux-minimal-2.41.3-lib' from 'https://install.determinate.systems'...
copying path '/nix/store/4sabfgpxkbv6w3mvk0wil50vdi37m9r8-acl-2.3.2' from 'https://install.determinate.systems'...
copying path '/nix/store/by6npbc13ly5a1zgsqghv7wv5bklyiny-bzip2-1.0.8-bin' from 'https://install.determinate.systems'...
copying path '/nix/store/ca84rbhb0bhwdcci7q51dad20nkbn9xc-patch-2.8' from 'https://install.determinate.systems'...
copying path '/nix/store/x8x0bp6q9x80lr3lljkj7xr4lx2495si-xz-5.8.2' from 'https://install.determinate.systems'...
copying path '/nix/store/2kdz3m7ic8w226pcvkz1dlg169v91p6a-zlib-1.3.2' from 'https://install.determinate.systems'...
copying path '/nix/store/scabrfc47i7h73kfp4yn7vkw3qkxv8gk-isl-0.20' from 'https://install.determinate.systems'...
copying path '/nix/store/sjlfsbd2lk4a1iva4vjjgvp4r1hga1xg-mpfr-4.2.2' from 'https://install.determinate.systems'...
copying path '/nix/store/kvmqv1jqv4792rsihf7yjc5kwk3d8z6x-gnutar-1.35' from 'https://install.determinate.systems'...
copying path '/nix/store/qq90p0xx02ydaqv2gv28mx4qx2vk98fq-readline-8.3p3' from 'https://install.determinate.systems'...
copying path '/nix/store/pnxiz967z73a45f4x7c1icldjaaqmlcp-gzip-1.14' from 'https://install.determinate.systems'...
copying path '/nix/store/qmbai9ywd5lvigv0rq1i8ap5pf4b67ym-make-shell-wrapper-hook' from 'https://install.determinate.systems'...
copying path '/nix/store/h0ip0h6qp7kc2wm7mwjaglkxxbzmjri4-glibc-2.42-51-dev' from 'https://install.determinate.systems'...
copying path '/nix/store/h6hdbgkfh59np7bi7h8qa76pq27ixz8r-gnugrep-3.12' from 'https://install.determinate.systems'...
copying path '/nix/store/g6mlwdvpg92rchq352ll7jbi0pz7h43r-xz-5.8.2-bin' from 'https://install.determinate.systems'...
copying path '/nix/store/dlr3cc27i1mjkqcm9jlp5bjmb0n57q01-gmp-with-cxx-6.3.0' from 'https://install.determinate.systems'...
copying path '/nix/store/sj3f6y3j8m1831l0gqm1bsk1f46jzkfd-patchelf-0.15.2' from 'https://install.determinate.systems'...
copying path '/nix/store/zfv59aslcf318vjkjs8zw855cdjcjdvq-libmpc-1.3.1' from 'https://install.determinate.systems'...
copying path '/nix/store/jg0wzzd657xyhhss3mfqqa1iv5s9r75i-binutils-2.44-lib' from 'https://install.determinate.systems'...
copying path '/nix/store/kjg8z2k0zvsczaij78803g7imlfm1vfb-file-5.45' from 'https://install.determinate.systems'...
copying path '/nix/store/yvh4iy0ab95dq2p6cfm1xfvs6j9m0gxy-sqlite-3.51.2' from 'https://install.determinate.systems'...
copying path '/nix/store/74sind1d6vf2bfwd7yklg8chsvzqxmmq-coreutils-9.10' from 'https://install.determinate.systems'...
copying path '/nix/store/lvwga6ivl1d4lnw0zis9ajs0rqx9gp4i-gcc-15.2.0' from 'https://install.determinate.systems'...
copying path '/nix/store/355mp4ns4042sb5p51rx3ys4mlliiwc5-diffutils-3.12' from 'https://install.determinate.systems'...
copying path '/nix/store/c89zz4vh8v9dbs8169wk8ahwxvrdxgm5-findutils-4.10.0' from 'https://install.determinate.systems'...
copying path '/nix/store/phnk1lwy8xs0yrbrcs6l2mb9yr9c2knp-perl-5.42.0' from 'https://cache.nixos.org'...
copying path '/nix/store/rfp8lhk4dl9syfn64rwb3h3c73426p08-binutils-2.44' from 'https://install.determinate.systems'...
copying path '/nix/store/z6z3ysqf5hy6mkk4gs5w8gyijmixpp4m-ensure-newer-sources-hook' from 'https://cache.nixos.org'...
copying path '/nix/store/wpvq4vqvr5xy7agk48c3adjq5mcpl8hg-python-namespaces-hook.sh' from 'https://cache.nixos.org'...
copying path '/nix/store/s2grcjv8pklvkajk3mkh75aja5dppx6z-stdenv-linux' from 'https://install.determinate.systems'...
copying path '/nix/store/pzdalg368npikvpq4ncz2saxnz19v53k-python3-3.13.12' from 'https://install.determinate.systems'...
copying path '/nix/store/hn6lg997pwqz4d0yfkp2a9szcgq6xcfv-python-catch-conflicts-hook' from 'https://cache.nixos.org'...
copying path '/nix/store/zdfdm33w83a487awxj7ag9gs3ms567in-python-imports-check-hook.sh' from 'https://cache.nixos.org'...
copying path '/nix/store/dm9slx7cs5wrmg1b6k2s07jqdza2zgrn-python3.13-annotated-doc-0.0.4' from 'https://cache.nixos.org'...
copying path '/nix/store/bjl4laiaspy4d4n1w2qj8knhi1iv9agg-python3.13-click-8.3.1' from 'https://cache.nixos.org'...
copying path '/nix/store/xf5xdzi3qa32kghy5mmsl0955m211w79-python3.13-annotated-types-0.7.0' from 'https://cache.nixos.org'...
copying path '/nix/store/7f2qrs85aid2awk28p4dwn12sq69i7xm-python3.13-h11-0.16.0' from 'https://cache.nixos.org'...
copying path '/nix/store/srb6n37b2ah22a9zxpqj2igxm9h3wpvf-python3.13-idna-3.11' from 'https://cache.nixos.org'...
copying path '/nix/store/clyvnawy913aqrg3hy15jjlr9b67kym5-python3.13-python-json-logger-4.0.0' from 'https://cache.nixos.org'...
copying path '/nix/store/llv9b1i1c1j8dzkakysmgn99nicjlcs1-python3.13-typing-extensions-4.15.0' from 'https://cache.nixos.org'...
copying path '/nix/store/6jnxjzpyvmxc3zny5jsfgsn07iqhzf53-wrap-python-hook' from 'https://cache.nixos.org'...
copying path '/nix/store/q8a34i008kavznc3f4z0yrh9brgkk38g-python3.13-anyio-4.12.1' from 'https://cache.nixos.org'...
copying path '/nix/store/3ihdwzv8wwvrdpixgrb0xiwc09asq8jb-python3.13-asgiref-3.11.0' from 'https://cache.nixos.org'...
copying path '/nix/store/67qy5jzdxi1j6i47qjw703far7a17bip-python3.13-pydantic-core-2.41.5' from 'https://cache.nixos.org'...
copying path '/nix/store/wpsa573cm2kslka6l3i9lvcdsghmsryf-python3.13-typing-inspection-0.4.2' from 'https://cache.nixos.org'...
copying path '/nix/store/5y6rxrmvj4qxzbzyl3dslyx72x5ckcbk-python3.13-uvicorn-0.40.0' from 'https://cache.nixos.org'...
copying path '/nix/store/09f6k42d8zfxiadj2rc02gfpnmhlja7y-python3.13-prometheus-client-0.24.1' from 'https://cache.nixos.org'...
copying path '/nix/store/i49gayd3b0n79l62rwx7zziyixkkwvb5-python3.13-starlette-0.52.1' from 'https://cache.nixos.org'...
copying path '/nix/store/29jcxy6ib2m084wrip51dm6wx7bvs3ff-python3.13-pydantic-2.12.5' from 'https://cache.nixos.org'...
copying path '/nix/store/kk0h2y5x6xrcwbmiy96zw8pxnjyr5xgj-python3.13-fastapi-0.128.0' from 'https://cache.nixos.org'...
copying path '/nix/store/x7ikkplbrv5dlihy1bqq32gp6lilkval-binutils-wrapper-2.44' from 'https://install.determinate.systems'...
copying path '/nix/store/hb2bs5fg5wkm04x565737qd5nh2hy5nk-gcc-wrapper-15.2.0' from 'https://install.determinate.systems'...
copying path '/nix/store/fv820x1rylda1kfsrwfhg09m4am3dvcq-make-binary-wrapper-hook' from 'https://cache.nixos.org'...
copying path '/nix/store/gvq9hvvnmkvrk27mba0jjjppj068z55x-stdenv-linux' from 'https://install.determinate.systems'...
building '/nix/store/vjyw2m15r2vzwjgwsqdrb7hhf7nan42g-python3-3.13.12-env.drv'...
created 258 symlinks in user environment
building '/nix/store/p1h09b426slz41ayiavkgsf46d3j92fi-devops-info-service-1.0.0.drv'...
Sourcing python-remove-tests-dir-hook
Sourcing python-catch-conflicts-hook.sh
Sourcing python-remove-bin-bytecode-hook.sh
Sourcing python-imports-check-hook.sh
Using pythonImportsCheckPhase
Sourcing python-namespaces-hook
Running phase: unpackPhase
unpacking source archive /nix/store/y5jbz8nkamc725h6y3fwli37s2gypmy7-source
source root is source
setting SOURCE_DATE_EPOCH to timestamp 315619200 of file "source/tests/test_app.py"
Running phase: patchPhase
Running phase: updateAutotoolsGnuConfigScriptsPhase
Running phase: configurePhase
no configure script, doing nothing
Running phase: installPhase
Running phase: fixupPhase
shrinking RPATHs of ELF executables and libraries in /nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0
checking for references to /build/ in /nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0...
patching script interpreter paths in /nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0
stripping (with command strip and flags -S -p) in  /nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0/bin
Rewriting #! /nix/store/v8sa6r6q037ihghxfbwzjj4p59v2x0pv-bash-5.3p9/bin/bash -e to #!/nix/store/pzdalg368npikvpq4ncz2saxnz19v53k-python3-3.13.12
Executing pythonRemoveTestsDir
Finished executing pythonRemoveTestsDir
Running phase: pythonCatchConflictsPhase
Running phase: pythonRemoveBinBytecodePhase
Running phase: pythonImportsCheckPhase
Executing pythonImportsCheckPhase
/nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ readlink result
/nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0
```

---

## 5. Running the Nix-Built Application

### 5.1 Run command

```bash
./result/bin/devops-info-service
```

Alternative background run:

```bash
./result/bin/devops-info-service > /tmp/lab18-nix-app.log 2>&1 &
APP_PID=$!
sleep 3
```

### 5.2 Test commands

```bash
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/visits
```

```bash
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ ./result/bin/devops-info-service
{"asctime": "2026-04-27 20:46:26,152", "levelname": "INFO", "name": "__main__", "message": "Application starting...", "service": "devops-info-service", "version": "1.0.0", "hostname": "LAPTOP-JONCQBVT", "method": null, "path": null, "status_code": null, "client_ip": null, "duration_ms": null}
/nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0/share/devops-info-service/app.py:121: DeprecationWarning: 
        on_event is deprecated, use lifespan event handlers instead.

        Read more about it in the
        [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
        
  @app.on_event("startup")
{"asctime": "2026-04-27 20:46:26,194", "levelname": "INFO", "name": "__main__", "message": "visits_counter_ready", "service": "devops-info-service", "version": "1.0.0", "hostname": "LAPTOP-JONCQBVT", "method": null, "path": null, "status_code": null, "client_ip": null, "duration_ms": null}
{"asctime": "2026-04-27 20:46:35,881", "levelname": "INFO", "name": "__main__", "message": "http_request", "service": "devops-info-service", "version": "1.0.0", "hostname": "LAPTOP-JONCQBVT", "method": "GET", "path": "/health", "status_code": 200, "client_ip": "127.0.0.1", "duration_ms": 0}
INFO:     127.0.0.1:51114 - "GET /health HTTP/1.1" 200 OK
{"asctime": "2026-04-27 20:46:39,580", "levelname": "INFO", "name": "__main__", "message": "http_request", "service": "devops-info-service", "version": "1.0.0", "hostname": "LAPTOP-JONCQBVT", "method": "GET", "path": "/", "status_code": 200, "client_ip": "127.0.0.1", "duration_ms": 5}
INFO:     127.0.0.1:37148 - "GET / HTTP/1.1" 200 OK
{"asctime": "2026-04-27 20:46:44,246", "levelname": "INFO", "name": "__main__", "message": "http_request", "service": "devops-info-service", "version": "1.0.0", "hostname": "LAPTOP-JONCQBVT", "method": "GET", "path": "/visits", "status_code": 200, "client_ip": "127.0.0.1", "duration_ms": 0}
INFO:     127.0.0.1:37162 - "GET /visits HTTP/1.1" 200 OK
{"asctime": "2026-04-27 20:56:23,887", "levelname": "INFO", "name": "__main__", "message": "http_request", "service": "devops-info-service", "version": "1.0.0", "hostname": "LAPTOP-JONCQBVT", "method": "GET", "path": "/health", "status_code": 200, "client_ip": "127.0.0.1", "duration_ms": 3}
INFO:     127.0.0.1:48904 - "GET /health HTTP/1.1" 200 OK
```

### 5.3 Output

`/health`:

```json
{"status":"healthy","timestamp":"2026-04-27T17:46:35.880Z","uptime_seconds":9,"request_path":"/health"}
```

`/`:

```json
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"application":{"environment":"dev","log_level":"INFO"},"config":{"config_file":"/nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0/share/devops-info-service/config/config.json","loaded":true,"content":{"applicationName":"devops-info-service","environment":"local","settings":{"featureFlags":{"debugEndpoints":true,"showVisitsInRoot":true},"logLevel":"INFO"}}},"persistence":{"visits_file":"/tmp/devops-info-service/visits","visits_count":1},"system":{"hostname":"LAPTOP-JONCQBVT","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":8,"python_version":"3.13.12"},"runtime":{"uptime_seconds":13,"uptime_human":"0 hours, 0 minutes","current_time":"2026-04-27T17:46:39.579Z","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/visits","method":"GET","description":"Current visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}
```

`/visits`:

```json
{"visits":1,"visits_file":"/tmp/devops-info-service/visits"}
```

The application runs successfully from the Nix-built artifact located in the Nix store.

Screenshot evidence:

![](/docs/screenshots/nix_terminal.png)

---

## 6. Reproducibility Proof for the Nix Application Build

### 6.1 First build

```bash
nix-build
STORE_PATH_1=$(readlink -f result)
HASH_1=$(nix-hash --type sha256 result)

echo "Store path 1: $STORE_PATH_1"
echo "Hash 1: $HASH_1"
```

Output:

```bash
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ nix-build
/nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ STORE_PATH_1=$(readlink -f result)
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ HASH_1=$(nix-hash --type sha256 result)
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ echo "Store path 1: $STORE_PATH_1"
Store path 1: /nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ echo "Hash 1: $HASH_1"
Hash 1: fb91b434cfa968bc8d3eb7143d949872c77f120bcc34f4beb9f6a744a6044733
```

### 6.2 Second build

```bash
rm result
nix-build
STORE_PATH_2=$(readlink -f result)
HASH_2=$(nix-hash --type sha256 result)

echo "Store path 2: $STORE_PATH_2"
echo "Hash 2: $HASH_2"
```

Output:

```bash
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ rm result
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ nix-build
/nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ STORE_PATH_2=$(readlink -f result)
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ HASH_2=$(nix-hash --type sha256 result)
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ echo "Store path 2: $STORE_PATH_2"
Store path 2: /nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ echo "Hash 2: $HASH_2"
Hash 2: fb91b434cfa968bc8d3eb7143d949872c77f120bcc34f4beb9f6a744a6044733
```

### 6.3 Forced rebuild attempt

```bash
STORE_PATH=$(readlink -f result)
rm result
nix-store --delete "$STORE_PATH"
nix-build
STORE_PATH_3=$(readlink -f result)
HASH_3=$(nix-hash --type sha256 result)

echo "Store path after forced rebuild: $STORE_PATH_3"
echo "Hash after forced rebuild: $HASH_3"
```

Output:

```bash
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ STORE_PATH=$(readlink -f result)
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ rm result
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ nix-store --delete "$STORE_PATH"
finding garbage collector roots...
removing stale link from '/nix/var/nix/gcroots/auto/2jg3vvpm9x3gbg1akm8psx2l75ry21jq' to '/tmp/.tmpAB5FZi/profile'
removing stale link from '/nix/var/nix/gcroots/auto/411n8v04s3mf18s8y4gciyzkl8gn3m70' to '/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python/result'
removing stale link from '/nix/var/nix/gcroots/auto/izs9mxqjskyxg3p0d6d6jv8qpjq7av1q' to '/tmp/.tmpAB5FZi/profile-1-link'
removing stale link from '/nix/var/nix/gcroots/auto/fikhrpaq9vcv693nz4iwbx1zlb1w7dhl' to '/tmp/.tmpAB5FZi/profile-2-link'
0 store paths deleted, 0.0 KiB freed
error: Cannot delete path '/nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0' because it's referenced by the GC root '{censored}'.
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ nix-build
/nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ STORE_PATH_3=$(readlink -f result)
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ HASH_3=$(nix-hash --type sha256 result)
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ echo "Store path after forced rebuild: $STORE_PATH_3"
Store path after forced rebuild: /nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ echo "Hash after forced rebuild: $HASH_3"
Hash after forced rebuild: fb91b434cfa968bc8d3eb7143d949872c77f120bcc34f4beb9f6a744a6044733
```

### 6.4 Result

The store paths and hashes were identical across repeated builds:

```text
Store path 1: /nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0
Store path 2: /nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0
Store path after forced rebuild: /nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0

Hash 1: fb91b434cfa968bc8d3eb7143d949872c77f120bcc34f4beb9f6a744a6044733
Hash 2: fb91b434cfa968bc8d3eb7143d949872c77f120bcc34f4beb9f6a744a6044733
Hash after forced rebuild: fb91b434cfa968bc8d3eb7143d949872c77f120bcc34f4beb9f6a744a6044733
```

![](/docs/screenshots/block_6.png)

This demonstrates that the same Nix expression and source inputs produced the same output.

---

## 7. Nix Store Path Explanation

A Nix store path has this structure:

```text
/nix/store/<hash>-<package-name>-<version>
```

For this lab, the path looks like:

```text
/nix/store/5xa9zc9hps38wbrlllfr8wisn026ah3r-devops-info-service-1.0.0
```

The hash is derived from the build inputs. These inputs include the source code, declared dependencies, build instructions, and relevant parts of the dependency graph. If the inputs do not change, Nix can reuse the same store path. This is one of the key mechanisms that gives Nix stronger reproducibility guarantees than a normal virtual environment.

---

## 8. Lab 1 pip/venv vs Lab 18 Nix

| Aspect | Lab 1: pip + venv | Lab 18: Nix |
|---|---|---|
| Python version | Depends on system Python | Comes from the Nix package set |
| Dependency resolution | Performed by pip during installation | Declared in Nix expression |
| Transitive dependencies | Can drift unless fully locked | Part of the Nix dependency graph |
| Isolation | Virtual environment | Nix store and isolated build model |
| Output artifact | No content-addressed artifact | `/nix/store/...` output |
| Binary cache | No equivalent | Supported by Nix |
| Reproducibility | Approximate | Stronger and content-addressed |

### 8.1 Why `requirements.txt` is weaker than Nix

A `requirements.txt` file describes Python package requirements, but it does not fully describe the whole build and runtime environment. It does not pin the operating system, Python interpreter build, native libraries, compilers, or the full closure of dependencies in the same way that Nix does.

Even if direct Python dependencies are pinned, the wider environment can still vary between machines. For example, two developers may use different Python versions, different system libraries, different pip versions, or different package index states.

Nix provides stronger guarantees because the build environment is expressed declaratively and the result is stored in the Nix store using a hash-based path.

### 8.2 Reflection

If Nix had been used from Lab 1, the development and runtime environments would have been more consistent across machines. It would have reduced the chance of problems caused by different Python versions, missing system packages, or dependency resolution differences.

---

# Task 2 — Reproducible Docker Images with Nix

## 9. Original Lab 2 Dockerfile

File:

```text
labs/lab18/app_python/Dockerfile
```

```dockerfile
# syntax=docker/dockerfile:1.7

############################
# Stage 1: build wheels
############################
FROM python:3.13-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .

RUN python -m pip install --upgrade pip \
 && python -m pip wheel --wheel-dir /wheels -r requirements.txt


############################
# Stage 2: runtime
############################
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=5000 \
    DEBUG=FALSE

WORKDIR /app

RUN addgroup --system app \
 && adduser --system --ingroup app --home /home/app --shell /usr/sbin/nologin app

COPY --from=builder /wheels /wheels
COPY requirements.txt .

RUN python -m pip install --no-index --find-links=/wheels -r requirements.txt \
 && rm -rf /wheels

COPY app.py .

USER app

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health').read()" || exit 1

CMD ["python", "app.py"]
```

This Dockerfile follows good containerization practices: it uses a multi-stage build, builds wheels first, runs the app as a non-root user, exposes port `5000`, and defines a health check.

However, it is not bit-for-bit reproducible. The tag `python:3.13-slim` can point to different image digests over time, Docker image metadata includes timestamps, and the build relies on external package indexes and build-time package resolution.

---

## 10. Nix Docker Image

File created:

```text
labs/lab18/app_python/docker.nix
```

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in

pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [
    app
  ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];

    Env = [
      "HOST=0.0.0.0"
      "PORT=5000"
      "DATA_DIR=/tmp/devops-info-service"
      "VISITS_FILE=/tmp/devops-info-service/visits"
      "PYTHONUNBUFFERED=1"
    ];

    ExposedPorts = {
      "5000/tcp" = {};
    };

    WorkingDir = "/";
  };

  created = "1970-01-01T00:00:01Z";
}
```

### 10.1 Explanation of fields

| Field | Explanation |
|---|---|
| `app = import ./default.nix { inherit pkgs; }` | Reuses the Nix-built application from Task 1. |
| `pkgs.dockerTools.buildLayeredImage` | Builds a Docker-compatible image from Nix store paths. |
| `name` | Docker image name. |
| `tag` | Docker image tag. |
| `contents` | Store paths included in the image. |
| `config.Cmd` | Default command executed when the container starts. |
| `config.Env` | Runtime environment variables for the app. |
| `ExposedPorts` | Documents that the container listens on `5000/tcp`. |
| `created = "1970-01-01T00:00:01Z"` | Fixed timestamp for reproducible image metadata. |

The important reproducibility detail is the fixed `created` timestamp. Using `created = "now"` would make each image build different.

---

## 11. Building the Nix Docker Image

### 11.1 Commands

```bash
cd labs/lab18/app_python
nix-build docker.nix
sha256sum result
docker load < result
```

### 11.2 Output

```bash
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ nix-build docker.nix
these 8 derivations will be built:
  /nix/store/i3jqxs4br3g7iw3xw4zr4hl9wmric1rn-devops-info-service-1.0.0.drv
  /nix/store/6w2n9f1ik3l3ixnag5rrwps6kzm390fi-devops-info-service-nix-base.json.drv
  /nix/store/x7a1mhp10q7242w4xg1z0mj1zmli2dxr-devops-info-service-nix-customisation-layer.drv
  /nix/store/nn4ha5j056nabkq65k5h0yinb76hnjn1-excludePaths.drv
  /nix/store/zmjj57x941my0h030h0944kw9fay99c7-layers.json.drv
  /nix/store/7qb4msyi3wnapgrz4gj6ahp20hgafrwl-devops-info-service-nix-conf.json.drv
  /nix/store/pq553xk0391gy5j1sr64h98b1b0y6fdf-stream-devops-info-service-nix.drv
  /nix/store/2r2b4pmk81f1jl06qcfrk9vvalxwm3p8-devops-info-service-nix.tar.gz.drv
these 10 paths will be fetched (177.9 KiB download, 1.6 MiB unpacked):
  /nix/store/rcgsmh2mf1z8hwhfq55sca7kh14ivfdr-fakeroot-1.37.2
  /nix/store/7z1z178hg0h9i66l0c2vjpf7390mhi5p-getopt-1.1.6
  /nix/store/s4w1j16dj8wyriv1ljfypr9s1r39yjwp-jq-1.8.1
  /nix/store/fc13hvlj7541i1xmwdka7f61qicdzr5a-jq-1.8.1-bin
  /nix/store/plinh1rzkh83n4gfpkxl748zgaydpxll-jq-1.8.1-dev
  /nix/store/ryyvifgrdw8x6k0bnzdaikcvwvma7xn1-lndir-1.0.5
  /nix/store/m5sybb5r3yml6lfgvgdsw4rd3r6bq5h2-oniguruma-6.9.10-lib
  /nix/store/xng6fnhxgbsdpg1akx4d8p34cmabd729-pigz-2.8
  /nix/store/f4zbh1mb3lvfw967jiy7jhivisl92is3-stream
  /nix/store/x4phmg42irx037sd1qjbcj5lqfwm9bjn-stream
copying path '/nix/store/xng6fnhxgbsdpg1akx4d8p34cmabd729-pigz-2.8' from 'https://cache.nixos.org'...
copying path '/nix/store/f4zbh1mb3lvfw967jiy7jhivisl92is3-stream' from 'https://cache.nixos.org'...
copying path '/nix/store/m5sybb5r3yml6lfgvgdsw4rd3r6bq5h2-oniguruma-6.9.10-lib' from 'https://install.determinate.systems'...
copying path '/nix/store/7z1z178hg0h9i66l0c2vjpf7390mhi5p-getopt-1.1.6' from 'https://cache.nixos.org'...
copying path '/nix/store/ryyvifgrdw8x6k0bnzdaikcvwvma7xn1-lndir-1.0.5' from 'https://install.determinate.systems'...
building '/nix/store/i3jqxs4br3g7iw3xw4zr4hl9wmric1rn-devops-info-service-1.0.0.drv'...
Sourcing python-remove-tests-dir-hook
Sourcing python-catch-conflicts-hook.sh
Sourcing python-remove-bin-bytecode-hook.sh
Sourcing python-imports-check-hook.sh
Using pythonImportsCheckPhase
Sourcing python-namespaces-hook
Running phase: unpackPhase
unpacking source archive /nix/store/qmv3f9w8i123hkaznswxkyv5q1snhalc-source
source root is source
setting SOURCE_DATE_EPOCH to timestamp 315619200 of file "source/tests/test_app.py"
Running phase: patchPhase
Running phase: updateAutotoolsGnuConfigScriptsPhase
Running phase: configurePhase
no configure script, doing nothing
Running phase: installPhase
copying path '/nix/store/x4phmg42irx037sd1qjbcj5lqfwm9bjn-stream' from 'https://cache.nixos.org'...
Running phase: fixupPhase
shrinking RPATHs of ELF executables and libraries in /nix/store/a51vp7nkw69aisqqjf0nxvsqqsg3hnsf-devops-info-service-1.0.0
copying path '/nix/store/rcgsmh2mf1z8hwhfq55sca7kh14ivfdr-fakeroot-1.37.2' from 'https://cache.nixos.org'...
checking for references to /build/ in /nix/store/a51vp7nkw69aisqqjf0nxvsqqsg3hnsf-devops-info-service-1.0.0...
patching script interpreter paths in /nix/store/a51vp7nkw69aisqqjf0nxvsqqsg3hnsf-devops-info-service-1.0.0
stripping (with command strip and flags -S -p) in  /nix/store/a51vp7nkw69aisqqjf0nxvsqqsg3hnsf-devops-info-service-1.0.0/bin
Rewriting #! /nix/store/v8sa6r6q037ihghxfbwzjj4p59v2x0pv-bash-5.3p9/bin/bash -e to #!/nix/store/pzdalg368npikvpq4ncz2saxnz19v53k-python3-3.13.12
Executing pythonRemoveTestsDir
Finished executing pythonRemoveTestsDir
Running phase: pythonCatchConflictsPhase
Running phase: pythonRemoveBinBytecodePhase
Running phase: pythonImportsCheckPhase
Executing pythonImportsCheckPhase
building '/nix/store/6w2n9f1ik3l3ixnag5rrwps6kzm390fi-devops-info-service-nix-base.json.drv'...
building '/nix/store/x7a1mhp10q7242w4xg1z0mj1zmli2dxr-devops-info-service-nix-customisation-layer.drv'...
building '/nix/store/nn4ha5j056nabkq65k5h0yinb76hnjn1-excludePaths.drv'...
copying path '/nix/store/s4w1j16dj8wyriv1ljfypr9s1r39yjwp-jq-1.8.1' from 'https://install.determinate.systems'...
copying path '/nix/store/fc13hvlj7541i1xmwdka7f61qicdzr5a-jq-1.8.1-bin' from 'https://install.determinate.systems'...
copying path '/nix/store/plinh1rzkh83n4gfpkxl748zgaydpxll-jq-1.8.1-dev' from 'https://install.determinate.systems'...
building '/nix/store/zmjj57x941my0h030h0944kw9fay99c7-layers.json.drv'...
structuredAttrs is enabled
building '/nix/store/7qb4msyi3wnapgrz4gj6ahp20hgafrwl-devops-info-service-nix-conf.json.drv'...
{
  "architecture": "amd64",
  "config": {
    "Cmd": [
      "/nix/store/a51vp7nkw69aisqqjf0nxvsqqsg3hnsf-devops-info-service-1.0.0/bin/devops-info-service"
    ],
    "Env": [
      "HOST=0.0.0.0",
      "PORT=5000",
      "DATA_DIR=/tmp/devops-info-service",
      "VISITS_FILE=/tmp/devops-info-service/visits",
      "PYTHONUNBUFFERED=1"
    ],
    "ExposedPorts": {
      "5000/tcp": {}
    },
    "WorkingDir": "/"
  },
  "os": "linux",
  "store_dir": "/nix/store",
  "from_image": null,
  "store_layers": [
    [
      "/nix/store/a6kd5v5x97jnyyzbmiild0m1ikn5yfmg-mailcap-2.1.54"
    ],
    [
      "/nix/store/vpxblivamvic1p5r5zny934jvg33m50r-xgcc-15.2.0-libgcc"
    ],
    [
      "/nix/store/hbnbbbx1n96v1waiiaid9fmg4li4i1kp-gcc-15.2.0-libgcc"
    ],
    [
      "/nix/store/p7jg95rzvfalb95k3mskk0jqxc9d724n-libunistring-1.4.1"
    ],
    [
      "/nix/store/h15ranlgwagilr6ajd7ich6d896kf9zd-tzdata-2026a"
    ],
    [
      "/nix/store/1ga782ml07vy0h503ac4cin0h8d7q6yh-libidn2-2.3.8"
    ],
    [
      "/nix/store/jms7zxzm7w1whczwny5m3gkgdjghmi2r-glibc-2.42-51"
    ],
    [
      "/nix/store/8zgy79sw0zjwfcfp78p883hkkdw0pdzs-libffi-3.5.2"
    ],
    [
      "/nix/store/vi21p90v3kj509rx00r101xcqa6za76b-bzip2-1.0.8"
    ],
    [
      "/nix/store/2kdz3m7ic8w226pcvkz1dlg169v91p6a-zlib-1.3.2"
    ],
    [
      "/nix/store/gac1a2359c62vgvy13d2i3asi6v00vfa-mpdecimal-4.0.1"
    ],
    [
      "/nix/store/cr8mzl7cj4s5mriwrqnf9cvadw1iai5m-expat-2.7.4"
    ],
    [
      "/nix/store/q9wz2k88ksbv9d90hw27hsr08b8jdc2d-gdbm-1.26-lib"
    ],
    [
      "/nix/store/x8x0bp6q9x80lr3lljkj7xr4lx2495si-xz-5.8.2"
    ],
    [
      "/nix/store/v8sa6r6q037ihghxfbwzjj4p59v2x0pv-bash-5.3p9"
    ],
    [
      "/nix/store/safgshpdshpq8v8ww406szddpfws3vml-util-linux-minimal-2.41.3-lib"
    ],
    [
      "/nix/store/4zmr3iw5s719y5zz7h2dnym67x2i6n23-ncurses-6.6"
    ],
    [
      "/nix/store/qq90p0xx02ydaqv2gv28mx4qx2vk98fq-readline-8.3p3"
    ],
    [
      "/nix/store/yvh4iy0ab95dq2p6cfm1xfvs6j9m0gxy-sqlite-3.51.2"
    ],
    [
      "/nix/store/bga5xf95jaypy385hvxm4h3yxl3m1566-openssl-3.6.1"
    ],
    [
      "/nix/store/ab3753m6i7isgvzphlar0a8xb84gl96i-gcc-15.2.0-lib"
    ],
    [
      "/nix/store/pzdalg368npikvpq4ncz2saxnz19v53k-python3-3.13.12"
    ],
    [
      "/nix/store/dm9slx7cs5wrmg1b6k2s07jqdza2zgrn-python3.13-annotated-doc-0.0.4"
    ],
    [
      "/nix/store/xf5xdzi3qa32kghy5mmsl0955m211w79-python3.13-annotated-types-0.7.0"
    ],
    [
      "/nix/store/clyvnawy913aqrg3hy15jjlr9b67kym5-python3.13-python-json-logger-4.0.0"
    ],
    [
      "/nix/store/7f2qrs85aid2awk28p4dwn12sq69i7xm-python3.13-h11-0.16.0"
    ],
    [
      "/nix/store/llv9b1i1c1j8dzkakysmgn99nicjlcs1-python3.13-typing-extensions-4.15.0"
    ],
    [
      "/nix/store/wpsa573cm2kslka6l3i9lvcdsghmsryf-python3.13-typing-inspection-0.4.2"
    ],
    [
      "/nix/store/3ihdwzv8wwvrdpixgrb0xiwc09asq8jb-python3.13-asgiref-3.11.0"
    ],
    [
      "/nix/store/srb6n37b2ah22a9zxpqj2igxm9h3wpvf-python3.13-idna-3.11"
    ],
    [
      "/nix/store/bjl4laiaspy4d4n1w2qj8knhi1iv9agg-python3.13-click-8.3.1"
    ],
    [
      "/nix/store/09f6k42d8zfxiadj2rc02gfpnmhlja7y-python3.13-prometheus-client-0.24.1"
    ],
    [
      "/nix/store/5y6rxrmvj4qxzbzyl3dslyx72x5ckcbk-python3.13-uvicorn-0.40.0"
    ],
    [
      "/nix/store/q8a34i008kavznc3f4z0yrh9brgkk38g-python3.13-anyio-4.12.1"
    ],
    [
      "/nix/store/i49gayd3b0n79l62rwx7zziyixkkwvb5-python3.13-starlette-0.52.1"
    ],
    [
      "/nix/store/67qy5jzdxi1j6i47qjw703far7a17bip-python3.13-pydantic-core-2.41.5"
    ],
    [
      "/nix/store/29jcxy6ib2m084wrip51dm6wx7bvs3ff-python3.13-pydantic-2.12.5"
    ],
    [
      "/nix/store/kk0h2y5x6xrcwbmiy96zw8pxnjyr5xgj-python3.13-fastapi-0.128.0"
    ],
    [
      "/nix/store/ifvfvlm2j46h0hdn8mkw585m6j1r40gr-python3-3.13.12-env"
    ],
    [
      "/nix/store/a51vp7nkw69aisqqjf0nxvsqqsg3hnsf-devops-info-service-1.0.0"
    ]
  ],
  "customisation_layer": "/nix/store/rq58y4ix8calf3wwjahlap3b85pdzl51-devops-info-service-nix-customisation-layer",
  "repo_tag": "devops-info-service-nix:1.0.0",
  "created": "1970-01-01T00:00:01+00:00",
  "mtime": "1970-01-01T00:00:01+00:00",
  "uid": "0",
  "gid": "0",
  "uname": "root",
  "gname": "root"
}
building '/nix/store/pq553xk0391gy5j1sr64h98b1b0y6fdf-stream-devops-info-service-nix.drv'...
building '/nix/store/2r2b4pmk81f1jl06qcfrk9vvalxwm3p8-devops-info-service-nix.tar.gz.drv'...
No 'fromImage' provided
Creating layer 1 from paths: ['/nix/store/a6kd5v5x97jnyyzbmiild0m1ikn5yfmg-mailcap-2.1.54']
Creating layer 2 from paths: ['/nix/store/vpxblivamvic1p5r5zny934jvg33m50r-xgcc-15.2.0-libgcc']
Creating layer 3 from paths: ['/nix/store/hbnbbbx1n96v1waiiaid9fmg4li4i1kp-gcc-15.2.0-libgcc']
Creating layer 4 from paths: ['/nix/store/p7jg95rzvfalb95k3mskk0jqxc9d724n-libunistring-1.4.1']
Creating layer 5 from paths: ['/nix/store/h15ranlgwagilr6ajd7ich6d896kf9zd-tzdata-2026a']
Creating layer 6 from paths: ['/nix/store/1ga782ml07vy0h503ac4cin0h8d7q6yh-libidn2-2.3.8']
Creating layer 7 from paths: ['/nix/store/jms7zxzm7w1whczwny5m3gkgdjghmi2r-glibc-2.42-51']
Creating layer 8 from paths: ['/nix/store/8zgy79sw0zjwfcfp78p883hkkdw0pdzs-libffi-3.5.2']
Creating layer 9 from paths: ['/nix/store/vi21p90v3kj509rx00r101xcqa6za76b-bzip2-1.0.8']
Creating layer 10 from paths: ['/nix/store/2kdz3m7ic8w226pcvkz1dlg169v91p6a-zlib-1.3.2']
Creating layer 11 from paths: ['/nix/store/gac1a2359c62vgvy13d2i3asi6v00vfa-mpdecimal-4.0.1']
Creating layer 12 from paths: ['/nix/store/cr8mzl7cj4s5mriwrqnf9cvadw1iai5m-expat-2.7.4']
Creating layer 13 from paths: ['/nix/store/q9wz2k88ksbv9d90hw27hsr08b8jdc2d-gdbm-1.26-lib']
Creating layer 14 from paths: ['/nix/store/x8x0bp6q9x80lr3lljkj7xr4lx2495si-xz-5.8.2']
Creating layer 15 from paths: ['/nix/store/v8sa6r6q037ihghxfbwzjj4p59v2x0pv-bash-5.3p9']
Creating layer 16 from paths: ['/nix/store/safgshpdshpq8v8ww406szddpfws3vml-util-linux-minimal-2.41.3-lib']
Creating layer 17 from paths: ['/nix/store/4zmr3iw5s719y5zz7h2dnym67x2i6n23-ncurses-6.6']
Creating layer 18 from paths: ['/nix/store/qq90p0xx02ydaqv2gv28mx4qx2vk98fq-readline-8.3p3']
Creating layer 19 from paths: ['/nix/store/yvh4iy0ab95dq2p6cfm1xfvs6j9m0gxy-sqlite-3.51.2']
Creating layer 20 from paths: ['/nix/store/bga5xf95jaypy385hvxm4h3yxl3m1566-openssl-3.6.1']
Creating layer 21 from paths: ['/nix/store/ab3753m6i7isgvzphlar0a8xb84gl96i-gcc-15.2.0-lib']
Creating layer 22 from paths: ['/nix/store/pzdalg368npikvpq4ncz2saxnz19v53k-python3-3.13.12']
Creating layer 23 from paths: ['/nix/store/dm9slx7cs5wrmg1b6k2s07jqdza2zgrn-python3.13-annotated-doc-0.0.4']
Creating layer 24 from paths: ['/nix/store/xf5xdzi3qa32kghy5mmsl0955m211w79-python3.13-annotated-types-0.7.0']
Creating layer 25 from paths: ['/nix/store/clyvnawy913aqrg3hy15jjlr9b67kym5-python3.13-python-json-logger-4.0.0']
Creating layer 26 from paths: ['/nix/store/7f2qrs85aid2awk28p4dwn12sq69i7xm-python3.13-h11-0.16.0']
Creating layer 27 from paths: ['/nix/store/llv9b1i1c1j8dzkakysmgn99nicjlcs1-python3.13-typing-extensions-4.15.0']
Creating layer 28 from paths: ['/nix/store/wpsa573cm2kslka6l3i9lvcdsghmsryf-python3.13-typing-inspection-0.4.2']
Creating layer 29 from paths: ['/nix/store/3ihdwzv8wwvrdpixgrb0xiwc09asq8jb-python3.13-asgiref-3.11.0']
Creating layer 30 from paths: ['/nix/store/srb6n37b2ah22a9zxpqj2igxm9h3wpvf-python3.13-idna-3.11']
Creating layer 31 from paths: ['/nix/store/bjl4laiaspy4d4n1w2qj8knhi1iv9agg-python3.13-click-8.3.1']
Creating layer 32 from paths: ['/nix/store/09f6k42d8zfxiadj2rc02gfpnmhlja7y-python3.13-prometheus-client-0.24.1']
Creating layer 33 from paths: ['/nix/store/5y6rxrmvj4qxzbzyl3dslyx72x5ckcbk-python3.13-uvicorn-0.40.0']
Creating layer 34 from paths: ['/nix/store/q8a34i008kavznc3f4z0yrh9brgkk38g-python3.13-anyio-4.12.1']
Creating layer 35 from paths: ['/nix/store/i49gayd3b0n79l62rwx7zziyixkkwvb5-python3.13-starlette-0.52.1']
Creating layer 36 from paths: ['/nix/store/67qy5jzdxi1j6i47qjw703far7a17bip-python3.13-pydantic-core-2.41.5']
Creating layer 37 from paths: ['/nix/store/29jcxy6ib2m084wrip51dm6wx7bvs3ff-python3.13-pydantic-2.12.5']
Creating layer 38 from paths: ['/nix/store/kk0h2y5x6xrcwbmiy96zw8pxnjyr5xgj-python3.13-fastapi-0.128.0']
Creating layer 39 from paths: ['/nix/store/ifvfvlm2j46h0hdn8mkw585m6j1r40gr-python3-3.13.12-env']
Creating layer 40 from paths: ['/nix/store/a51vp7nkw69aisqqjf0nxvsqqsg3hnsf-devops-info-service-1.0.0']
Creating layer 41 with customisation...
Adding manifests...
Done.
/nix/store/s9jhj6kl33bczqh78va9f3vl5xhcsn90-devops-info-service-nix.tar.gz
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ sha256sum result
8be82642568261ba08a0d8a2829fc95e0001cf01793f3d482de1159511a0ad6c  result
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ docker load < result
74bdc670638f: Loading layer  133.1kB/133.1kB
4d0baca456df: Loading layer  204.8kB/204.8kB
ba3238764a6a: Loading layer  204.8kB/204.8kB
3e8a64ab6b98: Loading layer  2.089MB/2.089MB
686cfd573905: Loading layer  2.939MB/2.939MB
090d18caa919: Loading layer  419.8kB/419.8kB
73e59db2596b: Loading layer   35.7MB/35.7MB
1df0d523d3f9: Loading layer  81.92kB/81.92kB
f45efbd0efa5: Loading layer  102.4kB/102.4kB
f746e7c908e0: Loading layer  143.4kB/143.4kB
a235908c7bdb: Loading layer  235.5kB/235.5kB
778199619ed4: Loading layer  317.4kB/317.4kB
c08f53782fdc: Loading layer  491.5kB/491.5kB
780946031cf0: Loading layer  901.1kB/901.1kB
7e3b702898fd: Loading layer  1.894MB/1.894MB
eeb8c7b1bb06: Loading layer  2.079MB/2.079MB
a841feaf52bc: Loading layer  5.284MB/5.284MB
a704927ce1cd: Loading layer    512kB/512kB
87ef6b272139: Loading layer  5.868MB/5.868MB
964c374eb729: Loading layer  9.318MB/9.318MB
6edaba3a8285: Loading layer  10.34MB/10.34MB
d72ac9537eb6: Loading layer  116.7MB/116.7MB
566925d0b727: Loading layer   51.2kB/51.2kB
ea2ee9e0a9ad: Loading layer  143.4kB/143.4kB
42d205810580: Loading layer  204.8kB/204.8kB
d94027967504: Loading layer  358.4kB/358.4kB
5ac0c19a281e: Loading layer  532.5kB/532.5kB
cf889b42edbf: Loading layer  174.1kB/174.1kB
693f01744406: Loading layer  307.2kB/307.2kB
582d931390a1: Loading layer  1.004MB/1.004MB
70943beecf6a: Loading layer  1.393MB/1.393MB
11d10bf164f6: Loading layer  921.6kB/921.6kB
c91dfed8623a: Loading layer  1.085MB/1.085MB
704500673a9c: Loading layer  2.017MB/2.017MB
cfa804e3b3e9: Loading layer  1.188MB/1.188MB
5f3ef610fb38: Loading layer  5.622MB/5.622MB
b62e7ec0c04c: Loading layer  6.205MB/6.205MB
d0b9edcbb993: Loading layer  1.956MB/1.956MB
4cfd24dcda95: Loading layer  389.1kB/389.1kB
13ee2208ac5e: Loading layer  30.72kB/30.72kB
f1df74a6b838: Loading layer  10.24kB/10.24kB
Loaded image: devops-info-service-nix:1.0.0
```

---

## 12. Running the Nix Docker Container

### 12.1 Commands

```bash
docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0
curl http://127.0.0.1:5001/health
curl http://127.0.0.1:5001/visits
```

### 12.2 Output

```bash
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0
0d965f27e5d71a1375ad71fcec913c3ed0e8a2f1672896f5c8b97abff8177193
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ curl http://127.0.0.1:5001/health
{"status":"healthy","timestamp":"2026-04-27T17:52:26.500Z","uptime_seconds":3,"request_path":"/health"}
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ curl http://127.0.0.1:5001/visits:5001/visits
{"visits":1,"visits_file":"/tmp/devops-info-service/visits"}
```

Screenshot evidence:

![](/docs/screenshots/block_12.png)

---

## 13. Side-by-Side Container Test

The traditional Lab 2 Docker image and the Nix-built Docker image were run at the same time.

### 13.1 Commands

```bash
docker stop lab2-container nix-container 2>/dev/null || true
docker rm lab2-container nix-container 2>/dev/null || true

docker build --no-cache -t lab2-app:v1 labs/lab18/app_python

docker run -d -p 5000:5000 --name lab2-container lab2-app:v1
docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0

curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5001/health

docker ps
```

### 13.2 Output

```bash
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ docker stop lab2-container nix-container 2>/dev/null || true
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ docker rm lab2-container nix-container 2>/dev/null || true
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ docker run -d -p 5000:5000 --name lab2-container lab2-app:v1
02cc4dbac22f9c356ba055c50cad0f8a59e78d0d3fbd00df736db44c3ec36145
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0
a803b9c9c2fa09331a664519073ce615aa6f81750d7233de0e03c9a07a32d601
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ curl http://127.0.0.1:5000/health
{"status":"healthy","timestamp":"2026-04-27T17:56:23.885Z","uptime_seconds":597,"request_path":"/health"}
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps$ curl http://127.0.0.1:5001/health.1:5001/health
{"status":"healthy","timestamp":"2026-04-27T17:56:27.697Z","uptime_seconds":6,"request_path":"/health"}
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ docker ps
CONTAINER ID   IMAGE                           COMMAND                  CREATED          STATUS          PORTS                                         NAMES
a803b9c9c2fa   devops-info-service-nix:1.0.0   "/nix/store/a51vp7nk…"   13 seconds ago   Up 12 seconds   0.0.0.0:5001->5000/tcp, [::]:5001->5000/tcp   nix-container
```

![](/docs/screenshots/block_13.png)

Both containers returned a healthy response, which shows that the traditional Docker image and the Nix-built image run the same application behavior.

---

## 14. Docker Reproducibility Comparison

### 14.1 Traditional Dockerfile builds

```bash
docker build --no-cache -t lab2-app:v1 labs/lab18/app_python
docker inspect lab2-app:v1 --format '{{.Created}}'
docker save lab2-app:v1 | sha256sum

sleep 5

docker build --no-cache -t lab2-app:v2 labs/lab18/app_python
docker inspect lab2-app:v2 --format '{{.Created}}'
docker save lab2-app:v2 | sha256sum
```

Output:

```bash
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ docker build --no-cache -t lab2-app:v1 labs/lab18/app_python
[+] Building 21.5s (18/18) FINISHED                                         docker:default
 => [internal] load build definition from Dockerfile                                  0.0s
 => => transferring dockerfile: 1.33kB                                                0.0s
 => resolve image config for docker-image://docker.io/docker/dockerfile:1.7           2.0s
 => [auth] docker/dockerfile:pull token for registry-1.docker.io                      0.0s
 => CACHED docker-image://docker.io/docker/dockerfile:1.7@sha256:a57df69d0ea827fb726  0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim                   0.0s
 => [internal] load .dockerignore                                                     0.0s
 => => transferring context: 2B                                                       0.0s
 => [internal] load build context                                                     0.1s
 => => transferring context: 11.94kB                                                  0.0s
 => [builder 1/4] FROM docker.io/library/python:3.13-slim                             0.0s
 => CACHED [builder 2/4] WORKDIR /build                                               0.0s
 => CACHED [runtime 2/7] WORKDIR /app                                                 0.0s
 => [runtime 3/7] RUN addgroup --system app  && adduser --system --ingroup app --hom  0.5s
 => [builder 3/4] COPY requirements.txt .                                             0.0s
 => [builder 4/4] RUN python -m pip install --upgrade pip  && python -m pip wheel -  14.3s
 => [runtime 4/7] COPY --from=builder /wheels /wheels                                 0.1s 
 => [runtime 5/7] COPY requirements.txt .                                             0.0s
 => [runtime 6/7] RUN python -m pip install --no-index --find-links=/wheels -r requi  3.1s
 => [runtime 7/7] COPY app.py .                                                       0.0s
 => exporting to image                                                                0.2s
 => => exporting layers                                                               0.2s
 => => writing image sha256:5b7662b944deda296ac2072562ae55f535ea4b5beee0f6272f33e4b7  0.0s
 => => naming to docker.io/library/lab2-app:v1                                        0.0s
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ docker inspect lab2-app:v1 --format '{{.Created}}'
2026-04-27T17:54:17.877251767Z
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ docker save lab2-app:v1 | sha256sum
3bde82ab45e90f23f5efaa2acf8eefde9d1999248f767e55f3b0a3ba0b34c3ab  -
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ sleep 5
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ docker build --no-cache -t lab2-app:v2 labs/lab18/app_python
[+] Building 17.9s (17/17) FINISHED                                         docker:default
 => [internal] load build definition from Dockerfile                                  0.0s
 => => transferring dockerfile: 1.33kB                                                0.0s
 => resolve image config for docker-image://docker.io/docker/dockerfile:1.7           0.7s
 => CACHED docker-image://docker.io/docker/dockerfile:1.7@sha256:a57df69d0ea827fb726  0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim                   0.0s
 => [internal] load .dockerignore                                                     0.0s
 => => transferring context: 2B                                                       0.0s
 => [internal] load build context                                                     0.0s
 => => transferring context: 63B                                                      0.0s
 => [builder 1/4] FROM docker.io/library/python:3.13-slim                             0.0s
 => CACHED [builder 2/4] WORKDIR /build                                               0.0s
 => CACHED [runtime 2/7] WORKDIR /app                                                 0.0s
 => [runtime 3/7] RUN addgroup --system app  && adduser --system --ingroup app --hom  0.4s
 => [builder 3/4] COPY requirements.txt .                                             0.0s
 => [builder 4/4] RUN python -m pip install --upgrade pip  && python -m pip wheel -  13.1s
 => [runtime 4/7] COPY --from=builder /wheels /wheels                                 0.0s 
 => [runtime 5/7] COPY requirements.txt .                                             0.0s 
 => [runtime 6/7] RUN python -m pip install --no-index --find-links=/wheels -r requi  3.3s
 => [runtime 7/7] COPY app.py .                                                       0.0s
 => exporting to image                                                                0.2s
 => => exporting layers                                                               0.2s
 => => writing image sha256:173ad58323c56faf819d042b6884cefa896d3042dfe8f40f52c57a3a  0.0s
 => => naming to docker.io/library/lab2-app:v2                                        0.0s
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ docker inspect lab2-app:v2 --format '{{.Created}}'
2026-04-27T17:55:02.783172177Z
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ docker save lab2-app:v2 | sha256sum
cc9cecf783ad6c1caa3a4756558fdac992bd8c91faa116cc4cdfb672d51e3796  -
```

Observation:

The two traditional Docker builds produced different timestamps and different saved image hashes. This shows that the Dockerfile workflow is not bit-for-bit reproducible even when the source code and Dockerfile are unchanged.

### 14.2 Nix Docker builds

```bash
cd labs/lab18/app_python

rm -f result
nix-build docker.nix
sha256sum result

rm -f result
nix-build docker.nix
sha256sum result
```

Output:

```bash
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ cd labs/lab18/app_python
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ rm -f result
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ nix-build docker.nix
/nix/store/s9jhj6kl33bczqh78va9f3vl5xhcsn90-devops-info-service-nix.tar.gz
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ sha256sum result
8be82642568261ba08a0d8a2829fc95e0001cf01793f3d482de1159511a0ad6c  result
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ rm -f result
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ nix-build docker.nix
/nix/store/s9jhj6kl33bczqh78va9f3vl5xhcsn90-devops-info-service-nix.tar.gz
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/labs/lab18/app_python$ sha256sum result
8be82642568261ba08a0d8a2829fc95e0001cf01793f3d482de1159511a0ad6c  result
```

Observation:

The two Nix Docker builds produced identical hashes. This shows that the Nix-generated Docker image is reproducible when the inputs do not change.

---

## 15. Image Size Comparison

### 15.1 Command

```bash
docker images | grep -E "lab2-app|devops-info-service-nix"
```

### 15.2 Output

```bash
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ docker images | grep -E "lab2-app|devops-info-service-nix"
lab2-app                         v2               173ad58323c5   About a minute ago   166MB
lab2-app                         v1               5b7662b944de   2 minutes ago        166MB
devops-info-service-nix          1.0.0            fe19294e58dc   56 years ago         207MB
```

### 15.3 Comparison table

| Metric | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
|---|---:|---:|
| Image size | TODO: paste size | TODO: paste size |
| Reproducibility | Different hashes between builds | Identical hashes between builds |
| Base image | `python:3.13-slim` | No traditional base image |
| Timestamp behavior | Build timestamp changes | Fixed timestamp |
| Dependency model | pip inside Docker build | Nix closure |
| Caching model | Docker layers | Nix content-addressed store |
| Runtime command | `python app.py` | Nix wrapper command |

The Nix image is assembled from the application closure rather than a mutable base image tag. This improves reproducibility and makes the runtime dependency set more explicit.

---

## 16. Docker History Comparison

### 16.1 Traditional Docker image

```bash
docker history lab2-app:v1
```

Output:

```bash
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ docker history lab2-app:v1
IMAGE          CREATED         CREATED BY                                      SIZE      COMMENT
5b7662b944de   2 minutes ago   CMD ["python" "app.py"]                         0B        buildkit.dockerfile.v0
<missing>      2 minutes ago   HEALTHCHECK &{["CMD-SHELL" "python -c \"impo…   0B        buildkit.dockerfile.v0
<missing>      2 minutes ago   EXPOSE map[5000/tcp:{}]                         0B        buildkit.dockerfile.v0
<missing>      2 minutes ago   USER app                                        0B        buildkit.dockerfile.v0
<missing>      2 minutes ago   COPY app.py . # buildkit                        11.8kB    buildkit.dockerfile.v0
<missing>      2 minutes ago   RUN /bin/sh -c python -m pip install --no-in…   38.6MB    buildkit.dockerfile.v0
<missing>      2 minutes ago   COPY requirements.txt . # buildkit              99B       buildkit.dockerfile.v0
<missing>      2 minutes ago   COPY /wheels /wheels # buildkit                 9.59MB    buildkit.dockerfile.v0
<missing>      2 minutes ago   RUN /bin/sh -c addgroup --system app  && add…   4.3kB     buildkit.dockerfile.v0
<missing>      2 months ago    WORKDIR /app                                    0B        buildkit.dockerfile.v0
<missing>      2 months ago    ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFER…   0B        buildkit.dockerfile.v0
<missing>      3 months ago    CMD ["python3"]                                 0B        buildkit.dockerfile.v0
<missing>      3 months ago    RUN /bin/sh -c set -eux;  for src in idle3 p…   36B       buildkit.dockerfile.v0
<missing>      3 months ago    RUN /bin/sh -c set -eux;   savedAptMark="$(a…   35.2MB    buildkit.dockerfile.v0
<missing>      3 months ago    ENV PYTHON_SHA256=16ede7bb7cdbfa895d11b0642f…   0B        buildkit.dockerfile.v0
<missing>      3 months ago    ENV PYTHON_VERSION=3.13.11                      0B        buildkit.dockerfile.v0
<missing>      3 months ago    ENV GPG_KEY=7169605F62C751356D054A26A821E680…   0B        buildkit.dockerfile.v0
<missing>      3 months ago    RUN /bin/sh -c set -eux;  apt-get update;  a…   3.81MB    buildkit.dockerfile.v0
<missing>      3 months ago    ENV PATH=/usr/local/bin:/usr/local/sbin:/usr…   0B        buildkit.dockerfile.v0
<missing>      3 months ago    # debian.sh --arch 'amd64' out/ 'trixie' '@1…   78.6MB    debuerreotype 0.17
```

### 16.2 Nix Docker image

```bash
docker history devops-info-service-nix:1.0.0
```

Output:

```bash
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course$ docker history devops-info-service-nix:1.0.0
IMAGE          CREATED   CREATED BY   SIZE      COMMENT
fe19294e58dc   N/A                    414B      store paths: ['/nix/store/rq58y4ix8calf3wwjahlap3b85pdzl51-devops-info-service-nix-customisation-layer']
<missing>      N/A                    12.7kB    store paths: ['/nix/store/a51vp7nkw69aisqqjf0nxvsqqsg3hnsf-devops-info-service-1.0.0']
<missing>      N/A                    215kB     store paths: ['/nix/store/ifvfvlm2j46h0hdn8mkw585m6j1r40gr-python3-3.13.12-env']
<missing>      N/A                    1.65MB    store paths: ['/nix/store/kk0h2y5x6xrcwbmiy96zw8pxnjyr5xgj-python3.13-fastapi-0.128.0']
<missing>      N/A                    5.6MB     store paths: ['/nix/store/29jcxy6ib2m084wrip51dm6wx7bvs3ff-python3.13-pydantic-2.12.5']
<missing>      N/A                    5.58MB    store paths: ['/nix/store/67qy5jzdxi1j6i47qjw703far7a17bip-python3.13-pydantic-core-2.41.5']
<missing>      N/A                    972kB     store paths: ['/nix/store/i49gayd3b0n79l62rwx7zziyixkkwvb5-python3.13-starlette-0.52.1']
<missing>      N/A                    1.75MB    store paths: ['/nix/store/q8a34i008kavznc3f4z0yrh9brgkk38g-python3.13-anyio-4.12.1']
<missing>      N/A                    819kB     store paths: ['/nix/store/5y6rxrmvj4qxzbzyl3dslyx72x5ckcbk-python3.13-uvicorn-0.40.0']
<missing>      N/A                    713kB     store paths: ['/nix/store/09f6k42d8zfxiadj2rc02gfpnmhlja7y-python3.13-prometheus-client-0.24.1']
<missing>      N/A                    1.27MB    store paths: ['/nix/store/bjl4laiaspy4d4n1w2qj8knhi1iv9agg-python3.13-click-8.3.1']
<missing>      N/A                    934kB     store paths: ['/nix/store/srb6n37b2ah22a9zxpqj2igxm9h3wpvf-python3.13-idna-3.11']
<missing>      N/A                    228kB     store paths: ['/nix/store/3ihdwzv8wwvrdpixgrb0xiwc09asq8jb-python3.13-asgiref-3.11.0']
<missing>      N/A                    125kB     store paths: ['/nix/store/wpsa573cm2kslka6l3i9lvcdsghmsryf-python3.13-typing-inspection-0.4.2']
<missing>      N/A                    504kB     store paths: ['/nix/store/llv9b1i1c1j8dzkakysmgn99nicjlcs1-python3.13-typing-extensions-4.15.0']
<missing>      N/A                    267kB     store paths: ['/nix/store/7f2qrs85aid2awk28p4dwn12sq69i7xm-python3.13-h11-0.16.0']
<missing>      N/A                    123kB     store paths: ['/nix/store/clyvnawy913aqrg3hy15jjlr9b67kym5-python3.13-python-json-logger-4.0.0']
<missing>      N/A                    102kB     store paths: ['/nix/store/xf5xdzi3qa32kghy5mmsl0955m211w79-python3.13-annotated-types-0.7.0']
<missing>      N/A                    14.1kB    store paths: ['/nix/store/dm9slx7cs5wrmg1b6k2s07jqdza2zgrn-python3.13-annotated-doc-0.0.4']
<missing>      N/A                    111MB     store paths: ['/nix/store/pzdalg368npikvpq4ncz2saxnz19v53k-python3-3.13.12']
<missing>      N/A                    10.3MB    store paths: ['/nix/store/ab3753m6i7isgvzphlar0a8xb84gl96i-gcc-15.2.0-lib']
<missing>      N/A                    9.3MB     store paths: ['/nix/store/bga5xf95jaypy385hvxm4h3yxl3m1566-openssl-3.6.1']
<missing>      N/A                    5.85MB    store paths: ['/nix/store/yvh4iy0ab95dq2p6cfm1xfvs6j9m0gxy-sqlite-3.51.2']
<missing>      N/A                    505kB     store paths: ['/nix/store/qq90p0xx02ydaqv2gv28mx4qx2vk98fq-readline-8.3p3']
<missing>      N/A                    3.3MB     store paths: ['/nix/store/4zmr3iw5s719y5zz7h2dnym67x2i6n23-ncurses-6.6']
<missing>      N/A                    2.05MB    store paths: ['/nix/store/safgshpdshpq8v8ww406szddpfws3vml-util-linux-minimal-2.41.3-lib']
<missing>      N/A                    1.85MB    store paths: ['/nix/store/v8sa6r6q037ihghxfbwzjj4p59v2x0pv-bash-5.3p9']
<missing>      N/A                    843kB     store paths: ['/nix/store/x8x0bp6q9x80lr3lljkj7xr4lx2495si-xz-5.8.2']
<missing>      N/A                    449kB     store paths: ['/nix/store/q9wz2k88ksbv9d90hw27hsr08b8jdc2d-gdbm-1.26-lib']
<missing>      N/A                    306kB     store paths: ['/nix/store/cr8mzl7cj4s5mriwrqnf9cvadw1iai5m-expat-2.7.4']
<missing>      N/A                    224kB     store paths: ['/nix/store/gac1a2359c62vgvy13d2i3asi6v00vfa-mpdecimal-4.0.1']
<missing>      N/A                    131kB     store paths: ['/nix/store/2kdz3m7ic8w226pcvkz1dlg169v91p6a-zlib-1.3.2']
<missing>      N/A                    87.7kB    store paths: ['/nix/store/vi21p90v3kj509rx00r101xcqa6za76b-bzip2-1.0.8']
<missing>      N/A                    72.5kB    store paths: ['/nix/store/8zgy79sw0zjwfcfp78p883hkkdw0pdzs-libffi-3.5.2']
<missing>      N/A                    34.9MB    store paths: ['/nix/store/jms7zxzm7w1whczwny5m3gkgdjghmi2r-glibc-2.42-51']
<missing>      N/A                    362kB     store paths: ['/nix/store/1ga782ml07vy0h503ac4cin0h8d7q6yh-libidn2-2.3.8']
<missing>      N/A                    1.9MB     store paths: ['/nix/store/h15ranlgwagilr6ajd7ich6d896kf9zd-tzdata-2026a']
<missing>      N/A                    2.08MB    store paths: ['/nix/store/p7jg95rzvfalb95k3mskk0jqxc9d724n-libunistring-1.4.1']
<missing>      N/A                    197kB     store paths: ['/nix/store/hbnbbbx1n96v1waiiaid9fmg4li4i1kp-gcc-15.2.0-libgcc']
<missing>      N/A                    197kB     store paths: ['/nix/store/vpxblivamvic1p5r5zny934jvg33m50r-xgcc-15.2.0-libgcc']
<missing>      N/A                    118kB     store paths: ['/nix/store/a6kd5v5x97jnyyzbmiild0m1ikn5yfmg-mailcap-2.1.54']
```

Observation:

The traditional Docker image contains layers created by Dockerfile instructions and includes build-time metadata. The Nix image is assembled from Nix store paths and uses deterministic metadata.

---

## 17. Why Traditional Dockerfiles Are Not Bit-for-Bit Reproducible

Traditional Dockerfiles usually cannot guarantee bit-for-bit reproducibility because:

1. Base image tags such as `python:3.13-slim` can point to different digests over time.
2. Docker image metadata includes timestamps.
3. Package managers such as pip, apt, apk, and npm can resolve packages differently over time.
4. Builds often depend on external network state.
5. Transitive dependencies are not always fully locked.
6. Docker layer caching improves speed, but it is not the same as cryptographic reproducibility.

Nix improves this by declaring dependencies explicitly, storing outputs in the Nix store, and deriving output paths from build inputs.

---

## 18. Practical Scenarios Where Nix Reproducibility Matters

Nix reproducibility is useful in the following scenarios:

| Scenario | Why Nix helps |
|---|---|
| CI/CD | Developers and CI runners can build the same artifact. |
| Security audits | Exact dependencies can be inspected and reproduced. |
| Rollbacks | Older artifacts can be rebuilt or retrieved more reliably. |
| Long-lived systems | Dependency drift is reduced over time. |
| Team development | Local machine differences cause fewer build problems. |

Reflection:

If I could redo Lab 2 with Nix, I would use Nix to build the application artifact first and then use `dockerTools` to create the container image. Docker would still be useful as a runtime and distribution format, but Nix would provide stronger guarantees for the build process.

---

## 19. Lab 1 vs Lab 10 vs Lab 18 Dependency Management

| Aspect | Lab 1: venv + requirements.txt | Lab 10: Helm values.yaml | Lab 18: Nix Flakes |
|---|---|---|---|
| Python version | System-dependent | Hidden inside image | Pinned through nixpkgs |
| App dependencies | Partially pinned | Hidden inside image | Nix dependency graph |
| Build tools | Not pinned | Not pinned | Pinned |
| Runtime image | Not applicable | Image tag | Nix-built image possible |
| Reproducibility | Approximate | Tag-based | Lock-file based |
| Cross-machine consistency | Weak | Medium | Strong |
| Rollback confidence | Medium | Depends on image immutability | Strong |

Helm is useful for Kubernetes deployment configuration, but `values.yaml` usually pins only image names, tags, replica counts, service ports, and environment-specific deployment options. It normally does not lock the full dependency graph inside the container image.

Nix Flakes go deeper because `flake.lock` pins the package set and build dependency graph. A strong combined approach is to build a reproducible image with Nix and deploy that immutable image through Helm.

---

## 20. Final Reflection

Nix made the build process more explicit and reproducible than the earlier `pip + venv` and Dockerfile workflows. The main advantage is that build inputs are declared and outputs are stored in content-addressed Nix store paths. This makes repeated builds more predictable and reduces environment drift.

The main challenge is that Nix has a steeper learning curve. It requires learning the Nix expression language, the nixpkgs package set, and the difference between development shells, derivations, store paths, and Docker images built from Nix closures.

Docker and Kubernetes are still useful for runtime packaging, deployment, and orchestration. However, Nix is stronger for reproducible artifact creation. In a production workflow, I would use Nix to build artifacts and then use Docker, Kubernetes, or Helm to run and deploy those artifacts.

---

## 21. Files Added

```text
labs/lab18/app_python/default.nix
labs/lab18/app_python/docker.nix
labs/lab18/app_python/flake.nix
labs/lab18/app_python/flake.lock
labs/submission18.md
```
