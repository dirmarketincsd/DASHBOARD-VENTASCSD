import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
from pathlib import Path

# ── CONFIGURACIÓN DE LA PÁGINA ────────────────────────────────────────────────
st.set_page_config(
    page_title="Colombia Smile Design — Dashboard",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CARGA DE LOGO EN BASE64 ───────────────────────────────────────────────────
def get_logo_base64():
    try:
        logo_path = Path(__file__).parent / "LOGO_DORADO.png"
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

logo_b64 = get_logo_base64()

# ── ESTILOS CSS PERSONALIZADOS (CON CORRECCIÓN DE CONTRASTE PARA TEXTOS) ──────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght=300;400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }

/* Forzar letras blancas y legibles en toda la barra lateral */
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] h2, 
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] label {
    color: #ffffff !important;
    font-weight: 500 !important;
}

/* Títulos específicos dentro de la barra lateral en dorado */
section[data-testid="stSidebar"] h3 {
    color: #c9a84c !important;
    font-size: 1.15rem !important;
    margin-bottom: 5px !important;
}

/* Tarjetas de Métricas (KPIs) */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0d0d0d, #1a1500);
    border-radius: 14px; padding: 16px 20px;
    border: 1px solid #c9a84c;
    box-shadow: 0 4px 20px rgba(201,168,76,0.15);
}
div[data-testid="stMetric"] label {
    color: #c9a84c !important; font-size: 0.75rem !important;
    text-transform: uppercase; letter-spacing: 1.2px;
}
div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.9rem !important; font-weight: 700 !important; }

