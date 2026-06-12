"""
app/db.py

Purpose:
- Handles all Azure SQL operations.
- Keeps database code separate from moderation logic.
- Other files should NOT directly use pyodbc.

Source table (projects):
  SWA_ModerationTestSuite — Id is the primary key (IDENTITY column).
  SWA_Projects is NOT used in this setup.

Column mapping (SWA_ModerationTestSuite vs old LEGAL_PolicyTestSuite):
  Id              ← was TestCaseId
  ProjectName     ← was TestCaseName  (used as display name)
  CaseType        ← was PolicyCode    (value is always 'Active'; used as subtitle)
  (no Language column — defaults to 'English')
  ExpectedOutcome, ReasonForExpectedOutcome, ProjectDescription,
  ProjectGoal, ResourceDescription, Message — same names as before ✓

Moderation result tables (unchanged):
  ModerationRuns, ModerationLogs, PolicyResults,
  ModuleResults, FinalModerationResults
"""

import json
from typing import Any, Optional

import pyodbc

from app.logger import get_logger
from app.outcome_vocabulary import to_external_action
from config.settings import settings

logger = get_logger()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def to_json(value: Any) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, default=str)


def get_connection():
    conn_str = (
        f"DRIVER={{{settings.SQL_DRIVER}}};"
        f"SERVER={settings.SQL_SERVER};"
        f"DATABASE={settings.SQL_DATABASE};"
        f"UID={settings.SQL_USERNAME};"
        f"PWD={settings.SQL_PASSWORD};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)


# ─────────────────────────────────────────────────────────────────────────────
# Project list  (source: SWA_ModerationTestSuite)
# ─────────────────────────────────────────────────────────────────────────────

def get_projects():
    """
    Return summary list of all test cases for the UI sidebar.
    Uses Id directly as the project Id (IDENTITY primary key).
    """
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            Id,
            ProjectName,
            CaseType,
            ExpectedOutcome
        FROM SWA_ModerationTestSuite
        ORDER BY Id
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            # Id is the primary key — used directly as project Id
            "id":              row.Id,
            # ProjectName is the display name in the sidebar
            "projectName":     row.ProjectName,
            "countryName":     None,
            "languageCode":    "English",   # no Language column in this table
            # CaseType is always 'Active' in this dataset; used as subtitle
            "projectStatus":   row.CaseType,
            # Expected outcome colours the row in the UI
            "expectedOutcome": row.ExpectedOutcome,
        }
        for row in rows
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Single project fetch  (source: SWA_ModerationTestSuite)
# ─────────────────────────────────────────────────────────────────────────────

