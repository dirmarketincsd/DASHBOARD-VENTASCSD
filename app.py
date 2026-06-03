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
marca_b64 = None

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }

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
div[data-testid="stMetricDelta"] { color: #f0d080 !important; }

.card-meta {
    background: linear-gradient(135deg, #0d0d0d, #1a1500);
    border-radius: 14px; padding: 16px;
    border: 1px solid #c9a84c; margin-bottom: 10px;
    box-shadow: 0 4px 20px rgba(201,168,76,0.1);
}
.stTabs [data-baseweb="tab-list"] { gap: 8px; background: #0a0a0a; padding: 8px; border-radius: 12px; border: 1px solid #2a2000; }
.stTabs [data-baseweb="tab"] { background: #111100; border-radius: 8px; color: #c9a84c; padding: 8px 20px; font-weight: 600; border: 1px solid #2a2000; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, #c9a84c, #f0d080) !important; color: #000000 !important; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0a00, #111100) !important;
    border-right: 1px solid #c9a84c !important;
}
.header-bar {
    background: linear-gradient(90deg, #0a0a00, #1a1500);
    border-bottom: 2px solid #c9a84c;
    padding: 10px 0 20px 0;
    margin-bottom: 20px;
}
hr { border-color: #c9a84c !important; opacity: 0.3; }
</style>
""", unsafe_allow_html=True)

# ── CONFIG ────────────────────────────────────────────────────
SHEET_ID = "1-KjGMIPUGcMynGfTYM7P68E_k0ylcZYeg0Wmgwd-36Q"
META_DIARIA  = 5
META_SEMANAL = 25
META_MENSUAL = 150
PLOT_CFG = dict(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

@st.cache_data(ttl=180)
def cargar_hoja(nombre, skiprows=0):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre.replace(' ','%20')}"
        df = pd.read_csv(url, skiprows=skiprows)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=180)
def cargar_ventas_diarias():
    df = cargar_hoja("Ventas diarias", skiprows=1)
    if df.empty:
        return df
    rename = {}
    for col in df.columns:
        u = col.upper()
        if 'FECHA' in u:                             rename[col] = 'Fecha'
        elif 'SEMANA' in u:                          rename[col] = 'Semana'
        elif 'RESPONSABLE' in u:                     rename[col] = 'Responsable'
        elif 'VALORACION' in u:                      rename[col] = 'Valoraciones'
        elif 'WPP' in u:                             rename[col] = 'Leads WPP'
        elif 'IG' in u or 'INSTAGRAM' in u:          rename[col] = 'Leads IG'
        elif 'SEDE' in u:                            rename[col] = 'Sede'
        elif 'CIERRE' in u or 'AGENDADO' in u:       rename[col] = 'Cierres'
        elif 'SIGUIENTE' in u:                       rename[col] = 'Venta Dia Siguiente'
        elif 'SEMANAL' in u and 'DIARIA' not in u:   rename[col] = 'Venta Semanal'
        elif 'DIARIA' in u:                          rename[col] = 'Venta Diaria'
        elif 'META' in u:                            rename[col] = 'Meta Mensual'
    df = df.rename(columns=rename)
    if 'Responsable' in df.columns:
        df = df[df['Responsable'].notna()]
        df = df[~df['Responsable'].astype(str).str.strip().isin(['','nan'])]
    if 'Fecha' in df.columns:
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
    for col in ['Valoraciones','Leads WPP','Leads IG','Cierres','Venta Dia Siguiente','Venta Semanal','Venta Diaria']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    if logo_b64:
        st.markdown(f'<div style="text-align:center;padding:16px 0 8px 0"><img src="data:image/png;base64,{logo_b64}" style="width:180px;border-radius:8px"></div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#c9a84c;font-size:0.7rem;text-transform:uppercase;letter-spacing:2px;text-align:center;margin-bottom:10px">Panel de Control</div>', unsafe_allow_html=True)
    st.markdown("---")
    periodo = st.selectbox("📅 Período", ["Hoy","Ayer","Esta semana","Este mes","Personalizado"])
    hoy = pd.Timestamp(date.today())
    if periodo == "Hoy":
        f_ini, f_fin = hoy, hoy
    elif periodo == "Ayer":
        f_ini = f_fin = hoy - timedelta(days=1)
    elif periodo == "Esta semana":
        f_ini = hoy - timedelta(days=hoy.weekday()); f_fin = hoy
    elif periodo == "Este mes":
        f_ini = hoy.replace(day=1); f_fin = hoy
    else:
        f_ini = pd.Timestamp(st.date_input("Desde", value=date.today()-timedelta(days=7)))
        f_fin = pd.Timestamp(st.date_input("Hasta", value=date.today()))
    st.markdown("---")
    if st.button("🔄 Actualizar datos"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Se actualiza cada 3 min")

# ── HEADER ────────────────────────────────────────────────────
col_logo, col_title, col_marca = st.columns([1.2, 2.5, 1.2])
with col_logo:
    if logo_b64:
        st.markdown(f'<img src="data:image/png;base64,{logo_b64}" style="width:200px;margin-top:10px;border-radius:8px">', unsafe_allow_html=True)
    else:
        st.markdown("### 🦷 CSD")
with col_title:
    st.markdown("""
    <div style="padding-top:15px;text-align:center">
        <div style="color:#c9a84c;font-size:0.8rem;text-transform:uppercase;letter-spacing:3px">Dashboard Comercial</div>
        <div style="color:#ffffff;font-size:2rem;font-weight:800;line-height:1.2">Reporte de Ventas</div>
        <div style="color:#c9a84c;font-size:0.85rem">España 🇪🇸 · USA 🇺🇸 · Seguimiento en tiempo real</div>
    </div>""", unsafe_allow_html=True)
with col_marca:
    if marca_b64:
        st.markdown(f'<div style="text-align:right;padding-top:10px"><img src="data:image/png;base64,{marca_b64}" style="width:180px;border-radius:8px;opacity:0.9"></div>', unsafe_allow_html=True)
st.markdown(f'<div style="color:#8b8b6b;font-size:0.8rem;margin-top:8px">📅 Hoy: {date.today().strftime("%d de %B de %Y")} · Período seleccionado: {periodo}</div>', unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Ventas Diarias","🎯 Metas","🇪🇸 España","🇺🇸 USA","📊 Global"])

# ══ TAB 1 — VENTAS DIARIAS ══
with tab1:
    st.markdown("### 📋 Reporte de Ventas Diarias")
    try:
        df = cargar_ventas_diarias()

        # ── Selector de semana ──
        hoy_t1 = pd.Timestamp(date.today())
        inicio_sem_t1 = hoy_t1 - timedelta(days=hoy_t1.weekday())
        fin_sem_t1    = inicio_sem_t1 + timedelta(days=6)
        inicio_sem_ant = inicio_sem_t1 - timedelta(days=7)
        fin_sem_ant    = inicio_sem_t1 - timedelta(days=1)

        col_sw1, col_sw2 = st.columns([2,1])
        with col_sw1:
            semana_sel = st.radio("📅 Semana a visualizar", ["Esta semana", "Semana anterior"], horizontal=True)
        with col_sw2:
            if st.button("🔄 Refrescar"):
                st.cache_data.clear(); st.rerun()

        if semana_sel == "Esta semana":
            sem_ini  = pd.Timestamp(inicio_sem_t1)
            sem_fin  = pd.Timestamp(fin_sem_t1)
            sem_ant_ini = pd.Timestamp(inicio_sem_ant)
            sem_ant_fin = pd.Timestamp(fin_sem_ant)
            label_sem = f"{sem_ini.strftime('%d/%m')} — {sem_fin.strftime('%d/%m/%Y')}"
        else:
            sem_ini  = pd.Timestamp(inicio_sem_ant)
            sem_fin  = pd.Timestamp(fin_sem_ant)
            sem_ant_ini = pd.Timestamp(inicio_sem_ant - timedelta(days=7))
            sem_ant_fin = pd.Timestamp(inicio_sem_ant - timedelta(days=1))
            label_sem = f"{sem_ini.strftime('%d/%m')} — {sem_fin.strftime('%d/%m/%Y')}"

        st.markdown(f"<div style='color:#c9a84c;font-size:0.85rem;margin-bottom:12px'>📆 Semana: <b>{label_sem}</b></div>", unsafe_allow_html=True)

        DIAS = ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom']
        METRICAS = ['Cierres','Valoraciones','Leads WPP','Leads IG','Venta Diaria']
        COLORES  = {'Cierres':'#00d4aa','Valoraciones':'#f0d080','Leads WPP':'#7c6af7','Leads IG':'#f7a76c','Venta Diaria':'#4fc3f7'}
        ICONOS   = {'Cierres':'🏆','Valoraciones':'⭐','Leads WPP':'💬','Leads IG':'📸','Venta Diaria':'💰'}

        def build_semana(df_src, sem_ini, sem_fin):
            dias = pd.date_range(sem_ini, sem_fin, freq='D')
            rows = []
            for d in dias:
                fila = {'Fecha': d, 'Dia': DIAS[d.weekday() % 7]}
                try:
                    if df_src is not None and not df_src.empty and 'Fecha' in df_src.columns:
                        sub = df_src[df_src['Fecha'] == d]
                    else:
                        sub = pd.DataFrame()
                    for m in METRICAS:
                        fila[m] = float(sub[m].sum()) if (not sub.empty and m in sub.columns) else 0.0
                except Exception:
                    for m in METRICAS:
                        fila[m] = 0.0
                rows.append(fila)
            return pd.DataFrame(rows)

        def render_grupo(titulo, bandera, sedes_grupo, color_header):
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#0d0d0d,#1a1500);border:1px solid #c9a84c;
                        border-radius:14px;padding:16px 20px;margin-bottom:6px">
                <div style="color:{color_header};font-size:1.1rem;font-weight:800;letter-spacing:1px">
                    {bandera} {titulo}
                </div>
            </div>""", unsafe_allow_html=True)

            if not df.empty and 'Sede' in df.columns:
                mask = df['Sede'].astype(str).str.strip().isin(sedes_grupo)
                df_grupo = df[mask].copy()
            else:
                df_grupo = df.copy()

            df_sem_g   = build_semana(df_grupo, sem_ini, sem_fin)
            df_ant_g   = build_semana(df_grupo, sem_ant_ini, sem_ant_fin)
            totales    = {m: df_sem_g[m].sum() for m in METRICAS}
            totales_ant= {m: df_ant_g[m].sum() for m in METRICAS}

            cols_k = st.columns(5)
            for i, m in enumerate(METRICAS):
                val = totales[m]; ant = totales_ant[m]
                delta = val - ant
                fmt = f"${val:,.0f}" if m == 'Venta Diaria' else f"{int(val)}"
                delta_fmt = f"{'+'if delta>=0 else ''}{int(delta)}" if m != 'Venta Diaria' else f"{'+'if delta>=0 else ''}${delta:,.0f}"
                cols_k[i].metric(f"{ICONOS[m]} {m}", fmt, delta_fmt)

            st.markdown("---")

            st.markdown("##### 📅 Detalle por día")
            header_cols = st.columns([2] + [1]*7 + [1])
            header_cols[0].markdown("<div style='color:#c9a84c;font-size:0.75rem;font-weight:700'>MÉTRICA</div>", unsafe_allow_html=True)
            for i, dia in enumerate(DIAS):
                fecha_dia = sem_ini + timedelta(days=i)
                es_hoy = fecha_dia.date() == date.today()
                estilo = "color:#00d4aa;font-weight:800" if es_hoy else "color:#8b9bb4"
                header_cols[i+1].markdown(f"<div style='{estilo};font-size:0.75rem;text-align:center'>{dia}<br>{fecha_dia.strftime('%d/%m')}</div>", unsafe_allow_html=True)
            header_cols[-1].markdown("<div style='color:#c9a84c;font-size:0.75rem;font-weight:700;text-align:center'>TOTAL</div>", unsafe_allow_html=True)

            for m in METRICAS:
                row_cols = st.columns([2] + [1]*7 + [1])
                row_cols[0].markdown(f"<div style='color:{COLORES[m]};font-size:0.78rem;font-weight:600;padding:6px 0'>{m}</div>", unsafe_allow_html=True)
                total_m = 0
                for i in range(7):
                    val = df_sem_g.iloc[i][m]
                    ant_val = df_ant_g.iloc[i][m]
                    total_m += val
                    fecha_dia = sem_ini + timedelta(days=i)
                    es_hoy = fecha_dia.date() == date.today()
                    bg = "rgba(0,212,170,0.08)" if es_hoy else "transparent"
                    if val > 0 and ant_val > 0:
                        if val > ant_val: ind = "🔼"
                        elif val < ant_val: ind = "🔽"
                        else: ind = "➡️"
                    else:
                        ind = ""
                    fmt_val = f"${val:,.0f}" if m == 'Venta Diaria' else f"{int(val)}" if val > 0 else "—"
                    row_cols[i+1].markdown(
                        f"<div style='text-align:center;background:{bg};border-radius:6px;padding:4px 2px;"
                        f"font-size:0.82rem;color:white'>{fmt_val} {ind}</div>",
                        unsafe_allow_html=True)
                fmt_total = f"${total_m:,.0f}" if m == 'Venta Diaria' else f"{int(total_m)}"
                ant_total = totales_ant[m]
                delta_t = total_m - ant_total
                color_t = "#00d4aa" if delta_t >= 0 else "#ff6b6b"
                row_cols[-1].markdown(
                    f"<div style='text-align:center;color:{color_t};font-weight:700;font-size:0.85rem;padding:4px 0'>{fmt_total}</div>",
                    unsafe_allow_html=True)

            st.markdown("##### 🎯 Comparativo vs Meta Semanal")
            meta_cols = st.columns(5)
            metas_sem = {'Cierres': META_SEMANAL, 'Valoraciones': META_SEMANAL,
                         'Leads WPP': 50, 'Leads IG': 100, 'Venta Diaria': 0}
            for i, m in enumerate(METRICAS):
                meta = metas_sem[m]
                if meta > 0:
                    val = totales[m]
                    p = min(round(val / meta * 100, 1), 100)
                    color = "#00d4aa" if p >= 100 else "#f7a76c" if p >= 50 else "#ff6b6b"
                    meta_cols[i].markdown(f"""
                    <div style="background:#0d0d0d;border:1px solid #2a2000;border-radius:10px;padding:10px;text-align:center">
                        <div style="color:#8b9bb4;font-size:0.7rem">{m}</div>
                        <div style="color:{color};font-weight:700;font-size:1rem">{p}%</div>
                        <div style="background:#1e2340;border-radius:6px;height:8px;margin-top:4px">
                            <div style="height:8px;border-radius:6px;background:{color};width:{p}%"></div>
                        </div>
                        <div style="color:#8b9bb4;font-size:0.65rem;margin-top:3px">{int(val)} / {meta}</div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

        SEDES_ESP = ['Alicante','Barcelona','Valencia','Madrid','Malaga','Bilbao']
        render_grupo("ESPAÑA", "🇪🇸", SEDES_ESP, "#00d4aa")

        st.markdown("<br>", unsafe_allow_html=True)

        SEDES_USA = ['Dallas','Houston','New Jersey','Orlando','Los Angeles']
        render_grupo("USA", "🇺🇸", SEDES_USA, "#7c6af7")

        if not df.empty:
            st.markdown("---")
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Descargar CSV completo", data=csv, file_name=f"ventas_{date.today()}.csv", mime="text/csv")

    except Exception as e:
        st.error(f"❌ Error: {e}")

# ══ TAB 2 — METAS ══
with tab2:
    st.markdown("### 🎯 Control de Metas")
    try:
        df = cargar_ventas_diarias()
        responsables = df['Responsable'].dropna().unique().tolist() if 'Responsable' in df.columns and not df.empty else []
        n = max(len(responsables), 1)

        hoy_ts = pd.Timestamp(date.today())
        inicio_mes = hoy_ts.replace(day=1)
        inicio_sem = hoy_ts - timedelta(days=hoy_ts.weekday())

        df_hoy = df[df['Fecha'] == hoy_ts]    if 'Fecha' in df.columns and not df.empty else pd.DataFrame()
        df_sem = df[df['Fecha'] >= inicio_sem] if 'Fecha' in df.columns and not df.empty else pd.DataFrame()
        df_mes = df[df['Fecha'] >= inicio_mes] if 'Fecha' in df.columns and not df.empty else pd.DataFrame()

        def gc(d): return int(d['Cierres'].sum()) if 'Cierres' in d.columns and not d.empty else 0

        c_hoy = gc(df_hoy); c_sem = gc(df_sem); c_mes = gc(df_mes)
        m_dia = META_DIARIA * n; m_sem = META_SEMANAL * n; m_mes = META_MENSUAL * n

        st.markdown(f"**Equipo:** {n} persona(s) · **Meta:** {META_DIARIA} cierres/día por persona")
        st.markdown("---")

        def tarjeta(titulo, actual, meta, emoji):
            p = min(round(actual / meta * 100, 1) if meta > 0 else 0, 100)
            color = "#00d4aa" if p >= 100 else "#f7a76c" if p >= 50 else "#ff6b6b"
            faltan = max(meta - actual, 0)
            st.markdown(f"""
            <div class="card-meta">
                <div style="color:#8b9bb4;font-size:0.75rem;text-transform:uppercase;letter-spacing:1px">{emoji} {titulo}</div>
                <div style="color:white;font-size:2.2rem;font-weight:800">{actual} <span style="color:#8b9bb4;font-size:1rem">/ {meta}</span></div>
                <div style="color:{color};font-size:0.95rem;font-weight:600">{p}% completado</div>
                <div style="background:#1e2340;border-radius:10px;height:12px;width:100%;margin:8px 0">
                    <div style="height:12px;border-radius:10px;background:{color};width:{p}%"></div>
                </div>
                <div style="color:#ff6b6b;font-size:0.85rem">Faltan: <b>{faltan}</b> cierres</div>
            </div>""", unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        with m1: tarjeta("Meta Diaria",  c_hoy, m_dia, "📅")
        with m2: tarjeta("Meta Semanal", c_sem, m_sem, "📆")
        with m3: tarjeta("Meta Mensual", c_mes, m_mes, "🗓️")

        st.markdown("---")
        st.markdown("#### 🏁 ¿Quién está más cerca de la meta de HOY?")
        if not df_hoy.empty and 'Responsable' in df_hoy.columns and 'Cierres' in df_hoy.columns:
            df_hoy_rank = df_hoy.groupby('Responsable')['Cierres'].sum().reset_index()
            df_hoy_rank['% Meta Diaria'] = (df_hoy_rank['Cierres'] / META_DIARIA * 100).round(1).clip(upper=100)
            df_hoy_rank = df_hoy_rank.sort_values('% Meta Diaria', ascending=False)

            for _, row in df_hoy_rank.iterrows():
                p = row['% Meta Diaria']
                cierres = int(row['Cierres'])
                nombre = row['Responsable']
                faltan = max(META_DIARIA - cierres, 0)
                if p >= 100:
                    color = "#00d4aa"
                    estado = "✅ ¡Meta cumplida!"
                elif p >= 60:
                    color = "#f7a76c"
                    estado = f"🔥 Faltan {faltan} cierres"
                else:
                    color = "#ff6b6b"
                    estado = f"⚡ Faltan {faltan} cierres"

                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#0d0d0d,#1a1500);border:1px solid #2a2000;
                            border-radius:12px;padding:14px 18px;margin-bottom:10px">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                        <div style="color:white;font-weight:700;font-size:1rem">👤 {nombre}</div>
                        <div style="color:{color};font-weight:600;font-size:0.9rem">{estado}</div>
                    </div>
                    <div style="display:flex;align-items:center;gap:12px">
                        <div style="flex:1;background:#1e2340;border-radius:10px;height:14px">
                            <div style="height:14px;border-radius:10px;background:{color};width:{p}%;
                                        transition:width 0.5s ease"></div>
                        </div>
                        <div style="color:#c9a84c;font-size:0.85rem;font-weight:700;min-width:80px;text-align:right">
                            {cierres} / {META_DIARIA} · {p}%
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("📝 Aún no hay datos de cierres para hoy.")

        st.markdown("---")
        st.markdown("#### 🏆 Ranking de Comerciales — Mes Actual")
        if not df_mes.empty and 'Responsable' in df_mes.columns and 'Cierres' in df_mes.columns:
            df_rank = df_mes.groupby('Responsable')['Cierres'].sum().reset_index()
            df_rank['Meta'] = META_MENSUAL
            df_rank['% Cumplimiento'] = (df_rank['Cierres'] / META_MENSUAL * 100).round(1)
            df_rank['Faltan'] = (META_MENSUAL - df_rank['Cierres']).clip(lower=0)
            df_rank = df_rank.sort_values('Cierres', ascending=False)
            fig_rank = go.Figure()
            fig_rank.add_trace(go.Bar(name='Cierres', x=df_rank['Responsable'], y=df_rank['Cierres'], marker_color='#00d4aa'))
            fig_rank.add_trace(go.Bar(name='Meta', x=df_rank['Responsable'], y=df_rank['Meta'], marker_color='rgba(124,106,247,0.35)'))
            fig_rank.update_layout(barmode='overlay', **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_rank, use_container_width=True)
            st.dataframe(df_rank, use_container_width=True, hide_index=True)
        else:
            st.info("📝 Ingresa datos en 'Ventas diarias' para ver el ranking.")
    except Exception as e:
        st.error(f"❌ Error: {e}")

# ══ TAB 3 — ESPAÑA ══
with tab3:
    st.markdown("### 🇪🇸 Ventas España — Mayo 2026")
    try:
        df_esp_real = pd.DataFrame({
            'Sede': ['Alicante','Barcelona','Valencia','Madrid','Malaga','Bilbao'],
            'Agendados': [10, 13.5, 6, 5.5, 20.5, 0],
            'Realizados': [7, 12.5, 2, 4.5, 10.5, 2.5],
        })
        df_esp_real['% Conversión'] = (df_esp_real['Realizados'] / df_esp_real['Agendados'] * 100).round(1)
        df_esp_real['% Conversión'] = df_esp_real['% Conversión'].fillna(0)

        total_ag_e = df_esp_real['Agendados'].sum()
        total_re_e = df_esp_real['Realizados'].sum()
        conv_e = round(total_re_e / total_ag_e * 100, 1) if total_ag_e > 0 else 0

        ke1, ke2, ke3, ke4 = st.columns(4)
        ke1.metric("📍 Sedes", 6)
        ke2.metric("📅 Agendados", f"{total_ag_e:.1f}")
        ke3.metric("✅ Realizados", f"{total_re_e:.1f}")
        ke4.metric("📊 Conversión", f"{conv_e}%")

        st.markdown("---")
        e1, e2 = st.columns(2)
        with e1:
            st.markdown("#### 📍 Agendados vs Realizados por Sede")
            fig_e1 = go.Figure()
            fig_e1.add_trace(go.Bar(name='Agendados', x=df_esp_real['Sede'], y=df_esp_real['Agendados'], marker_color='#7c6af7'))
            fig_e1.add_trace(go.Bar(name='Realizados', x=df_esp_real['Sede'], y=df_esp_real['Realizados'], marker_color='#00d4aa'))
            fig_e1.update_layout(barmode='group', **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_e1, use_container_width=True)
        with e2:
            st.markdown("#### 🍩 Distribución Realizados")
            df_e2 = df_esp_real[df_esp_real['Realizados'] > 0]
            fig_e2 = px.pie(df_e2, values='Realizados', names='Sede', hole=0.5,
                            color_discrete_sequence=px.colors.sequential.Teal)
            fig_e2.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_e2, use_container_width=True)

        e3, e4 = st.columns(2)
        with e3:
            st.markdown("#### 📊 % Conversión por Sede")
            df_conv = df_esp_real[df_esp_real['Agendados'] > 0]
            fig_e3 = px.bar(df_conv, x='Sede', y='% Conversión',
                            color='% Conversión', color_continuous_scale='teal',
                            text='% Conversión')
            fig_e3.update_traces(texttemplate='%{text}%')
            fig_e3.update_layout(coloraxis_showscale=False, **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_e3, use_container_width=True)
        with e4:
            st.markdown("#### 👤 Realizados por Comercial")
            df_com_esp = pd.DataFrame({
                'Comercial': ['Evelyn','Comercial 2','Administrador'],
                'Realizados': [15, 9, 15.5]
            })
            fig_e4 = px.bar(df_com_esp, x='Comercial', y='Realizados',
                            color='Realizados', color_continuous_scale='purples')
            fig_e4.update_layout(coloraxis_showscale=False, **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_e4, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 📋 Resumen España Mayo 2026")
        st.dataframe(df_esp_real, use_container_width=True, hide_index=True)

        st.markdown("#### 💬 Leads por Sede — España")
        df_leads_esp = pd.DataFrame({
            'Sede': ['Alicante','Barcelona','Valencia','Madrid','Malaga','Bilbao'],
            'Leads WPP': [27, 31, 18, 39, 43, 21],
            'Leads IG': [37, 144, 39, 214, 99, 0]
        })
        df_leads_esp['Total'] = df_leads_esp['Leads WPP'] + df_leads_esp['Leads IG']
        fig_leads = px.bar(df_leads_esp, x='Sede', y=['Leads WPP','Leads IG'],
                           barmode='group', color_discrete_sequence=['#00d4aa','#7c6af7'])
        fig_leads.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
        st.plotly_chart(fig_leads, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error España: {e}")

# ══ TAB 4 — USA ══
with tab4:
    st.markdown("### 🇺🇸 Ventas USA — Mayo 2026")
    try:
        df_usa_real = pd.DataFrame({
            'Sede': ['Dallas','Houston','New Jersey','Orlando','Los Angeles'],
            'Agendados': [8.5, 4, 6.5, 3.5, 11.5],
            'Realizados': [6.5, 7.5, 4.5, 4.5, 13.5],
        })
        df_usa_real['% Conversión'] = (df_usa_real['Realizados'] / df_usa_real['Agendados'] * 100).round(1)

        total_ag_u = df_usa_real['Agendados'].sum()
        total_re_u = df_usa_real['Realizados'].sum()
        conv_u = round(total_re_u / total_ag_u * 100, 1) if total_ag_u > 0 else 0

        ku1, ku2, ku3, ku4 = st.columns(4)
        ku1.metric("📍 Sedes", 5)
        ku2.metric("📅 Agendados", f"{total_ag_u:.1f}")
        ku3.metric("✅ Realizados", f"{total_re_u:.1f}")
        ku4.metric("📊 Conversión", f"{conv_u}%")

        st.markdown("---")
        u1, u2 = st.columns(2)
        with u1:
            st.markdown("#### 📍 Agendados vs Realizados por Sede")
            fig_u1 = go.Figure()
            fig_u1.add_trace(go.Bar(name='Agendados', x=df_usa_real['Sede'], y=df_usa_real['Agendados'], marker_color='#7c6af7'))
            fig_u1.add_trace(go.Bar(name='Realizados', x=df_usa_real['Sede'], y=df_usa_real['Realizados'], marker_color='#00d4aa'))
            fig_u1.update_layout(barmode='group', **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_u1, use_container_width=True)
        with u2:
            st.markdown("#### 🍩 Distribución Realizados")
            fig_u2 = px.pie(df_usa_real, values='Realizados', names='Sede', hole=0.5,
                            color_discrete_sequence=px.colors.sequential.Purples)
            fig_u2.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_u2, use_container_width=True)

        u3, u4 = st.columns(2)
        with u3:
            st.markdown("#### 📊 % Conversión por Sede")
            fig_u3 = px.bar(df_usa_real, x='Sede', y='% Conversión',
                            color='% Conversión', color_continuous_scale='purples',
                            text='% Conversión')
            fig_u3.update_traces(texttemplate='%{text}%')
            fig_u3.update_layout(coloraxis_showscale=False, **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_u3, use_container_width=True)
        with u4:
            st.markdown("#### 👤 Realizados por Comercial")
            df_com_usa = pd.DataFrame({
                'Comercial': ['Comercial 1','Comercial 2','Administrador'],
                'Realizados': [17, 1, 15.5]
            })
            fig_u4 = px.bar(df_com_usa, x='Comercial', y='Realizados',
                            color='Realizados', color_continuous_scale='teal')
            fig_u4.update_layout(coloraxis_showscale=False, **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_u4, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 📋 Resumen USA Mayo 2026")
        st.dataframe(df_usa_real, use_container_width=True, hide_index=True)

        st.markdown("#### 💬 Leads por Sede — USA")
        df_leads_usa = pd.DataFrame({
            'Sede': ['Dallas','Houston','New Jersey','Orlando','Los Angeles'],
            'Leads WPP+IG': [277.4, 296.4, 343.4, 214.4, 318.4]
        })
        fig_leads_u = px.bar(df_leads_usa, x='Sede', y='Leads WPP+IG',
                             color='Leads WPP+IG', color_continuous_scale='purples')
        fig_leads_u.update_layout(coloraxis_showscale=False, **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
        st.plotly_chart(fig_leads_u, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error USA: {e}")

# ══ TAB 5 — GLOBAL ══
with tab5:
    st.markdown("### 📊 Resumen Global — Mayo 2026")
    try:
        df_esp_g = pd.DataFrame({
            'Sede': ['Alicante','Barcelona','Valencia','Madrid','Malaga','Bilbao'],
            'País': ['🇪🇸 España']*6,
            'Agendados': [10, 13.5, 6, 5.5, 20.5, 0],
            'Realizados': [7, 12.5, 2, 4.5, 10.5, 2.5],
        })
        df_usa_g = pd.DataFrame({
            'Sede': ['Dallas','Houston','New Jersey','Orlando','Los Angeles'],
            'País': ['🇺🇸 USA']*5,
            'Agendados': [8.5, 4, 6.5, 3.5, 11.5],
            'Realizados': [6.5, 7.5, 4.5, 4.5, 13.5],
        })
        df_global = pd.concat([df_esp_g, df_usa_g], ignore_index=True)
        df_global['% Conversión'] = (df_global['Realizados'] / df_global['Agendados'] * 100).round(1).fillna(0)
        df_global['% Conversión'] = df_global['% Conversión'].replace([float('inf'), float('-inf')], 0)

        total_ag = df_global['Agendados'].sum()
        total_re = df_global['Realizados'].sum()
        total_e  = df_esp_g['Realizados'].sum()
        total_u  = df_usa_g['Realizados'].sum()
        conv_g   = round(total_re / total_ag * 100, 1) if total_ag > 0 else 0

        g1, g2, g3, g4, g5 = st.columns(5)
        g1.metric("🌍 Total Sedes",    11)
        g2.metric("📅 Total Agendados",f"{total_ag:.1f}")
        g3.metric("✅ Total Realizados",f"{total_re:.1f}")
        g4.metric("🇪🇸 España",        f"{total_e:.1f}")
        g5.metric("🇺🇸 USA",           f"{total_u:.1f}")

        st.markdown("---")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("#### 📊 Realizados por Sede — Global")
            df_global_sorted = df_global.sort_values(by='Realizados', ascending=False)
            fig_all = px.bar(
                df_global_sorted, 
                x='Sede', 
                y='Realizados',
                color='País',
                color_discrete_map={'🇪🇸 España': '#00d4aa', '🇺🇸 USA': '#7c6af7'},
                text='Realizados'
            )
            fig_all.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_all, use_container_width=True)
            
        with col_g2:
            st.markdown("#### 🍩 Proporción Global por País")
            fig_pie_g = px.pie(
                df_global, 
                values='Realizados', 
                names='País', 
                hole=0.5,
                color='País',
                color_discrete_map={'🇪🇸 España': '#00d4aa', '🇺🇸 USA': '#7c6af7'}
            )
            fig_pie_g.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_pie_g, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 📋 Consolidado General de Sedes")
        st.dataframe(df_global, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"❌ Error Global: {e}")