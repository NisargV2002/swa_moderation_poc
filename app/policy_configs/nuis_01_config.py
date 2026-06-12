"""
NUIS-01 Policy Configuration

Policy:
Spam, repetition, keyword stuffing, or mass solicitation content.

Unique trigger focus:
Detects content that is designed to game visibility through excessive keyword
repetition, mass advertising solicitation, or spam-like patterns rather than
delivering genuine project information. Distinct from MAL-04 (coordinated
abuse across accounts) and NUIS-02 (low substance/gibberish); this policy
targets deliberate gaming of search or discovery through spam tactics within
a single submission.

Severity: MEDIUM — spam content typically requires rewrite rather than
rejection, unless combined with other violations.
"""

NUIS_01_CONFIG = {
    "policy_code": "NUIS-01",

    "policy_name": (
        "Spam, repetition, keyword stuffing, or mass solicitation content"
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
        "prompt_id": "NUIS_01_SPAM_ANALYSIS",
        "max_tokens": 3500
    },

    "claim_types": [
        "keyword_stuffing",
        "repetitive_content",
        "mass_solicitation",
        "spam_advertising",
        "gaming_search_visibility",
        "unrelated_keyword_injection"
    ],

    # M03 absolute / authority scans
    "absolute_claim_terms": [],

    "authority_terms": [],

    "evidence_indicators": [],

    # M03 EXTRA_TERM_LIST_KEYS — auto-scanned by m03_rule_signals.py
    "spam_terms": [
        "buy now", "order today", "shop online", "best prices",
        "cheap", "cheapest", "lowest price", "price guarantee",
        "free delivery", "fast shipping", "same day delivery",
        "100% satisfaction", "money back", "no risk",
        "click here", "visit now", "go to", "check out",
        "limited time", "offer ends", "while stocks last",
        "seo", "search engine", "google ranking", "page rank",
        "keyword", "keywords", "key words", "meta tags",
        "backlink", "link building", "traffic", "boost traffic",
        "get more visitors", "increase visits",
        "contact us", "call us", "email us", "reach us",
        "we offer", "we provide", "we supply", "we deliver",
        "all services", "all products", "full range",
        "subscribe", "sign up", "join now", "register free"
    ],

    "decision_rules": {
        "default": {
            "matched_flag": False,
            "severity": "LOW",
            "suggested_action": "PASS",
            "manual_review_required": False,
            "confidence_score": 0.85,
            "reason_template": (
                "No spam, keyword stuffing, or mass-solicitation content was detected "
                "in the submitted project text."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "keyword_stuffing",
                "gaming_search_visibility",
                "mass_solicitation"
            ],
            "medium_risk_claim_types": [
                "repetitive_content",
                "spam_advertising",
                "unrelated_keyword_injection"
            ]
        },

        "rules": [

            # ── Tier-direct rules (fire before claim-count rules) ──────────────────
            # When the LLM returns recommended_tier, use it directly so M16 does not
            # fall through to raw claim-count rules that are miscalibrated for NUIS.
            {
                "rule_id": "NUIS01-RPASS",
                "description": "LLM recommends PASS tier — no actionable violation.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "PASS"},
                "result": {
                    "matched_flag": False, "severity": "LOW", "suggested_action": "PASS",
                    "manual_review_required": False, "confidence_score": 0.90,
                    "reason_template": ("No spam, keyword stuffing, or mass solicitation detected; keyword repetition is natural and contextual.")
                }
            },

            {
                "rule_id": "NUIS01-RQRN",
                "description": "LLM recommends QUARANTINE tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "QUARANTINE"},
                "result": {
                    "matched_flag": True, "severity": "CRITICAL", "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Anti-Abuse / Platform Integrity", "manual_review_required": True,
                    "confidence_score": 0.93, "reason_template": ("Bot-like duplicate submission — a wall of repeated phrases/URLs or a link farm/financial spam dump across fields. Reject and quarantine.")
                }
            },

            {
                "rule_id": "NUIS01-RESC",
                "description": "LLM recommends ESCALATE tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "ESCALATE"},
                "result": {
                    "matched_flag": True, "severity": "HIGH", "suggested_action": "ESCALATE",
                    "escalate_to": "Anti-Abuse / Compliance", "manual_review_required": True,
                    "confidence_score": 0.90, "reason_template": ("Explicit keyword stuffing, aggressive commercial solicitation, or repeated spam phrases unrelated to the project. Escalate to Anti-Abuse.")
                }
            },

            {
                "rule_id": "NUIS01-RNR",
                "description": "LLM recommends NEEDS_REVIEW tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "NEEDS_REVIEW"},
                "result": {
                    "matched_flag": True, "severity": "MEDIUM", "suggested_action": "REVIEW",
                    "manual_review_required": True, "confidence_score": 0.82,
                    "reason_template": ("Borderline keyword stuffing, SEO metadata block, or repetitive marketing language. Flag for moderator review.")
                }
            },

            {
                "rule_id": "NUIS01-R0",
                "description": "LLM spam analysis failed; cannot safely pass.",
                "conditions": {"llm_analysis_failed": True},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.40,
                    "reason_template": (
                        "LLM spam analysis failed. The policy cannot be safely passed because "
                        "keyword-stuffing and solicitation detection was incomplete."
                    )
                }
            },
            {
                "rule_id": "NUIS01-R1",
                "description": "Clear keyword stuffing or SEO manipulation detected — reject.",
                "conditions": {"min_high_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REJECT_RECOMMENDED",
                    "manual_review_required": True,
                    "confidence_score": 0.88,
                    "reason_template": (
                        "Keyword stuffing, SEO manipulation, or mass-solicitation content was detected. "
                        "The submission does not meet quality standards and should be rejected or "
                        "required to be completely rewritten."
                    )
                }
            },
            {
                "rule_id": "NUIS01-R2",
                "description": "Spam advertising or repetitive content — request amendment.",
                "conditions": {"min_medium_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REQUEST_AMENDMENT",
                    "manual_review_required": True,
                    "confidence_score": 0.78,
                    "reason_template": (
                        "Spam-like advertising language or repetitive content was detected. "
                        "The submitter should revise the content to focus on genuine project "
                        "information rather than promotional or solicitation language."
                    )
                }
            },
            {
                "rule_id": "NUIS01-R3",
                "description": "Low-confidence spam signal — review recommended.",
                "conditions": {"min_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "LOW",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.62,
                    "reason_template": (
                        "Content with possible spam or solicitation characteristics was detected. "
                        "Moderator review is recommended to assess content quality."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "repetition_requires_full_text_analysis",
                "condition": {"always": True},
                "message": (
                    "Repetition detection is most accurate on the full normalised text. "
                    "Token-level analysis may miss subtle repetition patterns."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "final_quality_determination_not_made",
                "condition": {"always": True},
                "message": (
                    "The pipeline does not make final content quality determinations. "
                    "Human review is required for borderline spam cases."
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
            "Detects keyword stuffing, repetitive content, SEO gaming, and mass-solicitation patterns.",
            "Identifies spam advertising language embedded in project submissions.",
            "Classifies spam content by type and generates amendment-request reason notes.",
            "Flags submissions that do not meet content quality standards."
        ],
        "what_this_policy_does_not_do": [
            "Does not compare keyword density against a statistical baseline.",
            "Does not cross-reference submissions for repetition across accounts.",
            "Does not apply automated spam scoring beyond pattern analysis.",
            "Does not make final content quality determinations."
        ]
    }
}
