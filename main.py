import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# ==================== CONFIGURACIÓN ====================
st.set_page_config(page_title="Monitor de Gírgolas - 4kg/semana", layout="wide")
st.title("🍄 Monitor de Producción de Gírgolas")
st.markdown("### Plan actualizado: 4 kg por semana | 40 bolsas | 1.1 kg paja húmeda | 70 g micelio")
st.markdown("---")

# ==================== PARÁMETROS FIJOS (actualizados) ====================
# Producción semanal
BOLSAS_SEMANA = 40                     # Aumentamos a 40 bolsas para llegar a 4 kg
PAJA_HUMEDA_X_BOLSA = 1.1              # kg
SUSTRATO_HUMEDO_SEMANA = BOLSAS_SEMANA * PAJA_HUMEDA_X_BOLSA  # 44 kg
PAJA_SECA_EQUIVALENTE = SUSTRATO_HUMEDO_SEMANA / 3.5          # ~12.57 kg
MICELIO_X_BOLSA = 70                   # gramos
MICELIO_SEMANA_GRAMOS = BOLSAS_SEMANA * MICELIO_X_BOLSA        # 2800 g = 2.8 kg

# Costos reales
COSTO_PAJA_SECA_52KG = 32000
COSTO_MICELIO_2BOTELLONES = 50000  # 2 botellones = 6 kg
COSTO_BOLSA_UNITARIO = 300

# Cálculo de costos semanales
costo_paja_semana = (PAJA_SECA_EQUIVALENTE / 52) * COSTO_PAJA_SECA_52KG
costo_micelio_semana = (MICELIO_SEMANA_GRAMOS / 1000) / 6 * COSTO_MICELIO_2BOTELLONES  # 2.8 kg de micelio
costo_bolsas_semana = BOLSAS_SEMANA * COSTO_BOLSA_UNITARIO
otros_costos_semana = 5000
COSTO_TOTAL_SEMANA = costo_paja_semana + costo_micelio_semana + costo_bolsas_semana + otros_costos_semana

PRECIO_VENTA_KG = 18000
PRODUCCION_ESPERADA_KG = 4.0   # kg de hongos por semana
INGRESO_SEMANA = PRODUCCION_ESPERADA_KG * PRECIO_VENTA_KG
GANANCIA_SEMANA = INGRESO_SEMANA - COSTO_TOTAL_SEMANA
PUNTO_EQUILIBRIO_KG = COSTO_TOTAL_SEMANA / PRECIO_VENTA_KG

# ==================== SIDEBAR ====================
st.sidebar.header("📊 Resumen semanal (plan 4kg)")
st.sidebar.metric("🥬 Paja húmeda total", f"{SUSTRATO_HUMEDO_SEMANA} kg")
st.sidebar.metric("🪣 Bolsas", f"{BOLSAS_SEMANA} bolsas")
st.sidebar.metric("🧫 Micelio total", f"{MICELIO_SEMANA_GRAMOS/1000:.2f} kg")
st.sidebar.markdown("---")
st.sidebar.metric("💰 Costo total", f"${COSTO_TOTAL_SEMANA:,.0f}")
st.sidebar.metric("🎯 Ingreso esperado", f"${INGRESO_SEMANA:,.0f}")
st.sidebar.metric("💵 Ganancia semanal", f"${GANANCIA_SEMANA:,.0f}")
st.sidebar.metric("⚖️ Punto equilibrio", f"{PUNTO_EQUILIBRIO_KG:.2f} kg")
st.sidebar.progress(min(PRODUCCION_ESPERADA_KG / PUNTO_EQUILIBRIO_KG, 1.0))

# ==================== BASE DE DATOS ====================
if not os.path.exists("data"):
    os.makedirs("data")

CSV_PATH = "data/tandas.csv"

def cargar_datos():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        if not df.empty and "fecha_siembra" in df.columns:
            df["fecha_siembra"] = pd.to_datetime(df["fecha_siembra"])
        return df
    else:
        return pd.DataFrame(columns=[
            "tanda", "fecha_siembra", "bolsas", "kg_sustrato_humedo",
            "micelio_g_por_bolsa", "kg_cosecha1", "kg_cosecha2", "kg_cosecha3", "notas"
        ])

def guardar_datos(df):
    df.to_csv(CSV_PATH, index=False)

df = cargar_datos()

# ==================== FUNCIONES AUXILIARES ====================
def calcular_rendimiento(row):
    kg_total = row["kg_cosecha1"] + row["kg_cosecha2"] + row["kg_cosecha3"]
    sustrato = row["kg_sustrato_humedo"]
    if sustrato > 0:
        return round((kg_total / sustrato) * 100, 1)
    return 0.0

