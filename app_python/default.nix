{ pkgs ? import <nixpkgs> {} }:

let
  # pythonEnv bundles the interpreter + all dependencies into one store path,
  # so the wrapper doesn't need to set PYTHONPATH for third-party packages.
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    fastapi
    uvicorn
    pydantic
    python-json-logger
    prometheus-client
  ]);
in
pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";
  src = builtins.path {
    path = ./.;
    name = "app_python";
    # Exclude build artifacts so they don't affect the source hash
    filter = path: type:
      baseNameOf path != "result" &&
      baseNameOf path != "__pycache__" &&
      baseNameOf path != "venv" &&
      baseNameOf path != "venv1" &&
      baseNameOf path != "venv2";
  };

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin $out/lib/devops-info-service

    cp *.py $out/lib/devops-info-service/
    cp -r routes $out/lib/devops-info-service/

    makeWrapper ${pythonEnv}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/lib/devops-info-service/app.py" \
      --set PYTHONPATH "$out/lib/devops-info-service"
  '';
}
