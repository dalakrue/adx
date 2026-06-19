"""Authoritative four-field Lunch layout requested on 2026-06-19.

Display-only module. It reads the already-published Full Metric, Power BI,
regime-standard, priority, and canonical caches. It never starts a calculation,
changes protected trading logic, or creates an alternative decision engine.
"""
from __future__ import annotations

from typing import Any, Mapping, MutableMapping

import pandas as pd
import streamlit as st

from ui.table_ordering_20260618 import chronological_view


FULL_METRIC_FIELD = "1. Open / Close — Full Metric 25-Day History + 10 Decision Histories"
POWERBI_FIELD = "2. Open / Close — Power BI Price Prediction Projection"
REGIME_FIELD = "3. Open / Close — 25-Day Regime History + Lower / Medium / Higher Standards"
CURRENT_FIELD = "4. Open / Close — All Current Data Display"

_TIME_NAMES = ("Time", "time", "Datetime", "DateTime", "Timestamp", "Date", "Hour", "candle time")
_CURRENT_TABLE_ORDER = (
    ("Session Decision", ("session", "session_table")),
    ("10 Reverse Decision", ("reverse10",)),
    ("10 Entry Decision", ("entry", "entry_table")),
    ("10 Direction Decision", ("direction", "direction_table")),
    ("10 Hold Decision", ("hold", "hold_table")),
    ("10 Exit Decision", ("exit", "exit_table")),
    ("10 TP Decision", ("tp", "tp_table")),
    ("Metric Table", ("metric_table",)),
    ("Full Metric Table", ("full_metric_table",)),
)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _canonical(state: MutableMapping[str, Any]) -> Mapping[str, Any]:
    try:
        from core.canonical_runtime_20260617 import get_canonical
        value = get_canonical(state)
        return value if isinstance(value, Mapping) else {}
    except Exception:
        value = state.get("canonical_result_20260617") or state.get("canonical_result")
        return value if isinstance(value, Mapping) else {}


def _metric_result(state: MutableMapping[str, Any]) -> Mapping[str, Any]:
    for key in ("lunch_metric_result_cache", "full_metric_result_cache_20260618"):
        value = state.get(key)
        if isinstance(value, Mapping) and value.get("ok"):
            return value
    try:
        from core.system_wide_completion_20260618 import published_metric_result
        value = published_metric_result(state)
        return value if isinstance(value, Mapping) else {}
    except Exception:
        return {}


def _time_column(frame: pd.DataFrame) -> str | None:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return None
    direct = next((name for name in _TIME_NAMES if name in frame.columns), None)
    if direct:
        return direct
    normalized = {str(column).strip().lower(): str(column) for column in frame.columns}
    return next((normalized[name.lower()] for name in _TIME_NAMES if name.lower() in normalized), None)


def _history_25day(frame: pd.DataFrame, *, maximum_rows: int = 600) -> pd.DataFrame:
    """Return a display-only historical 25-day slice, newest completed H1 first."""
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return pd.DataFrame()
    work = frame.copy(deep=False)
    time_col = _time_column(work)
    if time_col:
        parsed = pd.to_datetime(work[time_col], errors="coerce", utc=True)
        if parsed.notna().any():
            latest = parsed.max()
            cutoff = latest - pd.Timedelta(days=25)
            work = work.loc[parsed >= cutoff].copy()
    try:
        work = chronological_view(work, row_limit=None)
    except Exception:
        if time_col:
            parsed = pd.to_datetime(work[time_col], errors="coerce", utc=True)
            work = work.assign(__lunch_sort_time=parsed).sort_values("__lunch_sort_time", ascending=False).drop(columns="__lunch_sort_time")
        else:
            work = work.reset_index(drop=True)
    return work.head(maximum_rows).reset_index(drop=True)


def _display_table(
    title: str,
    frame: pd.DataFrame,
    *,
    height: int = 430,
    empty_message: str | None = None,
    historical: bool = True,
) -> None:
    st.markdown(f"#### {title}")
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        st.info(empty_message or f"{title} is unavailable in the completed generation.")
        return
    st.dataframe(frame, use_container_width=True, hide_index=True, height=height)
    if historical:
        st.caption(f"Historical rows displayed: {len(frame):,}. The view is historical and is not limited to a current-hour snapshot.")
    else:
        st.caption(f"Current published rows displayed: {len(frame):,}. No historical rows are mixed into this current-data table.")


def _factor_histories(result: Mapping[str, Any]) -> dict[str, pd.DataFrame]:
    raw = result.get("history_by_factor")
    if not isinstance(raw, Mapping):
        return {}
    prepared: dict[str, pd.DataFrame] = {}
    for name, frame in raw.items():
        if isinstance(frame, pd.DataFrame) and not frame.empty:
            prepared[str(name)] = _history_25day(frame)
    return prepared


