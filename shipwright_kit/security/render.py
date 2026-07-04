"""Terminal-safe rendering of untrusted (LLM-sourced) text.

Neutralizes the two ways attacker-influenced text — chiefly an LLM summary or
explanation a model can be steered to emit — manipulates a Rich-rendered
terminal when a consumer (vex, sift, barb) prints it:

* Rich console markup (``[red]``, ``[link=...]``) — escaped so it renders as
  literal text, following Rich's own ``\\[`` escape convention.
* ANSI / OSC escape sequences and other C0/C1 control characters — stripped, so
  a model cannot move the cursor, recolor, set the window title, or emit OSC-8
  hyperlinks. TAB (``\\t``) and newline (``\\n``) are preserved.

Render-sink half of the fleet's LLM-output hardening (OWASP LLM05, Improper
Output Handling); the prompt-input half lives in
:mod:`shipwright_kit.security.injection`. Apply ``safe_render`` to the
LLM-sourced field ONLY — trusted app-generated markup (e.g. a severity-color
span) must never be routed through it.

Import-light: stdlib only (``re``), no Rich import — mirrors the import-light
invariant of :mod:`shipwright_kit.security.injection`.
"""

from __future__ import annotations

import re

__all__ = ["SAFE_RENDER_VERSION", "safe_render"]

# Bump when the neutralization rule set changes (added/removed/retuned rule).
SAFE_RENDER_VERSION = 1

# CSI (ESC [ ... final byte), OSC (ESC ] ... BEL | ESC \), and other two-char
# ESC sequences.
_ANSI_RE = re.compile(
    r"\x1b\[[0-?]*[ -/]*[@-~]"  # CSI
    r"|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"  # OSC (terminated by BEL or ST)
    r"|\x1b[@-Z\\-_]"  # other two-char ESC sequences
)
# C0/C1 control chars except TAB (\x09) and LF (\x0a).
_CTRL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")


def safe_render(text: str, *, escape_markup: bool = True) -> str:
    """Return ``text`` safe to print at a terminal render sink.

    Always removes ANSI/OSC escape sequences and other control characters (TAB
    and newline kept). When ``escape_markup`` is True (default), ALSO escapes
    Rich console markup so ``[red]`` shows literally — for text printed into a
    Rich-markup-enabled sink (``console.print`` / ``Panel``). Set
    ``escape_markup=False`` for a plain builtin-``print`` sink, where there is no
    Rich to interpret markup and escaping ``[`` would only add spurious
    backslashes (the control/ANSI strip still applies). Use on LLM-sourced /
    attacker-influenceable text at the render site.
    """
    text = _ANSI_RE.sub("", text)
    text = _CTRL_RE.sub("", text)
    if escape_markup:
        # Escape Rich markup. Double backslashes first so an attacker-supplied
        # backslash cannot combine with the one we insert (Rich collapses \\ ->
        # \ and only parses the opening '['), then escape '['.
        text = text.replace("\\", "\\\\").replace("[", "\\[")
    return text
