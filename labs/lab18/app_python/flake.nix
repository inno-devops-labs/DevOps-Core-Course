{
  description = "Lab 18 — reproducible DevOps Info Service (Nix + optional dockerTools)";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      inherit (nixpkgs) lib;
    in
    {
      packages = lib.genAttrs systems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = import ./default.nix { inherit pkgs; };
          docker = import ./docker.nix { inherit pkgs; };
        }
      );
    };
}
