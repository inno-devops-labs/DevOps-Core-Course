{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication rec {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi
    uvicorn
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/${pname}
    chmod +x $out/bin/${pname}
    wrapProgram $out/bin/${pname} --prefix PYTHONPATH : "$PYTHONPATH"
  '';

  meta = with pkgs.lib; {
    description = "DevOps Info Service – Reproducible build with Nix";
    license = licenses.mit;
    maintainers = [ maintainers.yourname ];
  };
}