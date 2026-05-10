{
  description = "DevOps Info Service — reproducible build via Nix Flakes (Lab 18 Bonus)";

  # Lock the entire dependency tree (~80k packages) by pinning a specific
  # nixpkgs revision. `nix flake update` rewrites flake.lock; without that
  # command the lock stays frozen — far stronger than `requirements.txt`
  # (Lab 1) or `image.tag: 1.0.0` in `values.yaml` (Lab 10), both of which
  # only pin direct deps.
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        app = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      in
      {
        # `nix build` builds default; `nix build .#dockerImage` builds the OCI tarball.
        packages = {
          default = app;
          devops-info-service = app;
          dockerImage = dockerImage;
        };

        # `nix run .` launches the service.
        apps.default = {
          type = "app";
          program = "${app}/bin/devops-info-service";
        };

        # `nix develop` drops into a shell with Python + Flask + Werkzeug +
        # prometheus-client preinstalled, identical on every machine.
        # Compare with Lab 1's `python -m venv venv && pip install -r requirements.txt`,
        # which depends on the system's Python version and pip's resolution algorithm.
        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.python3
            pkgs.python3Packages.flask
            pkgs.python3Packages.werkzeug
            pkgs.python3Packages.prometheus-client
            pkgs.python3Packages.pytest
          ];
          shellHook = ''
            # Use importlib.metadata.version() — `__version__` is deprecated
            # in Flask 3.2 and was never provided by werkzeug / prometheus_client.
            echo "[nix develop] DevOps Info Service dev shell"
            echo "  python:            $(python3 --version)"
            echo "  flask:             $(python3 -c 'from importlib.metadata import version; print(version("flask"))')"
            echo "  werkzeug:          $(python3 -c 'from importlib.metadata import version; print(version("werkzeug"))')"
            echo "  prometheus_client: $(python3 -c 'from importlib.metadata import version; print(version("prometheus_client"))')"
          '';
        };

        # `nix flake check` will run this — sanity test of the whole flake.
        checks.default = app;
      });
}
