{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python313;
  pythonPackages = python.pkgs;
  pythonDeps = with pythonPackages; [
    flask
    prometheus-client
    python-json-logger
  ];
  source = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      type == "directory" || builtins.elem (baseNameOf path) [
        "app.py"
        "requirements.txt"
      ];
  };
in
pythonPackages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = source;

  format = "other";

  propagatedBuildInputs = pythonDeps;
  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py

    makeWrapper ${python}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --set PYTHONPATH "${pythonPackages.makePythonPath pythonDeps}:$out/share/devops-info-service" \
      --set-default HOST "0.0.0.0" \
      --set-default PORT "5000" \
      --set-default DEBUG "False" \
      --set-default APP_NAME "devops-info-service" \
      --set-default APP_ENV "nix" \
      --set-default LOG_LEVEL "INFO" \
      --set-default VISITS_FILE "/tmp/devops-info-service/visits" \
      --set-default APP_CONFIG_PATH "/tmp/devops-info-service/config.json"

    runHook postInstall
  '';

  checkPhase = ''
    runHook preCheck

    ${python}/bin/python -m py_compile app.py
    PYTHONPATH="${pythonPackages.makePythonPath pythonDeps}:$PWD" \
      VISITS_FILE="$TMPDIR/visits" \
      APP_CONFIG_PATH="$TMPDIR/config.json" \
      ${python}/bin/python -c "import app; assert app.app.name == 'app'"

    runHook postCheck
  '';

  meta = with pkgs.lib; {
    description = "DevOps Info Service packaged as a reproducible Nix derivation";
    mainProgram = "devops-info-service";
    platforms = platforms.linux;
  };
}
