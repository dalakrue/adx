"""Pure canonical-generation copy/export payload builders.

UI modules call these functions only after the user requests a copy or export,
so large JSON serialization is not performed on every Streamlit rerun.
"""
from __future__ import annotations

import json
from typing import Any, Mapping


def _m(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def short_text(canonical: Mapping[str, Any], summary: Mapping[str, Any], plan: Mapping[str, Any]) -> str:
    identity = _m(summary.get("identity")); decision = _m(summary.get("decision")); scores = _m(summary.get("scores"))
    priority = _m(summary.get("priority")); regime = _m(summary.get("regime")); uncertainty = _m(summary.get("uncertainty"))
    final = _m(canonical.get("final_decision"))
    reasons = [str(x) for x in list(final.get("blocking_reasons") or [])[:3]]
    return "\n".join([
        f"Symbol/timeframe: {identity.get('symbol','EURUSD')} {identity.get('timeframe','H1')}",
        f"Run ID/generation: {identity.get('run_id','-')} / {identity.get('calculation_generation','-')}",
        f"Schema/checksum: {canonical.get('schema_version','-')} / {canonical.get('checksum','-')}",
        f"Completed candle: {identity.get('latest_completed_candle_time','-')}",
        f"Decision: {decision.get('current_decision','WAIT')}",
        f"Less-risky decision: {decision.get('less_risky_bias','WAIT')}",
        f"Priority: {priority.get('opportunity_quality','WATCH')} (rank {priority.get('current_rank','N/A')})",
        f"Regime: {regime.get('directional_regime','UNKNOWN')}",
        f"Reliability: {float(regime.get('regime_reliability') or 0):.1f}%",
        "Master/Entry/Hold/TP/Exit Risk: " + "/".join(f"{float(scores.get(k,0) or 0):.2f}" for k in ("master","entry","hold","tp","exit_risk")),
        f"Uncertainty/error: {float(uncertainty.get('combined',0) or 0):.1f}% / {float(final.get('error_estimate_pct') or 0):.1f}%",
        f"Recommended total lots: {float(plan.get('recommended_lots') or 0):.2f}",
        f"Stop distance: {float(_m(plan.get('inputs')).get('stop_loss_pips') or 0):.1f} pips",
        f"Planned risk: ${float(plan.get('planned_dollar_loss') or 0):.2f} ({float(plan.get('planned_risk_pct') or 0):.2f}%)",
        f"Estimated margin: ${float(plan.get('margin_estimate') or 0):.2f} ({float(plan.get('margin_pct') or 0):.2f}%)",
        f"Risk status: {plan.get('status','BLOCK')} — {plan.get('reason','No risk plan')}",
        "Top reasons: " + ("; ".join(reasons) if reasons else str(decision.get("main_reason") or "No blockers")),
    ])


def _json_default(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        try:
            return value.to_dict("records")
        except Exception:
            try:
                return value.to_dict()
            except Exception:
                pass
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return str(value)


def all_text(canonical: Mapping[str, Any], summary: Mapping[str, Any], plan: Mapping[str, Any]) -> str:
    payload = dict(canonical)
    payload["run_id"] = canonical.get("run_id")
    payload["generation"] = canonical.get("calculation_generation")
    payload["schema_version"] = canonical.get("schema_version")
    payload["checksum"] = canonical.get("checksum")
    payload["completed_candle"] = canonical.get("latest_completed_candle_time")
    payload["risk_sizing_inputs"] = plan.get("inputs", {})
    payload["risk_sizing_outputs"] = {k: v for k, v in plan.items() if k != "inputs"}
    payload["compact_display_summary"] = dict(summary)
    return json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default)


__all__ = ["short_text", "all_text"]
