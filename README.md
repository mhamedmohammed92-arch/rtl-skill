# rtl-skill

**Teach your AI coding agent to build right-to-left interfaces that actually
work in Hebrew, Arabic, Persian and Urdu.**

A skill for Claude Code, a rule for Cursor, an `AGENTS.md` block for Codex and
every other agent, and a zero-dependency checker that finds the RTL bugs
before your users do. MIT.

---

## The problem

Coding agents learned CSS from a left-to-right web. Ask one for a Hebrew or
Arabic page and it writes `ml-4`, `text-left`, `margin-right`, `tracking-wide`
and `flex-row-reverse` by habit. The result looks fine in review and breaks for
every RTL user:

- spacing, borders and rounded corners sit on the wrong side;
- phone numbers come out in the wrong order (`+972 50 123 4567` shows as
  `4567 123 50 972+`);
- letter-spacing tears the joined letters of Arabic apart;
- the page flashes left-to-right on every first visit;
- an off-canvas menu adds a horizontal scrollbar that only exists in RTL.

This repo gives the agent the rules up front, and gives you a checker that
proves it followed them.

## What the checker finds

```text
$ python rtl_check.py examples/
examples/checkout.tsx:5:5   error  html-dir           <html lang="he"> has no dir; the first paint is left-to-right  ->  add dir="rtl" in the static HTML
examples/checkout.tsx:7:31  warn   tw-row-reverse     flex rows already follow dir; reversing one 'for RTL' flips it twice  ->  remove it and let dir order the row
examples/checkout.tsx:8:29  error  tw-physical        text-left does not flip in RTL  ->  text-start
examples/checkout.tsx:8:39  error  tw-physical        ml-2 does not flip in RTL  ->  ms-2
examples/checkout.tsx:9:29  error  tw-physical        rounded-l-lg does not flip in RTL  ->  rounded-s-lg
examples/checkout.tsx:10:11 warn   input-dir          type="tel" values are left-to-right and scramble on RTL pages  ->  add dir="ltr" to the input
examples/checkout.tsx:12:26 error  js-physical-style  marginRight is a physical side in a style object  ->  marginInlineEnd
...
rtl-check: 10 error(s), 5 warning(s) in 1 file(s)
```

Every finding names the exact fix. The checker knows the difference between a
bug and an intent: `left-1/2 -translate-x-1/2` (centring), `rtl:ml-4`,
`[dir="rtl"] .x { right: 0 }` and `html[lang=en] .k { letter-spacing: 2px }`
are left alone.

On its first run against a production Hebrew/Arabic web app it found nine
phone and e-mail inputs with no `dir="ltr"` on pages that default to Hebrew,
where a phone number typed with spaces or a leading `+` comes out in the
wrong order.

## Install

### Claude Code

```text
/plugin marketplace add mhamedmohammed92-arch/rtl-skill
/plugin install rtl@tervatrix
```

Or both in one command (Claude Code 2.1.275 or later):
`/plugin install rtl --marketplace mhamedmohammed92-arch/rtl-skill`

The `rtl-ui` skill then loads by itself whenever you work on RTL UI (it costs
about 100 tokens until it fires). Or copy
`plugins/rtl/skills/rtl-ui/` into `~/.claude/skills/` by hand.

### Cursor

Copy [`cursor/rtl-ui.mdc`](cursor/rtl-ui.mdc) into your project's
`.cursor/rules/` folder.

### Codex, Windsurf, Copilot, Gemini CLI and others

Append [`agents/RTL.md`](agents/RTL.md) to your `AGENTS.md` (or
`.github/copilot-instructions.md`, `GEMINI.md`, ...).

### The checker on its own

It is one Python file with no dependencies (Python 3.8+):

```bash
curl -O https://raw.githubusercontent.com/mhamedmohammed92-arch/rtl-skill/main/plugins/rtl/skills/rtl-ui/scripts/rtl_check.py
python rtl_check.py src/            # errors fail with exit code 1
python rtl_check.py src/ --strict   # also transforms and directional icons
python rtl_check.py src/ --json     # for tooling
```

