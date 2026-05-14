{ pkgs ? import <nixpkgs> {} }:

let
  # Docker runs Linux/aarch64; Nix on macOS builds darwin by default.
  # python3.withPackages requires running a builder on the target system, which
  # is unavailable on macOS without a remote Linux builder. Instead:
  #  - fetch individual pre-built aarch64-linux packages from binary cache
  #  - build the entrypoint script on the host (writeTextFile runs on macOS)
  #  - wire PYTHONPATH so the Linux Python interpreter finds the packages
  linuxPkgs = import <nixpkgs> { system = "aarch64-linux"; };
  python = linuxPkgs.python3;

  deps = with linuxPkgs.python3Packages; [
    flask werkzeug jinja2 click markupsafe itsdangerous blinker
    python-json-logger typing-extensions
    prometheus-client
  ];

  # makeSearchPath runs on the host — pure string computation, no building.
  pythonPath = pkgs.lib.makeSearchPath python.sitePackages deps;

  # writeTextFile runs on the host (macOS); output is a plain text script.
  # The shebang points to the Linux Python in the Nix store, which will be
  # present in the Docker image via the `contents` list below.
  entrypoint = pkgs.writeTextFile {
    name = "devops-info-service";
    executable = true;
    destination = "/bin/devops-info-service";
    text = "#!${python}/bin/python3\n" + builtins.readFile ./app.py;
  };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [ entrypoint python linuxPkgs.coreutils ] ++ deps;

  config = {
    Cmd = [ "${entrypoint}/bin/devops-info-service" ];
    ExposedPorts = {
      "5001/tcp" = {};
    };
    Env = [
      "PORT=5001"
      "HOST=0.0.0.0"
      "DEBUG=False"
      "PYTHONPATH=${pythonPath}"
    ];
  };

  created = "1970-01-01T00:00:01Z";
}
