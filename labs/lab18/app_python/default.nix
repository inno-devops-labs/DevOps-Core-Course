{ pkgs ? import <nixpkgs> { } }:

# Lab 18 — Reproducible Python build via Nix.
#
# Same source as labs/01-16's `app_python/`:
#   Flask 3.x app with `/`, `/health`, `/visits`, `/metrics` (prometheus-client).
#
# Reproducibility guarantees beyond `pip install -r requirements.txt`:
#   - the Python interpreter version is pinned by nixpkgs
#   - flask/werkzeug/prometheus-client are pulled from the pinned nixpkgs,
#     not from PyPI at install time, so transitive deps cannot drift
#   - the build runs in a sandbox with no network access
#   - the resulting store path is content-addressable —
#     same source + same nixpkgs ⇒ same `/nix/store/<hash>-...` forever

pkgs.python3Packages.buildPythonApplication rec {
  pname = "devops-info-service";
  version = "1.0.0";

  # Filter the source: keep only files that affect the build, drop dev junk
  # like the `result` symlink emitted by `nix-build` itself (would otherwise
  # mutate the input hash on every rebuild and break reproducibility),
  # `__pycache__/`, `*.pyc`, and direnv state. This is the standard "clean
  # source" pattern in nixpkgs.
  src = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let
        baseName = baseNameOf (toString path);
      in
      !(
        baseName == "result" ||
        pkgs.lib.hasPrefix "result-" baseName ||
        baseName == "__pycache__" ||
        pkgs.lib.hasSuffix ".pyc" baseName ||
        baseName == ".direnv" ||
        baseName == ".pytest_cache"
      );
  };

  # We don't ship a setup.py / pyproject.toml — the app is a single script,
  # so we use the "other" format and provide our own installPhase.
  format = "other";

  # Runtime Python deps. Transitively pulls Werkzeug, click, jinja2, etc. —
  # all locked by nixpkgs revision.
  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
    werkzeug
    prometheus-client
  ];

  # makeWrapper is what gives us a self-contained `devops-info-service`
  # binary that injects PYTHONPATH so the deps resolve at runtime.
  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall

    # The script has no shebang, so we don't `chmod +x` and run it directly.
    # Instead, ship the .py under $out/share and point a makeWrapper-generated
    # `devops-info-service` wrapper at `python3 app.py`, propagating PYTHONPATH
    # so flask / werkzeug / prometheus-client resolve at runtime.
    mkdir -p $out/share/devops-info-service $out/bin
    cp app.py $out/share/devops-info-service/app.py

    makeWrapper ${pkgs.python3}/bin/python3 $out/bin/devops-info-service \
      --add-flags $out/share/devops-info-service/app.py \
      --prefix PYTHONPATH : "$PYTHONPATH"

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "DevOps Info Service — Flask app exposing /, /health, /visits, /metrics";
    mainProgram = "devops-info-service";
    license = licenses.mit;
    platforms = platforms.unix;
  };
}
