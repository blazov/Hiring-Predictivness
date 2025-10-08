
import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- Page config
st.set_page_config(page_title="Hiring Predictiveness & Lifecycle", page_icon="🎯", layout="wide")
st.title("🎯 Hiring Predictiveness & Lifecycle")
st.markdown(
    "Use the controls to explore how selection quality (r) and the post‑offer environment shape realized performance. "
    "Key metrics are leadership‑friendly and consistent across charts."
)

# -----------------------------
# Helpers
# -----------------------------
def pretty_pct(x): return f"{100*x:.1f}%"

def ten_box_counts_fixed_miss(success_rate):
    # Always 1 Miss in the hiring snapshot; Bar Raiser rounded from success_rate; Solid fills the rest.
    br = int(round(10 * success_rate))
    br = max(0, min(9, br))  # reserve at least 1 miss
    miss = 1
    solid = 10 - br - miss
    return br, solid, miss

def apply_environment_effect(br, solid, miss, preset_label, env_multiplier):
    # Upgrade/downgrade Bar Raisers using only Solid as the donor/recipient to keep a baseline Miss.
    # Then enforce minimum Miss count per preset.
    target_br = int(round(br * env_multiplier))

    if target_br > br:
        add = min(solid, target_br - br)
        br += add
        solid -= add
    elif target_br < br:
        drop = min(br, br - target_br)
        br -= drop
        solid += drop

    # Enforce baseline Miss: 1 normally; 2 for Below Average; 3 for Poor
    baseline_miss = 1
    if preset_label == "Below Average":
        baseline_miss = 2
    elif preset_label == "Poor":
        baseline_miss = 3

    if miss < baseline_miss:
        need = baseline_miss - miss
        from_solid = min(solid, need)
        solid -= from_solid
        miss += from_solid
        need -= from_solid
        if need > 0:
            from_br = min(br, need)
            br -= from_br
            miss += from_br

    total = br + solid + miss
    if total != 10:
        solid += (10 - total)
    return br, solid, miss

# -----------------------------
# Methods catalog (informational)
# -----------------------------
METHODS = {
    "🟢 Work Sample / Case Study": {"r": 0.54, "type": "exercise"},
    "🟢 Structured Interviews": {"r": 0.51, "type": "interview"},
    "🟢 Problem-Solving / Cognitive Test": {"r": 0.51, "type": "test"},
    "🟡 Job Knowledge Tests": {"r": 0.48, "type": "test"},
    "🟡 Values Alignment Interview": {"r": 0.35, "type": "interview"},
    "🟡 Reference Checks (behavioral/TORC)": {"r": 0.26, "type": "reference"},
    "🔴 Unstructured 'Go-with-the-flow' Interview": {"r": 0.20, "type": "interview"},
    "🔴 Evaluating based on 'Gut Feel'": {"r": 0.00, "type": "interview"},
}

# -----------------------------
# Sidebar: Hiring Inputs
# -----------------------------
with st.sidebar:
    st.header("🧩 Hiring Inputs")
    st.caption("These are the inputs that influence or determine the success of the hiring process.")
    role_clarity = st.slider("Role clarity & hiring-team alignment", 0.0, 1.0, 1.00, 0.01)
    interviewer_effectiveness = st.slider("Interviewer effectiveness (applies to interview steps)", 0.0, 1.0, 1.00, 0.01)
    num_stages = st.slider("Number of interview stages (1–8)", 1, 8, 4, 1)

    with st.expander("Advanced Assumptions"):
        BASE_RATE = st.slider("Share of applicants who are Bar Raisers (base rate)", 0.01, 0.50, 0.10, 0.01)
        SELECTION_RATIO = st.slider("Selection ratio (hires ÷ applicants)", 0.01, 0.20, 0.02, 0.01)

    st.markdown("---")
    st.header("🌱 Post-offer environment")
    preset_labels = ["Excellent", "Strong", "Good", "Average", "Below Average", "Poor"]
    preset_multipliers = {
        "Excellent": 1.50,
        "Strong": 1.25,
        "Good": 1.10,
        "Average": 1.00,
        "Below Average": 0.80,
        "Poor": 0.60,
    }
    preset_baselines = {
        "Excellent": 0.95,
        "Strong": 0.80,
        "Good": 0.65,
        "Average": 0.50,   # sets all individual factors to 0.5
        "Below Average": 0.35,
        "Poor": 0.20,
    }
    preset_label = st.selectbox("Environment Preset", preset_labels, index=3)

    fine_tune = st.checkbox("Fine‑tune individual factors", value=False)
    keys = ["m_eff","coaching","onboarding","enable","climate","growth","workload"]
    if fine_tune:
        base = preset_baselines[preset_label]
        if st.session_state.get("_last_preset") != preset_label:
            for k in keys: st.session_state[k] = base
            st.session_state["_last_preset"] = preset_label

        m_eff = st.slider("Manager effectiveness", 0.0, 1.0, st.session_state.get("m_eff", base), 0.01, key="m_eff")
        coaching = st.slider("Coaching & feedback quality", 0.0, 1.0, st.session_state.get("coaching", base), 0.01, key="coaching")
        onboarding = st.slider("Role clarity post‑offer / onboarding", 0.0, 1.0, st.session_state.get("onboarding", base), 0.01, key="onboarding")
        enable = st.slider("Enablement (tools/process)", 0.0, 1.0, st.session_state.get("enable", base), 0.01, key="enable")
        climate = st.slider("Team climate & psych safety", 0.0, 1.0, st.session_state.get("climate", base), 0.01, key="climate")
        growth = st.slider("Growth & recognition", 0.0, 1.0, st.session_state.get("growth", base), 0.01, key="growth")
        workload = st.slider("Workload sustainability", 0.0, 1.0, st.session_state.get("workload", base), 0.01, key="workload")

