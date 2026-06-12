"""
REG-01 Policy Configuration

Policy:
Materially misleading factual claims or distorted information likely to mislead audiences.

Important:
- This config uses the existing generic moderation modules.
- No new module files are needed for current project-only POC.
"""

REG_01_CONFIG = {
    "policy_code": "REG-01",

    "policy_name": (
        "Materially misleading factual claims or distorted information likely "
        "to mislead audiences"
    ),

    "policy_category": "Regulatory (Media)",

    "severity": "HIGH",

    "applies_to": [
        "Project"
    ],

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
        "prompt_id": "REG_01_CLAIM_ANALYSIS",
        "max_tokens": 2600
    },

    "claim_types": [
        "statistical_or_numeric_claim",
        "environmental_claim",
        "impact_or_outcome_claim",
        "endorsement_or_authority_claim",
        "comparison_or_superiority_claim",
        "distorted_or_selectively_framed_claim",
        "false_or_unsubstantiated_factual_claim",
        "fabricated_statistic",
        "other_misleading_factual_claim"
    ],

    "absolute_claim_terms": [
        "proven",
        "verified",
        "fully verified",
        "scientifically proven",
        "guaranteed",
        "official",
        "officially",
        "certified",
        "approved",
        "endorsed",
        "backed by",
        "funded by",
        "recognised by",
        "recognized by",
        "industry-leading",
        "world-leading",
        "best",
        "only",
        "number one",
        "#1",
        "100%",
        "success rate",
        "zero impact",
        "carbon neutral",
        "net zero"
    ],

    "authority_terms": [
        "government",
        "ministry",
        "united nations",
        "world bank",
        "official body",
        "certification body",
        "approved by",
        "endorsed by"
    ],

    "environmental_terms": [
        "carbon neutral",
        "net zero",
        "emissions reduced by",
        "pollution reduced by",
        "deforestation reversed",
        "climate impact"
    ],

    "distortion_terms": [
        "fully solved",
        "completely eliminated",
        "proven impact",
        "verified impact",
        "unmatched",
        "zero emissions",
        "100% success"
    ],

    "evidence_indicators": [
        "source",
        "according to",
        "report",
        "study",
        "audit",
        "certificate",
        "certification",
        "approval number",
        "grant id",
        "reference",
        "citation",
        "link",
        "url",
        "attached",
        "attachment",
        "evidence uploaded",
        "see report",
        "verified by",
        "validated by",
        "published by",
        "survey",
        "dataset",
        "baseline",
        "methodology"
    ],

    "decision_rules": {
        "default": {
            "matched_flag": False,
            "severity": "LOW",
            "suggested_action": "PASS",
            "manual_review_required": False,
            "confidence_score": 0.82,
            "reason_template": (
                "No materially misleading factual claim was detected from the submitted project text."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "fabricated_statistic",
                "endorsement_or_authority_claim",
                "false_or_unsubstantiated_factual_claim",
                "distorted_or_selectively_framed_claim"
            ],

            "medium_risk_claim_types": [
                "statistical_or_numeric_claim",
                "comparison_or_superiority_claim"
            ]
        },

        "rules": [

            # ── Tier-direct rules (fire before claim-count rules) ──────────────────
            # When the LLM returns recommended_tier, use it directly so M16 does not
            # fall through to raw claim-count rules that are miscalibrated for REG.
            {
                "rule_id": "REG01-RPASS",
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
                        "No misleading, distorted, or unsubstantiated factual claim was detected, or all claims are properly attributed to named official sources."
                    )
                }
            },

            {
                "rule_id": "REG01-RQRN",
                "description": "LLM recommends QUARANTINE tier.",
                "conditions": {
                    "llm_analysis_failed": False,
                    "llm_recommended_tier": "QUARANTINE"
                },
                "result": {
                    "matched_flag": True,
                    "severity": "CRITICAL",
                    "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Legal / Safety / Regulatory Review",
                    "manual_review_required": True,
                    "confidence_score": 0.93,
                    "reason_template": (
                        "Severely misleading content combined with threats, doxxing, or fraud detected. Reject and escalate to Legal/Safety."
                    )
                }
            },

            {
                "rule_id": "REG01-RESC",
                "description": "LLM recommends ESCALATE tier.",
                "conditions": {
                    "llm_analysis_failed": False,
                    "llm_recommended_tier": "ESCALATE"
                },
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "ESCALATE",
                    "escalate_to": "Regulatory / Legal Review",
                    "manual_review_required": True,
                    "confidence_score": 0.90,
                    "reason_template": (
                        "False authority endorsement, fabricated certification, or severely distorted/impossible statistic detected. Escalate to Regulatory/Legal for review."
                    )
                }
            },

            {
                "rule_id": "REG01-RNR",
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
                        "Unsubstantiated factual claim(s) requiring source attribution were detected. Flag for moderator review and evidence/amendment request."
                    )
                }
            },

            {
                "rule_id": "REG01-R0",
                "description": (
                    "LLM semantic misleading-claim analysis failed, so the policy cannot safely pass."
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
                        "LLM misleading-claim analysis failed. The policy cannot be safely passed "
                        "because factual claim analysis was incomplete."
                    )
                }
            },

            {
                "rule_id": "REG01-R1",
                "description": (
                    "High-risk misleading or authority-backed factual claim without evidence should escalate."
                ),
                "conditions": {
                    "min_high_risk_claims": 1,
                    "min_evidence_issues": 1
                },
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "ESCALATE",
                    "escalate_to": "Human Moderator / Regulatory Review",
                    "manual_review_required": True,
                    "confidence_score": 0.90,
                    "reason_template": (
                        "High-risk factual or authority-backed claim(s) were detected without visible "
                        "supporting evidence or attribution. The content may materially mislead audiences "
                        "and should be escalated for human regulatory review."
                    )
                }
            },

            {
                "rule_id": "REG01-R2",
                "description": (
                    "Multiple evidence-required factual claims missing attribution should request evidence."
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
                        "Multiple factual claim(s) likely to influence audience understanding were detected, "
                        "but supporting evidence or attribution was not found in the submitted text. "
                        "Request evidence, source attribution, or claim revision."
                    )
                }
            },

            {
                "rule_id": "REG01-R3",
                "description": (
                    "High-risk misleading claim with some evidence reference still requires review."
                ),
                "conditions": {
                    "min_high_risk_claims": 1
                },
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.78,
                    "reason_template": (
                        "High-risk factual or potentially misleading claim(s) were detected. "
                        "Moderator review is recommended because the current POC does not verify "
                        "truth, source credibility, or external factual correctness."
                    )
                }
            },

            {
                "rule_id": "REG01-R4",
                "description": (
                    "Single evidence-required factual claim missing attribution; soft review recommended."
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
                        "A factual claim requiring supporting attribution was detected without an "
                        "evidence reference nearby. The claim is lower-risk; a soft review is recommended."
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
                    "Image/media evidence was not provided in current pipeline input; "
                    "therefore manipulated charts, images, or visual evidence cannot be assessed."
                ),
                "force_partial_evaluation": True
            },

            {
                "gap_key": "external_fact_verification_not_performed",
                "condition": {
                    "always": True
                },
                "message": (
                    "External factual verification was not performed; statistics, endorsements, "
                    "environmental claims, and factual assertions are assessed only from submitted text."
                ),
                "force_partial_evaluation": True
            },

            {
                "gap_key": "source_credibility_not_scored",
                "condition": {
                    "always": True
                },
                "message": (
                    "Source credibility scoring is not performed in the current POC."
                ),
                "force_partial_evaluation": True
            },

            {
                "gap_key": "cross_document_verification_not_performed",
                "condition": {
                    "always": True
                },
                "message": (
                    "Cross-document comparison or external source comparison is not performed "
                    "in the current POC."
                ),
                "force_partial_evaluation": True
            },

            {
                "gap_key": "final_regulatory_determination_not_made",
                "condition": {
                    "always": True
                },
                "message": (
                    "The system does not make final legal or regulatory determinations; "
                    "it only supports moderation triage."
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
            "dependency_gaps",
            "risk_classification"
        ]
    },

    "allowed_outcomes": [
        "PASS",
        "REVIEW",
        "REQUEST_AMENDMENT",
        "ESCALATE",
        "REJECT_RECOMMENDED"
    ],

    "scope_notes": {
        "current_scope": (
            "Project-only moderation for current POC. Profile, Service, and Self-Assessment "
            "records are outside current implementation scope."
        ),

        "what_this_policy_does": [
            "Extracts factual claims from project text.",
            "Classifies statistical, environmental, authority, endorsement, comparison, and impact claims.",
            "Detects claims that may mislead audiences if unsupported or distorted.",
            "Estimates whether evidence or attribution is required.",
            "Detects visible evidence or attribution indicators in submitted text.",
            "Generates moderator-facing reason notes and suggested action."
        ],

        "what_this_policy_does_not_do": [
            "Does not verify factual truth externally.",
            "Does not validate statistics against trusted sources.",
            "Does not confirm endorsements are genuine.",
            "Does not determine final legal or regulatory breach.",
            "Does not detect manipulated charts or images unless media-analysis modules are added later.",
            "Does not score source credibility in current POC."
        ]
    }
}