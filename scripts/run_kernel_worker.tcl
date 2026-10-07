# Usage: xsdb run_kernel_worker.tcl SERVER_URL ELF32 ELF64 CABLE_SERIAL
if {[llength $argv] != 4} {error "Require SERVER_URL ELF32 ELF64 CABLE_SERIAL"}
lassign $argv server elf32 elf64 cable_serial
proc select_genesys_target {name} {
    global cable_serial
    set matches {}
    foreach properties [targets -target-properties -filter "name == \"$name\""] {
        if {[dict exists $properties jtag_cable_serial] && [dict get $properties jtag_cable_serial] eq $cable_serial} {
            lappend matches [dict get $properties target_id]
        }
    }
    if {[llength $matches] != 1} {error "Target $name on $cable_serial not uniquely identified"}
    targets -set [lindex $matches 0]
}
connect -url $server
select_genesys_target PSU
configparams force-mem-accesses 1
set state [mrd -address-space AP0 -value 0xFD070004]
if {($state & 7) != 1} {error "DDR not initialized"}
mwr -bypass-cache-sync 0x200FF000 0 1152
select_genesys_target "Cortex-A53 #1"
catch {stop}
rst -processor -clear-registers
catch {stop}
dow $elf32
rst -processor -clear-registers
catch {stop}
dow $elf64
con
after 1000
select_genesys_target PSU
set status [mrd -address-space AP0 -value 0x200FF044]
if {$status != 1} {error "CPU1 worker not ready: $status"}
puts "TEST cpu1_worker_ready PASS"
disconnect
