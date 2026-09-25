"""Generate the Cursor rule and the AGENTS.md block from the one skill file.

SKILL.md is the single source. Run this after editing it:

    python tools/build.py          # rewrite the generated files
    python tools/build.py --check  # exit 1 if they are out of date (CI)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "plugins", "rtl", "skills", "rtl-ui", "SKILL.md")
RAW = ("https://raw.githubusercontent.com/mhamedmohammed92-arch/rtl-skill/"
       "main/plugins/rtl/skills/rtl-ui/scripts/rtl_check.py")
PLACEHOLDER = '`python "<this skill\'s directory>/scripts/rtl_check.py" src/`'
REPLACEMENT = "`python rtl_check.py src/` (get the file once: `curl -O %s`)" % RAW
NOTE = ("<!-- Generated from plugins/rtl/skills/rtl-ui/SKILL.md by "
        "tools/build.py - edit that file, not this one. -->\n\n")

CURSOR_HEAD = """---
description: Build and review right-to-left (Hebrew, Arabic, Persian, Urdu) interfaces without the usual RTL bugs. Apply when writing or editing UI, CSS or Tailwind classes for an RTL language.
globs:
alwaysApply: false
---

"""


def body():
    text = open(SKILL, encoding="utf-8").read()
    if not text.startswith("---"):
        raise SystemExit("SKILL.md has no front matter")
    text = text.split("---", 2)[2].lstrip("\n")
    if PLACEHOLDER not in text:
        raise SystemExit("SKILL.md no longer contains the checker command")
    # Outside Claude Code there is no skill directory: point at a local copy
    # of the checker and say where to get it.
    return text.replace(PLACEHOLDER, REPLACEMENT)


def outputs():
    b = body()
    return {
        os.path.join(ROOT, "cursor", "rtl-ui.mdc"): CURSOR_HEAD + NOTE + b,
        os.path.join(ROOT, "agents", "RTL.md"): NOTE + b,
    }


def main(argv):
    stale = []
    for path, content in outputs().items():
        current = ""
        if os.path.exists(path):
            current = open(path, encoding="utf-8").read()
        if current != content:
            stale.append(os.path.relpath(path, ROOT))
            if "--check" not in argv:
                with open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(content)
    if "--check" in argv and stale:
        print("out of date: %s (run python tools/build.py)" % ", ".join(stale))
        return 1
    print("up to date" if not stale else "wrote %s" % ", ".join(stale))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
