<!-- Generated from plugins/rtl/skills/rtl-ui/SKILL.md by tools/build.py - edit that file, not this one. -->

# RTL UI

Right-to-left bugs are invisible in an English review and obvious to every
Hebrew or Arabic user. Almost all of them come from a handful of habits:
writing `left`/`right` where the layout should follow the reading direction,
and letting numbers, phone numbers and Latin words fend for themselves inside
RTL sentences. Follow the rules below while you write the code, then run the
checker before you call the work done.

## The five rules

1. **Direction lives in HTML, set before the first paint.** Put
   `<html lang="he" dir="rtl">` (or `ar`, `fa`, `ur`) in the static HTML or the
   root layout. If the language is picked at runtime, set `lang` and `dir` on
   `<html>` in an inline script in `<head>`, before the stylesheet renders.
   Never use the CSS `direction` property for page direction: the `dir`
   attribute is what browsers, screen readers and Tailwind's `rtl:` variant read.
2. **Only logical CSS.** Never `left`/`right` for layout. Use
   `margin-inline-start/end`, `padding-inline-start/end`,
   `border-inline-start/end`, `border-start-start-radius` (and the other three
   corners), `inset-inline-start/end`, `text-align: start/end`,
   `float: inline-start/end`. In Tailwind (3.3+), use the table below.
3. **Let flex and grid follow `dir`.** A flex row and grid columns already run
   right-to-left in an RTL page. Never add `flex-row-reverse` / `row-reverse`
   "for RTL": it flips the row a second time, back to LTR order.
4. **Isolate mixed-direction text.** Numbers, prices, phone numbers, e-mails,
   URLs, product codes and Latin names inside an RTL sentence get reordered by
   the Unicode bidi algorithm. Wrap values of unknown direction in `<bdi>` (or
   `unicode-bidi: isolate`), give user-generated text `dir="auto"`, and give
   `type="tel"`, `type="email"` and `type="url"` inputs `dir="ltr"`.
5. **Respect the script.** No `letter-spacing` on Arabic, Persian or Urdu: it
   pulls joined letters apart (scope tracking to Latin with `:lang(en)`).
   Arabic needs more line-height than Latin (about 1.6-1.8 for body text) or its
   dots and marks clip. Form controls do not inherit the page font: add
   `button, input, select, textarea { font: inherit; }`.

## Tailwind: physical class -> logical class

| Physical (does not flip) | Logical (flips with `dir`) |
|---|---|
| `ml-*` `mr-*` `pl-*` `pr-*` | `ms-*` `me-*` `ps-*` `pe-*` |
| `left-*` `right-*` | `start-*` `end-*` |
| `text-left` `text-right` | `text-start` `text-end` |
| `rounded-l-*` `rounded-r-*` | `rounded-s-*` `rounded-e-*` |
| `rounded-tl-*` `rounded-tr-*` `rounded-bl-*` `rounded-br-*` | `rounded-ss-*` `rounded-se-*` `rounded-es-*` `rounded-ee-*` |
| `border-l-*` `border-r-*` | `border-s-*` `border-e-*` |
| `scroll-ml-*` `scroll-pr-*` ... | `scroll-ms-*` `scroll-pe-*` ... |
| `float-left` `float-right` | `float-start` `float-end` (v4), or use flex/grid |
| `space-x-*` (physical up to v3) | `gap-x-*` on the flex/grid parent |

Use `rtl:` / `ltr:` variants only for things that are truly different per
direction (an icon that must be mirrored, a transform). They only work when
`dir` is on an ancestor before the first paint (rule 1).

## Traps that pass review and break in production

Each of these shipped in a real product before it was caught.

- **Direction flash.** The static HTML says `lang="en"` (or nothing) and a
  script switches to RTL after load: every first visit renders left-to-right,
  then jumps. The static `lang`/`dir` must match the default language.
