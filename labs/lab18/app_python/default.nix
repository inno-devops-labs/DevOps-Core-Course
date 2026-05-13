{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
    prometheus-client
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin $out/lib
    cp app.py $out/lib/app.py

    cat > $out/bin/devops-info-service << 'EOF'
    #!/bin/sh
    exec python3 "$out/lib/app.py" "$@"
    EOF
    chmod +x $out/bin/devops-info-service

    wrapProgram $out/bin/devops-info-service \
      --set PYTHONPATH "$PYTHONPATH"
  '';

  meta = {
    description = "DevOps Info Service - Flask application";
  };
}
