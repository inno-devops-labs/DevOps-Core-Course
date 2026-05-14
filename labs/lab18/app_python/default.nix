{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python3.withPackages (ps: with ps; [
    flask
    prometheus-client
  ]);
in
pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";

  # Reuse the Lab 1 source tree as the build input for Task 1.
  src = ../../../app_python;

  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py

    cat > $out/bin/devops-info-service <<EOF
    #!${pkgs.runtimeShell}
    exec ${python}/bin/python $out/share/devops-info-service/app.py "\$@"
    EOF
    chmod +x $out/bin/devops-info-service

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "DevOps Info Service from Lab 1 built reproducibly with Nix";
    homepage = "https://github.com/";
    license = licenses.mit;
    platforms = platforms.unix;
  };
}
