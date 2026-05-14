{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python313;
  pythonPackages = python.pkgs;
  pythonEnv = python.withPackages (ps: with ps; [
    fastapi
    prometheus-client
    uvicorn
  ]);
  source = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let
        base = baseNameOf path;
      in
        !(base == "result"
          || base == ".pytest_cache"
          || base == "__pycache__"
          || base == "venv"
          || base == ".venv");
  };
in
pythonPackages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = source;

  format = "other";

  propagatedBuildInputs = with pythonPackages; [
    fastapi
    prometheus-client
    uvicorn
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py

    makeWrapper ${pythonEnv}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --set HOST "0.0.0.0" \
      --set PORT "5000" \
      --set RELEASE_VERSION "nix-1.0.0" \
      --set VISITS_FILE "/tmp/devops-info-service/visits"

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "DevOps Core Python info service built reproducibly with Nix";
    mainProgram = "devops-info-service";
    platforms = platforms.linux;
  };
}
