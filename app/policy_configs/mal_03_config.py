"""
MAL-03 Policy Configuration

Policy:
Impersonation of government bodies, regulators, official partners,
or trusted organisations.

Unique trigger focus:
Detects content falsely presenting itself as — or claiming affiliation with —
government agencies, official regulators, SWA partners, international bodies,
or other trusted organisations without legitimate authorisation. Distinct from
MAL-01 (phishing/scam) and LEGAL-03 (allegations); this policy targets
identity fraud through false official affiliation claims.

Severity: HIGH — confirmed impersonation must be rejected and escalated
to Risk and Compliance teams.
"""

MAL_03_CONFIG = {
    "policy_code": "MAL-03",

    "policy_name": (
        "Impersonation of government bodies, regulators, or official partners"
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
        "prompt_id": "MAL_03_IMPERSONATION_ANALYSIS",
        "max_tokens": 4000
    },

    "claim_types": [
        "government_body_impersonation",
        "regulator_impersonation",
        "official_partner_impersonation",
        "international_body_impersonation",
        "false_official_affiliation_claim",
        "unauthorised_use_of_official_name",
        "fake_government_programme"
    ],

    # M03 absolute / authority scans
    "absolute_claim_terms": [
        "official", "officially", "government", "government-run",
        "government-backed", "government-approved", "ministry",
        "department of", "agency", "regulatory authority"
    ],

    "authority_terms": [
        "government", "ministry", "council", "regulator",
        "authority", "united nations", "un", "world bank",
        "parliament", "senate", "department", "federal",
        "official body", "certification body",
        "approved by", "endorsed by", "funded by",
        "partnered with", "recognised by", "recognized by",
        "interpol", "europol", "oecd", "imf", "who", "unicef",
        "fda", "sec", "irs", "hmrc", "asic", "fca"
    ],

    "evidence_indicators": [
        "official letter", "authorisation letter", "mou", "memorandum",
        "signed agreement", "partnership certificate", "official document",
        "reference number", "accreditation number"
    ],

    # M03 EXTRA_TERM_LIST_KEYS — auto-scanned by m03_rule_signals.py
    "impersonation_terms": [
        "on behalf of the government", "acting on behalf of",
        "representing the government", "representing the ministry",
        "authorised representative", "official representative",
        "government initiative", "government programme", "government project",
        "ministry-approved", "ministry-funded", "ministry-backed",
        "un programme", "un project", "un initiative",
        "world bank project", "world bank funded",
        "officially launched by", "officially endorsed by",
        "official partner of", "certified partner of",
        "registered with the government", "listed by the government",
        "regulatory approved", "regulator-sanctioned",
        "government grant recipient", "official grant holder",
        "swa official", "swa authorised", "swa endorsed",
        "this is an official", "official notice", "official statement"
    ],

    "decision_rules": {
        "default": {
            "matched_flag": False,
            "severity": "LOW",
            "suggested_action": "PASS",
            "manual_review_required": False,
            "confidence_score": 0.88,
            "reason_template": (
                "No government, regulator, or official partner impersonation was detected "
                "in the submitted project text."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "government_body_impersonation",
                "regulator_impersonation",
                "international_body_impersonation",
                "fake_government_programme",
                "unauthorised_use_of_official_name"
            ],
            "medium_risk_claim_types": [
                "official_partner_impersonation",
                "false_official_affiliation_claim"
            ]
        },

        "rules": [

            # ── Tier-direct rules (fire before claim-count rules) ──────────────────
            # When the LLM returns recommended_tier, use it directly so M16 does not
            # fall through to raw claim-count rules that are miscalibrated for MAL.
            {
                "rule_id": "MAL03-RPASS",
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
                        "No impersonation detected; affiliation claims are realistic local council, municipal, or academic partnerships."
                    )
                }
            },

            {
                "rule_id": "MAL03-RQRN",
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
                        "Government/regulator impersonation combined with legal-prosecution or penalty threats and credential/payment harvesting. Reject and quarantine immediately."
                    )
                }
            },

            {
                "rule_id": "MAL03-RESC",
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
                        "Falsely claims to BE an official government/international body or its official branch (forged identity). Escalate to Compliance."
                    )
                }
            },

            {
                "rule_id": "MAL03-RNR",
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
                        "Claims backing or recommendation by a named authority without verifiable credentials or citations. Flag for affiliation verification."
                    )
                }
            },

            {
                "rule_id": "MAL03-R0",
                "description": "LLM impersonation analysis failed; cannot safely pass.",
                "conditions": {"llm_analysis_failed": True},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "ESCALATE",
                    "escalate_to": "Risk / Compliance Review",
                    "manual_review_required": True,
                    "confidence_score": 0.50,
                    "reason_template": (
                        "LLM impersonation analysis failed. The policy cannot be safely passed "
                        "because official-identity detection was incomplete. Escalating for "
                        "manual risk and compliance review."
                    )
                }
            },
            {
                "rule_id": "MAL03-R1",
                "description": "High-risk government or regulator impersonation detected — reject.",
                "conditions": {"min_high_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Risk / Compliance",
                    "manual_review_required": True,
                    "confidence_score": 0.92,
                    "reason_template": (
                        "Impersonation of a government body, regulator, or international organisation "
                        "was detected. The submission makes unauthorised official affiliation claims "
                        "and must be rejected. Escalate to Risk and Compliance teams."
                    )
                }
            },
            {
                "rule_id": "MAL03-R2",
                "description": "Unverified official affiliation claim — escalate for review.",
                "conditions": {"min_medium_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "ESCALATE",
                    "escalate_to": "Risk / Compliance Review",
                    "manual_review_required": True,
                    "confidence_score": 0.82,
                    "reason_template": (
                        "Unverified official partnership or affiliation claim was detected. "
                        "The submission requires risk and compliance review to verify authenticity."
                    )
                }
            },
            {
                "rule_id": "MAL03-R3",
                "description": "Low-confidence official affiliation signal — review required.",
                "conditions": {"min_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.68,
                    "reason_template": (
                        "Content referencing official or government affiliations was detected. "
                        "Moderator review is required to verify authenticity of claimed affiliations."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "partner_and_government_allowlist_not_finalised",
                "condition": {"always": True},
                "message": (
                    "A trusted partner, government, and regulator entity allowlist has not been "
                    "finalised. Impersonation detection relies on semantic pattern analysis only."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "affiliation_cannot_be_verified_externally",
                "condition": {"always": True},
                "message": (
                    "Claimed affiliations with government or partner bodies cannot be verified "
                    "by the pipeline. Risk and compliance teams must conduct external verification."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "final_compliance_determination_not_made",
                "condition": {"always": True},
                "message": (
                    "The pipeline does not make final compliance determinations. "
                    "All high-severity outputs require human risk and compliance review."
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
            "Detects false claims of government, regulator, or official partner affiliation.",
            "Identifies unauthorised use of official organisation names and designations.",
            "Classifies impersonation by type and risk level.",
            "Generates risk and compliance escalation signals."
        ],
        "what_this_policy_does_not_do": [
            "Does not verify claimed affiliations against an official partner list.",
            "Does not access government or regulatory databases to confirm registration.",
            "Does not detect impersonation through document forgery or logos.",
            "Does not make final compliance determinations.",
            "Does not apply jurisdiction-specific impersonation law standards."
        ]
    }
}
