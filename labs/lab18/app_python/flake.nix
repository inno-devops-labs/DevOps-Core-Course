{
  description = "DevOps Info Service - Reproducible Build";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
  let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};

    pythonEnv = pkgs.python3.withPackages (ps: with ps; [
      flask
      python-json-logger
      prometheus-client
    ]);

    app = pkgs.stdenv.mkDerivation {
      name = "app";
      src = ./.;

      installPhase = ''
        mkdir -p $out/lib
        cp app.py $out/lib/app.py
      '';
    };

  in {
    packages.${system} = {
      default = pkgs.stdenv.mkDerivation {
        name = "devops-info-service-flake";
        version = "1.0.0";

        src = ./.;

        installPhase = ''
          mkdir -p $out/bin

          cat > $out/bin/devops-info-service <<EOF
#!/bin/sh
exec ${pythonEnv}/bin/python ${app}/lib/app.py
EOF

          chmod +x $out/bin/devops-info-service
        '';
      };

      dockerImage = pkgs.dockerTools.buildLayeredImage {
        name = "devops-info-service-flake";
        tag = "1.0.0";

        contents = [ pythonEnv app ];

        config = {
          Cmd = [ "${pythonEnv}/bin/python" "${app}/lib/app.py" ];
          ExposedPorts = {
            "5000/tcp" = {};
          };
        };

        created = "1970-01-01T00:00:01Z";
      };
    };
  };
}
