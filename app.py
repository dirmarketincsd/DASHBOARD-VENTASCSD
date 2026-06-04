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
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #0a0a00, #111100) !important; border-right: 1px solid #c9a84c !important; }
hr { border-color: #c9a84c !important; opacity: 0.3; }
</style>
""", unsafe_allow_html=True)

SHEET_ID = "1-KjGMIPUGcMynGfTYM7P68E_k0ylcZYeg0Wmgwd-36Q"
PLOT_CFG = dict(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
EQUIPOS_BASE  = {'CAROLINA': 'USA', 'DANIELA': 'España', 'EVELYN': 'España'}
META_DIARIA   = 4
META_SEMANAL  = 40
META_MENSUAL  = 100

def sheet_url(nombre):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre.replace(' ','%20')}"

# ── CARGA VENTAS DIARIAS ───────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def cargar_ventas_diarias():
    try:
        url = sheet_url("Ventas diarias")
        raw = pd.read_csv(url, header=None)
        header_idx = 0
        for i in range(min(15, len(raw))):
            vals = raw.iloc[i].map(str).str.upper().str.strip().values
            if any('RESPONSABLE' in v or 'VALORACIONES' in v for v in vals):
                header_idx = i
                break
        df = pd.read_csv(url, skiprows=header_idx)
        df.columns = [str(c).strip().upper().replace('  ',' ') for c in df.columns]
        rename = {
            'FECHA':'Fecha','DIA':'Dia_Texto','SEMANA':'Semana',
            'RESPONSABLE':'Responsable','VALORACIONES':'Valoraciones',
            'LEADS WPP':'Leads WPP','LEADS IG':'Leads IG','SEDE':'Sede',
            'DEPOSITOS':'Cierres',
            'PRESUPUESTADO':'Venta Dia Siguiente',
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
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
            df = df[df['Fecha'].notna()]
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
        for col in ['Valoraciones','Leads WPP','Leads IG','Cierres','Venta Dia Siguiente']:
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
        if not data_esp: raise Exception()
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
        if not data_usa: raise Exception()
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

# ── CARGA TAREAS KOMMO ────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def cargar_tareas():
    try:
        url = sheet_url("TAREAS KOMMO")
        raw = pd.read_csv(url, header=None)
        header_idx = 0
        for i in range(min(10, len(raw))):
            vals = raw.iloc[i].map(str).str.upper().str.strip().values
            if any('RESPONSABLE' in v or 'TIPO' in v for v in vals):
                header_idx = i
                break
        df = pd.read_csv(url, skiprows=header_idx)
        df.columns = [str(c).strip().upper() for c in df.columns]
        rename = {'RESPONSABLE':'Responsable','TIPO':'Tipo','CANTIDAD':'Cantidad','FECHA':'Fecha'}
        df = df.rename(columns=rename)
        if 'Responsable' in df.columns:
            df = df[df['Responsable'].notna()]
            df['Responsable'] = df['Responsable'].astype(str).str.strip().str.upper()
            df = df[~df['Responsable'].isin(['','NAN','RESPONSABLE','TOTAL'])]
        if 'Cantidad' in df.columns:
            df['Cantidad'] = pd.to_numeric(df['Cantidad'].astype(str).str.replace('[^0-9]','',regex=True), errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        return pd.DataFrame()

# ── CARGA SECCIONES SECUNDARIAS (VENTAS CERRADAS Y AGENDA PENDIENTE) ───────────
@st.cache_data(ttl=60)
def cargar_ventas_cerradas():
    try:
        url = sheet_url("Ventas diarias")
        raw = pd.read_csv(url, header=None)
        data_usa, data_esp = [], []
        header_row, usa_col, esp_col = None, None, None
        for i in range(min(10, len(raw))):
            for j in range(len(raw.columns)):
                val = str(raw.iloc[i,j]).strip().upper()
                if 'VENTA CERRADA' in val and 'USA' in val:
                    usa_col = j
                    header_row = i + 1
                if 'VENTA CERRADA' in val and 'ESPA' in val:
                    esp_col = j
        if header_row is None: return pd.DataFrame(), pd.DataFrame()
        
        if usa_col is not None:
            for i in range(header_row+1, len(raw)):
                row = raw.iloc[i]
                resp = str(row.iloc[usa_col]).strip()
                if resp and resp not in ['nan','','RESPONSABLE']:
                    try: total = float(str(row.iloc[usa_col+4]).strip())
                    except: total = 0
                    data_usa.append({'Responsable':resp,'Tipo de Diseño':str(row.iloc[usa_col+1]).strip(),'Vendido En':str(row.iloc[usa_col+2]).strip(),'Sede':str(row.iloc[usa_col+3]).strip(),'Total':total})
        if esp_col is not None:
            for i in range(header_row+1, len(raw)):
                row = raw.iloc[i]
                resp = str(row.iloc[esp_col]).strip()
                if resp and resp not in ['nan','','RESPONSABLE']:
                    try: total = float(str(row.iloc[esp_col+4]).strip())
                    except: total = 0
                    data_esp.append({'Responsable':resp,'Tipo de Diseño':str(row.iloc[esp_col+1]).strip(),'Vendido En':str(row.iloc[esp_col+2]).strip(),'Sede':str(row.iloc[esp_col+3]).strip(),'Total':total})
        return pd.DataFrame(data_usa), pd.DataFrame(data_esp)
    except:
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=60)
def cargar_agenda_pendiente():
    try:
        url = sheet_url("Ventas diarias")
        raw = pd.read_csv(url, header=None)
        data_usa, data_esp = [], []
        for i in range(min(50, len(raw))):
            for j in range(len(raw.columns)):
                val = str(raw.iloc[i,j]).strip().upper()
                if 'AGENDA PENDIENTE' in val and 'USA' in val:
                    header_row = i + 1
                    for k in range(header_row+1, len(raw)):
                        row = raw.iloc[k]
                        resp = str(row.iloc[j]).strip()
                        if resp and resp not in ['nan','','RESPONSABLE']:
                            data_usa.append({'Responsable':resp,'Depósito':str(row.iloc[j+1]).strip(),'Fecha Pendiente':str(row.iloc[j+2]).strip(),'Tipo de Diseño':str(row.iloc[j+3]).strip()})
                if 'AGENDA PENDIENTE' in val and 'ESPA' in val:
                    header_row = i + 1
                    for k in range(header_row+1, len(raw)):
                        row = raw.iloc[k]
                        resp = str(row.iloc[j]).strip()
                        if resp and resp not in ['nan','','RESPONSABLE']:
                            data_esp.append({'Responsable':resp,'Depósito':str(row.iloc[j+1]).strip(),'Fecha Pendiente':str(row.iloc[j+2]).strip(),'Tipo de Diseño':str(row.iloc[j+3]).strip()})
        return pd.DataFrame(data_usa), pd.DataFrame(data_esp)
    except:
        return pd.DataFrame(), pd.DataFrame()

df_base = cargar_ventas_diarias()

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    if logo_b64:
        st.markdown(f'<div style="text-align:center;padding:16px 0 8px 0"><img src="data:image/png;base64,{logo_b64}" style="width:180px;border-radius:8px"></div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#c9a84c;font-size:0.7rem;text-transform:uppercase;letter-spacing:2px;text-align:center;margin-bottom:10px;font-weight:700">Panel de Control</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🔍 Filtros")

    modo_fecha = st.radio("📅 Filtrar por", ["Día específico","Rango de fechas","Semana","Todos"])
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
            sems += sorted(df_base['Semana'].dropna().unique().tolist(), key=lambda x: int(x) if str(x).isdigit() else 0)
        semana_sel = st.selectbox("📆 Semana", sems)

    dia_sel       = st.selectbox("📅 Día de la semana", ["Todos","Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"])
    grupo_sel     = st.selectbox("🌍 Grupo / País", ["Todos","USA","España"])

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

# ── APLICAR FILTROS ────────────────────────────────────────────────────────────
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

# ── HEADER ─────────────────────────────────────────────────────────────────────
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

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Ventas Diarias","🎯 Metas","🇪🇸 España Mayo","🇺🇸 USA Mayo","🌍 Global"])

# ══ TAB 1 — VENTAS DIARIAS ════════════════════════════════════════════════════
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
        # ── KPIs Grupo USA ──
        df_usa_f = df_filtrado[df_filtrado['Grupo_Pais']=='USA'] if 'Grupo_Pais' in df_filtrado.columns else pd.DataFrame()
        st.markdown('<div style="color:#7c6af7;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin-bottom:6px">🇺🇸 Grupo USA</div>', unsafe_allow_html=True)
        u1,u2,u3,u4,u5 = st.columns(5)
        u1.metric("💬 Leads WPP",     int(df_usa_f['Leads WPP'].sum()) if not df_usa_f.empty else 0)
        u2.metric("📸 Leads IG",      int(df_usa_f['Leads IG'].sum()) if not df_usa_f.empty else 0)
        u3.metric("⭐ Valoraciones",   int(df_usa_f['Valoraciones'].sum()) if not df_usa_f.empty else 0)
        u4.metric("📅 Presupuestado", int(df_usa_f['Venta Dia Siguiente'].sum()) if not df_usa_f.empty else 0)
        u5.metric("💰 Depósitos",     int(df_usa_f['Cierres'].sum()) if not df_usa_f.empty else 0)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── KPIs Grupo España ──
        df_esp_f = df_filtrado[df_filtrado['Grupo_Pais']=='España'] if 'Grupo_Pais' in df_filtrado.columns else pd.DataFrame()
        st.markdown('<div style="color:#00d4aa;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin-bottom:6px">🇪🇸 Grupo España</div>', unsafe_allow_html=True)
        e1,e2,e3,e4,e5 = st.columns(5)
        e1.metric("💬 Leads WPP",     int(df_esp_f['Leads WPP'].sum()) if not df_esp_f.empty else 0)
        e2.metric("📸 Leads IG",      int(df_esp_f['Leads IG'].sum()) if not df_esp_f.empty else 0)
        e3.metric("⭐ Valoraciones",   int(df_esp_f['Valoraciones'].sum()) if not df_esp_f.empty else 0)
        e4.metric("📅 Presupuestado", int(df_esp_f['Venta Dia Siguiente'].sum()) if not df_esp_f.empty else 0)
        e5.metric("💰 Depósitos",     int(df_esp_f['Cierres'].sum()) if not df_esp_f.empty else 0)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Tabla ordenada por fecha ──
        cols_vis = ['Fecha','Dia_Semana','Semana','Responsable','Grupo_Pais',
                    'Leads WPP','Leads IG','Valoraciones','Venta Dia Siguiente','Cierres']
        cols_ok = [c for c in cols_vis if c in df_filtrado.columns]
        df_show = df_filtrado[cols_ok].copy()

        if 'Fecha' in df_show.columns:
            df_show = df_show.sort_values('Fecha', ascending=True)
            df_show['Fecha'] = df_show['Fecha'].dt.strftime('%d/%m/%Y')

        df_show = df_show.rename(columns={
            'Venta Dia Siguiente':'Presupuestado',
            'Cierres':'Depósitos',
            'Dia_Semana':'Día',
            'Grupo_Pais':'Grupo'
        })

        cols_num = ['Leads WPP','Leads IG','Valoraciones','Presupuestado','Depósitos']
        totales = {c: df_show[c].sum() if c in df_show.columns else '' for c in df_show.columns}
        totales['Fecha'] = '📊 TOTAL'
        totales['Día'] = ''
        totales['Semana'] = ''
        totales['Responsable'] = ''
        totales['Grupo'] = ''
        df_totales = pd.DataFrame([totales])
        df_final = pd.concat([df_show, df_totales], ignore_index=True)

        st.markdown("#### 📋 Registros por Fecha")
        st.dataframe(df_final, use_container_width=True, hide_index=True)
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Descargar CSV", data=csv, file_name=f"ventas_{date.today()}.csv", mime="text/csv")
        st.markdown("---")

        st.markdown("### 🔻 Embudos de Ventas")

        def render_embudo_horizontal(titulo, etapas_vals, color_borde):
            st.markdown(f'<div style="color:{color_borde};font-size:0.8rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px">{titulo}</div>', unsafe_allow_html=True)
            items_html = ""
            for i, (etapa, val) in enumerate(etapas_vals):
                color_val = color_borde if str(val) != "—" and str(val) != "0" else "#555566"
                items_html += f"""
                <div style="display:inline-flex;flex-direction:column;align-items:center;justify-content:center;
                            background:linear-gradient(135deg,#0d0d0d,#1a1500);border:1px solid {color_borde};
                            border-radius:14px;padding:22px 20px;min-width:150px;min-height:110px;
                            text-align:center;vertical-align:top;
                            box-shadow:0 4px 15px rgba(0,0,0,0.3)">
                    <div style="color:#8b9bb4;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.8px;
                                margin-bottom:12px;white-space:nowrap">{etapa}</div>
                    <div style="color:{color_val};font-size:2.4rem;font-weight:800;line-height:1">{val}</div>
                </div>"""
                if i < len(etapas_vals) - 1:
                    items_html += f"""
                <div style="display:inline-flex;align-items:center;justify-content:center;
                            padding:0 6px;vertical-align:top;margin-top:30px">
                    <span style="color:{color_borde};font-size:1.5rem;font-weight:300">→</span>
                </div>"""
            st.markdown(f'<div style="overflow-x:auto;white-space:nowrap;padding-bottom:8px">{items_html}</div>', unsafe_allow_html=True)

        df_esp_emb = df_filtrado[df_filtrado['Grupo_Pais']=='España'] if 'Grupo_Pais' in df_filtrado.columns else pd.DataFrame()
        df_usa_emb = df_filtrado[df_filtrado['Grupo_Pais']=='USA']    if 'Grupo_Pais' in df_filtrado.columns else pd.DataFrame()

        leads_esp = int(df_esp_emb['Leads WPP'].sum() + df_esp_emb['Leads IG'].sum()) if not df_esp_emb.empty else 0
        val_esp   = int(df_esp_emb['Valoraciones'].sum())       if not df_esp_emb.empty else 0
        pres_esp  = int(df_esp_emb['Venta Dia Siguiente'].sum()) if not df_esp_emb.empty else 0
        dep_esp   = int(df_esp_emb['Cierres'].sum())            if not df_esp_emb.empty else 0

        leads_usa = int(df_usa_emb['Leads WPP'].sum() + df_usa_emb['Leads IG'].sum()) if not df_usa_emb.empty else 0
        val_usa   = int(df_usa_emb['Valoraciones'].sum())       if not df_usa_emb.empty else 0
        pres_usa  = int(df_usa_emb['Venta Dia Siguiente'].sum()) if not df_usa_emb.empty else 0
        dep_usa   = int(df_usa_emb['Cierres'].sum())            if not df_usa_emb.empty else 0

        etapas_esp = [
            ("📥 Leads", leads_esp), ("📞 Contactado", "—"), ("🔇 No Contestó", "—"),
            ("⭐ Valoración", val_esp), ("💵 Presupuesto", pres_esp), ("💳 Financiamiento", "—"),
            ("🏥 Val. Presencial", "—"), ("📅 Ag. Depósito", dep_esp), ("✅ Venta Cerrada", "—"),
        ]

        etapas_usa = [
            ("📥 Leads", leads_usa), ("📞 Contactado", "—"), ("🔇 No Contesta", "—"),
            ("💻 Val. Virtual", val_usa), ("💵 Presupuesto", pres_usa), ("🏥 Ag. Presencial", "—"),
            ("📅 Ag. Depósito", dep_usa),
        ]

        render_embudo_horizontal("🇪🇸 Embudo España", etapas_esp, "#00d4aa")
        st.markdown("<br>", unsafe_allow_html=True)
        render_embudo_horizontal("🇺🇸 Embudo USA", etapas_usa, "#7c6af7")

        st.markdown("---")

        # ── TAREAS PARA HOY (Bloque Completado y Cerrado Correctamente) ──
        st.markdown("### 📋 Tareas para Hoy")
        df_tareas = cargar_tareas()
        
        if df_tareas.empty:
            st.info("ℹ️ No hay tareas pendientes registradas para hoy en Kommo CRM.")
        else:
            t_col1, t_col2 = st.columns(2)
            TIPOS_TAREA = ['VALORACIÓN VIRTUAL', 'SEGUIMIENTO']
            ASESORES = ['DANIELA', 'EVELYN', 'CAROLINA']

            for asesor in ASESORES:
                df_a = df_tareas[df_tareas['Responsable'] == asesor] if 'Responsable' in df_tareas.columns else pd.DataFrame()
                grupo = EQUIPOS_BASE.get(asesor, 'Por Clasificar')
                color = "#00d4aa" if grupo == 'España' else "#7c6af7"

                with (t_col1 if grupo == 'España' else t_col2):
                    st.markdown(f"""
                    <div style="background:linear-gradient(135deg,#0d0d0d,#1a1500);border:1px solid {color};
                                border-radius:12px;padding:14px 18px;margin-bottom:12px">
                        <div style="color:{color};font-weight:800;font-size:1.05rem;margin-bottom:8px;letter-spacing:0.5px">👤 {asesor}</div>
                    """, unsafe_allow_html=True)
                    
                    tc1, tc2 = st.columns(2)
                    for idx, tipo in enumerate(TIPOS_TAREA):
                        # Filtrar cantidad de subtareas por tipo
                        cant = 0
                        if not df_a.empty and 'Tipo' in df_a.columns:
                            df_t = df_a[df_a['Tipo'].str.upper().str.strip() == tipo]
                            cant = int(df_t['Cantidad'].sum()) if not df_t.empty else 0
                        
                        with (tc1 if idx == 0 else tc2):
                            st.markdown(f"""
                            <div style="padding:4px 0">
                                <span style="color:#8b9bb4;font-size:0.78rem;text-transform:uppercase">{tipo.title()}</span><br>
                                <span style="color:#ffffff;font-size:1.5rem;font-weight:700">{cant}</span>
                            </div>
                            """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

# ══ TAB 2 — METAS ═════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 🎯 Cumplimiento de Metas")
    if df_filtrado.empty:
        st.warning("⚠️ Sin datos para calcular metas.")
    else:
        cierres_totales = int(df_filtrado['Cierres'].sum())
        
        m1, m2, m3 = st.columns(3)
        with m1:
            pct_d = min(round((cierres_totales / META_DIARIA) * 100, 1), 100.0) if META_DIARIA > 0 else 0
            st.metric("Meta Diaria (4)", f"{cierres_totales} Cierres", f"{pct_d}% Logrado")
            st.progress(pct_d / 100)
        with m2:
            pct_s = min(round((cierres_totales / META_SEMANAL) * 100, 1), 100.0) if META_SEMANAL > 0 else 0
            st.metric("Meta Semanal (40)", f"{cierres_totales} Cierres", f"{pct_s}% Logrado")
            st.progress(pct_s / 100)
        with m3:
            pct_m = min(round((cierres_totales / META_MENSUAL) * 100, 1), 100.0) if META_MENSUAL > 0 else 0
            st.metric("Meta Mensual (100)", f"{cierres_totales} Cierres", f"{pct_m}% Logrado")
            st.progress(pct_m / 100)

# ══ TAB 3 — ESPAÑA MAYO ═══════════════════════════════════════════════════════
with tab3:
    st.markdown("### 🇪🇸 Desempeño Clínicas España — Mayo 2026")
    df_esp_m = cargar_españa()
    st.dataframe(df_esp_m, use_container_width=True, hide_index=True)
    
    fig_esp = px.bar(df_esp_m, x='Sede', y=['Agendados', 'Realizados'], barmode='group',
                     title="Agendados vs Realizados por Sede (España)",
                     color_discrete_map={'Agendados': '#2a2000', 'Realizados': '#00d4aa'})
    fig_esp.update_layout(**PLOT_CFG)
    st.plotly_chart(fig_esp, use_container_width=True)

# ══ TAB 4 — USA MAYO ══════════════════════════════════════════════════════════
with tab4:
    st.markdown("### 🇺🇸 Desempeño Clínicas USA — Mayo 2026")
    df_usa_m = cargar_usa()
    st.dataframe(df_usa_m, use_container_width=True, hide_index=True)
    
    fig_usa = px.bar(df_usa_m, x='Sede', y=['Agendados', 'Realizados'], barmode='group',
                     title="Agendados vs Realizados por Sede (USA)",
                     color_discrete_map={'Agendados': '#2a2000', 'Realizados': '#7c6af7'})
    fig_usa.update_layout(**PLOT_CFG)
    st.plotly_chart(fig_usa, use_container_width=True)

# ══ TAB 5 — GLOBAL ════════════════════════════════════════════════════════════
with tab5:
    st.markdown("### 🌍 Comparativo Global e Histórico")
    df_glob = cargar_global()
    
    g1, g2 = st.columns(2)
    with g1:
        fig_g1 = px.sunburst(df_glob, path=['País', 'Sede'], values='Realizados',
                             title="Distribución de Valoraciones Realizadas",
                             color_discrete_sequence=['#00d4aa', '#7c6af7'])
        fig_g1.update_layout(**PLOT_CFG)
        st.plotly_chart(fig_g1, use_container_width=True)
    with g2:
        df_ventas_usa, df_ventas_esp = cargar_ventas_cerradas()
        st.markdown("#### 💰 Últimas Ventas Cerradas (USA)")
        if not df_ventas_usa.empty:
            st.dataframe(df_ventas_usa.head(10), use_container_width=True, hide_index=True)
        else:
            st.caption("No se detectan cierres detallados en las columnas M+ de USA.")