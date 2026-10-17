"""Optional record-stop mailbox result for pinned master; LGPL-3.0-or-later."""
from pathlib import Path


def apply(source,replace_once):
    firmware=Path(source)/'artiq/firmware'
    protocol=firmware/'libproto_artiq/kernel_proto.rs'
    text=replace_once(protocol.read_text(),
        '    DmaEraseRequest {\n',
        '    DmaRecordStopReply { succeeded: bool },\n\n    DmaEraseRequest {\n')
    protocol.write_text(text)
    kernel=firmware/'ksupport/lib.rs'
    text=replace_once(kernel.read_text(),
        '            enable_ddma: enable_ddma\n        });',
        '            enable_ddma: enable_ddma\n        });\n'
        '        // Acknowledge the reply before raising: runtime waits for it.\n'
        '        let succeeded = recv!(&DmaRecordStopReply { succeeded } => succeeded);\n'
        '        if !succeeded {\n'
        '            raise!("DMAError", "Failed to upload distributed DMA trace");\n'
        '        }')
    kernel.write_text(text)
    runtime=firmware/'runtime/session.rs'
    old='''                #[cfg(has_drtio)]
                if enable_ddma {
                    remote_dma::upload_traces(io, aux_mutex, ddma_mutex, subkernel_mutex, routing_table, _id)?;
                }
                cache::flush_l2_cache();
                kern_acknowledge()'''
    new='''                let mut succeeded = true;
                #[cfg(has_drtio)]
                if enable_ddma {
                    if let Err(error) = remote_dma::upload_traces(io, aux_mutex, ddma_mutex, subkernel_mutex, routing_table, _id) {
                        error!("DDMA upload rejected: {}", error);
                        succeeded = false;
                    }
                }
                cache::flush_l2_cache();
                kern_send(io, &kern::DmaRecordStopReply { succeeded: succeeded })'''
    runtime.write_text(replace_once(runtime.read_text(),old,new))
