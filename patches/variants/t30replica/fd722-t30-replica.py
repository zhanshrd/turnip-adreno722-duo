#!/usr/bin/env python3
"""FD722 t30replica variant: rewrite the Duo blob calibration to MrPurple T30's device values.

Runs after 56-fd722-blob.py (which installed a722_raw_magic_regs, num_ccu 1,
tile_align_h 16, highest_bank_bit 15, has_lpac False), and rewrites the FD722
block to the configuration MrPurple666's T30 package ships and that renders
cleanly on this chip:

  num_ccu          1 -> 2      (T30 meta.json)
  tile_align_h    16 -> 32     (T30 meta.json)
  highest_bank_bit 15 -> 16    (T30 meta.json)
  raw_magic_regs  a722_raw_magic_regs -> a730_raw_magic_regs (T30 = plain Mesa)
  GPUProps(has_lpac = False, enable_tp_ubwc_flag_hint = False) dropped
                               (T30 = plain upstream a7xx_base, lpac True)
  magic_regs stays a730_magic_regs where the ref uses it (August style).

Everything else in this build - gralloc UBWC detection, UBWC swapchains, the
KGSL governor lock, the QCOM_COMPRESSED guard, the two mesa-stable backports
and the sample-interp fix - is kept from the Duo stack. Only the device block
returns to the T30 baseline.

This variant exists to A/B the only never-tested combination: T30's device
values together with the Duo performance patches. Exits non-zero on any
missing anchor so a silent half-application cannot ship.
"""
import re
import sys

NAME = "fd722-t30-replica.py"
DEVICES_PY = "src/freedreno/common/freedreno_devices.py"

SUMMARY = ("FD722 t30replica: num_ccu=2, tile_align_h=32, highest_bank_bit=16, "
           "raw_magic_regs=a730_raw_magic_regs, upstream GPUProps (lpac True)")


def main():
    try:
        src = open(DEVICES_PY, encoding="utf-8").read()
    except OSError as e:
        print(f"{NAME}: ERROR cannot read {DEVICES_PY}: {e}", file=sys.stderr)
        return 1

    m = re.search(r"GPUId\(chip_id=0x43020100.*?\n    \)\)", src, re.S)
    if not m:
        print(f"{NAME}: ERROR FD722 (0x43020100) block not found", file=sys.stderr)
        return 1
    block = m.group(0)

    if "num_ccu = 2" in block and "raw_magic_regs = a730_raw_magic_regs" in block \
            and "GPUProps" not in block.split("CHIP.A7XX,", 1)[-1]:
        print(f"{NAME}: already applied")
        return 0

    new = block
    done = []

    # Drop the Duo GPUProps overrides so a7xx_base's own values apply (T30).
    new, n = re.subn(
        r", GPUProps\(has_lpac = False, enable_tp_ubwc_flag_hint = False\)",
        "", new, count=1)
    if n:
        done.append("GPUProps dropped (lpac/ubwc-hint upstream)")

    new, n = re.subn(r"\bnum_ccu\s*=\s*1\b", "num_ccu = 2", new, count=1)
    if n:
        done.append("num_ccu 1->2")
    new, n = re.subn(r"\btile_align_h\s*=\s*16\b", "tile_align_h = 32", new, count=1)
    if n:
        done.append("tile_align_h 16->32")
    new, n = re.subn(r"\bhighest_bank_bit\s*=\s*15\b", "highest_bank_bit = 16",
                     new, count=1)
    if n:
        done.append("highest_bank_bit 15->16")
    new, n = re.subn(r"\braw_magic_regs\s*=\s*a722_raw_magic_regs\b",
                     "raw_magic_regs = a730_raw_magic_regs", new, count=1)
    if n:
        done.append("raw_magic_regs -> a730")

    missing = [key for key in ("num_ccu = 2", "tile_align_h = 32",
                               "highest_bank_bit = 16",
                               "raw_magic_regs = a730_raw_magic_regs")
               if key not in new]
    if missing:
        print(f"{NAME}: ERROR rewrite incomplete, missing: {', '.join(missing)}; "
              f"block not modified", file=sys.stderr)
        return 1

    open(DEVICES_PY, "w", encoding="utf-8", newline="\n").write(src.replace(block, new, 1))
    print(f"{NAME}: applied ({SUMMARY})")
    print(f"{NAME}: " + "; ".join(done))
    return 0


if __name__ == "__main__":
    sys.exit(main())
