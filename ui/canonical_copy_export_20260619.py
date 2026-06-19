"""On-demand canonical-generation copy/export controls."""
from __future__ import annotations

from typing import Any, Mapping, MutableMapping
import streamlit as st

from core.canonical_runtime_20260617 import get_canonical
from core.compact_canonical_20260619 import get_compact_summary
from services.canonical_exports import all_text as _all_text, short_text as _short_text


def _m(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}



def render_canonical_copy_export(*, state: MutableMapping[str, Any] | None = None, plan: Mapping[str, Any] | None = None) -> None:
    state = state if state is not None else st.session_state
    canonical = get_canonical(state); summary = get_compact_summary(state); plan = dict(plan or state.get("position_sizing_plan_20260619") or {})
    if not canonical:
        return
    st.markdown("#### Copy and export — current canonical generation")
    cols = st.columns(3)
    actions = (("Copy Short", "short"), ("Copy All", "all"), ("Export", "export"))
    requested = None
    for col, (label, value) in zip(cols, actions):
        if col.button(label, key=f"canonical_{value}_prepare_20260619", use_container_width=True):
            requested = value
    if requested:
        identity = f"{canonical.get('run_id')}|{canonical.get('calculation_generation')}|{canonical.get('checksum')}"
        try:
            if requested == "short":
                state["canonical_copy_short_payload_20260619"] = {"identity": identity, "text": _short_text(canonical, summary, plan)}
            else:
                text = _all_text(canonical, summary, plan)
                state[f"canonical_{requested}_payload_20260619"] = {"identity": identity, "text": text}
        except Exception as exc:
            st.error(f"Copy/export preparation failed safely: {exc}")
    identity = f"{canonical.get('run_id')}|{canonical.get('calculation_generation')}|{canonical.get('checksum')}"
    for kind, label in (("short", "Copy prepared Short"), ("all", "Copy prepared All")):
        item = state.get(f"canonical_copy_{kind}_payload_20260619")
        if isinstance(item, Mapping) and item.get("identity") == identity:
            from ui.copy_tools import central_copy_button
            central_copy_button(label, item.get("text", ""), f"canonical_copy_{kind}_{canonical.get('calculation_generation')}", show_fallback=True)
    export_item = state.get("canonical_export_payload_20260619")
    if isinstance(export_item, Mapping) and export_item.get("identity") == identity:
        st.download_button("Download canonical generation JSON", export_item.get("text", "").encode("utf-8"), file_name=f"eurusd_h1_generation_{canonical.get('calculation_generation')}.json", mime="application/json", use_container_width=True, key="canonical_export_download_20260619")

__all__ = ["render_canonical_copy_export"]
