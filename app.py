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
            # Nombres nuevos en el sheet
            'DEPOSITOS':'Cierres',
            'PRESUPUESTADO':'Venta Dia Siguiente',
            # Nombres antiguos (compatibilidad)
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
                # Limpiar: reemplazar N/A, nan, vacíos con 0
                serie = df[col].astype(str).str.strip()
                serie = serie.replace({'N/A':'0','n/a':'0','NA':'0','nan':'0','None':'0','':'0'}, regex=False)
                serie = serie.str.replace('[^0-9.-]', '', regex=True)  # solo números
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
        # Buscar fila con sedes (alicante, barcelona, etc.)
        sedes = ['ALICANTE','BARCELONA','VALENCIA','MADRID','MALAGA','BILBAO']
        # Extraer totales de REALIZADOS por sede (columna TOTAL al final)
        # La estructura: fila con nombre sede, columnas de semanas y total
        # Buscamos las filas de sedes en la sección REALIZADOS
        data_esp = []
        for i in range(len(raw)):
            val = str(raw.iloc[i, 0]).strip().upper().replace(' ','')
            for sede in sedes:
                if val == sede or val == sede.replace(' ',''):
                    fila = raw.iloc[i].dropna().tolist()
                    # El último valor numérico relevante es el total realizados
                    nums = []
                    for v in fila[1:]:
                        try:
                            n = float(str(v).replace(',','.'))
                            if n >= 0: nums.append(n)
                        except: pass
                    # Agendados: primeros valores, Realizados: después de la mitad
                    mid = len(nums)//2
                    ag = sum(nums[:4]) if len(nums) >= 4 else sum(nums[:mid])
                    re = sum(nums[4:8]) if len(nums) >= 8 else sum(nums[mid:mid+4])
                    data_esp.append({'Sede': sede.capitalize(), 'Agendados': ag, 'Realizados': re})
                    break
        if not data_esp:
            data_esp = [
                {'Sede':'Alicante','Agendados':10,'Realizados':7},
                {'Sede':'Barcelona','Agendados':13.5,'Realizados':12.5},
                {'Sede':'Valencia','Agendados':6,'Realizados':2},
                {'Sede':'Madrid','Agendados':5.5,'Realizados':4.5},
                {'Sede':'Malaga','Agendados':20.5,'Realizados':10.5},
                {'Sede':'Bilbao','Agendados':0,'Realizados':2.5},
            ]
        df = pd.DataFrame(data_esp)
        df['Agendados'] = pd.to_numeric(df['Agendados'], errors='coerce').fillna(0)
        df['Realizados'] = pd.to_numeric(df['Realizados'], errors='coerce').fillna(0)
        df['% Conversión'] = df.apply(lambda r: round(r['Realizados']/r['Agendados']*100,1) if r['Agendados']>0 else 0, axis=1)
        return df
    except:
        df = pd.DataFrame([
            {'Sede':'Alicante','Agendados':10,'Realizados':7},
            {'Sede':'Barcelona','Agendados':13.5,'Realizados':12.5},
            {'Sede':'Valencia','Agendados':6,'Realizados':2},
            {'Sede':'Madrid','Agendados':5.5,'Realizados':4.5},
            {'Sede':'Malaga','Agendados':20.5,'Realizados':10.5},
            {'Sede':'Bilbao','Agendados':0,'Realizados':2.5},
        ])
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
            data_usa = [
                {'Sede':'Dallas','Agendados':8.5,'Realizados':6.5},
                {'Sede':'Houston','Agendados':4,'Realizados':7.5},
                {'Sede':'New Jersey','Agendados':6.5,'Realizados':4.5},
                {'Sede':'Orlando','Agendados':3.5,'Realizados':4.5},
                {'Sede':'Los Angeles','Agendados':11.5,'Realizados':13.5},
            ]
        df = pd.DataFrame(data_usa)
        df['Agendados'] = pd.to_numeric(df['Agendados'], errors='coerce').fillna(0)
        df['Realizados'] = pd.to_numeric(df['Realizados'], errors='coerce').fillna(0)
        df['% Conversión'] = df.apply(lambda r: round(r['Realizados']/r['Agendados']*100,1) if r['Agendados']>0 else 0, axis=1)
        return df
    except:
        df = pd.DataFrame([
            {'Sede':'Dallas','Agendados':8.5,'Realizados':6.5},
            {'Sede':'Houston','Agendados':4,'Realizados':7.5},
            {'Sede':'New Jersey','Agendados':6.5,'Realizados':4.5},
            {'Sede':'Orlando','Agendados':3.5,'Realizados':4.5},
            {'Sede':'Los Angeles','Agendados':11.5,'Realizados':13.5},
        ])
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

