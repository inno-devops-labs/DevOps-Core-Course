# Lab 18 — reproducible Python app (FastAPI) via nixpkgs-pinned interpreter + deps.
# Equivalent goal to `python3Packages.buildPythonApplication` + `format = "other"`: a single
# derivation that installs `devops-info-service` into the Nix store with a wrapped Python.
#
# Build: `nix-build`   Run: `./result/bin/devops-info-service`

{ pkgs ? import <nixpkgs> { } }:

let
  pydeps = ps: with ps; [
    fastapi
    uvicorn
    pydantic
    starlette
    typing-extensions
  ];
  pythonWith = pkgs.python3.withPackages pydeps;
in
pkgs.stdenvNoCC.mkDerivation rec {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall
    mkdir -p $out/bin $out/share/${pname}
    cp app.py requirements.txt $out/share/${pname}/
    makeWrapper ${pythonWith}/bin/python $out/bin/devops-info-service \
      --chdir "$out/share/${pname}" \
      --add-flags "app.py"
    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "DevOps Info Service (Lab 18 Nix build)";
    license = licenses.mit;
    mainProgram = "devops-info-service";
    platforms = platforms.all;
  };
}
