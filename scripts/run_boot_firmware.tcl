# Usage: xsdb run_boot_firmware.tcl SERVER_URL PMU_ELF FSBL_ELF CABLE_SERIAL
if {[llength $argv] != 4} {error "Require SERVER_URL PMU_ELF FSBL_ELF CABLE_SERIAL"}
lassign $argv server pmu_elf fsbl_elf cable_serial
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
for {set i 0} {$i < 4} {incr i} {select_genesys_target "Cortex-A53 #$i"; catch {stop}}
select_genesys_target PSU
puts "BOOT_MODE_BEFORE=[mrd 0xFF5E0200]"
# Preserve physical boot switches, select alternate JTAG for this debug session.
mwr 0xFF5E0200 0x10E
# AMD UG1137 JTAG flow: PMU firmware must run before FSBL.
mwr 0xFFCA0038 0x1FF
after 500
select_genesys_target "MicroBlaze PMU"
catch {stop}
dow $pmu_elf
con
after 500
select_genesys_target "Cortex-A53 #0"
rst -processor -clear-registers
catch {stop}
dow $fsbl_elf
con
puts "PIOTR_FSBL_STARTED"
disconnect
