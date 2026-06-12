"""
OFF-03 Policy Configuration

Policy:
Sexually explicit or obscene content in text (text-only in current POC scope).

Unique trigger focus:
Detects project submissions containing sexually explicit, graphic, or obscene
text content that is inappropriate for the SWA platform's professional and
public audience context. This is text-only in the current POC; image/media
analysis is out of scope. Distinct from OFF-01 (hate speech) and OFF-02
(harassment); this policy targets sexual explicitness and obscenity rather
than identity-based attacks.

Severity: MEDIUM — explicit content must be removed or heavily redacted;
escalation to Trust and Safety for severe cases.
"""

OFF_03_CONFIG = {
    "policy_code": "OFF-03",

    "policy_name": (
        "Sexually explicit or obscene content (text-only in current POC scope)"
    ),

    "policy_category": "Offensive",

    "severity": "MEDIUM",

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
        "prompt_id": "OFF_03_OBSCENITY_ANALYSIS",
        "max_tokens": 3500
    },

    "claim_types": [
        "sexually_explicit_description",
        "graphic_sexual_content",
        "obscene_language",
        "adult_content_in_inappropriate_context",
        "sexual_solicitation_text",
        "graphic_violence_description"
    ],

    # Safety-filter harm categories that indicate a genuine OFF-03 (sexual /
    # obscene) violation when they block this policy's LLM call (see M16).
    "content_filter_relevant_categories": [
        "sexual",
        "violence"
    ],

    # M03 absolute / authority scans
    "absolute_claim_terms": [],

    "authority_terms": [],

    "evidence_indicators": [],

    # M03 EXTRA_TERM_LIST_KEYS — auto-scanned by m03_rule_signals.py
    # Note: Explicit terms are intentionally limited here to avoid false positives.
    # The LLM handles nuanced obscenity detection with full context awareness.
    "obscenity_terms": [
        "porn", "pornographic", "pornography", "xxx",
        "nude", "nudity", "explicit content", "adult content",
        "sexual services", "escort", "prostitution",
        "erotic", "erotica", "explicit sexual",
        "genitalia", "graphic sex", "graphic sexual",
        "soliciting sex", "sexual solicitation",
        "adult entertainment", "strip club", "sex club",
        "onlyfans", "adult website", "18+ only"
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
                "No sexually explicit, graphic, or obscene text content was detected "
                "in the submitted project text."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "sexually_explicit_description",
                "graphic_sexual_content",
                "sexual_solicitation_text"
            ],
            "medium_risk_claim_types": [
                "obscene_language",
                "adult_content_in_inappropriate_context",
                "graphic_violence_description"
            ]
        },

        "rules": [

            # ── Tier-direct rules (fire before claim-count rules) ──────────────────
            # When the LLM returns recommended_tier, use it directly so M16 does not
            # fall through to raw claim-count rules that are miscalibrated for OFF.
            {
                "rule_id": "OFF03-RPASS",
                "description": "LLM recommends PASS tier — no actionable violation.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "PASS"},
                "result": {
                    "matched_flag": False, "severity": "LOW", "suggested_action": "PASS",
                    "manual_review_required": False, "confidence_score": 0.90,
                    "reason_template": ("No sexually explicit or obscene content detected; any sexual references are clinical, educational, or relationship-guidance in nature.")
                }
            },

            {
                "rule_id": "OFF03-RQRN",
                "description": "LLM recommends QUARANTINE tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "QUARANTINE"},
                "result": {
                    "matched_flag": True, "severity": "CRITICAL", "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Trust & Safety / Law Enforcement", "manual_review_required": True,
                    "confidence_score": 0.93, "reason_template": ("Non-consensual sexual content (revenge porn), coordination of sexual violence, or sexual content involving exploitation/lures. Reject and quarantine immediately.")
                }
            },

            {
                "rule_id": "OFF03-RESC",
                "description": "LLM recommends ESCALATE tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "ESCALATE"},
                "result": {
                    "matched_flag": True, "severity": "HIGH", "suggested_action": "ESCALATE",
                    "escalate_to": "Trust & Safety / Compliance", "manual_review_required": True,
                    "confidence_score": 0.90, "reason_template": ("Graphic sexual content, commercial sexual-service promotion, or pornographic material distribution. Escalate to Compliance.")
                }
            },

            {
                "rule_id": "OFF03-RNR",
                "description": "LLM recommends NEEDS_REVIEW tier.",
                "conditions": {"llm_analysis_failed": False, "llm_recommended_tier": "NEEDS_REVIEW"},
                "result": {
                    "matched_flag": True, "severity": "MEDIUM", "suggested_action": "REVIEW",
                    "manual_review_required": True, "confidence_score": 0.82,
                    "reason_template": ("Adult or sexually suggestive content in an artistic, literary, or academic framing. Flag for human review to confirm it is not gratuitous or obscene.")
                }
            },

            {
                "rule_id": "OFF03-R0a",
                "description": "Content filter fired AND quarantine-indicator terms present → QUARANTINE.",
                "conditions": {
                    "llm_analysis_failed": True,
                    "llm_content_filtered": True,
                    "rule_signals.has_quarantine_indicator_terms_signal": True
                },
                "result": {
                    "matched_flag": True, "severity": "CRITICAL", "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Trust & Safety / Law Enforcement", "manual_review_required": True,
                    "confidence_score": 0.88, "reason_template": ("Content filter confirmed harmful content AND non-consensual/sexual-violence/exploitation indicators detected. Reject and quarantine.")
                }
            },

            {
                "rule_id": "OFF03-R0b",
                "description": "Content filter fired (no quarantine indicators) → ESCALATE.",
                "conditions": {
                    "llm_analysis_failed": True,
                    "llm_content_filtered": True
                },
                "result": {
                    "matched_flag": True, "severity": "HIGH", "suggested_action": "ESCALATE",
                    "escalate_to": "Trust & Safety / Compliance", "manual_review_required": True,
                    "confidence_score": 0.80, "reason_template": ("Content filter confirmed explicit sexual content. Escalate to Trust & Safety for review.")
                }
            },

            {
                "rule_id": "OFF03-R0",
                "description": "LLM obscenity analysis failed; cannot safely pass.",
                "conditions": {"llm_analysis_failed": True},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.45,
                    "reason_template": (
                        "LLM obscenity analysis failed. The policy cannot be safely passed because "
                        "explicit content detection was incomplete."
                    )
                }
            },
            {
                "rule_id": "OFF03-R1",
                "description": "Clearly sexually explicit or graphic content detected — reject.",
                "conditions": {"min_high_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Trust and Safety",
                    "manual_review_required": True,
                    "confidence_score": 0.92,
                    "reason_template": (
                        "Sexually explicit or graphic content was detected in the project submission. "
                        "This content is inappropriate for the SWA platform and must be rejected. "
                        "Escalate to Trust and Safety for review."
                    )
                }
            },
            {
                "rule_id": "OFF03-R2",
                "description": "Obscene or adult content in inappropriate context — request amendment.",
                "conditions": {"min_medium_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REQUEST_AMENDMENT",
                    "manual_review_required": True,
                    "confidence_score": 0.80,
                    "reason_template": (
                        "Content containing obscene language or adult themes inappropriate for "
                        "the platform context was detected. The submitter should remove or revise "
                        "the offensive content before resubmission."
                    )
                }
            },
            {
                "rule_id": "OFF03-R3",
                "description": "Low-confidence obscenity signal — review recommended.",
                "conditions": {"min_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "LOW",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.65,
                    "reason_template": (
                        "Content that may contain inappropriate or borderline-explicit language "
                        "was detected. Moderator review is recommended to assess context."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "media_and_images_not_in_scope",
                "condition": {"always": True},
                "message": (
                    "This policy is text-only in the current POC. Sexually explicit or obscene "
                    "images, videos, or attachments are not assessed in the current pipeline."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "context_and_platform_norms_require_review",
                "condition": {"always": True},
                "message": (
                    "Obscenity determination is context-dependent. Content discussing sexual health, "
                    "education, or research may use clinical language that superficially resembles "
                    "explicit content. Human review is required for borderline cases."
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
        "current_scope": "Project-only, text-only moderation for current POC.",
        "what_this_policy_does": [
            "Detects sexually explicit descriptions, graphic content, and obscene language in text.",
            "Identifies adult content inappropriate for the SWA platform audience.",
            "Classifies explicit content by type and risk level.",
            "Generates Trust and Safety escalation signals for severe cases."
        ],
        "what_this_policy_does_not_do": [
            "Does not analyse images, videos, or attached files (out of current POC scope).",
            "Does not apply age-gating logic or jurisdiction-specific obscenity law standards.",
            "Does not distinguish clinical/educational sexual health language with certainty "
            "without human review.",
            "Does not make final Trust and Safety determinations."
        ]
    }
}
