"""
app/outcome_vocabulary.py

Single source of truth for translating the pipeline's INTERNAL canonical
action tokens into the EXTERNAL expected-outcome vocabulary that the test
suite is scored against.

Why this exists
---------------
Accuracy on the synthetic test suite is measured by EXACT-TOKEN match between
the pipeline's persisted action and the `SWA_ModerationTestSuite.ExpectedOutcome`
column. The pipeline and the test data were authored with two different
vocabularies, so semantically-correct decisions were still being scored as
"wrong flags":

    pipeline (internal)            test data (ExpectedOutcome)
    --------------------           ---------------------------
    PASS                           PASS                ✓ same
    REVIEW                         NEEDS_REVIEW        ✗ mismatch  (CONFIRMED)
    ESCALATE                       ESCALATE            ✓ same
    LAW_ENFORCEMENT                LAW_ENFORCEMENT     ✓ same
    REJECT_RECOMMENDED             ???                 ⚠ VERIFY
    REQUEST_AMENDMENT              ???                 ⚠ VERIFY
    (n/a — MAL only)               QUARANTINE          (MAL policies)

CONFIRMED tokens come from ui/index.html, which renders the live ExpectedOutcome
column: it has an explicit `expectedOutcome === "NEEDS_REVIEW"` branch and lists
"QUARANTINE"/"LAW_ENFORCEMENT" — and has NO branch for the literal "REVIEW".

Keep internal decision logic (M16 rules, M99 ACTION_PRIORITY) on the canonical
tokens. This mapping is applied ONLY at the external output boundary
(DB persistence of the compared action), so aggregation/priority logic is
unaffected.

To finish alignment
-------------------
Open the project list in the UI (or `SELECT DISTINCT ExpectedOutcome FROM
SWA_ModerationTestSuite`) and set the right-hand side of the two ⚠ entries below
to the exact strings used by the test data (e.g. "REJECT"). Identity mappings
are safe no-ops, so leaving a value unchanged never makes a correct case wrong.
"""

# Internal canonical action token  ->  external expected-outcome token.
#
# CONFIRMED from the live test suite (SELECT DISTINCT Testing_ExpectedFlag FROM
# dbo.SWA_Projects): the four scored tiers are exactly
#     Pass | Needs-Review | Escalate | Quarantine   (Title-Case, hyphenated).
# Accuracy is exact-token match against Testing_ExpectedFlag, so the pipeline
# must emit these exact strings. Mapping the internal canonical actions:
#     PASS               -> Pass
#     REVIEW             -> Needs-Review   (borderline / human review)
#     REQUEST_AMENDMENT  -> Needs-Review   (remediation request == human review tier)
#     ESCALATE           -> Escalate       (severe, specialist handling)
#     REJECT_RECOMMENDED -> Quarantine     (clear-cut, auto-isolate)
#     LAW_ENFORCEMENT    -> Quarantine     (most severe block)
EXTERNAL_ACTION_VOCABULARY = {
    "PASS":               "Pass",
    "REVIEW":             "Needs-Review",
    "REQUEST_AMENDMENT":  "Needs-Review",
    "ESCALATE":           "Escalate",
    "REJECT_RECOMMENDED": "Quarantine",
    "LAW_ENFORCEMENT":    "Quarantine",
}


def to_external_action(action):
    """
    Translate a canonical pipeline action into the external expected-outcome
    vocabulary used for accuracy scoring. Unknown / already-external tokens are
    returned unchanged.
    """
    if action is None:
        return None
    return EXTERNAL_ACTION_VOCABULARY.get(action, action)