def _render_full_metric_history(state: MutableMapping[str, Any]) -> None:
    result = _metric_result(state)
    if not result or not result.get("ok"):
        st.warning("Full Metric history is not published yet. Run Calculation + Open Lunch in Settings once.")
        return

    overall = _history_25day(result.get("history") if isinstance(result.get("history"), pd.DataFrame) else pd.DataFrame())
    _display_table(
        "Overall Full Metric History — Last 25 Days",
        overall,
        height=500,
        empty_message="The completed generation has no overall Full Metric history rows.",
    )

    histories = _factor_histories(result)
    st.markdown("#### All 10 Decision Histories — Last 25 Days")
    if not histories:
        st.info("The completed generation has no separate ten-factor decision histories.")
        return

    names = list(histories)
    if len(names) != 10:
        st.warning(f"The published generation contains {len(names)} separate decision histories instead of 10. Every available history is shown; rerun once from Settings to rebuild missing published histories.")
    st.caption(f"All {len(names)} published decision histories are restored below. Each table is filtered to the same last-25-day historical window.")
    tabs = st.tabs(names)
    for tab, name in zip(tabs, names):
        with tab:
            frame = histories[name]
            if frame.empty:
                st.info(f"{name} has no rows in the last 25 days.")
            else:
                st.dataframe(frame, use_container_width=True, hide_index=True, height=410)
                st.caption(f"{name}: {len(frame):,} historical rows, newest completed H1 first.")


def _render_powerbi(state: MutableMapping[str, Any]) -> None:
    try:
        from ui.powerbi_cached_renderer_20260619 import render_cached_powerbi_projection
        render_cached_powerbi_projection(state=state)
    except Exception as exc:
        state["lunch_four_field_powerbi_error_20260619"] = repr(exc)
        st.error("The cached Power BI projection could not render. Its calculation cache was not changed.")
        st.code(f"{type(exc).__name__}: {exc}")


