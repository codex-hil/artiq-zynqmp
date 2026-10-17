"""Optional master playback admission result; LGPL-3.0-or-later."""
from pathlib import Path


def apply(source,replace_once):
    firmware=Path(source)/'artiq/firmware'
    protocol=firmware/'libproto_artiq/kernel_proto.rs'
    protocol.write_text(replace_once(protocol.read_text(),
        '    DmaAwaitRemoteRequest {\n',
        '    DmaStartRemoteReply { succeeded: bool },\n\n    DmaAwaitRemoteRequest {\n'))
    runtime=firmware/'runtime/session.rs'
    old='''                #[cfg(has_drtio)]
                remote_dma::playback(io, aux_mutex, ddma_mutex, subkernel_mutex, routing_table, _id as u32, _timestamp as u64)?;
                kern_acknowledge()'''
    new='''                let mut succeeded = true;
                #[cfg(has_drtio)]
                if let Err(error) = remote_dma::playback(io, aux_mutex, ddma_mutex, subkernel_mutex, routing_table, _id as u32, _timestamp as u64) {
                    error!("DDMA playback rejected: {}", error);
                    succeeded = false;
                }
                kern_send(io, &kern::DmaStartRemoteReply { succeeded: succeeded })'''
    runtime.write_text(replace_once(runtime.read_text(),old,new))
    kernel=firmware/'ksupport/lib.rs';text=kernel.read_text()
    begin=text.index('#[cfg(kernel_has_rtio_dma)]\nextern "C-unwind" fn dma_playback')
    end=text.index('#[cfg(all(not(kernel_has_rtio_dma), not(has_rtio_dma)))]',begin)
    part=text[begin:end]
    part=replace_once(part,'    assert!(ptr % 64 == 0);',
        '    assert!(ptr % 64 == 0);\n    #[cfg(has_drtio)]\n    let mut remote_started = true;')
    part=replace_once(part,'            send(&DmaStartRemoteRequest { id: ptr as i32, timestamp: timestamp });',
        '            send(&DmaStartRemoteRequest { id: ptr as i32, timestamp: timestamp });\n'
        '            remote_started = recv!(&DmaStartRemoteReply { succeeded } => succeeded);')
    part=replace_once(part,'        send(&DmaAwaitRemoteRequest { id: ptr as i32 });',
        '        // Local enable has drained, CRI ownership and local errors are restored.\n'
        '        // Reply was acknowledged before raising; no wait for absent status.\n'
        '        if !remote_started {\n'
        '            raise!("DMAError", "Failed to start distributed DMA playback");\n'
        '        }\n'
        '        send(&DmaAwaitRemoteRequest { id: ptr as i32 });')
    kernel.write_text(text[:begin]+part+text[end:])
