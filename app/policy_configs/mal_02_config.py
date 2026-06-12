"""
MAL-02 Policy Configuration

Policy:
Malware distribution, unsafe download links, or executable attachments.

Unique trigger focus:
Detects content that attempts to distribute malicious software — links to
executable files, suspicious download instructions, embedded script payloads,
or references to malware-associated file types and distribution methods.
Distinct from MAL-01 (phishing/scam deception) and MAL-03 (impersonation);
this policy targets technical delivery of malicious code.

Severity: CRITICAL — any detected malware distribution signal triggers
immediate quarantine and Security escalation.
"""

MAL_02_CONFIG = {
    "policy_code": "MAL-02",

    "policy_name": (
        "Malware distribution, unsafe download links, or executable attachments"
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
        "prompt_id": "MAL_02_MALWARE_ANALYSIS",
        "max_tokens": 4000
    },

    "claim_types": [
        "malware_distribution_link",
        "executable_file_reference",
        "unsafe_download_instruction",
        "script_injection_attempt",
        "trojan_delivery_attempt",
        "ransomware_reference",
        "suspicious_redirect_chain",
        "obfuscated_malicious_payload"
    ],

    # M03 absolute / authority scans
    "absolute_claim_terms": [],

    "authority_terms": [],

    "evidence_indicators": [
        "download", "install", "run", "execute", "file", "link"
    ],

    # M03 EXTRA_TERM_LIST_KEYS — auto-scanned by m03_rule_signals.py
    "malware_terms": [
        "download and run", "download and execute", "run this file",
        "install this software", "install the following", "run the installer",
        "crack", "keygen", "serial key", "activation key", "patch",
        "hacked version", "modded version", "bypass", "bypass security",
        "disable antivirus", "disable your firewall", "turn off windows defender",
        "trojan", "ransomware", "spyware", "adware", "keylogger",
        "botnet", "rootkit", "backdoor", "exploit", "payload",
        "virus", "malware", "worm", "dropper",
        "remote access tool", "rat", "remote desktop", "anydesk install",
        "teamviewer install", "give access to your computer",
        "your computer has been infected", "system error detected",
        "call microsoft", "call apple support", "tech support"
    ],

    "executable_terms": [
        ".exe", ".bat", ".cmd", ".scr", ".vbs", ".js", ".wsf",
        ".msi", ".apk", ".dmg", ".sh", ".ps1", ".jar",
        "setup.exe", "install.exe", "update.exe", "patch.exe",
        "run.bat", "start.cmd", "payload.zip",
        "bit.ly", "tinyurl", "shortened link", "click the link",
        "download from", "download at", "get it here"
    ],

    "decision_rules": {
        "default": {
            "matched_flag": False,
            "severity": "LOW",
            "suggested_action": "PASS",
            "manual_review_required": False,
            "confidence_score": 0.90,
            "reason_template": (
                "No malware distribution, unsafe download, or executable attachment content "
                "was detected in the submitted project text."
            )
        },

        "risk_groups": {
            "high_risk_claim_types": [
                "malware_distribution_link",
                "executable_file_reference",
                "script_injection_attempt",
                "trojan_delivery_attempt",
                "ransomware_reference",
                "obfuscated_malicious_payload"
            ],
            "medium_risk_claim_types": [
                "unsafe_download_instruction",
                "suspicious_redirect_chain"
            ]
        },

        "rules": [

            # ── Tier-direct rules (fire before claim-count rules) ──────────────────
            # When the LLM returns recommended_tier, use it directly so M16 does not
            # fall through to raw claim-count rules that are miscalibrated for MAL.
            {
                "rule_id": "MAL02-RPASS",
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
                        "No malware or unsafe-download content detected; only safe document files (PDF/CSV/DOCX/PPTX/XLSX) are linked."
                    )
                }
            },

            {
                "rule_id": "MAL02-RQRN",
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
                        "Deceptive malware delivery — double-extension file disguised as a document, or a script delivered via a fake security-update lure. Reject and quarantine immediately."
                    )
                }
            },

            {
                "rule_id": "MAL02-RESC",
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
                        "Direct link to an openly distributed executable or script (.exe/.msi/.apk/.ps1/.cmd). Escalate to Security."
                    )
                }
            },

            {
                "rule_id": "MAL02-RNR",
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
                        "Link points to a compressed archive (ZIP/RAR/7Z) or macro-enabled document (XLSM) that could carry a payload. Flag for malware scan."
                    )
                }
            },

            {
                "rule_id": "MAL02-R0",
                "description": "LLM malware analysis failed; cannot safely pass.",
                "conditions": {"llm_analysis_failed": True},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "ESCALATE",
                    "escalate_to": "Security Review",
                    "manual_review_required": True,
                    "confidence_score": 0.50,
                    "reason_template": (
                        "LLM malware and unsafe-download analysis failed. This policy cannot be safely "
                        "passed because malicious-code detection was incomplete. Escalating for "
                        "manual security review."
                    )
                }
            },
            {
                "rule_id": "MAL02-R1",
                "description": "High-risk malware or executable content detected — reject and quarantine.",
                "conditions": {"min_high_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "CRITICAL",
                    "suggested_action": "REJECT_RECOMMENDED",
                    "escalate_to": "Security / Anti-Abuse",
                    "manual_review_required": True,
                    "confidence_score": 0.95,
                    "reason_template": (
                        "Malware distribution, executable file reference, or malicious-code delivery "
                        "content was detected. The submission poses an immediate security threat and "
                        "must be rejected and quarantined. Escalate to Security immediately."
                    )
                }
            },
            {
                "rule_id": "MAL02-R2",
                "description": "Unsafe download instruction or suspicious redirect — escalate.",
                "conditions": {"min_medium_risk_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "HIGH",
                    "suggested_action": "ESCALATE",
                    "escalate_to": "Security Review",
                    "manual_review_required": True,
                    "confidence_score": 0.88,
                    "reason_template": (
                        "Unsafe download instruction or suspicious redirect was detected. "
                        "The submission requires immediate security team review."
                    )
                }
            },
            {
                "rule_id": "MAL02-R3",
                "description": "Low-confidence malware signal — review required.",
                "conditions": {"min_claims": 1},
                "result": {
                    "matched_flag": True,
                    "severity": "MEDIUM",
                    "suggested_action": "REVIEW",
                    "manual_review_required": True,
                    "confidence_score": 0.70,
                    "reason_template": (
                        "Content with possible malware-associated language or download instruction "
                        "was detected. Moderator review is required to assess security risk."
                    )
                }
            }
        ],

        "dependency_gap_rules": [
            {
                "gap_key": "attachment_fields_not_in_pipeline_scope",
                "condition": {"always": True},
                "message": (
                    "Attached files and binary payloads are not available in the current pipeline "
                    "input schema. File-based malware detection is limited to text-referenced indicators."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "url_not_resolved_or_scanned",
                "condition": {"always": True},
                "message": (
                    "URLs referenced in the submission have not been resolved or scanned against "
                    "malware/phishing feeds. Security team must validate all links."
                ),
                "force_partial_evaluation": True
            },
            {
                "gap_key": "final_security_determination_not_made",
                "condition": {"always": True},
                "message": (
                    "The pipeline does not perform binary or link scanning. "
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
            "Detects references to malware distribution, executable downloads, and malicious scripts.",
            "Identifies suspicious executable file type references and unsafe download instructions.",
            "Classifies malicious delivery content by type and risk level.",
            "Generates quarantine and security escalation signals."
        ],
        "what_this_policy_does_not_do": [
            "Does not scan attached binary files (out of current POC scope).",
            "Does not resolve or scan URLs against malware/phishing feeds.",
            "Does not perform sandbox execution of referenced files.",
            "Does not make final security determinations.",
            "Does not detect obfuscated code embedded in text as encoded strings."
        ]
    }
}
