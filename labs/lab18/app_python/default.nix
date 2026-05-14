{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let name = baseNameOf path;
      in type == "directory" || builtins.elem name [
        "app.py"
        "config.json"
        "requirements.txt"
      ];
  };
  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
    gunicorn
    prometheus-client
    werkzeug
  ];

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py
    cp -r config $out/share/devops-info-service/config

    makeWrapper ${pkgs.python3.interpreter} $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --prefix PYTHONPATH : "$PYTHONPATH" \
      --set APP_CONFIG_PATH "$out/share/devops-info-service/config/config.json" \
      --set-default VISITS_FILE_PATH "/tmp/devops-info-service-visits"

    runHook postInstall
  '';
}