# -----------------------------
# Stages multiplier per your request — 3 and 4 close; 2 and 1 a bigger drop
# -----------------------------
stages_multiplier_map = {1:0.50, 2:0.75, 3:0.96, 4:1.00, 5:1.02, 6:1.00, 7:0.98, 8:0.96}
stages_factor = stages_multiplier_map.get(num_stages, 1.0)

# -----------------------------
# Select Hiring Methods (main)
# -----------------------------
st.subheader("Select Hiring Methods")
selected_methods = st.multiselect(
    "Pick methods used in the process:",
    options=list(METHODS.keys()),
    default=["🟢 Structured Interviews", "🟢 Work Sample / Case Study", "🟡 Values Alignment Interview"],
    help="Use 1–3 high‑quality complementary methods for signal without overburdening",
    key="selected_methods"
)
with st.expander("See all methods and meta-data"):
    for k, v in METHODS.items():
        st.write(f"{k} — base r={v['r']:.2f} — type={v['type']}")

if not selected_methods:
    st.warning("Select at least one method.")
    st.stop()

# -----------------------------
# Combine validities (reduced sensitivity + reference checks bonus)
# -----------------------------
r_list = [METHODS[m]["r"] for m in selected_methods if "Gut Feel" not in m]
base_r = max(r_list) if r_list else 0.0
num_high_quality = sum(1 for m in selected_methods if METHODS[m]["r"] >= 0.50)
incremental_bonus = 0.04 * (num_high_quality - 1) if num_high_quality > 1 else 0.0
gut_penalty = 0.75 if any("Gut Feel" in m for m in selected_methods) else 1.0
interview_count = sum(1 for m in selected_methods if METHODS[m]["type"] == "interview")
alpha = interview_count / len(selected_methods)

# Halved sensitivity: scale both sliders to 0.5..1.0 instead of 0..1.0
role_scaled = 0.5 * (1.0 + role_clarity)              # 0.0 -> 0.5, 1.0 -> 1.0
interviewer_scaled = 0.5 * (1.0 + interviewer_effectiveness)

# Reference checks provide a modest additive lift to r
ref_bonus = 0.02 if any("Reference Checks" in m for m in selected_methods) else 0.0

method_stack = (base_r + incremental_bonus + ref_bonus) * gut_penalty
method_stack = method_stack * (1 - alpha + alpha * interviewer_scaled * stages_factor)

# Values interview modest coupling to ORIGINAL role_clarity (kept as-is)
if any("Values Alignment" in m for m in selected_methods):
    method_stack *= (1.0 + 0.05 * max(0.0, (role_clarity - 0.80) / 0.20))

# Preliminary validity before assumptions
prelim_validity = method_stack * role_scaled

# -----------------------------
# Advanced Assumptions with stronger weight on r
# Defaults (0.10, 0.02) → multiplier = 1.00.
# Lower selection ratio (more selective) boosts r; lower base rate damps r; higher base rate lifts r.
# ±12% per factor (clamped) so the effect is visible but bounded.
# -----------------------------
def clamp(x, lo, hi): return max(lo, min(hi, x))

m_br = 1 + 0.12 * ((BASE_RATE - 0.10) / 0.39)         # 0.01..0.50 → up to ±12%
m_sr = 1 + 0.12 * ((0.02 - SELECTION_RATIO) / 0.19)   # 0.01..0.20 → up to ±12%
m_br = clamp(m_br, 0.88, 1.12)
m_sr = clamp(m_sr, 0.88, 1.12)