- **`rtl:` classes that silently do nothing.** When `dir` is applied late or
  on the wrong element, every `rtl:` variant misses. In one app a drawer
  styled only with `rtl:` classes disappeared completely in Hebrew.
- **Off-canvas menus create a horizontal scrollbar in RTL.** A drawer parked
  off-screen with `left: 0; transform: translateX(-100%)` is unreachable in
  LTR but becomes scrollable overflow in RTL, because RTL pages scroll toward
  the left. Position it with `inset-inline-start`, mirror the transform under
  `[dir="rtl"]`, and use `overflow-x: clip` (not `hidden`, which breaks
  `position: sticky` below it).
- **Transforms are physical.** `translateX`, slide-in animations and
  `scaleX` do not flip. Mirror them under `[dir="rtl"]`.
- **Directional icons.** Back/next arrows, chevrons in navigation, and
  "continue" arrows must be mirrored in RTL (`rtl:-scale-x-100`). Do not mirror
  logos, check marks, clocks, or media play/pause controls.
- **Centring is not a direction bug.** `left: 50%` + `translateX(-50%)` (or
  `left-1/2 -translate-x-1/2`) centres in both directions. Changing only the
  first half to `start-1/2` pushes the element off centre in RTL.
- **Phone numbers and times turn around.** Inside RTL text,
  `+972 4 000 0000` renders as `0000 000 4 972+` and `09:00 - 18:00` as
  `18:00 - 09:00`: the spaces between the number groups take the RTL
  direction, so the groups are laid out right to left. Wrap such values in
  `<bdi dir="ltr">` or an LTR isolate. In plain-text channels (SMS,
  WhatsApp, push, e-mail subjects) there is no markup: use Unicode isolates or
  marks (LRI U+2066 ... PDI U+2069, or LRM U+200E / RLM U+200F).
- **A Hebrew line that starts with a Latin word goes LTR.** "WhatsApp ..." at
  the start of a Hebrew paragraph makes `dir="auto"`, and every plain-text app
  that guesses direction from the first strong letter, lay the whole line out
  left-to-right. Set the direction explicitly, or prefix plain text with RLM.
- **Digits.** `toLocaleString('ar')` may return Arabic-Indic digits
  (U+0660-0669) depending on runtime and region. Decide which digits the
  product shows and pin it: `'ar-u-nu-latn'` for 0-9, `'ar-u-nu-arab'` for
  Arabic-Indic. Never mix the two on one screen.
- **SVG and charts do not mirror themselves.** Setting `direction="rtl"` on an
  SVG root changes what `text-anchor="start"` means and moves every label.
  Keep the SVG geometry LTR and give each RTL string its own direction.
- **Fonts fall back silently.** A web font blocked by CSP or the network
  falls back without an error, often to a font with poor Hebrew/Arabic
  glyphs. Start the stack with `system-ui` and self-host the web font.
- **Fixed heights clip translated text.** Hebrew, Arabic and Russian strings
  are often longer, and Arabic is taller. Use `min-height`, never `height`, on
  text containers, and check the longest language at 360px wide.
- **Uppercase and tracking are Latin tools.** `text-transform: uppercase`
  does nothing to Hebrew/Arabic, so a design that relies on it for emphasis
  loses it; use weight instead.

## Verify before you finish

1. Run the checker on what you changed:
   `python rtl_check.py src/` (get the file once: `curl -O https://raw.githubusercontent.com/mhamedmohammed92-arch/rtl-skill/main/plugins/rtl/skills/rtl-ui/scripts/rtl_check.py`)
   (it prints `file:line:col  severity  rule  message  ->  fix`). Fix every
   error. Read every warning; if a line is right on purpose, end it with the
   comment `rtl-check: ignore`. `--strict` also lists transforms and
   directional icons to review by eye.
2. In the browser: switch the language live (not only on first load) and
   confirm the header, drawer, forms and icons follow; check 360px and 768px
   widths with the longest language; look for a horizontal scrollbar; type a
   phone number and an e-mail into the forms.
