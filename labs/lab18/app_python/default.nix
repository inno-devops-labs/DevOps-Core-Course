{ pkgs ? import <nixpkgs> {} }:

let
  filteredSrc = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let baseName = baseNameOf path; in
      !(builtins.elem baseName [
        "result" "result-bin" "result-dev"
        "__pycache__" ".pytest_cache" ".ruff_cache"
        ".venv" ".direnv" ".env" ".DS_Store"
        "default.nix" "docker.nix" "flake.nix" "flake.lock"
      ] || pkgs.lib.hasSuffix ".pyc" baseName);
  };
in
pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = filteredSrc;
  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi
    uvicorn
    python-json-logger
    prometheus-client
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall
    mkdir -p $out/bin $out/lib/devops-info-service
    cp app.py $out/lib/devops-info-service/
    cp -r config data $out/lib/devops-info-service/

    makeWrapper ${pkgs.python3}/bin/python $out/bin/devops-info-service \
      --add-flags "-m uvicorn app:app --host 0.0.0.0 --port \''${PORT:-5000}" \
      --chdir $out/lib/devops-info-service \
      --prefix PYTHONPATH : "$out/lib/devops-info-service:$PYTHONPATH" \
      --set-default CONFIG_FILE "$out/lib/devops-info-service/config/config.json" \
      --set-default VISITS_FILE "/tmp/devops-info-service/visits"
    runHook postInstall
  '';

  doCheck = false;
}
