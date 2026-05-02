{ pkgs ? import <nixpkgs> {} }:

let
  pyDeps = with pkgs.python3Packages; [
    fastapi
    uvicorn
    prometheus-client
  ];
in
pkgs.python3Packages.buildPythonApplication rec {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";
  dontUnpack = true;

  propagatedBuildInputs = pyDeps;
  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/${pname}
    cp ${src}/app.py $out/share/${pname}/app.py

    cat > $out/bin/devops-info-service <<SCRIPT
#!${pkgs.bash}/bin/bash
exec ${pkgs.python3}/bin/python $out/share/${pname}/app.py
SCRIPT
    chmod +x $out/bin/devops-info-service

    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "${pkgs.python3Packages.makePythonPath pyDeps}"

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "DevOps Info Service built reproducibly with Nix";
    platforms = platforms.unix;
  };
}
