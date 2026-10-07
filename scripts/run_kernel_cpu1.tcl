# Usage: xsdb run_a53_ddr.tcl SERVER_URL ELF32 ELF64 CABLE_SERIAL EXPECTED_STATUS
if {[llength $argv] != 5} {error "Require SERVER_URL ELF32 ELF64 CABLE_SERIAL EXPECTED_STATUS"}
lassign $argv server elf32 elf64 cable_serial expected_status
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
set state [mrd -value 0xFD070004]
if {($state & 7) != 1} {error "DDR controller not normal"}
configparams force-mem-accesses 1
mwr -bypass-cache-sync 0x200FF000 0 3
select_genesys_target "Cortex-A53 #1"
catch {stop}
rst -processor -clear-registers
catch {stop}
dow $elf32
rst -processor -clear-registers
catch {stop}
dow $elf64
con
after 2000
select_genesys_target PSU
set status [mrd -address-space AP0 -value 0x200FF000]
puts "KERNEL_STATUS=$status"
set trap_lr [mrd -address-space AP0 -value 0x200FF004]
puts "TRAP_LR=$trap_lr"
if {$trap_lr != 0} {error "Unexpected hardware exception at LR=$trap_lr"}
if {$expected_status ni {PASS FAIL}} {error "Expected status must be PASS or FAIL"}
set expected [expr {$expected_status eq "PASS" ? 0x50415353 : 0x4641494c}]
if {$status != $expected} {error "A53 kernel diagnostic unexpected status: $status"}
puts "TEST a53_kernel_loader $expected_status"
if {$expected_status eq "FAIL"} {puts "TEST negative_control PASS"}
puts "TEST ttl_physical NOT_RUN; RTIO calls use memory-only model"
disconnect
