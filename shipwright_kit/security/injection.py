"""Shared prompt-injection detector for attacker-influenced strings.

Single source of truth for the regex pattern set + detection engine used by
every consumer (vex, sift). A bypass fixed here propagates to all of them.

Import-light: stdlib only (no pydantic), so ``import
shipwright_kit.security.injection`` stays dependency-free. The finding type is a
frozen dataclass; consumers serialize via ``dataclasses.asdict`` at their JSON
boundary.

Operates on plain string values. Tool-specific I/O — vex's ``sanitize`` (str ->
marker) and sift's ``redact_alert`` (Alert -> Alert) — stays in each tool.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum

__all__ = [
    "INJECTION_PATTERNS_VERSION",
    "InjectionFinding",
    "PromptInjectionDetector",
    "SeverityLevel",
    "scan",
]

# Bump when the pattern SET changes (added/removed/retuned pattern). Lets
# consumers assert they are matching against a known engine version, mirroring
# the EVAL_SCHEMA_VERSION / OUTPUT_SCHEMA_VERSION contract discipline (G10).
INJECTION_PATTERNS_VERSION = 2

# Cyrillic/Greek look-alikes folded to Latin before matching (written as
# escapes — never paste the raw characters). The mapping targets only letters
# that are visually indistinguishable from a Latin letter.
_CONFUSABLES = str.maketrans(
    {
        "\u0430": "a",
        "\u0435": "e",
        "\u0456": "i",
        "\u043e": "o",
        "\u0440": "p",
        "\u0441": "c",
        "\u0443": "y",
        "\u0445": "x",
        "\u0455": "s",
        "\u0458": "j",
        "\u0501": "d",
        "\u04cf": "l",
        "\u03bf": "o",
        "\u03b1": "a",
        "\u03b5": "e",
        "\u03b9": "i",
        "\u03bd": "v",
        "\u03c4": "t",
        "\u03ba": "k",
        "\u03c1": "p",
        "\u0410": "A",
        "\u0415": "E",
        "\u0406": "I",
        "\u041e": "O",
        "\u0420": "P",
        "\u0421": "C",
        "\u0425": "X",
        "\u039f": "O",
        "\u0391": "A",
        "\u0395": "E",
        "\u0399": "I",
        "\u039a": "K",
        "\u03a1": "P",
        "\u03a4": "T",
    }
)


def _fold(value: str) -> str:
    """NFKC, drop invisible format (Cf) characters, fold confusable letters."""
    text = unicodedata.normalize("NFKC", value)
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    return text.translate(_CONFUSABLES)


class SeverityLevel(str, Enum):
    """Severity of an injection finding."""

    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class InjectionFinding:
    """A detected injection pattern in a string value.

    Attribute names match the prior pydantic models in vex/sift so consumer
    call sites and ``.field`` / ``.pattern_type`` / ``.severity`` access are
    unchanged.
    """

    field: str
    pattern_type: str
    severity: SeverityLevel
    redaction: str
    value_preview: str | None = None


class PromptInjectionDetector:
    """Detects prompt-injection patterns in plain string values.

    Args:
        case_insensitive: case-insensitive matching when True (default).
        whitelist_patterns: regex strings for operator-defined known-safe
            text. A whitelist match exempts only the matched text; content
            outside it is still scanned. Matching runs on the normalized,
            confusable-folded string. Known limit: a whitelisted token placed
            inside an attack word splits it once the span is removed, which
            requires knowing the operator's whitelist.
    """

    def __init__(
        self,
        case_insensitive: bool = True,
        whitelist_patterns: list[str] | None = None,
    ) -> None:
        self.case_insensitive = case_insensitive
        flags = re.IGNORECASE if case_insensitive else 0
        self._whitelist: list[re.Pattern[str]] = [re.compile(p, flags) for p in (whitelist_patterns or [])]
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        flags = re.IGNORECASE if self.case_insensitive else 0

        # Pattern 1: "ignore previous instructions" variants.
        self.pattern_ignore_instructions = re.compile(
            r"(ignore|disregard|forget|dismiss|bypass|override)[\s\S]{0,40}?"
            r"(previous|prior|earlier|above|preceding)[\s\S]{0,40}?"
            r"(instruction|directive|prompt|command|context|system)",
            flags | re.DOTALL,
        )

        # Pattern 2: LLM-redirection via "instead" / "rather than".
        self.pattern_instead_output = re.compile(
            r"(?:"
            r"(output|respond|return|generate|create|print|write)\s+instead"
            r"|instead[\s,;.]+(?:of\s+)?(output|respond|return|generate|create|print|write)"
            r"|rather\s+than\s+(?:summariz|analyz|triag|the\s+above)"
            r")",
            flags,
        )

        # Pattern 3: JSON escape sequences.
        self.pattern_json_escapes = re.compile(
            r'\\(?:["\\/bfnrtu]|u[0-9a-fA-F]{4})',
            flags,
        )

        # Pattern 4: Base64 / hex encoded payloads (thresholds tuned to exclude
        # common security terms like "Exfiltration"/"Configuration").
        self.pattern_base64_hex = re.compile(
            r"(?:"
            r"(?=[A-Za-z0-9+/]*[+/])[A-Za-z0-9+/]{12,}"
            r"|[A-Za-z0-9+/]{4,}=="
            r"|[A-Za-z0-9+/]{8,}="
            r"|(?:[0-9a-fA-F]{2}){10,}"
            r"|[A-Za-z0-9]{20,}"
            r")",
            flags,
        )

        # Pattern 5: Shell command injection.
        self.pattern_shell_commands = re.compile(
            r"(?:\$\([^)]*\)|`[^`]*`|\$\w+)",
            flags,
        )

        # Pattern 6: Jailbreak / role override — role verb + (restriction
        # adjective bound to an AI-context noun | known idiom). Bare markers are
        # rejected to avoid FP on real SOC text.
        self.pattern_jailbreak = re.compile(
            r"(?:act as|you are now|pretend to be|roleplay as|behave as)[\s\S]{0,40}?"
            r"(?:"
            r"(?:unrestricted|unfiltered|jailbroken|uncensored|unaligned)\s+"
            r"(?:assistant|ai|model|chatbot|llm|gpt|bot|agent|persona|mode|version)"
            r"|jailbroken"
            r"|dan\b"
            r"|do\s+anything\s+now"
            r")",
            flags | re.DOTALL,
        )

        # Pattern 7: System-prompt exfiltration — exfil verb + high-signal prompt
        # noun only (system prompt / your [system] prompt / system instructions).
        self.pattern_prompt_exfil = re.compile(
            r"(?:reveal|print|show|output|repeat|leak|disclose|dump|expose|contents?\s+of)"
            r"[\s\S]{0,40}?"
            r"(?:system\s*prompt|system\s+instructions?"
            r"|your\s+(?:system\s+)?prompt|your\s+system\s+instructions?)",
            flags | re.DOTALL,
        )

    def detect(
        self,
        value: str,
        field_name: str = "",
        *,
        is_ioc_field: bool = False,
    ) -> list[InjectionFinding]:
        """Scan a single string value. Empty list means clean."""
        if not isinstance(value, str):
            return []

        normalized = _fold(value)

        if self._whitelist:
            for p in self._whitelist:
                normalized = p.sub(lambda m: " " if m.end() > m.start() else "", normalized)
            if not normalized.strip():
                return []

        findings: list[InjectionFinding] = []
        preview = self._truncate(value)

        def add(pattern_type: str, severity: SeverityLevel, redaction: str) -> None:
            findings.append(
                InjectionFinding(
                    field=field_name,
                    pattern_type=pattern_type,
                    severity=severity,
                    redaction=redaction,
                    value_preview=preview,
                )
            )

        # if (not elif) so all patterns in a value are reported.
        if self.pattern_ignore_instructions.search(normalized):
            add("instruction_override", SeverityLevel.CRITICAL, "[REDACTED: instruction override attempt]")
        if self.pattern_instead_output.search(normalized):
            add("output_manipulation", SeverityLevel.CRITICAL, "[REDACTED: output manipulation attempt]")
        if self.pattern_json_escapes.search(normalized):
            add("json_escape_sequence", SeverityLevel.WARNING, "[REDACTED: JSON escape sequences]")
        if not is_ioc_field and self.pattern_base64_hex.search(normalized):
            add("encoded_payload", SeverityLevel.WARNING, "[REDACTED: encoded payload]")
        if self.pattern_shell_commands.search(normalized):
            add("shell_injection", SeverityLevel.CRITICAL, "[REDACTED: shell command attempt]")
        if self.pattern_jailbreak.search(normalized):
            add("jailbreak", SeverityLevel.CRITICAL, "[REDACTED: jailbreak / role-override attempt]")
        if self.pattern_prompt_exfil.search(normalized):
            add("prompt_exfiltration", SeverityLevel.CRITICAL, "[REDACTED: system-prompt exfiltration attempt]")

        return findings

    @staticmethod
    def _truncate(value: str, max_len: int = 80) -> str:
        if len(value) <= max_len:
            return value
        return value[:max_len] + "..."


def scan(value: str) -> list[InjectionFinding]:
    """Scan a single string value with a default detector."""
    return PromptInjectionDetector().detect(value)
