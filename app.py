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
# Mapeo real según la hoja (CAROLINA=USA, DANIELA=España, EVELYN=España)
EQUIPOS_BASE  = {'CAROLINA': 'USA', 'DANIELA': 'España', 'EVELYN': 'España', 'EVELIN': 'España'}
META_DIARIA   = 4
META_SEMANAL  = 40
META_MENSUAL  = 100

def sheet_url(nombre):
    """Genera URL para leer CSV desde Google Sheets (requiere 'Publicar en la web')."""
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre.replace(' ','%20')}"

# ── DIAGNÓSTICO DE CONEXIÓN ────────────────────────────────────────────────────
def diagnosticar_sheets():
    """Prueba la conexión a cada pestaña y muestra el resultado."""
    import requests
    sheets = ["Ventas diarias", "España mayo 2026 ", "usa mayo 2026", "TAREAS KOMMO"]
    for nombre in sheets:
        try:
            r = requests.get(sheet_url(nombre), timeout=10)
            if r.status_code == 200 and len(r.text) > 200 and not r.text.strip().startswith('<'):
                st.success(f"✅ **'{nombre}'** → OK ({len(r.text):,} bytes)")
            else:
                st.error(f"❌ **'{nombre}'** → Status {r.status_code} | Respuesta HTML (sheet NO publicado en la web)")
                st.caption(r.text[:300])
        except Exception as e:
            st.error(f"❌ **'{nombre}'** → Error de red: {e}")

# ── CARGA VENTAS DIARIAS ───────────────────────────────────────────────────────
# Estructura real detectada:
# Col 0: FECHA | Col 1: DIA | Col 2: RESPONSABLE | Col 3: VALORACIONES
# Col 4: LEADS WPP | Col 5: LEADS IG | Col 6: LEADS FORMULARIO
# Col 7: LEADS LANDING | Col 8: LEADS TIKTOK | Col 9: DEPOSITOS | Col 10: PRESUPUESTADO

@st.cache_data(ttl=60)
def cargar_ventas_diarias():
    try:
        url = sheet_url("Ventas diarias")
        raw = pd.read_csv(url, header=None)

        # Buscar fila de encabezado (contiene FECHA, DIA, RESPONSABLE...)
        header_idx = 0
        for i in range(min(20, len(raw))):
            vals = raw.iloc[i].map(str).str.upper().str.strip().values
            if 'FECHA' in vals and 'RESPONSABLE' in vals:
                header_idx = i
                break

        df = pd.read_csv(url, skiprows=header_idx)
        # Limpiar columnas
        df.columns = [str(c).strip().upper().replace('  ', ' ') for c in df.columns]

        # Renombrar columnas según estructura real detectada
        rename_map = {
            'FECHA':             'Fecha',
            'DIA':               'Dia_Texto',
            'SEMANA':            'Semana',
            'RESPONSABLE':       'Responsable',
            'VALORACIONES':      'Valoraciones',
            'LEADS WPP':         'Leads WPP',
            'LEADS IG':          'Leads IG',
            'LEADS FORMULARIO':  'Leads Formulario',
            'LEADS LANDING':     'Leads Landing',
            'LEADS TIKTOK':      'Leads Tiktok',
            'DEPOSITOS':         'Cierres',         # ← nombre real en el sheet
            'DEPÓSITOS':         'Cierres',
            'PRESUPUESTADO':     'Venta Dia Siguiente',
            # Nombres alternativos por si acaso
            'CIERRES AGENDADOS':              'Cierres',
            'VENTA DIA SIGUIENTE(AGENDADOS)': 'Venta Dia Siguiente',
        }
        df = df.rename(columns=rename_map)

        # Filtrar filas válidas (que tengan responsable real)
        if 'Responsable' in df.columns:
            df['Responsable'] = df['Responsable'].astype(str).str.strip().str.upper()
            df = df[df['Responsable'].notna()]
            df = df[~df['Responsable'].isin(['', 'NAN', 'N/A', 'RESPONSABLE', 'TOTAL', 'TOTALES', 'NONE'])]

            def asignar_grupo(r):
                resp = str(r.get('Responsable', '')).upper().strip()
                if resp in EQUIPOS_BASE:
                    return EQUIPOS_BASE[resp]
                return 'Por Clasificar'

            df['Grupo_Pais'] = df.apply(asignar_grupo, axis=1)

        # Parsear fecha
        if 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
            df = df[df['Fecha'].notna()]

        # Día de la semana
        DIAS_NORM = {
            'LUNES':'Lunes','MARTES':'Martes','MIERCOLES':'Miércoles',
            'MIÉRCOLES':'Miércoles','JUEVES':'Jueves','VIERNES':'Viernes',
            'SABADO':'Sábado','SÁBADO':'Sábado','DOMINGO':'Domingo'
        }
        if 'Dia_Texto' in df.columns:
            df['Dia_Semana'] = df['Dia_Texto'].astype(str).str.strip().str.upper().map(DIAS_NORM).fillna('Sin dato')
        elif 'Fecha' in df.columns:
            nombres = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
            df['Dia_Semana'] = df['Fecha'].dt.dayofweek.map(lambda x: nombres[x])
        else:
            df['Dia_Semana'] = 'Sin dato'

        if 'Semana' not in df.columns:
            df['Semana'] = '1'
        df['Semana'] = df['Semana'].astype(str).str.strip()

        # Convertir columnas numéricas (incluye las nuevas: Formulario, Landing, Tiktok)
        cols_num = ['Valoraciones', 'Leads WPP', 'Leads IG', 'Leads Formulario',
                    'Leads Landing', 'Leads Tiktok', 'Cierres', 'Venta Dia Siguiente']
        for col in cols_num:
            if col in df.columns:
                serie = df[col].astype(str).str.strip()
                serie = serie.replace({'N/A':'0','n/a':'0','NA':'0','nan':'0','None':'0','':'0'}, regex=False)
                serie = serie.str.replace('[^0-9.-]', '', regex=True).replace('', '0')
                df[col] = pd.to_numeric(serie, errors='coerce').fillna(0).clip(lower=0).astype(int)
            else:
                df[col] = 0

        return df

    except Exception as e:
        st.error(f"❌ Error cargando 'Ventas diarias': {e}")
        st.info("💡 Asegúrate de hacer **Archivo → Publicar en la web** (diferente a 'Compartir').")
        return pd.DataFrame()


