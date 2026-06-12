"""
REG-02 Policy Configuration

Policy:
Unsubstantiated comparative or superlative claims (best/only/guaranteed/certified)
without supporting evidence.

Unique trigger focus:
REG-01 targets materially misleading factual claims broadly (statistics, distortions,
environmental assertions). REG-02 is specifically triggered by strong WORDING —
superlatives, absolutes, guarantees, exclusivity claims, and certification language —
even when those words appear in otherwise ordinary project descriptions.

The LLM validates whether each triggered span is actually making a REG-02 claim
(e.g. "best" used in a genuine superiority claim vs. "best efforts" which is not).

Important:
- Uses the same generic moderation modules as TYPE-PROJECT-01 and REG-01.
- No new module files are needed.
- M03 reads superlative_trigger_terms, certification_terms, exclusivity_terms,
  and guarantee_terms automatically via EXTRA_TERM_LIST_KEYS.
"""

REG_02_CONFIG = {
    "policy_code": "REG-02",

    "policy_name": (
        "Unsubstantiated comparative or superlative claims "
        "(best/only/guaranteed/certified) without evidence"
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
        "prompt_id": "REG_02_CLAIM_ANALYSIS",
        "max_tokens": 4500
    },

    "claim_types": [
        "superlative_claim",
        "comparative_claim",
        "exclusivity_claim",
        "guarantee_claim",
        "certification_or_compliance_claim",
        "authority_backed_absolute_claim",
        "unsubstantiated_absolute_wording"
    ],

    # ------------------------------------------------------------------ #
    # M03 EXTRA_TERM_LIST_KEYS — these four lists are picked up
    # automatically by m03_rule_signals.py. Each produces two signals:
    #   <key>_found: [matched terms]
    #   has_<key>_signal: bool
    # ------------------------------------------------------------------ #
    "superlative_trigger_terms": [
        "best", "top", "#1", "number 1", "number one",
        "leading", "world-class", "world class",
        "world-leading", "world leading",
        "industry-leading", "industry leading",
        "market-leading", "market leading",
        "highest rated", "top rated",
        "most effective", "most successful",
        "most impactful", "most trusted",
        "most recognised", "most recognized"
    ],

    "certification_terms": [
        "certified", "accredited",
        "officially approved", "officially recognised", "officially recognized",
        "officially endorsed",
        "compliant", "compliance", "in compliance",
        "fully compliant", "certified compliant",
        "iso certified", "iso accredited",
        "verified", "externally verified",
        "third-party verified", "third party verified",
        "audited", "externally audited"
    ],

    "exclusivity_terms": [
        "only", "unique", "one-of-a-kind", "one of a kind",
        "exclusive", "exclusively", "sole provider",
        "the only", "no other", "unlike any other",
        "first of its kind", "first in the world",
        "first in the country", "first in the region"
    ],

    "guarantee_terms": [
        "guaranteed", "guarantee", "assured", "100%",
        "always", "never fails", "zero failure",
        "certain", "certainty",
        "definite outcomes", "definitive results",
        "proven results", "proven outcomes",
        "will deliver", "will achieve", "will succeed"
    ],

    # Standard lists also used by M03 existing logic
    "evidence_indicators": [
        "source", "according to", "report", "study", "audit",
        "certificate", "certification", "approval number",
        "grant id", "reference", "citation", "link", "url",
        "attached", "attachment", "evidence uploaded", "see report",
        "verified by", "validated by", "published by",
        "survey", "dataset", "baseline", "methodology",
        "accreditation number", "iso number", "registration number"
    ],

    "authority_terms": [
        "government", "ministry", "council", "regulator", "authority",
        "united nations", "un ", "world bank", "university",
        "research institute", "official body", "certification body",
        "approved by", "endorsed by", "funded by", "partnered with",
        "recognised by", "recognized by"
    ],

    "absolute_claim_terms": [
        "guaranteed", "proven", "certified", "accredited",
        "officially approved", "100%", "best", "only", "#1",
        "number one", "world-class", "industry-leading",
        "fully compliant", "always", "never fails", "zero failure",
        "exclusive", "the only", "first of its kind"
    ],

    "decision_rules": {
        "default": {
            "matched_flag": False,
            "severity": "LOW",
            "suggested_action": "PASS",
            "manual_review_required": False,
            "confidence_score": 0.83,
            "reason_template": (
                "No unsubstantiated comparative, superlative, guarantee, or "
                "certification-style claim was detected in the submitted project text."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "guarantee_claim",
                "certification_or_compliance_claim",
                "authority_backed_absolute_claim",
                "exclusivity_claim"
            ],
            "medium_risk_claim_types": [
                "superlative_claim",
                "comparative_claim",
                "unsubstantiated_absolute_wording"
            ]
        },

        "rules": [

            # ── Tier-direct rules (fire before claim-count rules) ──────────────────
            # When the LLM returns recommended_tier, use it directly so M16 does not
            # fall through to raw claim-count rules that are miscalibrated for REG.
            {
                "rule_id": "REG02-RPASS",
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
                        "No absolute superlative, guarantee, or unsubstantiated certification claim detected, or all such wording is properly qualified or evidenced."
                    )
                }
            },

            {
                "rule_id": "REG02-RQRN",
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
                        "Fraudulent guarantee/certification combined with financial fraud or phishing. Reject and escalate."
                    )
                }
            },

            {
                "rule_id": "REG02-RESC",
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
                        "Fraudulent certification or authority claim without verifiable proof detected. Escalate to Regulatory/Legal for review."
                    )
                }
            },

            {
                "rule_id": "REG02-RNR",
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
                        "Absolute superlative, guarantee, or exclusivity wording without supporting evidence detected. Amendment required to add qualification or evidence."
                    )
                }
            },

            {
                "rule_id": "REG02-R0",
                "description": (
                    "LLM semantic claim analysis failed; the policy cannot safely pass."
                ),
                "conditions": {"llm_analysis_failed": True},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.45,
                    "reason_template": (
                        "LLM comparative/superlative claim analysis failed. "
                        "The policy cannot be safely passed because strong-wording "
                        "detection was incomplete."
                    )
                }
            },
            {
                "rule_id": "REG02-R1",
                "description": (
                    "High-risk absolute claim (guarantee, certification, exclusivity) "
                    "without supporting evidence — escalate."
                ),
                "conditions": {"min_high_risk_claims": 1, "min_evidence_issues": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "ESCALATE",
                    "escalate_to": "Human Moderator / Regulatory Review",
                    "manual_review_required": True,
                    "confidence_score": 0.91,
                    "reason_template": (
                        "A high-risk absolute, guarantee, or certification-style claim was "
                        "detected without visible supporting evidence or accreditation proof. "
                        "The wording may materially mislead audiences and should be escalated "
                        "for human regulatory review."
                    )
                }
            },
            {
                "rule_id": "REG02-R2",
                "description": (
                    "Claim requires evidence but none detected — request amendment."
                ),
                "conditions": {"min_evidence_issues": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "REQUEST_AMENDMENT",
                    "manual_review_required": True,
                    "confidence_score": 0.86,
                    "reason_template": (
                        "Strong wording (comparative, superlative, guarantee, or "
                        "certification-style) was detected, but supporting evidence "
                        "or accreditation proof was not found in the submitted text. "
                        "Request evidence, qualified-language replacement, or claim revision."
                    )
                }
            },
            {
                "rule_id": "REG02-R3",
                "description": (
                    "High-risk absolute claim even with some evidence — review still needed."
                ),
                "conditions": {"min_high_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.79,
                    "reason_template": (
                        "High-risk absolute, guarantee, or certification-style claim(s) "
                        "were detected. Moderator review is recommended because the current "
                        "POC does not verify certification numbers, guarantee validity, or "
                        "accreditation authenticity."
                    )
                }
            },
            {
                "rule_id": "REG02-R4",
                "description": (
                    "Comparative or superlative wording detected — review recommended."
                ),
                "conditions": {"min_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.71,
                    "reason_template": (
                        "Comparative or superlative claim wording was detected. "
                        "Moderator review is recommended to assess whether the wording "
                        "should be softened with qualifying language or supported with evidence."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "certification_documents_not_provided",
                "condition": {"input_coverage.attachments_available": False},
                "message": (
                    "Certification or accreditation documents were not provided; "
                    "claimed certifications cannot be confirmed from submitted text alone."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "external_accreditation_check_not_performed",
                "condition": {"always": True},
                "message": (
                    "External accreditation or certification number verification was not "
                    "performed; certification-style claims are assessed only from wording "
                    "in submitted text."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "guarantee_validity_not_verified",
                "condition": {"always": True},
                "message": (
                    "Guarantee validity was not verified externally; guarantee-style "
                    "claims are assessed only from wording and context."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "comparative_truth_not_verified",
                "condition": {"always": True},
                "message": (
                    "Whether the project is genuinely 'best', 'leading', or '#1' was not "
                    "verified externally; comparative/superlative claims are assessed only "
                    "by wording and available evidence in submitted text."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "final_regulatory_determination_not_made",
                "condition": {"always": True},
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
        "current_scope": (
            "Project-only moderation for current POC."
        ),
        "difference_from_reg_01": (
            "REG-01 targets materially misleading factual claims broadly "
            "(statistics, distortions, environmental impact). "
            "REG-02 specifically targets WORDING PATTERNS — superlatives, absolutes, "
            "guarantees, and certification language — even when no explicit statistic "
            "or factual claim is present."
        ),
        "what_this_policy_does": [
            "Detects superlative, absolute, guarantee, exclusivity, and certification-style wording.",
            "Validates whether triggered wording is actually a REG-02 claim.",
            "Classifies claim strength (weak / moderate / strong).",
            "Estimates whether evidence or accreditation proof is required.",
            "Detects visible certification or evidence indicators in submitted text.",
            "Suggests qualified-language replacements or requests amendment.",
            "Generates moderator-facing reason notes and suggested action."
        ],
        "what_this_policy_does_not_do": [
            "Does not verify that 'best' or 'leading' is actually true.",
            "Does not validate certification numbers externally.",
            "Does not confirm guarantees are legally enforceable.",
            "Does not determine final legal or regulatory breach."
        ]
    }
}