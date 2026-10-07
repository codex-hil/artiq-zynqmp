#![no_std]

#[cfg(feature = "alloc")]
extern crate alloc;

pub mod cursor;
#[cfg(feature = "byteorder")]
pub mod proto;

pub use cursor::Cursor;
#[cfg(all(feature = "byteorder", feature = "alloc"))]
pub use proto::ReadStringError;
#[cfg(feature = "byteorder")]
pub use proto::{ProtoRead, ProtoWrite};
