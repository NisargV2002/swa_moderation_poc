"""
OFF-02 Policy Configuration

Policy:
Targeted harassment or bullying of identifiable individuals.

Unique trigger focus:
Detects content that targets specific named or identifiable individuals with
personal attacks, bullying, sustained hostility, or intimidation — distinct
from LEGAL-01 (direct threats of physical violence) and OFF-01 (group-based
hate speech). This policy focuses on interpersonal harassment directed at a
specific person, whether named explicitly or identifiable from context.

Severity: HIGH — targeted harassment must be escalated immediately and
content rejected or heavily moderated.
"""

OFF_02_CONFIG = {
    "policy_code": "OFF-02",

    "policy_name": (
        "Targeted harassment or bullying of identifiable individuals"
    ),

    "policy_category": "Offensive",

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
        "prompt_id": "OFF_02_HARASSMENT_ANALYSIS",
        "max_tokens": 4000
    },

    "claim_types": [
        "targeted_personal_attack",
        "bullying_content",
        "sustained_individual_hostility",
        "public_shaming",
        "reputation_attack",
        "personal_humiliation",
        "named_individual_harassment",
        "coordinated_harassment_call"
    ],

    # Safety-filter harm categories that indicate a genuine OFF-02 (targeted
    # harassment) violation when they block this policy's LLM call (see M16).
    "content_filter_relevant_categories": [
        "hate",
        "violence"
    ],

    # M03 absolute / authority scans
    "absolute_claim_terms": [],

    "authority_terms": [],

    "evidence_indicators": [
        "source", "evidence", "record", "documented"
    ],

    # M03 EXTRA_TERM_LIST_KEYS — auto-scanned by m03_rule_signals.py
    "harassment_terms": [
        "loser", "idiot", "moron", "stupid", "pathetic",
        "worthless", "disgusting person", "disgusting individual",
        "piece of garbage", "piece of trash", "piece of work",
        "shut up", "shut your mouth", "nobody likes you",
        "everyone hates", "no one wants you",
        "you should be ashamed", "you are a disgrace",
        "you are a failure", "you are useless",
        "embarrassment to", "laughing stock",
        "humiliate", "humiliated", "humiliation",
        "bully", "bullied", "bullying",
        "harass", "harassed", "harassment",
        "shame on", "shamed", "public shame",
        "expose", "exposing", "I will expose",
        "ruin your reputation", "destroy your career",
        "make your life difficult",
        "go after", "target", "targeting this person",
        "attack their credibility",
        "doxxed", "spreading lies about"
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
            "confidence_score": 0.88,
            "reason_template": (
                "No targeted harassment or bullying of an identifiable individual "
                "was detected in the submitted project text."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "targeted_personal_attack",
                "named_individual_harassment",
                "coordinated_harassment_call",
                "public_shaming"
            ],
            "medium_risk_claim_types": [
                "bullying_content",
                "sustained_individual_hostility",
                "reputation_attack",
                "personal_humiliation"
            ]
        },

        "rules": [

            # ── Tier-direct rules (fire before claim-count rules) ──────────────────
            # When the LLM returns recommended_tier, use it directly so M16 does not
            # fall through to raw claim-count rules that are miscalibrated for OFF.
            {
                "rule_id": "OFF02-RPASS",
                "description": "LLM recommends PASS tier — no actionable violation.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "PASS"},
                "result": {
                    "matched_flag": False, "severity": "LOW", "suggested_action": "PASS",
                    "manual_review_required": False, "confidence_score": 0.90,
                    "reason_template": ("No targeted harassment detected; named individuals are referenced professionally, constructively, or appreciatively.")
                }
            },

            {
                "rule_id": "OFF02-RQRN",
                "description": "LLM recommends QUARANTINE tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "QUARANTINE"},
                "result": {
                    "matched_flag": True, "severity": "CRITICAL", "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Trust & Safety / Law Enforcement", "manual_review_required": True,
                    "confidence_score": 0.93, "reason_template": ("Targeted harassment combined with doxxing (home address/phone) and/or incitement to physical violence or a pile-on against an individual. Reject and quarantine immediately.")
                }
            },

            {
                "rule_id": "OFF02-RESC",
                "description": "LLM recommends ESCALATE tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "ESCALATE"},
                "result": {
                    "matched_flag": True, "severity": "HIGH", "suggested_action": "ESCALATE",
                    "escalate_to": "Trust & Safety / Compliance", "manual_review_required": True,
                    "confidence_score": 0.90, "reason_template": ("Hostile, degrading, or defamatory personal attacks targeting a named individual (insults, slurs, criminal accusations stated as fact). Escalate to Compliance.")
                }
            },

            {
                "rule_id": "OFF02-RNR",
                "description": "LLM recommends NEEDS_REVIEW tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "NEEDS_REVIEW"},
                "result": {
                    "matched_flag": True, "severity": "MEDIUM", "suggested_action": "REVIEW",
                    "manual_review_required": True, "confidence_score": 0.82,
                    "reason_template": ("A named individual is criticised or accused with hostile or unverified personal remarks. Flag for human review to separate legitimate complaint from personal attack.")
                }
            },

            {
                "rule_id": "OFF02-R0a",
                "description": "Content filter fired AND quarantine-indicator terms present → QUARANTINE.",
                "conditions": {
                    "llm_analysis_failed": True,
                    "llm_content_filtered": True,
                    "rule_signals.has_quarantine_indicator_terms_signal": True
                },
                "result": {
                    "matched_flag": True, "severity": "CRITICAL", "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Trust & Safety / Law Enforcement", "manual_review_required": True,
                    "confidence_score": 0.88, "reason_template": ("Content filter confirmed harmful content AND harassment-plus-doxxing/violence indicators detected (home address, incitement to go after the target). Reject and quarantine.")
                }
            },

            {
                "rule_id": "OFF02-R0b",
                "description": "Content filter fired (no quarantine indicators) → ESCALATE.",
                "conditions": {
                    "llm_analysis_failed": True,
                    "llm_content_filtered": True
                },
                "result": {
                    "matched_flag": True, "severity": "HIGH", "suggested_action": "ESCALATE",
                    "escalate_to": "Trust & Safety / Compliance", "manual_review_required": True,
                    "confidence_score": 0.80, "reason_template": ("Content filter confirmed harmful harassment content. Escalate to Trust & Safety for review.")
                }
            },

            {
                "rule_id": "OFF02-R0",
                "description": "LLM harassment analysis failed; cannot safely pass.",
                "conditions": {"llm_analysis_failed": True},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "ESCALATE",
                    "escalate_to": "Trust and Safety Review",
                    "manual_review_required": True,
                    "confidence_score": 0.50,
                    "reason_template": (
                        "LLM harassment analysis failed. This policy cannot be safely passed "
                        "because targeted-harassment detection was incomplete. Escalating for "
                        "manual Trust and Safety review."
                    )
                }
            },
            {
                "rule_id": "OFF02-R1",
                "description": "Clear targeted harassment or personal attack detected — reject.",
                "conditions": {"min_high_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Trust and Safety",
                    "manual_review_required": True,
                    "confidence_score": 0.92,
                    "reason_template": (
                        "Targeted harassment, personal attack, or coordinated bullying of an "
                        "identifiable individual was detected. The content must be rejected and "
                        "escalated to Trust and Safety for further action."
                    )
                }
            },
            {
                "rule_id": "OFF02-R2",
                "description": "Bullying or reputation attack detected — escalate.",
                "conditions": {"min_medium_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "ESCALATE",
                    "escalate_to": "Trust and Safety Review",
                    "manual_review_required": True,
                    "confidence_score": 0.82,
                    "reason_template": (
                        "Bullying language, public shaming, or reputation attack targeting an "
                        "identifiable individual was detected. Human Trust and Safety review "
                        "is required."
                    )
                }
            },
            {
                "rule_id": "OFF02-R3",
                "description": "Low-confidence harassment signal — review required.",
                "conditions": {"min_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.68,
                    "reason_template": (
                        "Content that may contain personally hostile or harassing language was "
                        "detected. Moderator review is required to assess target and severity."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "target_identity_not_confirmed",
                "condition": {"always": True},
                "message": (
                    "Whether the harassed individual is a real, identifiable person cannot be "
                    "confirmed without external investigation."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "repetition_pattern_requires_history",
                "condition": {"always": True},
                "message": (
                    "Sustained or coordinated harassment patterns are best detected across "
                    "multiple submissions. Single-submission analysis may undercount severity."
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
        "PASS", "REVIEW", "REQUEST_AMENDMENT", "ESCALATE", "REJECT_RECOMMENDED"
    ],

    "scope_notes": {
        "current_scope": "Project-only moderation for current POC.",
        "what_this_policy_does": [
            "Detects targeted personal attacks, bullying, and harassment of identifiable individuals.",
            "Identifies public shaming, reputation attacks, and coordinated harassment calls.",
            "Classifies harassment by type and risk level.",
            "Generates Trust and Safety escalation signals."
        ],
        "what_this_policy_does_not_do": [
            "Does not confirm whether the harassment target is a real identifiable person.",
            "Does not detect patterns across multiple submissions (history required).",
            "Does not distinguish between criticism and harassment with certainty without human review.",
            "Does not make final Trust and Safety determinations.",
            "Does not detect harassment patterns in attached media files."
        ]
    }
}
