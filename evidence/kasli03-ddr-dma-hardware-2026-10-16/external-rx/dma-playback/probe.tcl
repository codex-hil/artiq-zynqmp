lassign $argv server cable
connect -url $server
set matches {}
foreach p [targets -target-properties -filter {name == "PSU"}] {
if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend matches [dict get $p target_id]}
}
if {[llength $matches]!=1} {error "Exact Genesys target missing"}
targets -set [lindex $matches 0]
configparams force-mem-accesses 1
set addr(monitor_magic) 2684354560; set words(monitor_magic) 1
set addr(monitor_reset) 2684354564; set words(monitor_reset) 1
set addr(monitor_tx_enable) 2684354568; set words(monitor_tx_enable) 1
set addr(monitor_loopback) 2684354572; set words(monitor_loopback) 1
set addr(monitor_prbs) 2684354576; set words(monitor_prbs) 1
set addr(monitor_tx_prbs) 2684354580; set words(monitor_tx_prbs) 1
set addr(monitor_snapshot) 2684354584; set words(monitor_snapshot) 1
set addr(monitor_status) 2684354588; set words(monitor_status) 1
set addr(monitor_boot_ticks) 2684354592; set words(monitor_boot_ticks) 1
set addr(monitor_rx_ticks) 2684354596; set words(monitor_rx_ticks) 1
set addr(monitor_tx_ticks) 2684354600; set words(monitor_tx_ticks) 1
set addr(monitor_prbs_errors) 2684354604; set words(monitor_prbs_errors) 1
set addr(dma_address) 2684362752; set words(dma_address) 2
set addr(dma_time_offset) 2684362760; set words(dma_time_offset) 2
set addr(dma_max_bursts) 2684362768; set words(dma_max_bursts) 1
set addr(dma_watchdog) 2684362772; set words(dma_watchdog) 1
set addr(dma_start) 2684362776; set words(dma_start) 1
set addr(dma_abort) 2684362780; set words(dma_abort) 1
set addr(dma_clear) 2684362784; set words(dma_clear) 1
set addr(dma_active) 2684362788; set words(dma_active) 1
set addr(dma_pending) 2684362792; set words(dma_pending) 1
set addr(dma_reject) 2684362796; set words(dma_reject) 1
set addr(dma_result_error) 2684362800; set words(dma_result_error) 1
set addr(dma_result_channel) 2684362804; set words(dma_result_channel) 1
set addr(dma_result_timestamp) 2684362808; set words(dma_result_timestamp) 2
set addr(dma_accepted) 2684362816; set words(dma_accepted) 1
set addr(dma_completed) 2684362820; set words(dma_completed) 1
set addr(aux_aux_tx_length) 2684360704; set words(aux_aux_tx_length) 1
set addr(aux_aux_tx) 2684360708; set words(aux_aux_tx) 1
set addr(aux_aux_rx_present) 2684360712; set words(aux_aux_rx_present) 1
set addr(aux_aux_rx_error) 2684360716; set words(aux_aux_rx_error) 1
set addr(aux_aux_read_pointer) 2684360720; set words(aux_aux_read_pointer) 1
set addr(aux_bridge_busy) 2684360724; set words(aux_bridge_busy) 1
set addr(aux_rx_up) 2684360728; set words(aux_rx_up) 1
set addr(aux_in_reset) 2684360732; set words(aux_in_reset) 1
set addr(aux_tsc_load_count) 2684360736; set words(aux_tsc_load_count) 1
set addr(aux_rt_reply_fault) 2684360740; set words(aux_rt_reply_fault) 1
set addr(aux_rtio_error_flags) 2684360744; set words(aux_rtio_error_flags) 1
set addr(aux_rtio_spread_enable) 2684360748; set words(aux_rtio_spread_enable) 1
set addr(aux_rtio_reset_request) 2684360752; set words(aux_rtio_reset_request) 1
set addr(aux_rtio_reset_applied) 2684360756; set words(aux_rtio_reset_applied) 1
set addr(aux_phy_reset_request) 2684360760; set words(aux_phy_reset_request) 1
set addr(aux_phy_reset_applied) 2684360764; set words(aux_phy_reset_applied) 1
proc wr {name value} {
 global addr words
 for {set i 0} {$i<$words($name)} {incr i} {
  mwr [expr {$addr($name)+4*$i}] [expr {($value>>(32*($words($name)-1-$i)))&0xffffffff}]
 }
}
proc rd {name} {
 global addr words
 set value 0
 for {set i 0} {$i<$words($name)} {incr i} {
  set value [expr {($value<<32)|(wide([mrd -value [expr {$addr($name)+4*$i}]])&0xffffffff)}]
 }
 return $value
}
if {[rd monitor_magic]!=0x44525430} {error "Wrong PL identity"}
foreach n {aux_in_reset aux_rtio_reset_request aux_phy_reset_request aux_rt_reply_fault aux_rtio_error_flags dma_active} {
 if {[rd $n]!=0} {error "Unready DMA/RTIO: $n"}
}
if {[rd aux_rx_up]!=1 || [rd aux_tsc_load_count]==0} {error "No external TSC/link"}
wr dma_clear 1
set accepted [rd dma_accepted]
set completed [rd dma_completed]