def calcular_ganancia(row):
    kg_vendidos = row["kg_cosecha1"]
    ingreso = kg_vendidos * PRECIO_VENTA_KG
    costo_fijo = costo_paja_semana + costo_micelio_semana + costo_bolsas_semana + otros_costos_semana
    factor = row["bolsas"] / BOLSAS_SEMANA if row["bolsas"] > 0 else 1
    costo = costo_fijo * factor
    ganancia = ingreso - costo
    return ingreso, costo, ganancia

# ==================== MENÚ ====================
st.sidebar.header("📋 Menú")
opcion = st.sidebar.radio("Ir a:", ["📊 Dashboard", "➕ Registrar Tanda", "🍄 Registrar Cosecha", "💰 Rentabilidad", "📦 Guía Rápida"])

# ==================== DASHBOARD ====================
if opcion == "📊 Dashboard":
    st.header("📊 Dashboard de Producción (4 kg/semana)")
    col1, col2, col3, col4 = st.columns(4)
    if not df.empty and df["kg_cosecha1"].sum() > 0:
        total_kg = df["kg_cosecha1"].sum()
        col1.metric("🍄 Total cosechado", f"{total_kg:.1f} kg")
        col2.metric("📦 Tandas", len(df))
        df["rendimiento"] = df.apply(calcular_rendimiento, axis=1)
        rend_prom = df["rendimiento"].mean()
        col3.metric("📊 Rendimiento promedio", f"{rend_prom:.1f}%")
        ganancia_total = sum(calcular_ganancia(row)[2] for _, row in df.iterrows() if row["kg_cosecha1"] > 0)
        col4.metric("💰 Ganancia total", f"${ganancia_total:,.0f}")
    else:
        col1.metric("🍄 Total cosechado", "0 kg")
        col2.metric("📦 Tandas", "0")
        col3.metric("📊 Rendimiento", "0%")
        col4.metric("💰 Ganancia total", "$0")
    
    st.markdown("---")
    if not df.empty and df["kg_cosecha1"].sum() > 0:
        st.subheader("📈 Evolución del rendimiento")
        fig = px.line(df, x="tanda", y="rendimiento", markers=True, title="Rendimiento por tanda (%)")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("💰 Ingresos vs Costos por tanda")
        datos_ganancia = []
        for _, row in df.iterrows():
            if row["kg_cosecha1"] > 0:
                ing, cost, gan = calcular_ganancia(row)
                datos_ganancia.append({"tanda": row["tanda"], "ingreso": ing, "costo": cost, "ganancia": gan})
        if datos_ganancia:
            df_gan = pd.DataFrame(datos_ganancia)
            fig2 = px.bar(df_gan, x="tanda", y=["ingreso", "costo"], title="Ingresos y Costos", barmode="group")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Registra tus primeras cosechas para ver los gráficos.")

# ==================== REGISTRAR TANDA ====================
elif opcion == "➕ Registrar Tanda":
    st.header("➕ Nueva Tanda")
    st.info(f"Parámetros recomendados: {BOLSAS_SEMANA} bolsas | {PAJA_HUMEDA_X_BOLSA} kg paja húmeda/bolsa | {MICELIO_X_BOLSA} g micelio/bolsa")
    with st.form("form_tanda"):
        col1, col2 = st.columns(2)
        with col1:
            tanda = st.text_input("Identificador (A, B, C...)", max_chars=5)
            fecha = st.date_input("Fecha de siembra", datetime.now())
            bolsas = st.number_input("Número de bolsas", min_value=1, value=BOLSAS_SEMANA, step=1)
        with col2:
            paja_humeda_bolsa = st.number_input("Paja húmeda por bolsa (kg)", value=PAJA_HUMEDA_X_BOLSA, step=0.1)
            micelio_g = st.number_input("Micelio por bolsa (gramos)", value=MICELIO_X_BOLSA, step=10)
            notas = st.text_area("Notas")
        sustrato_total = bolsas * paja_humeda_bolsa
        st.info(f"📊 Sustrato húmedo total: {sustrato_total:.1f} kg | Micelio total: {bolsas * micelio_g / 1000:.2f} kg")
        if st.form_submit_button("Guardar"):
            if tanda:
                nueva = pd.DataFrame([{
                    "tanda": tanda.upper(),
                    "fecha_siembra": fecha,
                    "bolsas": bolsas,
                    "kg_sustrato_humedo": sustrato_total,
                    "micelio_g_por_bolsa": micelio_g,
                    "kg_cosecha1": 0.0,
                    "kg_cosecha2": 0.0,
                    "kg_cosecha3": 0.0,
                    "notas": notas
                }])
                df = pd.concat([df, nueva], ignore_index=True)
                guardar_datos(df)
                st.success(f"✅ Tanda {tanda.upper()} registrada")
                st.balloons()
            else:
                st.error("Ingresa un identificador")

