//! Trusted-kernel userspace ABI probe, not a production ARTIQ runtime.
use std::sync::Mutex;

extern "C" {
    fn __clear_cache(start: *mut u8, end: *mut u8);
}

#[derive(Default)]
struct State {
    now: i64,
    initialized: usize,
    integers: Vec<i64>,
    floats: Vec<f64>,
    outputs: Vec<(i64, i32, i32)>,
    writebacks: usize,
}
static STATE: Mutex<State> = Mutex::new(State {
    now: 0,
    initialized: 0,
    integers: Vec::new(),
    floats: Vec::new(),
    outputs: Vec::new(),
    writebacks: 0,
});

extern "C" fn rtio_init() {
    STATE.lock().unwrap().initialized += 1;
}
extern "C" fn rtio_get_counter() -> i64 {
    0
}
extern "C" fn at_mu(value: i64) {
    STATE.lock().unwrap().now = value;
}
extern "C" fn now_mu() -> i64 {
    STATE.lock().unwrap().now
}
extern "C" fn delay_mu(value: i64) {
    STATE.lock().unwrap().now += value;
}
extern "C" fn rtio_output(target: i32, data: i32) {
    let mut state = STATE.lock().unwrap();
    let now = state.now;
    state.outputs.push((now, target, data));
}
extern "C" fn abi_check64(value: i64) {
    STATE.lock().unwrap().integers.push(value);
}
extern "C" fn abi_check_float(value: f64) -> f64 {
    STATE.lock().unwrap().floats.push(value);
    value + 2.5
}
#[repr(C)]
struct CSlice {
    pointer: *const u8,
    length: usize,
}
extern "C" fn rpc_send_async(service: u32, tag: &CSlice, _data: *const *const ()) {
    let bytes = unsafe { std::slice::from_raw_parts(tag.pointer, tag.length) };
    println!("writeback service={service} tags={bytes:?}");
    assert_eq!(service, 0, "only empty automatic writeback is supported");
    assert_eq!(bytes, b":n", "no application RPC is supported");
    STATE.lock().unwrap().writebacks += 1;
}
// These symbols are referenced by compiler-generated exception/writeback paths.
// Fail explicitly if those unimplemented paths execute.
extern "C" fn unsupported() -> ! {
    eprintln!("FAIL: exception/RPC support is outside this ABI probe");
    std::process::exit(3)
}
fn resolve(name: &[u8]) -> Option<u32> {
    let address = match name {
        b"rtio_init" => rtio_init as usize,
        b"rtio_get_counter" => rtio_get_counter as usize,
        b"at_mu" => at_mu as usize,
        b"now_mu" => now_mu as usize,
        b"delay_mu" => delay_mu as usize,
        b"rtio_output" => rtio_output as usize,
        b"abi_check64" => abi_check64 as usize,
        b"abi_check_float" => abi_check_float as usize,
        b"rpc_send_async" => rpc_send_async as usize,
        b"__nac3_resume" | b"__nac3_personality" => unsupported as usize,
        _ => return None,
    };
    Some(address as u32)
}
fn main() {
    assert_eq!(std::mem::size_of::<usize>(), 4, "requires an ARM32 process");
    let path = std::env::args()
        .nth(1)
        .expect("specify trusted NAC3 module.elf");
    let data = std::fs::read(path).unwrap();
    let library = dyld::load(&data, &resolve).expect("upstream loader rejected kernel");
    let entry = library
        .lookup(b"__modinit__")
        .expect("missing kernel entry");
    unsafe {
        let start = library.image.ptr() as usize;
        let page = libc::sysconf(libc::_SC_PAGESIZE) as usize;
        let lower = start & !(page - 1);
        let upper = (start + library.image.data.len() + page - 1) & !(page - 1);
        // RWX is restricted to this disposable trusted-kernel test process.
        assert_eq!(
            libc::mprotect(
                lower as *mut _,
                upper - lower,
                libc::PROT_READ | libc::PROT_WRITE | libc::PROT_EXEC
            ),
            0
        );
        __clear_cache(
            start as *mut u8,
            (start + library.image.data.len()) as *mut u8,
        );
        let run: extern "C" fn() = std::mem::transmute(entry as usize);
        run();
    }
    let state = STATE.lock().unwrap();
    assert_eq!(state.initialized, 1);
    assert_eq!(state.writebacks, 1);
    assert_eq!(state.integers, [0x1234567887654321, 0x100000052]);
    assert_eq!(state.floats, [1.25, 3.75]);
    assert_eq!(state.outputs, [(0x100000020, 0, 1), (0x100000052, 0, 0)]);
    println!("PASS: actual NAC3 kernel loaded and executed; i64/hard-float/timeline/output ABI");
    println!(
        "SIMULATION ONLY: no physical RTIO, DDR, Ethernet, RPC or exception-unwind validation"
    );
}
