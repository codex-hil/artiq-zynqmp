#!/usr/bin/env python3
"""Extract pinned Ubuntu 24.04 tools locally; does not modify host packages."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    registry = Path(__file__).with_name("abi-tools.json")
    packages = json.loads(registry.read_text())
    output = args.output.resolve()
    downloads = output / "debs"
    downloads.mkdir(parents=True, exist_ok=True)
    root = output / "root"
    root.mkdir(exist_ok=True)
    for package in packages:
        deb = downloads / package["file"]
        if not deb.exists():
            subprocess.run(["apt", "download", package["name"] + "=" + package["version"]],
                           cwd=downloads, check=True)
        actual = hashlib.sha256(deb.read_bytes()).hexdigest()
        if actual != package["sha256"]:
            raise RuntimeError(f"Checksum mismatch: {deb}")
        subprocess.run(["dpkg-deb", "-x", str(deb), str(root)], check=True)
    binaries = output / "bin"
    binaries.mkdir(exist_ok=True)
    for name, target in [("clang-irrt", "clang"), ("llvm-as-irrt", "llvm-as")]:
        link = binaries / name
        if link.is_symlink():
            link.unlink()
        elif link.exists():
            raise RuntimeError(f"Refusing to replace existing file: {link}")
        link.symlink_to(root / "usr/lib/llvm-19/bin" / target)
    (output / "manifest.json").write_text(registry.read_text())
    print(f"Extracted {len(packages)} verified packages to {root}")


if __name__ == "__main__":
    main()
