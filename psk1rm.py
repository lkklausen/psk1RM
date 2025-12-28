import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(page_title="1RM beregning og estimat", page_icon="🏋️")

# --- 1RM FORMULAS ---
def calculate_epley(weight, reps):
    if reps == 1: return weight
    return weight * (1 + reps / 30)

def calculate_brzycki(weight, reps):
    if reps == 1: return weight
    if reps >= 37: return weight 
    return weight * (36 / (37 - reps))

def calculate_lombardi(weight, reps):
    if reps == 1: return weight
    return weight * (reps ** 0.10)

def calculate_oconner(weight, reps):
    if reps == 1: return weight
    return weight * (1 + 0.025 * reps)

def get_1rm(weight, reps, method):
    if method == "Epley":
        return calculate_epley(weight, reps)
    elif method == "Brzycki":
        return calculate_brzycki(weight, reps)
    elif method == "Lombardi":
        return calculate_lombardi(weight, reps)
    elif method == "O'Conner":
        return calculate_oconner(weight, reps)
    elif method == "Gennemsnit":
        v1 = calculate_epley(weight, reps)
        v2 = calculate_brzycki(weight, reps)
        v3 = calculate_lombardi(weight, reps)
        v4 = calculate_oconner(weight, reps)
        return (v1 + v2 + v3 + v4) / 4
    return 0

# --- APP LOGIC ---
st.title("🏋️ 1RM beregning og estimat")

# --- SIDEBAR INPUTS ---
st.sidebar.header("1. Nuværende løft")
weight = st.sidebar.number_input("Vægt løftet(kg)", min_value=1.0, value=100.0, step=2.5)
reps = st.sidebar.number_input("Gentagelser udført", min_value=1, max_value=30, value=5)

formula_choice = st.sidebar.selectbox(
    "1RM formel",
    ("Gennemsnit", "Epley", "Brzycki", "Lombardi", "O'Conner")
)

st.sidebar.header("2. Atletprofil")
experience = st.sidebar.selectbox(
    "Kompetenceniveau",
    ("Begynder (< 6 mdr)", "Let øvet (6 mdr - 2 år)", "Avanceret (2 år - 5 år)", "Elite (5 år +)")
)

nutrition = st.sidebar.selectbox(
    "Koststatus",
    ("Kalorieoverskud (Bulking)", "Vedligeholdelse", "Kalorieunderskud (Cutting)")
)

st.sidebar.header("3. Varighed")
weeks = st.sidebar.slider("Træningsvarighed (Uger)", min_value=1, max_value=24, value=8)

# --- CALCULATIONS ---

# 1. Calculate Current 1RM
current_1rm = get_1rm(weight, reps, formula_choice)

# 2. Determine Weekly Growth Rate
growth_rates = {
    "Begynder (< 6 mdr)": 0.0125,
    "Let øvet (6 mdr - 2 år)": 0.006,
    "Avanceret (2 år - 5 år)": 0.0025,
    "Elite (5 år +)": 0.001
}

nutrition_multipliers = {
    "Kalorieoverskud (Bulking)": 1.2,
    "Vedligeholdelse": 0.9,
    "Kalorieunderskud (Cutting)": 0.5
}

base_rate = growth_rates[experience]
modifier = nutrition_multipliers[nutrition]

weekly_rate_avg = base_rate * modifier
weekly_rate_high = base_rate * modifier * 1.5
weekly_rate_low = base_rate * modifier * 0.5

# --- GENERATE PROJECTION DATA ---
projection_data = []

val_avg = current_1rm
val_high = current_1rm
val_low = current_1rm

for w in range(weeks + 1):
    projection_data.append({
        "Uge": w,
        "Metode": formula_choice,  # <--- Added Method Column
        "Estimeret 1RM": val_avg,
        "Optimistisk": val_high,
        "Konservativ": val_low
    })
    
    val_avg = val_avg * (1 + weekly_rate_avg)
    val_high = val_high * (1 + weekly_rate_high)
    val_low = val_low * (1 + weekly_rate_low)

df = pd.DataFrame(projection_data)

# Reorder columns so Method is visible near the start
df = df[['Uge', 'Metode', 'Estimeret 1RM', 'Optimistisk', 'Konservativ']]

# --- DISPLAY RESULTS ---

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label=f"Nuværende 1RM ({formula_choice})", value=f"{current_1rm:.1f} kg")
with col2:
    projected_val = df.iloc[-1]['Estimeret 1RM']
    delta = projected_val - current_1rm
    st.metric(label=f"Estimeret 1RM (Uger {weeks})", value=f"{projected_val:.1f} kg", delta=f"+{delta:.1f} kg")
with col3:
    st.metric(label="Tilvækstfaktor", value=f"{weekly_rate_avg*100:.2f}% / uge")

st.divider()

# --- PLOTTING ---
st.subheader("📈 Estimeret styrkeudvikling")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df['Uge'], y=df['Optimistisk'],
    mode='lines',
    line=dict(width=1),
    showlegend=False,
    name='Optimistisk'
))

fig.add_trace(go.Scatter(
    x=df['Uge'], y=df['Konservativ'],
    mode='lines',
    line=dict(width=1),
    fill='tonexty', 
    fillcolor='rgba(68, 206, 27, 0.1)',
    showlegend=False,
    name='Konservativ'
))

fig.add_trace(go.Scatter(
    x=df['Uge'], y=df['Estimeret 1RM'],
    mode='lines+markers',
    name='Estimeret udvikling',
    line=dict(color='#FF4B4B', width=3)
))

fig.update_layout(
    title=f"1RM udvikling med brug af: {formula_choice}",
    xaxis_title="Uger",
    yaxis_title="Estimeret 1RM (kg)",
    hovermode="x unified",
    template="plotly_dark"
)

st.plotly_chart(fig, width='stretch')

# --- DETAILED DATA TABLE ---
with st.expander("Sammenlign alle formler"):
    st.write("Nuværende 1RM sammenligning:")
    f_epley = calculate_epley(weight, reps)
    f_brzycki = calculate_brzycki(weight, reps)
    f_lombardi = calculate_lombardi(weight, reps)
    f_oconner = calculate_oconner(weight, reps)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Epley", f"{f_epley:.1f} kg")
    c2.metric("Brzycki", f"{f_brzycki:.1f} kg")
    c3.metric("Lombardi", f"{f_lombardi:.1f} kg")
    c4.metric("O'Conner", f"{f_oconner:.1f} kg")

with st.expander("Se de rå tilvækstdata"):
    # Apply formatting only to numeric columns to avoid errors with the text 'Method' column
    st.dataframe(
        df.style.format({
            "Estimeret 1RM": "{:.1f}", 
            "Optimistisk": "{:.1f}", 
            "Konservativ": "{:.1f}"
        }),
        hide_index=True
    )