# ==================== REGISTRAR COSECHA ====================
elif opcion == "🍄 Registrar Cosecha":
    st.header("🍄 Registrar Cosecha")
    if df.empty:
        st.warning("No hay tandas registradas.")
    else:
        pendientes = [t for t in df["tanda"] if df[df["tanda"] == t]["kg_cosecha1"].iloc[0] == 0]
        if not pendientes:
            st.info("Todas las tandas ya tienen cosecha registrada.")
        else:
            sel = st.selectbox("Seleccionar tanda", pendientes)
            idx = df[df["tanda"] == sel].index[0]
            st.info(f"Bolsas: {df.loc[idx, 'bolsas']} | Sustrato: {df.loc[idx, 'kg_sustrato_humedo']:.1f} kg")
            col1, col2, col3 = st.columns(3)
            with col1:
                kg1 = st.number_input("Primer flush (kg)", 0.0, step=0.5)
            with col2:
                kg2 = st.number_input("Segundo flush (kg)", 0.0, step=0.5)
            with col3:
                kg3 = st.number_input("Tercer flush (kg)", 0.0, step=0.5)
            if st.button("Guardar cosecha"):
                df.loc[idx, "kg_cosecha1"] = kg1
                df.loc[idx, "kg_cosecha2"] = kg2
                df.loc[idx, "kg_cosecha3"] = kg3
                guardar_datos(df)
                total = kg1 + kg2 + kg3
                rend = (total / df.loc[idx, "kg_sustrato_humedo"]) * 100
                st.success(f"Cosecha guardada: {total:.1f} kg | Rendimiento: {rend:.1f}%")
                if kg1 < PUNTO_EQUILIBRIO_KG:
                    st.warning(f"⚠️ No alcanzaste el punto de equilibrio ({PUNTO_EQUILIBRIO_KG:.1f} kg)")
                else:
                    st.balloons()

# ==================== RENTABILIDAD ====================
elif opcion == "💰 Rentabilidad":
    st.header("💰 Análisis de Rentabilidad (Plan 4kg/semana)")
    st.markdown(f"""
    | Concepto | Valor |
    |----------|-------|
    | **Bolsas por semana** | {BOLSAS_SEMANA} |
    | **Paja húmeda por bolsa** | {PAJA_HUMEDA_X_BOLSA} kg |
    | **Micelio por bolsa** | {MICELIO_X_BOLSA} g |
    | **Producción esperada** | {PRODUCCION_ESPERADA_KG} kg/semana |
    | **Ingreso semanal** | ${INGRESO_SEMANA:,.0f} |
    | **Costo semanal** | ${COSTO_TOTAL_SEMANA:,.0f} |
    | **Ganancia semanal** | **${GANANCIA_SEMANA:,.0f}** |
    | **Ganancia mensual** | **${GANANCIA_SEMANA*4:,.0f}** |
    | **Ganancia anual (48 semanas)** | **${GANANCIA_SEMANA*48:,.0f}** |
    | **Punto de equilibrio** | {PUNTO_EQUILIBRIO_KG:.2f} kg/semana |
    """)

# ==================== GUÍA RÁPIDA ====================
elif opcion == "📦 Guía Rápida":
    st.header("📦 Guía Rápida de Producción (con 1.1 kg y 70g)")
    st.markdown(f"""
    **Por bolsa:**
    - Paja seca: ~0.314 kg → hidratar hasta **{PAJA_HUMEDA_X_BOLSA} kg de paja húmeda**
    - Micelio: **{MICELIO_X_BOLSA} gramos**
    - Hongos esperados: ~110 g por bolsa (10% de 1.1kg)

    **Por semana (para 4 kg):**
    - Bolsas: **{BOLSAS_SEMANA}**
    - Paja húmeda total: **{SUSTRATO_HUMEDO_SEMANA} kg**
    - Micelio total: **{MICELIO_SEMANA_GRAMOS/1000:.2f} kg**
    - Costo total: **${COSTO_TOTAL_SEMANA:,.0f}**
    - Ingreso: **${INGRESO_SEMANA:,.0f}**
    - Ganancia: **${GANANCIA_SEMANA:,.0f}**

    **Recomendaciones:**
    - Con 1.1 kg húmedos, necesitas **40 bolsas por semana** para llegar a 4 kg.
    - Si quieres mantener 20 bolsas, subí el peso a 2 kg húmedos por bolsa.
    - Tasa de siembra actual: 6.36% (sigue siendo alta, pero mucho mejor que 200g/bolsa).
    """)

st.markdown("---")
st.caption(f"🍄 Plan actualizado | {BOLSAS_SEMANA} bolsas de {PAJA_HUMEDA_X_BOLSA} kg | {MICELIO_X_BOLSA} g micelio/bolsa")
