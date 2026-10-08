# Minimal firmware tools from the exact ARTIQ flake (no GUI or NAC3 build).
let
  source = builtins.getEnv "ARTIQ_SOURCE";
  flake = builtins.getFlake source;
in flake.devShells.x86_64-linux.boards.overrideAttrs (old: {
  nativeBuildInputs = builtins.filter
    (p: builtins.match "(rust-default|llvm|lld|clang)-.*" (p.name or "") != null)
    old.nativeBuildInputs;
  buildInputs = [];
  shellHook = "";
})