# ── CARGA ESPAÑA MAYO 2026 ─────────────────────────────────────────────────────
# Estructura real: filas = sedes, col 0 = nombre sede
# Totales agendados en columna "TOTAL" (col ~35), realizados en otra "TOTAL" (~78)
# Sedes: alicante, barcelona, valencia, madrid, malaga, bilbao

@st.cache_data(ttl=300)
def cargar_españa():
    try:
        # OJO: el nombre real tiene espacio al final → "España mayo 2026 "
        # Probamos con y sin espacio
        for nombre in ["España mayo 2026 ", "España mayo 2026", "Espa%C3%B1a%20mayo%202026"]:
            url = sheet_url(nombre)
            try:
                raw = pd.read_csv(url, header=None)
                if len(raw) > 3:
                    break
            except:
                continue

        sedes_buscar = {
            'alicante': 'Alicante',
            'barcelona': 'Barcelona',
            'valencia': 'Valencia',
            'madrid': 'Madrid',
            'malaga': 'Málaga',
            'bilbao': 'Bilbao',
        }

        data_esp = []

        for i in range(len(raw)):
            val = str(raw.iloc[i, 0]).strip().lower().replace(' ', '').replace('á','a').replace('é','e')
            for key, label in sedes_buscar.items():
                if key in val:
                    fila = raw.iloc[i]
                    # La estructura tiene los TOTALES en columnas específicas
                    # Buscamos la columna "TOTAL" en la fila de encabezados
                    # Extraemos todos los números válidos de la fila
                    nums = []
                    for v in fila[1:]:
                        try:
                            n = float(str(v).replace(',', '.').strip())
                            if 0 <= n <= 100:
                                nums.append(n)
                        except:
                            pass

                    # La estructura es: [semana1_agendados x7cols, semana2 x7, semana3 x7, semana4 x7, TOTAL_ag]
                    # luego [semana1_realizados x7, ..., TOTAL_real]
                    # Nos interesa el total: aprox posición 0-27=agendados semanas, pos 28=total_ag
                    # posición 29-56=realizados semanas, pos 57=total_real
                    # Simplificamos: sumamos primeros 28 valores = agendados, siguientes 28 = realizados
                    mid = len(nums) // 2
                    ag = sum(nums[:mid]) if nums else 0
                    re = sum(nums[mid:]) if nums else 0

                    # Alternativa más robusta: buscar en fila TOTAL del sheet
                    data_esp.append({'Sede': label, 'Agendados': round(ag, 1), 'Realizados': round(re, 1)})
                    break

        # Si no se encontraron datos, usar valores del sheet que vimos directamente
        if not data_esp:
            raise Exception("No se encontraron sedes")

        df = pd.DataFrame(data_esp)

    except Exception as e:
        # Datos exactos del sheet leído en el documento
        df = pd.DataFrame([
            {'Sede': 'Alicante',  'Agendados': 10.0,  'Realizados': 7.0},
            {'Sede': 'Barcelona', 'Agendados': 13.5,  'Realizados': 12.5},
            {'Sede': 'Valencia',  'Agendados': 6.0,   'Realizados': 2.0},
            {'Sede': 'Madrid',    'Agendados': 5.5,   'Realizados': 4.5},
            {'Sede': 'Málaga',    'Agendados': 20.5,  'Realizados': 10.5},
            {'Sede': 'Bilbao',    'Agendados': 0.0,   'Realizados': 2.5},
        ])
        st.caption(f"⚠️ Usando datos de respaldo España (sheet no accesible aún)")

    df['Agendados']   = pd.to_numeric(df['Agendados'],   errors='coerce').fillna(0)
    df['Realizados']  = pd.to_numeric(df['Realizados'],  errors='coerce').fillna(0)
    df['% Conversión'] = df.apply(
        lambda r: round(r['Realizados'] / r['Agendados'] * 100, 1) if r['Agendados'] > 0 else 0, axis=1
    )
    return df


