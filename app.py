import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import base64
from pathlib import Path

# ── CONFIGURACIÓN DE LA PÁGINA ───────────────────────────────────────────────
st.set_page_config(
    page_title="Colombia Smile Design — Dashboard",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── ESTILOS CUSTOMIZADOS (CSS) ────────────────────────────────────────────────
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
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #0a0a00, #111100) !important; border-right: 1px solid #c9a84c !important; }
hr { border-color: #c9a84c !important; opacity: 0.3; }
.resumen-fijo {
    background: linear-gradient(135deg, #0a0a00, #111100);
    border: 1.5px solid #c9a84c;
    border-radius: 18px;
    padding: 20px 24px;
    margin-bottom: 20px;
    box-shadow: 0 6px 30px rgba(201,168,76,0.12);
}
.resumen-fijo-titulo {
    color: #c9a84c;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 2.5px;
    margin-bottom: 2px;
    font-weight: 700;
}
.resumen-fijo-sub {
    color: #ffffff;
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 14px;
    opacity: 0.85;
}
.grupo-label-usa {
    color: #7c6af7;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 6px;
}
.grupo-label-esp {
    color: #00d4aa;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)

# ── CONFIGURACIÓN GLOBAL ───────────────────────────────────────────────────────
SHEET_ID      = "1-KjGMIPUGcMynGfTYM7P68E_k0ylcZYeg0Wmgwd-36Q"
PLOT_CFG      = dict(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
EQUIPOS_BASE  = {'CAROLINA': 'USA', 'DANIELA': 'España', 'EVELYN': 'España'}
META_DIARIA   = 4
META_SEMANAL  = 40
META_MENSUAL  = 100

def sheet_url(nombre):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre.replace(' ','%20')}"

@st.cache_data(ttl=60)
def get_logo_base64():
    try:
        logo_path = Path(__file__).parent / "LOGO_DORADO.png"
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

logo_b64 = get_logo_base64()

# ── CARGA VENTAS DIARIAS ───────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def cargar_ventas_diarias():
    try:
        url = sheet_url("Ventas diarias")
        raw = pd.read_csv(url, header=None)
        header_idx = 3
        for i in range(min(10, len(raw))):
            vals = [str(v).strip().upper() for v in raw.iloc[i].tolist()]
            if 'FECHA' in vals and 'RESPONSABLE' in vals:
                header_idx = i
                break
        df = pd.read_csv(url, skiprows=header_idx, header=0)
        df.columns = [str(c).strip().upper().replace('  ',' ') for c in df.columns]
        df = df.iloc[:, :11]
        df.columns = ['FECHA','DIA','RESPONSABLE','VALORACIONES','LEADS WPP','LEADS IG',
                      'LEADS FORMULARIO','LEADS LANDING','LEADS TIKTOK','DEPOSITOS','PRESUPUESTADO']
        rename = {
            'FECHA':'Fecha', 'DIA':'Dia_Texto', 'SEMANA':'Semana',
            'RESPONSABLE':'Responsable', 'VALORACIONES':'Valoraciones',
            'LEADS WPP':'Leads WPP', 'LEADS IG':'Leads IG',
            'LEADS FORMULARIO':'Leads Formulario', 'LEADS LANDING':'Leads Landing',
            'LEADS TIKTOK':'Leads TikTok', 'SEDE':'Sede',
            'DEPOSITOS':'Cierres', 'PRESUPUESTADO':'Venta Dia Siguiente',
            'CIERRES AGENDADOS':'Cierres',
            'VENTA DIA SIGUIENTE(AGENDADOS)':'Venta Dia Siguiente'
        }
        df = df.rename(columns=rename)
        if 'Responsable' in df.columns:
            df = df[df['Responsable'].notna()]
            df['Responsable'] = df['Responsable'].astype(str).str.strip().str.upper()
            df = df[~df['Responsable'].isin(['','NAN','N/A','RESPONSABLE','TOTAL','TOTALES'])]
            def asignar_grupo(r):
                resp = str(r.get('Responsable','')).upper()
                sede = str(r.get('Sede','')).upper()
                if resp in EQUIPOS_BASE: return EQUIPOS_BASE[resp]
                if any(x in sede for x in ['MADRID','BARCELONA','VALENCIA','ALICANTE','MALAGA','BILBAO','ESPAÑA']): return 'España'
                if any(x in sede for x in ['DALLAS','HOUSTON','ORLANDO','JERSEY','ANGELES','MIAMI','USA']): return 'USA'
                return 'Por Clasificar'
            df['Grupo_Pais'] = df.apply(asignar_grupo, axis=1)
            
        if 'Fecha' in df.columns:
            # CORRECCIÓN DE PARSEO: Forzamos orden de día primero para evitar saltos cruzados a meses incorrectos
            df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', errors='coerce')
            df['Fecha'] = df['Fecha'].fillna(pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce'))
            df['Fecha'] = df['Fecha'].ffill()
            df = df[df['Fecha'].notna()]
            
        if 'Dia_Texto' in df.columns:
            df['Dia_Texto'] = df['Dia_Texto'].ffill()
        DIAS_NORM = {'LUNES':'Lunes','MARTES':'Martes','MIERCOLES':'Miércoles',
                     'MIÉRCOLES':'Miércoles','JUEVES':'Jueves','VIERNES':'Viernes',
                     'SABADO':'Sábado','SÁBADO':'Sábado','DOMINGO':'Domingo'}
        if 'Dia_Texto' in df.columns:
            df['Dia_Semana'] = df['Dia_Texto'].astype(str).str.strip().str.upper().map(DIAS_NORM).fillna('Sin dato')
        elif 'Fecha' in df.columns:
            nombres = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
            df['Dia_Semana'] = df['Fecha'].dt.dayofweek.map(lambda x: nombres[x])
        else:
            df['Dia_Semana'] = 'Sin dato'
        if 'Semana' not in df.columns: df['Semana'] = '1'
        df['Semana'] = df['Semana'].astype(str).str.strip()
        for col in ['Valoraciones','Leads WPP','Leads IG','Leads Formulario','Leads Landing','Leads TikTok','Cierres','Venta Dia Siguiente']:
            if col in df.columns:
                serie = df[col].astype(str).str.strip()
                serie = serie.replace({'N/A':'0','n/a':'0','NA':'0','nan':'0','None':'0','':'0'}, regex=False)
                serie = serie.str.replace('[^0-9.-]', '', regex=True)
                serie = serie.replace('', '0')
                df[col] = pd.to_numeric(serie, errors='coerce').fillna(0).clip(lower=0).astype(int)
            else:
                df[col] = 0
        return df
    except Exception as e:
        st.error(f"❌ Error ventas diarias: {e}")
        return pd.DataFrame()

# ── CARGA ESPAÑA MAYO ──────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_españa():
    try:
        url = sheet_url("España mayo 2026")
        raw = pd.read_csv(url, header=None)
        sedes = ['ALICANTE','BARCELONA','VALENCIA','MADRID','MALAGA','BILBAO']
        data_esp = []
        for i in range(len(raw)):
            val = str(raw.iloc[i, 0]).strip().upper().replace(' ','')
            for sede in sedes:
                if val == sede or val == sede.replace(' ',''):
                    fila = raw.iloc[i].dropna().tolist()
                    nums = []
                    for v in fila[1:]:
                        try:
                            n = float(str(v).replace(',','.'))
                            if n >= 0: nums.append(n)
                        except: pass
                    mid = len(nums)//2
                    ag = sum(nums[:4]) if len(nums) >= 4 else sum(nums[:mid])
                    re = sum(nums[4:8]) if len(nums) >= 8 else sum(nums[mid:mid+4])
                    data_esp.append({'Sede': sede.capitalize(), 'Agendados': ag, 'Realizados': re})
                    break
        if not data_esp:
            raise ValueError()
        df = pd.DataFrame(data_esp)
    except:
        df = pd.DataFrame([
            {'Sede':'Alicante','Agendados':10,'Realizados':7},
            {'Sede':'Barcelona','Agendados':13.5,'Realizados':12.5},
            {'Sede':'Valencia','Agendados':6,'Realizados':2},
            {'Sede':'Madrid','Agendados':5.5,'Realizados':4.5},
            {'Sede':'Malaga','Agendados':20.5,'Realizados':10.5},
            {'Sede':'Bilbao','Agendados':0,'Realizados':2.5},
        ])
    df['Agendados'] = pd.to_numeric(df['Agendados'], errors='coerce').fillna(0)
    df['Realizados'] = pd.to_numeric(df['Realizados'], errors='coerce').fillna(0)
    df['% Conversión'] = df.apply(lambda r: round(r['Realizados']/r['Agendados']*100,1) if r['Agendados']>0 else 0, axis=1)
    return df

# ── CARGA USA MAYO ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_usa():
    try:
        url = sheet_url("usa mayo 2026")
        raw = pd.read_csv(url, header=None)
        sedes = ['DALLAS','HOUSTON','NEW JERSY','ORLANDO','ANGELES']
        sedes_label = ['Dallas','Houston','New Jersey','Orlando','Los Angeles']
        data_usa = []
        for i in range(len(raw)):
            val = str(raw.iloc[i, 0]).strip().upper().replace(' ','')
            for j, sede in enumerate(sedes):
                if val == sede.replace(' ','') or sede.replace(' ','') in val:
                    fila = raw.iloc[i].dropna().tolist()
                    nums = []
                    for v in fila[1:]:
                        try:
                            n = float(str(v).replace(',','.'))
                            if 0 < n < 50: nums.append(n)
                        except: pass
                    ag = sum(nums[:4]) if len(nums) >= 4 else (sum(nums) if nums else 0)
                    re = sum(nums[4:8]) if len(nums) >= 8 else 0
                    data_usa.append({'Sede': sedes_label[j], 'Agendados': ag, 'Realizados': re})
                    break
        if not data_usa:
            raise ValueError()
        df = pd.DataFrame(data_usa)
    except:
        df = pd.DataFrame([
            {'Sede':'Dallas','Agendados':8.5,'Realizados':6.5},
            {'Sede':'Houston','Agendados':4,'Realizados':7.5},
            {'Sede':'New Jersey','Agendados':6.5,'Realizados':4.5},
            {'Sede':'Orlando','Agendados':3.5,'Realizados':4.5},
            {'Sede':'Los Angeles','Agendados':11.5,'Realizados':13.5},
        ])
    df['Agendados'] = pd.to_numeric(df['Agendados'], errors='coerce').fillna(0)
    df['Realizados'] = pd.to_numeric(df['Realizados'], errors='coerce').fillna(0)
    df['% Conversión'] = df.apply(lambda r: round(r['Realizados']/r['Agendados']*100,1) if r['Agendados']>0 else 0, axis=1)
    return df

# ── CARGA GLOBAL ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_global():
    df_esp = cargar_españa()
    df_usa = cargar_usa()
    df_esp['País'] = '🇪🇸 España'
    df_usa['País'] = '🇺🇸 USA'
    return pd.concat([df_esp, df_usa], ignore_index=True)

# ── HELPER DE CONTEO ───────────────────────────────────────────────────────────
def get_val(df, col):
    return int(df[col].sum()) if not df.empty and col in df.columns else 0

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
        st.cache_data.clear()
        st.rerun()
    st.caption("Se actualiza cada 60 seg")

# ══════════════════════════════════════════════════════════════════════════════
# APLICAR FILTROS AL DATAFRAME DE TRABAJO
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
# HEADER PRINCIPAL
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
# SECCIÓN DE RESUMEN FIJO DE CONTROL INTERNO
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

# ── Grid Metrics de USA ──
st.markdown('<div class="grupo-label-usa">🇺🇸 USA</div>', unsafe_allow_html=True)
u_cols = st.columns(7)
u_cols[0].metric("💬 WPP",         get_val(df_rfijo_usa,'Leads WPP'))
u_cols[1].metric("📸 IG",          get_val(df_rfijo_usa,'Leads IG'))
u_cols[2].metric("📝 Formulario",  get_val(df_rfijo_usa,'Leads Formulario'))
u_cols[3].metric("🌐 Landing",     get_val(df_rfijo_usa,'Leads Landing'))
u_cols[4].metric("🎵 TikTok",      get_val(df_rfijo_usa,'Leads TikTok'))
u_cols[5].metric("⭐ Valoraciones",get_val(df_rfijo_usa,'Valoraciones'))
u_cols[6].metric("💰 Depósitos",   get_val(df_rfijo_usa,'Cierres'))

st.markdown("<br>", unsafe_allow_html=True)

# ── Grid Metrics de España ──
st.markdown('<div class="grupo-label-esp">🇪🇸 España</div>', unsafe_allow_html=True)
e_cols = st.columns(7)
e_cols[0].metric("💬 WPP",         get_val(df_rfijo_esp,'Leads WPP'))
e_cols[1].metric("📸 IG",          get_val(df_rfijo_esp,'Leads IG'))
e_cols[2].metric("📝 Formulario",  get_val(df_rfijo_esp,'Leads Formulario'))
e_cols[3].metric("🌐 Landing",     get_val(df_rfijo_esp,'Leads Landing'))
e_cols[4].metric("🎵 TikTok",      get_val(df_rfijo_esp,'Leads TikTok'))
e_cols[5].metric("⭐ Valoraciones",get_val(df_rfijo_esp,'Valoraciones'))
e_cols[6].metric("💰 Depósitos",   get_val(df_rfijo_esp,'Cierres'))

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# NACHOS Y PESTAÑAS (TABS)
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Ventas Diarias","🎯 Metas","🇪🇸 España Mayo","🇺🇸 USA Mayo","🌍 Global"])

# ══ TAB 1 — VENTAS DIARIAS (FILTRADO) ═════════════════════════════════════════
with tab1:
    partes = []
    if modo_fecha=="Día específico" and fecha_ini: partes.append(fecha_ini.strftime('%d/%m/%Y'))
    elif modo_fecha=="Rango de fechas" and fecha_ini: partes.append(f"{fecha_ini.strftime('%d/%m')}→{fecha_fin.strftime('%d/%m')}")
    elif modo_fecha=="Semana": partes.append(f"Semana {semana_sel}")
    if dia_sel!="Todos": partes.append(dia_sel)
    if grupo_sel!="Todos": partes.append(grupo_sel)
    if responsable_sel!="Todos": partes.append(responsable_sel)
    desc = " · ".join(partes) if partes else "Todos los registros"
    st.markdown(f"### 📊 {desc}")

    if df_filtrado.empty:
        st.warning("⚠️ Sin registros para estos filtros.")
    else:
        cols_vis = ['Fecha','Dia_Semana','Responsable','Grupo_Pais',
                    'Leads WPP','Leads IG','Leads Formulario','Leads Landing','Leads TikTok',
                    'Valoraciones','Venta Dia Siguiente','Cierres']
        cols_ok  = [c for c in cols_vis if c in df_filtrado.columns]
        df_show  = df_filtrado[cols_ok].copy()
        if 'Fecha' in df_show.columns:
            df_show = df_show.sort_values('Fecha', ascending=True)
            df_show['Fecha'] = df_show['Fecha'].dt.strftime('%d/%m/%Y')
        df_show = df_show.rename(columns={
            'Venta Dia Siguiente':'Presupuestado', 'Cierres':'Depósitos',
            'Dia_Semana':'Día', 'Grupo_Pais':'Grupo'
        })
        
        # Evitamos rellenar strings en la fila de totales numéricos
        totales = {c: df_show[c].sum() if c in df_show.columns and c not in ['Fecha','Día','Responsable','Grupo'] else '' for c in df_show.columns}
        totales['Fecha'] = '📊 TOTAL'
        df_final = pd.concat([df_show, pd.DataFrame([totales])], ignore_index=True)
        
        st.markdown("#### 📋 Registros por Fecha")
        st.dataframe(df_final, use_container_width=True, hide_index=True)
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Descargar CSV", data=csv, file_name=f"ventas_{date.today()}.csv", mime="text/csv")

        st.markdown("---")
        st.markdown("### 🔻 Embudos de Ventas")

        def render_embudo_horizontal(titulo, etapas_vals, color_borde):
            st.markdown(f'<div style="color:{color_borde};font-size:0.8rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px">{titulo}</div>', unsafe_allow_html=True)
            items_html = ""
            for etapa, val in etapas_vals:
                color_val = color_borde if str(val) != "—" and str(val) != "0" else "#555566"
                items_html += f"""
                <div style="display:inline-flex;flex-direction:column;align-items:center;justify-content:center;
                            background:linear-gradient(135deg,#0d0d0d,#1a1500);border:1px solid {color_borde};
                            border-radius:14px;padding:22px 20px;min-width:150px;min-height:110px;
                            text-align:center;vertical-align:top;margin: 5px;
                            box-shadow:0 4px 15px rgba(0,0,0,0.3)">
                    <div style="color:#888888;font-size:0.68rem;text-transform:uppercase;letter-spacing:1px;font-weight:600;margin-bottom:6px">{etapa}</div>
                    <div style="color:{color_val};font-size:1.7rem;font-weight:800">{val}</div>
                </div>"""
            st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:10px;margin-bottom:25px">{items_html}</div>', unsafe_allow_html=True)

        tot_wpp  = get_val(df_filtrado, 'Leads WPP')
        tot_ig   = get_val(df_filtrado, 'Leads IG')
        tot_form = get_val(df_filtrado, 'Leads Formulario')
        tot_land = get_val(df_filtrado, 'Leads Landing')
        tot_tik  = get_val(df_filtrado, 'Leads TikTok')
        tot_val  = get_val(df_filtrado, 'Valoraciones')
        tot_cie  = get_val(df_filtrado, 'Cierres')
        tot_leads= tot_wpp + tot_ig + tot_form + tot_land + tot_tik

        etapas_general = [
            ("Total Leads", tot_leads),
            ("Valoraciones", tot_val),
            ("Depósitos (Cierres)", tot_cie)
        ]
        render_embudo_horizontal("🔲 Proceso Comercial Consolidado", etapas_general, "#c9a84c")

# ══ TAB 2 — METAS Y AVANCES ═══════════════════════════════════════════════════
with tab2:
    st.markdown("### 🎯 Control de Objetivos")
    cierres_totales = get_val(df_filtrado, 'Cierres')
    
    def render_gauge(actual, meta, titulo):
        pct = min(round((actual / meta) * 100, 1), 100.0) if meta > 0 else 0.0
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = actual,
            title = {'text': f"{titulo}<br><span style='font-size:0.8em;color:gray'>Meta: {meta}</span>", 'font': {'size': 14}},
            gauge = {
                'axis': {'range': [0, max(meta, actual*1.2 if actual > 0 else 10)]},
                'bar': {'color': "#c9a84c"},
                'steps': [{'range': [0, meta], 'color': "#222211"}],
                'threshold': {'line': {'color': "gold", 'width': 4}, 'thickness': 0.75, 'value': meta}
            }
        ))
        fig.update_layout(PLOT_CFG, height=220, margin=dict(t=40, b=10, l=30, r=30))
        return fig

    m1, m2, m3 = st.columns(3)
    with m1: st.plotly_chart(render_gauge(cierres_totales, META_DIARIA, "Meta Diaria"), use_container_width=True)
    with m2: st.plotly_chart(render_gauge(cierres_totales, META_SEMANAL, "Meta Semanal"), use_container_width=True)
    with m3: st.plotly_chart(render_gauge(cierres_totales, META_MENSUAL, "Meta Mensual"), use_container_width=True)

# ══ TAB 3 — ESPAÑA MAYO ═══════════════════════════════════════════════════════
with tab3:
    st.markdown("### 🇪🇸 Análisis Territorial — España Mayo 2026")
    df_esp_m = cargar_españa()
    if df_esp_m.empty:
        st.info("No hay datos cargados para España.")
    else:
        c1, c2 = st.columns([3, 2])
        with c1:
            st.dataframe(df_esp_m, use_container_width=True, hide_index=True)
        with c2:
            fig_esp = px.bar(df_esp_m, x='Sede', y=['Agendados', 'Realizados'],
                             barmode='group', title="Agendados vs Realizados por Sede",
                             color_discrete_sequence=['#c9a84c', '#ffffff'])
            fig_esp.update_layout(PLOT_CFG, height=300)
            st.plotly_chart(fig_esp, use_container_width=True)

# ══ TAB 4 — USA MAYO ══════════════════════════════════════════════════════════
with tab4:
    st.markdown("### 🇺🇸 Análisis Territorial — USA Mayo 2026")
    df_usa_m = cargar_usa()
    if df_usa_m.empty:
        st.info("No hay datos cargados para USA.")
    else:
        c1, c2 = st.columns([3, 2])
        with c1:
            st.dataframe(df_usa_m, use_container_width=True, hide_index=True)
        with c2:
            fig_usa = px.bar(df_usa_m, x='Sede', y=['Agendados', 'Realizados'],
                             barmode='group', title="Agendados vs Realizados por Sede",
                             color_discrete_sequence=['#7c6af7', '#ffffff'])
            fig_usa.update_layout(PLOT_CFG, height=300)
            st.plotly_chart(fig_usa, use_container_width=True)

# ══ TAB 5 — GLOBAL COMPRENSIVO ════════════════════════════════════════════════
with tab5:
    st.markdown("### 🌍 Comparativa Consolidada Internacional")
    df_glob = cargar_global()
    if df_glob.empty:
        st.info("No hay datos globales consolidados disponibles.")
    else:
        g1, g2 = st.columns(2)
        with g1:
            df_g_pais = df_glob.groupby('País')[['Agendados','Realizados']].sum().reset_index()
            fig_g1 = px.bar(df_g_pais, x='País', y=['Agendados','Realizados'],
                            barmode='group', title="Volumen General por Mercado",
                            color_discrete_sequence=['#c9a84c', '#ffffff'])
            fig_g1.update_layout(PLOT_CFG)
            st.plotly_chart(fig_g1, use_container_width=True)
        with g2:
            fig_g2 = px.pie(df_glob, values='Realizados', names='Sede', hole=0.4,
                            title="Distribución Operativa Global (Citas Realizadas)",
                            color_discrete_sequence=px.colors.sequential.YlOrBr)
            fig_g2.update_layout(PLOT_CFG)
            st.plotly_chart(fig_g2, use_container_width=True)