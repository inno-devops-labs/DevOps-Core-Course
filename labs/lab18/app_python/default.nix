{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  # Only include application source files so the derivation hash is not
  # affected by build artifacts (result symlinks, __pycache__, flake.lock…).
  src = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = name: _type:
      let basename = builtins.baseNameOf name;
      in builtins.elem basename [ "main.py" ];
  };

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi
    uvicorn
    prometheus-client
    python-json-logger
    httpx
    python-dotenv
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin $out/lib
    cp main.py $out/lib/main.py

    # Launch via `python -m uvicorn main:app` so that main.py is only
    # imported once as a module (not first executed as __main__), which
    # prevents the Prometheus CollectorRegistry duplicate-registration error.
    makeWrapper ${pkgs.python3}/bin/python $out/bin/devops-info-service \
      --add-flags "-m uvicorn main:app --host 0.0.0.0 --port 8000" \
      --prefix PYTHONPATH : "$out/lib:$PYTHONPATH"
  '';

  meta = {
    description = "DevOps Info Service built reproducibly with Nix";
    mainProgram = "devops-info-service";
  };
}