# ── CARGA USA MAYO 2026 ────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_usa():
    try:
        url = sheet_url("usa mayo 2026")
        raw = pd.read_csv(url, header=None)

        sedes_buscar = {
            'dallas':      'Dallas',
            'houston':     'Houston',
            'newjersy':    'New Jersey',
            'newjersey':   'New Jersey',
            'orlando':     'Orlando',
            'angeles':     'Los Ángeles',
            'losangeles':  'Los Ángeles',
        }

        data_usa = []
        vistas = set()

        for i in range(len(raw)):
            val = str(raw.iloc[i, 0]).strip().lower().replace(' ', '').replace('á','a')
            for key, label in sedes_buscar.items():
                if key in val and label not in vistas:
                    vistas.add(label)
                    fila = raw.iloc[i]
                    nums = []
                    for v in fila[1:]:
                        try:
                            n = float(str(v).replace(',', '.').strip())
                            if 0 <= n <= 100:
                                nums.append(n)
                        except:
                            pass
                    mid = len(nums) // 2
                    ag = sum(nums[:mid]) if nums else 0
                    re = sum(nums[mid:]) if nums else 0
                    data_usa.append({'Sede': label, 'Agendados': round(ag, 1), 'Realizados': round(re, 1)})
                    break

        if not data_usa:
            raise Exception("No se encontraron sedes USA")

        df = pd.DataFrame(data_usa)

    except Exception as e:
        # Datos exactos del sheet leído
        df = pd.DataFrame([
            {'Sede': 'Dallas',      'Agendados': 8.5,  'Realizados': 6.5},
            {'Sede': 'Houston',     'Agendados': 4.0,  'Realizados': 7.5},
            {'Sede': 'New Jersey',  'Agendados': 6.5,  'Realizados': 4.5},
            {'Sede': 'Orlando',     'Agendados': 3.5,  'Realizados': 4.5},
            {'Sede': 'Los Ángeles', 'Agendados': 11.5, 'Realizados': 13.5},
        ])
        st.caption(f"⚠️ Usando datos de respaldo USA (sheet no accesible aún)")

    df['Agendados']   = pd.to_numeric(df['Agendados'],   errors='coerce').fillna(0)
    df['Realizados']  = pd.to_numeric(df['Realizados'],  errors='coerce').fillna(0)
    df['% Conversión'] = df.apply(
        lambda r: round(r['Realizados'] / r['Agendados'] * 100, 1) if r['Agendados'] > 0 else 0, axis=1
    )
    return df


# ── CARGA GLOBAL ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_global():
    df_esp = cargar_españa()
    df_usa = cargar_usa()
    df_esp['País'] = '🇪🇸 España'
    df_usa['País'] = '🇺🇸 USA'
    return pd.concat([df_esp, df_usa], ignore_index=True)


# ── CARGA TAREAS KOMMO ─────────────────────────────────────────────────────────
# Estructura real: fila 0=TAREAS PENDIENTES, fila 1=RESPONSABLE,TIPO,CANTIDAD,FECHA
@st.cache_data(ttl=60)
def cargar_tareas():
    try:
        url = sheet_url("TAREAS KOMMO")
        raw = pd.read_csv(url, header=None)

        header_idx = 0
        for i in range(min(10, len(raw))):
            vals = raw.iloc[i].map(str).str.upper().str.strip().values
            if 'RESPONSABLE' in vals and 'TIPO' in vals:
                header_idx = i
                break

        df = pd.read_csv(url, skiprows=header_idx)
        df.columns = [str(c).strip().upper() for c in df.columns]

        rename = {
            'RESPONSABLE': 'Responsable',
            'TIPO':        'Tipo',
            'CANTIDAD':    'Cantidad',
            'FECHA':       'Fecha'
        }
        df = df.rename(columns=rename)

        if 'Responsable' in df.columns:
            df['Responsable'] = df['Responsable'].astype(str).str.strip().str.upper()
            df = df[df['Responsable'].notna()]
            df = df[~df['Responsable'].isin(['', 'NAN', 'RESPONSABLE', 'TOTAL'])]

        if 'Cantidad' in df.columns:
            df['Cantidad'] = pd.to_numeric(
                df['Cantidad'].astype(str).str.replace('[^0-9]', '', regex=True),
                errors='coerce'
            ).fillna(0).astype(int)

        return df

    except Exception as e:
        return pd.DataFrame()


