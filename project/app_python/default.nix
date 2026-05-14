{ pkgs ? import <nixpkgs> { } }:

let
  python = pkgs.python313;
  pyPkgs = python.pkgs;
in
pyPkgs.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";

  src = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let base = baseNameOf (toString path); in
      !(builtins.elem base [
        ".venv" "__pycache__" ".pytest_cache" ".ruff_cache"
        "result" "result-docker" ".env" ".direnv"
        "tests" "docs"
      ]);
  };

  format = "other";

  propagatedBuildInputs = with pyPkgs; [
    fastapi
    uvicorn
    pydantic
    pydantic-settings
    prometheus-client
    python-json-logger
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/${python.sitePackages}
    cp -r app $out/${python.sitePackages}/

    mkdir -p $out/bin
    cat > $out/bin/devops-info-service <<EOF
    #!${python}/bin/python3
    from app.__main__ import *  # noqa
    import runpy
    runpy.run_module("app", run_name="__main__")
    EOF
    chmod +x $out/bin/devops-info-service

    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$out/${python.sitePackages}:$PYTHONPATH"

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "DevOps course info service — Lab 1 FastAPI app built reproducibly with Nix";
    homepage = "https://github.com/peplxx/DevOps-Core-Course";
    license = licenses.mit;
    mainProgram = "devops-info-service";
    platforms = platforms.unix;
  };
}
