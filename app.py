import streamlit as st
import pandas as pd
import pulp
from fpdf import FPDF
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="NutriPig Optima", page_icon="🐷", layout="wide")

st.title("🐷 NutriPig Optima")
st.subheader("Sistema Inteligente de Formulación y Minimización de Costos en Alimentación Porcina")
st.markdown("---")

# --- PARAMETROS DE ENTRADA ---
st.sidebar.header("1. Parámetros del Lote")
etapa = st.sidebar.selectbox("Etapa Productiva:", ["Engorda / Terminación (50-100 kg)", "Crecimiento (25-50 kg)", "Iniciador / Destete (10-25 kg)"])
toneladas = st.sidebar.number_input("Volumen de Batch (Toneladas):", min_value=0.5, max_value=50.0, value=2.0, step=0.5)

st.header("2. Precios Locales de Materias Primas ($ CLP / kg)")
col1, col2, col3 = st.columns(3)
with col1:
    p_maiz = st.number_input("Maíz Amarillo:", value=235.0, step=5.0)
    p_afrecho = st.number_input("Afrecho de Trigo:", value=155.0, step=5.0)
with col2:
    p_soya = st.number_input("Harina de Soya 46%:", value=540.0, step=5.0)
    p_aceite = st.number_input("Aceite de Soya:", value=1100.0, step=10.0)
with col3:
    p_nucleo = st.number_input("Núcleo Engorda 2.5%:", value=1850.0, step=20.0)

precios = {'Maíz Amarillo': p_maiz, 'Afrecho de Trigo': p_afrecho, 'Harina de Soya 46%': p_soya, 'Aceite de Soya': p_aceite, 'Núcleo Engorda 2.5%': p_nucleo}

# --- FUNCIÓN GENERADORA DE PDF ---
def generar_pdf_bytes(etapa, toneladas, receta, precios, costo_ton):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "NUTRIPIG OPTIMA - FICHA TÉCNICA Y ORDEN DE MEZCLADO", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Etapa: {etapa} | Volumen: {toneladas} Toneladas | Costo/Ton: ${costo_ton:,.0f} CLP", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(65, 7, "Ingrediente", border=1)
    pdf.cell(30, 7, "% Inclusión", border=1, align="C")
    pdf.cell(35, 7, "kg / Tonelada", border=1, align="C")
    pdf.cell(30, 7, f"kg Batch ({toneladas}T)", border=1, align="C")
    pdf.cell(30, 7, "Costo ($)", border=1, align="C")
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 9)
    for ing, kg in receta.items():
        pct = (kg / 1000) * 100
        kg_batch = kg * toneladas
        costo_i = kg_batch * precios[ing]
        pdf.cell(65, 6, ing, border=1)
        pdf.cell(30, 6, f"{pct:.1f}%", border=1, align="C")
        pdf.cell(35, 6, f"{kg:,.1f} kg", border=1, align="C")
        pdf.cell(30, 6, f"{kg_batch:,.1f} kg", border=1, align="C")
        pdf.cell(30, 6, f"${costo_i:,.0f}", border=1, align="R")
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1')

# --- EJECUCIÓN Y OPTIMIZACIÓN ---
if st.button("🚀 OPTIMIZAR FÓRMULA DE MÍNIMO COSTO", type="primary", use_container_width=True):
    prob = pulp.LpProblem("NutriPig", pulp.LpMinimize)
    insumos = list(precios.keys())
    x = pulp.LpVariable.dicts("Insumo", insumos, lowBound=0, cat='Continuous')
    
    prob += pulp.lpSum([precios[i] * x[i] for i in insumos])
    prob += pulp.lpSum([x[i] for i in insumos]) == 1000
    
    comp = {
        'Maíz Amarillo':       {'PC': 85,  'EM': 3.3, 'Lisina': 2.4, 'Fibra': 22},
        'Afrecho de Trigo':    {'PC': 150, 'EM': 2.2, 'Lisina': 5.8, 'Fibra': 95},
        'Harina de Soya 46%':  {'PC': 460, 'EM': 3.2, 'Lisina': 28.0,'Fibra': 38},
        'Aceite de Soya':      {'PC': 0,   'EM': 8.8, 'Lisina': 0.0, 'Fibra': 0},
        'Núcleo Engorda 2.5%': {'PC': 0,   'EM': 0.0, 'Lisina': 40.0,'Fibra': 0}
    }
    
    prob += pulp.lpSum([comp[i]['PC'] * x[i] for i in insumos]) >= 140000
    prob += pulp.lpSum([comp[i]['EM'] * x[i] for i in insumos]) >= 3150
    prob += pulp.lpSum([comp[i]['Lisina'] * x[i] for i in insumos]) >= 7500
    prob += pulp.lpSum([comp[i]['Fibra'] * x[i] for i in insumos]) <= 50000
    
    prob += x['Núcleo Engorda 2.5%'] == 25
    prob += x['Afrecho de Trigo'] <= 150
    prob += x['Aceite de Soya'] <= 30
    
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    if pulp.LpStatus[prob.status] == 'Optimal':
        receta = {i: x[i].varValue for i in insumos if x[i].varValue > 0}
        costo_ton = pulp.value(prob.objective)
        costo_ref = 370000.0
        ahorro_ton = costo_ref - costo_ton
        
        st.success("✅ ¡Fórmula Optimizada con Éxito!")
        m1, m2, m3 = st.columns(3)
        m1.metric("Costo / Tonelada", f"${costo_ton:,.0f} CLP")
        m2.metric("Ahorro / Tonelada", f"${ahorro_ton:,.0f} CLP", delta=f"{((ahorro_ton/costo_ref)*100):.1f}%")
        m3.metric(f"Ahorro Total ({toneladas} Ton)", f"${(ahorro_ton * toneladas):,.0f} CLP")
        
        df_receta = pd.DataFrame([
            {"Ingrediente": ing, "Inclusión (%)": f"{(kg/10):.1f}%", "kg / Ton": round(kg, 1), f"kg Batch ({toneladas}T)": round(kg * toneladas, 1), "Costo Batch ($)": round(kg * toneladas * precios[ing], 0)}
            for ing, kg in receta.items()
        ])
        st.dataframe(df_receta, use_container_width=True)
        
        # Botón Descargar PDF
        pdf_bytes = generar_pdf_bytes(etapa, toneladas, receta, precios, costo_ton)
        st.download_button(label="📄 Descargar Orden de Mezclado en PDF", data=pdf_bytes, file_name="Orden_Mezclado_NutriPig.pdf", mime="application/pdf")
