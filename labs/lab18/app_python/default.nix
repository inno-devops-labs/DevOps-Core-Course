{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python313;
  pythonPackages = pkgs.python313Packages;
  source = builtins.path {
    path = ./.;
    name = "devops-info-service-src";
    filter = path: type:
      type == "regular"
      && builtins.elem (baseNameOf path) [
        "app.py"
        "requirements.txt"
      ];
  };
  appPythonPath = pythonPackages.makePythonPath (with pythonPackages; [
    flask
    gunicorn
    prometheus-client
  ]);
in
pythonPackages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = source;

  format = "other";
  dontCheck = true;

  propagatedBuildInputs = with pythonPackages; [
    flask
    gunicorn
    prometheus-client
  ];

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py

    makeWrapper ${python.interpreter} $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --prefix PYTHONPATH : "${appPythonPath}" \
      --set-default HOST "0.0.0.0" \
      --set-default PORT "5002" \
      --set-default SERVICE_NAME "devops-info-service" \
      --set-default SERVICE_VERSION "1.0.0" \
      --set-default VISITS_FILE "/tmp/devops-info-service-visits"

    runHook postInstall
  '';
}
