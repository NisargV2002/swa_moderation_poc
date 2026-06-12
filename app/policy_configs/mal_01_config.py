"""
MAL-01 Policy Configuration

Policy:
Phishing, scam, social engineering, or credential harvesting content.

Unique trigger focus:
Detects content designed to deceive recipients into providing credentials,
money, or personal information — phishing links, scam solicitations,
social-engineering scripts, fake prize notifications, urgent payment requests,
and credential-harvesting tactics. This is distinct from MAL-03 (impersonation)
and MAL-02 (malware); this policy targets deceptive persuasion patterns.

Severity: CRITICAL — any confirmed phishing or scam signal triggers
immediate quarantine and Security escalation.
"""

MAL_01_CONFIG = {
    "policy_code": "MAL-01",

    "policy_name": (
        "Phishing, scam, social engineering, or credential harvesting content"
    ),

    "policy_category": "Malicious",

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
        "enabled": True,
        "prompt_id": "MAL_01_PHISHING_ANALYSIS",
        "max_tokens": 4000
    },

    "claim_types": [
        "phishing_attempt",
        "credential_harvesting",
        "scam_solicitation",
        "social_engineering",
        "fake_prize_or_lottery",
        "advance_fee_fraud",
        "financial_fraud_attempt",
        "account_verification_scam",
        "urgent_payment_request"
    ],

    # M03 absolute / authority scans
    "absolute_claim_terms": [],

    "authority_terms": [],

    "evidence_indicators": [
        "source", "reference", "attached", "link"
    ],

    # M03 EXTRA_TERM_LIST_KEYS — auto-scanned by m03_rule_signals.py
    "phishing_terms": [
        "verify your account", "confirm your identity", "confirm your details",
        "click the link below", "click here to verify", "click here to confirm",
        "your account has been suspended", "your account will be closed",
        "unusual activity detected", "suspicious login",
        "update your payment information", "update your billing",
        "your password has expired", "reset your password immediately",
        "we need to verify", "verify immediately", "action required",
        "your account will be terminated", "failure to respond",
        "login credentials", "enter your username and password",
        "provide your details", "submit your information",
        "bank details", "credit card details", "card number",
        "you have won", "you are selected", "you are a winner",
        "claim your prize", "claim your reward", "claim your winnings",
        "advance fee", "processing fee", "release fee", "administration fee",
        "wire transfer", "western union", "money gram",
        "secret", "confidential offer", "private offer",
        "lottery", "jackpot", "sweepstake"
    ],

    "urgency_terms": [
        "urgent", "immediately", "act now", "respond within 24 hours",
        "respond within 48 hours", "expires today", "expires soon",
        "last chance", "final notice", "final warning", "time sensitive",
        "do not delay", "limited time", "deadline",
        "failure to comply", "failure to respond", "penalty",
        "your account will be", "risk of termination"
    ],

    "decision_rules": {
        "default": {
            "matched_flag": False,
            "severity": "LOW",
            "suggested_action": "PASS",
            "manual_review_required": False,
            "confidence_score": 0.90,
            "reason_template": (
                "No phishing, scam, social-engineering, or credential-harvesting content "
                "was detected in the submitted project text."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "phishing_attempt",
                "credential_harvesting",
                "advance_fee_fraud",
                "financial_fraud_attempt",
                "account_verification_scam"
            ],
            "medium_risk_claim_types": [
                "scam_solicitation",
                "social_engineering",
                "fake_prize_or_lottery",
                "urgent_payment_request"
            ]
        },

        "rules": [

            # ── Tier-direct rules (fire before claim-count rules) ──────────────────
            # When the LLM returns recommended_tier, use it directly so M16 does not
            # fall through to raw claim-count rules that are miscalibrated for MAL.
            {
                "rule_id": "MAL01-RPASS",
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
                        "No phishing, credential-harvesting, or scam-solicitation content detected; links are benign informational or contact pages."
                    )
                }
            },

            {
                "rule_id": "MAL01-RQRN",
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
                        "Direct phishing portal impersonating the official SWA login/SSO domain to harvest moderation credentials. Reject and quarantine immediately."
                    )
                }
            },

            {
                "rule_id": "MAL01-RESC",
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
                        "Impersonation of an official department with urgency-based credential, OTP, banking, or wallet-key harvesting detected. Escalate to Security."
                    )
                }
            },

            {
                "rule_id": "MAL01-RNR",
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
                        "Login/credential entry requested on an unverified external domain. Flag for moderator review of phishing risk."
                    )
                }
            },

            {
                "rule_id": "MAL01-R0",
                "description": "LLM phishing/scam analysis failed; cannot safely pass.",
                "conditions": {"llm_analysis_failed": True},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "ESCALATE",
                    "escalate_to": "Security Review",
                    "manual_review_required": True,
                    "confidence_score": 0.50,
                    "reason_template": (
                        "LLM phishing and scam analysis failed. This policy cannot be safely passed "
                        "because malicious-content detection was incomplete. Escalating for "
                        "manual security review."
                    )
                }
            },
            {
                "rule_id": "MAL01-R1",
                "description": "High-risk phishing or fraud content detected — reject and quarantine.",
                "conditions": {"min_high_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "CRITICAL",
                    "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Security / Anti-Abuse",
                    "manual_review_required": True,
                    "confidence_score": 0.95,
                    "reason_template": (
                        "Phishing, credential-harvesting, or financial fraud content was detected. "
                        "The submission poses an immediate security risk to users and must be rejected "
                        "and quarantined. Escalate to Security and Anti-Abuse teams."
                    )
                }
            },
            {
                "rule_id": "MAL01-R2",
                "description": "Scam or social-engineering content detected — escalate.",
                "conditions": {"min_medium_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "ESCALATE",
                    "escalate_to": "Security Review",
                    "manual_review_required": True,
                    "confidence_score": 0.88,
                    "reason_template": (
                        "Scam solicitation, fake prize offer, or social-engineering content was detected. "
                        "The submission requires immediate security team review."
                    )
                }
            },
            {
                "rule_id": "MAL01-R3",
                "description": "Low-confidence deceptive content signal — review required.",
                "conditions": {"min_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.70,
                    "reason_template": (
                        "Content with possible deceptive or scam-related language was detected. "
                        "Moderator review is required to assess intent and risk."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "link_destination_not_verified",
                "condition": {"always": True},
                "message": (
                    "URLs detected in the submission have not been resolved or verified. "
                    "Security team must validate link destinations for phishing risk."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "sender_identity_not_verified",
                "condition": {"always": True},
                "message": (
                    "The identity of the submitter is not verified by the pipeline. "
                    "Security investigation is required for confirmed phishing or scam submissions."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "trusted_domain_list_not_finalised",
                "condition": {"always": True},
                "message": (
                    "A trusted partner/domain allowlist has not been finalised. "
                    "Domain-level phishing detection is limited to text pattern analysis."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "final_security_determination_not_made",
                "condition": {"always": True},
                "message": (
                    "The pipeline does not make final security determinations. "
                    "All high-severity outputs require human security review."
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
            "Detects phishing attempts, credential-harvesting, scam solicitations, and social engineering.",
            "Identifies fake prize notifications, advance-fee fraud, and urgent payment requests.",
            "Classifies deceptive content by type and risk level.",
            "Generates quarantine and security escalation signals."
        ],
        "what_this_policy_does_not_do": [
            "Does not resolve or verify URLs to confirm phishing destinations.",
            "Does not verify submitter identity.",
            "Does not apply real-time domain reputation or phishing feed checks.",
            "Does not make final security determinations.",
            "Does not detect phishing content embedded in attached files."
        ]
    }
}
