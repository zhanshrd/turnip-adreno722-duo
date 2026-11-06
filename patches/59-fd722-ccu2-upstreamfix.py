#!/usr/bin/env python3
"""FD722: num_ccu 1 -> 2, tracking upstream mesa commit 8c589b89 ("Fix the A722 CCU count").

Upstream (MR 45827, 2026-11-01) established that the A722 has 2 CCUs and
2 SPs, not 1: pvtmem is sized per SP from num_ccu, so with 1 the second SP
runs off the end of the BO and any shader that spills register storage hits
UCHE translation faults, whose hang recovery leaves stale results.

This also un-does the num_ccu = 1 override that 56-fd722-blob.py writes into
the FD722 block. The blob traces that suggested 1 CCU contradict upstream's
finding; upstream's commit message describes a concrete failure mechanism,
so upstream wins. tile_align_h stays at 16 (upstream's own value after the
same fix); the t30replica variant continues to test T30's 32 on top of this.

Runs after 56/57. Exits non-zero unless the block ends at num_ccu = 2.
"""
import re
import sys

NAME = "59-fd722-ccu2-upstreamfix.py"
DEVICES_PY = "src/freedreno/common/freedreno_devices.py"


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

    if re.search(r"\bnum_ccu\s*=\s*2\b", block):
        print(f"{NAME}: already applied (FD722 num_ccu = 2)")
        return 0

    new, n = re.subn(r"\bnum_ccu\s*=\s*1\b", "num_ccu = 2", block, count=1)
    if not n:
        print(f"{NAME}: ERROR no 'num_ccu = 1' anchor in the FD722 block; "
              f"block not modified", file=sys.stderr)
        return 1

    open(DEVICES_PY, "w", encoding="utf-8", newline="\n").write(src.replace(block, new, 1))
    print(f"{NAME}: applied (FD722 num_ccu 1->2 per upstream 8c589b89)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
