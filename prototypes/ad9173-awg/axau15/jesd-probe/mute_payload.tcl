# Emergency volatile SPI mute, exact cable + DAC identity. Does not touch HMC.
source [file join [file dirname [info script]] transport.tcl]
$sq clear;$sq irshift -state IDLE -integer 6 3;$sq drshift -state IDLE -tdi 0 64;$sq run
gpio 12
if {[readreg 4]!=0x72 || [readreg 5]!=0x91} {error "Refuse mute on unknown DAC"}
transfer [expr {(8<<8)|192}]
transfer [expr {(1430<<8)|4}]
transfer [expr {(63<<8)|48}]
if {([readreg 1430]&12)!=4} {error "Mute readback failed"}
gpio 12
$sq clear;$sq irshift -state IDLE -integer 6 63;$sq run
disconnect
puts "AD9172_SPI_MUTED"
