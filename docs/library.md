# Library API reference

The library is import-light: `import shipwright_kit` pulls in no `rich` or
`pyfiglet`; heavy deps load lazily only when you render. Three public modules.

Install: `uv pip install "git+https://github.com/duathron/shipwright@main"` →
`import shipwright_kit`. (Distribution name is `shipwright-kit`; see the README.)

---

## `shipwright_kit.design` — severity tiers + accessible output

One generic severity scale that tools map their own verdicts onto, plus glyphs, a
colour palette, and an accessibility-aware console/output layer.

### `Severity`

An `IntEnum` with five tiers, ordered low → high:

```python
from shipwright_kit.design import Severity
[(s.name, int(s)) for s in Severity]
# [('OK', 0), ('INFO', 1), ('NOTICE', 2), ('WARN', 3), ('CRITICAL', 4)]
```

### `tier_label(tier)` and `glyph(tier, *, ascii_only=False)`

`tier_label` returns a glyph + name; `glyph` returns just the symbol. Pass
`ascii_only=True` for environments without Unicode.

```python
from shipwright_kit.design import Severity, tier_label, glyph
tier_label(Severity.CRITICAL)        # '✗ CRITICAL'
glyph(Severity.WARN)                  # '⚠'
glyph(Severity.WARN, ascii_only=True) # '!'
```

### `TierMappable` — map a tool's own enum onto `Severity`

Subclass and implement `base_tier()` to overlay a domain enum (e.g. a phishing
verdict) onto the generic scale, so shared rendering/eval code works across tools.

```python
from shipwright_kit.design import Severity, TierMappable

class Verdict(TierMappable):
    def __init__(self, sev): self._sev = sev
    def base_tier(self) -> Severity: return self._sev

Verdict(Severity.CRITICAL).base_tier()  # <Severity.CRITICAL: 4>
```

### Rendering

`render(obj, fmt="console", *, ascii_only=False)` renders a `Renderable` in one of
`VALID_FORMATS`. The console layer honours `NO_COLOR`, pipe detection, and a Unicode
probe; `supports_color()` / `supports_unicode()` expose those checks. `palette`
provides default and colour-blind-safe themes (`DefaultTheme`, `ColorblindTheme`).

---

## `shipwright_kit.eval` — detection-quality eval harness

Score a classifier against a labeled corpus and gate on precision/recall. barb and
sift both build their CI detection gates on this.

### `Sample` and `load_corpus`

```python
from shipwright_kit.eval import Sample, load_corpus
Sample("phish-login", "phishing")   # Sample(input=..., label=...)
# load_corpus(path, *, input_col="input", label_col="label") -> list[Sample]
# Reads CSV/JSON, tolerates blank lines and `#` comments.
```

### `evaluate(...)` — two-binarizer

```python
evaluate(
    predict_fn,            # Callable[[str], str]   — your classifier
    corpus,                # list[Sample]
    *,
    positive_pred,         # Callable[[str], bool]  — is a PREDICTION positive?
    positive_expected=None # Callable[[str], bool]  — is a LABEL positive? (defaults to positive_pred)
) -> EvalResult
```

Separate binarizers exist because a tool's prediction space (e.g. a verdict enum)
often differs from its label space (e.g. `phishing`/`benign`). Predictions that raise
are counted, not crashed (`EvalResult.errors`).

```python
from shipwright_kit.eval import Sample, evaluate
corpus = [Sample("phish-login", "phishing"), Sample("example.com", "benign")]
r = evaluate(lambda t: "phishing" if "phish" in t else "benign", corpus,
             positive_pred=lambda p: p == "phishing",
             positive_expected=lambda label: label == "phishing")
(r.tp, r.fp, r.tn, r.fn, r.precision, r.recall)   # (1, 0, 1, 0, 1.0, 1.0)
```

### `EvalResult`

A dataclass: `tp`, `fp`, `tn`, `fn`, `errors`, plus computed `precision`, `recall`,
`f1`, `accuracy`, `false_positive_rate` (each `0.0` on a zero denominator).

### `gate(result, *, min_precision, min_recall)`

Raises `EvalGateError` if a floor is unmet (use it as a CI gate). Includes a
zero-recall floor.

```python
from shipwright_kit.eval import gate, EvalGateError
gate(r, min_precision=1.0, min_recall=0.9)   # no raise on the result above
```

---

## `shipwright_kit.security` — security pack

Ships with the base install and registers via the `shipwright_kit.packs` entry point
(it is **not** a `pip install shipwright[...]` extra).

### `is_alert(tier, *, alert_at=NOTICE)`

Binarises a `Severity` into alert / not-alert. `alert_at` is keyword-only and
defaults to `NOTICE` — i.e. `NOTICE` and above alert.

```python
from shipwright_kit.design import Severity
from shipwright_kit.security.eval import is_alert, SECURITY_MIN_PRECISION, SECURITY_MIN_RECALL

is_alert(Severity.NOTICE)                       # True
is_alert(Severity.INFO)                         # False
is_alert(Severity.INFO, alert_at=Severity.INFO) # True
SECURITY_MIN_PRECISION, SECURITY_MIN_RECALL     # (1.0, 0.7)
```

`SECURITY_MIN_PRECISION = 1.0` / `SECURITY_MIN_RECALL = 0.7` are the security
domain's eval floors (no false positives; recall ≥ 0.70) — feed them to `gate(...)`.

### Labels theme

`shipwright_kit.security.theme` maps `Severity` onto security labels (CLEAN → LOW →
SUSPICIOUS → HIGH → MALICIOUS) and registers a `SecurityTheme` for rendering.
