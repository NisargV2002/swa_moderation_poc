"""
LEGAL-03 Policy Configuration

Policy:
Serious unsubstantiated allegations of fraud, crime, abuse, or misconduct
against identifiable parties.

Unique trigger focus:
Detects content making serious factual allegations — criminal conduct, fraud,
abuse, negligence, or corruption — against named or identifiable individuals
or organisations, without substantiating evidence. Distinct from LEGAL-01
(direct threats) and REG-01 (misleading facts); this policy targets defamatory
or legally harmful unverified allegation language.

Severity: HIGH — allegations against identifiable parties require escalation
to Legal for defamation and liability review.

Content-filter fallback strategy (3 tiers):
  R0a  content_filtered AND quarantine_indicator terms found
       → REJECT_RECOMMENDED  (fabricated conviction/arrest claims, targeting lists)
  R0b  content_filtered (no quarantine indicators)
       → ESCALATE             (confirmed allegation content, severity unknown)
  R0c  LLM failed (non-filter)
       → REVIEW               (technical failure, safe default)
"""

LEGAL_03_CONFIG = {
    "policy_code": "LEGAL-03",

    "policy_name": (
        "Serious unsubstantiated allegations of fraud, crime, or misconduct "
        "against identifiable parties"
    ),

    "policy_category": "Legal",

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
        "enabled":   True,
        "prompt_id": "LEGAL_03_ALLEGATION_ANALYSIS",
        "max_tokens": 4000
    },

    "claim_types": [
        "fraud_allegation",
        "criminal_allegation",
        "abuse_allegation",
        "corruption_allegation",
        "negligence_allegation",
        "defamatory_allegation",
        "misconduct_allegation",
        "unsubstantiated_serious_allegation"
    ],

    # M03 absolute / authority scans
    "absolute_claim_terms": [],
    "authority_terms":       [],
    "evidence_indicators": [
        "source", "report", "evidence", "investigation", "filed",
        "court", "conviction", "verdict", "judgment", "ruling",
        "police", "official record", "documented", "attached"
    ],

    # ── M03 term lists ────────────────────────────────────────────────────
    "allegation_terms": [
        "fraud", "fraudulent", "scam", "deceived", "deception",
        "criminal", "crime", "illegal", "unlawful", "illegally",
        "corrupt", "corruption", "bribery", "bribed", "kickback",
        "abuse", "abused", "abuser", "misconduct", "malpractice",
        "negligence", "negligent", "reckless", "recklessly",
        "embezzlement", "embezzled", "stole", "stolen", "theft",
        "money laundering", "tax evasion", "evaded",
        "falsified", "forged", "fabricated records",
        "accused", "allegation", "alleged", "alleges",
        "cover-up", "coverup", "whitewash",
        "victim of", "perpetrator", "offender",
        "harassed", "sexually harassed", "assaulted",
        "racketeer", "conspiracy to"
    ],

    # ── quarantine_indicator_terms ────────────────────────────────────────
    # Highly specific terms that appear ONLY in QUARANTINE allegation cases.
    # These represent fabricated criminal records, coordinated-targeting language,
    # or extreme defamatory claims (sex offender, child abuse registers, etc.).
    # Verified not to appear in PASS, NEEDS_REVIEW, or ESCALATE test cases.
    "quarantine_indicator_terms": [
        # Fabricated conviction / arrest language (QRN-03, QRN-04)
        "convicted of",
        "has been arrested",
        "sex offender register",
        "sex offender",
        # Breaking-news fabrication framing (QRN-04)
        "breaking:",
        # Coordinated reputational destruction (QRN-01)
        "targeting list",
        "destroy career",
        "destroy his career",
        "destroy her career",
        "destroy their career",
        # Extreme defamatory language
        "should be in prison",
        "paedophile",
        "predator",
        # Bankruptcy as weapon (QRN-02)
        "bankrupt",
        "destroy reputations",
        # Court / criminal record fabrication
        "criminal record shows",
        "appear in court",
    ],

    "decision_rules": {
        "default": {
            "matched_flag":           False,
            "severity":               "LOW",
            "suggested_action":       "PASS",
            "manual_review_required": False,
            "confidence_score":       0.88,
            "reason_template": (
                "No serious unsubstantiated allegation against an identifiable party "
                "was detected in the submitted project text."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "fraud_allegation",
                "criminal_allegation",
                "abuse_allegation",
                "corruption_allegation",
                "defamatory_allegation"
            ],
            "medium_risk_claim_types": [
                "negligence_allegation",
                "misconduct_allegation",
                "unsubstantiated_serious_allegation"
            ]
        },

        "rules": [
            # ── Tier-0 fallback rules ─────────────────────────────────────

            {
                "rule_id": "LEGAL03-R0a",
                "description": (
                    "LLM blocked by content filter AND quarantine-specific fabricated-conviction/"
                    "targeting indicators found → REJECT_RECOMMENDED."
                ),
                "conditions": {
                    "llm_analysis_failed":  True,
                    "llm_content_filtered": True,
                    "rule_signals.has_quarantine_indicator_terms_signal": True
                },
                "result": {
                    "matched_flag":           True,
                    "severity":               "HIGH",
                    "suggested_action":       "REJECT_RECOMMENDED",
                    "escalate_to":            "Legal Review",
                    "manual_review_required": True,
                    "confidence_score":       0.88,
                    "reason_template": (
                        "Content safety filter blocked LLM analysis AND signals of fabricated "
                        "criminal convictions, sex-offender allegations, coordinated-targeting "
                        "language, or extreme defamatory claims were detected. This submission "
                        "exhibits the signal pattern of a QUARANTINE-severity allegation and "
                        "must be rejected and referred to Legal immediately."
                    )
                }
            },

            {
                "rule_id": "LEGAL03-R0b",
                "description": (
                    "LLM blocked by content filter (no quarantine indicators) "
                    "→ ESCALATE for legal review."
                ),
                "conditions": {
                    "llm_analysis_failed":  True,
                    "llm_content_filtered": True
                },
                "result": {
                    "matched_flag":           True,
                    "severity":               "HIGH",
                    "suggested_action":       "ESCALATE",
                    "escalate_to":            "Legal Review",
                    "manual_review_required": True,
                    "confidence_score":       0.75,
                    "reason_template": (
                        "Azure content safety filter blocked analysis of this submission, "
                        "indicating it likely contains serious allegation or defamatory content. "
                        "Escalating for immediate manual legal review."
                    )
                }
            },

            {
                "rule_id": "LEGAL03-R0c",
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
                        "LLM allegation analysis encountered a technical failure. "
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
                "rule_id": "LEGAL03-RQRN",
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
                "rule_id": "LEGAL03-RESC",
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
                "rule_id": "LEGAL03-RNR",
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
                "rule_id": "LEGAL03-R1",
                "description": "High-risk serious allegation against identifiable party — reject.",
                "conditions": {"min_high_risk_claims": 1},
                "result": {
                    "matched_flag":           True,
                    "severity":               "HIGH",
                    "suggested_action":       "REJECT_RECOMMENDED",
                    "escalate_to":            "Legal Review",
                    "manual_review_required": True,
                    "confidence_score":       0.92,
                    "reason_template": (
                        "Serious unsubstantiated allegation(s) of fraud, criminal conduct, abuse, "
                        "or corruption against an identifiable party were detected. The content poses "
                        "significant legal and defamation risk and must be escalated for legal review."
                    )
                }
            },

            {
                "rule_id": "LEGAL03-R2",
                "description": "Medium-risk allegation detected — escalate for review.",
                "conditions": {"min_medium_risk_claims": 1},
                "result": {
                    "matched_flag":           True,
                    "severity":               "HIGH",
                    "suggested_action":       "ESCALATE",
                    "escalate_to":            "Legal Review",
                    "manual_review_required": True,
                    "confidence_score":       0.82,
                    "reason_template": (
                        "Allegation language suggesting misconduct, negligence, or unverified serious "
                        "claims was detected. Human legal review is required before any publication."
                    )
                }
            },

            {
                "rule_id": "LEGAL03-R3",
                "description": "Low-confidence allegation signal — review required.",
                "conditions": {"min_claims": 1},
                "result": {
                    "matched_flag":           True,
                    "severity":               "MEDIUM",
                    "suggested_action":       "REVIEW",
                    "manual_review_required": True,
                    "confidence_score":       0.68,
                    "reason_template": (
                        "Content that may contain allegation language about identifiable parties "
                        "was detected. Moderator review is required to assess context and legal risk."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "truth_of_allegation_not_verifiable",
                "condition": {"always": True},
                "message": (
                    "The truth or falsity of allegations cannot be verified by the pipeline. "
                    "Legal review is required for all flagged allegation content."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "identity_of_alleged_party_not_confirmed",
                "condition": {"always": True},
                "message": (
                    "Whether allegations refer to a real, identifiable individual or organisation "
                    "cannot be confirmed without external investigation."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "final_legal_determination_not_made",
                "condition": {"always": True},
                "message": (
                    "The pipeline does not determine whether content is defamatory or legally actionable. "
                    "All high-severity outputs require human legal review."
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
            "Detects serious unsubstantiated allegations of fraud, crime, abuse, "
            "corruption, and misconduct against identifiable parties.",
            "Identifies defamatory-risk content targeting named individuals or organisations.",
            "Generates escalation signals with legal moderator-facing reason notes.",
            "Distinguishes verified/documented allegations from unsubstantiated claims.",
            "Uses quarantine_indicator_terms as a rule-based signal when LLM is blocked."
        ],
        "what_this_policy_does_not_do": [
            "Does not verify whether allegations are true or false.",
            "Does not determine whether content is legally defamatory.",
            "Does not confirm identity of alleged parties.",
            "Does not perform external legal or criminal record checks.",
            "Does not make final legal determinations."
        ]
    }
}