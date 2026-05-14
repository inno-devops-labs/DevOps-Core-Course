{ pkgs ? import <nixpkgs> {} }:

let
  # Create a Python environment with all runtime dependencies
  # Nix pins exact versions from nixpkgs, ensuring bit-for-bit reproducibility
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    fastapi           # Web framework (0.128.0 in nixpkgs)
    uvicorn           # ASGI server (0.40.0 in nixpkgs)
    colorlog          # Colored logging (6.10.1 in nixpkgs)
    python-json-logger # JSON structured logging (4.0.0 in nixpkgs)
    pydantic          # Data validation (dependency of fastapi)
    pydantic-settings # Settings management (2.12.0 in nixpkgs)
    prometheus-client # Metrics endpoint
  ]);
in

pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";

  # Source: current directory, excluding venv and build artifacts
  src = builtins.filterSource
    (path: type:
      let baseName = baseNameOf path;
      in !(builtins.elem baseName [
        "venv" "result" ".git" "__pycache__" ".env"
        "default.nix" "docker.nix" "flake.nix" "flake.lock"
        "tests" "docs"
      ]))
    ./.;

  # makeWrapper is needed to create a wrapper script
  nativeBuildInputs = [ pkgs.makeWrapper ];

  dontBuild = true;

  installPhase = ''
    runHook preInstall

    # Install application source files to the Nix store
    mkdir -p $out/lib/devops-info-service $out/bin

    # Copy all Python source modules
    cp app.py config.py visits.py $out/lib/devops-info-service/
    [ -f __init__.py ] && cp __init__.py $out/lib/devops-info-service/ || true
    cp -r core routes $out/lib/devops-info-service/

    # Create an executable wrapper that:
    # 1. Changes to the app directory (required for uvicorn module discovery)
    # 2. Prepends PYTHONPATH so Python finds all local modules
    # 3. Invokes python -m uvicorn with the correct app target
    makeWrapper ${pythonEnv}/bin/python $out/bin/devops-info-service \
      --add-flags "-m uvicorn app:app --host 0.0.0.0 --port 5000" \
      --run "cd $out/lib/devops-info-service" \
      --prefix PYTHONPATH : "$out/lib/devops-info-service"

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "DevOps Info Service built with Nix for reproducible builds";
    platforms = platforms.linux;
  };
}