# ── CARGA DE VENTAS MAYO CONSOLIDADO (pestaña "VENTAS MES DE MAYO") ────────────
@st.cache_data(ttl=300)
def cargar_ventas_mes_mayo():
    """
    Lee la pestaña 'VENTAS MES DE MAYO' que tiene la estructura consolidada
    con totales por sede USA y los totales generales.
    """
    try:
        url = sheet_url("VENTAS MES DE MAYO")
        raw = pd.read_csv(url, header=None)

        # Buscar fila con SEDES
        header_idx = 0
        for i in range(min(15, len(raw))):
            vals = raw.iloc[i].map(str).str.upper().str.strip().values
            if 'SEDES' in vals or 'DALLAS' in vals:
                header_idx = i
                break

        df = pd.read_csv(url, skiprows=header_idx)
        df.columns = [str(c).strip().upper() for c in df.columns]

        # Renombrar primera columna a Sede
        primera_col = df.columns[0]
        df = df.rename(columns={primera_col: 'Sede'})

        df['Sede'] = df['Sede'].astype(str).str.strip()
        df = df[~df['Sede'].isin(['', 'NAN', 'SEDES', 'TOTAL'])]
        df = df[df['Sede'].notna()]

        return df

    except Exception as e:
        return pd.DataFrame()


