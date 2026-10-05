#!/usr/bin/env python3
"""Compile an actual NAC3 kernel and execute it in ARM userspace and A53 bare metal."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

NAC3_REV = "322b7bd2537e176d7997f816ae2fb6ab9e029939"
TARGET = "armv7-unknown-linux-gnueabihf"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nac3-source", type=Path, required=True)
    parser.add_argument("--tools", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--artiq-source", type=Path)
    parser.add_argument("--sipyco-source", type=Path)
    parser.add_argument("--compiler-toolchain", default="stable")
    parser.add_argument("--compiler-rustup-home", type=Path, default=Path.home() / ".rustup")
    parser.add_argument("--runtime-rustup-home", type=Path,
                        default=Path(os.environ.get("RUSTUP_HOME", Path.home() / ".rustup")))
    args = parser.parse_args()
    if bool(args.artiq_source) != bool(args.sipyco_source):
        parser.error("--artiq-source and --sipyco-source must be specified together")
    repo = Path(__file__).resolve().parent.parent
    source, tools, output = (p.resolve() for p in (args.nac3_source, args.tools, args.output))
    output.mkdir(parents=True, exist_ok=True)
    # Replace any previous success before attempting this run.
    report = output / "results.json"
    report.write_text(json.dumps({"status": "INCOMPLETE", "hardware": "NOT_RUN"}) + "\n")
    actual = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if actual != NAC3_REV:
        raise RuntimeError(f"Expected NAC3 {NAC3_REV}, got {actual}")
    subprocess.run(["git", "-C", str(source), "diff", "--exit-code"], check=True,
                   stdout=subprocess.DEVNULL)
    root = tools / "root"
    env = os.environ.copy()
    env.pop("RUSTFLAGS", None)
    env["PATH"] = os.pathsep.join(map(str, [tools / "bin", root / "usr/bin",
                                          root / "usr/lib/llvm-19/bin"])) + os.pathsep + env["PATH"]
    libraries = str(root / "usr/lib/x86_64-linux-gnu")
    env["LD_LIBRARY_PATH"] = libraries + (os.pathsep + env["LD_LIBRARY_PATH"]
                                         if env.get("LD_LIBRARY_PATH") else "")
    env["LIBRARY_PATH"] = libraries
    env["LLVM_SYS_191_PREFIX"] = str(root / "usr/lib/llvm-19")
    records = []

    def run(name, command, cwd=repo, extra=None, expected=0, timeout=600):
        command = list(map(str, command))
        process_env = env | (extra or {})
        with (output / (name + ".log")).open("w") as log:
            result = subprocess.run(command, cwd=cwd, env=process_env, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=timeout)
        records.append({"name": name, "command": command, "returncode": result.returncode,
                        "expected": expected})
        if result.returncode != expected:
            raise RuntimeError(f"{name}: exit {result.returncode}; see {output / (name + '.log')}")
        return (output / (name + ".log")).read_text()

    compiler_env = {"RUSTUP_HOME": str(args.compiler_rustup_home.resolve())}
    compiler_target = output / "compiler"
    run("compiler-build", ["cargo", "+" + args.compiler_toolchain, "build", "--release",
                            "--locked", "-p", "nac3artiq", "--target-dir", compiler_target],
        source, compiler_env)
    runtime_env = {
        "RUSTUP_HOME": str(args.runtime_rustup_home.resolve()),
        "CARGO_TARGET_ARMV7_UNKNOWN_LINUX_GNUEABIHF_LINKER": str(root / "usr/bin/arm-linux-gnueabihf-gcc"),
        "CARGO_TARGET_ARMV7_UNKNOWN_LINUX_GNUEABIHF_RUSTFLAGS": "-C link-arg=--sysroot=" + str(root),
    }
    runtime_target = output / "runtime"
    prototype = repo / "prototypes/kernel-abi"
    run("runtime-build", ["cargo", "+1.87.0", "build", "--release", "--locked", "--target", TARGET,
                           "--target-dir", runtime_target], prototype, runtime_env)
    baremetal = prototype / "baremetal"
    bare_target = output / "baremetal"
    bare_target.mkdir(exist_ok=True)
    run("startup64-build", ["clang", "--target=aarch64-none-elf", "-fuse-ld=lld", "-nostdlib",
                            "-Wl,-T,link64.ld", "start64.S", "-o", bare_target / "start64.elf"], baremetal)
    source_revisions = {"nac3": NAC3_REV}
    if args.artiq_source:
        for name, path in [("artiq", args.artiq_source), ("sipyco", args.sipyco_source)]:
            source_revisions[name] = subprocess.check_output(
                ["git", "-C", str(path.resolve()), "rev-parse", "HEAD"], text=True).strip()
            subprocess.run(["git", "-C", str(path.resolve()), "diff", "--exit-code"],
                           stdout=subprocess.DEVNULL, check=True)
    variants = ("positive", "negative", "artiq") if args.artiq_source else ("positive", "negative")
    for variant in variants:
        directory = output / variant
        directory.mkdir(exist_ok=True)
        shutil.copy(source / "nac3artiq/demo/min_artiq.py", directory / "min_artiq.py")
        shutil.copy(compiler_target / "release/libnac3artiq.so", directory / "nac3artiq.so")
        (directory / "device_db.py").write_text(
            'device_db = {"core": {"arguments": {"target": "cortexa9", "ref_period": 8e-9}}}\n')
        probe = (prototype / ("artiq_probe.py" if variant == "artiq" else "probe.py")).read_text()
        if variant == "negative":
            probe = probe.replace("0x1234567887654321", "0x1234567887654320")
        (directory / "probe.py").write_text(probe)
        compile_env = {}
        if variant == "artiq":
            compile_env["PYTHONPATH"] = os.pathsep.join([
                str(args.artiq_source.resolve()), str(args.sipyco_source.resolve())])
        run(variant + "-compile", [os.sys.executable, "probe.py"], directory, compile_env)
        if variant != "negative":
            text = run(variant + "-userspace-qemu", ["qemu-arm", "-cpu", "cortex-a15", "-L",
                       root / "usr/arm-linux-gnueabihf",
                       runtime_target / TARGET / "release/genesys-kernel-abi-probe", directory / "module.elf"])
            if "PASS: actual NAC3 kernel" not in text:
                raise RuntimeError("Userspace probe did not report completion")
        bare_env = runtime_env | {
            "KERNEL_ELF": str(directory / "module.elf"),
            "CARGO_TARGET_ARMV7_UNKNOWN_LINUX_GNUEABIHF_RUSTFLAGS":
                "-C target-cpu=cortex-a9 -C relocation-model=static",
        }
        run(variant + "-baremetal-build", ["cargo", "+1.87.0", "build", "--release", "--locked",
             "--target", TARGET, "--target-dir", bare_target], baremetal, bare_env)
        elf = directory / "probe32.elf"
        run(variant + "-baremetal-link", ["arm-linux-gnueabihf-gcc", "-nostdlib", "-static", "-no-pie",
             "-mcpu=cortex-a9", "-marm", "-mfpu=neon", "-mfloat-abi=hard", "-ffreestanding",
             "-fno-builtin", "-O2", "-Wl,--gc-sections", "-Wl,-T,link32.ld", "start32.S", "probe.c",
             bare_target / TARGET / "release/libgenesys_aarch32_loader_probe.a", "-lgcc", "-o", elf], baremetal)
        text = run(variant + "-a53-qemu", ["qemu-system-aarch64", "-M", "virt,secure=on,virtualization=on",
             "-cpu", "cortex-a53", "-m", "128M", "-nographic", "-monitor", "none", "-nic", "none",
             "-semihosting-config", "enable=on,target=native", "-device",
             "loader,file=" + str(bare_target / "start64.elf") + ",cpu-num=0",
             "-device", "loader,file=" + str(elf)], expected=3 if variant == "negative" else 0, timeout=20)
        marker = "FAIL: bare-metal kernel ABI probe" if variant == "negative" else "PASS: A53 bare-metal NAC3 kernel"
        if marker not in text or (variant == "negative" and "PASS:" in text):
            raise RuntimeError(f"Unexpected {variant} QEMU result")
    versions = {}
    for name, command, extra in [
        ("compiler_rust", ["rustc", "+" + args.compiler_toolchain, "--version"], compiler_env),
        ("runtime_rust", ["rustc", "+1.87.0", "--version"], runtime_env),
        ("llvm", ["llvm-config", "--version"], {}),
        ("qemu", ["qemu-system-aarch64", "--version"], {}),
    ]:
        versions[name] = run("version-" + name, command, extra=extra).strip()
    artifacts = {}
    for path in [output / "positive/module.elf", output / "positive/probe32.elf", bare_target / "start64.elf"]:
        artifacts[str(path.relative_to(output))] = hashlib.sha256(path.read_bytes()).hexdigest()
    if args.artiq_source:
        for path in [output / "artiq/module.elf", output / "artiq/probe32.elf"]:
            artifacts[str(path.relative_to(output))] = hashlib.sha256(path.read_bytes()).hexdigest()
    report.write_text(json.dumps({"status": "PASS", "mode": "EMULATED", "hardware": "NOT_RUN",
        "source_revisions": source_revisions, "versions": versions, "artifacts_sha256": artifacts,
        "checks": ["ARM32 upstream loader", "A53 EL3/AArch64 to EL1/AArch32", "i64 ABI",
                   "hard-float argument/return", "timeline", "empty automatic writeback",
                   "negative wrong i64 rejected"], "commands": records}, indent=2) + "\n")
    print("PASS: kernel ABI emulation including A53 bare metal and negative control")
    print(f"Evidence: {report}; hardware NOT_RUN")


if __name__ == "__main__":
    main()
