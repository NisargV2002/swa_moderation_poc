"""
REG-03 Policy Configuration

Policy:
Private or sensitive information about identifiable individuals shared
without evidence of consent.

Unique trigger focus:
Detects project content that discloses private facts — health, financial
status, personal relationships, religious beliefs, political views, or other
sensitive attributes — about real, identifiable individuals without demonstrating
consent. Distinct from LEGAL-02 (doxxing/PII numbers) and OFF-02 (harassment);
this policy focuses on privacy violations that arise from publishing sensitive
personal facts rather than from hostility or coercive intent.

Severity: HIGH — confirmed privacy violation must be rejected and escalated.
"""

REG_03_CONFIG = {
    "policy_code": "REG-03",

    "policy_name": (
        "Private or sensitive information about identifiable individuals without consent"
    ),

    "policy_category": "Regulatory (Media)",

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
        "prompt_id": "REG_03_PRIVACY_ANALYSIS",
        "max_tokens": 4000
    },

    "claim_types": [
        "health_or_medical_disclosure",
        "financial_status_disclosure",
        "relationship_or_family_disclosure",
        "religious_or_political_belief_disclosure",
        "sexual_orientation_or_gender_disclosure",
        "personal_circumstance_disclosure",
        "identifiable_individual_exposure",
        "consent_absent_sensitive_disclosure"
    ],

    # M03 absolute / authority scans
    "absolute_claim_terms": [],

    "authority_terms": [],

    "evidence_indicators": [
        "with consent", "consented", "permission", "authorised", "authorised by",
        "source", "attached", "reference"
    ],

    # M03 EXTRA_TERM_LIST_KEYS — auto-scanned by m03_rule_signals.py
    "privacy_violation_terms": [
        "medical condition", "health status", "diagnosis", "illness", "disease",
        "disability", "mental health", "therapy", "psychiatric", "addiction",
        "debt", "bankrupt", "bankruptcy", "financial difficulty", "in debt",
        "salary", "earning", "income level", "net worth",
        "divorce", "separation", "custody", "marital status",
        "sexual orientation", "gay", "lesbian", "bisexual", "transgender",
        "gender identity", "non-binary",
        "religion", "religious belief", "faith", "atheist", "Muslim",
        "Christian", "Jewish", "Hindu",
        "political affiliation", "political belief", "party membership",
        "immigration status", "undocumented", "visa status",
        "criminal history", "arrest record", "prior conviction",
        "pregnancy", "miscarriage", "abortion",
        "personal relationship", "affair", "infidelity"
    ],

    "decision_rules": {
        "default": {
            "matched_flag": False,
            "severity": "LOW",
            "suggested_action": "PASS",
            "manual_review_required": False,
            "confidence_score": 0.88,
            "reason_template": (
                "No non-consensual disclosure of private or sensitive personal information "
                "about an identifiable individual was detected in the submitted project text."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "health_or_medical_disclosure",
                "sexual_orientation_or_gender_disclosure",
                "identifiable_individual_exposure",
                "consent_absent_sensitive_disclosure"
            ],
            "medium_risk_claim_types": [
                "financial_status_disclosure",
                "relationship_or_family_disclosure",
                "religious_or_political_belief_disclosure",
                "personal_circumstance_disclosure"
            ]
        },

        "rules": [

            # ── Tier-direct rules (fire before claim-count rules) ──────────────────
            # When the LLM returns recommended_tier, use it directly so M16 does not
            # fall through to raw claim-count rules that are miscalibrated for REG.
            {
                "rule_id": "REG03-RPASS",
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
                        "No non-consensual disclosure of private or sensitive personal information about an identifiable individual was detected."
                    )
                }
            },

            {
                "rule_id": "REG03-RQRN",
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
                        "Hostile doxxing, sexual orientation outed against will, or stalking/targeting profile detected. Reject and escalate to Privacy/Legal/Safety."
                    )
                }
            },

            {
                "rule_id": "REG03-RESC",
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
                        "Clear disclosure of sensitive third-party PII (medical, financial, government ID) about an identifiable individual without hostile intent detected. Escalate to Privacy/Legal."
                    )
                }
            },

            {
                "rule_id": "REG03-RNR",
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
                        "Personal contact information (mobile/personal email) of a named third-party with unconfirmed public platform consent, or a partial re-identifiable profile detected. Moderator review required."
                    )
                }
            },

            {
                "rule_id": "REG03-R0",
                "description": "LLM privacy analysis failed; cannot safely pass.",
                "conditions": {"llm_analysis_failed": True},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "ESCALATE",
                    "escalate_to": "Privacy Review",
                    "manual_review_required": True,
                    "confidence_score": 0.50,
                    "reason_template": (
                        "LLM privacy analysis failed. The policy cannot be safely passed because "
                        "sensitive information detection was incomplete. Escalating for manual "
                        "privacy review."
                    )
                }
            },
            {
                "rule_id": "REG03-R1",
                "description": "High-risk sensitive personal disclosure detected — reject.",
                "conditions": {"min_high_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Privacy Review",
                    "manual_review_required": True,
                    "confidence_score": 0.90,
                    "reason_template": (
                        "Non-consensual disclosure of sensitive personal information about an "
                        "identifiable individual was detected. The content poses significant privacy "
                        "risk and must be rejected. Escalate to Privacy team."
                    )
                }
            },
            {
                "rule_id": "REG03-R2",
                "description": "Sensitive personal attribute disclosure without consent — escalate.",
                "conditions": {"min_medium_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "ESCALATE",
                    "escalate_to": "Privacy Review",
                    "manual_review_required": True,
                    "confidence_score": 0.82,
                    "reason_template": (
                        "Content disclosing potentially sensitive personal information about an "
                        "identifiable individual was detected. Human privacy review is required."
                    )
                }
            },
            {
                "rule_id": "REG03-R3",
                "description": "Low-confidence privacy signal — review required.",
                "conditions": {"min_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.68,
                    "reason_template": (
                        "Content that may include private information about an identifiable individual "
                        "was detected. Moderator review is required to assess consent and context."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "consent_cannot_be_verified_from_text",
                "condition": {"always": True},
                "message": (
                    "Whether the individual named or described has consented to this disclosure "
                    "cannot be determined from submitted text alone. Privacy review is required."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "individual_identifiability_not_confirmed",
                "condition": {"always": True},
                "message": (
                    "Whether content refers to a real, identifiable individual cannot be confirmed "
                    "without external verification."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "final_privacy_determination_not_made",
                "condition": {"always": True},
                "message": (
                    "The pipeline does not make final privacy or regulatory determinations. "
                    "All high-severity outputs require human privacy review."
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
            "Detects non-consensual disclosure of private sensitive facts about identifiable individuals.",
            "Classifies disclosures by sensitivity type (health, financial, relationship, belief, etc.).",
            "Escalates confirmed privacy violations to Privacy teams.",
            "Generates moderator-facing reason notes."
        ],
        "what_this_policy_does_not_do": [
            "Does not verify whether individual has consented.",
            "Does not confirm whether subject is a real, identifiable person.",
            "Does not determine jurisdiction-specific privacy law applicability.",
            "Does not make final privacy or regulatory determinations.",
            "Does not detect privacy violations in attached files or images."
        ]
    }
}
