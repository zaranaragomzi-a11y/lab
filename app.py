# app_indicator_color.py
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="지시약 색 변화 중화 적정 시뮬레이터", layout="centered")

st.title("🎨 지시약 색 변화가 포함된 중화 적정 시뮬레이터")

# -------------------------
# 1. 데이터 설정
# -------------------------
acids = {
    "강산 (HCl)": {"type": "acid", "Ka": None, "n": 1},
    "약산 (CH3COOH)": {"type": "acid", "Ka": 1.8e-5, "n": 1},
    "이염기산 (H2SO4)": {"type": "acid", "Ka1": 1e3, "Ka2": 1.2e-2, "n": 2},
}

bases = {
    "강염기 (NaOH)": {"type": "base", "Kb": None, "n": 1},
    "약염기 (NH3)": {"type": "base", "Kb": 1.8e-5, "n": 1},
    "이염기염기 (Ca(OH)2)": {"type": "base", "Kb": None, "n": 2},
}

# 지시약 색상 데이터 (산성 / 중성 / 염기성)
indicators = {
    "메틸 오렌지": {"range": (3.1, 4.4), "acid": "#FF4500", "mid": "#FFA500", "base": "#FFFF00"},
    "메틸 레드": {"range": (4.4, 6.2), "acid": "#FF0000", "mid": "#FF8C00", "base": "#FFFF00"},
    "브로모티몰 블루": {"range": (6.0, 7.6), "acid": "#FFFF00", "mid": "#00FF00", "base": "#0000FF"},
    "페놀프탈레인": {"range": (8.2, 10.0), "acid": "#FFFFFF", "mid": "#FFC0CB", "base": "#FF00FF"}
}

# -------------------------
# 2. 사용자 입력
# -------------------------
st.sidebar.header("⚙️ 조건 설정")

acid_name = st.sidebar.selectbox("분석할 산 선택", list(acids.keys()))
base_name = st.sidebar.selectbox("적정할 염기 선택", list(bases.keys()))

C_acid = st.sidebar.number_input("산의 농도 (M)", 0.01, 2.0, 0.1, 0.01)
V_acid = st.sidebar.number_input("산의 부피 (mL)", 1.0, 200.0, 25.0, 1.0)
C_base = st.sidebar.number_input("염기의 농도 (M)", 0.01, 2.0, 0.1, 0.01)

indicator = st.sidebar.selectbox("지시약 선택", list(indicators.keys()))

# -------------------------
# 3. pH 계산 함수
# -------------------------
def calc_pH(Vb):
    n_acid = C_acid * V_acid / 1000
    n_base = C_base * Vb / 1000
    nH = acids[acid_name]["n"]
    nOH = bases[base_name]["n"]

    eqV = (n_acid * nH) / (C_base * nOH) * 1000  # 중화점 부피 (mL)

    # 강산-강염기 단순모델
    if acids[acid_name]["Ka"] is None and bases[base_name]["Kb"] is None:
        if n_base * nOH < n_acid * nH:  # 산 과량
            H = (n_acid*nH - n_base*nOH) / ((V_acid + Vb)/1000)
            pH = -np.log10(H)
        elif n_base * nOH > n_acid * nH:  # 염기 과량
            OH = (n_base*nOH - n_acid*nH) / ((V_acid + Vb)/1000)
            pH = 14 + np.log10(OH)
        else:
            pH = 7.0
    else:
        # 단순 약산-강염기 (예: 아세트산)
        Ka = acids[acid_name].get("Ka", 1e-7)
        if n_base * nOH < n_acid * nH:
            HA = n_acid * nH - n_base * nOH
            A = n_base * nOH
            pH = 0.5 * (14 + np.log10(Ka) + np.log10(A/HA))
        elif n_base * nOH > n_acid * nH:
            OH = (n_base*nOH - n_acid*nH) / ((V_acid + Vb)/1000)
            pH = 14 + np.log10(OH)
        else:
            pH = 14 - 0.5*(14 + np.log10(Ka))
    return pH, eqV

# -------------------------
# 4. 전체 곡선 계산
# -------------------------
Vb_values = np.arange(0, 2*V_acid, 1)
pH_values = []
for Vb in Vb_values:
    pH, eqV = calc_pH(Vb)
    pH_values.append(pH)

# -------------------------
# 5. 사용자 조작용 슬라이더
# -------------------------
current_Vb = st.slider("적정 용액 부피 (mL)", 0.0, float(Vb_values[-1]), float(eqV/2), 1.0)
current_pH, _ = calc_pH(current_Vb)

# -------------------------
# 6. 지시약 색상 계산
# -------------------------
ind_data = indicators[indicator]
low, high = ind_data["range"]

if current_pH <= low:
    color = ind_data["acid"]
elif current_pH >= high:
    color = ind_data["base"]
else:
    color = ind_data["mid"]

# 색상 표시 박스
st.markdown(
    f"""
    <div style='width:200px;height:100px;border-radius:15px;
    background-color:{color};
    border:2px solid black;display:flex;align-items:center;
    justify-content:center;font-size:20px;font-weight:bold'>
    현재 pH = {current_pH:.2f}
    </div>
    """,
    unsafe_allow_html=True
)

# -------------------------
# 7. 그래프 표시
# -------------------------
fig, ax = plt.subplots()
ax.plot(Vb_values, pH_values, color='blue')
ax.axvline(eqV, color='gray', linestyle='--')
ax.scatter(current_Vb, current_pH, color=color, s=100, edgecolor='black')
ax.set_xlabel("적정 용액 부피 (mL)")
ax.set_ylabel("pH")
ax.set_title("중화 적정 곡선")

st.pyplot(fig)

# -------------------------
# 8. 결과 판정
# -------------------------
pH_eq = pH_values[np.argmin(np.abs(Vb_values - eqV))]
ind_low, ind_high = ind_data["range"]

if ind_low <= pH_eq <= ind_high:
    suitability = "✅ 적합한 지시약입니다."
else:
    suitability = f"⚠️ 중화점의 pH는 {pH_eq:.2f}이므로 {indicator}는 적합하지 않습니다."

st.subheader("🧾 결과 요약")
st.write(f"- **중화점 부피:** {eqV:.2f} mL")
st.write(f"- **중화점 pH:** {pH_eq:.2f}")
st.write(f"- **현재 적정 pH:** {current_pH:.2f}")
st.write(f"- **지시약 색상:** {color}")
st.write(f"- **지시약 판정:** {suitability}")

