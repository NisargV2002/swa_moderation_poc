"""
NUIS-03 Policy Configuration

Policy:
Off-topic content unrelated to the stated project purpose or SWA platform scope.

Unique trigger focus:
Detects submissions where the content is fundamentally unrelated to the
SWA platform's mandate — personal advertisements, unrelated commercial
listings, social media posts, personal journals, or content that has
no connection to the project objectives stated or implied by the submission
context. Distinct from NUIS-01 (spam) and NUIS-02 (low substance); this
policy targets content that is coherent but simply wrong for the platform.

Severity: MEDIUM — off-topic submissions typically require amendment or
rejection with guidance to resubmit appropriate content.
"""

NUIS_03_CONFIG = {
    "policy_code": "NUIS-03",

    "policy_name": (
        "Off-topic content unrelated to project purpose or SWA platform scope"
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
        "prompt_id": "NUIS_03_OFF_TOPIC_ANALYSIS",
        "max_tokens": 3500
    },

    "claim_types": [
        "personal_advertisement",
        "unrelated_commercial_content",
        "personal_journal_or_blog",
        "social_media_repurposed_content",
        "unrelated_product_listing",
        "platform_scope_mismatch",
        "missing_project_substance"
    ],

    # M03 absolute / authority scans
    "absolute_claim_terms": [],

    "authority_terms": [],

    "evidence_indicators": [],

    # M03 EXTRA_TERM_LIST_KEYS — auto-scanned by m03_rule_signals.py
    "off_topic_indicators": [
        "for sale", "for rent", "for lease", "property listing",
        "real estate", "selling my", "i am selling",
        "personal trainer", "fitness coach", "my coaching services",
        "dating", "meet singles", "find love", "relationship advice",
        "travel blog", "my travel diary", "my holiday",
        "restaurant review", "hotel review", "food blog",
        "gaming", "my gaming channel", "subscribe to my channel",
        "my youtube", "my instagram", "my tiktok", "my twitter",
        "entertainment", "movie review", "music release",
        "hire me", "freelance", "available for work",
        "my resume", "my cv", "job application",
        "personal opinion", "my thoughts on", "my views on",
        "political campaign", "vote for", "support my campaign",
        "religious organisation", "church", "mosque", "temple",
        "unrelated to", "not about sustainability", "not a project"
    ],

    "decision_rules": {
        "default": {
            "matched_flag": False,
            "severity": "LOW",
            "suggested_action": "PASS",
            "manual_review_required": False,
            "confidence_score": 0.85,
            "reason_template": (
                "No off-topic or platform-scope-mismatch content was detected. "
                "The submission appears to be relevant to the project's stated purpose."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "personal_advertisement",
                "unrelated_commercial_content",
                "unrelated_product_listing",
                "platform_scope_mismatch"
            ],
            "medium_risk_claim_types": [
                "personal_journal_or_blog",
                "social_media_repurposed_content",
                "missing_project_substance"
            ]
        },

        "rules": [

            # ── Tier-direct rules (fire before claim-count rules) ──────────────────
            # When the LLM returns recommended_tier, use it directly so M16 does not
            # fall through to raw claim-count rules that are miscalibrated for NUIS.
            {
                "rule_id": "NUIS03-RPASS",
                "description": "LLM recommends PASS tier — no actionable violation.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "PASS"},
                "result": {
                    "matched_flag": False, "severity": "LOW", "suggested_action": "PASS",
                    "manual_review_required": False, "confidence_score": 0.90,
                    "reason_template": ("Content is on-topic; any contextual background is relevant to the sustainability/community project.")
                }
            },

            {
                "rule_id": "NUIS03-RQRN",
                "description": "LLM recommends QUARANTINE tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "QUARANTINE"},
                "result": {
                    "matched_flag": True, "severity": "CRITICAL", "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Anti-Abuse / Platform Integrity", "manual_review_required": True,
                    "confidence_score": 0.93, "reason_template": ("Restricted off-topic content — gambling ads, weight-loss/supplement sales, or MLM recruitment disguised as a project. Reject and quarantine.")
                }
            },

            {
                "rule_id": "NUIS03-RESC",
                "description": "LLM recommends ESCALATE tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "ESCALATE"},
                "result": {
                    "matched_flag": True, "severity": "HIGH", "suggested_action": "ESCALATE",
                    "escalate_to": "Anti-Abuse / Compliance", "manual_review_required": True,
                    "confidence_score": 0.90, "reason_template": ("Off-topic content replacing the project — political campaign, sports news, religious tract, real-estate ad, or personal blog. Escalate to Anti-Abuse.")
                }
            },

            {
                "rule_id": "NUIS03-RNR",
                "description": "LLM recommends NEEDS_REVIEW tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "NEEDS_REVIEW"},
                "result": {
                    "matched_flag": True, "severity": "MEDIUM", "suggested_action": "REVIEW",
                    "manual_review_required": True, "confidence_score": 0.82,
                    "reason_template": ("Mixed relevance — project content combined with a tangential personal critique, recipe, or brand review. Flag for moderator review.")
                }
            },

            {
                "rule_id": "NUIS03-R0",
                "description": "LLM off-topic analysis failed; cannot safely pass.",
                "conditions": {"llm_analysis_failed": True},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.40,
                    "reason_template": (
                        "LLM off-topic analysis failed. The policy cannot be safely passed because "
                        "content relevance detection was incomplete."
                    )
                }
            },
            {
                "rule_id": "NUIS03-R1",
                "description": "Clearly off-topic content detected — reject.",
                "conditions": {"min_high_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REJECT_RECOMMENDED",
                    "manual_review_required": True,
                    "confidence_score": 0.88,
                    "reason_template": (
                        "Content that is clearly unrelated to the project purpose or SWA platform "
                        "scope was detected. The submission should be rejected with guidance for "
                        "the submitter to provide relevant project content."
                    )
                }
            },
            {
                "rule_id": "NUIS03-R2",
                "description": "Partially off-topic or misaligned content — request amendment.",
                "conditions": {"min_medium_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REQUEST_AMENDMENT",
                    "manual_review_required": True,
                    "confidence_score": 0.75,
                    "reason_template": (
                        "Content that appears partially off-topic or not aligned with the stated "
                        "project purpose was detected. The submitter should revise to ensure all "
                        "content is directly relevant to the project goals."
                    )
                }
            },
            {
                "rule_id": "NUIS03-R3",
                "description": "Low-confidence off-topic signal — review recommended.",
                "conditions": {"min_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "LOW",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.60,
                    "reason_template": (
                        "Content that may not be fully aligned with the project purpose was detected. "
                        "Moderator review is recommended to assess relevance."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "platform_scope_definition_not_formalised",
                "condition": {"always": True},
                "message": (
                    "The SWA platform's formal scope definition and acceptable content categories "
                    "have not been fully finalised. Moderation applies best-judgement standards."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "project_category_context_limited",
                "condition": {"always": True},
                "message": (
                    "The pipeline has limited context about the project's intended category "
                    "and domain, which may affect off-topic determination accuracy."
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
            "Detects content fundamentally unrelated to the project purpose or SWA platform scope.",
            "Identifies personal advertisements, unrelated commercial content, and platform misuse.",
            "Classifies off-topic content by type and generates amendment-request reason notes.",
            "Flags submissions requiring content relevance correction."
        ],
        "what_this_policy_does_not_do": [
            "Does not apply formal platform-scope rules (not yet finalised).",
            "Does not access project category metadata to improve relevance scoring.",
            "Does not compare against approved project templates.",
            "Does not make final platform-scope determinations."
        ]
    }
}
