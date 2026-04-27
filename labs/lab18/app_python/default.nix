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
