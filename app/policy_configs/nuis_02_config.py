"""
NUIS-02 Policy Configuration

Policy:
Low-substance, placeholder, gibberish, or AI-generated filler content
that does not provide meaningful project information.

Unique trigger focus:
Detects project submissions with insufficient substantive content —
placeholder text (lorem ipsum, test content), gibberish, or AI-generated
filler that has been submitted in place of genuine project information.
Distinct from NUIS-01 (spam/solicitation) and NUIS-03 (off-topic); this
policy targets content that is meaningless or incomplete rather than
deliberately disruptive.

Severity: MEDIUM — low-substance content requires the submitter to
provide genuine project information before approval.
"""

NUIS_02_CONFIG = {
    "policy_code": "NUIS-02",

    "policy_name": (
        "Low-substance, placeholder, gibberish, or AI-generated filler content"
    ),

    "policy_category": "Nuisance",

    "severity": "MEDIUM",

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
        "prompt_id": "NUIS_02_SUBSTANCE_ANALYSIS",
        "max_tokens": 3500
    },

    "claim_types": [
        "placeholder_text",
        "lorem_ipsum_content",
        "test_submission_content",
        "gibberish_or_nonsense",
        "ai_filler_content",
        "insufficient_substance",
        "empty_template_submission"
    ],

    # M03 absolute / authority scans
    "absolute_claim_terms": [],

    "authority_terms": [],

    "evidence_indicators": [],

    # M03 EXTRA_TERM_LIST_KEYS — auto-scanned by m03_rule_signals.py
    "placeholder_terms": [
        "lorem ipsum", "dolor sit amet", "consectetur adipiscing",
        "placeholder", "insert text here", "add description here",
        "coming soon", "to be updated", "tbd", "tba", "n/a",
        "test project", "test submission", "test entry",
        "this is a test", "testing 123", "1 2 3",
        "sample project", "sample description", "sample text",
        "example project", "example description",
        "fill in later", "to be completed", "to be written",
        "draft", "draft only", "work in progress",
        "copy and paste", "todo", "to do",
        "aaaa", "aaabbb", "asdf", "qwerty", "xxxxx",
        "click to edit", "edit this text"
    ],

    "decision_rules": {
        "default": {
            "matched_flag": False,
            "severity": "LOW",
            "suggested_action": "PASS",
            "manual_review_required": False,
            "confidence_score": 0.85,
            "reason_template": (
                "No placeholder, gibberish, or low-substance content was detected. "
                "The submission appears to contain genuine project information."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "placeholder_text",
                "lorem_ipsum_content",
                "test_submission_content",
                "gibberish_or_nonsense",
                "empty_template_submission"
            ],
            "medium_risk_claim_types": [
                "ai_filler_content",
                "insufficient_substance"
            ]
        },

        "rules": [

            # ── Tier-direct rules (fire before claim-count rules) ──────────────────
            # When the LLM returns recommended_tier, use it directly so M16 does not
            # fall through to raw claim-count rules that are miscalibrated for NUIS.
            {
                "rule_id": "NUIS02-RPASS",
                "description": "LLM recommends PASS tier — no actionable violation.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "PASS"},
                "result": {
                    "matched_flag": False, "severity": "LOW", "suggested_action": "PASS",
                    "manual_review_required": False, "confidence_score": 0.90,
                    "reason_template": ("Submission has sufficient substantive content; specific, meaningful project details are present.")
                }
            },

            {
                "rule_id": "NUIS02-RQRN",
                "description": "LLM recommends QUARANTINE tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "QUARANTINE"},
                "result": {
                    "matched_flag": True, "severity": "CRITICAL", "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Anti-Abuse / Platform Integrity", "manual_review_required": True,
                    "confidence_score": 0.93, "reason_template": ("Meaningless content — random keyboard mashing, corrupted encoding, or incoherent word soup with no real information. Reject and quarantine.")
                }
            },

            {
                "rule_id": "NUIS02-RESC",
                "description": "LLM recommends ESCALATE tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "ESCALATE"},
                "result": {
                    "matched_flag": True, "severity": "HIGH", "suggested_action": "ESCALATE",
                    "escalate_to": "Anti-Abuse / Compliance", "manual_review_required": True,
                    "confidence_score": 0.90, "reason_template": ("Placeholder/dummy content — lorem ipsum, unfilled template brackets, 'test test', or TBD placeholders. Escalate to Anti-Abuse.")
                }
            },

            {
                "rule_id": "NUIS02-RNR",
                "description": "LLM recommends NEEDS_REVIEW tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "NEEDS_REVIEW"},
                "result": {
                    "matched_flag": True, "severity": "MEDIUM", "suggested_action": "REVIEW",
                    "manual_review_required": True, "confidence_score": 0.82,
                    "reason_template": ("Low-substance content — vague jargon, unfinished draft notes, or extremely brief vague fields. Flag for moderator review.")
                }
            },

            {
                "rule_id": "NUIS02-R0",
                "description": "LLM substance analysis failed; cannot safely pass.",
                "conditions": {"llm_analysis_failed": True},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.40,
                    "reason_template": (
                        "LLM content-substance analysis failed. The policy cannot be safely passed "
                        "because placeholder and filler detection was incomplete."
                    )
                }
            },
            {
                "rule_id": "NUIS02-R1",
                "description": "Clear placeholder or gibberish content detected — reject.",
                "conditions": {"min_high_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REJECT_RECOMMENDED",
                    "manual_review_required": True,
                    "confidence_score": 0.92,
                    "reason_template": (
                        "Placeholder text, lorem ipsum, test submission, or gibberish content was "
                        "detected. The submission does not contain genuine project information and "
                        "must be rejected until real content is provided."
                    )
                }
            },
            {
                "rule_id": "NUIS02-R2",
                "description": "Insufficient substance or AI filler detected — request amendment.",
                "conditions": {"min_medium_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REQUEST_AMENDMENT",
                    "manual_review_required": True,
                    "confidence_score": 0.80,
                    "reason_template": (
                        "Content with insufficient substance or possible AI-generated filler was "
                        "detected. The submitter should revise to provide meaningful project "
                        "information covering goals, activities, and expected outcomes."
                    )
                }
            },
            {
                "rule_id": "NUIS02-R3",
                "description": "Low-confidence low-substance signal — review recommended.",
                "conditions": {"min_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "LOW",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.62,
                    "reason_template": (
                        "Content with potentially low informational value was detected. "
                        "Moderator review is recommended to assess whether the submission "
                        "provides adequate project information."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "minimum_content_length_standard_not_defined",
                "condition": {"always": True},
                "message": (
                    "A minimum acceptable content length or substance threshold has not been "
                    "formally defined for SWA projects. Moderation applies best-judgement standards."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "ai_detection_not_conclusive",
                "condition": {"always": True},
                "message": (
                    "AI-generated content detection is probabilistic and cannot be conclusively "
                    "determined. Human review is required before taking action on AI-filler signals."
                ),
                "force_partial_evaluation": True
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
        "PASS", "REVIEW", "REQUEST_AMENDMENT", "REJECT_RECOMMENDED"
    ],

    "scope_notes": {
        "current_scope": "Project-only moderation for current POC.",
        "what_this_policy_does": [
            "Detects placeholder text, lorem ipsum, test submissions, and gibberish content.",
            "Identifies AI-generated filler that lacks genuine project information.",
            "Classifies low-substance content by type and generates amendment-request reason notes.",
            "Flags submissions that do not meet minimum content quality standards."
        ],
        "what_this_policy_does_not_do": [
            "Does not apply a formally defined minimum word count or content standard.",
            "Does not conclusively determine whether content is AI-generated.",
            "Does not compare content depth against other approved submissions.",
            "Does not make final content-quality determinations."
        ]
    }
}
