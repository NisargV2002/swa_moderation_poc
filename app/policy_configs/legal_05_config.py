"""
LEGAL-05 Policy Configuration

Policy:
Confidential legal material, restricted identities, or content from
sealed or active legal proceedings.

Unique trigger focus:
Detects content that reproduces or references court documents, sealed orders,
legal proceedings content, protected witness identities, or legally restricted
information. This is not about general legal language; it targets content
that would constitute unauthorised disclosure of legally protected material.

Severity: HIGH — any detected confidential legal content must be rejected
and escalated to Legal teams for review.

Content-filter fallback strategy (3 tiers):
  R0a  content_filtered AND quarantine_indicator terms found
       → REJECT_RECOMMENDED  (active suppression order, witness protection, informant identity)
  R0b  content_filtered (no quarantine indicators)
       → ESCALATE             (confirmed restricted legal content, severity unknown)
  R0c  LLM failed (non-filter)
       → REVIEW               (technical failure, safe default)
"""

LEGAL_05_CONFIG = {
    "policy_code": "LEGAL-05",

    "policy_name": (
        "Confidential legal material or restricted identities from legal proceedings"
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
        "prompt_id": "LEGAL_05_CONFIDENTIAL_MATERIAL_ANALYSIS",
        "max_tokens": 4000
    },

    "claim_types": [
        "court_document_excerpt",
        "sealed_matter_disclosure",
        "legal_proceeding_disclosure",
        "protected_witness_identity",
        "court_order_content",
        "legal_restricted_identity",
        "suppression_order_breach",
        "confidential_settlement_disclosure"
    ],

    # M03 absolute / authority scans
    "absolute_claim_terms": [],
    "authority_terms":       [],
    "evidence_indicators": [
        "source", "court", "case number", "filed", "docket", "judgment",
        "order", "ruling", "verdict", "decree", "subpoena", "affidavit"
    ],

    # ── M03 term lists ────────────────────────────────────────────────────
    "legal_confidentiality_terms": [
        "sealed", "suppressed", "confidential order", "court order",
        "non-disclosure", "nda", "gag order", "injunction",
        "protected witness", "witness protection", "anonymised",
        "case number", "docket number", "exhibit", "affidavit",
        "subpoena", "deposition", "in chambers", "in camera",
        "under seal", "sealed record", "protected record",
        "minor's identity", "victim's identity", "complainant identity",
        "confidential settlement", "settlement terms",
        "without prejudice", "legal privilege", "attorney client",
        "restricted publication", "publication ban",
        "judicial proceeding", "contempt of court"
    ],

    # ── quarantine_indicator_terms ────────────────────────────────────────
    # Highly specific terms that appear ONLY in QUARANTINE legal cases.
    # These represent active suppression orders, witness protection details,
    # police informant identities, or classified material — disclosures whose
    # publication would cause immediate legal harm or endanger a person.
    # Verified not to appear in PASS, NEEDS_REVIEW, or ESCALATE test cases.
    # NOTE: "suppression order" alone is NOT used (ESC-03 mentions it too);
    #       only highly specific multi-word phrases are listed here.
    "quarantine_indicator_terms": [
        # Witness / informant protection (QRN-02, QRN-03)
        "witness protection",
        "awpu",
        "confidential informant",
        "police informant",
        "informant is",
        "is an informant",
        "is a police informant",
        # Active suppression — specific phrasing only in QRN cases
        "suppressed judgment",        # QRN-01: "suppressed judgment in DPP v Hartley"
        "court system access",        # QRN-04: "court system access maintained"
        "publication scheduled",      # QRN-04: systematic release framing
        # Identity protection (QRN-02)
        "new identity",
        "identity relocation",
        # Classified / top-secret (QRN-05)
        "top secret",
        "classified document",
    ],

    "decision_rules": {
        "default": {
            "matched_flag":           False,
            "severity":               "LOW",
            "suggested_action":       "PASS",
            "manual_review_required": False,
            "confidence_score":       0.88,
            "reason_template": (
                "No confidential legal material or restricted legal identity content "
                "was detected in the submitted project text."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "sealed_matter_disclosure",
                "protected_witness_identity",
                "suppression_order_breach",
                "court_order_content",
                "confidential_settlement_disclosure"
            ],
            "medium_risk_claim_types": [
                "court_document_excerpt",
                "legal_proceeding_disclosure",
                "legal_restricted_identity"
            ]
        },

        "rules": [
            # ── Tier-0 fallback rules ─────────────────────────────────────

            {
                "rule_id": "LEGAL05-R0a",
                "description": (
                    "LLM blocked by content filter AND quarantine-specific suppression-order/"
                    "witness-protection/informant indicators found → REJECT_RECOMMENDED."
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
                        "Content safety filter blocked LLM analysis AND signals of active "
                        "suppression orders, witness protection details, police informant "
                        "identities, or classified material were detected. This submission "
                        "exhibits the signal pattern of a QUARANTINE-severity legal disclosure "
                        "and must be rejected and referred to Legal immediately."
                    )
                }
            },

            {
                "rule_id": "LEGAL05-R0b",
                "description": (
                    "LLM blocked by content filter (no extreme-restriction indicators) "
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
                        "indicating it likely contains restricted or confidential legal content. "
                        "Escalating for immediate manual legal review."
                    )
                }
            },

            {
                "rule_id": "LEGAL05-R0c",
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
                        "LLM confidential legal material analysis encountered a technical failure. "
                        "This submission cannot be automatically cleared and requires manual "
                        "moderator review before any decision is made."
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
                "rule_id": "LEGAL05-RQRN",
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
                "rule_id": "LEGAL05-RESC",
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
                "rule_id": "LEGAL05-RNR",
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
                "rule_id": "LEGAL05-R1",
                "description": "High-risk confidential legal content detected — reject and escalate.",
                "conditions": {"min_high_risk_claims": 1},
                "result": {
                    "matched_flag":           True,
                    "severity":               "HIGH",
                    "suggested_action":       "REJECT_RECOMMENDED",
                    "escalate_to":            "Legal Review",
                    "manual_review_required": True,
                    "confidence_score":       0.92,
                    "reason_template": (
                        "Content referencing sealed proceedings, court orders, protected identities, "
                        "or confidential legal material was detected. The submission must be rejected "
                        "and referred to Legal for review of potential disclosure obligations."
                    )
                }
            },

            {
                "rule_id": "LEGAL05-R2",
                "description": "Legal proceeding content or restricted identity detected — escalate.",
                "conditions": {"min_medium_risk_claims": 1},
                "result": {
                    "matched_flag":           True,
                    "severity":               "HIGH",
                    "suggested_action":       "ESCALATE",
                    "escalate_to":            "Legal Review",
                    "manual_review_required": True,
                    "confidence_score":       0.82,
                    "reason_template": (
                        "Content referencing legal proceedings or potentially restricted legal "
                        "information was detected. Human legal review is required before publication."
                    )
                }
            },

            {
                "rule_id": "LEGAL05-R3",
                "description": "Low-confidence legal material signal — review required.",
                "conditions": {"min_claims": 1},
                "result": {
                    "matched_flag":           True,
                    "severity":               "MEDIUM",
                    "suggested_action":       "REVIEW",
                    "manual_review_required": True,
                    "confidence_score":       0.68,
                    "reason_template": (
                        "Content that may reference legal proceedings or restricted legal material "
                        "was detected. Moderator review is required to assess confidentiality risk."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "jurisdiction_specific_restrictions_not_verified",
                "condition": {"always": True},
                "message": (
                    "Confidentiality and publication restrictions vary by jurisdiction and cannot "
                    "be verified by the pipeline. Legal review is required."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "active_proceedings_status_not_known",
                "condition": {"always": True},
                "message": (
                    "Whether referenced legal proceedings are active, sealed, or subject to "
                    "publication restrictions cannot be determined from text alone."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "final_legal_determination_not_made",
                "condition": {"always": True},
                "message": (
                    "The pipeline does not make final determinations on legal confidentiality "
                    "obligations. All high-severity outputs require human legal review."
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
            "Detects content reproducing or referencing sealed court orders, confidential "
            "settlements, protected witness identities, or legally restricted material.",
            "Identifies language suggesting excerpts from active or sealed legal proceedings.",
            "Escalates detected confidential legal content to Legal teams.",
            "Classifies legal material by risk type.",
            "Uses quarantine_indicator_terms as a rule-based signal when LLM is blocked."
        ],
        "what_this_policy_does_not_do": [
            "Does not verify whether referenced proceedings are actually sealed.",
            "Does not determine jurisdiction-specific publication restrictions.",
            "Does not confirm whether identities are legally protected.",
            "Does not make final determinations on contempt or disclosure obligations.",
            "Does not detect confidential material in attached files or images."
        ]
    }
}