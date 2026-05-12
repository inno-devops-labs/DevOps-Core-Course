{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python3;
  pythonPackages = python.pkgs;
  runtimeDependencies = with pythonPackages; [
    flask
    prometheus-client
  ];
in
pythonPackages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = runtimeDependencies;
  nativeBuildInputs = [ pkgs.makeWrapper ];
  nativeCheckInputs = with pythonPackages; [ pytest ];

  installCheckPhase = ''
    runHook preInstallCheck
    export PYTHONPATH="$PWD:${pythonPackages.makePythonPath runtimeDependencies}"
    export VISITS_FILE="$TMPDIR/visits"
    pytest -q
    runHook postInstallCheck
  '';

  installPhase = ''
    runHook preInstall
    mkdir -p $out/share/devops-info-service $out/bin
    cp app.py $out/share/devops-info-service/app.py
    cp -r data $out/share/devops-info-service/data

    makeWrapper ${python}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --prefix PYTHONPATH : "${pythonPackages.makePythonPath runtimeDependencies}" \
      --set PYTHONUNBUFFERED "1"
    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "Flask DevOps information service built reproducibly with Nix";
    mainProgram = "devops-info-service";
    platforms = platforms.unix;
  };
}
