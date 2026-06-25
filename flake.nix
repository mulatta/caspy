{
  description = "caspy: light python library for content-addressable store";

  inputs = {
    # keep-sorted start
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";
    treefmt-nix.url = "github:numtide/treefmt-nix";
    # keep-sorted end
  };

  outputs =
    {
      self,
      nixpkgs,
      treefmt-nix,
    }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
      ];

      eachSystem =
        f:
        nixpkgs.lib.genAttrs systems (
          system:
          f {
            inherit system;
            pkgs = nixpkgs.legacyPackages.${system};
          }
        );

      treefmtEval = eachSystem (
        { pkgs, ... }:
        treefmt-nix.lib.evalModule pkgs {
          projectRootFile = "flake.nix";
          programs = {
            # keep-sorted start
            deadnix.enable = true;
            keep-sorted.enable = true;
            nixfmt.enable = true;
            ruff-check.enable = true;
            ruff-format.enable = true;
            statix.enable = true;
            # keep-sorted end
          };
        }
      );
    in
    {
      # Zero-dependency core (stdlib hashlib); blake3 is an optional extra
      # exercised by the test suite via nativeCheckInputs.
      packages = eachSystem (
        { pkgs, ... }:
        rec {
          default = caspy;
          caspy = pkgs.python3Packages.buildPythonPackage {
            pname = "caspy";
            version = "0.1.1";
            src = ./.;
            pyproject = true;
            build-system = [ pkgs.python3Packages.hatchling ];
            nativeCheckInputs = [
              # keep-sorted start
              pkgs.python3Packages.blake3
              pkgs.python3Packages.pytestCheckHook
              # keep-sorted end
            ];
            pythonImportsCheck = [ "caspy" ];
          };
        }
      );

      devShells = eachSystem (
        { pkgs, ... }:
        {
          default = pkgs.mkShell {
            shellHook = "export PYTHONPATH=$PWD/src\${PYTHONPATH:+:$PYTHONPATH}";
            packages = [
              (pkgs.python3.withPackages (
                ps: with ps; [
                  # keep-sorted start
                  blake3
                  pytest
                  # keep-sorted end
                ]
              ))
              pkgs.ruff
            ];
          };
        }
      );

      checks = eachSystem (
        { system, ... }:
        {
          formatting = treefmtEval.${system}.config.build.check self;
          package = self.packages.${system}.caspy;
        }
      );

      formatter = eachSystem ({ system, ... }: treefmtEval.${system}.config.build.wrapper);
    };
}
