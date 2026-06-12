"""
app/policies/policy_registry.py

Central registry for all active moderation policies.

How to add a new policy:
    1. Create app/policy_configs/<policy_code>_config.py
    2. Add the LLM prompt to app/prompts/prompt_library.py
    3. Import the config here and add one entry to POLICY_REGISTRY
    4. Add the policy code to ENABLED_POLICIES in .env / local.settings.json
"""

from app.policies.generic_policy_runner import run_policy

# ── TYPE policies ──────────────────────────────────────────────────────────
from app.policy_configs.type_project_01_config import TYPE_PROJECT_01_CONFIG

# ── REG policies ───────────────────────────────────────────────────────────
from app.policy_configs.reg_01_config import REG_01_CONFIG
from app.policy_configs.reg_02_config import REG_02_CONFIG
from app.policy_configs.reg_03_config import REG_03_CONFIG
from app.policy_configs.reg_04_config import REG_04_CONFIG

# ── LEGAL policies ─────────────────────────────────────────────────────────
from app.policy_configs.legal_01_config import LEGAL_01_CONFIG
from app.policy_configs.legal_02_config import LEGAL_02_CONFIG
from app.policy_configs.legal_03_config import LEGAL_03_CONFIG
from app.policy_configs.legal_05_config import LEGAL_05_CONFIG

# ── MAL policies ───────────────────────────────────────────────────────────
from app.policy_configs.mal_01_config import MAL_01_CONFIG
from app.policy_configs.mal_02_config import MAL_02_CONFIG
from app.policy_configs.mal_03_config import MAL_03_CONFIG
from app.policy_configs.mal_04_config import MAL_04_CONFIG

# ── NUIS policies ──────────────────────────────────────────────────────────
from app.policy_configs.nuis_01_config import NUIS_01_CONFIG
from app.policy_configs.nuis_02_config import NUIS_02_CONFIG
from app.policy_configs.nuis_03_config import NUIS_03_CONFIG
from app.policy_configs.nuis_04_config import NUIS_04_CONFIG

# ── OFF policies ───────────────────────────────────────────────────────────
from app.policy_configs.off_01_config import OFF_01_CONFIG
from app.policy_configs.off_02_config import OFF_02_CONFIG
from app.policy_configs.off_03_config import OFF_03_CONFIG


POLICY_REGISTRY = {
    # ── TYPE ──────────────────────────────────────────────────────────────
    "TYPE-PROJECT-01": {
        "runner": run_policy,
        "config": TYPE_PROJECT_01_CONFIG
    },

    # ── REG ───────────────────────────────────────────────────────────────
    "REG-01": {
        "runner": run_policy,
        "config": REG_01_CONFIG
    },
    "REG-02": {
        "runner": run_policy,
        "config": REG_02_CONFIG
    },
    "REG-03": {
        "runner": run_policy,
        "config": REG_03_CONFIG
    },
    "REG-04": {
        "runner": run_policy,
        "config": REG_04_CONFIG
    },

    # ── LEGAL ─────────────────────────────────────────────────────────────
    "LEGAL-01": {
        "runner": run_policy,
        "config": LEGAL_01_CONFIG
    },
    "LEGAL-02": {
        "runner": run_policy,
        "config": LEGAL_02_CONFIG
    },
    "LEGAL-03": {
        "runner": run_policy,
        "config": LEGAL_03_CONFIG
    },
    "LEGAL-05": {
        "runner": run_policy,
        "config": LEGAL_05_CONFIG
    },

    # ── MAL ───────────────────────────────────────────────────────────────
    "MAL-01": {
        "runner": run_policy,
        "config": MAL_01_CONFIG
    },
    "MAL-02": {
        "runner": run_policy,
        "config": MAL_02_CONFIG
    },
    "MAL-03": {
        "runner": run_policy,
        "config": MAL_03_CONFIG
    },
    "MAL-04": {
        "runner": run_policy,
        "config": MAL_04_CONFIG
    },

    # ── NUIS ──────────────────────────────────────────────────────────────
    "NUIS-01": {
        "runner": run_policy,
        "config": NUIS_01_CONFIG
    },
    "NUIS-02": {
        "runner": run_policy,
        "config": NUIS_02_CONFIG
    },
    "NUIS-03": {
        "runner": run_policy,
        "config": NUIS_03_CONFIG
    },
    "NUIS-04": {
        "runner": run_policy,
        "config": NUIS_04_CONFIG
    },

    # ── OFF ───────────────────────────────────────────────────────────────
    "OFF-01": {
        "runner": run_policy,
        "config": OFF_01_CONFIG
    },
    "OFF-02": {
        "runner": run_policy,
        "config": OFF_02_CONFIG
    },
    "OFF-03": {
        "runner": run_policy,
        "config": OFF_03_CONFIG
    },
}
