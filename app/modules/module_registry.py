"""
app/modules/module_registry.py

Central registry of reusable modules.
"""

from app.modules.m01_data_assembly import run_m01_data_assembly
from app.modules.m02_language_and_spans import run_m02_language_and_spans
from app.modules.m03_rule_signals import run_m03_rule_signals
from app.modules.m05_entity_extraction import run_m05_entity_extraction
from app.modules.m07_llm_policy_analysis import run_m07_llm_policy_analysis
from app.modules.m08_evidence_matching import run_m08_evidence_matching
from app.modules.m16_policy_decision import run_m16_policy_decision
from app.modules.m17_result_packaging import run_m17_result_packaging


MODULE_REGISTRY = {
    "M01": run_m01_data_assembly,
    "M02": run_m02_language_and_spans,
    "M03": run_m03_rule_signals,
    "M05": run_m05_entity_extraction,
    "M07": run_m07_llm_policy_analysis,
    "M08": run_m08_evidence_matching,
    "M16": run_m16_policy_decision,
    "M17": run_m17_result_packaging,
}