/* Pestañas (Tabs) */
.stTabs [data-baseweb="tab-list"] { gap: 8px; background: #0a0a0a; padding: 8px; border-radius: 12px; border: 1px solid #2a2000; }
.stTabs [data-baseweb="tab"] { background: #111100; border-radius: 8px; color: #c9a84c; padding: 8px 20px; font-weight: 600; border: 1px solid #2a2000; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, #c9a84c, #f0d080) !important; color: #000000 !important; }

/* Barra Lateral (Fondo y Bordes) */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0a00, #111100) !important;
    border-right: 1px solid #c9a84c !important;
}
hr { border-color: #c9a84c !important; opacity: 0.3; }
</style>
""", unsafe_allow_html=True)

# ── CONFIGURACIÓN DE ID DE HOJA Y EQUIPOS ─────────────────────────────────────
SHEET_ID = "1-KjGMIPUGcMynGfTYM7P68E_k0ylcZYeg0Wmgwd-36Q"
PLOT_CFG = dict(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

# Mapeo explícito para comerciales clave
EQUIPOS_BASE = {
    'CAROLINA': 'USA',
    'DANIELA': 'España',
    'EVELYN': 'España'
}

# ── FUNCIÓN EXTRACCIÓN Y COORDINACIÓN DE GOOGLE SHEETS ────────────────────────
@st.cache_data(ttl=60)
def cargar_ventas_diarias():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Ventas%20diarias"
        raw_df = pd.read_csv(url, header=None)
        
        # 1. Buscador dinámico de la fila de encabezados reales
        header_idx = 0
        for i in range(min(15, len(raw_df))):
            fila_valores = raw_df.iloc[i].map(str).str.upper().str.replace(r'\s+', ' ', regex=True).str.strip().values
            if any('RESPONSABLE' in f or 'VALORACIONES' in f for f in fila_valores):
                header_idx = i
                break
        
        # 2. Carga limpia saltando la fila combinada superior
        df = pd.read_csv(url, skiprows=header_idx)
        df.columns = [str(c).strip().upper().replace('  ', ' ') for c in df.columns]
        
        # Diccionario de normalización exacto
        rename_dict = {
            'FECHA': 'Fecha', 'SEMANA': 'Semana', 'RESPONSABLE': 'Responsable',
            'VALORACIONES': 'Valoraciones', 'LEADS WPP': 'Leads WPP', 'LEADS IG': 'Leads IG',
            'SEDE': 'Sede', 'CIERRES AGENDADOS': 'Cierres Agendados',
            'VENTA DIA SIGUIENTE(AGENDADOS)': 'Venta Dia Siguiente'
        }
        df = df.rename(columns=rename_dict)
        
        # 3. Limpieza de filas vacías o totales
        if 'Responsable' in df.columns:
            df = df[df['Responsable'].notna()]
            df['Responsable'] = df['Responsable'].astype(str).str.strip().str.upper()
            df = df[~df['Responsable'].isin(['', 'NAN', 'NAN/A', 'RESPONSABLE', 'TOTAL', 'TOTALES'])]
            
            # 4. Asignación de grupo/país
            def asignar_grupo(fila):
                resp = str(fila.get('Responsable', '')).upper()
                sede = str(fila.get('Sede', '')).upper()
                
                if resp in EQUIPOS_BASE:
                    return EQUIPOS_BASE[resp]
                if any(x in sede for x in ['MADRID', 'BARCELONA', 'ESPAÑA', 'ESP', 'EU']):
                    return 'España'
                if any(x in sede for x in ['MIAMI', 'ORLANDO', 'HOUSTON', 'USA', 'US']):
                    return 'USA'
                return 'Por Clasificar'

            df['Grupo_Pais'] = df.apply(asignar_grupo, axis=1)
            
        # 5. Formateo estructurado de Fechas y cálculo del Día de la Semana con mapeo robusto
        if 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', errors='coerce')
            # Mapeo numérico nativo de Pandas (0=Lunes, 6=Domingo) para evitar fallos por idioma del servidor
            dias_es = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
            df['Dia_Semana'] = df['Fecha'].dt.weekday.map(dias_es)

        # 6. Conversión limpia de métricas comerciales operativas
        columnas_numericas = ['Valoraciones', 'Leads WPP', 'Leads IG', 'Cierres Agendados', 'Venta Dia Siguiente']
        for col in columnas_numericas:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('N/A', '0', case=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            else:
                df[col] = 0
                
        return df
    except Exception as e:
        st.error(f"❌ Error en la coordinación de datos: {e}")
        return pd.DataFrame()

# Carga inicial del DataFrame base
df_base = cargar_ventas_diarias()

if not df_base.empty:
    if 'Semana' not in df_base.columns: df_base['Semana'] = "1"
    if 'Dia_Semana' not in df_base.columns: df_base['Dia_Semana'] = "Todos"
    if 'Grupo_Pais' not in df_base.columns: df_base['Grupo_Pais'] = "Por Clasificar"

# ── BARRA LATERAL: FILTROS DINÁMICOS CRUZADOS ─────────────────────────────────
with st.sidebar:
    if logo_b64:
        st.markdown(f'<div style="text-align:center;padding:16px 0 8px 0"><img src="data:image/png;base64,{logo_b64}" style="width:180px;border-radius:8px"></div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#c9a84c;font-size:0.7rem;text-transform:uppercase;letter-spacing:2px;text-align:center;margin-bottom:10px;font-weight:700">Panel de Control</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("### 🔍 Filtrar Tabla Comercial")
    
    # 1. Filtro por Semana de Operación
    semanas_disp = ["Todas"] + sorted(list(df_base['Semana'].dropna().unique().astype(str))) if not df_base.empty else ["Todas"]
    semana_sel = st.selectbox("📆 Seleccionar Semana", semanas_disp)
    
    # 2. Filtro por Día de la Semana
    dia_sel = st.selectbox("📅 Seleccionar Día", ["Todos", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
    
    # 3. Filtro de Región / Grupo Comercial
    grupo_sel = st.selectbox("🌍 Grupo / País", ["Todos", "USA", "España"])
    
    # 4. Filtro dinámico por Responsable
    if not df_base.empty and 'Responsable' in df_base.columns:
        if grupo_sel == "USA":
            comerciales = df_base[df_base['Grupo_Pais'] == 'USA']['Responsable'].unique().tolist()
        elif grupo_sel == "España":
            comerciales = df_base[df_base['Grupo_Pais'] == 'España']['Responsable'].unique().tolist()
        else:
            comerciales = df_base['Responsable'].unique().tolist()
        vendedores = ["Todos"] + sorted(comerciales)
    else:
        vendedores = ["Todos"]
    responsable_sel = st.selectbox("👤 Responsable Comercial", vendedores)
    
    st.markdown("---")
    if st.button("🔄 Forzar Actualización"):
        st.cache_data.clear()
        st.rerun()

# ── APLICAR FILTRADO MULTINIVEL AL DATAFRAME ──────────────────────────────────
df_filtrado = df_base.copy()

if not df_filtrado.empty:
    if semana_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Semana'].astype(str) == semana_sel]
    if dia_sel != "Todos" and 'Dia_Semana' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Dia_Semana'] == dia_sel]
    if grupo_sel != "Todos" and 'Grupo_Pais' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Grupo_Pais'] == grupo_sel]
    if responsable_sel != "Todos" and 'Responsable' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Responsable'] == responsable_sel]

# ── DISEÑO DE LA INTERFAZ PRINCIPAL ───────────────────────────────────────────
col_logo_h, col_title_h = st.columns([1.2, 4])
with col_logo_h:
    if logo_b64:
        st.markdown(f'<img src="data:image/png;base64,{logo_b64}" style="width:160px;margin-top:10px;border-radius:8px">', unsafe_allow_html=True)
with col_title_h:
    st.markdown("""
    <div style="padding-top:5px;text-align:left">
        <div style="color:#c9a84c;font-size:0.8rem;text-transform:uppercase;letter-spacing:3px">Colombia Smile Design</div>
        <div style="color:#ffffff;font-size:2.2rem;font-weight:800;line-height:1.2">Dashboard de Ventas Diarias</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

tab1, tab2 = st.tabs(["📋 Vista Estilo Google Sheets", "📊 Vista Global por Grupos"])

# ==========================================
# ══ TAB 1 — VISTA FILTRADA (ESTILO SHEETS) 
# ==========================================
with tab1:
    st.markdown(f"### 📊 Resumen Ejecutivo (Semana: {semana_sel} / Día: {dia_sel} / Grupo: {grupo_sel})")
    
    if df_filtrado.empty:
        st.warning("⚠️ No se encontraron registros para el día o los filtros seleccionados. Intenta cambiando el filtro de 'Día' o pon 'Semana' en 'Todas'.")
    else:
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric("💬 Leads WPP", f"{int(df_filtrado['Leads WPP'].sum())}")
        kpi2.metric("📸 Leads IG", f"{int(df_filtrado['Leads IG'].sum())}")
        kpi3.metric("⭐ Valoraciones", f"{int(df_filtrado['Valoraciones'].sum())}")
        kpi4.metric("📅 Agendados (Mañana)", f"{int(df_filtrado['Venta Dia Siguiente'].sum())}")
        kpi5.metric("🏆 Cierres", f"{int(df_filtrado['Cierres Agendados'].sum())}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        columnas_visibles = [
            'Fecha', 'Semana', 'Dia_Semana', 'Responsable', 'Grupo_Pais', 'Sede', 
            'Leads WPP', 'Leads IG', 'Valoraciones', 'Venta Dia Siguiente', 'Cierres Agendados'
        ]
        cols_existentes = [c for c in columnas_visibles if c in df_filtrado.columns]
        
        st.markdown("#### 📋 Registros Diarios Coordinados")
        if cols_existentes:
            df_mostrar = df_filtrado[cols_existentes].copy()
            if 'Fecha' in df_mostrar.columns and not df_mostrar['Fecha'].isnull().all():
                df_mostrar['Fecha'] = df_mostrar['Fecha'].dt.strftime('%d/%m/%Y')
                
            st.dataframe(
                df_mostrar,
                use_container_width=True,
                hide_index=True
            )
        
        if 'Responsable' in df_filtrado.columns and not df_filtrado.empty:
            st.markdown("---")
            st.markdown("#### 📈 Leads Entrantes por Canal y Comercial")
            
            df_leads = df_filtrado.groupby('Responsable', as_index=False)[['Leads WPP', 'Leads IG']].sum()
            
            if not df_leads.empty and (df_leads['Leads WPP'].sum() > 0 or df_leads['Leads IG'].sum() > 0):
                fig_leads = px.bar(
                    df_leads, 
                    x='Responsable', 
                    y=['Leads WPP', 'Leads IG'],
                    barmode='group', 
                    title="Canal de Entrada (WhatsApp vs Instagram)",
                    color_discrete_sequence=['#00d4aa', '#7c6af7'], 
                    template='plotly_dark'
                )
                fig_leads.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_leads, use_container_width=True)

# ==========================================
# ══ TAB 2 — DESGLOSE REGIONAL USA VS ESPAÑA
# ==========================================
with tab2:
    st.markdown("### 🌍 Desglose Consolidado por Países")
    
    col_usa, col_esp = st.columns(2)
    columnas_agrupar = [c for c in ['Leads WPP', 'Leads IG', 'Valoraciones', 'Venta Dia Siguiente', 'Cierres Agendados'] if c in df_base.columns]
    
    with col_usa:
        st.markdown("<h4 style='color:#7c6af7;'>🇺🇸 Grupo USA</h4>", unsafe_allow_html=True)
        if not df_base.empty and 'Grupo_Pais' in df_base.columns:
            df_usa_panel = df_base[df_base['Grupo_Pais'] == 'USA']
            if not df_usa_panel.empty:
                st.dataframe(df_usa_panel.groupby('Responsable')[columnas_agrupar].sum(), use_container_width=True)
            else:
                st.info("No hay datos para el equipo de USA.")
            
    with col_esp:
        st.markdown("<h4 style='color:#00d4aa;'>🇪🇸 Grupo España</h4>", unsafe_allow_html=True)
        if not df_base.empty and 'Grupo_Pais' in df_base.columns:
            df_esp_panel = df_base[df_base['Grupo_Pais'] == 'España']
            if not df_esp_panel.empty:
                st.dataframe(df_esp_panel.groupby('Responsable')[columnas_agrupar].sum(), use_container_width=True)
            else:
                st.info("No hay datos para el equipo de España.")