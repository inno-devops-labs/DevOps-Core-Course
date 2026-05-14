{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python3;
  pythonPackages = python.pkgs;
in
pythonPackages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = with pythonPackages; [
    fastapi
    uvicorn
    prometheus-client
  ];

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  doCheck = true;

  checkInputs = with pythonPackages; [
    httpx
    pytest
  ];

  checkPhase = ''
    runHook preCheck
    pytest tests -q
    runHook postCheck
  '';

  installPhase = ''
    runHook preInstall

    mkdir -p $out/share/devops-info-service
    cp app.py config.py $out/share/devops-info-service/
    cp -r routes services $out/share/devops-info-service/

    makeWrapper ${python.interpreter} $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --prefix PYTHONPATH : "$out/share/devops-info-service:$PYTHONPATH" \
      --set HOST "0.0.0.0" \
      --set PORT "8000" \
      --set VISITS_FILE "/tmp/devops-info-service-visits"

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "DevOps Info Service built reproducibly with Nix";
    mainProgram = "devops-info-service";
    platforms = platforms.unix;
  };
}