def _published_regime_tables(state: MutableMapping[str, Any], canonical: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("regime_standard_detail_tables_published_20260618", "regime_standard_detail_tables_20260617"):
        value = state.get(key)
        if isinstance(value, Mapping):
            return value
    regime = _mapping(canonical.get("regime"))
    for key in ("standard_detail_tables", "detail_tables", "regime_standard_detail_tables"):
        value = regime.get(key)
        if isinstance(value, Mapping):
            return value
    return {}


def _overall_regime_history(result: Mapping[str, Any]) -> pd.DataFrame:
    history = result.get("history")
    if not isinstance(history, pd.DataFrame) or history.empty:
        return pd.DataFrame()
    historical = _history_25day(history)
    if historical.empty:
        return historical
    tokens = ("regime", "alpha", "delta", "transition", "reliab", "priority", "knn", "greedy", "decision", "direction")
    time_col = _time_column(historical)
    chosen: list[str] = []
    if time_col:
        chosen.append(time_col)
    for column in historical.columns:
        text = str(column).lower()
        if any(token in text for token in tokens) and str(column) not in chosen:
            chosen.append(str(column))
    return historical[chosen].copy() if len(chosen) > 1 else historical


def _render_regime_history(state: MutableMapping[str, Any]) -> None:
    canonical = _canonical(state)
    result = _metric_result(state)
    _display_table(
        "Overall Regime History — Last 25 Days",
        _overall_regime_history(result),
        height=480,
        empty_message="The 25-day overall regime history is unavailable in the completed generation.",
    )

    details = _published_regime_tables(state, canonical)
    summary = state.get("regime_standard_table_20260617")
    if isinstance(summary, pd.DataFrame) and not summary.empty:
        _display_table("Three-Standard Summary", summary.reset_index(drop=True), height=220, historical=True)

    specs = (
        ("lower", "Lower Standard Regime History — Last 25 Days (1-Day Standard)"),
        ("medium", "Medium Standard Regime History — Last 25 Days (5-Day Standard)"),
        ("higher", "Higher Standard Regime History — Last 25 Days (25-Day Standard)"),
    )
    for key, title in specs:
        frame = details.get(key) if isinstance(details, Mapping) else None
        prepared = _history_25day(frame) if isinstance(frame, pd.DataFrame) else pd.DataFrame()
        _display_table(title, prepared, height=420)


def _current_priority_table(state: MutableMapping[str, Any], canonical: Mapping[str, Any]) -> pd.DataFrame:
    for key in ("canonical_priority_table_20260617", "finder_readonly_priority_table_20260618", "lunch_quick_decision_merged_table_20260617"):
        frame = state.get(key)
        if isinstance(frame, pd.DataFrame) and not frame.empty:
            work = frame.copy(deep=False)
            time_col = _time_column(work)
            if time_col:
                parsed = pd.to_datetime(work[time_col], errors="coerce", utc=True)
                if parsed.notna().any():
                    latest = parsed.max()
                    latest_rows = work.loc[parsed == latest].copy()
                    if not latest_rows.empty:
                        return latest_rows.reset_index(drop=True)
            return work.head(14).reset_index(drop=True)
    records = canonical.get("priority_table")
    if isinstance(records, list) and records:
        return pd.DataFrame.from_records(records).head(14)
    return pd.DataFrame()


def _current_identity_table(canonical: Mapping[str, Any]) -> pd.DataFrame:
    final = _mapping(canonical.get("final_decision"))
    regime = _mapping(canonical.get("regime"))
    market = _mapping(canonical.get("market"))
    rows = [
        ("Symbol", canonical.get("symbol", "EURUSD")),
        ("Timeframe", canonical.get("timeframe", "H1")),
        ("Calculation Generation", canonical.get("calculation_generation", "-")),
        ("Run ID", canonical.get("run_id", "-")),
        ("Latest Completed H1", canonical.get("latest_completed_candle_time", market.get("latest_completed_candle_time", "-"))),
        ("Current Decision", final.get("final_decision", "WAIT")),
        ("Directional Market View", final.get("directional_market_view", canonical.get("full_metric_direction", "WAIT"))),
        ("Less-Risky Decision", final.get("less_risky_decision", "WAIT")),
        ("Selected Horizon", final.get("selected_horizon", "-")),
        ("Current Major Regime", regime.get("major_regime", "UNKNOWN")),
        ("Regime Reliability", regime.get("reliability", regime.get("regime_reliability", "-"))),
        ("Decision Expiry", final.get("decision_expiry_time", canonical.get("expires_at", "-"))),
    ]
    return pd.DataFrame(rows, columns=["Current Data Field", "Value"])


def _render_current_data(state: MutableMapping[str, Any]) -> None:
    canonical = _canonical(state)
    result = _metric_result(state)
    if not canonical and not result:
        st.warning("Current synchronized data is not published yet. Run Calculation + Open Lunch in Settings once.")
        return

    try:
        from ui.trusted_operational_metrics_20260619 import render_trusted_operational_metrics
        render_trusted_operational_metrics(state=state)
    except Exception as exc:
        state["lunch_four_field_current_metrics_error_20260619"] = repr(exc)
        st.warning(f"Current operational cards skipped safely: {exc}")

    try:
        from core.compact_canonical_20260619 import get_compact_summary
        from ui.composite_summary_cards_20260619 import render_eight_cards
        summary = get_compact_summary(state)
        if summary:
            st.markdown("#### Current Canonical Summary Cards")
            render_eight_cards(summary, location="lunch_four_field_current_20260619")
    except Exception as exc:
        st.caption(f"Current summary cards skipped safely: {exc}")

    if canonical:
        _display_table("Current Canonical Identity and Decision", _current_identity_table(canonical), height=390, historical=False)

    priority = _current_priority_table(state, canonical)
    _display_table("Current H1 Priority / Ranking Data", priority, height=360, historical=False)

    position_plan = state.get("position_sizing_plan_20260619")
    if isinstance(position_plan, Mapping) and position_plan:
        plan_row = {
            "Status": position_plan.get("status", "-"),
            "Recommended Total Lots": position_plan.get("recommended_lots", 0),
            "Scale-In Entries": position_plan.get("scale_in_entries", 0),
            "Scale-In Splits": " + ".join(str(x) for x in position_plan.get("scale_in_splits", []) or []),
            "Planned Risk %": position_plan.get("planned_risk_pct", 0),
            "Planned Dollar Loss": position_plan.get("planned_dollar_loss", 0),
            "Estimated Margin": position_plan.get("margin_estimate", 0),
            "Reason": position_plan.get("reason", "-"),
        }
        _display_table("Current Published Position-Sizing Plan", pd.DataFrame([plan_row]), height=220, historical=False)

    if not isinstance(result, Mapping) or not result.get("ok"):
        st.info("Current Full Metric snapshot tables are not available in the published generation.")
        return

    seen: set[int] = set()
    for title, aliases in _CURRENT_TABLE_ORDER:
        frame = next((result.get(key) for key in aliases if isinstance(result.get(key), pd.DataFrame) and not result.get(key).empty), None)
        if not isinstance(frame, pd.DataFrame) or frame.empty or id(frame) in seen:
            continue
        seen.add(id(frame))
        # These are current/snapshot tables; preserve their protected factor order.
        _display_table(title, frame.reset_index(drop=True), height=min(500, max(230, 44 + min(len(frame), 16) * 28)), historical=False)


def render_lunch_four_core_fields(*, state: MutableMapping[str, Any] | None = None) -> None:
    """Render exactly four top-level Lunch open/close fields, all closed first."""
    state = state if state is not None else st.session_state
    st.markdown("### 🍱 Lunch — Four Core Fields")
    st.caption(
        "Exactly four core open/close fields. All start closed on first entry. "
        "Historical fields use the completed 25-day EURUSD H1 generation; current-only data is isolated in field 4."
    )

    with st.expander(FULL_METRIC_FIELD, expanded=False):
        _render_full_metric_history(state)

    with st.expander(POWERBI_FIELD, expanded=False):
        _render_powerbi(state)

    with st.expander(REGIME_FIELD, expanded=False):
        _render_regime_history(state)

    with st.expander(CURRENT_FIELD, expanded=False):
        _render_current_data(state)


__all__ = [
    "FULL_METRIC_FIELD",
    "POWERBI_FIELD",
    "REGIME_FIELD",
    "CURRENT_FIELD",
    "render_lunch_four_core_fields",
]
