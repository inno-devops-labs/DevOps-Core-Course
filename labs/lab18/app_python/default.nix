{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-python-app";
  version = "1.0.0";
  src = ../../../app_python;

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi
    uvicorn
    prometheus-client
    python-json-logger
  ];

  nativeBuildInputs = with pkgs; [ makeWrapper ];

  postPatch = ''
    substituteInPlace app.py \
      --replace-fail 'DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")' \
      'DEFAULT_DATA_DIR = "/data"'
  '';

  installPhase = ''
    mkdir -p $out/bin
    mkdir -p $out/data
    cp app.py $out/bin/devops-python-app
    cp requirements.txt $out/ 2>/dev/null || true

    wrapProgram $out/bin/devops-python-app \
      --prefix PYTHONPATH : "$PYTHONPATH:$out" \
      --set HOST "0.0.0.0" \
      --set PORT "5000"
  '';

  meta = with pkgs.lib; {
    description = "DevOps Info Service - FastAPI application built with Nix";
    homepage = "https://github.com/Ge-os/DevOps-Core-Course";
    license = licenses.mit;
    platforms = platforms.linux;
  };
}
