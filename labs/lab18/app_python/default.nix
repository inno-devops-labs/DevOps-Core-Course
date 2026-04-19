{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python3;
  runtimeDeps = with python.pkgs; [
    flask
    prometheus-client
    python-json-logger
  ];
in
python.pkgs.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  format = "other";
  src = pkgs.lib.cleanSource ./.;

  propagatedBuildInputs = runtimeDeps;

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py

    makeWrapper ${python}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --prefix PYTHONPATH : "${python.pkgs.makePythonPath runtimeDeps}" \
      --set PYTHONDONTWRITEBYTECODE 1 \
      --set PYTHONUNBUFFERED 1

    runHook postInstall
  '';

  checkPhase = ''
    runHook preCheck
    export PYTHONPATH=$PWD:${python.pkgs.makePythonPath runtimeDeps}
    ${python.pkgs.pytest}/bin/pytest tests -q
    runHook postCheck
  '';

  nativeCheckInputs = with python.pkgs; [
    pytest
  ];

  doCheck = true;

  meta = with pkgs.lib; {
    description = "DevOps course info service built reproducibly with Nix";
    mainProgram = "devops-info-service";
    platforms = platforms.unix;
  };
}
