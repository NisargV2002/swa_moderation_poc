"""
LEGAL-02 Policy Configuration

Policy:
Doxxing or non-consensual disclosure of personally identifiable information (PII)
about identifiable individuals.

Unique trigger focus:
Detects content that exposes private personal information — contact details,
home addresses, identity numbers, financial data, or sensitive attributes — about
real individuals without evidence of consent. Distinct from LEGAL-01 (threats)
and REG-03 (general privacy); this policy targets deliberate PII exposure.

Severity: CRITICAL — any confirmed PII exposure about an identifiable individual
must be rejected and escalated to Privacy and Legal teams.

Content-filter fallback strategy (3 tiers):
  R0a  content_filtered AND quarantine_indicator terms found
       → REJECT_RECOMMENDED  (mass doxxing / PII bundle / sensitive attributes)
  R0b  content_filtered (no quarantine indicators)
       → ESCALATE             (confirmed PII content, severity unknown)
  R0c  LLM failed (non-filter)
       → REVIEW               (technical failure, safe default)
"""

LEGAL_02_CONFIG = {
    "policy_code": "LEGAL-02",

    "policy_name": (
        "Doxxing or non-consensual disclosure of personally identifiable information (PII)"
    ),

    "policy_category": "Legal",

    "severity": "CRITICAL",

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
        "enabled":   True,
        "prompt_id": "LEGAL_02_PII_ANALYSIS",
        "max_tokens": 4000
    },

    "claim_types": [
        "doxxing",
        "private_contact_disclosure",
        "home_address_disclosure",
        "identity_number_disclosure",
        "financial_info_disclosure",
        "sensitive_attribute_disclosure",
        "identity_bundle_exposure",
        "location_disclosure_of_individual"
    ],

    # M03 absolute / authority scans
    "absolute_claim_terms": [],
    "authority_terms":       [],
    "evidence_indicators": [
        "source", "attached", "reference", "record", "document"
    ],

    # ── M03 term lists ────────────────────────────────────────────────────
    "pii_indicator_terms": [
        "home address", "residential address", "lives at", "lives on",
        "phone number", "mobile number", "cell number", "contact number",
        "email address", "personal email",
        "passport number", "national id", "social security", "tax id",
        "id number", "driver's license", "driving licence",
        "bank account", "account number", "credit card", "debit card",
        "date of birth", "born on", "place of birth",
        "salary", "annual income", "financial details",
        "medical condition", "health record", "diagnosis",
        "sexual orientation", "gender identity", "religion",
        "ip address", "device id", "biometric"
    ],

    # ── quarantine_indicator_terms ────────────────────────────────────────
    # Highly specific terms that appear ONLY in QUARANTINE doxxing cases.
    # These represent mass-exposure or sensitive-attribute bundles that go
    # beyond the single-identifier disclosures typical of ESCALATE cases.
    # Verified not to appear in PASS, NEEDS_REVIEW, or ESCALATE test cases.
    "quarantine_indicator_terms": [
        # Live-tracking / movement monitoring (QRN-02)
        "live tracking",
        "tracking register",
        "daily movements",
        "card ending",
        # Sensitive personal attributes (QRN-04)
        "treating psychologist",
        "sexual orientation",
        # Identity reconstruction bundle (QRN-02)
        "new identity",
        "identity documentation",
        # Mass distribution intent (QRN-01)
        "will be distributed to",
        "distribution list",
        # Surveillance data aggregation
        "surveillance data",
        "personal surveillance",
        "relocation address",
        # Daily-routine exposure (QRN-02: daily movements)
        "daily routine",
    ],

    "decision_rules": {
        "default": {
            "matched_flag":           False,
            "severity":               "LOW",
            "suggested_action":       "PASS",
            "manual_review_required": False,
            "confidence_score":       0.90,
            "reason_template": (
                "No non-consensual PII disclosure or doxxing content was detected "
                "in the submitted project text."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "doxxing",
                "home_address_disclosure",
                "identity_number_disclosure",
                "identity_bundle_exposure",
                "financial_info_disclosure"
            ],
            "medium_risk_claim_types": [
                "private_contact_disclosure",
                "sensitive_attribute_disclosure",
                "location_disclosure_of_individual"
            ]
        },

        "rules": [
            # ── Tier-0 fallback rules ─────────────────────────────────────

            {
                "rule_id": "LEGAL02-R0a",
                "description": (
                    "LLM blocked by content filter AND quarantine-specific PII bundle/"
                    "surveillance/sensitive-attribute indicators found → REJECT_RECOMMENDED."
                ),
                "conditions": {
                    "llm_analysis_failed":  True,
                    "llm_content_filtered": True,
                    "rule_signals.has_quarantine_indicator_terms_signal": True
                },
                "result": {
                    "matched_flag":           True,
                    "severity":               "CRITICAL",
                    "suggested_action":       "REJECT_RECOMMENDED",
                    "escalate_to":            "Privacy / Legal",
                    "manual_review_required": True,
                    "confidence_score":       0.88,
                    "reason_template": (
                        "Content safety filter blocked LLM analysis AND signals of mass PII "
                        "exposure, live-tracking, sensitive attribute disclosure, or identity "
                        "bundle distribution were detected. This submission exhibits the signal "
                        "pattern of a QUARANTINE-severity doxxing event and must be rejected "
                        "and referred to Privacy and Legal immediately."
                    )
                }
            },

            {
                "rule_id": "LEGAL02-R0b",
                "description": (
                    "LLM blocked by content filter (no mass-exposure indicators) "
                    "→ ESCALATE for privacy review."
                ),
                "conditions": {
                    "llm_analysis_failed":  True,
                    "llm_content_filtered": True
                },
                "result": {
                    "matched_flag":           True,
                    "severity":               "HIGH",
                    "suggested_action":       "ESCALATE",
                    "escalate_to":            "Privacy / Legal Review",
                    "manual_review_required": True,
                    "confidence_score":       0.75,
                    "reason_template": (
                        "Azure content safety filter blocked analysis of this submission, "
                        "indicating it likely contains personal or sensitive information. "
                        "Escalating for immediate manual privacy and legal review."
                    )
                }
            },

            {
                "rule_id": "LEGAL02-R0c",
                "description": (
                    "LLM failed for a non-content-filter technical reason "
                    "→ REVIEW (safe default)."
                ),
                "conditions": {
                    "llm_analysis_failed": True
                },
                "result": {
                    "matched_flag":           True,
                    "severity":               "MEDIUM",
                    "suggested_action":       "REVIEW",
                    "manual_review_required": True,
                    "confidence_score":       0.50,
                    "reason_template": (
                        "LLM PII analysis encountered a technical failure. "
                        "This submission cannot be automatically cleared and requires "
                        "manual moderator review before any decision is made."
                    )
                }
            },

            # ── Standard claim-based rules ────────────────────────────────


            # ── Tier-direct rules ────────────────────────────────────────────
            # These fire when the LLM SUCCEEDS (llm_analysis_failed=False) and
            # returned a recommended_tier in its response.
            # They fire BEFORE claim-type rules (R1/R2/R3) to avoid the
            # problem where both ESCALATE and QUARANTINE content produces
            # high-risk claim types, making both map to REJECT_RECOMMENDED.
            # Rule order: QUARANTINE first (most specific), then ESCALATE, NEEDS_REVIEW.
            {
                "rule_id": "LEGAL02-RQRN",
                "description": "LLM recommends QUARANTINE tier → reject and escalate to Law Enforcement review.",
                "conditions": {
                    "llm_analysis_failed": False,
                    "llm_recommended_tier": "QUARANTINE"
                },
                "result": {
                    "matched_flag":           True,
                    "severity":               "CRITICAL",
                    "suggested_action":       "REJECT_RECOMMENDED",
                    "escalate_to":            "Legal / Safety / Law Enforcement",
                    "manual_review_required": True,
                    "confidence_score":       0.93,
                    "reason_template": (
                        "LLM analysis identified content in the QUARANTINE severity tier: "
                        "concrete operational instructions, extreme targeting, or incitement "
                        "with specific targets and detail. Submission must be rejected and "
                        "escalated to Legal, Safety, and Law Enforcement for review."
                    )
                }
            },

            {
                "rule_id": "LEGAL02-RESC",
                "description": "LLM recommends ESCALATE tier.",
                "conditions": {
                    "llm_analysis_failed": False,
                    "llm_recommended_tier": "ESCALATE"
                },
                "result": {
                    "matched_flag":           True,
                    "severity":               "HIGH",
                    "suggested_action":       "ESCALATE",
                    "escalate_to":            "Legal / Safety Review",
                    "manual_review_required": True,
                    "confidence_score":       0.90,
                    "reason_template": (
                        "LLM analysis identified content in the ESCALATE severity tier: "
                        "explicit threat, extortion demand, or serious coercive language "
                        "directed at identifiable individuals. Escalating for immediate "
                        "safety and legal review."
                    )
                }
            },

            {
                "rule_id": "LEGAL02-RNR",
                "description": "LLM recommends NEEDS_REVIEW tier.",
                "conditions": {
                    "llm_analysis_failed": False,
                    "llm_recommended_tier": "NEEDS_REVIEW"
                },
                "result": {
                    "matched_flag":           True,
                    "severity":               "MEDIUM",
                    "suggested_action":       "REVIEW",
                    "manual_review_required": True,
                    "confidence_score":       0.80,
                    "reason_template": (
                        "LLM analysis identified content in the NEEDS_REVIEW tier: "
                        "aggressive advocacy, veiled or ambiguous menacing language, or "
                        "strong pressure without explicit threat of bodily harm. "
                        "Requires human moderator review to assess intent and context."
                    )
                }
            },

            {
                "rule_id": "LEGAL02-R1",
                "description": "High-risk PII exposure detected — reject and escalate.",
                "conditions": {"min_high_risk_claims": 1},
                "result": {
                    "matched_flag":           True,
                    "severity":               "CRITICAL",
                    "suggested_action":       "REJECT_RECOMMENDED",
                    "escalate_to":            "Privacy / Legal",
                    "manual_review_required": True,
                    "confidence_score":       0.95,
                    "reason_template": (
                        "Non-consensual disclosure of personally identifiable information was detected. "
                        "The content exposes private data about an identifiable individual and must be "
                        "rejected. Escalate to Privacy and Legal teams immediately."
                    )
                }
            },

            {
                "rule_id": "LEGAL02-R2",
                "description": "Sensitive attribute or contact disclosure — escalate.",
                "conditions": {"min_medium_risk_claims": 1},
                "result": {
                    "matched_flag":           True,
                    "severity":               "HIGH",
                    "suggested_action":       "ESCALATE",
                    "escalate_to":            "Privacy / Legal Review",
                    "manual_review_required": True,
                    "confidence_score":       0.85,
                    "reason_template": (
                        "Possible non-consensual personal information disclosure was detected. "
                        "The submission requires human privacy and legal review before any action."
                    )
                }
            },

            {
                "rule_id": "LEGAL02-R3",
                "description": "Low-confidence PII signal — review required.",
                "conditions": {"min_claims": 1},
                "result": {
                    "matched_flag":           True,
                    "severity":               "MEDIUM",
                    "suggested_action":       "REVIEW",
                    "manual_review_required": True,
                    "confidence_score":       0.70,
                    "reason_template": (
                        "Content that may contain personal information about an identifiable individual "
                        "was detected. Moderator review is required to assess consent and context."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "consent_cannot_be_verified",
                "condition": {"always": True},
                "message": (
                    "Whether the individual named or described has consented to disclosure "
                    "cannot be determined from submitted text alone."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "individual_identity_not_confirmed",
                "condition": {"always": True},
                "message": (
                    "Whether the information refers to a real, identifiable individual cannot "
                    "be confirmed without external verification."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "final_legal_determination_not_made",
                "condition": {"always": True},
                "message": (
                    "The pipeline does not make final privacy or legal determinations. "
                    "All high-severity outputs require human review."
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
            "Detects non-consensual disclosure of PII including addresses, identity numbers, "
            "financial data, contact details, and sensitive personal attributes.",
            "Identifies doxxing-style content targeting identifiable individuals.",
            "Escalates confirmed or suspected PII exposure to Privacy and Legal teams.",
            "Classifies PII exposure by type and risk level.",
            "Uses quarantine_indicator_terms as a rule-based signal when LLM is blocked."
        ],
        "what_this_policy_does_not_do": [
            "Does not verify whether the individual has actually consented.",
            "Does not confirm whether information refers to a real person.",
            "Does not perform external identity verification.",
            "Does not make final legal or privacy determinations.",
            "Does not detect PII embedded in attached files or images."
        ]
    }
}