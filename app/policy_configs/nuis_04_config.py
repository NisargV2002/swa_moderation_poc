"""
NUIS-04 Policy Configuration

Policy:
Formatting abuse — ALL CAPS text, emoji floods, excessive punctuation bursts,
or aggressive visual-noise formatting that degrades content quality.

Unique trigger focus:
Detects content that uses aggressive formatting as a substitute for substance —
excessive capitalisation, repeated punctuation (!!!!, ???), emoji floods, or
other visual-noise patterns that make content harder to evaluate. This is a
non-blocking, advisory-only policy. It does not reject submissions; it signals
to moderators that formatting improvements are recommended.

Severity: LOW — advisory only, no escalation.
"""

NUIS_04_CONFIG = {
    "policy_code": "NUIS-04",

    "policy_name": (
        "Formatting abuse — ALL CAPS, emoji floods, or excessive punctuation"
    ),

    "policy_category": "Nuisance",

    "severity": "LOW",

    "applies_to": ["Project"],

    "module_sequence": [
        "M01", "M02", "M03", "M05", "M07", "M08", "M16", "M17"
    ],

    "fields_to_scan": [
        "ProjectName",
        "ProjectDescription",
        "ProjectGoal",
        "ResourceDescription",
        "Message"
    ],

    "context_fields": [
        "ProjectSponsorFirstName",
        "ProjectSponsorLastName",
        "CountryName",
        "ProjectStartDate",
        "ProjectEndDate",
        "ProjectStatus",
        "IsPublished",
        "IsVirtual",
        "LanguageCode",
        "ExpectedPolicyOutcome",
        "ExpectedNotes"
    ],

    "llm_task": {
        "enabled": True,
        "prompt_id": "NUIS_04_FORMATTING_ANALYSIS",
        "max_tokens": 2000
    },

    "claim_types": [
        "excessive_capitalisation",
        "emoji_flood",
        "repeated_punctuation_burst",
        "aggressive_visual_noise",
        "all_caps_abuse"
    ],

    # M03 absolute / authority scans
    "absolute_claim_terms": [],

    "authority_terms": [],

    "evidence_indicators": [],

    # M03 EXTRA_TERM_LIST_KEYS — auto-scanned by m03_rule_signals.py
    # Formatting-abuse indicators detectable through text patterns
    "formatting_abuse_terms": [
        "!!!", "???", "!?!?", "!!!!", "?????",
        "...........", "------",
        "###", "***", "===",
        "click!!!", "urgent!!!", "important!!!"
    ],

    "decision_rules": {
        "default": {
            "matched_flag": False,
            "severity": "LOW",
            "suggested_action": "PASS",
            "manual_review_required": False,
            "confidence_score": 0.90,
            "reason_template": (
                "No significant formatting abuse was detected in the submitted project text."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "all_caps_abuse",
                "emoji_flood"
            ],
            "medium_risk_claim_types": [
                "excessive_capitalisation",
                "repeated_punctuation_burst",
                "aggressive_visual_noise"
            ]
        },

        "rules": [

            # ── Tier-direct rules (fire before claim-count rules) ──────────────────
            # When the LLM returns recommended_tier, use it directly so M16 does not
            # fall through to raw claim-count rules that are miscalibrated for NUIS.
            {
                "rule_id": "NUIS04-RPASS",
                "description": "LLM recommends PASS tier — no actionable violation.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "PASS"},
                "result": {
                    "matched_flag": False, "severity": "LOW", "suggested_action": "PASS",
                    "manual_review_required": False, "confidence_score": 0.90,
                    "reason_template": ("Formatting is clean and readable; acronyms, structured lists, and occasional emphasis are acceptable.")
                }
            },

            {
                "rule_id": "NUIS04-RQRN",
                "description": "LLM recommends QUARANTINE tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "QUARANTINE"},
                "result": {
                    "matched_flag": True, "severity": "CRITICAL", "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Anti-Abuse / Platform Integrity", "manual_review_required": True,
                    "confidence_score": 0.93, "reason_template": ("Malicious formatting injection — zalgo/combining-character overflow, RTL-override obfuscation, or newline-flood designed to break UI/DB. Reject and quarantine.")
                }
            },

            {
                "rule_id": "NUIS04-RESC",
                "description": "LLM recommends ESCALATE tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "ESCALATE"},
                "result": {
                    "matched_flag": True, "severity": "HIGH", "suggested_action": "ESCALATE",
                    "escalate_to": "Anti-Abuse / Compliance", "manual_review_required": True,
                    "confidence_score": 0.90, "reason_template": ("Severe formatting abuse — all fields in ALL CAPS, punctuation-burst flooding, emoji blocks, or decoration-symbol/character spacing that destroys readability. Escalate to Advisory.")
                }
            },

            {
                "rule_id": "NUIS04-RNR",
                "description": "LLM recommends NEEDS_REVIEW tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "NEEDS_REVIEW"},
                "result": {
                    "matched_flag": True, "severity": "MEDIUM", "suggested_action": "REVIEW",
                    "manual_review_required": True, "confidence_score": 0.82,
                    "reason_template": ("Minor formatting issues — an ALL-CAPS field, excessive exclamation marks, or high emoji density. Flag for advisory review.")
                }
            },

            {
                "rule_id": "NUIS04-R0",
                "description": "LLM formatting analysis failed — advisory pass, flag for awareness.",
                "conditions": {"llm_analysis_failed": True},
                "result": {
                    "matched_flag": False,
                    "severity": "LOW",
                    "suggested_action": "PASS",
                    "manual_review_required": False,
                    "confidence_score": 0.80,
                    "reason_template": (
                        "LLM formatting analysis failed, but this is a non-blocking advisory policy. "
                        "The submission is passed; formatting review may be beneficial."
                    )
                }
            },
            {
                "rule_id": "NUIS04-R1",
                "description": "Clear formatting abuse detected — advisory review suggested.",
                "conditions": {"min_high_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "LOW",
                    "suggested_action": "REVIEW",
                    "manual_review_required": False,
                    "confidence_score": 0.80,
                    "reason_template": (
                        "Formatting abuse was detected — ALL CAPS text or emoji flooding impairs "
                        "readability. This is an advisory signal only. No escalation required; "
                        "the submitter may be asked to improve formatting."
                    )
                }
            },
            {
                "rule_id": "NUIS04-R2",
                "description": "Moderate formatting abuse — advisory note.",
                "conditions": {"min_medium_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "LOW",
                    "suggested_action": "REVIEW",
                    "manual_review_required": False,
                    "confidence_score": 0.72,
                    "reason_template": (
                        "Excessive punctuation, capitalisation, or aggressive formatting was detected. "
                        "Advisory only — the submitter may be encouraged to revise formatting for clarity."
                    )
                }
            },
            {
                "rule_id": "NUIS04-R3",
                "description": "Minor formatting signal — pass with advisory note.",
                "conditions": {"min_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "LOW",
                    "suggested_action": "REVIEW",
                    "manual_review_required": False,
                    "confidence_score": 0.65,
                    "reason_template": (
                        "Minor formatting irregularities were detected. Advisory only — no action "
                        "required unless combined with other policy violations."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "formatting_detection_limited_by_text_normalisation",
                "condition": {"always": True},
                "message": (
                    "Text normalisation in M02 may reduce or remove some formatting signals "
                    "(e.g., casing). Formatting detection is approximate in the current pipeline."
                ),
                "force_partial_evaluation": False
            }
        ]
    },

    "expected_output_schema": {
        "required_top_level_fields": [
            "policy_code", "policy_name", "matched_flag",
            "evaluation_status", "severity", "suggested_action",
            "manual_review_required", "moderator_reason_note",
            "confidence_score", "details", "result_json"
        ],
        "required_detail_fields": [
            "claim_count", "evidence_issue_count", "claims",
            "evidence_issues", "rule_signals", "entities",
            "language_info", "input_coverage",
            "dependency_gaps", "risk_classification"
        ]
    },

    "allowed_outcomes": [
        "PASS", "REVIEW"
    ],

    "scope_notes": {
        "current_scope": "Project-only moderation for current POC.",
        "what_this_policy_does": [
            "Detects excessive capitalisation, emoji floods, and punctuation bursts.",
            "Generates low-severity advisory signals for formatting quality issues.",
            "This is non-blocking — no submission is rejected on formatting grounds alone."
        ],
        "what_this_policy_does_not_do": [
            "Does not reject submissions based on formatting alone.",
            "Does not precisely measure capitalisation ratios (requires preprocessing extension).",
            "Does not count emoji character density precisely.",
            "Does not escalate formatting issues to reviewers."
        ]
    }
}
