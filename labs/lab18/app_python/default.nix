{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi
    uvicorn
    prometheus-client
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  dontUnpack = false;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/lib/devops-info-service
    cp app.py $out/lib/devops-info-service/app.py

    makeWrapper ${pkgs.python3}/bin/python3 $out/bin/devops-info-service \
      --add-flags "$out/lib/devops-info-service/app.py" \
      --prefix PYTHONPATH : "$PYTHONPATH"

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "DevOps Info Service - FastAPI app from Lab 1, built reproducibly with Nix";
    license = licenses.mit;
  };
}
