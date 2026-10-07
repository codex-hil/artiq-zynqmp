use std::{env, fs, path::PathBuf};
fn main() {
    let output = PathBuf::from(env::var_os("OUT_DIR").unwrap());
    let ocm = env::var_os("CARGO_FEATURE_OCM").is_some();
    let memory = if ocm { "memory-ocm.x" } else { "memory.x" };
    fs::copy(memory, output.join("memory.x")).unwrap();
    if ocm {
        let script = fs::read_to_string("ocm-link.x").unwrap().replace(
            "INCLUDE memory.x",
            &format!("INCLUDE {}", output.join("memory.x").display()),
        );
        fs::write(output.join("ocm-link.x"), script).unwrap();
        println!(
            "cargo:rustc-link-arg=-T{}",
            output.join("ocm-link.x").display()
        );
    } else {
        println!("cargo:rustc-link-arg=-Tlink.x");
    }
    println!("cargo:rustc-link-search={}", output.display());
    for file in ["memory.x", "memory-ocm.x", "ocm-link.x"] {
        println!("cargo:rerun-if-changed={file}");
    }
}