# Cargar datos
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
            sems += sorted(df_base['Semana'].dropna().unique().tolist(),
                           key=lambda x: int(x) if str(x).isdigit() else 0)
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
if not df_filtrado.empty:
    if modo_fecha == "Día específico" and fecha_ini is not None:
        df_filtrado = df_filtrado[df_filtrado['Fecha'].dt.date == fecha_ini.date()]
    elif modo_fecha == "Rango de fechas" and fecha_ini is not None:
        df_filtrado = df_filtrado[(df_filtrado['Fecha']>=fecha_ini)&(df_filtrado['Fecha']<=fecha_fin)]
    elif modo_fecha == "Semana" and semana_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Semana'].astype(str)==semana_sel]
    if dia_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Dia_Semana']==dia_sel]
    if grupo_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Grupo_Pais']==grupo_sel]
    if responsable_sel != "Todos":
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

        cols_vis = ['Fecha','Semana','Dia_Semana','Responsable','Grupo_Pais','Sede',
                    'Leads WPP','Leads IG','Valoraciones','Venta Dia Siguiente','Cierres']
        cols_ok = [c for c in cols_vis if c in df_filtrado.columns]
        df_show = df_filtrado[cols_ok].copy()
        if 'Fecha' in df_show.columns:
            df_show['Fecha'] = df_show['Fecha'].dt.strftime('%d/%m/%Y')
        if 'Venta Dia Siguiente' in df_show.columns:
            df_show = df_show.rename(columns={'Venta Dia Siguiente':'Presupuestado','Cierres':'Depósitos'})
        st.markdown("#### 📋 Registros")
        st.dataframe(df_show, use_container_width=True, hide_index=True)
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Descargar CSV", data=csv, file_name=f"ventas_{date.today()}.csv", mime="text/csv")
        st.markdown("---")

        # ══ EMBUDOS DE VENTAS ══════════════════════════════════════════════
        st.markdown("### 🔻 Embudos de Ventas")
        emb_col1, emb_col2 = st.columns(2)

        def render_embudo(titulo, etapas, valores, color_top, color_bot):
            st.markdown(f"""<div style="background:linear-gradient(135deg,#0d0d0d,#1a1500);
                border:1px solid {color_top};border-radius:14px;padding:16px 20px;margin-bottom:10px">
                <div style="color:{color_top};font-size:1rem;font-weight:800;margin-bottom:14px">{titulo}</div>
            </div>""", unsafe_allow_html=True)
            max_val = max(valores) if max(valores) > 0 else 1
            n = len(etapas)
            for i, (etapa, val) in enumerate(zip(etapas, valores)):
                pct_ancho = max(20, int(val / max_val * 100))
                # Color gradiente de arriba a abajo
                r1,g1,b1 = int(color_top[1:3],16), int(color_top[3:5],16), int(color_top[5:7],16)
                r2,g2,b2 = int(color_bot[1:3],16), int(color_bot[3:5],16), int(color_bot[5:7],16)
                t = i/(n-1) if n > 1 else 0
                r = int(r1 + (r2-r1)*t); g = int(g1 + (g2-g1)*t); b = int(b1 + (b2-b1)*t)
                color_actual = f"#{r:02x}{g:02x}{b:02x}"
                conv = f" · {round(val/valores[i-1]*100,1)}% conv." if i > 0 and valores[i-1] > 0 else ""
                st.markdown(f"""
                <div style="margin-bottom:6px">
                    <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                        <span style="color:#c9a84c;font-size:0.78rem;font-weight:600">{etapa}</span>
                        <span style="color:white;font-size:0.78rem;font-weight:700">{val}{conv}</span>
                    </div>
                    <div style="background:#1e2340;border-radius:6px;height:28px;width:100%;position:relative">
                        <div style="height:28px;border-radius:6px;background:{color_actual};
                                    width:{pct_ancho}%;display:flex;align-items:center;padding-left:8px">
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)

        # ── Datos embudo España (manual por ahora) ──
        etapas_esp = [
            "📥 Leads Entrantes",
            "📞 Contactado",
            "🔇 No Contestó",
            "⭐ Valoración",
            "💵 Presupuesto",
            "💳 Financiamiento",
            "🏥 Valoración Presencial",
            "📅 Agendado con Depósito",
            "✅ Venta Cerrada"
        ]
        # Tomar leads del df filtrado para España
        df_esp_emb = df_filtrado[df_filtrado['Grupo_Pais']=='España'] if 'Grupo_Pais' in df_filtrado.columns else pd.DataFrame()
        leads_esp = int(df_esp_emb['Leads WPP'].sum() + df_esp_emb['Leads IG'].sum()) if not df_esp_emb.empty else 0
        dep_esp   = int(df_esp_emb['Cierres'].sum()) if not df_esp_emb.empty else 0
        val_esp   = int(df_esp_emb['Valoraciones'].sum()) if not df_esp_emb.empty else 0
        pres_esp  = int(df_esp_emb['Venta Dia Siguiente'].sum()) if not df_esp_emb.empty else 0
        valores_esp = [
            leads_esp,
            max(0, int(leads_esp*0.7)),
            max(0, int(leads_esp*0.3)),
            val_esp,
            pres_esp,
            max(0, int(pres_esp*0.5)),
            max(0, int(pres_esp*0.4)),
            dep_esp,
            max(0, int(dep_esp*0.9))
        ]

        # ── Datos embudo USA ──
        etapas_usa = [
            "📥 Leads Entrantes",
            "📞 Contactado",
            "🔇 No Contesta",
            "💻 Valoración Virtual",
            "💵 Presupuesto",
            "🏥 Agendado Presencial",
            "📅 Agendado con Depósito"
        ]
        df_usa_emb = df_filtrado[df_filtrado['Grupo_Pais']=='USA'] if 'Grupo_Pais' in df_filtrado.columns else pd.DataFrame()
        leads_usa = int(df_usa_emb['Leads WPP'].sum() + df_usa_emb['Leads IG'].sum()) if not df_usa_emb.empty else 0
        dep_usa   = int(df_usa_emb['Cierres'].sum()) if not df_usa_emb.empty else 0
        val_usa   = int(df_usa_emb['Valoraciones'].sum()) if not df_usa_emb.empty else 0
        pres_usa  = int(df_usa_emb['Venta Dia Siguiente'].sum()) if not df_usa_emb.empty else 0
        valores_usa = [
            leads_usa,
            max(0, int(leads_usa*0.7)),
            max(0, int(leads_usa*0.3)),
            val_usa,
            pres_usa,
            max(0, int(pres_usa*0.5)),
            dep_usa
        ]

        with emb_col1:
            render_embudo("🇪🇸 Embudo España", etapas_esp, valores_esp, "#00d4aa", "#c9a84c")
        with emb_col2:
            render_embudo("🇺🇸 Embudo USA", etapas_usa, valores_usa, "#7c6af7", "#f7a76c")

# ══ TAB 2 — METAS ═══════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 🎯 Control de Metas")
    try:
        df_m = cargar_ventas_diarias()
        if df_m.empty:
            st.info("📝 Sin datos aún. Ingresa registros en la hoja 'Ventas diarias'.")
        else:
            hoy_ts     = pd.Timestamp(date.today())
            inicio_sem = hoy_ts - timedelta(days=hoy_ts.weekday())
            inicio_mes = hoy_ts.replace(day=1)

            def filtrar_periodo(df_src, grupo=None):
                d = df_src.copy()
                if grupo and 'Grupo_Pais' in d.columns:
                    d = d[d['Grupo_Pais'] == grupo]
                return d

            def get_cierres(df_src, desde=None, hasta=None):
                d = df_src.copy()
                if 'Fecha' in d.columns:
                    if desde is not None:
                        d = d[d['Fecha'].dt.date >= desde]
                    if hasta is not None:
                        d = d[d['Fecha'].dt.date <= hasta]
                if 'Cierres' not in d.columns or d.empty:
                    return 0
                return int(pd.to_numeric(d['Cierres'], errors='coerce').fillna(0).sum())

            # Asesores por grupo
            asesores_esp = [r for r in df_m['Responsable'].dropna().unique() if EQUIPOS_BASE.get(r,'') == 'España'] if 'Responsable' in df_m.columns else []
            asesores_usa = [r for r in df_m['Responsable'].dropna().unique() if EQUIPOS_BASE.get(r,'') == 'USA']    if 'Responsable' in df_m.columns else []
            n_esp = max(len(asesores_esp), 1)
            n_usa = max(len(asesores_usa), 1)

            df_esp_m = filtrar_periodo(df_m, 'España')
            df_usa_m = filtrar_periodo(df_m, 'USA')

            hoy_date = hoy_ts.date()

            def tarjeta_meta(titulo, actual, meta, emoji, color_borde='#c9a84c'):
                p = min(round(actual/meta*100, 1) if meta > 0 else 0, 100)
                color = "#00d4aa" if p >= 100 else "#f7a76c" if p >= 50 else "#ff6b6b"
                faltan = max(meta - actual, 0)
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#0d0d0d,#1a1500);border:1px solid {color_borde};
                            border-radius:14px;padding:14px 18px;margin-bottom:8px">
                    <div style="color:#8b9bb4;font-size:0.72rem;text-transform:uppercase;letter-spacing:1px">{emoji} {titulo}</div>
                    <div style="color:white;font-size:1.9rem;font-weight:800">{actual} <span style="color:#8b9bb4;font-size:0.95rem">/ {meta}</span></div>
                    <div style="color:{color};font-size:0.9rem;font-weight:600">{p}% completado</div>
                    <div style="background:#1e2340;border-radius:10px;height:10px;width:100%;margin:6px 0">
                        <div style="height:10px;border-radius:10px;background:{color};width:{p}%"></div>
                    </div>
                    <div style="color:#ff6b6b;font-size:0.8rem">Faltan: <b>{faltan}</b></div>
                </div>""", unsafe_allow_html=True)

            def barras_asesor(df_grupo, titulo, color_borde):
                st.markdown(f"#### 🏁 {titulo}")
                df_hoy_g = df_grupo[df_grupo['Fecha'].dt.date == hoy_date] if 'Fecha' in df_grupo.columns else pd.DataFrame()
                if not df_hoy_g.empty and 'Responsable' in df_hoy_g.columns:
                    df_r = df_hoy_g.groupby('Responsable')['Cierres'].sum().reset_index().sort_values('Cierres', ascending=False)
                    for _, row in df_r.iterrows():
                        p = min(round(row['Cierres']/META_DIARIA*100, 1), 100)
                        c = int(row['Cierres'])
                        nombre = row['Responsable']
                        faltan = max(META_DIARIA - c, 0)
                        color = "#00d4aa" if p >= 100 else "#f7a76c" if p >= 60 else "#ff6b6b"
                        estado = "✅ ¡Meta!" if p >= 100 else f"🔥 Faltan {faltan}" if p >= 60 else f"⚡ Faltan {faltan}"
                        st.markdown(f"""
                        <div style="background:linear-gradient(135deg,#0d0d0d,#1a1500);border:1px solid {color_borde};
                                    border-radius:12px;padding:12px 16px;margin-bottom:8px">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                                <div style="color:white;font-weight:700">👤 {nombre}</div>
                                <div style="color:{color};font-weight:600;font-size:0.85rem">{estado}</div>
                            </div>
                            <div style="display:flex;align-items:center;gap:10px">
                                <div style="flex:1;background:#1e2340;border-radius:8px;height:12px">
                                    <div style="height:12px;border-radius:8px;background:{color};width:{p}%"></div>
                                </div>
                                <div style="color:#c9a84c;font-size:0.82rem;font-weight:700;min-width:80px;text-align:right">
                                    {c} / {META_DIARIA} · {p}%
                                </div>
                            </div>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.info("Sin depósitos hoy.")

            # ── ESPAÑA ──────────────────────────────────────────────────────
            st.markdown("""<div style="background:linear-gradient(135deg,#0d0d0d,#1a1500);border:1px solid #00d4aa;
                border-radius:14px;padding:12px 20px;margin-bottom:12px">
                <span style="color:#00d4aa;font-size:1.1rem;font-weight:800">🇪🇸 GRUPO ESPAÑA</span>
                <span style="color:#8b9bb4;font-size:0.8rem;margin-left:12px">{} asesor(es): {}</span>
            </div>""".format(n_esp, ', '.join(asesores_esp) if asesores_esp else 'Sin datos'), unsafe_allow_html=True)

            ec1, ec2, ec3 = st.columns(3)
            with ec1: tarjeta_meta("Depósitos Hoy",    get_cierres(df_esp_m, hoy_date, hoy_date),              META_DIARIA*n_esp,   "📅", "#00d4aa")
            with ec2: tarjeta_meta("Depósitos Semana", get_cierres(df_esp_m, inicio_sem.date(), hoy_date),    META_SEMANAL*n_esp,  "📆", "#00d4aa")
            with ec3: tarjeta_meta("Depósitos Mes",    get_cierres(df_esp_m, inicio_mes.date(), hoy_date),    META_MENSUAL*n_esp,  "🗓️", "#00d4aa")

            barras_asesor(df_esp_m, "Progreso de HOY — España", "#00d4aa")

            st.markdown("---")

            # ── USA ─────────────────────────────────────────────────────────
            st.markdown("""<div style="background:linear-gradient(135deg,#0d0d0d,#1a1500);border:1px solid #7c6af7;
                border-radius:14px;padding:12px 20px;margin-bottom:12px">
                <span style="color:#7c6af7;font-size:1.1rem;font-weight:800">🇺🇸 GRUPO USA</span>
                <span style="color:#8b9bb4;font-size:0.8rem;margin-left:12px">{} asesor(es): {}</span>
            </div>""".format(n_usa, ', '.join(asesores_usa) if asesores_usa else 'Sin datos'), unsafe_allow_html=True)

            uc1, uc2, uc3 = st.columns(3)
            with uc1: tarjeta_meta("Depósitos Hoy",    get_cierres(df_usa_m, hoy_date, hoy_date),             META_DIARIA*n_usa,   "📅", "#7c6af7")
            with uc2: tarjeta_meta("Depósitos Semana", get_cierres(df_usa_m, inicio_sem.date(), hoy_date),   META_SEMANAL*n_usa,  "📆", "#7c6af7")
            with uc3: tarjeta_meta("Depósitos Mes",    get_cierres(df_usa_m, inicio_mes.date(), hoy_date),   META_MENSUAL*n_usa,  "🗓️", "#7c6af7")

            barras_asesor(df_usa_m, "Progreso de HOY — USA", "#7c6af7")

            st.markdown("---")

            # ── Ranking mensual global ───────────────────────────────────────
            st.markdown("#### 🏆 Ranking Mensual Global por Asesor")
            df_mes_all = df_m[df_m['Fecha'] >= inicio_mes] if 'Fecha' in df_m.columns else pd.DataFrame()
            if not df_mes_all.empty and 'Responsable' in df_mes_all.columns:
                df_rank = df_mes_all.groupby('Responsable')['Cierres'].sum().reset_index()
                df_rank['Grupo'] = df_rank['Responsable'].map(lambda x: EQUIPOS_BASE.get(x, 'Por Clasificar'))
                df_rank = df_rank.rename(columns={'Cierres':'Depósitos'})
                df_rank['Meta'] = META_MENSUAL
                df_rank['% Cumplimiento'] = (df_rank['Depósitos']/META_MENSUAL*100).round(1)
                df_rank['Faltan'] = (META_MENSUAL - df_rank['Depósitos']).clip(lower=0)
                df_rank = df_rank.sort_values('Depósitos', ascending=False)
                color_map = {'España':'#00d4aa','USA':'#7c6af7','Por Clasificar':'#f0d080'}
                fig_rank = px.bar(df_rank, x='Responsable', y='Depósitos', color='Grupo',
                                  color_discrete_map=color_map)
                fig_rank.add_hline(y=META_MENSUAL, line_dash='dash', line_color='#c9a84c',
                                   annotation_text=f'Meta {META_MENSUAL}')
                fig_rank.update_layout(**PLOT_CFG, margin=dict(t=30,b=0,l=0,r=0))
                st.plotly_chart(fig_rank, use_container_width=True)
                st.dataframe(df_rank, use_container_width=True, hide_index=True)
            else:
                st.info("📝 Sin datos del mes actual.")

    except Exception as e:
        st.error(f"❌ Error Metas: {e}")

# ══ TAB 3 — ESPAÑA MAYO ══════════════════════════════════════════════════════
with tab3:
    st.markdown("### 🇪🇸 Ventas España — Mayo 2026")
    df_esp = cargar_españa()
    if df_esp.empty:
        st.error("No se pudieron cargar datos de España.")
    else:
        t_ag = df_esp['Agendados'].sum(); t_re = df_esp['Realizados'].sum()
        conv = round(t_re/t_ag*100,1) if t_ag>0 else 0
        ke1,ke2,ke3,ke4 = st.columns(4)
        ke1.metric("📍 Sedes", len(df_esp))
        ke2.metric("📅 Agendados", f"{t_ag:.1f}")
        ke3.metric("✅ Realizados", f"{t_re:.1f}")
        ke4.metric("📊 Conversión", f"{conv}%")
        st.markdown("---")
        e1,e2 = st.columns(2)
        with e1:
            st.markdown("#### 📍 Agendados vs Realizados")
            fig_e1 = go.Figure()
            fig_e1.add_trace(go.Bar(name='Agendados', x=df_esp['Sede'], y=df_esp['Agendados'], marker_color='#7c6af7'))
            fig_e1.add_trace(go.Bar(name='Realizados', x=df_esp['Sede'], y=df_esp['Realizados'], marker_color='#00d4aa'))
            fig_e1.update_layout(barmode='group', **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_e1, use_container_width=True)
        with e2:
            st.markdown("#### 🍩 Distribución Realizados")
            df_e2 = df_esp[df_esp['Realizados']>0]
            fig_e2 = px.pie(df_e2, values='Realizados', names='Sede', hole=0.5,
                            color_discrete_sequence=px.colors.sequential.Teal)
            fig_e2.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_e2, use_container_width=True)
        e3,e4 = st.columns(2)
        with e3:
            st.markdown("#### 📊 % Conversión por Sede")
            df_conv = df_esp[df_esp['Agendados']>0].copy()
            df_conv['% Conversión'] = pd.to_numeric(df_conv['% Conversión'], errors='coerce').fillna(0)
            if not df_conv.empty and df_conv['% Conversión'].sum() > 0:
                fig_e3 = px.bar(df_conv, x='Sede', y='% Conversión', color='% Conversión',
                                color_continuous_scale='teal', text='% Conversión')
                fig_e3.update_traces(texttemplate='%{text}%')
                fig_e3.update_layout(coloraxis_showscale=False, **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
                st.plotly_chart(fig_e3, use_container_width=True)
            else:
                st.info("Sin datos de conversión.")
        with e4:
            st.markdown("#### 💬 Leads por Sede")
            df_leads_esp = pd.DataFrame({
                'Sede':['Alicante','Barcelona','Valencia','Madrid','Malaga','Bilbao'],
                'Leads WPP':[27,31,18,39,43,21],
                'Leads IG':[37,144,39,214,99,0]
            })
            fig_e4 = px.bar(df_leads_esp, x='Sede', y=['Leads WPP','Leads IG'],
                            barmode='group', color_discrete_sequence=['#00d4aa','#7c6af7'])
            fig_e4.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_e4, use_container_width=True)
        st.markdown("---")
        st.dataframe(df_esp, use_container_width=True, hide_index=True)

# ══ TAB 4 — USA MAYO ═════════════════════════════════════════════════════════
with tab4:
    st.markdown("### 🇺🇸 Ventas USA — Mayo 2026")
    df_usa = cargar_usa()
    if df_usa.empty:
        st.error("No se pudieron cargar datos de USA.")
    else:
        t_ag = df_usa['Agendados'].sum(); t_re = df_usa['Realizados'].sum()
        conv = round(t_re/t_ag*100,1) if t_ag>0 else 0
        ku1,ku2,ku3,ku4 = st.columns(4)
        ku1.metric("📍 Sedes", len(df_usa))
        ku2.metric("📅 Agendados", f"{t_ag:.1f}")
        ku3.metric("✅ Realizados", f"{t_re:.1f}")
        ku4.metric("📊 Conversión", f"{conv}%")
        st.markdown("---")
        u1,u2 = st.columns(2)
        with u1:
            st.markdown("#### 📍 Agendados vs Realizados")
            fig_u1 = go.Figure()
            fig_u1.add_trace(go.Bar(name='Agendados', x=df_usa['Sede'], y=df_usa['Agendados'], marker_color='#7c6af7'))
            fig_u1.add_trace(go.Bar(name='Realizados', x=df_usa['Sede'], y=df_usa['Realizados'], marker_color='#00d4aa'))
            fig_u1.update_layout(barmode='group', **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_u1, use_container_width=True)
        with u2:
            st.markdown("#### 🍩 Distribución Realizados")
            fig_u2 = px.pie(df_usa, values='Realizados', names='Sede', hole=0.5,
                            color_discrete_sequence=px.colors.sequential.Purples)
            fig_u2.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_u2, use_container_width=True)
        u3,u4 = st.columns(2)
        with u3:
            st.markdown("#### 📊 % Conversión por Sede")
            df_usa_conv = df_usa[df_usa['Agendados']>0].copy()
            df_usa_conv['% Conversión'] = pd.to_numeric(df_usa_conv['% Conversión'], errors='coerce').fillna(0)
            if not df_usa_conv.empty and df_usa_conv['% Conversión'].sum() > 0:
                fig_u3 = px.bar(df_usa_conv, x='Sede', y='% Conversión', color='% Conversión',
                                color_continuous_scale='purples', text='% Conversión')
                fig_u3.update_traces(texttemplate='%{text}%')
                fig_u3.update_layout(coloraxis_showscale=False, **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
                st.plotly_chart(fig_u3, use_container_width=True)
            else:
                st.info("Sin datos de conversión.")
        with u4:
            st.markdown("#### 💬 Leads por Sede")
            df_leads_usa = pd.DataFrame({
                'Sede':['Dallas','Houston','New Jersey','Orlando','Los Angeles'],
                'Leads WPP+IG':[277.4,296.4,343.4,214.4,318.4]
            })
            fig_u4 = px.bar(df_leads_usa, x='Sede', y='Leads WPP+IG',
                            color='Leads WPP+IG', color_continuous_scale='purples')
            fig_u4.update_layout(coloraxis_showscale=False, **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_u4, use_container_width=True)
        st.markdown("---")
        st.dataframe(df_usa, use_container_width=True, hide_index=True)

# ══ TAB 5 — GLOBAL ═══════════════════════════════════════════════════════════
with tab5:
    st.markdown("### 🌍 Resumen Global — Mayo 2026")
    df_global = cargar_global()
    t_ag = df_global['Agendados'].sum(); t_re = df_global['Realizados'].sum()
    t_esp = df_global[df_global['País']=='🇪🇸 España']['Realizados'].sum()
    t_usa = df_global[df_global['País']=='🇺🇸 USA']['Realizados'].sum()
    conv_g = round(t_re/t_ag*100,1) if t_ag>0 else 0
    g1,g2,g3,g4,g5 = st.columns(5)
    g1.metric("🌍 Total Sedes", len(df_global))
    g2.metric("📅 Agendados", f"{t_ag:.1f}")
    g3.metric("✅ Realizados", f"{t_re:.1f}")
    g4.metric("🇪🇸 España", f"{t_esp:.1f}")
    g5.metric("🇺🇸 USA", f"{t_usa:.1f}")
    st.markdown("---")
    col1,col2 = st.columns(2)
    with col1:
        st.markdown("#### 📊 Realizados por Sede")
        fig_all = px.bar(df_global.sort_values('Realizados',ascending=True),
                         x='Realizados', y='Sede', orientation='h',
                         color='País', color_discrete_map={'🇪🇸 España':'#00d4aa','🇺🇸 USA':'#7c6af7'})
        fig_all.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
        st.plotly_chart(fig_all, use_container_width=True)
    with col2:
        st.markdown("#### 🌍 España vs USA")
        df_pais = pd.DataFrame({'País':['🇪🇸 España','🇺🇸 USA'],'Total':[t_esp,t_usa]})
        fig_p = px.pie(df_pais, values='Total', names='País', hole=0.5,
                       color_discrete_sequence=['#00d4aa','#7c6af7'])
        fig_p.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
        st.plotly_chart(fig_p, use_container_width=True)
    col3,col4 = st.columns(2)
    with col3:
        st.markdown("#### 📈 Agendados vs Realizados")
        fig_g3 = go.Figure()
        fig_g3.add_trace(go.Bar(name='Agendados', x=df_global['Sede'], y=df_global['Agendados'], marker_color='rgba(124,106,247,0.6)'))
        fig_g3.add_trace(go.Bar(name='Realizados', x=df_global['Sede'], y=df_global['Realizados'], marker_color='#00d4aa'))
        fig_g3.update_layout(barmode='group', **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
        st.plotly_chart(fig_g3, use_container_width=True)
    with col4:
        st.markdown("#### 📊 % Conversión por Sede")
        df_cv = df_global[df_global['Agendados']>0].copy()
        df_cv['% Conversión'] = pd.to_numeric(df_cv['% Conversión'], errors='coerce').fillna(0)
        if not df_cv.empty and df_cv['% Conversión'].sum() > 0:
            fig_g4 = px.bar(df_cv, x='Sede', y='% Conversión', color='País',
                            text='% Conversión',
                            color_discrete_map={'🇪🇸 España':'#00d4aa','🇺🇸 USA':'#7c6af7'})
            fig_g4.update_traces(texttemplate='%{text}%')
            fig_g4.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_g4, use_container_width=True)
        else:
            st.info("Sin datos de conversión.")
    st.markdown("---")
    st.dataframe(df_global.sort_values(['País','Realizados'],ascending=[True,False]),
                 use_container_width=True, hide_index=True)