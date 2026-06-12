"""
MAL-04 Policy Configuration

Policy:
Coordinated abuse — mass submissions, template reuse, link farms,
or automated submission patterns.

Unique trigger focus:
Detects content patterns suggesting coordinated manipulation of the SWA
platform — identical or near-identical boilerplate, link farm structures,
mass-solicitation templates, or submission patterns indicating automated
or organised abuse. This policy overlaps with NUIS-01 (spam) but focuses
on organised/coordinated abuse rather than single-instance spam. Full
effectiveness requires historical submission data (currently out of scope).

Severity: HIGH — coordinated abuse signals must be escalated to the
Anti-Abuse team for pattern investigation.
"""

MAL_04_CONFIG = {
    "policy_code": "MAL-04",

    "policy_name": (
        "Coordinated abuse — mass submissions, template reuse, or link farms"
    ),

    "policy_category": "Malicious",

    "severity": "HIGH",

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
        "prompt_id": "MAL_04_COORDINATED_ABUSE_ANALYSIS",
        "max_tokens": 3500
    },

    "claim_types": [
        "template_reuse_pattern",
        "mass_solicitation_content",
        "link_farm_structure",
        "coordinated_submission_signal",
        "automated_content_pattern",
        "boilerplate_abuse"
    ],

    # M03 absolute / authority scans
    "absolute_claim_terms": [],

    "authority_terms": [],

    "evidence_indicators": [
        "source", "reference", "attached"
    ],

    # M03 EXTRA_TERM_LIST_KEYS — auto-scanned by m03_rule_signals.py
    "abuse_pattern_terms": [
        "submit your project", "submit your listing", "submit your site",
        "add your link", "add your url", "add your website",
        "backlink", "link exchange", "link building", "seo link",
        "directory submission", "article submission", "mass submission",
        "automated submission", "bulk submission",
        "copy and paste", "use this template", "fill in the blanks",
        "enter your details below", "replace with your information",
        "lorem ipsum", "placeholder", "sample text", "insert text here",
        "contact us at [email]", "visit us at [url]", "call [number]",
        "we accept all projects", "all projects welcome",
        "guaranteed approval", "instant approval", "no review needed"
    ],

    "decision_rules": {
        "default": {
            "matched_flag": False,
            "severity": "LOW",
            "suggested_action": "PASS",
            "manual_review_required": False,
            "confidence_score": 0.85,
            "reason_template": (
                "No coordinated abuse, mass-submission, or template-reuse pattern was detected "
                "in the submitted project text."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "link_farm_structure",
                "coordinated_submission_signal",
                "automated_content_pattern"
            ],
            "medium_risk_claim_types": [
                "template_reuse_pattern",
                "mass_solicitation_content",
                "boilerplate_abuse"
            ]
        },

        "rules": [

            # ── Tier-direct rules (fire before claim-count rules) ──────────────────
            # When the LLM returns recommended_tier, use it directly so M16 does not
            # fall through to raw claim-count rules that are miscalibrated for MAL.
            {
                "rule_id": "MAL04-RPASS",
                "description": "LLM recommends PASS tier — no actionable violation.",
                "conditions": {
                    "llm_analysis_failed": False,
                    "llm_recommended_tier": "PASS"
                },
                "result": {
                    "matched_flag": False,
                    "severity": "LOW",
                    "suggested_action": "PASS",
                    "manual_review_required": False,
                    "confidence_score": 0.90,
                    "reason_template": (
                        "No coordinated-abuse signals; submission is unique, specific, and individually authored."
                    )
                }
            },

            {
                "rule_id": "MAL04-RQRN",
                "description": "LLM recommends QUARANTINE tier.",
                "conditions": {
                    "llm_analysis_failed": False,
                    "llm_recommended_tier": "QUARANTINE"
                },
                "result": {
                    "matched_flag": True,
                    "severity": "CRITICAL",
                    "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Security / Anti-Abuse",
                    "manual_review_required": True,
                    "confidence_score": 0.93,
                    "reason_template": (
                        "Link-farm / SEO redirect abuse — multiple links to a shared redirect/spam hub. Reject and quarantine immediately."
                    )
                }
            },

            {
                "rule_id": "MAL04-RESC",
                "description": "LLM recommends ESCALATE tier.",
                "conditions": {
                    "llm_analysis_failed": False,
                    "llm_recommended_tier": "ESCALATE"
                },
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "ESCALATE",
                    "escalate_to": "Security / Anti-Abuse",
                    "manual_review_required": True,
                    "confidence_score": 0.90,
                    "reason_template": (
                        "Clear coordinated campaign — automated-system language, rigid identical targets, cloud-synced template structure matching many submissions. Escalate to Anti-Abuse."
                    )
                }
            },

            {
                "rule_id": "MAL04-RNR",
                "description": "LLM recommends NEEDS_REVIEW tier.",
                "conditions": {
                    "llm_analysis_failed": False,
                    "llm_recommended_tier": "NEEDS_REVIEW"
                },
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.82,
                    "reason_template": (
                        "Generic template-like content that may be part of a mass-submission campaign. Flag for coordination review."
                    )
                }
            },

            {
                "rule_id": "MAL04-R0",
                "description": "LLM coordinated abuse analysis failed; cannot safely pass.",
                "conditions": {"llm_analysis_failed": True},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.45,
                    "reason_template": (
                        "LLM coordinated-abuse analysis failed. The policy cannot be safely passed "
                        "because abuse-pattern detection was incomplete."
                    )
                }
            },
            {
                "rule_id": "MAL04-R1",
                "description": "High-risk coordinated abuse pattern detected — escalate.",
                "conditions": {"min_high_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "ESCALATE",
                    "escalate_to": "Anti-Abuse Review",
                    "manual_review_required": True,
                    "confidence_score": 0.88,
                    "reason_template": (
                        "Link farm structure, coordinated submission pattern, or automated-content "
                        "indicators were detected. Escalate to Anti-Abuse for pattern investigation "
                        "and cross-submission comparison."
                    )
                }
            },
            {
                "rule_id": "MAL04-R2",
                "description": "Template reuse or mass solicitation pattern detected — review.",
                "conditions": {"min_medium_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.75,
                    "reason_template": (
                        "Template-reuse or mass-solicitation content pattern was detected. "
                        "Moderator review is required to assess whether this is part of a "
                        "coordinated submission campaign."
                    )
                }
            },
            {
                "rule_id": "MAL04-R3",
                "description": "Low-confidence abuse signal — review recommended.",
                "conditions": {"min_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "LOW",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.60,
                    "reason_template": (
                        "Content with possible boilerplate or mass-submission characteristics was "
                        "detected. Review is recommended particularly if similar content appears "
                        "in multiple submissions."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "historical_submission_data_not_available",
                "condition": {"always": True},
                "message": (
                    "Cross-submission comparison requires historical submission data which is not "
                    "available in the current POC. Coordinated abuse signals are limited to "
                    "single-submission pattern analysis."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "submitter_identity_not_verified",
                "condition": {"always": True},
                "message": (
                    "Submitter identity and account history are not verified by the pipeline. "
                    "Anti-abuse investigation requires account-level data."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "final_abuse_determination_not_made",
                "condition": {"always": True},
                "message": (
                    "The pipeline cannot confirm coordinated abuse without cross-submission analysis. "
                    "Anti-abuse team must investigate all escalated cases."
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
        "PASS", "REVIEW", "ESCALATE", "REJECT_RECOMMENDED"
    ],

    "scope_notes": {
        "current_scope": "Project-only moderation for current POC.",
        "what_this_policy_does": [
            "Detects template-reuse, boilerplate, link-farm, and mass-solicitation patterns.",
            "Identifies automated or coordinated submission signals within single submissions.",
            "Classifies abuse patterns by type and risk level.",
            "Generates anti-abuse escalation signals for pattern investigation."
        ],
        "what_this_policy_does_not_do": [
            "Does not compare submissions across accounts (historical data required).",
            "Does not verify submitter identity or account history.",
            "Does not detect IP-level or device-level patterns.",
            "Does not make final coordinated-abuse determinations.",
            "Full detection requires historical data (out of current POC scope)."
        ]
    }
}
