{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  # format = "other" because we have no setup.py
  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service
    chmod +x $out/bin/devops-info-service

    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "${pkgs.python3Packages.flask}/${pkgs.python3.sitePackages}" \
      --set PYTHONPATH "$PYTHONPATH" \
      --prefix PATH : "${pkgs.python3}/bin"
  '';
}
