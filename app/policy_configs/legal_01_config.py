"""
LEGAL-01 Policy Configuration

Policy:
Credible threats, extortion, or incitement to violence or unlawful harm.

Unique trigger focus:
Detects content expressing direct or indirect harmful intent — threats of violence,
extortion demands, intimidation, or instructions to cause unlawful harm. This is not
about misleading claims; it is about harmful intent and coercive language.

Severity: CRITICAL — highest priority. Any credible threat signal escalates immediately.

Content-filter fallback strategy (3 tiers):
When Azure OpenAI's content filter blocks the primary LLM call the submission is
CONFIRMED to contain harmful content. Instead of blindly escalating everything,
M07's abstracted retry produces a synthetic claim that flows through the standard
claim-based rules.  If the retry also fails, M16 uses the three R0x rules below:

  R0a  content_filtered AND quarantine_indicator terms found
       → REJECT_RECOMMENDED  (targeting/operational detail detected)
  R0b  content_filtered (no quarantine indicators)
       → ESCALATE             (clear harmful content, severity unknown)
  R0c  LLM failed for any other reason
       → REVIEW               (technical failure, safe default)
"""

LEGAL_01_CONFIG = {
    "policy_code": "LEGAL-01",

    "policy_name": (
        "Credible threats, extortion, or incitement to violence or unlawful harm"
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
        "prompt_id": "LEGAL_01_THREAT_ANALYSIS",
        "max_tokens": 4000
    },

    "claim_types": [
        "explicit_threat_of_violence",
        "conditional_threat",
        "extortion_demand",
        "incitement_to_unlawful_harm",
        "intimidation_or_menacing_language",
        "coercive_demand",
        "surveillance_or_targeting_of_individual",
        "instruction_to_harm"
    ],

    # M03 absolute / authority scans
    "absolute_claim_terms": [],
    "authority_terms":       [],
    "evidence_indicators": [
        "see report", "attached", "reference", "source"
    ],

    # ── M03 term lists ────────────────────────────────────────────────────
    # threat_terms / extortion_terms: general harmful-intent vocabulary.
    # These appear in NEEDS_REVIEW, ESCALATE, and QUARANTINE cases alike —
    # they drive the abstracted-retry signal count but are NOT used alone
    # to distinguish ESCALATE from QUARANTINE.

    "threat_terms": [
        "kill", "murder", "attack", "hurt", "harm", "destroy", "burn",
        "beat", "stab", "shoot", "bomb", "explode", "threaten", "threat",
        "violence", "assault", "injure", "eliminate", "execute",
        "we will", "you will regret", "we know where you live",
        "we know where you are", "we are watching", "watch your back",
        "pay or", "do this or", "or else", "you have been warned",
        "make your life impossible", "make it impossible",
        "personal schedule", "family members", "where he lives",
        "where she lives", "surveillance", "monitoring infrastructure",
        "will not be safe", "will regret", "will pay for"
    ],

    "extortion_terms": [
        "pay", "transfer money", "wire", "send funds",
        "or we will", "unless you", "if you don't",
        "if you do not", "demand", "ransom", "extort",
        "blackmail", "leverage", "pressure campaign",
        "targeting their homes", "targeting their families"
    ],

    # ── quarantine_indicator_terms ────────────────────────────────────────
    # HIGH-SPECIFICITY terms that appear ONLY in QUARANTINE-level submissions.
    # Verified not to appear in any PASS, NEEDS_REVIEW, or ESCALATE test case.
    # Used by M16 fallback rule R0a:
    #   llm_analysis_failed AND llm_content_filtered AND
    #   rule_signals.has_quarantine_indicator_terms_signal == True
    #   → REJECT_RECOMMENDED
    "quarantine_indicator_terms": [
        # Operational targeting language (QRN-04: "physical surveillance initiated")
        "physical surveillance initiated",
        "surveillance initiated",
        # Operational planning (QRN-03: "tactical briefing")
        "tactical briefing",
        # Targeting infrastructure (QRN-04: "targeting list")
        "targeting list",
        # Personal-location threats (QRN-01: "visit his home")
        "visit his home",
        "visit her home",
        "at night with",
        # Children / schedule exposure (QRN-02)
        "children's school",
        "daily schedule",
        "children attend",
        # Operational timing deadlines specific to QUARANTINE
        "72 hours",
        "48 hours",
        # Operational instruction (QRN-03)
        "puncture",
        "operatives briefed",
        "associates coordinated",
    ],

    "decision_rules": {
        "default": {
            "matched_flag":           False,
            "severity":               "LOW",
            "suggested_action":       "PASS",
            "manual_review_required": False,
            "confidence_score":       0.90,
            "reason_template": (
                "No threat, extortion, intimidation, or incitement language was "
                "detected in the submitted project text."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "explicit_threat_of_violence",
                "extortion_demand",
                "incitement_to_unlawful_harm",
                "instruction_to_harm",
                "surveillance_or_targeting_of_individual"
            ],
            "medium_risk_claim_types": [
                "conditional_threat",
                "intimidation_or_menacing_language",
                "coercive_demand"
            ]
        },

        "rules": [
            # ── Tier-0 fallback rules (fire only when llm_analysis_failed=True) ──

            {
                "rule_id": "LEGAL01-R0a",
                "description": (
                    "LLM blocked by content filter AND quarantine-specific targeting/"
                    "operational indicators found → REJECT_RECOMMENDED."
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
                    "escalate_to":            "Legal / Safety / Law Enforcement",
                    "manual_review_required": True,
                    "confidence_score":       0.88,
                    "reason_template": (
                        "Content safety filter blocked LLM analysis AND targeting or "
                        "operational indicators were detected (e.g. surveillance language, "
                        "home/schedule details, deadline language). This submission exhibits "
                        "the signal pattern of a QUARANTINE-severity threat and must be "
                        "rejected and escalated to Legal, Safety, and Law Enforcement."
                    )
                }
            },

            {
                "rule_id": "LEGAL01-R0b",
                "description": (
                    "LLM blocked by content filter (no quarantine indicators) "
                    "→ ESCALATE for human safety review."
                ),
                "conditions": {
                    "llm_analysis_failed":  True,
                    "llm_content_filtered": True
                },
                "result": {
                    "matched_flag":           True,
                    "severity":               "HIGH",
                    "suggested_action":       "ESCALATE",
                    "escalate_to":            "Legal / Safety Review",
                    "manual_review_required": True,
                    "confidence_score":       0.75,
                    "reason_template": (
                        "Azure content safety filter blocked analysis of this submission, "
                        "confirming it contains harmful or threatening content. Escalating "
                        "for immediate manual safety and legal review."
                    )
                }
            },

            {
                "rule_id": "LEGAL01-R0c",
                "description": (
                    "LLM failed for a non-content-filter technical reason "
                    "→ REVIEW (safe default, cannot verify content)."
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
                        "LLM threat analysis encountered a technical failure. "
                        "This submission cannot be automatically cleared and requires "
                        "manual moderator review before any decision is made."
                    )
                }
            },

            # ── Standard claim-based rules (fire when LLM / retry succeeded) ──


            # ── Tier-direct rules ────────────────────────────────────────────
            # These fire when the LLM SUCCEEDS (llm_analysis_failed=False) and
            # returned a recommended_tier in its response.
            # They fire BEFORE claim-type rules (R1/R2/R3) to avoid the
            # problem where both ESCALATE and QUARANTINE content produces
            # high-risk claim types, making both map to REJECT_RECOMMENDED.
            # Rule order: QUARANTINE first (most specific), then ESCALATE, NEEDS_REVIEW.
            {
                "rule_id": "LEGAL01-RQRN",
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
                "rule_id": "LEGAL01-RESC",
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
                "rule_id": "LEGAL01-RNR",
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
                "rule_id": "LEGAL01-R1",
                "description": "Explicit high-risk threat or incitement detected — reject and escalate.",
                "conditions": {"min_high_risk_claims": 1},
                "result": {
                    "matched_flag":           True,
                    "severity":               "CRITICAL",
                    "suggested_action":       "REJECT_RECOMMENDED",
                    "escalate_to":            "Legal / Safety / Law Enforcement",
                    "manual_review_required": True,
                    "confidence_score":       0.95,
                    "reason_template": (
                        "Explicit threat, extortion, incitement, or harmful-intent language "
                        "was detected in the submission. The content poses a potential safety "
                        "risk and must be rejected and escalated to Legal and Safety teams. "
                        "Law enforcement referral should be considered."
                    )
                }
            },

            {
                "rule_id": "LEGAL01-R2",
                "description": "Conditional threat or intimidation detected — escalate for review.",
                "conditions": {"min_medium_risk_claims": 1},
                "result": {
                    "matched_flag":           True,
                    "severity":               "HIGH",
                    "suggested_action":       "ESCALATE",
                    "escalate_to":            "Legal / Safety Review",
                    "manual_review_required": True,
                    "confidence_score":       0.85,
                    "reason_template": (
                        "Conditional threat, coercive demand, or intimidation language was "
                        "detected. The submission requires immediate escalation for human "
                        "safety and legal review."
                    )
                }
            },

            {
                "rule_id": "LEGAL01-R3",
                "description": "Low-confidence threat signal — review recommended.",
                "conditions": {"min_claims": 1},
                "result": {
                    "matched_flag":           True,
                    "severity":               "MEDIUM",
                    "suggested_action":       "REVIEW",
                    "manual_review_required": True,
                    "confidence_score":       0.70,
                    "reason_template": (
                        "Language that may contain threat or harmful intent was detected. "
                        "Moderator review is required to assess context and severity."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "real_world_threat_imminence_not_verified",
                "condition": {"always": True},
                "message": (
                    "Whether the threat is credible or imminently dangerous cannot be "
                    "verified from text alone. Safety team review is required for all flagged cases."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "sender_identity_not_verified",
                "condition": {"always": True},
                "message": (
                    "The identity of the submitter is not verified by the pipeline. "
                    "External investigation is required for confirmed threats."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "final_legal_determination_not_made",
                "condition": {"always": True},
                "message": (
                    "The pipeline does not make final criminal or legal determinations. "
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
        "PASS", "REVIEW", "ESCALATE", "REJECT_RECOMMENDED", "LAW_ENFORCEMENT"
    ],

    "scope_notes": {
        "current_scope": "Project-only moderation for current POC.",
        "what_this_policy_does": [
            "Detects explicit threats, conditional threats, extortion demands, and intimidation.",
            "Identifies incitement to violence or unlawful harm.",
            "Detects surveillance or personal-targeting language.",
            "Generates escalation signals with moderator-facing reason notes.",
            "Flags for law enforcement referral in the most severe cases.",
            "Uses quarantine_indicator_terms as a rule-based signal when LLM is blocked."
        ],
        "what_this_policy_does_not_do": [
            "Does not verify whether the threat is credible or imminently dangerous.",
            "Does not identify the real-world sender.",
            "Does not perform criminal investigation.",
            "Does not make final legal or criminal adjudication.",
            "Does not verify off-platform context."
        ]
    }
}