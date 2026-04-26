import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(
    page_title="SomNexus Decision Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CONSTANTS ──────────────────────────────────────────────────────────────
DIG_RATE  = 0.009   # 0.9% digital margin
CASH_RATE = 0.005   # 0.5% cashout margin
DAYS      = 26

# ── CUSTOM CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stMetricValue"]  { font-size: 1.55rem !important; }
[data-testid="stMetricLabel"]  { font-size: 0.70rem !important;
                                  text-transform: uppercase;
                                  letter-spacing: 0.05em; }
section[data-testid="stSidebar"] { background: #111827; }
.block-container { padding-top: 1rem; }

.formula-box {
    background: #1E293B;
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 10px;
    padding: 14px 16px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    line-height: 2;
    margin-bottom: 10px;
}
.insight-box {
    background: rgba(16,185,129,.08);
    border: 1px solid rgba(16,185,129,.25);
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 13px;
    margin-top: 8px;
    line-height: 1.7;
}
.alert-box {
    background: rgba(239,68,68,.08);
    border: 1px solid rgba(239,68,68,.25);
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 13px;
    margin-top: 6px;
    line-height: 1.7;
}
.warn-box {
    background: rgba(245,158,11,.08);
    border: 1px solid rgba(245,158,11,.25);
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 13px;
    margin-top: 6px;
    line-height: 1.7;
}
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💱 SomNexus")
    view = st.radio(
        "View as",
        ["🏛️ Admin / Investor", "👤 Agent", "🏪 Merchant", "🏢 Company"],
        index=0
    )
    st.markdown("---")

    st.markdown("### 📊 Volume inputs")
    volume      = st.number_input("Total monthly volume (USD)",
                                  100_000, 50_000_000, 6_200_000, 100_000)
    digital_pct = st.slider("Digital % of volume", 0, 100, 48, 1)
    cash_pct    = 100 - digital_pct

    st.markdown("### 💸 Cost structure")
    whatsapp_c  = st.number_input("WhatsApp cost (USD)",  0, 50_000,  12_000, 500)
    incentive_c = st.number_input("Incentives paid (USD)",0, 100_000, 18_000, 500)
    agent_pay_c = st.number_input("Agent payouts (USD)",  0, 50_000,   8_200, 100)
    fixed_c     = st.number_input("Fixed cost (USD)",     0, 200_000,  40_000, 1_000)

    st.markdown("### 👥 Agent model")
    agent_count = st.number_input("Active agents",     100, 20_000, 1_200, 100)
    tx_per_day  = st.slider("Tx per agent per day",    1, 50, 5)
    avg_tx_size = st.number_input("Avg tx size (USD)", 10, 1_000, 100, 10)
    agent_comm  = st.slider("Agent commission %",      0.0, 2.5, 1.0, 0.1)

    st.markdown("### 🔮 Scenario controls")
    growth      = st.slider("Volume growth % (next month)", -30, 200, 40, 5)
    dig_boost   = st.slider("Digital adoption boost (pp)",  -20, 40, 10, 2)
    agent_scale = st.slider("Agent scale factor (best)",    0.5, 5.0, 1.5, 0.1)
    comm_min    = st.slider("Commission range min %",       0.1, 1.5, 0.3, 0.1)
    comm_max    = st.slider("Commission range max %",       0.5, 3.0, 2.0, 0.1)

# ── CORE CALCULATIONS ──────────────────────────────────────────────────────
dig_vol    = volume * (digital_pct / 100)
cash_vol   = volume - dig_vol
dig_rev    = dig_vol  * DIG_RATE
cash_rev   = cash_vol * CASH_RATE
total_rev  = dig_rev + cash_rev
total_cost = whatsapp_c + incentive_c + agent_pay_c + fixed_c
net_profit = total_rev - total_cost
blended    = (digital_pct / 100 * DIG_RATE) + (cash_pct / 100 * CASH_RATE)
be_vol     = fixed_c / blended if blended > 0 else float("nan")
be_50      = fixed_c / (0.5 * DIG_RATE + 0.5 * CASH_RATE)
be_60      = fixed_c / (0.6 * DIG_RATE + 0.4 * CASH_RATE)
be_70      = fixed_c / (0.7 * DIG_RATE + 0.3 * CASH_RATE)

agent_take   = agent_comm / 100
ag_tx_month  = tx_per_day * DAYS
ag_rev_pt    = avg_tx_size * agent_take
ag_monthly_r = ag_tx_month * ag_rev_pt
ag_op_cost   = volume / max(1, agent_count) * 0.002
ag_profit    = ag_monthly_r - ag_op_cost
be_tx        = ag_op_cost / max(0.0001, avg_tx_size * agent_take * DAYS)

profitable   = net_profit >= 0
status_emoji = "🟢" if profitable else "🔴"

# ── PAGE HEADER ────────────────────────────────────────────────────────────
st.markdown(f"# {status_emoji} SomNexus Decision Engine")
st.caption(
    f"{'✅ Profitable' if profitable else '⚠️ Below break-even'} · "
    f"{view.split()[-1]} view · May 2025"
)

# ══════════════════════════════════════════════════════════════════════════
#  ADMIN / INVESTOR VIEW
# ══════════════════════════════════════════════════════════════════════════
if "Admin" in view:

    # ── TOP KPIs ──────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Volume",  f"${volume:,.0f}",     "↑ 12% vs Apr")
    k2.metric("Digital Rate",  f"{digital_pct}%",
              "⚠️ Below target" if digital_pct < 60 else "✅ Above target",
              delta_color="inverse" if digital_pct < 60 else "normal")
    k3.metric("Total Revenue", f"${total_rev:,.0f}",  "↑ 8% vs Apr")
    k4.metric("Net Profit",    f"${net_profit:+,.0f}",
              "Profitable" if profitable else "Loss",
              delta_color="normal" if profitable else "inverse")

    st.markdown("---")
    # ── BREAK-EVEN ENGINE ─────────────────────────────────────────────────
    st.subheader("🔥 Break-even Engine")
    b1, b2, b3 = st.columns([1.1, 1, 1.1])

    with b1:
        st.markdown("**Break-even status**")
        gauge_pct = min(100, int(total_rev / max(1, fixed_c * 2) * 100))
        st.progress(gauge_pct)
        st.markdown(f"""
<div class="formula-box">
Break-even target&nbsp;: <b style="color:#F59E0B">${fixed_c:,.0f}</b><br>
Current revenue&nbsp;&nbsp;&nbsp;: <b style="color:#3B82F6">${total_rev:,.0f}</b><br>
Net profit&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: <b style="color:{'#10B981' if profitable else '#EF4444'}">{net_profit:+,.0f}</b><br>
Status&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: <b>{'🟢 PROFITABLE' if profitable else '🔴 BELOW BREAK-EVEN'}</b>
</div>""", unsafe_allow_html=True)
        if profitable:
            extra_profit = volume * (0.1 * (DIG_RATE - CASH_RATE))
            st.markdown(f"""<div class="insight-box">
✅ <b>${net_profit:,.0f} above break-even</b><br>
+10% digital rate → estimated <b>+${extra_profit:,.0f} more profit</b>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="alert-box">
❌ Short by <b>${abs(net_profit):,.0f}</b><br>
Increase volume OR raise digital rate to become profitable.
</div>""", unsafe_allow_html=True)

    with b2:
        st.markdown("**Volume needed to break even**")
        st.markdown(f"""
<div class="formula-box">
At <b>50%</b> digital&nbsp;:<br>
&nbsp;&nbsp;<b style="color:#EF4444">${be_50:,.0f}</b> volume needed<br><br>
At <b>60%</b> digital&nbsp;:<br>
&nbsp;&nbsp;<b style="color:#F59E0B">${be_60:,.0f}</b> volume needed<br><br>
At <b>70%</b> digital&nbsp;:<br>
&nbsp;&nbsp;<b style="color:#10B981">${be_70:,.0f}</b> volume needed<br><br>
Current volume&nbsp;: <b>${volume:,.0f}</b>
</div>""", unsafe_allow_html=True)
        st.caption("Higher digital % → less volume needed to break even")

    with b3:
        st.markdown("**Exact revenue formula**")
        st.markdown(f"""
<div class="formula-box">
Digital revenue&nbsp;:<br>
&nbsp;&nbsp;${dig_vol:,.0f} × 0.9%<br>
&nbsp;&nbsp;= <b style="color:#10B981">${dig_rev:,.0f}</b><br><br>
Cash-out revenue&nbsp;:<br>
&nbsp;&nbsp;${cash_vol:,.0f} × 0.5%<br>
&nbsp;&nbsp;= <b style="color:#3B82F6">${cash_rev:,.0f}</b><br><br>
<b>Total Revenue = ${total_rev:,.0f}</b>
</div>""", unsafe_allow_html=True)

    # ── COST LAYER ────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("💸 Cost Layer vs Revenue")
    c1, c2 = st.columns([1.3, 1])

    with c1:
        cost_df = pd.DataFrame({
            "Category": ["WhatsApp fees", "Incentives paid",
                         "Agent payouts",  "Fixed cost"],
            "Cost":     [whatsapp_c, incentive_c, agent_pay_c, fixed_c]
        })
        bar_cost = alt.Chart(cost_df).mark_bar(
            cornerRadiusTopLeft=5, cornerRadiusTopRight=5
        ).encode(
            x=alt.X("Category:N", sort="-y",
                    axis=alt.Axis(labelAngle=-20, labelLimit=120)),
            y=alt.Y("Cost:Q", title="USD"),
            color=alt.Color("Category:N",
                scale=alt.Scale(range=["#3B82F6","#10B981","#8B5CF6","#F59E0B"]),
                legend=None),
            tooltip=["Category", "Cost"]
        ).properties(height=230)
        rev_rule = alt.Chart(pd.DataFrame({"y": [total_rev]})).mark_rule(
            color="#EF4444", strokeDash=[6, 3], size=2
        ).encode(y="y:Q")
        st.altair_chart(bar_cost + rev_rule, use_container_width=True)
        st.caption("Red dashed = total revenue. Cost bars above it contribute to loss.")

    with c2:
        st.markdown(f"""
<div class="formula-box">
Profit = Revenue − Costs<br><br>
WhatsApp fees&nbsp; : -${whatsapp_c:>9,.0f}<br>
Incentives&nbsp;&nbsp;&nbsp;&nbsp; : -${incentive_c:>9,.0f}<br>
Agent payouts&nbsp; : -${agent_pay_c:>9,.0f}<br>
Fixed cost&nbsp;&nbsp;&nbsp;&nbsp; : -${fixed_c:>9,.0f}<br>
─────────────────────────<br>
Total cost&nbsp;&nbsp;&nbsp;&nbsp; : <b style="color:#EF4444">-${total_cost:>9,.0f}</b><br>
Total revenue&nbsp; : <b style="color:#3B82F6"> ${total_rev:>9,.0f}</b><br>
─────────────────────────<br>
Net profit&nbsp;&nbsp;&nbsp;&nbsp; : <b style="color:{'#10B981' if profitable else '#EF4444'}">{net_profit:>+10,.0f}</b>
</div>""", unsafe_allow_html=True)
        save = int(whatsapp_c * 0.2)
        st.info(f"💡 Reduce WhatsApp msgs by 20% → save **${save:,}/month**")

    # ── DIGITAL % PROFIT SENSITIVITY ──────────────────────────────────────
    st.markdown("---")
    st.subheader("📈 Digital % → Profit Impact (Core Engine)")
    dig_range = np.arange(0, 101, 5)
    sens_rows = []
    for d in dig_range:
        dv = volume * (d / 100)
        cv = volume - dv
        r  = dv * DIG_RATE + cv * CASH_RATE
        p  = r - total_cost
        sens_rows.append({"Digital %": int(d), "Net Profit": round(p)})
    sens_df = pd.DataFrame(sens_rows)

    sens_line = alt.Chart(sens_df).mark_line(
        point=True, strokeWidth=2.5, color="#3B82F6"
    ).encode(
        x=alt.X("Digital %:Q"),
        y=alt.Y("Net Profit:Q", title="Net Profit (USD)"),
        tooltip=["Digital %", "Net Profit"]
    )
    zero_rule = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(
        color="#EF4444", strokeDash=[5, 3], size=1.5
    ).encode(y="y:Q")
    cur_rule = alt.Chart(pd.DataFrame({"x": [digital_pct]})).mark_rule(
        color="#F59E0B", strokeDash=[4, 3], size=1.5
    ).encode(x="x:Q")
    st.altair_chart(sens_line + zero_rule + cur_rule, use_container_width=True)

    profit_60 = (volume * 0.6 * DIG_RATE + volume * 0.4 * CASH_RATE) - total_cost
    profit_70 = (volume * 0.7 * DIG_RATE + volume * 0.3 * CASH_RATE) - total_cost
    col_a, col_b = st.columns(2)
    col_a.success(f"📌 At **60% digital** → profit **${profit_60:,.0f}**")
    col_b.success(f"🚀 At **70% digital** → profit **${profit_70:,.0f}**")

    # ── WHAT-IF SIMULATOR ─────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🎛️ What-If Simulator")
    st.caption("Move sliders to project the impact in real time")
    w1, w2 = st.columns([1, 1.3])

    with w1:
        sim_dig  = st.slider("Simulated digital %",   0,   100, min(digital_pct + 10, 100), 1)
        sim_vol  = st.slider("Simulated volume ($M)",  1.0, 20.0, volume / 1_000_000, 0.1)
        sim_inc  = st.slider("Simulated incentive %",  0.0, 1.0,  incentive_c / volume * 100 if volume > 0 else 0.3, 0.05)

    sim_v   = sim_vol * 1_000_000
    sim_dv  = sim_v * (sim_dig / 100)
    sim_cv  = sim_v - sim_dv
    sim_rev = sim_dv * DIG_RATE + sim_cv * CASH_RATE
    sim_inc_cost = sim_v * (sim_inc / 100)
    sim_cost = whatsapp_c + sim_inc_cost + agent_pay_c + fixed_c
    sim_prof = sim_rev - sim_cost
    sim_bm   = (sim_dig / 100 * DIG_RATE) + ((100 - sim_dig) / 100 * CASH_RATE)
    sim_be   = fixed_c / sim_bm if sim_bm > 0 else float("nan")
    days_faster = max(0, int(30 * (net_profit / max(1, sim_prof) if sim_prof > 0 else 0)))

    with w2:
        p1, p2 = st.columns(2)
        p1.metric("Projected Revenue",  f"${sim_rev:,.0f}")
        p2.metric("Projected Cost",     f"${sim_cost:,.0f}")
        p1.metric("Blended Margin",     f"{sim_bm * 10000:.0f} bps")
        p2.metric("Break-even Volume",  f"${sim_be:,.0f}")
        st.metric("🎯 Projected Profit",
                  f"${sim_prof:+,.0f}",
                  f"vs current ${net_profit:+,.0f}",
                  delta_color="normal" if sim_prof >= net_profit else "inverse")
        if sim_prof > 0:
            st.markdown(f"""<div class="insight-box">
✅ <b>Profitable at these settings</b><br>
Break-even reached earlier by approx <b>{days_faster} days</b>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="alert-box">
❌ Still unprofitable — increase digital % or reduce incentives
</div>""", unsafe_allow_html=True)

    # ── DAILY TARGET ENGINE ───────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📅 Daily Target Engine")
    daily_vol_target = volume / 30
    daily_rev_target = total_rev / 30
    daily_prof       = net_profit / 30
    be_day_of_month  = int(30 * fixed_c / max(1, total_rev))

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Daily volume needed", f"${daily_vol_target:,.0f}")
    d2.metric("Daily revenue",       f"${daily_rev_target:,.0f}")
    d3.metric("Daily profit",        f"${daily_prof:,.0f}")
    d4.metric("Break-even day",      f"Day {be_day_of_month} of 30")
    st.info(
        "🎯 **Today's focus:** Push grocery merchant digital payments · "
        "Bajaj/taxi driver conversions · Remind agents: hit 60% digital for bonus"
    )

    # ── SCENARIO PLANNER ──────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🎯 Scenario Planner — Worst / Base / Best")

    def run_scenario(vol_mult, dig_pp, ag_mult):
        v  = volume * vol_mult
        d  = min(1.0, max(0.0, digital_pct / 100 + dig_pp / 100))
        dv = v * d
        cv = v - dv
        r  = dv * DIG_RATE + cv * CASH_RATE
        p  = r - total_cost
        return {"Volume": v, "Digital %": d * 100, "Revenue": r, "Profit": p,
                "Agents": int(agent_count * ag_mult)}

    g     = 1 + growth / 100
    worst = run_scenario(1 + growth / 100 * 0.3,  -5,                0.8)
    base  = run_scenario(g,                         dig_boost,         1.0)
    best  = run_scenario(1 + growth / 100 * 1.5,   dig_boost * 1.5,   agent_scale)

    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("🔴 Worst — Profit", f"${worst['Profit']:,.0f}",
               f"Vol ${worst['Volume']:,.0f}")
    sc2.metric("🟡 Base — Profit",  f"${base['Profit']:,.0f}",
               f"Vol ${base['Volume']:,.0f}")
    sc3.metric("🟢 Best — Profit",  f"${best['Profit']:,.0f}",
               f"Vol ${best['Volume']:,.0f}")

    sc_df = pd.DataFrame([
        {"Scenario": "Worst", "Company Profit": worst["Profit"],
         "Agent Pool": ag_profit * worst["Agents"]},
        {"Scenario": "Base",  "Company Profit": base["Profit"],
         "Agent Pool": ag_profit * base["Agents"]},
        {"Scenario": "Best",  "Company Profit": best["Profit"],
         "Agent Pool": ag_profit * best["Agents"]},
    ])
    sc_melt = sc_df.melt("Scenario", var_name="Type", value_name="Value")
    sc_bar = alt.Chart(sc_melt).mark_bar(
        cornerRadiusTopLeft=5, cornerRadiusTopRight=5
    ).encode(
        x=alt.X("Scenario:N", sort=["Worst","Base","Best"],
                axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Value:Q", title="Profit (USD)"),
        color=alt.Color("Type:N",
            scale=alt.Scale(domain=["Company Profit","Agent Pool"],
                            range=["#3B82F6","#10B981"])),
        xOffset="Type:N",
        tooltip=["Scenario","Type","Value"]
    ).properties(height=220)
    st.altair_chart(sc_bar, use_container_width=True)

    # ── AI INSIGHTS ───────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🧠 AI Insights & Alerts")
    ai1, ai2 = st.columns(2)
    with ai1:
        st.markdown(f"""<div class="insight-box">
<b>System insights:</b><br>
→ Digital rate {digital_pct}% — {'below' if digital_pct < 60 else 'above'} the 60% profitability threshold<br>
→ At current trajectory: {'on track' if profitable else 'will miss break-even'}<br>
→ Recommendation: Push grocery incentives in Zone 3 — highest digital conversion<br>
→ If digital hits 60%: profit = <b>${profit_60:,.0f}</b>
</div>""", unsafe_allow_html=True)
    with ai2:
        st.markdown(f"""<div class="{'insight-box' if profitable else 'alert-box'}">
<b>Alert status:</b><br>
{'✅ No critical alerts' if profitable else '🚨 Below break-even — action needed'}<br>
⚠️ Digital rate below 50% — agent liquidity risk<br>
⚠️ High cash-out spike detected mid-month<br>
💡 Reduce WhatsApp by 20% → save ${int(whatsapp_c * 0.2):,}/month
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
#  AGENT VIEW
# ══════════════════════════════════════════════════════════════════════════
elif "Agent" in view:
    st.subheader("👤 Your Agent Dashboard")

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("You generated",  f"${volume / max(1, agent_count):,.0f}",
              "Your volume this month")
    a2.metric("Your earnings",  f"${ag_monthly_r:,.0f}",
              f"{agent_comm}% commission")
    a3.metric("Your rank",      "#12 / 240",   "↑ 4 positions this week")
    a4.metric("Your digital %", "62%",         "+14pp vs network avg (48%)")

    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Your contribution vs network")
        comp_df = pd.DataFrame({
            "Category":  ["You",  "Network avg"],
            "Digital %": [62,     48]
        })
        comp_bar = alt.Chart(comp_df).mark_bar(
            cornerRadiusTopLeft=5, cornerRadiusTopRight=5
        ).encode(
            x=alt.X("Category:N", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Digital %:Q", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("Category:N",
                scale=alt.Scale(domain=["You","Network avg"],
                                range=["#10B981","#F59E0B"]), legend=None),
            tooltip=["Category","Digital %"]
        ).properties(height=200)
        st.altair_chart(comp_bar, use_container_width=True)
        st.success("🌟 You are outperforming the network by **+14pp**. Keep pushing digital!")

        st.markdown("#### Your earnings formula")
        monthly_vol_agent = volume / max(1, agent_count)
        st.markdown(f"""
<div class="formula-box">
Your volume&nbsp;&nbsp;&nbsp;: ${monthly_vol_agent:,.0f}<br>
Commission&nbsp;&nbsp;&nbsp;&nbsp;: {agent_comm}%<br>
─────────────────────<br>
Earnings/month : <b style="color:#10B981">${ag_monthly_r:,.0f}</b><br>
Daily take-home: <b style="color:#10B981">${ag_monthly_r / DAYS:,.0f}</b><br>
Break-even tx/d: <b style="color:#F59E0B">{be_tx:.1f} tx/day</b>
</div>""", unsafe_allow_html=True)
        st.info(f"💡 If you push digital to **70%** → estimated earnings: **${ag_monthly_r * 1.2:,.0f}/month**")

        st.markdown("#### Your profit vs daily transfers")
        tx_range = np.arange(1, 41)
        curve_df = pd.DataFrame({
            "Tx per Day":     tx_range,
            "Monthly Profit": tx_range * DAYS * avg_tx_size * agent_take - ag_op_cost
        })
        ag_line = alt.Chart(curve_df).mark_line(
            color="#10B981", strokeWidth=2, point=True
        ).encode(
            x="Tx per Day:Q",
            y=alt.Y("Monthly Profit:Q", title="Profit (USD)"),
            tooltip=["Tx per Day","Monthly Profit"]
        ) + alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(
            color="#EF4444", strokeDash=[5, 3]
        ).encode(y="y:Q")
        st.altair_chart(ag_line, use_container_width=True)

    with c2:
        st.markdown("#### What to do TODAY to earn more")
        st.markdown("""
<div class="insight-box">
<b>Your action list:</b><br><br>
✅ Help 3 users pay digitally — 0/3 done<br>
✅ Refer 2 new users — 1/2 done<br>
→ Focus on <b>grocery store customers</b> — highest conversion<br>
→ Bajaj / taxi drivers near you — push digital payment<br>
→ Remind repeat customers to use digital for speed<br><br>
🏆 <b>Bonus:</b> Hit 70% digital this month = <b>+$50 bonus</b>
</div>""", unsafe_allow_html=True)

        st.markdown("#### Your leaderboard")
        leaders_df = pd.DataFrame({
            "Rank":     [10,       11,          12,           13,           14],
            "Agent":    ["Amir S.","Hassan M.", "YOU",        "Fatuma A.",  "Omar B."],
            "Earnings": [1310,     1260,        int(ag_monthly_r), 1100,   980]
        })
        styled = leaders_df.style.apply(
            lambda r: [
                "background-color: rgba(16,185,129,.15); color: #10B981; font-weight: bold"
                if r["Agent"] == "YOU" else "" for _ in r
            ], axis=1
        ).format({"Earnings": "${:,.0f}"})
        st.dataframe(styled, use_container_width=True, hide_index=True)

        st.markdown("#### Today's stats")
        t1, t2 = st.columns(2)
        t1.metric("Today's earnings", "$45.60",  "↑ 12% vs yesterday")
        t2.metric("Daily target",     "$55.00",  "$9.40 to go", delta_color="inverse")
        t1.metric("Tx completed",     "12",      "of 15 target")
        t2.metric("Digital rate",     "62%",     "Above 55% goal")

        st.markdown("#### Digital rate impact on YOUR earnings")
        d_range = np.arange(0, 101, 5)
        earn_df = pd.DataFrame({
            "Digital %":    d_range,
            "Est. Earnings": [
                ag_tx_month * avg_tx_size * agent_take * (1 + d * 0.003)
                for d in d_range
            ]
        })
        earn_line = alt.Chart(earn_df).mark_line(
            color="#8B5CF6", strokeWidth=2, point=True
        ).encode(
            x="Digital %:Q",
            y=alt.Y("Est. Earnings:Q", title="Monthly Earnings (USD)"),
            tooltip=["Digital %","Est. Earnings"]
        ).properties(height=180)
        st.altair_chart(earn_line, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════
#  MERCHANT VIEW
# ══════════════════════════════════════════════════════════════════════════
elif "Merchant" in view:
    st.subheader("🏪 Merchant Dashboard")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Today's sales",    "$3,200",  "↑ 10% vs yesterday")
    m2.metric("Transactions",     "65",      "↑ 8 more than average")
    m3.metric("Digital payments", "65%",     "Target: 70%", delta_color="inverse")
    m4.metric("Your incentives",  "$12.80",  "↑ 15% this month")

    st.markdown("---")
    mc1, mc2 = st.columns(2)

    with mc1:
        st.markdown("#### Sales this week")
        sales_df = pd.DataFrame({
            "Day":   ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
            "Sales": [2100, 2800, 2400, 3200, 3800, 2900, 2200]
        })
        sales_bar = alt.Chart(sales_df).mark_bar(
            cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color="#F59E0B"
        ).encode(
            x=alt.X("Day:N", sort=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Sales:Q", title="USD"),
            tooltip=["Day","Sales"]
        ).properties(height=200)
        st.altair_chart(sales_bar, use_container_width=True)

        st.markdown("""
<div class="insight-box">
<b>💡 Suggestions to earn more incentives:</b><br>
→ Offer <b>$0.30 discount</b> on digital payments → +12% conversion<br>
→ 35% of your customers still use cash — they are your growth pool<br>
→ Display QR code prominently at counter<br>
→ Remind customers: digital is faster, no change needed
</div>""", unsafe_allow_html=True)

    with mc2:
        st.markdown("#### Incentive calculator — move the sliders")
        m_dig = st.slider("Your digital payment %", 0, 100, 65, 1, key="m_dig")
        m_vol = st.number_input("Your daily sales volume (USD)",
                                500, 10_000, 3_200, 100, key="m_vol")

        m_dsales = m_vol * m_dig / 100
        m_inc    = m_dsales * 0.004
        m_minc   = m_inc * 26

        mi1, mi2 = st.columns(2)
        mi1.metric("Digital sales",     f"${m_dsales:,.0f}")
        mi2.metric("Daily incentive",   f"${m_inc:,.2f}")
        mi1.metric("Monthly incentive", f"${m_minc:,.0f}")
        mi2.metric("vs cash only",      f"+${m_minc:,.0f}")

        st.markdown(f"""
<div class="insight-box">
<b>Projected monthly incentive: ${m_minc:,.0f}</b><br>
At 80% digital → <b>${m_vol * 0.8 * 0.004 * 26:,.0f}/month</b><br>
Reach 80% digital to unlock <b>Platinum tier</b> benefits.
</div>""", unsafe_allow_html=True)

        st.markdown("#### Incentive vs digital rate")
        dig_r2 = np.arange(0, 101, 5)
        inc_df = pd.DataFrame({
            "Digital %":        dig_r2,
            "Monthly Incentive": [m_vol * d / 100 * 0.004 * 26 for d in dig_r2]
        })
        inc_line = alt.Chart(inc_df).mark_line(
            color="#8B5CF6", strokeWidth=2, point=True
        ).encode(
            x="Digital %:Q",
            y=alt.Y("Monthly Incentive:Q", title="Monthly Incentive (USD)"),
            tooltip=["Digital %","Monthly Incentive"]
        ).properties(height=200)
        st.altair_chart(inc_line, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════
#  COMPANY VIEW
# ══════════════════════════════════════════════════════════════════════════
elif "Company" in view:
    st.subheader("🏢 Company / Operator Dashboard")

    co1, co2, co3, co4 = st.columns(4)
    co1.metric("Total agents",   f"{agent_count:,}",
               f"{int(agent_count * 0.72):,} active today (72%)")
    co2.metric("Cash-out volume", f"${cash_vol:,.0f}",  "↑ 11% this month")
    co3.metric("Flagged txns",    "3",
               "Under review", delta_color="inverse")
    co4.metric("Low liquidity",   "5 agents",
               "Action needed", delta_color="inverse")

    st.markdown("---")
    p1, p2 = st.columns([1.3, 1])

    with p1:
        st.markdown("#### Agent network performance")
        net_df = pd.DataFrame({
            "Agent":     ["A1","A2","A3","A4","A5"],
            "Volume":    [4200, 3800, 5100, 2900, 4600],
            "Digital %": [52,   45,   60,   38,   55]
        })
        ch_vol = alt.Chart(net_df).mark_bar(
            color="#3B82F6",
            cornerRadiusTopLeft=4, cornerRadiusTopRight=4
        ).encode(
            x=alt.X("Agent:N", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Volume:Q", title="Volume (USD)"),
            tooltip=["Agent","Volume"]
        )
        ch_dig = alt.Chart(net_df).mark_line(
            color="#10B981", strokeWidth=2, point=True
        ).encode(
            x="Agent:N",
            y=alt.Y("Digital %:Q",
                    title="Digital %",
                    scale=alt.Scale(domain=[0, 100])),
            tooltip=["Agent","Digital %"]
        )
        st.altair_chart(
            alt.layer(ch_vol, ch_dig).resolve_scale(y="independent").properties(height=220),
            use_container_width=True
        )

        st.markdown("#### Float / liquidity monitor")
        liq_df = pd.DataFrame({
            "Agent":  ["Agent #234","Agent #876","Agent #125","Agent #445","Agent #512"],
            "Float":  [120, 210, 320, 850, 940],
            "Status": ["Critical","Low","Low","Good","Good"]
        })
        def color_status(row):
            c = {"Critical":"color:#EF4444;font-weight:bold",
                 "Low":      "color:#F59E0B",
                 "Good":     "color:#10B981"}
            return [c.get(row["Status"],"") for _ in row]
        st.dataframe(
            liq_df.style.apply(color_status, axis=1).format({"Float":"${:,.0f}"}),
            use_container_width=True, hide_index=True
        )

        st.markdown("#### Digital adoption gap")
        adopt_gap = 60 - digital_pct
        extra = volume * max(0, adopt_gap / 100) * (DIG_RATE - CASH_RATE)
        st.markdown(f"""
<div class="{'insight-box' if adopt_gap <= 0 else 'warn-box'}">
Current digital rate&nbsp;: <b>{digital_pct}%</b><br>
Target for profitability: <b>60%</b><br>
Gap&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: <b>{adopt_gap:+}pp</b><br>
Extra profit if gap closed: <b>${extra:,.0f}/month</b>
</div>""", unsafe_allow_html=True)

    with p2:
        st.markdown("#### Cost breakdown")
        cost_pie = pd.DataFrame({
            "Category": ["WhatsApp","Incentives","Agent Payouts","Fixed"],
            "Amount":   [whatsapp_c, incentive_c, agent_pay_c, fixed_c]
        })
        pie = alt.Chart(cost_pie).mark_arc(innerRadius=55, outerRadius=95).encode(
            theta=alt.Theta("Amount:Q"),
            color=alt.Color("Category:N",
                scale=alt.Scale(domain=["WhatsApp","Incentives","Agent Payouts","Fixed"],
                                range=["#3B82F6","#10B981","#8B5CF6","#F59E0B"])),
            tooltip=["Category","Amount"]
        ).properties(height=220)
        st.altair_chart(pie, use_container_width=True)
        st.info(f"💡 Cut WhatsApp msgs by 20% → save **${int(whatsapp_c*0.2):,}/month**")

        st.markdown("#### Risk & compliance")
        st.markdown("""
<div class="alert-box">
🚨 <b>3 flagged transactions</b> — large cash-out spike detected<br>
⚠️ <b>2 compliance alerts</b> — KYC documents expiring soon
</div>
<div class="insight-box" style="margin-top:8px">
✅ System healthy — no major outages this month
</div>""", unsafe_allow_html=True)

        st.markdown("#### Trade-off engine")
        st.caption("Agent commission % vs company profit — find the win-win zone")
        comm_vals = np.arange(comm_min, comm_max + 0.01, 0.1)
        to_rows = []
        for c in comm_vals:
            cr   = c / 100
            ag_r = tx_per_day * DAYS * avg_tx_size * cr
            ag_p = ag_r - ag_op_cost
            net_cm = max(0, CASH_RATE - cr)
            co_r   = dig_rev + cash_vol * net_cm
            co_p   = co_r - total_cost
            to_rows.append({
                "Commission %":   round(c, 2),
                "Agent Profit":   round(ag_p),
                "Company Profit": round(co_p)
            })
        to_df = pd.DataFrame(to_rows)
        to_melt = to_df.melt(
            "Commission %", ["Agent Profit","Company Profit"],
            var_name="Party", value_name="Profit"
        )
        trade_line = alt.Chart(to_melt).mark_line(point=True, strokeWidth=2).encode(
            x=alt.X("Commission %:Q"),
            y=alt.Y("Profit:Q", title="Profit (USD)"),
            color=alt.Color("Party:N",
                scale=alt.Scale(domain=["Agent Profit","Company Profit"],
                                range=["#10B981","#3B82F6"])),
            tooltip=["Commission %","Party","Profit"]
        ) + alt.Chart(pd.DataFrame({"y":[0]})).mark_rule(
            color="#EF4444", strokeDash=[5,3]
        ).encode(y="y:Q")
        st.altair_chart(trade_line, use_container_width=True)

        win = to_df[(to_df["Agent Profit"] > 0) & (to_df["Company Profit"] > 0)]
        if not win.empty:
            st.success(
                f"✅ Win-win: **{win['Commission %'].min():.1f}% – "
                f"{win['Commission %'].max():.1f}%** commission — "
                "both sides profitable"
            )
        else:
            st.warning("⚠️ No win-win zone found. Adjust margins.")

# ── FOOTER ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "SomNexus Decision Engine — operator-grade insight · investor-grade clarity · "
    "behavior-change by design"
)
