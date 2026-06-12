"""
REG-04 Policy Configuration

Policy:
Promotional or sponsored content presented without required disclosure
of commercial interest or sponsorship relationship.

Unique trigger focus:
Detects content that appears to be commercially motivated — advertising,
sponsored promotion, paid partnership, affiliate promotion — presented as
neutral project content without the required disclosure that it is promotional
or sponsored. Distinct from REG-02 (superlative wording) and NUIS-01 (spam);
this policy targets hidden commercial intent.

Severity: MEDIUM — undisclosed promotional content requires amendment or
moderator review; it does not automatically require rejection.
"""

REG_04_CONFIG = {
    "policy_code": "REG-04",

    "policy_name": (
        "Promotional or sponsored content without required disclosure"
    ),

    "policy_category": "Regulatory (Media)",

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
        "prompt_id": "REG_04_PROMOTIONAL_ANALYSIS",
        "max_tokens": 3500
    },

    "claim_types": [
        "undisclosed_sponsorship",
        "undisclosed_paid_partnership",
        "undisclosed_commercial_interest",
        "affiliate_promotion_without_disclosure",
        "product_service_advertisement",
        "brand_promotion_disguised_as_project",
        "financial_incentive_not_declared"
    ],

    # M03 absolute / authority scans
    "absolute_claim_terms": [],

    "authority_terms": [],

    "evidence_indicators": [
        "sponsored", "paid partnership", "advertisement", "ad", "affiliate",
        "disclosure", "commercial interest", "paid content"
    ],

    # M03 EXTRA_TERM_LIST_KEYS — auto-scanned by m03_rule_signals.py
    "promotional_disclosure_terms": [
        "buy now", "purchase", "shop now", "order today", "limited offer",
        "discount", "promo code", "coupon", "special offer", "sale",
        "click here", "visit our website", "sign up now", "register now",
        "sponsored by", "brought to you by", "in partnership with",
        "affiliate", "commission", "referral link", "referral code",
        "earn money", "make money", "passive income", "investment opportunity",
        "free trial", "no obligation", "money back guarantee",
        "exclusive deal", "members only", "subscribers only",
        "follow us", "subscribe to", "like and share",
        "contact us for pricing", "request a quote", "book a demo"
    ],

    "decision_rules": {
        "default": {
            "matched_flag": False,
            "severity": "LOW",
            "suggested_action": "PASS",
            "manual_review_required": False,
            "confidence_score": 0.85,
            "reason_template": (
                "No undisclosed promotional or sponsored content was detected in the submitted "
                "project text."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "undisclosed_sponsorship",
                "undisclosed_paid_partnership",
                "brand_promotion_disguised_as_project",
                "financial_incentive_not_declared"
            ],
            "medium_risk_claim_types": [
                "undisclosed_commercial_interest",
                "affiliate_promotion_without_disclosure",
                "product_service_advertisement",
                "financial_incentive_not_declared"
            ]
        },

        "rules": [

            # ── Tier-direct rules (fire before claim-count rules) ──────────────────
            # When the LLM returns recommended_tier, use it directly so M16 does not
            # fall through to raw claim-count rules that are miscalibrated for REG.
            {
                "rule_id": "REG04-RPASS",
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
                        "No undisclosed promotional content detected, or commercial content has clear and conspicuous disclosure in the submitted text."
                    )
                }
            },

            {
                "rule_id": "REG04-RQRN",
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
                        "Phishing or credential-harvesting content impersonating an official body detected. Reject and escalate immediately."
                    )
                }
            },

            {
                "rule_id": "REG04-RESC",
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
                        "High-risk financial fraud, crypto/gambling/MLM scheme, or unregulated health product promotion without disclosure detected. Escalate to Legal."
                    )
                }
            },

            {
                "rule_id": "REG04-RNR",
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
                        "Commercial promotional content (affiliate links, brand CTAs) without required disclosure detected. Amendment required to add disclosure."
                    )
                }
            },

            {
                "rule_id": "REG04-R0",
                "description": "LLM promotional analysis failed; cannot safely pass.",
                "conditions": {"llm_analysis_failed": True},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.45,
                    "reason_template": (
                        "LLM promotional content analysis failed. The policy cannot be safely "
                        "passed because commercial-intent detection was incomplete."
                    )
                }
            },
            {
                "rule_id": "REG04-R1",
                "description": "Undisclosed sponsorship or paid partnership detected — reject.",
                "conditions": {"min_high_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Moderation Review",
                    "manual_review_required": True,
                    "confidence_score": 0.88,
                    "reason_template": (
                        "Undisclosed sponsorship, paid partnership, or commercial promotion was detected "
                        "in the project content without the required disclosure. The submission must be "
                        "amended or rejected until proper disclosure is added."
                    )
                }
            },
            {
                "rule_id": "REG04-R2",
                "description": "Commercial or affiliate content without disclosure — request amendment.",
                "conditions": {"min_medium_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REQUEST_AMENDMENT",
                    "manual_review_required": True,
                    "confidence_score": 0.78,
                    "reason_template": (
                        "Content with possible commercial interest or promotional framing was detected "
                        "without disclosure. The submitter should clarify whether the content is "
                        "sponsored and add appropriate disclosure if so."
                    )
                }
            },
            {
                "rule_id": "REG04-R3",
                "description": "Low-confidence promotional signal — review recommended.",
                "conditions": {"min_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "LOW",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.62,
                    "reason_template": (
                        "Content that may have commercial intent was detected. Moderator review is "
                        "recommended to assess whether disclosure is required."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "sponsorship_relationship_not_verifiable",
                "condition": {"always": True},
                "message": (
                    "Whether a financial or commercial relationship exists between the submitter "
                    "and any promoted entity cannot be verified from submitted text alone."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "disclosure_policy_wording_not_finalised",
                "condition": {"always": True},
                "message": (
                    "SWA platform disclosure wording requirements are not yet finalised. "
                    "Moderation should apply best-judgement standards pending policy finalisation."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "final_regulatory_determination_not_made",
                "condition": {"always": True},
                "message": (
                    "The pipeline does not make final regulatory determinations on disclosure "
                    "obligations. Human review is required for all flagged cases."
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
        "PASS", "REVIEW", "REQUEST_AMENDMENT", "ESCALATE", "REJECT_RECOMMENDED"
    ],

    "scope_notes": {
        "current_scope": "Project-only moderation for current POC.",
        "what_this_policy_does": [
            "Detects content with commercial, promotional, or sponsored intent presented without disclosure.",
            "Identifies undisclosed paid partnerships, affiliate links, and brand promotion.",
            "Classifies promotional content type and generates amendment-request reason notes.",
            "Flags content for moderator review when commercial intent is suspected."
        ],
        "what_this_policy_does_not_do": [
            "Does not verify whether a commercial relationship actually exists.",
            "Does not confirm the identity of sponsors or paid partners.",
            "Does not make final regulatory determinations on disclosure obligations.",
            "Does not detect promotional content in attached files or media.",
            "Does not apply jurisdiction-specific advertising standards."
        ]
    }
}
