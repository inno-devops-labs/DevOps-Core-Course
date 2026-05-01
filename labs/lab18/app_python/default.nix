{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python313.withPackages (ps: with ps; [
    flask
    prometheus-client
    python-dotenv
    python-json-logger
    requests
  ]);
in
pkgs.python313Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "2.0.0";
  src = ./.;

  format = "other";
  dontBuild = true;
  doCheck = false;

  nativeBuildInputs = [ pkgs.makeWrapper ];

  propagatedBuildInputs = with pkgs.python313Packages; [
    flask
    prometheus-client
    python-dotenv
    python-json-logger
    requests
  ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/share/devops-info-service $out/bin
    cp app.py $out/share/devops-info-service/app.py
    cp requirements.txt $out/share/devops-info-service/requirements.txt

    makeWrapper ${python}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --set-default HOST "0.0.0.0" \
      --set-default PORT "5000" \
      --set-default DATA_DIR "/tmp/devops-info-service/data" \
      --set-default CONFIG_FILE "$out/share/devops-info-service/config/config.json"

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "DevOps Info Service from Labs 1-2 built reproducibly with Nix";
    mainProgram = "devops-info-service";
    platforms = platforms.linux;
  };
}
