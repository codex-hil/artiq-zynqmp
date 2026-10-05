{
  inputs = {
    self.submodules = true;
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    rust-overlay = {
      url = "github:oxalica/rust-overlay";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    artiq = {
      url = "path:common/artiq";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    rust-overlay,
    artiq,
  }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs {
      inherit system;
      overlays = [(import rust-overlay)];
    };
  in {
    devShells.${system}.default = pkgs.mkShell {
      packages = [
        # Code quality tools (linters/formatters)
        pkgs.alejandra
        pkgs.shellcheck
        pkgs.clang-tools
        pkgs.python3Packages.isort
        pkgs.python3Packages.black
        pkgs.python3Packages.pylint
        pkgs.python3Packages.mypy

        # Rust toolchain
        (pkgs.rust-bin.stable."1.87.0".default.override {
          extensions = ["rust-src"];
          targets = ["armv7r-none-eabihf" "aarch64-unknown-none"];
        })

        # ARTIQ and Migen dependencies
        artiq.packages.${system}.artiq.propagatedBuildInputs
        pkgs.python3Packages.colorama

        # The gen-machineconf tool requires pyymal
        pkgs.python3Packages.pyyaml

        # Various Python packages - mainly for local source code resolution and
        # letting mypy/pylint work
        pkgs.python3Packages.setuptools
        pkgs.python3Packages.types-setuptools
      ];

      shellHook = ''
        . "./envsetup.bash"
      '';
    };
  };
}
