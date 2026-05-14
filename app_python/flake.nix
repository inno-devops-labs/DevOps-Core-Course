{
  description = "DevOps Info Service — Reproducible Build with Nix Flakes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      # Mac M1/M2/M3/M4 — change to x86_64-darwin for Intel Mac
      system = "aarch64-darwin";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system} = {
        default = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      };

      # Development shell: exact same env on every machine
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs.python3Packages; [
          fastapi
          uvicorn
          pydantic
          python-json-logger
          prometheus-client
        ];
      };
    };
}
