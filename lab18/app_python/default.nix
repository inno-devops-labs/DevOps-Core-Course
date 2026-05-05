{ pkgs ? import <nixpkgs> {} }:

let
  cleanAppSource = pkgs.lib.cleanSourceWith {
    src = ./.;

    # Keep only files that are real application inputs.
    # This prevents __pycache__, result symlinks, virtualenvs,
    # evidence files, and temporary files from changing the Nix output hash.
    filter = path: type:
      let
        base = baseNameOf path;
      in
        base == "app.py" || base == "requirements.txt";
  };
in

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = cleanAppSource;

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi
    uvicorn
  ];

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  dontUnpack = false;

  installPhase = ''
    mkdir -p $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py

    mkdir -p $out/bin
    makeWrapper ${pkgs.python3Packages.uvicorn}/bin/uvicorn $out/bin/devops-info-service \
      --add-flags "app:app" \
      --add-flags "--host" \
      --add-flags "0.0.0.0" \
      --add-flags "--port" \
      --add-flags "5000" \
      --set PYTHONPATH "$out/share/devops-info-service:$PYTHONPATH"
  '';
}