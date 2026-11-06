#!/usr/bin/env python3
"""t30replica variant: revert 36's PREFER_SYSMEM autotune default to upstream BANDWIDTH.

MrPurple T30 runs plain upstream tu_autotune (DEFAULT = BANDWIDTH), which picks
GMEM or sysmem per render pass from measured bandwidth. 36-tu-z-sysmem-only.py
pins the default to PREFER_SYSMEM; this variant restores the upstream line so
the t30replica build behaves exactly like T30 for render-mode selection, while
keeping every other Duo patch.

Exits non-zero if neither the patched nor the upstream line is present, so a
variant built against a moved autotune anchor cannot ship silently.
"""
import sys

NAME = "autotune-default-upstream.py"
AUTOTUNE = "src/freedreno/vulkan/tu_autotune.cc"

PREFER = "   DEFAULT = PREFER_SYSMEM, /* Default algorithm for Adreno 722 1 MiB GMEM. */\n"
UPSTREAM = "   DEFAULT = BANDWIDTH, /* Default algorithm, used if no other is specified. */\n"


def main():
    try:
        s = open(AUTOTUNE, encoding="utf-8").read()
    except OSError as e:
        print(f"{NAME}: ERROR cannot read {AUTOTUNE}: {e}", file=sys.stderr)
        return 1

    if UPSTREAM in s and PREFER not in s:
        print(f"{NAME}: already applied")
        return 0

    if s.count(PREFER) != 1:
        print(f"{NAME}: ERROR anchor matched {s.count(PREFER)}x in {AUTOTUNE}; "
              f"36's patched line not found exactly once", file=sys.stderr)
        return 1

    s = s.replace(PREFER, UPSTREAM, 1)
    open(AUTOTUNE, "w", encoding="utf-8", newline="\n").write(s)
    print(f"{NAME}: applied (tu_autotune DEFAULT back to upstream BANDWIDTH)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
