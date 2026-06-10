from datetime import date, timedelta

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Colombia Smile Design — Dashboard",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="expanded"
)

from styles import get_logo_base64, inject_css
from data_loaders import cargar_ventas_diarias, get_val
from tabs import ventas_diarias, metas, espana, usa, global_tab, campanas

logo_b64 = get_logo_base64()
inject_css()

# ── CARGAR DATOS BASE ──────────────────────────────────────────────────────────
df_base = cargar_ventas_diarias()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    if logo_b64:
        st.markdown(f'<div style="text-align:center;padding:16px 0 8px 0"><img src="data:image/png;base64,{logo_b64}" style="width:180px;border-radius:8px"></div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#c9a84c;font-size:0.7rem;text-transform:uppercase;letter-spacing:2px;text-align:center;margin-bottom:10px;font-weight:700">Panel de Control</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🔍 Filtros")

    modo_fecha = st.radio("📅 Filtrar por", ["Todos","Día específico","Rango de fechas","Semana"])
    fecha_ini = fecha_fin = None
    semana_sel = "Todas"

    if modo_fecha == "Día específico":
        fecha_sel = st.date_input("Selecciona el día", value=date.today())
        fecha_ini = fecha_fin = pd.Timestamp(fecha_sel)
    elif modo_fecha == "Rango de fechas":
        fecha_ini = pd.Timestamp(st.date_input("Desde", value=date.today()-timedelta(days=6)))
        fecha_fin = pd.Timestamp(st.date_input("Hasta", value=date.today()))
    elif modo_fecha == "Semana":
        sems = ["Todas"]
        if not df_base.empty and 'Semana' in df_base.columns:
            sems += sorted(df_base['Semana'].dropna().unique().tolist(),
                           key=lambda x: int(x) if str(x).isdigit() else 0)
        semana_sel = st.selectbox("📆 Semana", sems)

    dia_sel   = st.selectbox("📅 Día de la semana", ["Todos","Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"])
    grupo_sel = st.selectbox("🌍 Grupo / País", ["Todos","USA","España"])

    if not df_base.empty and 'Responsable' in df_base.columns:
        if grupo_sel == "USA":
            coms = df_base[df_base['Grupo_Pais']=='USA']['Responsable'].unique().tolist()
        elif grupo_sel == "España":
            coms = df_base[df_base['Grupo_Pais']=='España']['Responsable'].unique().tolist()
        else:
            coms = df_base['Responsable'].unique().tolist()
        vendedores = ["Todos"] + sorted(coms)
    else:
        vendedores = ["Todos"]
    responsable_sel = st.selectbox("👤 Responsable", vendedores)

    st.markdown("---")
    if st.button("🔄 Actualizar datos"):
        st.cache_data.clear(); st.rerun()
    st.caption("Se actualiza cada 60 seg")

# ══════════════════════════════════════════════════════════════════════════════
# APLICAR FILTROS
# ══════════════════════════════════════════════════════════════════════════════
df_filtrado = df_base.copy()
if not df_filtrado.empty and 'Fecha' in df_filtrado.columns:
    if modo_fecha == "Día específico" and fecha_ini is not None:
        df_filtrado = df_filtrado[df_filtrado['Fecha'].dt.date == fecha_ini.date()]
    elif modo_fecha == "Rango de fechas" and fecha_ini is not None:
        df_filtrado = df_filtrado[(df_filtrado['Fecha']>=fecha_ini)&(df_filtrado['Fecha']<=fecha_fin)]
    elif modo_fecha == "Semana" and semana_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Semana'].astype(str)==semana_sel]
    if dia_sel != "Todos" and 'Dia_Semana' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Dia_Semana']==dia_sel]
    if grupo_sel != "Todos" and 'Grupo_Pais' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Grupo_Pais']==grupo_sel]
    if responsable_sel != "Todos" and 'Responsable' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Responsable']==responsable_sel]

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
col_logo_h, col_title_h = st.columns([1,4])
with col_logo_h:
    if logo_b64:
        st.markdown(f'<img src="data:image/png;base64,{logo_b64}" style="width:160px;margin-top:10px;border-radius:8px">', unsafe_allow_html=True)
with col_title_h:
    st.markdown("""
    <div style="padding-top:5px">
        <div style="color:#c9a84c;font-size:0.8rem;text-transform:uppercase;letter-spacing:3px">Colombia Smile Design</div>
        <div style="color:#ffffff;font-size:2.2rem;font-weight:800;line-height:1.2">Dashboard de Ventas</div>
        <div style="color:#c9a84c;font-size:0.85rem">España 🇪🇸 · USA 🇺🇸 · Tiempo real</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# RESUMEN FIJO
# ══════════════════════════════════════════════════════════════════════════════
hoy_ts     = pd.Timestamp(date.today())
inicio_sem = hoy_ts - timedelta(days=hoy_ts.weekday())
inicio_mes = hoy_ts.replace(day=1)

df_semana_fija = pd.DataFrame()
df_hoy_fija    = pd.DataFrame()
df_mes_fija    = pd.DataFrame()

if not df_base.empty and 'Fecha' in df_base.columns:
    df_semana_fija = df_base[(df_base['Fecha'] >= inicio_sem) & (df_base['Fecha'] <= hoy_ts)]
    df_hoy_fija    = df_base[df_base['Fecha'].dt.date == hoy_ts.date()]
    df_mes_fija    = df_base[(df_base['Fecha'] >= inicio_mes) & (df_base['Fecha'] <= hoy_ts)]

lunes_str = inicio_sem.strftime('%d/%m')
hoy_str   = hoy_ts.strftime('%d/%m/%Y')

periodo_resumen = st.radio(
    "📊 Ver resumen fijo por:",
    ["📅 Hoy", "📆 Esta semana", "🗓️ Este mes"],
    horizontal=True,
    key="periodo_resumen_toggle"
)

if periodo_resumen == "📅 Hoy":
    df_resumen_fijo = df_hoy_fija
    label_periodo   = f"Hoy — {hoy_str}"
elif periodo_resumen == "📆 Esta semana":
    df_resumen_fijo = df_semana_fija
    label_periodo   = f"Semana — {lunes_str} al {hoy_str}"
else:
    df_resumen_fijo = df_mes_fija
    label_periodo   = f"Mes — {inicio_mes.strftime('%d/%m')} al {hoy_str}"

df_rfijo_usa = df_resumen_fijo[df_resumen_fijo['Grupo_Pais']=='USA']    if not df_resumen_fijo.empty and 'Grupo_Pais' in df_resumen_fijo.columns else pd.DataFrame()
df_rfijo_esp = df_resumen_fijo[df_resumen_fijo['Grupo_Pais']=='España'] if not df_resumen_fijo.empty and 'Grupo_Pais' in df_resumen_fijo.columns else pd.DataFrame()

st.markdown(f"""
<div class="resumen-fijo">
    <div class="resumen-fijo-titulo">📊 Resumen Fijo · Independiente de filtros</div>
    <div class="resumen-fijo-sub">⏱ {label_periodo}</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="grupo-label-usa">🇺🇸 USA</div>', unsafe_allow_html=True)
u1,u2,u3,u4,u5,u6,u7 = st.columns(7)
u1.metric("💬 WPP",         get_val(df_rfijo_usa,'Leads WPP'))
u2.metric("📸 IG",          get_val(df_rfijo_usa,'Leads IG'))
u3.metric("📝 Formulario",  get_val(df_rfijo_usa,'Leads Formulario'))
u4.metric("🌐 Landing",     get_val(df_rfijo_usa,'Leads Landing'))
u5.metric("🎵 TikTok",      get_val(df_rfijo_usa,'Leads TikTok'))
u6.metric("⭐ Valoraciones",get_val(df_rfijo_usa,'Valoraciones'))
u7.metric("💰 Depósitos",   get_val(df_rfijo_usa,'Cierres'))

st.markdown("<br>", unsafe_allow_html=True)

st.markdown('<div class="grupo-label-esp">🇪🇸 España</div>', unsafe_allow_html=True)
e1,e2,e3,e4,e5,e6,e7 = st.columns(7)
e1.metric("💬 WPP",         get_val(df_rfijo_esp,'Leads WPP'))
e2.metric("📸 IG",          get_val(df_rfijo_esp,'Leads IG'))
e3.metric("📝 Formulario",  get_val(df_rfijo_esp,'Leads Formulario'))
e4.metric("🌐 Landing",     get_val(df_rfijo_esp,'Leads Landing'))
e5.metric("🎵 TikTok",      get_val(df_rfijo_esp,'Leads TikTok'))
e6.metric("⭐ Valoraciones",get_val(df_rfijo_esp,'Valoraciones'))
e7.metric("💰 Depósitos",   get_val(df_rfijo_esp,'Cierres'))

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# CONTEXTO COMPARTIDO + TABS
# ══════════════════════════════════════════════════════════════════════════════
ctx = {
    'df_base':         df_base,
    'df_filtrado':     df_filtrado,
    'modo_fecha':      modo_fecha,
    'fecha_ini':       fecha_ini,
    'fecha_fin':       fecha_fin,
    'semana_sel':      semana_sel,
    'dia_sel':         dia_sel,
    'grupo_sel':       grupo_sel,
    'responsable_sel': responsable_sel,
    'hoy_ts':          hoy_ts,
    'inicio_sem':      inicio_sem,
    'inicio_mes':      inicio_mes,
}

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Ventas Diarias","🎯 Metas","🇪🇸 España Mayo",
    "🇺🇸 USA Mayo","🌍 Global","📢 Campañas Meta Ads"
])

with tab1: ventas_diarias.render(ctx)
with tab2: metas.render(ctx)
with tab3: espana.render(ctx)
with tab4: usa.render(ctx)
with tab5: global_tab.render(ctx)
with tab6: campanas.render(ctx)