def get_project_by_id(project_id: int):
    """
    Return full project record from SWA_ModerationTestSuite by Id.

    The returned dict uses the exact field names that M01 and all pipeline
    modules expect (ProjectName, ProjectDescription, ProjectGoal,
    ResourceDescription, Message, LanguageCode) so the pipeline runs
    without any modifications.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            Id,
            ProjectName,
            ProjectSponsorFirstName,
            ProjectSponsorLastName,
            CaseType,
            IsPublished,
            IsVirtual,
            ProjectDescription,
            ProjectGoal,
            ResourceDescription,
            Message,
            ExpectedOutcome,
            ReasonForExpectedOutcome
        FROM SWA_ModerationTestSuite
        WHERE Id = ?
    """, project_id)

    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    columns = [column[0] for column in cursor.description]
    raw     = dict(zip(columns, row))
    conn.close()

    # Convert any datetime values to ISO strings
    for key, value in raw.items():
        if hasattr(value, "isoformat"):
            raw[key] = value.isoformat()

    # Build the project dict in the format the pipeline expects.
    # Field names must match exactly what M01's fields_to_scan and
    # context_fields reference in the REG/LEGAL policy configs.
    return {
        "Id":                       raw["Id"],
        "ProjectName":              raw.get("ProjectName")             or "",
        "ProjectSponsorFirstName":  raw.get("ProjectSponsorFirstName") or "",
        "ProjectSponsorLastName":   raw.get("ProjectSponsorLastName")  or "",
        "ProjectDescription":       raw.get("ProjectDescription")      or "",
        "ProjectGoal":              raw.get("ProjectGoal")             or "",
        "ResourceDescription":      raw.get("ResourceDescription")     or "",
        "Message":                  raw.get("Message")                 or "",
        # Metadata used by M01 context fields
        "LanguageCode":             "English",   # no Language column in this table
        "CountryName":              "Australia",
        "ProjectStatus":            raw.get("CaseType")                or "",
        "IsPublished":              int(raw.get("IsPublished") or 0),
        "IsVirtual":                int(raw.get("IsVirtual")   or 0),
        # Expected outcome for logging and history display
        "ExpectedPolicyOutcome":    raw.get("ExpectedOutcome"),
        "ExpectedNotes":            raw.get("ReasonForExpectedOutcome"),
        # Extra metadata — for logs, not used by the pipeline
        "_policyCode":              raw.get("CaseType"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Moderation history
# ─────────────────────────────────────────────────────────────────────────────

def get_moderation_history(limit: int = 200, offset: int = 0) -> list:
    """
    Return a summary list of all past moderation runs, newest first.
    Joins ModerationRuns → FinalModerationResults → SWA_ModerationTestSuite
    to resolve the project name for display.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            r.RunId,
            r.ProjectId,
            r.PolicyCode,
            r.RunStatus,
            CONVERT(varchar(30), r.StartedAt,   127) AS StartedAt,
            CONVERT(varchar(30), r.CompletedAt,  127) AS CompletedAt,
            ts.ProjectName                            AS ProjectName,
            f.FinalOutcome,
            f.FinalRiskLevel,
            f.FinalSuggestedAction,
            CAST(f.HumanDecisionRequired AS INT)      AS HumanDecisionRequired,
            CAST(f.EscalationFlag        AS INT)      AS EscalationFlag,
            f.ModeratorReasonNote
        FROM ModerationRuns r
        LEFT JOIN FinalModerationResults   f  ON f.RunId   = r.RunId
        LEFT JOIN SWA_ModerationTestSuite  ts ON ts.Id     = r.ProjectId
        ORDER BY r.StartedAt DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """, offset, limit)

    columns = [col[0] for col in cursor.description]
    rows    = cursor.fetchall()
    conn.close()

    return [dict(zip(columns, row)) for row in rows]


def get_run_policy_results(run_id: int) -> list:
    """Return per-policy results for a single run (for history detail expand)."""
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            PolicyCode,
            PolicyName,
            PolicyOutcome,
            RiskLevel,
            SuggestedAction,
            CAST(EscalationFlag        AS INT) AS EscalationFlag,
            CAST(HumanDecisionRequired AS INT) AS HumanDecisionRequired,
            Summary
        FROM PolicyResults
        WHERE RunId = ?
        ORDER BY PolicyResultId
    """, run_id)

    columns = [col[0] for col in cursor.description]
    rows    = cursor.fetchall()
    conn.close()

    return [dict(zip(columns, row)) for row in rows]


# ─────────────────────────────────────────────────────────────────────────────
# Moderation run lifecycle  (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

def create_moderation_run(
    project_id: int,
    policy_code: str,
    input_snapshot: dict
):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ModerationRuns (
            ProjectId,
            PolicyCode,
            RunStatus,
            TriggeredBy,
            InputSnapshotJson,
            StartedAt
        )
        OUTPUT INSERTED.RunId
        VALUES (?, ?, ?, ?, ?, SYSUTCDATETIME())
    """,
    project_id,
    policy_code,
    "RUNNING",
    "UI",
    to_json(input_snapshot)
    )

    run_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return run_id