In CI (GitHub Actions):

```yaml
- run: curl -sO https://raw.githubusercontent.com/mhamedmohammed92-arch/rtl-skill/main/plugins/rtl/skills/rtl-ui/scripts/rtl_check.py
- run: python rtl_check.py src/
```

A line that is right on purpose can end with the comment `rtl-check: ignore`.

## Rules

| Rule | Severity | Catches |
|---|---|---|
| `css-physical-spacing` | error | `margin-left`, `padding-right`, ... |
| `css-physical-border` | error | `border-left`, `border-right-color`, ... |
| `css-physical-radius` | error | `border-top-left-radius`, ... |
| `css-text-align` | error | `text-align: left / right` |
| `css-float` | error | `float: left / right` |
| `css-physical-inset` | warn | `left:` / `right:` in stylesheets and `style=""` |
| `css-letter-spacing` | warn | non-zero `letter-spacing` not scoped to Latin |
| `css-row-reverse` | warn | `flex-direction: row-reverse` |
| `tw-physical` | error | `ml-* mr-* pl-* pr-* left-* right-* text-left rounded-l-* border-r-* scroll-ml-* float-left`, ... |
| `tw-space-x` | warn | `space-x-*` (physical up to Tailwind v3) |
| `tw-letter-spacing` | warn | `tracking-*` |
| `tw-row-reverse` | warn | `flex-row-reverse` |
| `js-physical-style` | error | `marginLeft`, `paddingRight`, `borderLeftWidth`, ... in style objects |
| `js-text-align` | error | `textAlign: 'left'` |
| `js-letter-spacing` | warn | `letterSpacing: 2` |
| `html-dir` | error | `<html lang="he">` (or `ar`, `fa`, `ur`, ...) without `dir` |
| `html-viewport-zoom` | warn | `maximum-scale=1`, `user-scalable=no`, `maximumScale: 1` |
| `input-dir` | warn | `type="tel"`, `"email"`, `"url"` inputs without `dir="ltr"` |
| `css-translate-x` | hint | physical transforms (`--strict`) |
| `icon-direction` | hint | `ChevronLeft`, `arrow-right`, ... that may need mirroring (`--strict`) |

Scans `.css .scss .less .html .vue .svelte .astro .jsx .tsx .js .ts .php` and
common template files; skips `node_modules`, build output, minified files and
tests.

## What the skill teaches

Five rules (direction in HTML before first paint, logical CSS only, let flex
and grid follow `dir`, isolate mixed-direction text, respect the script), a
Tailwind physical-to-logical table, and the traps that pass review: direction
flash, `rtl:` variants that silently miss, off-canvas scrollbars, transforms,
icons, reversed phone numbers and times, Arabic-Indic digits from
`toLocaleString`, SVG labels, silent font fallback, and fixed heights. Read it
in [`SKILL.md`](plugins/rtl/skills/rtl-ui/SKILL.md).

## Related

- [tervatrix-rtl](https://github.com/mhamedmohammed92-arch/tervatrix-rtl)
  (Python, `pip install tervatrix-rtl`): fixes the same bidi bugs in plain
  text, for WhatsApp, SMS, push and e-mail, where there is no markup.
- [tervatrix-rtl-ui](https://github.com/mhamedmohammed92-arch/tervatrix-rtl-ui):
  framework-free JavaScript helpers and logical-property CSS for Hebrew and
  Arabic interfaces.
- [wa-agent-starter](https://github.com/mhamedmohammed92-arch/wa-agent-starter):
  a small WhatsApp agent on the official Cloud API that answers in Hebrew,
  Arabic and English. The full production kit is at
  [tervatrix.com/wa-agent-kit](https://tervatrix.com/wa-agent-kit/).

## Contributing

`SKILL.md` is the single source. After editing it run
`python tools/build.py` to regenerate the Cursor and `AGENTS.md` copies, and
`python -m pytest tests` before opening a pull request. New checker rules need
a test that shows the bug firing and the fix staying quiet.

Built by [Tervatrix](https://tervatrix.com), from bugs that reached real
Hebrew and Arabic users first.
