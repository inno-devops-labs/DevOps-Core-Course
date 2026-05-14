{
    pkgs ? import <nixpkgs> {
    } 
}:

let
  app = import ./default.nix { inherit pkgs; };

in pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [
    app
    pkgs.bash
    pkgs.coreutils
  ];

  config = {
    Cmd = [ 
        "${pkgs.bash}/bin/bash"
        "-c"
        ''
            echo contents of app;
            ls -la ${app}/bin/devops-info-service";
            echo file contents;
            cat ${app}/bin/devops-info-service;
            echo executing;
            ${app}/bin/devops-info-service
        '' 
    ];

    ExposedPorts = {
      "12345/tcp" = { };
    };

    Env = [
      "PORT=12345"
      "HOST=0.0.0.0"
    ];
  };

  created = "1970-01-01T00:00:01Z";
}
