import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import base64
from pathlib import Path

st.set_page_config(
    page_title="Colombia Smile Design — Dashboard",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_logo_base64():
    try:
        logo_path = Path(__file__).parent / "LOGO_DORADO.png"
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

logo_b64 = get_logo_base64()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }

section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] label { color: #ffffff !important; font-weight: 500 !important; }
section[data-testid="stSidebar"] h3 { color: #c9a84c !important; font-size: 1.1rem !important; }

div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0d0d0d, #1a1500);
    border-radius: 14px; padding: 16px 20px;
    border: 1px solid #c9a84c;
    box-shadow: 0 4px 20px rgba(201,168,76,0.15);
}
div[data-testid="stMetric"] label { color: #c9a84c !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 1.2px; }
div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.9rem !important; font-weight: 700 !important; }
div[data-testid="stMetricDelta"] { color: #f0d080 !important; }

.stTabs [data-baseweb="tab-list"] { gap: 8px; background: #0a0a0a; padding: 8px; border-radius: 12px; border: 1px solid #2a2000; }
.stTabs [data-baseweb="tab"] { background: #111100; border-radius: 8px; color: #c9a84c; padding: 8px 20px; font-weight: 600; border: 1px solid #2a2000; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, #c9a84c, #f0d080) !important; color: #000000 !important; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0a00, #111100) !important;
    border-right: 1px solid #c9a84c !important;
}
hr { border-color: #c9a84c !important; opacity: 0.3; }
</style>
""", unsafe_allow_html=True)

# ── CONFIG ─────────────────────────────────────────────────────────────────────
SHEET_ID = "1-KjGMIPUGcMynGfTYM7P68E_k0ylcZYeg0Wmgwd-36Q"
PLOT_CFG = dict(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

EQUIPOS_BASE = {
    'CAROLINA': 'USA',
    'DANIELA': 'España',
    'EVELYN': 'España'
}

# ── CARGA DE DATOS ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def cargar_ventas_diarias():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Ventas%20diarias"
        raw_df = pd.read_csv(url, header=None)

        # Buscar fila de encabezados
        header_idx = 0
        for i in range(min(15, len(raw_df))):
            vals = raw_df.iloc[i].map(str).str.upper().str.strip().values
            if any('RESPONSABLE' in v or 'VALORACIONES' in v for v in vals):
                header_idx = i
                break

        df = pd.read_csv(url, skiprows=header_idx)
        df.columns = [str(c).strip().upper().replace('  ', ' ') for c in df.columns]

        rename_dict = {
            'FECHA': 'Fecha',
            'DIA': 'Dia_Texto',
            'SEMANA': 'Semana',
            'RESPONSABLE': 'Responsable',
            'VALORACIONES': 'Valoraciones',
            'LEADS WPP': 'Leads WPP',
            'LEADS IG': 'Leads IG',
            'SEDE': 'Sede',
            'CIERRES AGENDADOS': 'Cierres',
            'VENTA DIA SIGUIENTE(AGENDADOS)': 'Venta Dia Siguiente'
        }
        df = df.rename(columns=rename_dict)

        # Limpiar responsables
        if 'Responsable' in df.columns:
            df = df[df['Responsable'].notna()]
            df['Responsable'] = df['Responsable'].astype(str).str.strip().str.upper()
            df = df[~df['Responsable'].isin(['', 'NAN', 'N/A', 'RESPONSABLE', 'TOTAL', 'TOTALES'])]

            def asignar_grupo(fila):
                resp = str(fila.get('Responsable', '')).upper()
                sede = str(fila.get('Sede', '')).upper()
                if resp in EQUIPOS_BASE:
                    return EQUIPOS_BASE[resp]
                if any(x in sede for x in ['MADRID','BARCELONA','VALENCIA','ALICANTE','MALAGA','BILBAO','ESPAÑA','ESP']):
                    return 'España'
                if any(x in sede for x in ['DALLAS','HOUSTON','ORLANDO','JERSEY','LOS ANGELES','MIAMI','USA','US']):
                    return 'USA'
                return 'Por Clasificar'

            df['Grupo_Pais'] = df.apply(asignar_grupo, axis=1)

        # Parsear fecha
        if 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
            df = df[df['Fecha'].notna()]

        # Día de la semana desde columna DIA o desde Fecha
        DIAS_NORM = {
            'LUNES':'Lunes','MARTES':'Martes','MIERCOLES':'Miércoles','MIÉRCOLES':'Miércoles',
            'JUEVES':'Jueves','VIERNES':'Viernes','SABADO':'Sábado','SÁBADO':'Sábado','DOMINGO':'Domingo'
        }
        if 'Dia_Texto' in df.columns:
            df['Dia_Semana'] = df['Dia_Texto'].astype(str).str.strip().str.upper().map(DIAS_NORM).fillna('Sin dato')
        elif 'Fecha' in df.columns:
            nombres = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
            df['Dia_Semana'] = df['Fecha'].dt.dayofweek.map(lambda x: nombres[x])
        else:
            df['Dia_Semana'] = 'Sin dato'

        # Semana
        if 'Semana' not in df.columns:
            df['Semana'] = '1'
        df['Semana'] = df['Semana'].astype(str).str.strip()

        # Columnas numéricas
        cols_num = ['Valoraciones','Leads WPP','Leads IG','Cierres','Venta Dia Siguiente']
        for col in cols_num:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('N/A','0',case=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            else:
                df[col] = 0

        return df

    except Exception as e:
        st.error(f"❌ Error cargando datos: {e}")
        return pd.DataFrame()

df_base = cargar_ventas_diarias()

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    if logo_b64:
        st.markdown(f'<div style="text-align:center;padding:16px 0 8px 0"><img src="data:image/png;base64,{logo_b64}" style="width:180px;border-radius:8px"></div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#c9a84c;font-size:0.7rem;text-transform:uppercase;letter-spacing:2px;text-align:center;margin-bottom:10px;font-weight:700">Panel de Control</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🔍 Filtros")

    # ── Filtro por FECHA específica o rango ──
    modo_fecha = st.radio("📅 Filtrar por", ["Día específico", "Rango de fechas", "Semana", "Todos"], horizontal=False)

    fecha_ini = None
    fecha_fin = None

    if modo_fecha == "Día específico":
        fecha_sel = st.date_input("Selecciona el día", value=date.today())
        fecha_ini = fecha_fin = pd.Timestamp(fecha_sel)

    elif modo_fecha == "Rango de fechas":
        fecha_ini = pd.Timestamp(st.date_input("Desde", value=date.today() - timedelta(days=6)))
        fecha_fin = pd.Timestamp(st.date_input("Hasta", value=date.today()))

    elif modo_fecha == "Semana":
        semanas_disp = ["Todas"]
        if not df_base.empty and 'Semana' in df_base.columns:
            semanas_disp += sorted(df_base['Semana'].dropna().unique().tolist(),
                                   key=lambda x: int(x) if str(x).isdigit() else 0)
        semana_sel = st.selectbox("📆 Semana", semanas_disp)

    # ── Filtro por Día de la semana ──
    dia_sel = st.selectbox("📅 Día de la semana", ["Todos","Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"])

    # ── Filtro por Grupo / País ──
    grupo_sel = st.selectbox("🌍 Grupo / País", ["Todos","USA","España"])

    # ── Filtro por Responsable ──
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
    responsable_sel = st.selectbox("👤 Responsable", vendedores)

    st.markdown("---")
    if st.button("🔄 Actualizar datos"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Se actualiza cada 60 seg")

# ── APLICAR FILTROS ────────────────────────────────────────────────────────────
df_filtrado = df_base.copy()

if not df_filtrado.empty:
    # Filtro fecha
    if modo_fecha == "Día específico" and fecha_ini is not None:
        df_filtrado = df_filtrado[df_filtrado['Fecha'].dt.date == fecha_ini.date()]
    elif modo_fecha == "Rango de fechas" and fecha_ini is not None and fecha_fin is not None:
        df_filtrado = df_filtrado[(df_filtrado['Fecha'] >= fecha_ini) & (df_filtrado['Fecha'] <= fecha_fin)]
    elif modo_fecha == "Semana" and semana_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Semana'].astype(str) == semana_sel]

    # Filtro día semana
    if dia_sel != "Todos" and 'Dia_Semana' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Dia_Semana'] == dia_sel]

    # Filtro grupo
    if grupo_sel != "Todos" and 'Grupo_Pais' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Grupo_Pais'] == grupo_sel]

    # Filtro responsable
    if responsable_sel != "Todos" and 'Responsable' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Responsable'] == responsable_sel]

# ── HEADER ─────────────────────────────────────────────────────────────────────
col_logo_h, col_title_h = st.columns([1, 4])
with col_logo_h:
    if logo_b64:
        st.markdown(f'<img src="data:image/png;base64,{logo_b64}" style="width:160px;margin-top:10px;border-radius:8px">', unsafe_allow_html=True)
with col_title_h:
    st.markdown("""
    <div style="padding-top:5px">
        <div style="color:#c9a84c;font-size:0.8rem;text-transform:uppercase;letter-spacing:3px">Colombia Smile Design</div>
        <div style="color:#ffffff;font-size:2.2rem;font-weight:800;line-height:1.2">Dashboard de Ventas Diarias</div>
        <div style="color:#c9a84c;font-size:0.85rem">España 🇪🇸 · USA 🇺🇸 · Seguimiento en tiempo real</div>
    </div>""", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2 = st.tabs(["📋 Ventas Diarias", "🌍 Vista por Grupos"])

# ══ TAB 1 ══════════════════════════════════════════════════════════════════════
with tab1:
    # Descripción del filtro activo
    filtro_desc = []
    if modo_fecha == "Día específico" and fecha_ini:
        filtro_desc.append(f"📅 {fecha_ini.strftime('%d/%m/%Y')}")
    elif modo_fecha == "Rango de fechas" and fecha_ini and fecha_fin:
        filtro_desc.append(f"📅 {fecha_ini.strftime('%d/%m')} → {fecha_fin.strftime('%d/%m/%Y')}")
    elif modo_fecha == "Semana":
        filtro_desc.append(f"Semana {semana_sel}")
    if dia_sel != "Todos": filtro_desc.append(dia_sel)
    if grupo_sel != "Todos": filtro_desc.append(grupo_sel)
    if responsable_sel != "Todos": filtro_desc.append(responsable_sel)
    desc = " · ".join(filtro_desc) if filtro_desc else "Todos los registros"

    st.markdown(f"### 📊 Resumen — {desc}")

    if df_filtrado.empty:
        st.warning("⚠️ No hay registros con estos filtros. Prueba cambiando el día o la fecha.")
    else:
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("💬 Leads WPP",       int(df_filtrado['Leads WPP'].sum()))
        k2.metric("📸 Leads IG",        int(df_filtrado['Leads IG'].sum()))
        k3.metric("⭐ Valoraciones",     int(df_filtrado['Valoraciones'].sum()))
        k4.metric("📅 Agend. Mañana",   int(df_filtrado['Venta Dia Siguiente'].sum()))
        k5.metric("🏆 Cierres",         int(df_filtrado['Cierres'].sum()))

        st.markdown("<br>", unsafe_allow_html=True)

        # Tabla detalle
        cols_vis = ['Fecha','Semana','Dia_Semana','Responsable','Grupo_Pais','Sede',
                    'Leads WPP','Leads IG','Valoraciones','Venta Dia Siguiente','Cierres']
        cols_ok = [c for c in cols_vis if c in df_filtrado.columns]
        df_show = df_filtrado[cols_ok].copy()
        if 'Fecha' in df_show.columns:
            df_show['Fecha'] = df_show['Fecha'].dt.strftime('%d/%m/%Y')

        st.markdown("#### 📋 Registros Filtrados")
        st.dataframe(df_show, use_container_width=True, hide_index=True)

        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Descargar CSV", data=csv,
                           file_name=f"ventas_{date.today()}.csv", mime="text/csv")

        st.markdown("---")

        # Gráficas
        if 'Responsable' in df_filtrado.columns:
            g1, g2 = st.columns(2)
            with g1:
                st.markdown("#### 📈 Leads por Canal y Comercial")
                df_leads = df_filtrado.groupby('Responsable')[['Leads WPP','Leads IG']].sum().reset_index()
                if df_leads[['Leads WPP','Leads IG']].sum().sum() > 0:
                    fig = px.bar(df_leads, x='Responsable', y=['Leads WPP','Leads IG'],
                                 barmode='group', color_discrete_sequence=['#00d4aa','#7c6af7'])
                    fig.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Sin datos de leads para este filtro.")

            with g2:
                st.markdown("#### 🏆 Cierres por Comercial")
                df_cierres = df_filtrado.groupby('Responsable')['Cierres'].sum().reset_index()
                if df_cierres['Cierres'].sum() > 0:
                    fig2 = px.bar(df_cierres, x='Responsable', y='Cierres',
                                  color='Cierres', color_continuous_scale='teal')
                    fig2.update_layout(coloraxis_showscale=False, **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("Sin cierres para este filtro.")

            # Evolución por fecha si hay rango
            if modo_fecha in ["Rango de fechas", "Todos", "Semana"] and 'Fecha' in df_filtrado.columns:
                st.markdown("#### 📅 Evolución Diaria de Cierres")
                df_evo = df_filtrado.groupby('Fecha')['Cierres'].sum().reset_index()
                if len(df_evo) > 1:
                    fig3 = px.line(df_evo, x='Fecha', y='Cierres',
                                   color_discrete_sequence=['#00d4aa'], markers=True)
                    fig3.update_traces(fill='tozeroy', fillcolor='rgba(0,212,170,0.08)')
                    fig3.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
                    st.plotly_chart(fig3, use_container_width=True)

# ══ TAB 2 ══════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 🌍 Desglose por Grupos — USA vs España")

    col_usa, col_esp = st.columns(2)
    cols_num = [c for c in ['Leads WPP','Leads IG','Valoraciones','Venta Dia Siguiente','Cierres'] if c in df_base.columns]

    with col_usa:
        st.markdown("<h4 style='color:#7c6af7;'>🇺🇸 Grupo USA</h4>", unsafe_allow_html=True)
        df_usa_p = df_base[df_base['Grupo_Pais'] == 'USA'] if not df_base.empty else pd.DataFrame()
        if not df_usa_p.empty:
            df_usa_g = df_usa_p.groupby('Responsable')[cols_num].sum()
            st.dataframe(df_usa_g, use_container_width=True)
            # Gráfica
            fig_u = px.bar(df_usa_g.reset_index(), x='Responsable', y='Cierres',
                           color='Cierres', color_continuous_scale='purples')
            fig_u.update_layout(coloraxis_showscale=False, **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_u, use_container_width=True)
        else:
            st.info("Sin datos para USA.")

    with col_esp:
        st.markdown("<h4 style='color:#00d4aa;'>🇪🇸 Grupo España</h4>", unsafe_allow_html=True)
        df_esp_p = df_base[df_base['Grupo_Pais'] == 'España'] if not df_base.empty else pd.DataFrame()
        if not df_esp_p.empty:
            df_esp_g = df_esp_p.groupby('Responsable')[cols_num].sum()
            st.dataframe(df_esp_g, use_container_width=True)
            # Gráfica
            fig_e = px.bar(df_esp_g.reset_index(), x='Responsable', y='Cierres',
                           color='Cierres', color_continuous_scale='teal')
            fig_e.update_layout(coloraxis_showscale=False, **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_e, use_container_width=True)
        else:
            st.info("Sin datos para España.")

    # Comparativo global
    st.markdown("---")
    st.markdown("#### 📊 Comparativo Global USA vs España")
    if not df_base.empty and 'Grupo_Pais' in df_base.columns:
        df_comp = df_base[df_base['Grupo_Pais'].isin(['USA','España'])].groupby('Grupo_Pais')[cols_num].sum().reset_index()
        fig_comp = px.bar(df_comp, x='Grupo_Pais', y=cols_num, barmode='group',
                          color_discrete_sequence=['#00d4aa','#7c6af7','#f0d080','#f7a76c','#4fc3f7'])
        fig_comp.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
        st.plotly_chart(fig_comp, use_container_width=True)