{
  description = "DevOps Info Service — reproducible build with Nix Flakes";

  inputs = {
    # Pin exact nixpkgs revision for maximum reproducibility
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      # Mac M1/M2/M3: change to "aarch64-darwin"
      # Mac Intel:    change to "x86_64-darwin"
      # Linux/WSL2:   change to "x86_64-linux"
      system = "aarch64-darwin";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system} = {
        default = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      };

      # Reproducible dev shell — replaces `python -m venv venv && pip install -r requirements.txt`
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python3
          python3Packages.flask
          python3Packages.python-json-logger
          python3Packages.prometheus-client
        ];
        shellHook = ''
          echo "DevOps Info Service dev shell ready"
          echo "Python: $(python3 --version)"
          echo "Flask:  $(python3 -c 'import flask; print(flask.__version__)')"
        '';
      };
    };
}
