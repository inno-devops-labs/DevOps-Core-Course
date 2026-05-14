{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python3;
  pythonPackages = pkgs.python3Packages;
in
pythonPackages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";
  dontBuild = true;
  dontCheck = true;

  propagatedBuildInputs = with pythonPackages; [
    fastapi
    uvicorn
    prometheus-client
  ];

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py

    makeWrapper ${python}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --prefix PYTHONPATH : "$PYTHONPATH"

    runHook postInstall
  '';

  meta = {
    description = "FastAPI DevOps Info Service built reproducibly with Nix";
    mainProgram = "devops-info-service";
  };
}
