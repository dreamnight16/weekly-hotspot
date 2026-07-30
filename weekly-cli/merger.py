"""Dual-layer merge: combines dialectical (core) and empirical (auxiliary) output per phase.

Merge rules:
1. Empirical confirms dialectical → merge with empiricalVerified=True
2. Empirical challenges dialectical → both kept, divergence flagged
3. Empirical degraded (None) → dialectical only, empiricalDegraded=True
4. Empirical supplements → appended with empiricalSupplemental markers
"""
from pydantic import BaseModel


def merge_phase(
    dialectical: BaseModel,
    empirical: dict | None,
) -> dict:
    """Merge dialectical and empirical output for one phase.

    Returns a dict with the merged output plus metadata flags.
    The merger does NOT resolve conflicts — it annotates them.
    """
    result = dialectical.model_dump()

    if empirical is None:
        result["empiricalVerified"] = False
        result["empiricalDegraded"] = True
        result["empiricalNotes"] = "实证层降级：数据不可用"
        return result

    # Empirical layer present
    result["empiricalVerified"] = empirical.get("verified", True)
    result["empiricalDegraded"] = False

    # If empirical challenges the dialectical analysis
    if empirical.get("challenges"):
        result["empiricalChallenges"] = empirical["challenges"]
        result["empiricalVerified"] = False

    # If empirical adds supplementary findings
    if empirical.get("supplements"):
        result["empiricalSupplemental"] = empirical["supplements"]

    # Merge any additional empirical data
    for key in ("verificationNote", "scoreCalibration", "dataContext"):
        if key in empirical:
            result[f"empirical_{key}"] = empirical[key]

    return result
