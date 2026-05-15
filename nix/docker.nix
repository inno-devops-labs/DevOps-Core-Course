{
  dockerTools,
  appPackage,
}:

dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "lab18";
  created = "1970-01-01T00:00:01Z";

  contents = [
    appPackage
    dockerTools.fakeNss
  ];

  extraCommands = ''
    mkdir -p data tmp
    chmod 0777 data tmp
  '';

  config = {
    Cmd = [ "${appPackage}/bin/devops-info-service" ];
    Env = [
      "HOST=0.0.0.0"
      "PORT=5000"
      "PYTHONDONTWRITEBYTECODE=1"
    ];
    ExposedPorts = {
      "5000/tcp" = { };
    };
    WorkingDir = "/";
    User = "65534:65534";
  };
}
