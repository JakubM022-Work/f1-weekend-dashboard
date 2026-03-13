"""Stylowanie aplikacji - wszystkie klasy CSS"""

DASHBOARD_STYLES = """
<style>
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.2rem;
        max-width: 1320px;
    }

    .hero-card {
        background:
            radial-gradient(circle at top right, rgba(37, 99, 235, 0.22), transparent 30%),
            linear-gradient(135deg, #111827 0%, #0b1220 55%, #0f1b3d 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 28px;
        padding: 28px 30px 22px 30px;
        margin-bottom: 22px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.22);
    }

    .hero-topline {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 14px;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        color: #E5E7EB;
        border-radius: 999px;
        padding: 7px 12px;
        font-size: 0.85rem;
        font-weight: 700;
    }

    .hero-title {
        font-size: 2.35rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 8px;
        color: #F9FAFB;
    }

    .hero-subtitle {
        color: #9CA3AF;
        font-size: 1rem;
        margin: 0;
    }

    .quick-stats {
        margin-top: 20px;
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
    }

    .quick-stat-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 14px 16px;
        backdrop-filter: blur(6px);
    }

    .quick-stat-label {
        color: #9CA3AF;
        font-size: 0.82rem;
        margin-bottom: 6px;
    }

    .quick-stat-value {
        color: #F9FAFB;
        font-size: 1.25rem;
        font-weight: 800;
        line-height: 1.1;
    }

    .metric-card {
        background: linear-gradient(180deg, rgba(17,24,39,0.96) 0%, rgba(11,18,32,0.98) 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 18px 20px;
        min-height: 120px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    }

    .metric-label {
        font-size: 0.88rem;
        color: #9CA3AF;
        margin-bottom: 10px;
    }

    .metric-value {
        font-size: 1.35rem;
        font-weight: 800;
        line-height: 1.2;
        color: #F9FAFB;
    }

    .metric-subvalue {
        font-size: 0.95rem;
        color: #D1D5DB;
        margin-top: 8px;
    }

    .section-card {
        background: #0f172a;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
        padding: 20px;
        margin-top: 12px;
    }

    .section-title {
        font-size: 1.12rem;
        font-weight: 800;
        margin-bottom: 14px;
        color: #F9FAFB;
    }

    .ranking-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .ranking-card {
        background: linear-gradient(180deg, rgba(11,18,32,0.96) 0%, rgba(9,14,26,1) 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 14px 16px;
        transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
        box-shadow: 0 6px 18px rgba(0,0,0,0.10);
    }

    .ranking-card:hover {
        transform: translateY(-1px);
        border-color: rgba(255,255,255,0.14);
        box-shadow: 0 10px 24px rgba(0,0,0,0.18);
    }

    .ranking-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
    }

    .ranking-left {
        display: flex;
        align-items: center;
        gap: 14px;
        min-width: 0;
    }

    .ranking-pos {
        width: 36px;
        height: 36px;
        border-radius: 999px;
        background: #111827;
        border: 1px solid rgba(255,255,255,0.08);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        color: #E5E7EB;
        flex-shrink: 0;
    }

    .ranking-driver-block {
        min-width: 0;
    }

    .ranking-driver {
        font-weight: 800;
        font-size: 0.98rem;
        color: #F9FAFB;
        line-height: 1.2;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .ranking-team {
        font-size: 0.86rem;
        color: #9CA3AF;
        margin-top: 4px;
    }

    .team-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 999px;
        margin-right: 8px;
        vertical-align: middle;
        box-shadow: 0 0 10px rgba(255,255,255,0.08);
    }

    .pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 0.82rem;
        font-weight: 800;
        border: 1px solid rgba(255,255,255,0.08);
        white-space: nowrap;
    }

    .pill-green {
        background: rgba(22,163,74,0.15);
        color: #4ADE80;
    }

    .pill-red {
        background: rgba(220,38,38,0.15);
        color: #F87171;
    }

    .pill-gray {
        background: rgba(107,114,128,0.18);
        color: #D1D5DB;
    }

    .pill-status {
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 800;
        color: white;
        white-space: nowrap;
        border: 1px solid rgba(255,255,255,0.08);
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        overflow: hidden;
        box-shadow: 0 8px 24px rgba(0,0,0,0.10);
    }

    div[data-baseweb="tab-list"] {
        gap: 25px;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1f2a 0%, #202332 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
    }

    @media (max-width: 900px) {
        .quick-stats {
            grid-template-columns: 1fr;
        }

        .hero-title {
            font-size: 1.8rem;
        }

        .ranking-row {
            flex-direction: column;
            align-items: flex-start;
        }
    }
</style>
"""
