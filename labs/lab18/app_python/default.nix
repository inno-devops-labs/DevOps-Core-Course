{
  pkgs ? import
    (fetchTarball {
      url = "https://github.com/NixOS/nixpkgs/archive/50ab793786d9de88ee30ec4e4c24fb4236fc2674.tar.gz";
      sha256 = "1s2gr5rcyqvpr58vxdcb095mdhblij9bfzaximrva2243aal3dgx";
    })
    { },
}:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";

  # Filter out build artifacts so the source hash stays stable across rebuilds.
  src = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter =
      path: _type:
      let
        base = baseNameOf (toString path);
      in
      base != "result"
      && !(pkgs.lib.hasPrefix "result-" base)
      && !(pkgs.lib.hasSuffix ".tar.gz" base)
      && base != "__pycache__"
      && base != ".direnv";
  };

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
    prometheus-client
    requests
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  dontUnpack = false;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py

    makeWrapper ${pkgs.python3.interpreter} $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --prefix PYTHONPATH : "$PYTHONPATH"

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "DevOps Info Service - Flask app exposing system info, visit counter, and Prometheus metrics";
    license = licenses.mit;
    platforms = platforms.unix;
  };
}
