{
  description = "DevOps Lab 18 - reproducible builds with Nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [
        "aarch64-darwin"
        "x86_64-darwin"
        "aarch64-linux"
        "x86_64-linux"
      ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = import ./default.nix { inherit pkgs; };
          go = import ./go.nix { inherit pkgs; };
          dockerImage = import ./docker.nix { inherit pkgs; };
        });

      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            buildInputs = with pkgs; [
              python3
              python3Packages.flask
              python3Packages.prometheus-client
              go
            ];

            shellHook = ''
              echo "lab18 dev shell ready"
              echo "  python: $(python3 --version)"
              echo "  go:     $(go version | awk '{print $3}')"
              echo "  flask:  $(python3 -c 'import flask; print(flask.__version__)')"
            '';
          };
        });
    };
}
