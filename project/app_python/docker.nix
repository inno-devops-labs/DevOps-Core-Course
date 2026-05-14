{ pkgs ? import <nixpkgs> { } }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [
    app
    pkgs.cacert
    pkgs.tzdata
  ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = {
      "5000/tcp" = { };
    };
    Env = [
      "HOST=0.0.0.0"
      "PORT=5000"
      "PYTHONUNBUFFERED=1"
      "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
      "TZ=UTC"
    ];
    WorkingDir = "/";
    User = "65532:65532";
    Labels = {
      "org.opencontainers.image.title" = "devops-info-service";
      "org.opencontainers.image.version" = "1.0.0";
      "org.opencontainers.image.source" = "https://github.com/peplxx/DevOps-Core-Course";
      "org.opencontainers.image.description" =
        "Lab 18 — reproducible image built with Nix dockerTools";
    };
  };

  created = "1970-01-01T00:00:01Z";
  maxLayers = 32;
}
