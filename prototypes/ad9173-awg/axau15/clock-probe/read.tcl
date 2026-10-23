connect -url tcp:localhost:3121
set matches [jtag targets -target-properties -filter {jtag_cable_serial == "210512180081" && name == "xcau15p"}]
if {[llength $matches]!=1} {error "AXAU15 identity mismatch"}
set p [lindex $matches 0]
if {[string tolower [dict get $p idcode]] ne "04ac2093"} {error "IDCODE mismatch"}
jtag targets [dict get $p node_id]
set sq [jtag sequence]
proc sample {} {
 global sq
 $sq clear
 $sq irshift -state IDLE -integer 6 2
 $sq drshift -state IDLE -capture -tdi 0 64
 set h [lindex [$sq run -hex] 0]
 binary scan [binary format H* $h] i2 words
 if {[lindex $words 1] != 0x41583135} {error "Clock-probe signature mismatch $h"}
 set g [expr {[lindex $words 0]&0xffffffff}]
 set n $g
 for {set shift 1} {$shift<32} {set shift [expr {$shift*2}]} {set n [expr {$n ^ ($n >> $shift)}]}
 return $n
}
# Prime the two TCK-clocked synchronizer stages; compare subsequent captures.
sample
sample
set prev [sample]
for {set i 0} {$i<3} {incr i} {
 after 100
 sample
 sample
 set n [sample]
 set delta [expr {($n-$prev)&0xffffffff}]
 puts "CLOCK_SAMPLE $i $n DELTA $delta"
 if {$delta<1000000 || $delta>100000000} {error "Clock counter not advancing at plausible rate"}
 set prev $n
}
puts "AXAU15_CLOCK_ACTIVITY_PASS_NOT_PRECISION_FREQUENCY_MEASUREMENT"
$sq clear
$sq irshift -state IDLE -integer 6 63
$sq run
disconnect
