"""Tests for rtl_check: every rule fires on the bug and stays quiet on the fix."""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "plugins", "rtl", "skills",
                                "rtl-ui", "scripts"))
import rtl_check  # noqa: E402


def rules(name, text, strict=False):
    return [(f.rule, f.severity, f.fix)
            for f in rtl_check.scan_text(name, text, strict)]


def ids(name, text, strict=False):
    return [r for r, _, _ in rules(name, text, strict)]


# ------------------------------------------------------------------- CSS
@pytest.mark.parametrize("css, fix", [
    (".a { margin-left: 8px }", "margin-inline-start"),
    (".a { padding-right: 8px }", "padding-inline-end"),
    (".a { border-left: 1px solid }", "border-inline-start"),
    (".a { border-right-color: red }", "border-inline-end-color"),
    (".a { border-top-left-radius: 4px }", "border-start-start-radius"),
    (".a { border-bottom-right-radius: 4px }", "border-end-end-radius"),
    (".a { text-align: left }", "text-align: start"),
    (".a { float: right }", "float: inline-end"),
])
def test_physical_css_is_an_error_with_the_logical_fix(css, fix):
    found = rules("a.css", css)
    assert len(found) == 1
    assert found[0][1] == "error"
    assert found[0][2] == fix


def test_logical_css_is_clean():
    css = """.a { margin-inline-start: 8px; padding-inline-end: 4px;
    border-inline-start: 1px solid; text-align: start; float: inline-end;
    border-start-start-radius: 4px; inset-inline-start: 0; }"""
    assert rules("a.css", css) == []


def test_inset_left_is_a_warning_but_centring_is_not():
    assert ids("a.css", ".a { left: 0 }") == ["css-physical-inset"]
    assert ids("a.css", ".a { left: 50%; transform: translateX(-50%) }") == []
    assert ids("a.css", ".a { right: auto }") == []


def test_inset_ignores_scss_variables_and_page_selectors():
    assert ids("a.scss", "$left: 10px;\n@page :left { margin: 0 }") == []


@pytest.mark.parametrize("value, flagged", [
    ("0", False), ("0px", False), ("0 !important", False), ("normal", False),
    ("0.05em", True), ("-0.02em", True), ("2px", True), (".1em", True),
])
def test_letter_spacing_only_flags_real_spacing(value, flagged):
    found = ids("a.css", ".t { letter-spacing: %s; }" % value)
    assert (found == ["css-letter-spacing"]) is flagged


def test_row_reverse_is_a_warning():
    assert ids("a.css", ".row { flex-direction: row-reverse }") == [
        "css-row-reverse"]


def test_translate_is_a_hint_only_in_strict_mode():
    css = ".d { transform: translateX(-100%) }"
    assert ids("a.css", css) == []
    assert ids("a.css", css, strict=True) == ["css-translate-x"]


def test_style_block_in_html_gets_the_inset_check():
    html = "<style>\n.a { left: 0 }\n</style>\n<p>left: 0 in prose</p>"
    assert ids("a.html", html) == ["css-physical-inset"]


def test_inline_style_attribute_is_checked():
    assert ids("a.html", '<div style="right: 4px"></div>') == [
        "css-physical-inset"]


# -------------------------------------------------------------- Tailwind
@pytest.mark.parametrize("cls, fix", [
    ("ml-4", "ms-4"), ("mr-auto", "me-auto"), ("pl-[10px]", "ps-[10px]"),
    ("-mr-2", "-me-2"), ("pr-0.5", "pe-0.5"), ("left-0", "start-0"),
    ("right-full", "end-full"), ("text-left", "text-start"),
    ("rounded-l-lg", "rounded-s-lg"), ("rounded-tr", "rounded-se"),
    ("border-l", "border-s"), ("border-r-2", "border-e-2"),
    ("scroll-ml-4", "scroll-ms-4"), ("md:hover:ml-4", "md:hover:ms-4"),
])
def test_physical_tailwind_classes_get_the_logical_class(cls, fix):
    found = rules("a.tsx", '<div className="flex %s gap-2" />' % cls)
    assert [(r, s) for r, s, _ in found] == [("tw-physical", "error")]
    assert found[0][2] == fix


def test_logical_and_direction_specific_classes_are_clean():
    html = ('<div class="ms-4 pe-2 start-0 text-start rounded-s-lg border-e '
            'rtl:ml-4 ltr:mr-4 [dir=rtl]:pl-2 gap-x-4">')
    assert rules("a.html", html) == []


def test_centring_pair_and_custom_class_names_are_not_flagged():
    html = ('<div class="absolute left-1/2 -translate-x-1/2 left-panel '
            'right-col rounded-lg border-red-500 prose">')
    assert rules("a.html", html) == []


def test_tailwind_warnings():
    found = ids("a.vue", '<div class="space-x-4 tracking-wide flex-row-reverse">')
    assert found == ["tw-space-x", "tw-letter-spacing", "tw-row-reverse"]
    assert ids("a.vue", '<div class="space-x-reverse tracking-normal">') == []


def test_class_helpers_and_template_literals():
    src = ("const c = cn('ml-2', active && 'pr-4')\n"
           "<a className={`p-2 ${x} text-right`} />\n"
           "<b :class=\"{ 'mr-4': on }\" />")
    got = [f.fix for f in rtl_check.scan_text("a.jsx", src)]
    assert got == ["ms-2", "pe-4", "text-end", "me-4"]


def test_classes_in_a_stylesheet_are_not_parsed_as_tailwind():
    assert ids("a.css", '.ml-4 { color: red }') == []


