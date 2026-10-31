import streamlit as st
import pandas as pd
import pulp as plp
from fpdf import FPDF
import tempfile
import os

# Configuración inicial de la página
st.set_page_config(
    page_title="Nutripig Óptima | INGEBER",
    page_icon="🐷",
    layout="wide"
)

# Estilos CSS avanzados: Paleta Amarillo, Negro y Blanco (Alto Contraste / Industrial)
st.markdown("""
    <style>
    .main { background-color: #121212; color: #f0f0f0; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #000000; padding: 10px; border-radius: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #222222;
        border-radius: 6px;
        padding: 10px 22px;
        font-weight: 700;
        color: #ffffff;
        border: 1px solid #333333;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffcc00 !important;
        color: #000000 !important;
        border: 1px solid #ffcc00;
    }
    .card-container {
        background-color: #1e1e1e;
        padding: 24px;
        border-radius: 10px;
        border: 1px solid #333333;
        border-left: 5px solid #ffcc00;
        box-shadow: 0 4px 6px rgba(0,0,0,0.4);
        margin-bottom: 20px;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado visual corporativo estilizado con Negro y Amarillo
st.markdown("""
    <div style="background: linear-gradient(135deg, #000000, #1f1f1f); color: white; padding: 30px; border-radius: 10px; border-bottom: 5px solid #ffcc00; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.5);">
        <h1 style="margin:0; font-size: 28px; font-weight: 700; color: #ffcc00 !important;">🐷 NUTRIPIG ÓPTIMA</h1>
        <p style="margin:8px 0 0 0; font-size: 15px; color: #cccccc;">Sistema Avanzado de Optimización Nutricional y Costos Porcinos | Oficina Técnica INGEBER</p>
    </div>
""", unsafe_allow_html=True)

# Navegación por pestañas limpias y estructuradas
tab1, tab2, tab3, tab4 = st.tabs([
    "🌾 Formulación de Raciones", 
    "📊 Base de Datos y Stock", 
    "💰 Calculadora de Costos", 
    "📈 Modelado de Crecimiento"
])

# --- PESTAÑA 1: FORMULACIÓN DE RACIONES ---
with tab1:
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    st.subheader("⚙️ Motor de Optimización Lineal (Algoritmo Simplex)")
    st.write("Configure los parámetros del lote y las restricciones nutricionales para calcular la ración de mínimo costo.")
    
    col1, col2 = st.columns(2)
    with col1:
        etapa = st.selectbox(
            "Seleccione Etapa Productiva:",
            ["Inicio / Pre-inicio", "Crecimiento", "Engorda / Terminación", "Gestación / Lactancia"]
        )
    with col2:
        lote_kg = st.number_input("Cantidad de alimento a preparar (Kg):", min_value=10.0, value=1000.0, step=100.0)

    st.markdown("---")
    st.markdown("#### 🔬 Restricciones Nutricionales Mínimas")
    
    col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5)
    with col_r1:
        min_em = st.number_input("Energía (Mcal/kg)", value=3.0, step=0.1)
    with col_r2:
        min_pc = st.number_input("Proteína Cruda (%)", value=16.0, step=0.5)
    with col_r3:
        min_met = st.number_input("Metionina (%)", value=0.3, step=0.01)
    with col_r4:
        min_lys = st.number_input("Treonina / Lis (%)", value=0.6, step=0.01)
    with col_r5:
        min_cal = st.number_input("Calcio / Fósforo (%)", value=0.7, step=0.05)

    st.markdown("---")
    st.markdown("#### 📦 Matriz de Materias Primas, Costos y Stock en Bodega")
    
    df_default = pd.DataFrame([
        {"Ingrediente": "Maíz Grano", "Costo ($/kg)": 280, "Stock (kg)": 5000, "EM (Mcal)": 3.3, "PC (%)": 8.5, "Met (%)": 0.18, "Lys (%)": 0.26, "Ca (%)": 0.02},
        {"Ingrediente": "Afrecho de Trigo", "Costo ($/kg)": 180, "Stock (kg)": 2000, "EM (Mcal)": 2.1, "PC (%)": 15.0, "Met (%)": 0.22, "Lys (%)": 0.55, "Ca (%)": 0.12},
        {"Ingrediente": "Harina de Soya 46%", "Costo ($/kg)": 550, "Stock (kg)": 3000, "EM (Mcal)": 3.4, "PC (%)": 46.0, "Met (%)": 0.65, "Lys (%)": 2.90, "Ca (%)": 0.30},
        {"Ingrediente": "Carbonato de Calcio", "Costo ($/kg)": 120, "Stock (kg)": 500, "EM (Mcal)": 0.0, "PC (%)": 0.0, "Met (%)": 0.00, "Lys (%)": 0.00, "Ca (%)": 38.0},
        {"Ingrediente": "Núcleo Vit-Min Porcino", "Costo ($/kg)": 1400, "Stock (kg)": 300, "EM (Mcal)": 1.5, "PC (%)": 10.0, "Met (%)": 2.50, "Lys (%)": 5.00, "Ca (%)": 15.0}
    ])
    
    edited_df = st.data_editor(df_default, num_rows="dynamic", use_container_width=True)

    if st.button("🚀 Ejecutar Optimización de Mezcla", type="primary"):
        try:
            prob = plp.LpProblem("Optimizacion_Alimento_Porcino", plp.LpMinimize)
            
            ingredientes = edited_df["Ingrediente"].tolist()
            # Corrección aplicada aquí usando el argumento posicional 0 para el límite inferior
            x = {ing: plp.LpVariable(f"x_{ing}", 0) for ing in ingredientes}
            
            prob += plp.lpSum(x[ing] * edited_df.loc[edited_df["Ingrediente"] == ing, "Costo ($/kg)"].values[0] for ing in ingredientes)
            
            total_kg = plp.lpSum(x[ing] for ing in ingredientes)
            prob += total_kg == lote_kg, "Suma_Total"
            
            for idx, row in edited_df.iterrows():
                ing = row["Ingrediente"]
                stock_max = row["Stock (kg)"]
                prob += x[ing] <= stock_max, f"Stock_Max_{ing}"
            
            prob += plp.lpSum(x[ing] * edited_df.loc[edited_df["Ingrediente"] == ing, "EM (Mcal)"].values[0] for ing in ingredientes) >= min_em * lote_kg, "Min_EM"
            prob += plp.lpSum(x[ing] * edited_df.loc[edited_df["Ingrediente"] == ing, "PC (%)"].values[0] for ing in ingredientes) >= min_pc * lote_kg, "Min_PC"
            
            prob.solve(plp.PULP_CBC_CMD(msg=False))
            
            if plp.LpStatus[prob.status] == 'Optimal':
                st.success("¡Optimización completada con éxito!")
                
                resultados = []
                costo_total = 0
                for ing in ingredientes:
                    cantidad = x[ing].varValue
                    if cantidad > 0.001:
                        c_unit = edited_df.loc[edited_df["Ingrediente"] == ing, "Costo ($/kg)"].values[0]
                        subtotal = cantidad * c_unit
                        costo_total += subtotal
                        porcentaje = (cantidad / lote_kg) * 100
                        resultados.append({
                            "Ingrediente": ing,
                            "Participación (%)": round(porcentaje, 2),
                            "Cantidad (Kg)": round(cantidad, 2),
                            "Costo Subtotal ($)": round(subtotal, 2)
                        })
                
                df_res = pd.DataFrame(resultados)
                st.dataframe(df_res, use_container_width=True)
                
                m1, m2 = st.columns(2)
                with m1:
                    st.metric("Costo Total del Lote ($)", f"${costo_total:,.2f}")
                with m2:
                    st.metric("Costo Promedio por Kilogramo ($/kg)", f"${costo_total/lote_kg:,.2f}")
                
                class PDF(FPDF):
                    def header(self):
                        self.set_fill_color(0, 0, 0)
                        self.rect(0, 0, 210, 25, 'F')
                        self.set_font('Helvetica', 'B', 14)
                        self.set_text_color(255, 204, 0)
                        self.cell(0, 15, ' INGEBER - REPORTE TÉCNICO DE FORMULACIÓN', 0, 1, 'L')
                        self.ln(10)

                    def footer(self):
                        self.set_y(-20)
                        self.set_font('Helvetica', 'I', 8)
                        self.set_text_color(100, 100, 100)
                        self.cell(0, 10, 'Oficina Técnica Consultora INGEBER | Soluciones Integrales para la Agroindustria', 0, 0, 'C')

                pdf = PDF()
                pdf.add_page()
                pdf.set_font('Helvetica', 'B', 12)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 10, f'Plan de Alimentación: {etapa}', 0, 1, 'L')
                
                pdf.set_font('Helvetica', '', 10)
                pdf.cell(0, 6, f'Tamano del Lote Producido: {lote_kg} Kg', 0, 1, 'L')
                pdf.cell(0, 6, f'Costo Total de la Formula: ${costo_total:,.2f}', 0, 1, 'L')
                pdf.cell(0, 6, f'Costo Unitario: ${costo_total/lote_kg:,.2f} por Kg', 0, 1, 'L')
                pdf.ln(5)
                
                pdf.set_font('Helvetica', 'B', 10)
                pdf.cell(0, 8, 'Desglose de Ingredientes y Mezcla:', 0, 1, 'L')
                
                pdf.set_font('Helvetica', 'B', 9)
                pdf.set_fill_color(240, 240, 240)
                pdf.cell(80, 7, 'Ingrediente', 1, 0, 'C', True)
                pdf.cell(35, 7, '% en Formula', 1, 0, 'C', True)
                pdf.cell(35, 7, 'Cantidad (Kg)', 1, 0, 'C', True)
                pdf.cell(40, 7, 'Subtotal ($)', 1, 1, 'C', True)
                
                pdf.set_font('Helvetica', '', 9)
                for r in resultados:
                    pdf.cell(80, 6, str(r['Ingrediente']), 1, 0, 'L')
                    pdf.cell(35, 6, f"{r['Participación (%)']}%", 1, 0, 'C')
                    pdf.cell(35, 6, f"{r['Cantidad (Kg)']}", 1, 0, 'C')
                    pdf.cell(40, 6, f"${r['Costo Subtotal ($)']}", 1, 1, 'R')
                
                pdf.ln(10)
                pdf.set_font('Helvetica', 'B', 10)
                pdf.cell(0, 8, 'Instrucciones de Mezclado en Terreno:', 0, 1, 'L')
                pdf.set_font('Helvetica', '', 9)
                pdf.multi_cell(0, 5, "1. Pesar previamente los ingredientes según el desglose de cantidades calculado.\n2. Incorporar los componentes de mayor volumen (cereales y subproductos) en la mezcladora.\n3. Agregar los núcleos y aditivos minerales asegurando una homogenización correcta.\n4. Almacenar en sacos limpios e identificados para evitar humedad en bodega.")
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    pdf.output(tmp_file.name)
                    tmp_path = tmp_file.name

                with open(tmp_path, "rb") as f:
                    st.download_button(
                        label="📄 Descargar Informe Técnico en PDF",
                        data=f,
                        file_name="Informe_Nutricional_Ingeber.pdf",
                        mime="application/pdf"
                    )
            else:
                st.error("No se encontró una solución factible con las restricciones y el stock ingresado. Intente relajar algún límite nutricional o aumentar el stock.")
        except Exception as e:
            st.error(f"Error en la ejecución del optimizador: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- PESTAÑA 2: BASE DE DATOS Y STOCK ---
with tab2:
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    st.subheader("📊 Gestión de Inventario y Materias Primas")
    st.info("Administre los precios vigentes en el mercado local y el stock físico disponible en su bodega para optimizar las compras y evitar quiebres de inventario.")
    st.dataframe(df_default, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- PESTAÑA 3: CALCULADORA DE COSTOS ---
with tab3:
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    st.subheader("💰 Análisis Financiero de Producción Porcina")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        num_animales = st.number_input("Número de animales en lote:", value=50, step=10)
        consumo_diario = st.number_input("Consumo diario estimado por animal (kg):", value=2.5, step=0.1)
    with col_c2:
        dias_etapa = st.number_input("Duración de la etapa (días):", value=60, step=5)
        costo_kg_alimento = st.number_input("Costo estimado por kg de alimento ($):", value=350.0, step=10.0)
    
    consumo_total_lote = num_animales * consumo_diario * dias_etapa
    costo_total_proyeccion = consumo_total_lote * costo_kg_alimento
    
    st.markdown("---")
    mc1, mc2 = st.columns(2)
    with mc1:
        st.metric("Consumo Total Requerido (Kg)", f"{consumo_total_lote:,.2f} Kg")
    with mc2:
        st.metric("Proyección Financiera ($)", f"${costo_total_proyeccion:,.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- PESTAÑA 4: MODELADO DE CRECIMIENTO ---
with tab4:
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    st.subheader("📈 Parámetros de Crecimiento y Conversión Alimenticia")
    st.write("Control técnico de conversión y ganancia diaria de peso (GDP) adaptado para sistemas convencionales y de cama profunda.")
    
    peso_inicial = st.number_input("Peso Inicial Promedio (kg):", value=30.0)
    peso_final = st.number_input("Peso Final Objetivo (kg):", value=100.0)
    gdp = st.number_input("Ganancia Diaria de Peso Esperada (kg/día):", value=0.8, step=0.05)
    
    if gdp > 0:
        dias_necesarios = (peso_final - peso_inicial) / gdp
        st.success(f"Tiempo estimado para alcanzar la meta: **{dias_necesarios:.1f} días**")
    st.markdown('</div>', unsafe_allow_html=True)