# ════════════════════════════════════════════════════════════════════
# CARGA INICIAL
# ════════════════════════════════════════════════════════════════════
df_base = cargar_ventas_diarias()

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    if logo_b64:
        st.markdown(
            f'<div style="text-align:center;padding:16px 0 8px 0">'
            f'<img src="data:image/png;base64,{logo_b64}" style="width:180px;border-radius:8px"></div>',
            unsafe_allow_html=True
        )
    st.markdown(
        '<div style="color:#c9a84c;font-size:0.7rem;text-transform:uppercase;'
        'letter-spacing:2px;text-align:center;margin-bottom:10px;font-weight:700">Panel de Control</div>',
        unsafe_allow_html=True
    )
    st.markdown("---")
    st.markdown("### 🔍 Filtros")

    modo_fecha = st.radio("📅 Filtrar por", ["Día específico", "Rango de fechas", "Semana", "Todos"])
    fecha_ini = fecha_fin = None
    semana_sel = "Todas"

    if modo_fecha == "Día específico":
        fecha_sel  = st.date_input("Selecciona el día", value=date.today())
        fecha_ini  = fecha_fin = pd.Timestamp(fecha_sel)
    elif modo_fecha == "Rango de fechas":
        fecha_ini  = pd.Timestamp(st.date_input("Desde", value=date.today() - timedelta(days=6)))
        fecha_fin  = pd.Timestamp(st.date_input("Hasta", value=date.today()))
    elif modo_fecha == "Semana":
        sems = ["Todas"]
        if not df_base.empty and 'Semana' in df_base.columns:
            sems += sorted(
                df_base['Semana'].dropna().unique().tolist(),
                key=lambda x: int(x) if str(x).isdigit() else 0
            )
        semana_sel = st.selectbox("📆 Semana", sems)

    dia_sel  = st.selectbox("📅 Día de la semana",
                            ["Todos", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
    grupo_sel = st.selectbox("🌍 Grupo / País", ["Todos", "USA", "España"])

    if not df_base.empty and 'Responsable' in df_base.columns:
        if grupo_sel == "USA":
            coms = df_base[df_base['Grupo_Pais'] == 'USA']['Responsable'].unique().tolist()
        elif grupo_sel == "España":
            coms = df_base[df_base['Grupo_Pais'] == 'España']['Responsable'].unique().tolist()
        else:
            coms = df_base['Responsable'].unique().tolist()
        vendedores = ["Todos"] + sorted(coms)
    else:
        vendedores = ["Todos"]
    responsable_sel = st.selectbox("👤 Responsable", vendedores)

    st.markdown("---")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Actualizar"):
            st.cache_data.clear()
            st.rerun()
    with col_btn2:
        if st.button("🔧 Diagnóstico"):
            diagnosticar_sheets()
    st.caption("Datos en tiempo real · TTL 60s")

# ── APLICAR FILTROS ────────────────────────────────────────────────────────────
df_filtrado = df_base.copy()
if not df_filtrado.empty and 'Fecha' in df_filtrado.columns:
    if modo_fecha == "Día específico" and fecha_ini is not None:
        df_filtrado = df_filtrado[df_filtrado['Fecha'].dt.date == fecha_ini.date()]
    elif modo_fecha == "Rango de fechas" and fecha_ini is not None:
        df_filtrado = df_filtrado[(df_filtrado['Fecha'] >= fecha_ini) & (df_filtrado['Fecha'] <= fecha_fin)]
    elif modo_fecha == "Semana" and semana_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Semana'].astype(str) == semana_sel]
    if dia_sel != "Todos" and 'Dia_Semana' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Dia_Semana'] == dia_sel]
    if grupo_sel != "Todos" and 'Grupo_Pais' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Grupo_Pais'] == grupo_sel]
    if responsable_sel != "Todos" and 'Responsable' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Responsable'] == responsable_sel]

# ── HEADER ─────────────────────────────────────────────────────────────────────
col_logo_h, col_title_h = st.columns([1, 4])
with col_logo_h:
    if logo_b64:
        st.markdown(
            f'<img src="data:image/png;base64,{logo_b64}" style="width:160px;margin-top:10px;border-radius:8px">',
            unsafe_allow_html=True
        )
with col_title_h:
    st.markdown("""
    <div style="padding-top:5px">
        <div style="color:#c9a84c;font-size:0.8rem;text-transform:uppercase;letter-spacing:3px">Colombia Smile Design</div>
        <div style="color:#ffffff;font-size:2.2rem;font-weight:800;line-height:1.2">Dashboard de Ventas</div>
        <div style="color:#c9a84c;font-size:0.85rem">España 🇪🇸 · USA 🇺🇸 · Tiempo real</div>
    </div>""", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📋 Ventas Diarias", "🎯 Metas", "🇪🇸 España Mayo", "🇺🇸 USA Mayo", "🌍 Global"]
)

# ══ TAB 1 — VENTAS DIARIAS ════════════════════════════════════════════════════
with tab1:
    partes = []
    if modo_fecha == "Día específico" and fecha_ini:
        partes.append(fecha_ini.strftime('%d/%m/%Y'))
    elif modo_fecha == "Rango de fechas" and fecha_ini:
        partes.append(f"{fecha_ini.strftime('%d/%m')}→{fecha_fin.strftime('%d/%m')}")
    elif modo_fecha == "Semana":
        partes.append(f"Semana {semana_sel}")
    if dia_sel != "Todos":          partes.append(dia_sel)
    if grupo_sel != "Todos":        partes.append(grupo_sel)
    if responsable_sel != "Todos":  partes.append(responsable_sel)
    desc = " · ".join(partes) if partes else "Todos los registros"
    st.markdown(f"### 📊 {desc}")

    if df_filtrado.empty:
        st.warning("⚠️ Sin registros para estos filtros.")
        st.info(
            "**Si el dashboard no muestra datos**, el sheet necesita ser publicado:\n\n"
            "1. Abre el sheet en Google Sheets\n"
            "2. **Archivo → Compartir → Publicar en la web**\n"
            "3. Selecciona *Documento completo* → *Valores separados por comas (.csv)*\n"
            "4. Clic en **Publicar**\n\n"
            "Esto es diferente al botón 'Compartir' habitual.\n\n"
            "Luego pulsa **🔧 Diagnóstico** en el sidebar para verificar."
        )
    else:
        # ── KPIs Grupo USA ──
        df_usa_f = df_filtrado[df_filtrado['Grupo_Pais'] == 'USA'] if 'Grupo_Pais' in df_filtrado.columns else pd.DataFrame()
        st.markdown(
            '<div style="color:#7c6af7;font-size:0.75rem;font-weight:700;'
            'text-transform:uppercase;letter-spacing:2px;margin-bottom:6px">🇺🇸 Grupo USA</div>',
            unsafe_allow_html=True
        )
        u1, u2, u3, u4, u5, u6 = st.columns(6)
        u1.metric("💬 WPP",          int(df_usa_f['Leads WPP'].sum())        if not df_usa_f.empty else 0)
        u2.metric("📸 IG",           int(df_usa_f['Leads IG'].sum())         if not df_usa_f.empty else 0)
        u3.metric("📝 Formulario",   int(df_usa_f['Leads Formulario'].sum()) if not df_usa_f.empty else 0)
        u4.metric("⭐ Valoraciones",  int(df_usa_f['Valoraciones'].sum())     if not df_usa_f.empty else 0)
        u5.metric("📅 Presupuestado",int(df_usa_f['Venta Dia Siguiente'].sum()) if not df_usa_f.empty else 0)
        u6.metric("💰 Depósitos",    int(df_usa_f['Cierres'].sum())          if not df_usa_f.empty else 0)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── KPIs Grupo España ──
        df_esp_f = df_filtrado[df_filtrado['Grupo_Pais'] == 'España'] if 'Grupo_Pais' in df_filtrado.columns else pd.DataFrame()
        st.markdown(
            '<div style="color:#00d4aa;font-size:0.75rem;font-weight:700;'
            'text-transform:uppercase;letter-spacing:2px;margin-bottom:6px">🇪🇸 Grupo España</div>',
            unsafe_allow_html=True
        )
        e1, e2, e3, e4, e5, e6 = st.columns(6)
        e1.metric("💬 WPP",          int(df_esp_f['Leads WPP'].sum())        if not df_esp_f.empty else 0)
        e2.metric("📸 IG",           int(df_esp_f['Leads IG'].sum())         if not df_esp_f.empty else 0)
        e3.metric("📝 Formulario",   int(df_esp_f['Leads Formulario'].sum()) if not df_esp_f.empty else 0)
        e4.metric("⭐ Valoraciones",  int(df_esp_f['Valoraciones'].sum())     if not df_esp_f.empty else 0)
        e5.metric("📅 Presupuestado",int(df_esp_f['Venta Dia Siguiente'].sum()) if not df_esp_f.empty else 0)
        e6.metric("💰 Depósitos",    int(df_esp_f['Cierres'].sum())          if not df_esp_f.empty else 0)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Tabla ──
        cols_vis = ['Fecha', 'Dia_Semana', 'Semana', 'Responsable', 'Grupo_Pais',
                    'Leads WPP', 'Leads IG', 'Leads Formulario', 'Leads Landing', 'Leads Tiktok',
                    'Valoraciones', 'Venta Dia Siguiente', 'Cierres']
        cols_ok  = [c for c in cols_vis if c in df_filtrado.columns]
        df_show  = df_filtrado[cols_ok].copy()

        if 'Fecha' in df_show.columns:
            df_show = df_show.sort_values('Fecha', ascending=True)
            df_show['Fecha'] = df_show['Fecha'].dt.strftime('%d/%m/%Y')

        df_show = df_show.rename(columns={
            'Venta Dia Siguiente': 'Presupuestado',
            'Cierres':             'Depósitos',
            'Dia_Semana':          'Día',
            'Grupo_Pais':          'Grupo',
            'Leads Formulario':    'Formulario',
            'Leads Landing':       'Landing',
            'Leads Tiktok':        'TikTok',
        })

        cols_num_tabla = ['Leads WPP', 'Leads IG', 'Formulario', 'Landing', 'TikTok',
                          'Valoraciones', 'Presupuestado', 'Depósitos']
        totales = {c: df_show[c].sum() if c in df_show.columns and c in cols_num_tabla else ''
                   for c in df_show.columns}
        totales['Fecha']        = '📊 TOTAL'
        totales['Día']          = ''
        totales['Semana']       = ''
        totales['Responsable']  = ''
        totales['Grupo']        = ''

        df_final = pd.concat([df_show, pd.DataFrame([totales])], ignore_index=True)

        st.markdown("#### 📋 Registros por Fecha")
        st.dataframe(df_final, use_container_width=True, hide_index=True)
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Descargar CSV", data=csv,
                           file_name=f"ventas_{date.today()}.csv", mime="text/csv")
        st.markdown("---")

        # ── Embudos ──
        st.markdown("### 🔻 Embudos de Ventas")

        def render_embudo_horizontal(titulo, etapas_vals, color_borde):
            st.markdown(
                f'<div style="color:{color_borde};font-size:0.8rem;font-weight:800;'
                f'text-transform:uppercase;letter-spacing:2px;margin-bottom:10px">{titulo}</div>',
                unsafe_allow_html=True
            )
            items_html = ""
            for i, (etapa, val) in enumerate(etapas_vals):
                color_val = color_borde if str(val) not in ["—", "0", 0] else "#555566"
                items_html += f"""
                <div style="display:inline-flex;flex-direction:column;align-items:center;
                            justify-content:center;background:linear-gradient(135deg,#0d0d0d,#1a1500);
                            border:1px solid {color_borde};border-radius:14px;padding:22px 20px;
                            min-width:150px;min-height:110px;text-align:center;vertical-align:top;
                            box-shadow:0 4px 15px rgba(0,0,0,0.3)">
                    <div style="color:#8b9bb4;font-size:0.75rem;text-transform:uppercase;
                                letter-spacing:0.8px;margin-bottom:12px;white-space:nowrap">{etapa}</div>
                    <div style="color:{color_val};font-size:2.4rem;font-weight:800;line-height:1">{val}</div>
                </div>"""
                if i < len(etapas_vals) - 1:
                    items_html += f"""
                <div style="display:inline-flex;align-items:center;justify-content:center;
                            padding:0 6px;vertical-align:top;margin-top:30px">
                    <span style="color:{color_borde};font-size:1.5rem;font-weight:300">→</span>
                </div>"""
            st.markdown(
                f'<div style="overflow-x:auto;white-space:nowrap;padding-bottom:8px">{items_html}</div>',
                unsafe_allow_html=True
            )

        df_esp_emb = df_filtrado[df_filtrado['Grupo_Pais'] == 'España'] if 'Grupo_Pais' in df_filtrado.columns else pd.DataFrame()
        df_usa_emb = df_filtrado[df_filtrado['Grupo_Pais'] == 'USA']    if 'Grupo_Pais' in df_filtrado.columns else pd.DataFrame()

        def s(df, col): return int(df[col].sum()) if not df.empty and col in df.columns else 0

        leads_esp = s(df_esp_emb, 'Leads WPP') + s(df_esp_emb, 'Leads IG') + s(df_esp_emb, 'Leads Formulario')
        val_esp   = s(df_esp_emb, 'Valoraciones')
        pres_esp  = s(df_esp_emb, 'Venta Dia Siguiente')
        dep_esp   = s(df_esp_emb, 'Cierres')

        leads_usa = s(df_usa_emb, 'Leads WPP') + s(df_usa_emb, 'Leads IG') + s(df_usa_emb, 'Leads Formulario')
        val_usa   = s(df_usa_emb, 'Valoraciones')
        pres_usa  = s(df_usa_emb, 'Venta Dia Siguiente')
        dep_usa   = s(df_usa_emb, 'Cierres')

        etapas_esp = [
            ("📥 Leads", leads_esp), ("📞 Contactado", "—"), ("🔇 No Contestó", "—"),
            ("⭐ Valoración", val_esp), ("💵 Presupuesto", pres_esp), ("💳 Financiamiento", "—"),
            ("🏥 Val. Presencial", "—"), ("📅 Ag. Depósito", dep_esp), ("✅ Venta Cerrada", "—"),
        ]
        etapas_usa = [
            ("📥 Leads", leads_usa), ("📞 Contactado", "—"), ("🔇 No Contesta", "—"),
            ("💻 Val. Virtual", val_usa), ("💵 Presupuesto", pres_usa),
            ("🏥 Ag. Presencial", "—"), ("📅 Ag. Depósito", dep_usa),
        ]

        render_embudo_horizontal("🇪🇸 Embudo España", etapas_esp, "#00d4aa")
        st.markdown("<br>", unsafe_allow_html=True)
        render_embudo_horizontal("🇺🇸 Embudo USA",    etapas_usa, "#7c6af7")

        st.markdown("---")

        # ── Tareas ──
        st.markdown("### 📋 Tareas para Hoy")
        df_tareas = cargar_tareas()

        if df_tareas.empty:
            st.info("ℹ️ No hay tareas pendientes registradas en TAREAS KOMMO.")
        else:
            t_col1, t_col2 = st.columns(2)
            TIPOS_TAREA = ['VALORACIÓN VIRTUAL', 'VALORACION VIRTUAL', 'SEGUIMIENTO']
            ASESORES    = ['DANIELA', 'EVELYN', 'EVELIN', 'CAROLINA']

            for asesor in ASESORES:
                df_a   = df_tareas[df_tareas['Responsable'] == asesor] if 'Responsable' in df_tareas.columns else pd.DataFrame()
                grupo  = EQUIPOS_BASE.get(asesor, 'Por Clasificar')
                color  = "#00d4aa" if grupo == 'España' else "#7c6af7"
                col_t  = t_col1 if grupo == 'España' else t_col2

                with col_t:
                    st.markdown(f"""
                    <div style="background:linear-gradient(135deg,#0d0d0d,#1a1500);border:1px solid {color};
                                border-radius:12px;padding:14px 18px;margin-bottom:12px">
                        <div style="color:{color};font-weight:800;font-size:1.05rem;
                                    margin-bottom:8px;letter-spacing:0.5px">👤 {asesor}</div>
                    """, unsafe_allow_html=True)
                    tc1, tc2 = st.columns(2)
                    for idx, tipo_label in enumerate(['Valoración Virtual', 'Seguimiento']):
                        cant = 0
                        if not df_a.empty and 'Tipo' in df_a.columns:
                            mask = df_a['Tipo'].astype(str).str.upper().str.strip().str.contains(
                                tipo_label.upper().replace('Ó', 'O').replace('ó', 'o'), na=False
                            )
                            cant = int(df_a[mask]['Cantidad'].sum()) if mask.any() else 0
                        with (tc1 if idx == 0 else tc2):
                            st.markdown(f"""
                            <div style="padding:4px 0">
                                <span style="color:#8b9bb4;font-size:0.78rem;text-transform:uppercase">{tipo_label}</span><br>
                                <span style="color:#ffffff;font-size:1.5rem;font-weight:700">{cant}</span>
                            </div>""", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)


# ══ TAB 2 — METAS ══════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 🎯 Cumplimiento de Metas")
    if df_filtrado.empty:
        st.warning("⚠️ Sin datos para calcular metas.")
    else:
        cierres_totales = int(df_filtrado['Cierres'].sum()) if 'Cierres' in df_filtrado.columns else 0

        m1, m2, m3 = st.columns(3)
        with m1:
            pct_d = min(round((cierres_totales / META_DIARIA)   * 100, 1), 100.0) if META_DIARIA   > 0 else 0
            st.metric("Meta Diaria (4)",    f"{cierres_totales} Depósitos", f"{pct_d}% Logrado")
            st.progress(pct_d / 100)
        with m2:
            pct_s = min(round((cierres_totales / META_SEMANAL)  * 100, 1), 100.0) if META_SEMANAL  > 0 else 0
            st.metric("Meta Semanal (40)",  f"{cierres_totales} Depósitos", f"{pct_s}% Logrado")
            st.progress(pct_s / 100)
        with m3:
            pct_m = min(round((cierres_totales / META_MENSUAL)  * 100, 1), 100.0) if META_MENSUAL  > 0 else 0
            st.metric("Meta Mensual (100)", f"{cierres_totales} Depósitos", f"{pct_m}% Logrado")
            st.progress(pct_m / 100)

        # Gráfico depósitos por responsable
        if 'Responsable' in df_filtrado.columns and not df_filtrado.empty:
            df_resp = df_filtrado.groupby(['Responsable', 'Grupo_Pais'])['Cierres'].sum().reset_index()
            df_resp = df_resp[df_resp['Cierres'] > 0]
            if not df_resp.empty:
                fig_metas = px.bar(
                    df_resp, x='Responsable', y='Cierres', color='Grupo_Pais',
                    title="Depósitos por Responsable",
                    color_discrete_map={'USA': '#7c6af7', 'España': '#00d4aa', 'Por Clasificar': '#c9a84c'}
                )
                fig_metas.update_layout(**PLOT_CFG)
                st.plotly_chart(fig_metas, use_container_width=True)


# ══ TAB 3 — ESPAÑA MAYO ════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 🇪🇸 Desempeño Clínicas España — Mayo 2026")
    df_esp_m = cargar_españa()
    st.dataframe(df_esp_m, use_container_width=True, hide_index=True)

    fig_esp = px.bar(
        df_esp_m, x='Sede', y=['Agendados', 'Realizados'], barmode='group',
        title="Agendados vs Realizados por Sede (España)",
        color_discrete_map={'Agendados': '#c9a84c', 'Realizados': '#00d4aa'}
    )
    fig_esp.update_layout(**PLOT_CFG)
    st.plotly_chart(fig_esp, use_container_width=True)

    # Conversión
    fig_conv_esp = px.bar(
        df_esp_m, x='Sede', y='% Conversión',
        title="% Conversión por Sede (España)",
        color='% Conversión',
        color_continuous_scale=['#c9a84c', '#00d4aa']
    )
    fig_conv_esp.update_layout(**PLOT_CFG)
    st.plotly_chart(fig_conv_esp, use_container_width=True)


# ══ TAB 4 — USA MAYO ══════════════════════════════════════════════════════════
with tab4:
    st.markdown("### 🇺🇸 Desempeño Clínicas USA — Mayo 2026")
    df_usa_m = cargar_usa()
    st.dataframe(df_usa_m, use_container_width=True, hide_index=True)

    fig_usa = px.bar(
        df_usa_m, x='Sede', y=['Agendados', 'Realizados'], barmode='group',
        title="Agendados vs Realizados por Sede (USA)",
        color_discrete_map={'Agendados': '#c9a84c', 'Realizados': '#7c6af7'}
    )
    fig_usa.update_layout(**PLOT_CFG)
    st.plotly_chart(fig_usa, use_container_width=True)

    fig_conv_usa = px.bar(
        df_usa_m, x='Sede', y='% Conversión',
        title="% Conversión por Sede (USA)",
        color='% Conversión',
        color_continuous_scale=['#c9a84c', '#7c6af7']
    )
    fig_conv_usa.update_layout(**PLOT_CFG)
    st.plotly_chart(fig_conv_usa, use_container_width=True)


# ══ TAB 5 — GLOBAL ════════════════════════════════════════════════════════════
with tab5:
    st.markdown("### 🌍 Comparativo Global — Mayo 2026")
    df_glob = cargar_global()

    g1, g2 = st.columns(2)
    with g1:
        fig_g1 = px.sunburst(
            df_glob, path=['País', 'Sede'], values='Realizados',
            title="Distribución de Valoraciones Realizadas",
            color_discrete_sequence=['#00d4aa', '#7c6af7', '#c9a84c']
        )
        fig_g1.update_layout(**PLOT_CFG)
        st.plotly_chart(fig_g1, use_container_width=True)
    with g2:
        fig_g2 = px.bar(
            df_glob, x='Sede', y='% Conversión', color='País',
            title="% Conversión por Sede y País",
            color_discrete_map={'🇪🇸 España': '#00d4aa', '🇺🇸 USA': '#7c6af7'}
        )
        fig_g2.update_layout(**PLOT_CFG)
        st.plotly_chart(fig_g2, use_container_width=True)

    st.markdown("#### 📊 Resumen Consolidado Mayo 2026")
    total_ag  = df_glob['Agendados'].sum()
    total_re  = df_glob['Realizados'].sum()
    conv_glob = round(total_re / total_ag * 100, 1) if total_ag > 0 else 0

    r1, r2, r3 = st.columns(3)
    r1.metric("Total Agendados",  f"{total_ag:.1f}")
    r2.metric("Total Realizados", f"{total_re:.1f}")
    r3.metric("Conversión Global", f"{conv_glob}%")

    st.dataframe(
        df_glob[['País', 'Sede', 'Agendados', 'Realizados', '% Conversión']],
        use_container_width=True, hide_index=True
    )