# ------------------------------------------------------------ JS styles
def test_style_objects():
    src = ("const s = { marginLeft: 8, paddingRight: 4, borderLeftWidth: 1,"
           " textAlign: 'right', letterSpacing: 2 }")
    found = rules("a.tsx", src)
    assert [f for _, _, f in found] == [
        "marginInlineStart", "paddingInlineEnd", "borderInlineStartWidth",
        "textAlign: 'end'", "apply it only to Latin text"]


def test_style_object_keys_left_right_are_left_alone():
    assert ids("a.ts", "const node = { left: child, right: other }") == []
    assert ids("a.ts", "const s = { letterSpacing: 0 }") == []


# ------------------------------------------------------------------ HTML
def test_rtl_html_without_dir_is_an_error():
    assert ids("a.html", '<html lang="he">') == ["html-dir"]
    assert ids("a.tsx", '<html lang="ar-EG" className="x">') == ["html-dir"]
    assert ids("a.html", '<html lang="he" dir="rtl">') == []
    assert ids("a.html", '<html lang="en">') == []
    assert ids("a.html", '<html lang="hr">') == []  # Croatian, not Hebrew


def test_viewport_zoom_lock():
    bad = '<meta name="viewport" content="width=device-width, maximum-scale=1">'
    assert ids("a.html", bad) == ["html-viewport-zoom"]
    assert ids("a.html", '<meta name="viewport" '
               'content="width=device-width, initial-scale=1">') == []
    assert ids("layout.tsx", "export const viewport = { maximumScale: 1 }") == [
        "html-viewport-zoom"]


def test_phone_and_email_inputs_need_dir_ltr():
    assert ids("a.html", '<input type="tel" name="p">') == ["input-dir"]
    assert ids("a.html", '<input type="email" dir="ltr">') == []
    assert ids("a.html", '<input type="text">') == []


def test_jsx_arrow_function_does_not_end_the_tag_early():
    src = ('<input\n  type="tel"\n  onChange={e => set(e.target.value)}\n'
           '  dir="ltr"\n/>')
    assert ids("a.tsx", src) == []


def test_icons_are_hints_in_strict_mode_only():
    src = "<ChevronLeft /> <i class='fa fa-arrow-right'></i>"
    assert "icon-direction" not in ids("a.jsx", src)
    assert ids("a.jsx", src, strict=True).count("icon-direction") == 2


# ------------------------------------------------------------- plumbing
def test_ignore_comment_silences_one_line():
    css = ".a { margin-left: 8px } /* rtl-check: ignore */\n.b { padding-left: 2px }"
    assert ids("a.css", css) == ["css-physical-spacing"]


def test_ignore_comment_on_a_tag_line():
    assert ids("a.html", '<html lang="he"> <!-- rtl-check: ignore -->') == []


def test_line_and_column_are_reported():
    f = rtl_check.scan_text("a.css", "\n\n  .a { margin-right: 1px }")[0]
    assert (f.line, f.col) == (3, 8)


def test_directory_walk_skips_vendor_and_minified(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.css").write_text(".a { margin-left: 1px }")
    (tmp_path / "src" / "b.min.css").write_text(".a { margin-left: 1px }")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "c.css").write_text(".a { margin-left: 1px }")
    (tmp_path / "README.md").write_text("margin-left: 1px")
    findings, count = rtl_check.scan_paths([str(tmp_path)])
    assert count == 1
    assert len(findings) == 1


def test_exit_codes_and_json(tmp_path, capsys):
    bad = tmp_path / "a.css"
    bad.write_text(".a { margin-left: 1px; letter-spacing: 1px }")
    assert rtl_check.main([str(bad)]) == 1
    warn_only = tmp_path / "b.css"
    warn_only.write_text(".a { letter-spacing: 1px }")
    assert rtl_check.main([str(warn_only)]) == 0
    assert rtl_check.main([str(warn_only), "--strict"]) == 1
    capsys.readouterr()
    rtl_check.main([str(bad), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert {d["rule"] for d in data} == {"css-physical-spacing",
                                         "css-letter-spacing"}


def test_clean_tree_exits_zero(tmp_path, capsys):
    (tmp_path / "a.css").write_text(".a { margin-inline-start: 1px }")
    assert rtl_check.main([str(tmp_path)]) == 0
    assert "0 error(s), 0 warning(s)" in capsys.readouterr().out


def test_direction_scoped_rules_are_intentional():
    css = ('.msg[dir="rtl"] { text-align: right }\n'
           '[dir=rtl] .drawer { right: 0; margin-right: 4px }\n'
           '.x:dir(ltr) { float: left }')
    assert ids("a.css", css) == []


def test_letter_spacing_scoped_to_latin_is_the_fix_not_the_bug():
    css = ("html[lang='en'] .k { letter-spacing: 2px }\n"
           ":lang(en) .t { letter-spacing: .1em }\n"
           ":lang(ar) .t { letter-spacing: .1em }")
    assert ids("a.css", css) == ["css-letter-spacing"]


def test_test_files_are_skipped_when_walking(tmp_path):
    (tmp_path / "a.test.js").write_text("const c = 'text-align: left'")
    (tmp_path / "b.spec.ts").write_text("const c = 'text-align: left'")
    (tmp_path / "__tests__").mkdir()
    (tmp_path / "__tests__" / "c.js").write_text("const c = 'text-align: left'")
    findings, count = rtl_check.scan_paths([str(tmp_path)])
    assert (findings, count) == ([], 0)


def test_generated_rule_files_match_the_skill():
    import subprocess
    build = os.path.join(HERE, "..", "tools", "build.py")
    done = subprocess.run([sys.executable, build, "--check"],
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stdout
