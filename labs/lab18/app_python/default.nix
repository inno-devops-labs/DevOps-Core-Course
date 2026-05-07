{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python313;
  pythonPackages = pkgs.python313Packages;
  pythonEnv = python.withPackages (ps: [
    ps.fastapi
    ps.uvicorn
    ps."prometheus-client"
    ps."python-dotenv"
  ]);
in
pythonPackages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;
  format = "other";

  propagatedBuildInputs = [
    pythonPackages.fastapi
    pythonPackages.uvicorn
    pythonPackages."prometheus-client"
    pythonPackages."python-dotenv"
  ];

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/share/devops-info-service
    cp app.py requirements.txt Dockerfile $out/share/devops-info-service/

    mkdir -p $out/bin
    makeWrapper ${pythonEnv}/bin/python $out/bin/devops-info-service \
      --set PYTHONPATH "$out/share/devops-info-service" \
      --set HOST "0.0.0.0" \
      --set PORT "8000" \
      --add-flags "-m uvicorn app:app --host 0.0.0.0 --port 8000"

    runHook postInstall
  '';

  doCheck = false;

  meta = with pkgs.lib; {
    description = "FastAPI DevOps info service packaged reproducibly with Nix";
    license = licenses.mit;
    platforms = platforms.unix;
    mainProgram = "devops-info-service";
  };
}
