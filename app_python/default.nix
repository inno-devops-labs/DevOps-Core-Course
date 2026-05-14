# Nix derivation for DevOps Info Service (FastAPI application)
# Lab 18 - Reproducible Builds with Nix
#
# Key fields explained:
# - pname: Package name (used in store path)
# - version: Package version (used in store path)
# - src: Source code location (./. means current directory)
# - format = "other": For apps without setup.py/pyproject.toml
# - propagatedBuildInputs: Runtime dependencies (Python packages)
# - nativeBuildInputs: Build-time dependencies (makeWrapper for wrapping Python script)
# - installPhase: How to install the application into Nix store

{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  # Format "other" because we don't have setup.py or pyproject.toml
  format = "other";

  # Runtime Python dependencies
  # These are resolved from nixpkgs, not PyPI directly
  # Nix pins exact versions for reproducibility
  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi
    uvicorn
    prometheus-client
    pydantic
    starlette
  ];

  # Build-time dependencies
  # makeWrapper creates a wrapper script that sets up PYTHONPATH correctly
  nativeBuildInputs = [ pkgs.makeWrapper ];

  # No setup.py, so we manually define the install phase
  installPhase = ''
    # Create bin directory in the Nix store output path
    mkdir -p $out/bin
    
    # Copy the application script
    cp app.py $out/bin/devops-info-service
    
    # Wrap the script with Python interpreter and dependencies
    # This ensures the script can find all Python packages at runtime
    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$PYTHONPATH"
  '';

  # Meta information for the package
  meta = with pkgs.lib; {
    description = "DevOps Info Service - FastAPI application for Lab 1/2/18";
    homepage = "https://github.com/course-repo";
    license = licenses.mit;
    maintainers = [ "student" ];
    mainProgram = "devops-info-service";
  };
}
