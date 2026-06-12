"""
TYPE-PROJECT-01 Policy Config

Purpose:
- Policy-specific configuration.
- Modules stay reusable.
"""
TYPE_PROJECT_01_CONFIG = {
    "policy_code": "TYPE-PROJECT-01",

    "policy_name": (
        "Project claims about outcomes, funding, approvals, certifications, "
        "authority affiliations, or partnerships that appear unverifiable or misleading"
    ),

    "module_sequence": [
        "M01",
        "M02",
        "M03",
        "M05",
        "M07",
        "M08",
        "M16",
        "M17"
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
        "prompt_id": "TYPE_PROJECT_01_CLAIM_EXTRACTION",
        "max_tokens": 2400
    },

    "claim_types": [
        "outcome",
        "funding",
        "approval",
        "certification",
        "partnership",
        "authority_affiliation",
        "recognition",
        "sustainability_impact",
        "other"
    ],

    "absolute_claim_terms": [
        "guaranteed",
        "officially approved",
        "fully certified",
        "best",
        "only",
        "#1",
        "100%",
        "world leading",
        "government funded",
        "un approved",
        "united nations approved"
    ],

    "authority_terms": [
        "united nations",
        "government",
        "ministry",
        "un approved",
        "united nations approved",
        "government funded",
        "government recognized"
    ],

    "evidence_indicators": [
        "report",
        "link",
        "url",
        "certificate",
        "grant id",
        "approval number",
        "attached",
        "evidence uploaded",
        "see report",
        "reference",
        "according to",
        "source",
        "verified by"
    ],

    "decision_rules": {
        "default": {
            "matched_flag": False,
            "severity": "LOW",
            "suggested_action": "PASS",
            "manual_review_required": False,
            "confidence_score": 0.82,
            "reason_template": "No relevant TYPE-PROJECT-01 claim risk was detected."
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "funding",
                "approval",
                "certification",
                "partnership",
                "authority_affiliation",
                "recognition"
            ],
            "medium_risk_claim_types": []
        },

        "rules": [

            # ── Tier-direct rules (fire before claim-count rules) ──────────────────
            # When the LLM returns recommended_tier, use it directly so M16 does not
            # fall through to raw claim-count rules that are miscalibrated.
            {
                "rule_id": "TP01-RPASS",
                "description": "LLM recommends PASS tier — no actionable violation.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "PASS"},
                "result": {
                    "matched_flag": False, "severity": "LOW", "suggested_action": "PASS",
                    "manual_review_required": False, "confidence_score": 0.90,
                    "reason_template": (
                        "No unverifiable factual claim requiring evidence was detected, or all "
                        "claims are aspirational or supported by specific verifiable references."
                    )
                }
            },

            {
                "rule_id": "TP01-RQRN",
                "description": "LLM recommends QUARANTINE tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "QUARANTINE"},
                "result": {
                    "matched_flag": True, "severity": "CRITICAL", "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Security / Compliance / Law Enforcement", "manual_review_required": True,
                    "confidence_score": 0.93,
                    "reason_template": (
                        "Phishing or financial fraud detected — fabricated registration/certification "
                        "codes combined with a malicious URL harvesting credentials or payments. "
                        "Reject and quarantine immediately."
                    )
                }
            },

            {
                "rule_id": "TP01-RESC",
                "description": "LLM recommends ESCALATE tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "ESCALATE"},
                "result": {
                    "matched_flag": True, "severity": "HIGH", "suggested_action": "ESCALATE",
                    "escalate_to": "Compliance / Legal", "manual_review_required": True,
                    "confidence_score": 0.90,
                    "reason_template": (
                        "Unverified high-authority claim (exclusive monopoly/partnership, major "
                        "government or international funding) used to solicit public money, "
                        "investment, or donations. Escalate to Compliance/Legal."
                    )
                }
            },

            {
                "rule_id": "TP01-RNR",
                "description": "LLM recommends NEEDS_REVIEW tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "NEEDS_REVIEW"},
                "result": {
                    "matched_flag": True, "severity": "MEDIUM", "suggested_action": "REVIEW",
                    "manual_review_required": True, "confidence_score": 0.82,
                    "reason_template": (
                        "Factual claim of partnership, funding, official approval, or certification "
                        "without supporting evidence (no reference number, official URL, or document), "
                        "or strong absolute marketing claims. Flag for moderator verification."
                    )
                }
            },

            {
                "rule_id": "TP01-R0",
                "description": (
                    "LLM semantic analysis failed, so policy cannot safely pass."
                ),
                "conditions": {
                    "llm_analysis_failed": True
                },
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.45,
                    "reason_template": (
                        "LLM semantic claim extraction failed. The policy cannot be safely passed "
                        "because claim analysis was incomplete."
                    )
                }
            },
            {
                "rule_id": "TP01-R1",
                "description": (
                    "High-risk authority/funding/approval claims missing evidence require escalation."
                ),
                "conditions": {
                    "min_high_risk_claims": 1,
                    "min_evidence_issues": 1
                },
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "ESCALATE",
                    "escalate_to": "Human Moderator / Legal-Safety Review",
                    "manual_review_required": True,
                    "confidence_score": 0.90,
                    "reason_template": (
                        "High-risk unsupported claims were detected, including official approval, "
                        "government funding, authority affiliation, or similar institutional claims. "
                        "Because these claims may imply formal endorsement or verified impact without "
                        "supporting evidence, the submission should be escalated for human review."
                    )
                }
            },
            {
                "rule_id": "TP01-R2",
                "description": (
                    "Multiple evidence-required claims missing evidence requires amendment."
                ),
                "conditions": {
                    "min_evidence_issues": 2
                },
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REQUEST_AMENDMENT",
                    "manual_review_required": True,
                    "confidence_score": 0.80,
                    "reason_template": (
                        "Project claim(s) requiring evidence were detected, but supporting "
                        "evidence was not found in the provided text."
                    )
                }
            },
            {
                "rule_id": "TP01-R3",
                "description": (
                    "High-risk claims with evidence references require review because authenticity is not verified."
                ),
                "conditions": {
                    "min_high_risk_claims": 1
                },
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.76,
                    "reason_template": (
                        "High-risk project claim(s) were detected. Moderator review is recommended "
                        "because evidence authenticity is not externally verified."
                    )
                }
            },
            {
                "rule_id": "TP01-R4",
                "description": (
                    "Single evidence-required claim missing evidence; request project to provide supporting details."
                ),
                "conditions": {
                    "min_evidence_issues": 1
                },
                "result": {
                    "matched_flag": True,
                    "severity": "LOW",
                    "suggested_action": "REVIEW",
                    "manual_review_required": False,
                    "confidence_score": 0.65,
                    "reason_template": (
                        "A claim requiring supporting evidence was detected but no evidence reference "
                        "was found near it. The claim is lower-risk; a soft review is recommended."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "attachments_not_provided",
                "condition": {
                    "input_coverage.attachments_available": False
                },
                "message": (
                    "Attachment evidence was not provided in current pipeline input."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "images_not_provided",
                "condition": {
                    "input_coverage.images_available": False
                },
                "message": (
                    "Image/media evidence was not provided in current pipeline input."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "external_verification_not_performed",
                "condition": {
                    "always": True
                },
                "message": (
                    "External evidence authenticity was not verified in current POC."
                ),
                "force_partial_evaluation": True
            }
        ]
    },

    "expected_output_schema": {
        "required_top_level_fields": [
            "policy_code",
            "policy_name",
            "matched_flag",
            "evaluation_status",
            "severity",
            "suggested_action",
            "manual_review_required",
            "moderator_reason_note",
            "confidence_score",
            "details",
            "result_json"
        ],
        "required_detail_fields": [
            "claim_count",
            "evidence_issue_count",
            "claims",
            "evidence_issues",
            "rule_signals",
            "entities",
            "language_info",
            "input_coverage",
            "dependency_gaps"
        ]
    },

    "allowed_outcomes": [
        "PASS",
        "REVIEW",
        "REQUEST_AMENDMENT",
        "ESCALATE",
        "REJECT_RECOMMENDED"
    ]
}