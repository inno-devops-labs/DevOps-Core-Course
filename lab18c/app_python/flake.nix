{
  description = "DevOps Info Service — reproducible Nix build with Flakes";

  inputs = {
    # Pin exact nixpkgs commit (nixos-24.11 stable channel).
    # flake.lock records the precise git SHA — this is what makes Flakes
    # stronger than requirements.txt or Helm image tags.
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      # Change to "x86_64-darwin" (Mac Intel) or "aarch64-darwin" (Mac M-series).
      system = "x86_64-linux";
      pkgs   = nixpkgs.legacyPackages.${system};
    in
    {
      # nix build          → builds the Python app
      # nix build .#dockerImage → builds the Docker image tarball
      packages.${system} = {
        default     = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix  { inherit pkgs; };
      };

      # nix develop  → isolated shell with exact Python + deps
      # Replaces: python -m venv venv && pip install -r requirements.txt
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs.python3Packages; [
          fastapi
          uvicorn
          httptools
          websockets
        ] ++ [ pkgs.python3 ];

        shellHook = ''
          echo "DevOps Info Service dev shell"
          echo "Python: $(python --version)"
          echo "Run:    python app.py"
        '';
      };
    };
}
