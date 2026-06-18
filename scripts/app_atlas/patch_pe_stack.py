#!/usr/bin/env python3
"""Patch a Windows PE executable's SizeOfStackReserve (main-thread stack).

Why: apkeep 1.0.0's google-play download path overflows the default 1 MB
main-thread stack on Windows during protobuf decode (crashes with
"thread 'main' has overflowed its stack"). RUST_MIN_STACK only affects
spawned threads, not main. The reserved main-thread stack size lives in
the PE optional header and can be bumped in-place.

Usage:
    py _patch_pe_stack.py <exe> <reserve_bytes>
    py _patch_pe_stack.py apkeep.exe 67108864   # 64 MB
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path


def patch(path: Path, reserve: int) -> None:
    data = bytearray(path.read_bytes())
    if data[:2] != b"MZ":
        raise SystemExit("not an MZ/PE file")
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    if data[e_lfanew:e_lfanew + 4] != b"PE\0\0":
        raise SystemExit("PE signature not found")
    coff = e_lfanew + 4
    opt = coff + 20                      # optional header starts after 20-byte COFF header
    magic = struct.unpack_from("<H", data, opt)[0]
    if magic == 0x20B:                   # PE32+
        off = opt + 72                   # SizeOfStackReserve (8 bytes)
        cur = struct.unpack_from("<Q", data, off)[0]
        struct.pack_into("<Q", data, off, reserve)
    elif magic == 0x10B:                 # PE32
        off = opt + 72                   # SizeOfStackReserve (4 bytes)
        cur = struct.unpack_from("<I", data, off)[0]
        struct.pack_into("<I", data, off, reserve)
    else:
        raise SystemExit(f"unknown optional-header magic 0x{magic:X}")
    path.write_bytes(data)
    print(f"patched {path.name}: SizeOfStackReserve {cur:#x} -> {reserve:#x}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    patch(Path(sys.argv[1]), int(sys.argv[2]))
