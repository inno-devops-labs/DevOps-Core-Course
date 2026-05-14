# Nix derivation for DevOps Info Service (FastAPI).
# Build with: nix-build
# Run with:   ./result/bin/devops-info-service
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";

  # Use the current directory as source.
  # Nix hashes this directory — any change → new hash → new store path.
  src = ./.;

  # format = "other" means no setup.py/pyproject.toml;
  # we handle the install phase manually below.
  format = "other";

  # Runtime Python dependencies (translated from requirements.txt).
  # Nix pins these via the nixpkgs revision, not PyPI — so they are
  # immutable: same nixpkgs commit → identical packages, forever.
  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi      # requirements.txt: fastapi==0.115.0
    uvicorn      # requirements.txt: uvicorn[standard]==0.32.0
    httptools    # uvicorn[standard] extra
    websockets   # uvicorn[standard] extra
  ];

  # makeWrapper lets us produce a real executable that knows where Python is.
  nativeBuildInputs = [ pkgs.makeWrapper ];

  # Copy app.py into the Nix store and wrap it with the correct interpreter.
  installPhase = ''
    mkdir -p $out/bin $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py

    # $PYTHONPATH is already set by buildPythonApplication to include all
    # propagatedBuildInputs, so we just prefix with it.
    makeWrapper ${pkgs.python3}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --prefix PYTHONPATH : "$PYTHONPATH"
  '';
}
