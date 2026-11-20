// SPDX-License-Identifier: LGPL-3.0-or-later
//! Isolated no_std target library; not bootable firmware or runtime integration.
#![no_std]
#[macro_use]
extern crate failure_derive;
extern crate failure;
extern crate io;
extern crate crc;
mod protocol {include!(env!("ARTIQ_AUX_PROTOCOL"));}
mod master_leaf_codec;
mod master_control_codec;
extern "C" {fn aux_master_panic()->!;}
#[panic_handler]
fn panic(_: &core::panic::PanicInfo)->! {unsafe{aux_master_panic()}}
