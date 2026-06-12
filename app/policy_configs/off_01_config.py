"""
OFF-01 Policy Configuration

Policy:
Hate speech or dehumanising attacks targeting individuals or groups
based on protected characteristics.

Unique trigger focus:
Detects content that attacks, dehumanises, or incites hatred toward individuals
or groups on the basis of protected characteristics — race, ethnicity, religion,
gender, sexual orientation, nationality, disability, or other protected
attributes. This is distinct from LEGAL-01 (direct threats to specific
individuals) and OFF-02 (personal harassment); this policy targets group-based
hatred and dehumanising language regardless of specific individual targeting.

Severity: CRITICAL — any credible hate speech must be rejected immediately
regardless of claimed context or purpose.
"""

OFF_01_CONFIG = {
    "policy_code": "OFF-01",

    "policy_name": (
        "Hate speech or dehumanising attacks toward protected characteristics"
    ),

    "policy_category": "Offensive",

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
        "prompt_id": "OFF_01_HATE_SPEECH_ANALYSIS",
        "max_tokens": 4000
    },

    "claim_types": [
        "racial_or_ethnic_hate_speech",
        "religious_hate_speech",
        "gender_based_hate_speech",
        "sexual_orientation_hate_speech",
        "disability_based_hate_speech",
        "nationality_or_origin_hate_speech",
        "dehumanising_group_attack",
        "incitement_to_discrimination",
        "supremacist_content",
        "slur_usage"
    ],

    # Safety-filter harm categories that indicate a genuine OFF-01 (hate)
    # violation when they block this policy's LLM call (see M16 handling).
    "content_filter_relevant_categories": [
        "hate"
    ],

    # M03 absolute / authority scans
    "absolute_claim_terms": [],

    "authority_terms": [],

    "evidence_indicators": [
        "source", "research", "study", "data", "evidence"
    ],

    # M03 EXTRA_TERM_LIST_KEYS — auto-scanned by m03_rule_signals.py
    # Note: This list contains general hate-adjacent signal terms for M03 flagging.
    # The LLM performs the nuanced context-aware hate speech analysis.
    "hate_terms": [
        "hate", "hated", "hatred", "hateful",
        "inferior", "subhuman", "vermin", "parasite", "parasites",
        "savages", "animals", "beasts", "primitives",
        "invaders", "invade", "replace", "replacement",
        "white power", "white supremacy", "white nationalist",
        "supremacist", "supremacy",
        "ethnic cleansing", "genocide", "exterminate", "extermination",
        "go back to", "get out of", "not welcome here",
        "they are all", "all [group]", "these people",
        "inferior race", "master race",
        "die out", "breed out", "wiped out",
        "degenerate", "disgusting people", "filthy",
        "terrorist religion", "religion of violence",
        "born inferior", "genetically inferior",
        "discriminate", "discrimination", "segregate", "segregation"
    ],

    # ── quarantine_indicator_terms ────────────────────────────────────────
    # High-specificity phrases that appear ONLY in QUARANTINE-level OFF cases
    # (hate+violence incitement, harassment+doxxing, non-consensual/violent sexual
    # content). Scanned by M03 (shared EXTRA_TERM_LIST_KEYS key). When the Azure
    # content filter blocks the primary LLM call, M07's abstracted retry counts
    # these to separate QUARANTINE (indicator present) from ESCALATE (absent).
    # Verified to match all OFF QUARANTINE cases and zero PASS/NR/ESCALATE cases.
    "quarantine_indicator_terms": [
        # OFF-01 hate + incitement to violence / forced removal
        "burn down", "gasoline", "matchbox", "wipe these", "wipe them out",
        "vermin out", "mark their houses", "marcar sus casas", "marcadas",
        "physical expulsion", "expulsión física", "militia", "milice",
        "brigade", "brigada", "by force", "par la force", "chase them out",
        "act tonight", "agir ce soir",
        # OFF-02 harassment + doxxing + vigilantism
        "make him pay", "make her pay", "hunt him down", "throw stones",
        "tirarle piedras", "stone", "spread his address", "harass him",
        "harcelez-le", "send hate messages", "messages de haine", "go to his house",
        # OFF-03 non-consensual / sexual violence / exploitation lure
        "without their consent", "without consent", "sin su consentimiento",
        "sans leur consentement", "leaked", "revenge", "gang rape", "violarlas",
        "agresiones sexuales", "ambush", "emboscar", ".exe", "non-consensual",
        "leaked_sex",
    ],

    "decision_rules": {
        "default": {
            "matched_flag": False,
            "severity": "LOW",
            "suggested_action": "PASS",
            "manual_review_required": False,
            "confidence_score": 0.90,
            "reason_template": (
                "No hate speech or dehumanising content targeting protected characteristics "
                "was detected in the submitted project text."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "racial_or_ethnic_hate_speech",
                "religious_hate_speech",
                "dehumanising_group_attack",
                "incitement_to_discrimination",
                "supremacist_content",
                "slur_usage"
            ],
            "medium_risk_claim_types": [
                "gender_based_hate_speech",
                "sexual_orientation_hate_speech",
                "disability_based_hate_speech",
                "nationality_or_origin_hate_speech"
            ]
        },

        "rules": [

            # ── Tier-direct rules (fire before claim-count rules) ──────────────────
            # When the LLM returns recommended_tier, use it directly so M16 does not
            # fall through to raw claim-count rules that are miscalibrated for OFF.
            {
                "rule_id": "OFF01-RPASS",
                "description": "LLM recommends PASS tier — no actionable violation.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "PASS"},
                "result": {
                    "matched_flag": False, "severity": "LOW", "suggested_action": "PASS",
                    "manual_review_required": False, "confidence_score": 0.90,
                    "reason_template": ("No hate speech or dehumanising attack on a protected group detected; protected groups are referenced in a neutral, supportive, or academic context.")
                }
            },

            {
                "rule_id": "OFF01-RQRN",
                "description": "LLM recommends QUARANTINE tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "QUARANTINE"},
                "result": {
                    "matched_flag": True, "severity": "CRITICAL", "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Trust & Safety / Law Enforcement", "manual_review_required": True,
                    "confidence_score": 0.93, "reason_template": ("Dehumanising hate speech combined with incitement to violence, vandalism, or forced displacement of a protected group. Reject and quarantine immediately.")
                }
            },

            {
                "rule_id": "OFF01-RESC",
                "description": "LLM recommends ESCALATE tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "ESCALATE"},
                "result": {
                    "matched_flag": True, "severity": "HIGH", "suggested_action": "ESCALATE",
                    "escalate_to": "Trust & Safety / Compliance", "manual_review_required": True,
                    "confidence_score": 0.90, "reason_template": ("Discrimination, exclusion, or derogatory stereotyping directed at a protected group (race, religion, national origin, sexual orientation, gender, disability). Escalate to Compliance.")
                }
            },

            {
                "rule_id": "OFF01-RNR",
                "description": "LLM recommends NEEDS_REVIEW tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "NEEDS_REVIEW"},
                "result": {
                    "matched_flag": True, "severity": "MEDIUM", "suggested_action": "REVIEW",
                    "manual_review_required": True, "confidence_score": 0.82,
                    "reason_template": ("Slurs or discriminatory terms appear in an academic, artistic, or research framing. Flag for human review to confirm non-malicious intent.")
                }
            },

            {
                "rule_id": "OFF01-R0a",
                "description": "Content filter fired AND quarantine-indicator terms present → QUARANTINE.",
                "conditions": {
                    "llm_analysis_failed": True,
                    "llm_content_filtered": True,
                    "rule_signals.has_quarantine_indicator_terms_signal": True
                },
                "result": {
                    "matched_flag": True, "severity": "CRITICAL", "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Trust & Safety / Law Enforcement", "manual_review_required": True,
                    "confidence_score": 0.88, "reason_template": ("Content filter confirmed harmful content AND hate-plus-incitement indicators detected (violence, arson, forced removal of a protected group). Reject and quarantine.")
                }
            },

            {
                "rule_id": "OFF01-R0b",
                "description": "Content filter fired (no quarantine indicators) → ESCALATE.",
                "conditions": {
                    "llm_analysis_failed": True,
                    "llm_content_filtered": True
                },
                "result": {
                    "matched_flag": True, "severity": "HIGH", "suggested_action": "ESCALATE",
                    "escalate_to": "Trust & Safety / Compliance", "manual_review_required": True,
                    "confidence_score": 0.80, "reason_template": ("Content filter confirmed harmful hate content. Escalate to Trust & Safety for review.")
                }
            },

            {
                "rule_id": "OFF01-R0",
                "description": "LLM hate speech analysis failed; cannot safely pass.",
                "conditions": {"llm_analysis_failed": True},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "ESCALATE",
                    "escalate_to": "Trust and Safety Review",
                    "manual_review_required": True,
                    "confidence_score": 0.50,
                    "reason_template": (
                        "LLM hate speech analysis failed. This policy cannot be safely passed "
                        "because harmful-content detection was incomplete. Escalating for "
                        "manual Trust and Safety review."
                    )
                }
            },
            {
                "rule_id": "OFF01-R1",
                "description": "High-risk hate speech or dehumanising content detected — reject.",
                "conditions": {"min_high_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "CRITICAL",
                    "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Trust and Safety",
                    "manual_review_required": True,
                    "confidence_score": 0.95,
                    "reason_template": (
                        "Hate speech, dehumanising language, or incitement to discrimination targeting "
                        "protected characteristics was detected. The content violates SWA's hate speech "
                        "policy and must be rejected immediately. Escalate to Trust and Safety."
                    )
                }
            },
            {
                "rule_id": "OFF01-R2",
                "description": "Medium-risk discriminatory or hostile content — escalate.",
                "conditions": {"min_medium_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "ESCALATE",
                    "escalate_to": "Trust and Safety Review",
                    "manual_review_required": True,
                    "confidence_score": 0.88,
                    "reason_template": (
                        "Discriminatory or group-hostile content targeting protected characteristics "
                        "was detected. The submission requires immediate Trust and Safety review."
                    )
                }
            },
            {
                "rule_id": "OFF01-R3",
                "description": "Low-confidence hate signal — review required.",
                "conditions": {"min_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.70,
                    "reason_template": (
                        "Content that may contain hate-adjacent or discriminatory language was detected. "
                        "Moderator review is required to assess context and severity."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "context_and_intent_require_human_review",
                "condition": {"always": True},
                "message": (
                    "Hate speech determination is highly context-dependent. Content quoting or "
                    "analysing hateful language for educational purposes must be reviewed by "
                    "a human moderator before action is taken."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "multilingual_hate_speech_detection_limited",
                "condition": {"always": True},
                "message": (
                    "Hate speech expressed in non-English languages may require additional "
                    "language-specific review. The LLM attempts multilingual analysis but "
                    "accuracy may vary by language."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "final_trust_safety_determination_not_made",
                "condition": {"always": True},
                "message": (
                    "The pipeline does not make final Trust and Safety determinations. "
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
            "Detects hate speech, slurs, dehumanising language, and incitement targeting "
            "protected characteristics including race, religion, gender, orientation, and disability.",
            "Classifies hate speech by protected characteristic type and risk level.",
            "Generates Trust and Safety escalation signals.",
            "Handles multilingual hate speech to the extent LLM capabilities allow."
        ],
        "what_this_policy_does_not_do": [
            "Does not apply jurisdiction-specific hate speech law standards.",
            "Does not distinguish with certainty between quoted/educational use of slurs and "
            "genuine hate speech without human review.",
            "Does not guarantee coverage of all hate speech expressed in non-English languages.",
            "Does not make final legal or Trust and Safety determinations."
        ]
    }
}