def update_moderation_run_status(
    run_id: int,
    status: str,
    error_message: Optional[str] = None
):
    conn   = get_connection()
    cursor = conn.cursor()

    if status in ("COMPLETED", "FAILED"):
        cursor.execute("""
            UPDATE ModerationRuns
            SET
                RunStatus    = ?,
                CompletedAt  = SYSUTCDATETIME(),
                ErrorMessage = ?
            WHERE RunId = ?
        """, status, error_message, run_id)
    else:
        cursor.execute("""
            UPDATE ModerationRuns
            SET
                RunStatus    = ?,
                ErrorMessage = ?
            WHERE RunId = ?
        """, status, error_message, run_id)

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Logging  (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

def insert_moderation_log(
    run_id,
    project_id,
    policy_code,
    log_level,
    step_name,
    message,
    details=None
):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ModerationLogs (
            RunId,
            ProjectId,
            PolicyCode,
            LogLevel,
            StepName,
            Message,
            DetailsJson,
            CreatedAt
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
    """,
    run_id,
    project_id,
    policy_code,
    log_level,
    step_name,
    message,
    to_json(details)
    )

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Results persistence  (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

def insert_policy_result(
    run_id,
    project_id,
    final_result: dict
):
    details         = final_result.get("details", {}) or {}
    claims          = details.get("claims", []) or []
    evidence_issues = details.get("evidence_issues", []) or []

    highest_risk_claim_type = None
    for claim in claims:
        claim_types = claim.get("claim_types", [])
        if claim_types:
            highest_risk_claim_type = claim_types[0]
            break

    canonical_action = final_result.get("suggested_action")
    external_action  = to_external_action(canonical_action)

    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO PolicyResults (
            RunId,
            ProjectId,
            PolicyCode,
            PolicyName,
            PolicyOutcome,
            RiskLevel,
            SuggestedAction,
            ClaimCount,
            EvidenceNeededCount,
            EvidenceMissingCount,
            HighestRiskClaimType,
            RequestEvidenceFlag,
            EscalationFlag,
            HumanDecisionRequired,
            Summary,
            PolicyOutputJson,
            CreatedAt
        )
        OUTPUT INSERTED.PolicyResultId
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
    """,
    run_id,
    project_id,
    final_result.get("policy_code"),
    final_result.get("policy_name"),
    external_action,
    final_result.get("severity"),
    external_action,
    len(claims),
    sum(1 for c in claims if c.get("evidence_needed") or c.get("evidence_required")),
    len(evidence_issues),
    highest_risk_claim_type,
    1 if final_result.get("suggested_action") == "REQUEST_AMENDMENT" else 0,
    1 if final_result.get("suggested_action") == "ESCALATE" else 0,
    1 if final_result.get("manual_review_required") else 0,
    final_result.get("moderator_reason_note"),
    to_json(final_result)
    )

    policy_result_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return policy_result_id


def insert_module_result(
    run_id,
    policy_result_id,
    project_id,
    module_output: dict
):
    data            = module_output.get("data", {}) or {}
    claims          = data.get("claims", [])
    evidence_issues = data.get("evidence_issues", [])

    claim_count = data.get("claim_count")
    if claim_count is None and isinstance(claims, list):
        claim_count = len(claims)

    flagged_claim_count = None
    if isinstance(claims, list):
        flagged_claim_count = sum(
            1 for c in claims
            if c.get("evidence_needed") or c.get("evidence_required")
        )

    evidence_issue_count = data.get("evidence_issue_count")
    if evidence_issue_count is None and isinstance(evidence_issues, list):
        evidence_issue_count = len(evidence_issues)

    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ModuleResults (
            RunId,
            PolicyResultId,
            ProjectId,
            ModuleName,
            ModuleStatus,
            ModuleOutcome,
            ClaimCount,
            FlaggedClaimCount,
            EvidenceIssueCount,
            ModuleSummary,
            ModuleOutputJson,
            CreatedAt
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
    """,
    run_id,
    policy_result_id,
    project_id,
    f"{module_output.get('module_code')} - {module_output.get('module_name')}",
    module_output.get("module_status"),
    module_output.get("module_outcome"),
    claim_count,
    flagged_claim_count,
    evidence_issue_count,
    module_output.get("summary"),
    to_json(module_output)
    )

    conn.commit()
    conn.close()


def batch_insert_moderation_logs(entries: list):
    """Insert multiple ModerationLogs rows in a single connection + transaction."""
    if not entries:
        return

    conn   = get_connection()
    cursor = conn.cursor()

    try:
        for e in entries:
            cursor.execute("""
                INSERT INTO ModerationLogs (
                    RunId, ProjectId, PolicyCode, LogLevel,
                    StepName, Message, DetailsJson, CreatedAt
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
            """,
            e["run_id"], e["project_id"], e["policy_code"], e["log_level"],
            e["step_name"], e["message"], to_json(e.get("details")))
        conn.commit()
    finally:
        conn.close()


def batch_insert_module_results(
    run_id: int,
    policy_result_id,
    project_id: int,
    module_outputs: list
):
    """Insert multiple ModuleResults rows in a single connection + transaction."""
    if not module_outputs:
        return

    conn   = get_connection()
    cursor = conn.cursor()

    try:
        for module_output in module_outputs:
            data            = module_output.get("data", {}) or {}
            claims          = data.get("claims", [])
            evidence_issues = data.get("evidence_issues", [])

            claim_count = data.get("claim_count")
            if claim_count is None and isinstance(claims, list):
                claim_count = len(claims)

            flagged_claim_count = None
            if isinstance(claims, list):
                flagged_claim_count = sum(
                    1 for c in claims
                    if c.get("evidence_needed") or c.get("evidence_required")
                )

            evidence_issue_count = data.get("evidence_issue_count")
            if evidence_issue_count is None and isinstance(evidence_issues, list):
                evidence_issue_count = len(evidence_issues)

            cursor.execute("""
                INSERT INTO ModuleResults (
                    RunId, PolicyResultId, ProjectId,
                    ModuleName, ModuleStatus, ModuleOutcome,
                    ClaimCount, FlaggedClaimCount, EvidenceIssueCount,
                    ModuleSummary, ModuleOutputJson, CreatedAt
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
            """,
            run_id, policy_result_id, project_id,
            f"{module_output.get('module_code')} - {module_output.get('module_name')}",
            module_output.get("module_status"),
            module_output.get("module_outcome"),
            claim_count, flagged_claim_count, evidence_issue_count,
            module_output.get("summary"),
            to_json(module_output))
        conn.commit()
    finally:
        conn.close()


def insert_final_moderation_result(
    run_id,
    project_id,
    final_result: dict
):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO FinalModerationResults (
            RunId,
            ProjectId,
            FinalOutcome,
            FinalRiskLevel,
            FinalSuggestedAction,
            FinalReason,
            ModeratorReasonNote,
            RequestEvidenceFlag,
            EscalationFlag,
            HumanDecisionRequired,
            FinalOutputJson,
            CreatedAt
        )
        OUTPUT INSERTED.FinalResultId
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
    """,
    run_id,
    project_id,
    to_external_action(final_result.get("final_outcome")),
    final_result.get("final_risk_level"),
    to_external_action(final_result.get("final_suggested_action")),
    final_result.get("final_reason"),
    final_result.get("moderator_reason_note"),
    1 if final_result.get("request_evidence_flag") else 0,
    1 if final_result.get("escalation_flag") else 0,
    1 if final_result.get("human_decision_required") else 0,
    to_json(final_result)
    )

    final_result_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return final_result_id