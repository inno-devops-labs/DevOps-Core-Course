{ pkgs ? import <nixpkgs> {} }:

let
  cleanSrc = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let
        name = builtins.baseNameOf path;
      in
      !(
        name == "data" ||
        name == "visits" ||
        name == "result" ||
        name == ".git"
      );
  };

  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    flask
    prometheus-client
  ]);
in
pkgs.python3Packages.buildPythonApplication rec {
  pname = "devops-info-service";
  version = "1.1.0";
  src = cleanSrc;

  format = "other";
  strictDeps = true;

  propagatedBuildInputs = [ pythonEnv ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/${pname}
    cp app.py $out/share/${pname}/app.py
    cp -r config $out/share/${pname}/

    cat > $out/bin/${pname} <<APP
#!${pkgs.runtimeShell}
    exec ${pythonEnv}/bin/python $out/share/${pname}/app.py "\$@"
APP
    chmod +x $out/bin/${pname}

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "DevOps Info Service packaged reproducibly with Nix";
    license = licenses.mit;
    platforms = platforms.unix;
  };
}