final_validity = float(min(max(prelim_validity * m_br * m_sr, 0.0), 0.65))

# -----------------------------
# Bar Raiser rate = r²
# -----------------------------
success_rate_process = final_validity ** 2
br_p, solid_p, miss_p = ten_box_counts_fixed_miss(success_rate_process)

# -----------------------------
# Post‑offer environment multiplier
# -----------------------------
if 'fine_tune' in locals() and fine_tune:
    env_factors = np.array([st.session_state[k] for k in keys])
    env_score = float(env_factors.mean())
    if env_score >= 0.5:
        env_multiplier = 1.0 + (env_score - 0.5) * (1.5 - 1.0) / 0.5
    else:
        env_multiplier = 1.0 - (0.5 - env_score) * (1.0 - 0.6) / 0.5
else:
    env_multiplier = preset_multipliers[preset_label]
    env_score = preset_baselines[preset_label]

rbr, rsolid, rmiss = apply_environment_effect(br_p, solid_p, miss_p, preset_label, env_multiplier)

# -----------------------------
# Key outcomes
# -----------------------------
st.header("📈 Key outcomes & explanations")
c1, c2, c3 = st.columns(3)
c1.metric("Predictive power (r)", f"{final_validity:.2f}")
c2.metric("How Much Our Process Can Explain", f"{final_validity**2:.0%}")
c3.metric("% of hires who are Bar Raisers", pretty_pct(success_rate_process))

st.caption("In this model, Bar Raiser % = r². Example: r = 0.65 ⇒ r² = 42% ⇒ ~4 Bar Raisers, 5 Solid, 1 Miss per 10 hires (before environment).")

# -----------------------------
# Visuals (hiring outcomes)
# -----------------------------
st.markdown('---')
st.header('📊 Hiring outcomes')

CURRENT_STATE = 0.35  # 35% Bar Raisers among hires today
col1, col2 = st.columns(2)
with col1:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=['Random'], y=[100 * BASE_RATE], marker_color='lightgray',
                         text=[pretty_pct(BASE_RATE)], textposition='auto'))
    fig.add_trace(go.Bar(x=['Current State'], y=[100 * CURRENT_STATE], marker_color='#9CA3AF',
                         text=[pretty_pct(CURRENT_STATE)], textposition='auto'))
    fig.add_trace(go.Bar(x=['New process'], y=[100 * success_rate_process], marker_color='#0047AB',
                         text=[pretty_pct(success_rate_process)], textposition='auto'))
    fig.update_layout(title='Chance of hiring a Bar Raiser',
                      yaxis_title='% of hires', yaxis_range=[0, 100], showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=['Bar Raiser','Solid','Miss'], y=[br_p, solid_p, miss_p],
                          marker_color=['#2E8B57','#4682B4','#B22222'],
                          text=[br_p, solid_p, miss_p], textposition='auto'))
    fig2.update_layout(title='Expected distribution per 10 hires',
                       yaxis_title='count out of 10', yaxis_range=[0,10], showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# Visuals (realized performance)
# -----------------------------
st.markdown('---')
st.header('🔁 Realized performance after offer')

cc1, cc2, cc3 = st.columns(3)
cc1.metric('Environment preset', preset_label)
cc2.metric('Environment score (0–1)', f'{env_score:.2f}')
cc3.metric('Talent multiplier', f'×{env_multiplier:.2f}')

colb1, colb2 = st.columns(2)
with colb1:
    b1 = go.Figure()
    b1.add_trace(go.Bar(x=['Bar Raiser','Solid','Miss'], y=[br_p, solid_p, miss_p],
                        marker_color=['#2E8B57','#4682B4','#B22222'],
                        text=[br_p, solid_p, miss_p], textposition='auto'))
    b1.update_layout(title='Before environment (at offer)', yaxis_title='count out of 10', yaxis_range=[0,10], showlegend=False)
    st.plotly_chart(b1, use_container_width=True)

with colb2:
    b2 = go.Figure()
    b2.add_trace(go.Bar(x=['Bar Raiser','Solid','Miss'], y=[rbr, rsolid, rmiss],
                        marker_color=['#2E8B57','#4682B4','#B22222'],
                        text=[rbr, rsolid, rmiss], textposition='auto'))
    b2.update_layout(title='After environment (realized)', yaxis_title='count out of 10', yaxis_range=[0,10], showlegend=False)
    st.plotly_chart(b2, use_container_width=True)

st.caption(
    'Misses are fixed at 1 in the hiring snapshot unless the environment is Below Average (min 2) or Poor (min 3). '
    'Excellent environments convert some Solid ⇒ Bar Raiser; weak environments convert some Bar Raiser ⇒ Solid/Miss.'
)
