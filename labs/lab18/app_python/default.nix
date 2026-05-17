{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  pyproject = false;
  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
  ];
  src = ./.;
  meta = {
    description = "DevOps Info Service - Flask application";
    mainProgram = "devops-info-service";
  };
}