mwr 570425344 273
if {(wide([mrd -value 570425344])&0xffffffff)!=273} {error "DDR readback offset 0"}
mwr 570425348 0
if {(wide([mrd -value 570425348])&0xffffffff)!=0} {error "DDR readback offset 4"}
mwr 570425352 0
if {(wide([mrd -value 570425352])&0xffffffff)!=0} {error "DDR readback offset 8"}
mwr 570425356 770
if {(wide([mrd -value 570425356])&0xffffffff)!=770} {error "DDR readback offset 12"}
mwr 570425360 4352
if {(wide([mrd -value 570425360])&0xffffffff)!=4352} {error "DDR readback offset 16"}
mwr 570425364 256000000
if {(wide([mrd -value 570425364])&0xffffffff)!=256000000} {error "DDR readback offset 20"}
mwr 570425368 0
if {(wide([mrd -value 570425368])&0xffffffff)!=0} {error "DDR readback offset 24"}
mwr 570425372 65536
if {(wide([mrd -value 570425372])&0xffffffff)!=65536} {error "DDR readback offset 28"}
mwr 570425376 1114112
if {(wide([mrd -value 570425376])&0xffffffff)!=1114112} {error "DDR readback offset 32"}
mwr 570425380 1635778560
if {(wide([mrd -value 570425380])&0xffffffff)!=1635778560} {error "DDR readback offset 36"}
mwr 570425384 15
if {(wide([mrd -value 570425384])&0xffffffff)!=15} {error "DDR readback offset 40"}
mwr 570425388 0
if {(wide([mrd -value 570425388])&0xffffffff)!=0} {error "DDR readback offset 44"}
mwr 570425392 285212672
if {(wide([mrd -value 570425392])&0xffffffff)!=285212672} {error "DDR readback offset 48"}
mwr 570425396 3221225472
if {(wide([mrd -value 570425396])&0xffffffff)!=3221225472} {error "DDR readback offset 52"}
mwr 570425400 4218
if {(wide([mrd -value 570425400])&0xffffffff)!=4218} {error "DDR readback offset 56"}
mwr 570425404 0
if {(wide([mrd -value 570425404])&0xffffffff)!=0} {error "DDR readback offset 60"}
mwr 570425408 1
if {(wide([mrd -value 570425408])&0xffffffff)!=1} {error "DDR readback offset 64"}
mwr 570425412 17
if {(wide([mrd -value 570425412])&0xffffffff)!=17} {error "DDR readback offset 68"}
mwr 570425416 1088000
if {(wide([mrd -value 570425416])&0xffffffff)!=1088000} {error "DDR readback offset 72"}
mwr 570425420 0
if {(wide([mrd -value 570425420])&0xffffffff)!=0} {error "DDR readback offset 76"}
mwr 570425424 0
if {(wide([mrd -value 570425424])&0xffffffff)!=0} {error "DDR readback offset 80"}
mwr 570425428 4352
if {(wide([mrd -value 570425428])&0xffffffff)!=4352} {error "DDR readback offset 84"}
mwr 570425432 296960000
if {(wide([mrd -value 570425432])&0xffffffff)!=296960000} {error "DDR readback offset 88"}
mwr 570425436 0
if {(wide([mrd -value 570425436])&0xffffffff)!=0} {error "DDR readback offset 92"}
mwr 570425440 65536
if {(wide([mrd -value 570425440])&0xffffffff)!=65536} {error "DDR readback offset 96"}
mwr 570425444 1114112
if {(wide([mrd -value 570425444])&0xffffffff)!=1114112} {error "DDR readback offset 100"}
mwr 570425448 3531603968
if {(wide([mrd -value 570425448])&0xffffffff)!=3531603968} {error "DDR readback offset 104"}
mwr 570425452 17
if {(wide([mrd -value 570425452])&0xffffffff)!=17} {error "DDR readback offset 108"}
mwr 570425456 0
if {(wide([mrd -value 570425456])&0xffffffff)!=0} {error "DDR readback offset 112"}
mwr 570425460 285212672
if {(wide([mrd -value 570425460])&0xffffffff)!=285212672} {error "DDR readback offset 116"}
mwr 570425464 3221225472
if {(wide([mrd -value 570425464])&0xffffffff)!=3221225472} {error "DDR readback offset 120"}
mwr 570425468 4843
if {(wide([mrd -value 570425468])&0xffffffff)!=4843} {error "DDR readback offset 124"}
mwr 570425472 0
if {(wide([mrd -value 570425472])&0xffffffff)!=0} {error "DDR readback offset 128"}
mwr 570425476 1
if {(wide([mrd -value 570425476])&0xffffffff)!=1} {error "DDR readback offset 132"}
mwr 570425480 17
if {(wide([mrd -value 570425480])&0xffffffff)!=17} {error "DDR readback offset 136"}
mwr 570425484 1248000
if {(wide([mrd -value 570425484])&0xffffffff)!=1248000} {error "DDR readback offset 140"}
mwr 570425488 0
if {(wide([mrd -value 570425488])&0xffffffff)!=0} {error "DDR readback offset 144"}
mwr 570425492 0
if {(wide([mrd -value 570425492])&0xffffffff)!=0} {error "DDR readback offset 148"}
mwr 570425496 69888
if {(wide([mrd -value 570425496])&0xffffffff)!=69888} {error "DDR readback offset 152"}
mwr 570425500 512000000
if {(wide([mrd -value 570425500])&0xffffffff)!=512000000} {error "DDR readback offset 156"}
mwr 570425504 0
if {(wide([mrd -value 570425504])&0xffffffff)!=0} {error "DDR readback offset 160"}
mwr 570425508 512
if {(wide([mrd -value 570425508])&0xffffffff)!=512} {error "DDR readback offset 164"}
mwr 570425512 0
if {(wide([mrd -value 570425512])&0xffffffff)!=0} {error "DDR readback offset 168"}
mwr 570425516 0
if {(wide([mrd -value 570425516])&0xffffffff)!=0} {error "DDR readback offset 172"}
mwr 570425520 0
if {(wide([mrd -value 570425520])&0xffffffff)!=0} {error "DDR readback offset 176"}
mwr 570425524 0
if {(wide([mrd -value 570425524])&0xffffffff)!=0} {error "DDR readback offset 180"}
mwr 570425528 0
if {(wide([mrd -value 570425528])&0xffffffff)!=0} {error "DDR readback offset 184"}
mwr 570425532 0
if {(wide([mrd -value 570425532])&0xffffffff)!=0} {error "DDR readback offset 188"}
mwr 570425536 0
if {(wide([mrd -value 570425536])&0xffffffff)!=0} {error "DDR readback offset 192"}
mwr 570425540 0
if {(wide([mrd -value 570425540])&0xffffffff)!=0} {error "DDR readback offset 196"}
mwr 570425544 0
if {(wide([mrd -value 570425544])&0xffffffff)!=0} {error "DDR readback offset 200"}
mwr 570425548 0
if {(wide([mrd -value 570425548])&0xffffffff)!=0} {error "DDR readback offset 204"}
mwr 570425552 0
if {(wide([mrd -value 570425552])&0xffffffff)!=0} {error "DDR readback offset 208"}
mwr 570425556 0
if {(wide([mrd -value 570425556])&0xffffffff)!=0} {error "DDR readback offset 212"}
mwr 570425560 0
if {(wide([mrd -value 570425560])&0xffffffff)!=0} {error "DDR readback offset 216"}
mwr 570425564 0
if {(wide([mrd -value 570425564])&0xffffffff)!=0} {error "DDR readback offset 220"}
mwr 570425568 0
if {(wide([mrd -value 570425568])&0xffffffff)!=0} {error "DDR readback offset 224"}
mwr 570425572 0
if {(wide([mrd -value 570425572])&0xffffffff)!=0} {error "DDR readback offset 228"}
mwr 570425576 0
if {(wide([mrd -value 570425576])&0xffffffff)!=0} {error "DDR readback offset 232"}
mwr 570425580 0
if {(wide([mrd -value 570425580])&0xffffffff)!=0} {error "DDR readback offset 236"}
mwr 570425584 0
if {(wide([mrd -value 570425584])&0xffffffff)!=0} {error "DDR readback offset 240"}
mwr 570425588 0
if {(wide([mrd -value 570425588])&0xffffffff)!=0} {error "DDR readback offset 244"}
mwr 570425592 0
if {(wide([mrd -value 570425592])&0xffffffff)!=0} {error "DDR readback offset 248"}
mwr 570425596 0
if {(wide([mrd -value 570425596])&0xffffffff)!=0} {error "DDR readback offset 252"}
mwr 570425600 0
if {(wide([mrd -value 570425600])&0xffffffff)!=0} {error "DDR readback offset 256"}
mwr 570425604 0
if {(wide([mrd -value 570425604])&0xffffffff)!=0} {error "DDR readback offset 260"}
mwr 570425608 0
if {(wide([mrd -value 570425608])&0xffffffff)!=0} {error "DDR readback offset 264"}
mwr 570425612 0
if {(wide([mrd -value 570425612])&0xffffffff)!=0} {error "DDR readback offset 268"}
mwr 570425616 0
if {(wide([mrd -value 570425616])&0xffffffff)!=0} {error "DDR readback offset 272"}
mwr 570425620 0
if {(wide([mrd -value 570425620])&0xffffffff)!=0} {error "DDR readback offset 276"}
mwr 570425624 0
if {(wide([mrd -value 570425624])&0xffffffff)!=0} {error "DDR readback offset 280"}
mwr 570425628 0
if {(wide([mrd -value 570425628])&0xffffffff)!=0} {error "DDR readback offset 284"}
mwr 570425632 0
if {(wide([mrd -value 570425632])&0xffffffff)!=0} {error "DDR readback offset 288"}
mwr 570425636 0
if {(wide([mrd -value 570425636])&0xffffffff)!=0} {error "DDR readback offset 292"}
mwr 570425640 0
if {(wide([mrd -value 570425640])&0xffffffff)!=0} {error "DDR readback offset 296"}
mwr 570425644 0
if {(wide([mrd -value 570425644])&0xffffffff)!=0} {error "DDR readback offset 300"}
mwr 570425648 0
if {(wide([mrd -value 570425648])&0xffffffff)!=0} {error "DDR readback offset 304"}
mwr 570425652 0
if {(wide([mrd -value 570425652])&0xffffffff)!=0} {error "DDR readback offset 308"}
mwr 570425656 0
if {(wide([mrd -value 570425656])&0xffffffff)!=0} {error "DDR readback offset 312"}
mwr 570425660 0
if {(wide([mrd -value 570425660])&0xffffffff)!=0} {error "DDR readback offset 316"}
mwr 570425664 0
if {(wide([mrd -value 570425664])&0xffffffff)!=0} {error "DDR readback offset 320"}
mwr 570425668 0
if {(wide([mrd -value 570425668])&0xffffffff)!=0} {error "DDR readback offset 324"}
mwr 570425672 0
if {(wide([mrd -value 570425672])&0xffffffff)!=0} {error "DDR readback offset 328"}
mwr 570425676 0
if {(wide([mrd -value 570425676])&0xffffffff)!=0} {error "DDR readback offset 332"}
mwr 570425680 0
if {(wide([mrd -value 570425680])&0xffffffff)!=0} {error "DDR readback offset 336"}
mwr 570425684 0
if {(wide([mrd -value 570425684])&0xffffffff)!=0} {error "DDR readback offset 340"}
mwr 570425688 0
if {(wide([mrd -value 570425688])&0xffffffff)!=0} {error "DDR readback offset 344"}
mwr 570425692 0
if {(wide([mrd -value 570425692])&0xffffffff)!=0} {error "DDR readback offset 348"}
mwr 570425696 0
if {(wide([mrd -value 570425696])&0xffffffff)!=0} {error "DDR readback offset 352"}
mwr 570425700 0
if {(wide([mrd -value 570425700])&0xffffffff)!=0} {error "DDR readback offset 356"}
mwr 570425704 0
if {(wide([mrd -value 570425704])&0xffffffff)!=0} {error "DDR readback offset 360"}
mwr 570425708 0
if {(wide([mrd -value 570425708])&0xffffffff)!=0} {error "DDR readback offset 364"}
mwr 570425712 0
if {(wide([mrd -value 570425712])&0xffffffff)!=0} {error "DDR readback offset 368"}
mwr 570425716 0
if {(wide([mrd -value 570425716])&0xffffffff)!=0} {error "DDR readback offset 372"}
mwr 570425720 0
if {(wide([mrd -value 570425720])&0xffffffff)!=0} {error "DDR readback offset 376"}
mwr 570425724 0
if {(wide([mrd -value 570425724])&0xffffffff)!=0} {error "DDR readback offset 380"}
mwr 570425728 0
if {(wide([mrd -value 570425728])&0xffffffff)!=0} {error "DDR readback offset 384"}
mwr 570425732 0
if {(wide([mrd -value 570425732])&0xffffffff)!=0} {error "DDR readback offset 388"}
mwr 570425736 0
if {(wide([mrd -value 570425736])&0xffffffff)!=0} {error "DDR readback offset 392"}
mwr 570425740 0
if {(wide([mrd -value 570425740])&0xffffffff)!=0} {error "DDR readback offset 396"}
mwr 570425744 0
if {(wide([mrd -value 570425744])&0xffffffff)!=0} {error "DDR readback offset 400"}
mwr 570425748 0
if {(wide([mrd -value 570425748])&0xffffffff)!=0} {error "DDR readback offset 404"}
mwr 570425752 0
if {(wide([mrd -value 570425752])&0xffffffff)!=0} {error "DDR readback offset 408"}
mwr 570425756 0
if {(wide([mrd -value 570425756])&0xffffffff)!=0} {error "DDR readback offset 412"}
mwr 570425760 0
if {(wide([mrd -value 570425760])&0xffffffff)!=0} {error "DDR readback offset 416"}
mwr 570425764 0
if {(wide([mrd -value 570425764])&0xffffffff)!=0} {error "DDR readback offset 420"}
mwr 570425768 0
if {(wide([mrd -value 570425768])&0xffffffff)!=0} {error "DDR readback offset 424"}
mwr 570425772 0
if {(wide([mrd -value 570425772])&0xffffffff)!=0} {error "DDR readback offset 428"}
mwr 570425776 0
if {(wide([mrd -value 570425776])&0xffffffff)!=0} {error "DDR readback offset 432"}
mwr 570425780 0
if {(wide([mrd -value 570425780])&0xffffffff)!=0} {error "DDR readback offset 436"}
mwr 570425784 0
if {(wide([mrd -value 570425784])&0xffffffff)!=0} {error "DDR readback offset 440"}
mwr 570425788 0
if {(wide([mrd -value 570425788])&0xffffffff)!=0} {error "DDR readback offset 444"}
mwr 570425792 0
if {(wide([mrd -value 570425792])&0xffffffff)!=0} {error "DDR readback offset 448"}
mwr 570425796 0
if {(wide([mrd -value 570425796])&0xffffffff)!=0} {error "DDR readback offset 452"}
mwr 570425800 0
if {(wide([mrd -value 570425800])&0xffffffff)!=0} {error "DDR readback offset 456"}
mwr 570425804 0
if {(wide([mrd -value 570425804])&0xffffffff)!=0} {error "DDR readback offset 460"}
mwr 570425808 0
if {(wide([mrd -value 570425808])&0xffffffff)!=0} {error "DDR readback offset 464"}
mwr 570425812 0
if {(wide([mrd -value 570425812])&0xffffffff)!=0} {error "DDR readback offset 468"}
mwr 570425816 0
if {(wide([mrd -value 570425816])&0xffffffff)!=0} {error "DDR readback offset 472"}
mwr 570425820 0
if {(wide([mrd -value 570425820])&0xffffffff)!=0} {error "DDR readback offset 476"}
mwr 570425824 0
if {(wide([mrd -value 570425824])&0xffffffff)!=0} {error "DDR readback offset 480"}
mwr 570425828 0
if {(wide([mrd -value 570425828])&0xffffffff)!=0} {error "DDR readback offset 484"}
mwr 570425832 0
if {(wide([mrd -value 570425832])&0xffffffff)!=0} {error "DDR readback offset 488"}
mwr 570425836 0
if {(wide([mrd -value 570425836])&0xffffffff)!=0} {error "DDR readback offset 492"}
mwr 570425840 0
if {(wide([mrd -value 570425840])&0xffffffff)!=0} {error "DDR readback offset 496"}
mwr 570425844 0
if {(wide([mrd -value 570425844])&0xffffffff)!=0} {error "DDR readback offset 500"}
mwr 570425848 0
if {(wide([mrd -value 570425848])&0xffffffff)!=0} {error "DDR readback offset 504"}
mwr 570425852 0
if {(wide([mrd -value 570425852])&0xffffffff)!=0} {error "DDR readback offset 508"}
mwr 570425856 0
if {(wide([mrd -value 570425856])&0xffffffff)!=0} {error "DDR readback offset 512"}
mwr 570425860 0
if {(wide([mrd -value 570425860])&0xffffffff)!=0} {error "DDR readback offset 516"}
mwr 570425864 0
if {(wide([mrd -value 570425864])&0xffffffff)!=0} {error "DDR readback offset 520"}
mwr 570425868 0
if {(wide([mrd -value 570425868])&0xffffffff)!=0} {error "DDR readback offset 524"}
mwr 570425872 0
if {(wide([mrd -value 570425872])&0xffffffff)!=0} {error "DDR readback offset 528"}
mwr 570425876 0
if {(wide([mrd -value 570425876])&0xffffffff)!=0} {error "DDR readback offset 532"}
mwr 570425880 0
if {(wide([mrd -value 570425880])&0xffffffff)!=0} {error "DDR readback offset 536"}
mwr 570425884 0
if {(wide([mrd -value 570425884])&0xffffffff)!=0} {error "DDR readback offset 540"}
mwr 570425888 0
if {(wide([mrd -value 570425888])&0xffffffff)!=0} {error "DDR readback offset 544"}
mwr 570425892 0
if {(wide([mrd -value 570425892])&0xffffffff)!=0} {error "DDR readback offset 548"}
mwr 570425896 0
if {(wide([mrd -value 570425896])&0xffffffff)!=0} {error "DDR readback offset 552"}
mwr 570425900 0
if {(wide([mrd -value 570425900])&0xffffffff)!=0} {error "DDR readback offset 556"}
mwr 570425904 0
if {(wide([mrd -value 570425904])&0xffffffff)!=0} {error "DDR readback offset 560"}
mwr 570425908 0
if {(wide([mrd -value 570425908])&0xffffffff)!=0} {error "DDR readback offset 564"}
mwr 570425912 0
if {(wide([mrd -value 570425912])&0xffffffff)!=0} {error "DDR readback offset 568"}
mwr 570425916 0
if {(wide([mrd -value 570425916])&0xffffffff)!=0} {error "DDR readback offset 572"}
mwr 570425920 0
if {(wide([mrd -value 570425920])&0xffffffff)!=0} {error "DDR readback offset 576"}
mwr 570425924 0
if {(wide([mrd -value 570425924])&0xffffffff)!=0} {error "DDR readback offset 580"}
mwr 570425928 0
if {(wide([mrd -value 570425928])&0xffffffff)!=0} {error "DDR readback offset 584"}
mwr 570425932 0
if {(wide([mrd -value 570425932])&0xffffffff)!=0} {error "DDR readback offset 588"}
mwr 570425936 0
if {(wide([mrd -value 570425936])&0xffffffff)!=0} {error "DDR readback offset 592"}
mwr 570425940 0
if {(wide([mrd -value 570425940])&0xffffffff)!=0} {error "DDR readback offset 596"}
mwr 570425944 0
if {(wide([mrd -value 570425944])&0xffffffff)!=0} {error "DDR readback offset 600"}
mwr 570425948 0
if {(wide([mrd -value 570425948])&0xffffffff)!=0} {error "DDR readback offset 604"}
mwr 570425952 0
if {(wide([mrd -value 570425952])&0xffffffff)!=0} {error "DDR readback offset 608"}
mwr 570425956 0
if {(wide([mrd -value 570425956])&0xffffffff)!=0} {error "DDR readback offset 612"}
mwr 570425960 0
if {(wide([mrd -value 570425960])&0xffffffff)!=0} {error "DDR readback offset 616"}
mwr 570425964 0
if {(wide([mrd -value 570425964])&0xffffffff)!=0} {error "DDR readback offset 620"}
mwr 570425968 0
if {(wide([mrd -value 570425968])&0xffffffff)!=0} {error "DDR readback offset 624"}
mwr 570425972 0
if {(wide([mrd -value 570425972])&0xffffffff)!=0} {error "DDR readback offset 628"}
mwr 570425976 0
if {(wide([mrd -value 570425976])&0xffffffff)!=0} {error "DDR readback offset 632"}
mwr 570425980 0
if {(wide([mrd -value 570425980])&0xffffffff)!=0} {error "DDR readback offset 636"}
mwr 570425984 0
if {(wide([mrd -value 570425984])&0xffffffff)!=0} {error "DDR readback offset 640"}
mwr 570425988 0
if {(wide([mrd -value 570425988])&0xffffffff)!=0} {error "DDR readback offset 644"}
mwr 570425992 0
if {(wide([mrd -value 570425992])&0xffffffff)!=0} {error "DDR readback offset 648"}
mwr 570425996 0
if {(wide([mrd -value 570425996])&0xffffffff)!=0} {error "DDR readback offset 652"}
mwr 570426000 0
if {(wide([mrd -value 570426000])&0xffffffff)!=0} {error "DDR readback offset 656"}
mwr 570426004 0
if {(wide([mrd -value 570426004])&0xffffffff)!=0} {error "DDR readback offset 660"}
mwr 570426008 0
if {(wide([mrd -value 570426008])&0xffffffff)!=0} {error "DDR readback offset 664"}
mwr 570426012 0
if {(wide([mrd -value 570426012])&0xffffffff)!=0} {error "DDR readback offset 668"}
mwr 570426016 0
if {(wide([mrd -value 570426016])&0xffffffff)!=0} {error "DDR readback offset 672"}
mwr 570426020 0
if {(wide([mrd -value 570426020])&0xffffffff)!=0} {error "DDR readback offset 676"}
mwr 570426024 0
if {(wide([mrd -value 570426024])&0xffffffff)!=0} {error "DDR readback offset 680"}
mwr 570426028 0
if {(wide([mrd -value 570426028])&0xffffffff)!=0} {error "DDR readback offset 684"}
mwr 570426032 0
if {(wide([mrd -value 570426032])&0xffffffff)!=0} {error "DDR readback offset 688"}
mwr 570426036 0
if {(wide([mrd -value 570426036])&0xffffffff)!=0} {error "DDR readback offset 692"}
mwr 570426040 0
if {(wide([mrd -value 570426040])&0xffffffff)!=0} {error "DDR readback offset 696"}
mwr 570426044 0
if {(wide([mrd -value 570426044])&0xffffffff)!=0} {error "DDR readback offset 700"}
mwr 570426048 0
if {(wide([mrd -value 570426048])&0xffffffff)!=0} {error "DDR readback offset 704"}
mwr 570426052 0
if {(wide([mrd -value 570426052])&0xffffffff)!=0} {error "DDR readback offset 708"}
mwr 570426056 0
if {(wide([mrd -value 570426056])&0xffffffff)!=0} {error "DDR readback offset 712"}
mwr 570426060 0
if {(wide([mrd -value 570426060])&0xffffffff)!=0} {error "DDR readback offset 716"}
mwr 570426064 0
if {(wide([mrd -value 570426064])&0xffffffff)!=0} {error "DDR readback offset 720"}
mwr 570426068 0
if {(wide([mrd -value 570426068])&0xffffffff)!=0} {error "DDR readback offset 724"}
mwr 570426072 0
if {(wide([mrd -value 570426072])&0xffffffff)!=0} {error "DDR readback offset 728"}
mwr 570426076 0
if {(wide([mrd -value 570426076])&0xffffffff)!=0} {error "DDR readback offset 732"}
mwr 570426080 0
if {(wide([mrd -value 570426080])&0xffffffff)!=0} {error "DDR readback offset 736"}
mwr 570426084 0
if {(wide([mrd -value 570426084])&0xffffffff)!=0} {error "DDR readback offset 740"}
mwr 570426088 0
if {(wide([mrd -value 570426088])&0xffffffff)!=0} {error "DDR readback offset 744"}
mwr 570426092 0
if {(wide([mrd -value 570426092])&0xffffffff)!=0} {error "DDR readback offset 748"}
mwr 570426096 0
if {(wide([mrd -value 570426096])&0xffffffff)!=0} {error "DDR readback offset 752"}
mwr 570426100 0
if {(wide([mrd -value 570426100])&0xffffffff)!=0} {error "DDR readback offset 756"}
mwr 570426104 0
if {(wide([mrd -value 570426104])&0xffffffff)!=0} {error "DDR readback offset 760"}
mwr 570426108 0
if {(wide([mrd -value 570426108])&0xffffffff)!=0} {error "DDR readback offset 764"}
mwr 570426112 0
if {(wide([mrd -value 570426112])&0xffffffff)!=0} {error "DDR readback offset 768"}
mwr 570426116 0
if {(wide([mrd -value 570426116])&0xffffffff)!=0} {error "DDR readback offset 772"}
mwr 570426120 0
if {(wide([mrd -value 570426120])&0xffffffff)!=0} {error "DDR readback offset 776"}
mwr 570426124 0
if {(wide([mrd -value 570426124])&0xffffffff)!=0} {error "DDR readback offset 780"}
mwr 570426128 0
if {(wide([mrd -value 570426128])&0xffffffff)!=0} {error "DDR readback offset 784"}
mwr 570426132 0
if {(wide([mrd -value 570426132])&0xffffffff)!=0} {error "DDR readback offset 788"}
mwr 570426136 0
if {(wide([mrd -value 570426136])&0xffffffff)!=0} {error "DDR readback offset 792"}
mwr 570426140 0
if {(wide([mrd -value 570426140])&0xffffffff)!=0} {error "DDR readback offset 796"}
mwr 570426144 0
if {(wide([mrd -value 570426144])&0xffffffff)!=0} {error "DDR readback offset 800"}
mwr 570426148 0
if {(wide([mrd -value 570426148])&0xffffffff)!=0} {error "DDR readback offset 804"}
mwr 570426152 0
if {(wide([mrd -value 570426152])&0xffffffff)!=0} {error "DDR readback offset 808"}
mwr 570426156 0
if {(wide([mrd -value 570426156])&0xffffffff)!=0} {error "DDR readback offset 812"}
mwr 570426160 0
if {(wide([mrd -value 570426160])&0xffffffff)!=0} {error "DDR readback offset 816"}
mwr 570426164 0
if {(wide([mrd -value 570426164])&0xffffffff)!=0} {error "DDR readback offset 820"}
mwr 570426168 0
if {(wide([mrd -value 570426168])&0xffffffff)!=0} {error "DDR readback offset 824"}
mwr 570426172 0
if {(wide([mrd -value 570426172])&0xffffffff)!=0} {error "DDR readback offset 828"}
mwr 570426176 0
if {(wide([mrd -value 570426176])&0xffffffff)!=0} {error "DDR readback offset 832"}
mwr 570426180 0
if {(wide([mrd -value 570426180])&0xffffffff)!=0} {error "DDR readback offset 836"}
mwr 570426184 0
if {(wide([mrd -value 570426184])&0xffffffff)!=0} {error "DDR readback offset 840"}
mwr 570426188 0
if {(wide([mrd -value 570426188])&0xffffffff)!=0} {error "DDR readback offset 844"}
mwr 570426192 0
if {(wide([mrd -value 570426192])&0xffffffff)!=0} {error "DDR readback offset 848"}
mwr 570426196 0
if {(wide([mrd -value 570426196])&0xffffffff)!=0} {error "DDR readback offset 852"}
mwr 570426200 0
if {(wide([mrd -value 570426200])&0xffffffff)!=0} {error "DDR readback offset 856"}
mwr 570426204 0
if {(wide([mrd -value 570426204])&0xffffffff)!=0} {error "DDR readback offset 860"}
mwr 570426208 0
if {(wide([mrd -value 570426208])&0xffffffff)!=0} {error "DDR readback offset 864"}
mwr 570426212 0
if {(wide([mrd -value 570426212])&0xffffffff)!=0} {error "DDR readback offset 868"}
mwr 570426216 0
if {(wide([mrd -value 570426216])&0xffffffff)!=0} {error "DDR readback offset 872"}
mwr 570426220 0
if {(wide([mrd -value 570426220])&0xffffffff)!=0} {error "DDR readback offset 876"}
mwr 570426224 0
if {(wide([mrd -value 570426224])&0xffffffff)!=0} {error "DDR readback offset 880"}
mwr 570426228 0
if {(wide([mrd -value 570426228])&0xffffffff)!=0} {error "DDR readback offset 884"}
mwr 570426232 0
if {(wide([mrd -value 570426232])&0xffffffff)!=0} {error "DDR readback offset 888"}
mwr 570426236 0
if {(wide([mrd -value 570426236])&0xffffffff)!=0} {error "DDR readback offset 892"}
mwr 570426240 0
if {(wide([mrd -value 570426240])&0xffffffff)!=0} {error "DDR readback offset 896"}
mwr 570426244 0
if {(wide([mrd -value 570426244])&0xffffffff)!=0} {error "DDR readback offset 900"}
mwr 570426248 0
if {(wide([mrd -value 570426248])&0xffffffff)!=0} {error "DDR readback offset 904"}
mwr 570426252 0
if {(wide([mrd -value 570426252])&0xffffffff)!=0} {error "DDR readback offset 908"}
mwr 570426256 0
if {(wide([mrd -value 570426256])&0xffffffff)!=0} {error "DDR readback offset 912"}
mwr 570426260 0
if {(wide([mrd -value 570426260])&0xffffffff)!=0} {error "DDR readback offset 916"}
mwr 570426264 0
if {(wide([mrd -value 570426264])&0xffffffff)!=0} {error "DDR readback offset 920"}
mwr 570426268 0
if {(wide([mrd -value 570426268])&0xffffffff)!=0} {error "DDR readback offset 924"}
mwr 570426272 0
if {(wide([mrd -value 570426272])&0xffffffff)!=0} {error "DDR readback offset 928"}
mwr 570426276 0
if {(wide([mrd -value 570426276])&0xffffffff)!=0} {error "DDR readback offset 932"}
mwr 570426280 0
if {(wide([mrd -value 570426280])&0xffffffff)!=0} {error "DDR readback offset 936"}
mwr 570426284 0
if {(wide([mrd -value 570426284])&0xffffffff)!=0} {error "DDR readback offset 940"}
mwr 570426288 0
if {(wide([mrd -value 570426288])&0xffffffff)!=0} {error "DDR readback offset 944"}
mwr 570426292 0
if {(wide([mrd -value 570426292])&0xffffffff)!=0} {error "DDR readback offset 948"}
mwr 570426296 0
if {(wide([mrd -value 570426296])&0xffffffff)!=0} {error "DDR readback offset 952"}
mwr 570426300 0
if {(wide([mrd -value 570426300])&0xffffffff)!=0} {error "DDR readback offset 956"}
mwr 570426304 0
if {(wide([mrd -value 570426304])&0xffffffff)!=0} {error "DDR readback offset 960"}
mwr 570426308 0
if {(wide([mrd -value 570426308])&0xffffffff)!=0} {error "DDR readback offset 964"}
mwr 570426312 0
if {(wide([mrd -value 570426312])&0xffffffff)!=0} {error "DDR readback offset 968"}
mwr 570426316 0
if {(wide([mrd -value 570426316])&0xffffffff)!=0} {error "DDR readback offset 972"}
mwr 570426320 0
if {(wide([mrd -value 570426320])&0xffffffff)!=0} {error "DDR readback offset 976"}
mwr 570426324 0
if {(wide([mrd -value 570426324])&0xffffffff)!=0} {error "DDR readback offset 980"}
mwr 570426328 0
if {(wide([mrd -value 570426328])&0xffffffff)!=0} {error "DDR readback offset 984"}
mwr 570426332 0
if {(wide([mrd -value 570426332])&0xffffffff)!=0} {error "DDR readback offset 988"}
mwr 570426336 0
if {(wide([mrd -value 570426336])&0xffffffff)!=0} {error "DDR readback offset 992"}
mwr 570426340 0
if {(wide([mrd -value 570426340])&0xffffffff)!=0} {error "DDR readback offset 996"}
mwr 570426344 0
if {(wide([mrd -value 570426344])&0xffffffff)!=0} {error "DDR readback offset 1000"}
mwr 570426348 0
if {(wide([mrd -value 570426348])&0xffffffff)!=0} {error "DDR readback offset 1004"}
mwr 570426352 0
if {(wide([mrd -value 570426352])&0xffffffff)!=0} {error "DDR readback offset 1008"}
mwr 570426356 0
if {(wide([mrd -value 570426356])&0xffffffff)!=0} {error "DDR readback offset 1012"}
mwr 570426360 0
if {(wide([mrd -value 570426360])&0xffffffff)!=0} {error "DDR readback offset 1016"}
mwr 570426364 0
if {(wide([mrd -value 570426364])&0xffffffff)!=0} {error "DDR readback offset 1020"}
mwr 570426368 0
if {(wide([mrd -value 570426368])&0xffffffff)!=0} {error "DDR readback offset 1024"}
mwr 570426372 0
if {(wide([mrd -value 570426372])&0xffffffff)!=0} {error "DDR readback offset 1028"}
mwr 570426376 0
if {(wide([mrd -value 570426376])&0xffffffff)!=0} {error "DDR readback offset 1032"}
mwr 570426380 0
if {(wide([mrd -value 570426380])&0xffffffff)!=0} {error "DDR readback offset 1036"}
mwr 570426384 0
if {(wide([mrd -value 570426384])&0xffffffff)!=0} {error "DDR readback offset 1040"}
mwr 570426388 0
if {(wide([mrd -value 570426388])&0xffffffff)!=0} {error "DDR readback offset 1044"}
mwr 570426392 0
if {(wide([mrd -value 570426392])&0xffffffff)!=0} {error "DDR readback offset 1048"}
mwr 570426396 0
if {(wide([mrd -value 570426396])&0xffffffff)!=0} {error "DDR readback offset 1052"}
mwr 570426400 0
if {(wide([mrd -value 570426400])&0xffffffff)!=0} {error "DDR readback offset 1056"}
mwr 570426404 0
if {(wide([mrd -value 570426404])&0xffffffff)!=0} {error "DDR readback offset 1060"}
mwr 570426408 0
if {(wide([mrd -value 570426408])&0xffffffff)!=0} {error "DDR readback offset 1064"}
mwr 570426412 0
if {(wide([mrd -value 570426412])&0xffffffff)!=0} {error "DDR readback offset 1068"}
mwr 570426416 0
if {(wide([mrd -value 570426416])&0xffffffff)!=0} {error "DDR readback offset 1072"}
mwr 570426420 0
if {(wide([mrd -value 570426420])&0xffffffff)!=0} {error "DDR readback offset 1076"}
mwr 570426424 0
if {(wide([mrd -value 570426424])&0xffffffff)!=0} {error "DDR readback offset 1080"}
mwr 570426428 0
if {(wide([mrd -value 570426428])&0xffffffff)!=0} {error "DDR readback offset 1084"}
mwr 570426432 0
if {(wide([mrd -value 570426432])&0xffffffff)!=0} {error "DDR readback offset 1088"}
mwr 570426436 0
if {(wide([mrd -value 570426436])&0xffffffff)!=0} {error "DDR readback offset 1092"}
mwr 570426440 0
if {(wide([mrd -value 570426440])&0xffffffff)!=0} {error "DDR readback offset 1096"}
mwr 570426444 0
if {(wide([mrd -value 570426444])&0xffffffff)!=0} {error "DDR readback offset 1100"}
mwr 570426448 0
if {(wide([mrd -value 570426448])&0xffffffff)!=0} {error "DDR readback offset 1104"}
mwr 570426452 0
if {(wide([mrd -value 570426452])&0xffffffff)!=0} {error "DDR readback offset 1108"}
mwr 570426456 0
if {(wide([mrd -value 570426456])&0xffffffff)!=0} {error "DDR readback offset 1112"}
mwr 570426460 0
if {(wide([mrd -value 570426460])&0xffffffff)!=0} {error "DDR readback offset 1116"}
mwr 570426464 0
if {(wide([mrd -value 570426464])&0xffffffff)!=0} {error "DDR readback offset 1120"}
mwr 570426468 0
if {(wide([mrd -value 570426468])&0xffffffff)!=0} {error "DDR readback offset 1124"}
mwr 570426472 0
if {(wide([mrd -value 570426472])&0xffffffff)!=0} {error "DDR readback offset 1128"}
mwr 570426476 0
if {(wide([mrd -value 570426476])&0xffffffff)!=0} {error "DDR readback offset 1132"}
mwr 570426480 0
if {(wide([mrd -value 570426480])&0xffffffff)!=0} {error "DDR readback offset 1136"}
mwr 570426484 0
if {(wide([mrd -value 570426484])&0xffffffff)!=0} {error "DDR readback offset 1140"}
mwr 570426488 0
if {(wide([mrd -value 570426488])&0xffffffff)!=0} {error "DDR readback offset 1144"}
mwr 570426492 0
if {(wide([mrd -value 570426492])&0xffffffff)!=0} {error "DDR readback offset 1148"}
mwr 570426496 0
if {(wide([mrd -value 570426496])&0xffffffff)!=0} {error "DDR readback offset 1152"}
mwr 570426500 0
if {(wide([mrd -value 570426500])&0xffffffff)!=0} {error "DDR readback offset 1156"}
mwr 570426504 0
if {(wide([mrd -value 570426504])&0xffffffff)!=0} {error "DDR readback offset 1160"}
mwr 570426508 0
if {(wide([mrd -value 570426508])&0xffffffff)!=0} {error "DDR readback offset 1164"}
mwr 570426512 0
if {(wide([mrd -value 570426512])&0xffffffff)!=0} {error "DDR readback offset 1168"}
mwr 570426516 0
if {(wide([mrd -value 570426516])&0xffffffff)!=0} {error "DDR readback offset 1172"}
mwr 570426520 0
if {(wide([mrd -value 570426520])&0xffffffff)!=0} {error "DDR readback offset 1176"}
mwr 570426524 0
if {(wide([mrd -value 570426524])&0xffffffff)!=0} {error "DDR readback offset 1180"}
mwr 570426528 0
if {(wide([mrd -value 570426528])&0xffffffff)!=0} {error "DDR readback offset 1184"}
mwr 570426532 0
if {(wide([mrd -value 570426532])&0xffffffff)!=0} {error "DDR readback offset 1188"}
mwr 570426536 0
if {(wide([mrd -value 570426536])&0xffffffff)!=0} {error "DDR readback offset 1192"}
mwr 570426540 0
if {(wide([mrd -value 570426540])&0xffffffff)!=0} {error "DDR readback offset 1196"}
mwr 570426544 0
if {(wide([mrd -value 570426544])&0xffffffff)!=0} {error "DDR readback offset 1200"}
mwr 570426548 0
if {(wide([mrd -value 570426548])&0xffffffff)!=0} {error "DDR readback offset 1204"}
mwr 570426552 0
if {(wide([mrd -value 570426552])&0xffffffff)!=0} {error "DDR readback offset 1208"}
mwr 570426556 0
if {(wide([mrd -value 570426556])&0xffffffff)!=0} {error "DDR readback offset 1212"}
mwr 570426560 0
if {(wide([mrd -value 570426560])&0xffffffff)!=0} {error "DDR readback offset 1216"}
mwr 570426564 0
if {(wide([mrd -value 570426564])&0xffffffff)!=0} {error "DDR readback offset 1220"}
mwr 570426568 0
if {(wide([mrd -value 570426568])&0xffffffff)!=0} {error "DDR readback offset 1224"}
mwr 570426572 0
if {(wide([mrd -value 570426572])&0xffffffff)!=0} {error "DDR readback offset 1228"}
mwr 570426576 0
if {(wide([mrd -value 570426576])&0xffffffff)!=0} {error "DDR readback offset 1232"}
mwr 570426580 0
if {(wide([mrd -value 570426580])&0xffffffff)!=0} {error "DDR readback offset 1236"}
mwr 570426584 0
if {(wide([mrd -value 570426584])&0xffffffff)!=0} {error "DDR readback offset 1240"}
mwr 570426588 0
if {(wide([mrd -value 570426588])&0xffffffff)!=0} {error "DDR readback offset 1244"}
mwr 570426592 0
if {(wide([mrd -value 570426592])&0xffffffff)!=0} {error "DDR readback offset 1248"}
mwr 570426596 0
if {(wide([mrd -value 570426596])&0xffffffff)!=0} {error "DDR readback offset 1252"}
mwr 570426600 0
if {(wide([mrd -value 570426600])&0xffffffff)!=0} {error "DDR readback offset 1256"}
mwr 570426604 0
if {(wide([mrd -value 570426604])&0xffffffff)!=0} {error "DDR readback offset 1260"}
mwr 570426608 0
if {(wide([mrd -value 570426608])&0xffffffff)!=0} {error "DDR readback offset 1264"}
mwr 570426612 0
if {(wide([mrd -value 570426612])&0xffffffff)!=0} {error "DDR readback offset 1268"}
mwr 570426616 0
if {(wide([mrd -value 570426616])&0xffffffff)!=0} {error "DDR readback offset 1272"}
mwr 570426620 0
if {(wide([mrd -value 570426620])&0xffffffff)!=0} {error "DDR readback offset 1276"}
mwr 570426624 0
if {(wide([mrd -value 570426624])&0xffffffff)!=0} {error "DDR readback offset 1280"}
mwr 570426628 0
if {(wide([mrd -value 570426628])&0xffffffff)!=0} {error "DDR readback offset 1284"}
mwr 570426632 0
if {(wide([mrd -value 570426632])&0xffffffff)!=0} {error "DDR readback offset 1288"}
mwr 570426636 0
if {(wide([mrd -value 570426636])&0xffffffff)!=0} {error "DDR readback offset 1292"}
mwr 570426640 0
if {(wide([mrd -value 570426640])&0xffffffff)!=0} {error "DDR readback offset 1296"}
mwr 570426644 0
if {(wide([mrd -value 570426644])&0xffffffff)!=0} {error "DDR readback offset 1300"}
mwr 570426648 0
if {(wide([mrd -value 570426648])&0xffffffff)!=0} {error "DDR readback offset 1304"}
mwr 570426652 0
if {(wide([mrd -value 570426652])&0xffffffff)!=0} {error "DDR readback offset 1308"}
mwr 570426656 0
if {(wide([mrd -value 570426656])&0xffffffff)!=0} {error "DDR readback offset 1312"}
mwr 570426660 0
if {(wide([mrd -value 570426660])&0xffffffff)!=0} {error "DDR readback offset 1316"}
mwr 570426664 0
if {(wide([mrd -value 570426664])&0xffffffff)!=0} {error "DDR readback offset 1320"}
mwr 570426668 0
if {(wide([mrd -value 570426668])&0xffffffff)!=0} {error "DDR readback offset 1324"}
mwr 570426672 0
if {(wide([mrd -value 570426672])&0xffffffff)!=0} {error "DDR readback offset 1328"}
mwr 570426676 0
if {(wide([mrd -value 570426676])&0xffffffff)!=0} {error "DDR readback offset 1332"}
mwr 570426680 0
if {(wide([mrd -value 570426680])&0xffffffff)!=0} {error "DDR readback offset 1336"}
mwr 570426684 0
if {(wide([mrd -value 570426684])&0xffffffff)!=0} {error "DDR readback offset 1340"}
mwr 570426688 0
if {(wide([mrd -value 570426688])&0xffffffff)!=0} {error "DDR readback offset 1344"}
mwr 570426692 0
if {(wide([mrd -value 570426692])&0xffffffff)!=0} {error "DDR readback offset 1348"}
mwr 570426696 0
if {(wide([mrd -value 570426696])&0xffffffff)!=0} {error "DDR readback offset 1352"}
mwr 570426700 0
if {(wide([mrd -value 570426700])&0xffffffff)!=0} {error "DDR readback offset 1356"}
mwr 570426704 0
if {(wide([mrd -value 570426704])&0xffffffff)!=0} {error "DDR readback offset 1360"}
mwr 570426708 0
if {(wide([mrd -value 570426708])&0xffffffff)!=0} {error "DDR readback offset 1364"}
mwr 570426712 0
if {(wide([mrd -value 570426712])&0xffffffff)!=0} {error "DDR readback offset 1368"}
mwr 570426716 0
if {(wide([mrd -value 570426716])&0xffffffff)!=0} {error "DDR readback offset 1372"}
mwr 570426720 0
if {(wide([mrd -value 570426720])&0xffffffff)!=0} {error "DDR readback offset 1376"}
mwr 570426724 0
if {(wide([mrd -value 570426724])&0xffffffff)!=0} {error "DDR readback offset 1380"}
mwr 570426728 0
if {(wide([mrd -value 570426728])&0xffffffff)!=0} {error "DDR readback offset 1384"}
mwr 570426732 0
if {(wide([mrd -value 570426732])&0xffffffff)!=0} {error "DDR readback offset 1388"}
mwr 570426736 0
if {(wide([mrd -value 570426736])&0xffffffff)!=0} {error "DDR readback offset 1392"}
mwr 570426740 0
if {(wide([mrd -value 570426740])&0xffffffff)!=0} {error "DDR readback offset 1396"}
mwr 570426744 0
if {(wide([mrd -value 570426744])&0xffffffff)!=0} {error "DDR readback offset 1400"}
mwr 570426748 0
if {(wide([mrd -value 570426748])&0xffffffff)!=0} {error "DDR readback offset 1404"}
mwr 570426752 0
if {(wide([mrd -value 570426752])&0xffffffff)!=0} {error "DDR readback offset 1408"}
mwr 570426756 0
if {(wide([mrd -value 570426756])&0xffffffff)!=0} {error "DDR readback offset 1412"}
mwr 570426760 0
if {(wide([mrd -value 570426760])&0xffffffff)!=0} {error "DDR readback offset 1416"}
mwr 570426764 0
if {(wide([mrd -value 570426764])&0xffffffff)!=0} {error "DDR readback offset 1420"}
mwr 570426768 0
if {(wide([mrd -value 570426768])&0xffffffff)!=0} {error "DDR readback offset 1424"}
mwr 570426772 0
if {(wide([mrd -value 570426772])&0xffffffff)!=0} {error "DDR readback offset 1428"}
mwr 570426776 0
if {(wide([mrd -value 570426776])&0xffffffff)!=0} {error "DDR readback offset 1432"}
mwr 570426780 0
if {(wide([mrd -value 570426780])&0xffffffff)!=0} {error "DDR readback offset 1436"}
mwr 570426784 0
if {(wide([mrd -value 570426784])&0xffffffff)!=0} {error "DDR readback offset 1440"}
mwr 570426788 0
if {(wide([mrd -value 570426788])&0xffffffff)!=0} {error "DDR readback offset 1444"}
mwr 570426792 0
if {(wide([mrd -value 570426792])&0xffffffff)!=0} {error "DDR readback offset 1448"}
mwr 570426796 0
if {(wide([mrd -value 570426796])&0xffffffff)!=0} {error "DDR readback offset 1452"}
mwr 570426800 0
if {(wide([mrd -value 570426800])&0xffffffff)!=0} {error "DDR readback offset 1456"}
mwr 570426804 0
if {(wide([mrd -value 570426804])&0xffffffff)!=0} {error "DDR readback offset 1460"}
mwr 570426808 0
if {(wide([mrd -value 570426808])&0xffffffff)!=0} {error "DDR readback offset 1464"}
mwr 570426812 0
if {(wide([mrd -value 570426812])&0xffffffff)!=0} {error "DDR readback offset 1468"}
mwr 570426816 0
if {(wide([mrd -value 570426816])&0xffffffff)!=0} {error "DDR readback offset 1472"}
mwr 570426820 0
if {(wide([mrd -value 570426820])&0xffffffff)!=0} {error "DDR readback offset 1476"}
mwr 570426824 0
if {(wide([mrd -value 570426824])&0xffffffff)!=0} {error "DDR readback offset 1480"}
mwr 570426828 0
if {(wide([mrd -value 570426828])&0xffffffff)!=0} {error "DDR readback offset 1484"}
mwr 570426832 0
if {(wide([mrd -value 570426832])&0xffffffff)!=0} {error "DDR readback offset 1488"}
mwr 570426836 0
if {(wide([mrd -value 570426836])&0xffffffff)!=0} {error "DDR readback offset 1492"}
mwr 570426840 0
if {(wide([mrd -value 570426840])&0xffffffff)!=0} {error "DDR readback offset 1496"}
mwr 570426844 0
if {(wide([mrd -value 570426844])&0xffffffff)!=0} {error "DDR readback offset 1500"}
mwr 570426848 0
if {(wide([mrd -value 570426848])&0xffffffff)!=0} {error "DDR readback offset 1504"}
mwr 570426852 0
if {(wide([mrd -value 570426852])&0xffffffff)!=0} {error "DDR readback offset 1508"}
mwr 570426856 0
if {(wide([mrd -value 570426856])&0xffffffff)!=0} {error "DDR readback offset 1512"}
mwr 570426860 0
if {(wide([mrd -value 570426860])&0xffffffff)!=0} {error "DDR readback offset 1516"}
mwr 570426864 0
if {(wide([mrd -value 570426864])&0xffffffff)!=0} {error "DDR readback offset 1520"}
mwr 570426868 0
if {(wide([mrd -value 570426868])&0xffffffff)!=0} {error "DDR readback offset 1524"}
mwr 570426872 0
if {(wide([mrd -value 570426872])&0xffffffff)!=0} {error "DDR readback offset 1528"}
mwr 570426876 0
if {(wide([mrd -value 570426876])&0xffffffff)!=0} {error "DDR readback offset 1532"}
mwr 570426880 0
if {(wide([mrd -value 570426880])&0xffffffff)!=0} {error "DDR readback offset 1536"}
mwr 570426884 0
if {(wide([mrd -value 570426884])&0xffffffff)!=0} {error "DDR readback offset 1540"}
mwr 570426888 0
if {(wide([mrd -value 570426888])&0xffffffff)!=0} {error "DDR readback offset 1544"}
mwr 570426892 0
if {(wide([mrd -value 570426892])&0xffffffff)!=0} {error "DDR readback offset 1548"}
mwr 570426896 0
if {(wide([mrd -value 570426896])&0xffffffff)!=0} {error "DDR readback offset 1552"}
mwr 570426900 0
if {(wide([mrd -value 570426900])&0xffffffff)!=0} {error "DDR readback offset 1556"}
mwr 570426904 0
if {(wide([mrd -value 570426904])&0xffffffff)!=0} {error "DDR readback offset 1560"}
mwr 570426908 0
if {(wide([mrd -value 570426908])&0xffffffff)!=0} {error "DDR readback offset 1564"}
mwr 570426912 0
if {(wide([mrd -value 570426912])&0xffffffff)!=0} {error "DDR readback offset 1568"}
mwr 570426916 0
if {(wide([mrd -value 570426916])&0xffffffff)!=0} {error "DDR readback offset 1572"}
mwr 570426920 0
if {(wide([mrd -value 570426920])&0xffffffff)!=0} {error "DDR readback offset 1576"}
mwr 570426924 0
if {(wide([mrd -value 570426924])&0xffffffff)!=0} {error "DDR readback offset 1580"}
mwr 570426928 0
if {(wide([mrd -value 570426928])&0xffffffff)!=0} {error "DDR readback offset 1584"}
mwr 570426932 0
if {(wide([mrd -value 570426932])&0xffffffff)!=0} {error "DDR readback offset 1588"}
mwr 570426936 0
if {(wide([mrd -value 570426936])&0xffffffff)!=0} {error "DDR readback offset 1592"}
mwr 570426940 0
if {(wide([mrd -value 570426940])&0xffffffff)!=0} {error "DDR readback offset 1596"}
mwr 570426944 0
if {(wide([mrd -value 570426944])&0xffffffff)!=0} {error "DDR readback offset 1600"}
mwr 570426948 0
if {(wide([mrd -value 570426948])&0xffffffff)!=0} {error "DDR readback offset 1604"}
mwr 570426952 0
if {(wide([mrd -value 570426952])&0xffffffff)!=0} {error "DDR readback offset 1608"}
mwr 570426956 0
if {(wide([mrd -value 570426956])&0xffffffff)!=0} {error "DDR readback offset 1612"}
mwr 570426960 0
if {(wide([mrd -value 570426960])&0xffffffff)!=0} {error "DDR readback offset 1616"}
mwr 570426964 0
if {(wide([mrd -value 570426964])&0xffffffff)!=0} {error "DDR readback offset 1620"}
mwr 570426968 0
if {(wide([mrd -value 570426968])&0xffffffff)!=0} {error "DDR readback offset 1624"}
mwr 570426972 0
if {(wide([mrd -value 570426972])&0xffffffff)!=0} {error "DDR readback offset 1628"}
mwr 570426976 0
if {(wide([mrd -value 570426976])&0xffffffff)!=0} {error "DDR readback offset 1632"}
mwr 570426980 0
if {(wide([mrd -value 570426980])&0xffffffff)!=0} {error "DDR readback offset 1636"}
mwr 570426984 0
if {(wide([mrd -value 570426984])&0xffffffff)!=0} {error "DDR readback offset 1640"}
mwr 570426988 0
if {(wide([mrd -value 570426988])&0xffffffff)!=0} {error "DDR readback offset 1644"}
mwr 570426992 0
if {(wide([mrd -value 570426992])&0xffffffff)!=0} {error "DDR readback offset 1648"}
mwr 570426996 0
if {(wide([mrd -value 570426996])&0xffffffff)!=0} {error "DDR readback offset 1652"}
mwr 570427000 0
if {(wide([mrd -value 570427000])&0xffffffff)!=0} {error "DDR readback offset 1656"}
mwr 570427004 0
if {(wide([mrd -value 570427004])&0xffffffff)!=0} {error "DDR readback offset 1660"}
mwr 570427008 0
if {(wide([mrd -value 570427008])&0xffffffff)!=0} {error "DDR readback offset 1664"}
mwr 570427012 0
if {(wide([mrd -value 570427012])&0xffffffff)!=0} {error "DDR readback offset 1668"}
mwr 570427016 0
if {(wide([mrd -value 570427016])&0xffffffff)!=0} {error "DDR readback offset 1672"}
mwr 570427020 0
if {(wide([mrd -value 570427020])&0xffffffff)!=0} {error "DDR readback offset 1676"}
mwr 570427024 0
if {(wide([mrd -value 570427024])&0xffffffff)!=0} {error "DDR readback offset 1680"}
mwr 570427028 0
if {(wide([mrd -value 570427028])&0xffffffff)!=0} {error "DDR readback offset 1684"}
mwr 570427032 0
if {(wide([mrd -value 570427032])&0xffffffff)!=0} {error "DDR readback offset 1688"}
mwr 570427036 0
if {(wide([mrd -value 570427036])&0xffffffff)!=0} {error "DDR readback offset 1692"}
mwr 570427040 0
if {(wide([mrd -value 570427040])&0xffffffff)!=0} {error "DDR readback offset 1696"}
mwr 570427044 0
if {(wide([mrd -value 570427044])&0xffffffff)!=0} {error "DDR readback offset 1700"}
mwr 570427048 0
if {(wide([mrd -value 570427048])&0xffffffff)!=0} {error "DDR readback offset 1704"}
mwr 570427052 0
if {(wide([mrd -value 570427052])&0xffffffff)!=0} {error "DDR readback offset 1708"}
mwr 570427056 0
if {(wide([mrd -value 570427056])&0xffffffff)!=0} {error "DDR readback offset 1712"}
mwr 570427060 0
if {(wide([mrd -value 570427060])&0xffffffff)!=0} {error "DDR readback offset 1716"}
mwr 570427064 0
if {(wide([mrd -value 570427064])&0xffffffff)!=0} {error "DDR readback offset 1720"}
mwr 570427068 0
if {(wide([mrd -value 570427068])&0xffffffff)!=0} {error "DDR readback offset 1724"}
mwr 570427072 0
if {(wide([mrd -value 570427072])&0xffffffff)!=0} {error "DDR readback offset 1728"}
mwr 570427076 0
if {(wide([mrd -value 570427076])&0xffffffff)!=0} {error "DDR readback offset 1732"}
mwr 570427080 0
if {(wide([mrd -value 570427080])&0xffffffff)!=0} {error "DDR readback offset 1736"}
mwr 570427084 0
if {(wide([mrd -value 570427084])&0xffffffff)!=0} {error "DDR readback offset 1740"}
mwr 570427088 0
if {(wide([mrd -value 570427088])&0xffffffff)!=0} {error "DDR readback offset 1744"}
mwr 570427092 0
if {(wide([mrd -value 570427092])&0xffffffff)!=0} {error "DDR readback offset 1748"}
mwr 570427096 0
if {(wide([mrd -value 570427096])&0xffffffff)!=0} {error "DDR readback offset 1752"}
mwr 570427100 0
if {(wide([mrd -value 570427100])&0xffffffff)!=0} {error "DDR readback offset 1756"}
mwr 570427104 0
if {(wide([mrd -value 570427104])&0xffffffff)!=0} {error "DDR readback offset 1760"}
mwr 570427108 0
if {(wide([mrd -value 570427108])&0xffffffff)!=0} {error "DDR readback offset 1764"}
mwr 570427112 0
if {(wide([mrd -value 570427112])&0xffffffff)!=0} {error "DDR readback offset 1768"}
mwr 570427116 0
if {(wide([mrd -value 570427116])&0xffffffff)!=0} {error "DDR readback offset 1772"}
mwr 570427120 0
if {(wide([mrd -value 570427120])&0xffffffff)!=0} {error "DDR readback offset 1776"}
mwr 570427124 0
if {(wide([mrd -value 570427124])&0xffffffff)!=0} {error "DDR readback offset 1780"}
mwr 570427128 0
if {(wide([mrd -value 570427128])&0xffffffff)!=0} {error "DDR readback offset 1784"}
mwr 570427132 0
if {(wide([mrd -value 570427132])&0xffffffff)!=0} {error "DDR readback offset 1788"}
mwr 570427136 0
if {(wide([mrd -value 570427136])&0xffffffff)!=0} {error "DDR readback offset 1792"}
mwr 570427140 0
if {(wide([mrd -value 570427140])&0xffffffff)!=0} {error "DDR readback offset 1796"}
mwr 570427144 0
if {(wide([mrd -value 570427144])&0xffffffff)!=0} {error "DDR readback offset 1800"}
mwr 570427148 0
if {(wide([mrd -value 570427148])&0xffffffff)!=0} {error "DDR readback offset 1804"}
mwr 570427152 0
if {(wide([mrd -value 570427152])&0xffffffff)!=0} {error "DDR readback offset 1808"}
mwr 570427156 0
if {(wide([mrd -value 570427156])&0xffffffff)!=0} {error "DDR readback offset 1812"}
mwr 570427160 0
if {(wide([mrd -value 570427160])&0xffffffff)!=0} {error "DDR readback offset 1816"}
mwr 570427164 0
if {(wide([mrd -value 570427164])&0xffffffff)!=0} {error "DDR readback offset 1820"}
mwr 570427168 0
if {(wide([mrd -value 570427168])&0xffffffff)!=0} {error "DDR readback offset 1824"}
mwr 570427172 0
if {(wide([mrd -value 570427172])&0xffffffff)!=0} {error "DDR readback offset 1828"}
mwr 570427176 0
if {(wide([mrd -value 570427176])&0xffffffff)!=0} {error "DDR readback offset 1832"}
mwr 570427180 0
if {(wide([mrd -value 570427180])&0xffffffff)!=0} {error "DDR readback offset 1836"}
mwr 570427184 0
if {(wide([mrd -value 570427184])&0xffffffff)!=0} {error "DDR readback offset 1840"}
mwr 570427188 0
if {(wide([mrd -value 570427188])&0xffffffff)!=0} {error "DDR readback offset 1844"}
mwr 570427192 0
if {(wide([mrd -value 570427192])&0xffffffff)!=0} {error "DDR readback offset 1848"}
mwr 570427196 0
if {(wide([mrd -value 570427196])&0xffffffff)!=0} {error "DDR readback offset 1852"}
mwr 570427200 0
if {(wide([mrd -value 570427200])&0xffffffff)!=0} {error "DDR readback offset 1856"}
mwr 570427204 0
if {(wide([mrd -value 570427204])&0xffffffff)!=0} {error "DDR readback offset 1860"}
mwr 570427208 0
if {(wide([mrd -value 570427208])&0xffffffff)!=0} {error "DDR readback offset 1864"}
mwr 570427212 0
if {(wide([mrd -value 570427212])&0xffffffff)!=0} {error "DDR readback offset 1868"}
mwr 570427216 0
if {(wide([mrd -value 570427216])&0xffffffff)!=0} {error "DDR readback offset 1872"}
mwr 570427220 0
if {(wide([mrd -value 570427220])&0xffffffff)!=0} {error "DDR readback offset 1876"}
mwr 570427224 0
if {(wide([mrd -value 570427224])&0xffffffff)!=0} {error "DDR readback offset 1880"}
mwr 570427228 0
if {(wide([mrd -value 570427228])&0xffffffff)!=0} {error "DDR readback offset 1884"}
mwr 570427232 0
if {(wide([mrd -value 570427232])&0xffffffff)!=0} {error "DDR readback offset 1888"}
mwr 570427236 0
if {(wide([mrd -value 570427236])&0xffffffff)!=0} {error "DDR readback offset 1892"}
mwr 570427240 0
if {(wide([mrd -value 570427240])&0xffffffff)!=0} {error "DDR readback offset 1896"}
mwr 570427244 0
if {(wide([mrd -value 570427244])&0xffffffff)!=0} {error "DDR readback offset 1900"}
mwr 570427248 0
if {(wide([mrd -value 570427248])&0xffffffff)!=0} {error "DDR readback offset 1904"}
mwr 570427252 0
if {(wide([mrd -value 570427252])&0xffffffff)!=0} {error "DDR readback offset 1908"}
mwr 570427256 0
if {(wide([mrd -value 570427256])&0xffffffff)!=0} {error "DDR readback offset 1912"}
mwr 570427260 0
if {(wide([mrd -value 570427260])&0xffffffff)!=0} {error "DDR readback offset 1916"}
mwr 570427264 0
if {(wide([mrd -value 570427264])&0xffffffff)!=0} {error "DDR readback offset 1920"}
mwr 570427268 0
if {(wide([mrd -value 570427268])&0xffffffff)!=0} {error "DDR readback offset 1924"}
mwr 570427272 0
if {(wide([mrd -value 570427272])&0xffffffff)!=0} {error "DDR readback offset 1928"}
mwr 570427276 0
if {(wide([mrd -value 570427276])&0xffffffff)!=0} {error "DDR readback offset 1932"}
mwr 570427280 0
if {(wide([mrd -value 570427280])&0xffffffff)!=0} {error "DDR readback offset 1936"}
mwr 570427284 0
if {(wide([mrd -value 570427284])&0xffffffff)!=0} {error "DDR readback offset 1940"}
mwr 570427288 0
if {(wide([mrd -value 570427288])&0xffffffff)!=0} {error "DDR readback offset 1944"}
mwr 570427292 0
if {(wide([mrd -value 570427292])&0xffffffff)!=0} {error "DDR readback offset 1948"}
mwr 570427296 0
if {(wide([mrd -value 570427296])&0xffffffff)!=0} {error "DDR readback offset 1952"}
mwr 570427300 0
if {(wide([mrd -value 570427300])&0xffffffff)!=0} {error "DDR readback offset 1956"}
mwr 570427304 0
if {(wide([mrd -value 570427304])&0xffffffff)!=0} {error "DDR readback offset 1960"}
mwr 570427308 0
if {(wide([mrd -value 570427308])&0xffffffff)!=0} {error "DDR readback offset 1964"}
mwr 570427312 0
if {(wide([mrd -value 570427312])&0xffffffff)!=0} {error "DDR readback offset 1968"}
mwr 570427316 0
if {(wide([mrd -value 570427316])&0xffffffff)!=0} {error "DDR readback offset 1972"}
mwr 570427320 0
if {(wide([mrd -value 570427320])&0xffffffff)!=0} {error "DDR readback offset 1976"}
mwr 570427324 0
if {(wide([mrd -value 570427324])&0xffffffff)!=0} {error "DDR readback offset 1980"}
mwr 570427328 0
if {(wide([mrd -value 570427328])&0xffffffff)!=0} {error "DDR readback offset 1984"}
mwr 570427332 0
if {(wide([mrd -value 570427332])&0xffffffff)!=0} {error "DDR readback offset 1988"}
mwr 570427336 0
if {(wide([mrd -value 570427336])&0xffffffff)!=0} {error "DDR readback offset 1992"}
mwr 570427340 0
if {(wide([mrd -value 570427340])&0xffffffff)!=0} {error "DDR readback offset 1996"}
mwr 570427344 0
if {(wide([mrd -value 570427344])&0xffffffff)!=0} {error "DDR readback offset 2000"}
mwr 570427348 0
if {(wide([mrd -value 570427348])&0xffffffff)!=0} {error "DDR readback offset 2004"}
mwr 570427352 0
if {(wide([mrd -value 570427352])&0xffffffff)!=0} {error "DDR readback offset 2008"}
mwr 570427356 0
if {(wide([mrd -value 570427356])&0xffffffff)!=0} {error "DDR readback offset 2012"}
mwr 570427360 0
if {(wide([mrd -value 570427360])&0xffffffff)!=0} {error "DDR readback offset 2016"}
mwr 570427364 0
if {(wide([mrd -value 570427364])&0xffffffff)!=0} {error "DDR readback offset 2020"}
mwr 570427368 0
if {(wide([mrd -value 570427368])&0xffffffff)!=0} {error "DDR readback offset 2024"}
mwr 570427372 0
if {(wide([mrd -value 570427372])&0xffffffff)!=0} {error "DDR readback offset 2028"}
mwr 570427376 0
if {(wide([mrd -value 570427376])&0xffffffff)!=0} {error "DDR readback offset 2032"}
mwr 570427380 0
if {(wide([mrd -value 570427380])&0xffffffff)!=0} {error "DDR readback offset 2036"}
mwr 570427384 0
if {(wide([mrd -value 570427384])&0xffffffff)!=0} {error "DDR readback offset 2040"}
mwr 570427388 0
if {(wide([mrd -value 570427388])&0xffffffff)!=0} {error "DDR readback offset 2044"}
wr dma_address 570425344
wr dma_time_offset 76031978976
wr dma_max_bursts 16
wr dma_watchdog 134217728
wr dma_start 1

set deadline [expr {[clock milliseconds]+3000}]
while {[rd dma_pending]==0} {
 if {[clock milliseconds]>$deadline} {error "DMA completion timeout; restoration required"}
 after 1
}
if {[rd dma_active]!=0 || [rd dma_reject]!=0 || [rd dma_result_error]!=0} {error "DMA failed/rejected"}
if {[rd dma_accepted]!=$accepted+1 || [rd dma_completed]!=$completed+1} {error "Missing hardware DMA epoch"}
if {[rd aux_rt_reply_fault]!=0 || [rd aux_rtio_error_flags]!=0} {error "Satellite RTIO fault"}
puts "SATELLITE_DDR_DMA_ADMITTED_PASS bursts_limit=16 readback_bytes=2048"
disconnect

