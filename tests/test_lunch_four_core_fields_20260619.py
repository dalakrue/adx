from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_lunch_has_exactly_four_closed_first_core_expanders():
    source = text("ui/lunch_four_core_fields_20260619.py")
    assert source.count("with st.expander(") == 4
    assert source.count("expanded=False") == 4
    for label in (
        "Full Metric 25-Day History + 10 Decision Histories",
        "Power BI Price Prediction Projection",
        "25-Day Regime History + Lower / Medium / Higher Standards",
        "All Current Data Display",
    ):
        assert label in source


def test_lunch_root_delegates_only_to_four_field_renderer():
    source = text("tabs/final_lunch_upgrade_20260617.py")
    assert "render_lunch_four_core_fields" in source
    router = text("tabs/antd_page_router_20260615.py")
    assert 'if not subpage:' in router
    assert '"Lunch Four Core Fields"' in router
    nav = text("ui/antd_navigation_20260615.py")
    assert "LUNCH_CHILDREN: List[str] = []" in nav


def test_powerbi_does_not_add_nested_open_close_expanders():
    source = text("ui/powerbi_cached_renderer_20260619.py")
    assert 'with st.expander("Open / Close — Power BI error details"' not in source
    assert 'with st.expander("Open / Close — Projection integrity details"' not in source


def test_native_sidebar_is_not_rendered_or_reopenable():
    runner = text("core/app/runner.py")
    assert "sidebar_nav()" not in runner
    assert 'use_native_sidebar_fallback_20260619"] = False' in runner
    popup = text("ui/liquid_menu_popup_20260615.py")
    assert "with st.sidebar" not in popup
    assert "Open Sidebar" not in popup
    lock = text("ui/sidebar_hard_lock.py")
    assert '[data-testid="stSidebarCollapsedControl"]' in lock
    assert "def show_native_sidebar" in lock
    assert "Backward-compatible no-op" in lock
