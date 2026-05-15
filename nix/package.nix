{
  lib,
  stdenvNoCC,
  python314,
  appSrc ? ../app_python,
}:

let
  python = python314.override {
    packageOverrides =
      pyFinal: pyPrev:
      let
        isRuntimeOnlyInput =
          input:
          let
            name = input.name or input.pname or "";
            dropPatterns = [
              "astor"
              "cryptography-vectors"
              "flaky"
              "freezegun"
              "gevent"
              "ipython"
              "jedi"
              "lxml"
              "mypy"
              "parso"
              "pytest"
              "sphinx"
              "watchdog"
              "xdist"
            ];
          in
          !(lib.any (pattern: lib.hasInfix pattern name) dropPatterns);

        withoutChecks =
          pkg:
          pkg.overridePythonAttrs (old: {
            doCheck = false;
            build-system = lib.filter isRuntimeOnlyInput (old.build-system or [ ]);
            checkInputs = [ ];
            nativeCheckInputs = [ ];
            nativeBuildInputs = lib.filter isRuntimeOnlyInput (old.nativeBuildInputs or [ ]);
          });

        runtimePackage =
          pkg: deps:
          (withoutChecks pkg).overridePythonAttrs (_old: {
            dependencies = deps;
            propagatedBuildInputs = deps;
          });
      in
      {
        blinker = runtimePackage pyPrev.blinker [ ];
        click = runtimePackage pyPrev.click [ ];
        flask = runtimePackage pyPrev.flask [
          pyFinal.blinker
          pyFinal.click
          pyFinal.itsdangerous
          pyFinal.jinja2
          pyFinal.werkzeug
        ];
        gunicorn = runtimePackage pyPrev.gunicorn [ pyFinal.packaging ];
        idna = runtimePackage pyPrev.idna [ ];
        itsdangerous = runtimePackage pyPrev.itsdangerous [ ];
        jinja2 = runtimePackage pyPrev.jinja2 [ pyFinal.markupsafe ];
        markupsafe = runtimePackage pyPrev.markupsafe [ ];
        packaging = runtimePackage pyPrev.packaging [ ];
        prometheus-client = runtimePackage pyPrev.prometheus-client [ ];
        werkzeug = runtimePackage pyPrev.werkzeug [ pyFinal.markupsafe ];
      };
  };

  pythonEnv = python.withPackages (ps: [
    ps.flask
    ps.gunicorn
    ps.prometheus-client
  ]);

  cleanAppSrc = lib.cleanSourceWith {
    src = appSrc;
    filter =
      path: type:
      let
        rel = lib.removePrefix ((toString appSrc) + "/") (toString path);
      in
      rel == "README.md"
      || rel == "gunicorn.conf.py"
      || rel == "pyproject.toml"
      || rel == "uv.lock"
      || rel == "src"
      || lib.hasPrefix "src/" rel;
  };
in
stdenvNoCC.mkDerivation {
  pname = "devops-info-service";
  version = "1.12.0";

  src = cleanAppSrc;

  dontBuild = true;

  installPhase = ''
    runHook preInstall

    app_dir="$out/share/devops-info-service"
    mkdir -p "$app_dir" "$out/bin"
    cp -r src gunicorn.conf.py pyproject.toml uv.lock README.md "$app_dir/"

    cat > "$out/bin/devops-info-service" <<EOF
    #!${stdenvNoCC.shell}
    export PYTHONPATH="$app_dir\''${PYTHONPATH:+:}\''${PYTHONPATH:-}"
    export HOST="\''${HOST:-0.0.0.0}"
    export PORT="\''${PORT:-5000}"
    cd "$app_dir"
    exec ${pythonEnv}/bin/gunicorn --config "$app_dir/gunicorn.conf.py" src.main:app "\$@"
    EOF
    chmod +x "$out/bin/devops-info-service"

    runHook postInstall
  '';

  passthru = {
    inherit pythonEnv;
    inherit python;
  };

  meta = {
    description = "Flask DevOps info service packaged reproducibly with Nix";
    mainProgram = "devops-info-service";
    platforms = [ "x86_64-linux" ];
  };
}
