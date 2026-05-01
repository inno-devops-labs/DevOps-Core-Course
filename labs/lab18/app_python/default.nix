{ pkgs ? import <nixpkgs> { } }:

let
  # Only ship application files so extra paths (`result`, `flake.lock`, *.nix) never change the input hash.
  src = pkgs.runCommand "devops-info-service-src" { } ''
    mkdir -p $out
    cp ${./app.py} $out/app.py
    cp ${./requirements.txt} $out/requirements.txt
  '';
in
pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  inherit src;
  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [ flask ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/libexec/devops-info-service
    cp app.py $out/libexec/devops-info-service/
    makeWrapper ${pkgs.python3}/bin/python3 $out/bin/devops-info-service \
      --chdir "$out/libexec/devops-info-service" \
      --prefix PYTHONPATH : "$PYTHONPATH" \
      --add-flags "$out/libexec/devops-info-service/app.py"
  '';
}
