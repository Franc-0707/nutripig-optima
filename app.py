import streamlit as-st
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

# Estilos CSS personalizados (Paleta corporativa verde industrial)
st.markdown("""
    <style>
    .main { background-color: #f7f9f8; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #e0f2ec;
        border-radius: 4px;
        padding: 10px 20px;
        font-weight: 600;
        color: #1b4d3e;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1b4d3e !important;
        color: #ffffff !important;
    }
    .card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #d0ded6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado visual corporativo
st.markdown("""
    <div style="background: linear-gradient(135deg, #1b4d3e, #2e6f5c); color: white; padding: 25px; border-radius: 8px; border-bottom: 4px solid #d4af37; margin-bottom: 20px;">
        <h1 style="margin:0; font-size: 26px;">🐷 NUTRIPIG ÓPTIMA</h1>
        <p style="margin:5px 0 0 0; font-size: 14px; color: #e0f2ec;">Sistema de Optimización Nutricional y Costos porcinos | Desarrollado por INGEBER</p>
    </div>
""", unsafe_allow_html=True)

# Pestañas de navegación de la aplicación
tab1, tab2, tab3, tab4 = st.tabs([
    "🌾 Formulación de Raciones", 
    "📊 Base de Datos y Stock", 
    "💰 Calculadora de Costos", 
    "📈 Modelado de Crecimiento"
])

# --- PESTAÑA 1: FORMULACIÓN DE RACIONES ---
with tab1:
    st.markdown("### Motor de Optimización Lineal (Algoritmo Simplex)")
    
    col1, col2 = st.columns(2)
    with col1:
        etapa = st.selectbox(
            "Seleccione Etapa Productiva:",
            ["Inicio / Pre-inicio", "Crecimiento", "Engorda / Terminación", "Gestación / Lactancia"]
        )
    with col2:
        lote_kg = st.number_input("Cantidad de alimento a preparar (Kg):", min_value=10.0, value=1000.0, step=100.0)

    st.markdown("---")
    st.subheader("Restricciones Nutricionales Avanzadas (Mínimos requeridos)")
    
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
    st.subheader("Matriz de Ingredientes, Costos y Stock en Bodega")
    
    # Base de datos editable de ingredientes
    df_default = pd.DataFrame([
        {"Ingrediente": "Maíz Grano", "Costo ($/kg)": 280, "Stock (kg)": 5000, "EM (Mcal)": 3.3, "PC (%)": 8.5, "Met (%)": 0.18, "Lys (%)": 0.26, "Ca (%)": 0.02},
        {"Ingrediente": "Afrecho de Trigo", "Costo ($/kg)": 180, "Stock (kg)": 2000, "EM (Mcal)": 2.1, "PC (%)": 15.0, "Met (%)": 0.22, "Lys (%)": 0.55, "Ca (%)": 0.12},
        {"Ingrediente": "Harina de Soya 46%", "Costo ($/kg)": 550, "Stock (kg)": 3000, "EM (Mcal)": 3.4, "PC (%)": 46.0, "Met (%)": 0.65, "Lys (%)": 2.90, "Ca (%)": 0.30},
        {"Ingrediente": "Carbonato de Calcio", "Costo ($/kg)": 120, "Stock (kg)": 500, "EM (Mcal)": 0.0, "PC (%)": 0.0, "Met (%)": 0.00, "Lys (%)": 0.00, "Ca (%)": 38.0},
        {"Ingrediente": "Núcleo Vit-Min Porcino", "Costo ($/kg)": 1400, "Stock (kg)": 300, "EM (Mcal)": 1.5, "PC (%)": 10.0, "Met (%)": 2.50, "Lys (%)": 5.00, "Ca (%)": 15.0}
    ])
    
    edited_df = st.data_editor(df_default, num_rows="dynamic", use_container_width=True)

    if st.button("Ejecutar Optimización de Mezcla", type="primary"):
        try:
            prob = plp.LpProblem("Optimizacion_Alimento_Porcino", plp.LpMinimize)
            
            # Variables de decisión (Kg de cada ingrediente)
            ingredientes = edited_df["Ingrediente"].tolist()
            x = {ing: plp.LpVariable(f"x_{ing}", lowBound=0) for ing in ingredientes}
            
            # Función Objetivo: Minimizar costo total
            prob += plp.lpSum(x[ing] * edited_df.loc[edited_df["Ingrediente"] == ing, "Costo ($/kg)"].values[0] for ing in ingredientes)
            
            # Restricción: El total debe sumar la cantidad solicitada (o 100% si se maneja proporcional, ajustado a lote)
            total_kg = plp.lpSum(x[ing] for ing in ingredientes)
            prob += total_kg == lote_kg, "Suma_Total"
            
            # Restricción de Stock disponible en bodega
            for idx, row in edited_df.iterrows():
                ing = row["Ingrediente"]
                stock_max = row["Stock (kg)"]
                prob += x[ing] <= stock_max, f"Stock_Max_{ing}"
            
            # Restricciones nutricionales proporcionales al total
            prob += plp.lpSum(x[ing] * edited_df.loc[edited_df["Ingrediente"] == ing, "EM (Mcal)"].values[0] for ing in ingredientes) >= min_em * lote_kg, "Min_EM"
            prob += plp.lpSum(x[ing] * edited_df.loc[edited_df["Ingrediente"] == ing, "PC (%)"].values[0] for ing in ingredientes) >= min_pc * lote_kg, "Min_PC"
            
            # Resolver modelo con PuLP
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
                
                st.metric("Costo Total del Lote ($)", f"${costo_total:,.2f}")
                st.metric("Costo Promedio por Kilogramo ($/kg)", f"${costo_total/lote_kg:,.2f}")
                
                # Generación de Reporte PDF Corporativo con fpdf2
                class PDF(FPDF):
                    def header(self):
                        self.set_fill_ofp = (27, 77, 62)
                        self.rect(0, 0, 210, 25, 'F')
                        self.set_font('Helvetica', 'B', 14)
                        self.set_text_color(255, 255, 255)
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
                pdf.set_text_color(27, 77, 62)
                pdf.cell(0, 10, f'Plan de Alimentación: {etapa}', 0, 1, 'L')
                
                pdf.set_font('Helvetica', '', 10)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 6, f'Tamano del Lote Producido: {lote_kg} Kg', 0, 1, 'L')
                pdf.cell(0, 6, f'Costo Total de la Formula: ${costo_total:,.2f}', 0, 1, 'L')
                pdf.cell(0, 6, f'Costo Unitario: ${costo_total/lote_kg:,.2f} por Kg', 0, 1, 'L')
                pdf.ln(5)
                
                pdf.set_font('Helvetica', 'B', 10)
                pdf.cell(0, 8, 'Desglose de Ingredientes y Mezcla:', 0, 1, 'L')
                
                pdf.set_font('Helvetica', 'B', 9)
                pdf.set_fill_ofp_color = (224, 242, 236)
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

# --- PESTAÑA 2: BASE DE DATOS Y STOCK ---
with tab2:
    st.markdown("### Gestión de Inventario y Materias Primas")
    st.info("Administre los precios vigentes en el mercado local y el stock físico disponible en su bodega para optimizar las compras y evitar quiebres de inventario.")
    st.dataframe(df_default, use_container_width=True)

# --- PESTAÑA 3: CALCULADORA DE COSTOS ---
with tab3:
    st.markdown("### Análisis Financiero de Producción porcina")
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
    st.metric("Consumo Total Requerido para el Lote (Kg)", f"{consumo_total_lote:,.2f} Kg")
    st.metric("Proyección Financiera de Alimentación ($)", f"${costo_total_proyeccion:,.2f}")

# --- PESTAÑA 4: MODELADO DE CRECIMIENTO ---
with tab4:
    st.markdown("### Parámetros de Crecimiento y Conversión Alimenticia")
    st.write("Control técnico de conversión y ganancia diaria de peso (GDP) adaptado para sistemas convencionales y de cama profunda.")
    
    peso_inicial = st.number_input("Peso Inicial Promedio (kg):", value=30.0)
    peso_final = st.number_input("Peso Final Objetivo (kg):", value=100.0)
    gdp = st.number_input("Ganancia Diaria de Peso Esperada (kg/día):", value=0.8, step=0.05)
    
    if gdp > 0:
        dias_necesarios = (peso_final - peso_inicial) / gdp
        st.success(f"Tiempo estimado para alcanzar la meta: **{dias_necesarios:.1f} días**")
