import pandas as pd
import plotly.express as px
import streamlit as st

from config import EQUIPOS_BASE, PLOT_CFG, META_DIARIA, META_SEMANAL, META_MENSUAL
from data_loaders import cargar_ventas_diarias


def render(ctx):
    hoy_ts     = ctx['hoy_ts']
    inicio_sem = ctx['inicio_sem']
    inicio_mes = ctx['inicio_mes']

    st.markdown("### 🎯 Control de Metas")
    try:
        df_m = cargar_ventas_diarias()
        if df_m.empty:
            st.info("📝 Sin datos aún.")
        else:
            def filtrar_periodo(df_src, grupo=None):
                d = df_src.copy()
                if grupo and 'Grupo_Pais' in d.columns:
                    d = d[d['Grupo_Pais'] == grupo]
                return d

            def get_cierres(df_src, desde=None, hasta=None):
                d = df_src.copy()
                if 'Fecha' in d.columns:
                    if desde is not None: d = d[d['Fecha'].dt.date >= desde]
                    if hasta is not None: d = d[d['Fecha'].dt.date <= hasta]
                if 'Cierres' not in d.columns or d.empty: return 0
                return int(pd.to_numeric(d['Cierres'], errors='coerce').fillna(0).sum())

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
                        p      = min(round(row['Cierres']/META_DIARIA*100, 1), 100)
                        c      = int(row['Cierres'])
                        nombre = row['Responsable']
                        faltan = max(META_DIARIA - c, 0)
                        color  = "#00d4aa" if p >= 100 else "#f7a76c" if p >= 60 else "#ff6b6b"
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

            st.markdown("""<div style="background:linear-gradient(135deg,#0d0d0d,#1a1500);border:1px solid #00d4aa;
                border-radius:14px;padding:12px 20px;margin-bottom:12px">
                <span style="color:#00d4aa;font-size:1.1rem;font-weight:800">🇪🇸 GRUPO ESPAÑA</span>
                <span style="color:#8b9bb4;font-size:0.8rem;margin-left:12px">{} asesor(es): {}</span>
            </div>""".format(n_esp, ', '.join(asesores_esp) if asesores_esp else 'Sin datos'), unsafe_allow_html=True)
            ec1, ec2, ec3 = st.columns(3)
            with ec1: tarjeta_meta("Depósitos Hoy",    get_cierres(df_esp_m, hoy_date, hoy_date),           META_DIARIA*n_esp,  "📅", "#00d4aa")
            with ec2: tarjeta_meta("Depósitos Semana", get_cierres(df_esp_m, inicio_sem.date(), hoy_date),  META_SEMANAL*n_esp, "📆", "#00d4aa")
            with ec3: tarjeta_meta("Depósitos Mes",    get_cierres(df_esp_m, inicio_mes.date(), hoy_date),  META_MENSUAL*n_esp, "🗓️", "#00d4aa")
            barras_asesor(df_esp_m, "Progreso de HOY — España", "#00d4aa")

            st.markdown("---")

            st.markdown("""<div style="background:linear-gradient(135deg,#0d0d0d,#1a1500);border:1px solid #7c6af7;
                border-radius:14px;padding:12px 20px;margin-bottom:12px">
                <span style="color:#7c6af7;font-size:1.1rem;font-weight:800">🇺🇸 GRUPO USA</span>
                <span style="color:#8b9bb4;font-size:0.8rem;margin-left:12px">{} asesor(es): {}</span>
            </div>""".format(n_usa, ', '.join(asesores_usa) if asesores_usa else 'Sin datos'), unsafe_allow_html=True)
            uc1, uc2, uc3 = st.columns(3)
            with uc1: tarjeta_meta("Depósitos Hoy",    get_cierres(df_usa_m, hoy_date, hoy_date),           META_DIARIA*n_usa,  "📅", "#7c6af7")
            with uc2: tarjeta_meta("Depósitos Semana", get_cierres(df_usa_m, inicio_sem.date(), hoy_date),  META_SEMANAL*n_usa, "📆", "#7c6af7")
            with uc3: tarjeta_meta("Depósitos Mes",    get_cierres(df_usa_m, inicio_mes.date(), hoy_date),  META_MENSUAL*n_usa, "🗓️", "#7c6af7")
            barras_asesor(df_usa_m, "Progreso de HOY — USA", "#7c6af7")

            st.markdown("---")

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
                fig_rank = px.bar(df_rank, x='Responsable', y='Depósitos', color='Grupo', color_discrete_map=color_map)
                fig_rank.add_hline(y=META_MENSUAL, line_dash='dash', line_color='#c9a84c', annotation_text=f'Meta {META_MENSUAL}')
                fig_rank.update_layout(**PLOT_CFG, margin=dict(t=30,b=0,l=0,r=0))
                st.plotly_chart(fig_rank, use_container_width=True)
                st.dataframe(df_rank, use_container_width=True, hide_index=True)
            else:
                st.info("📝 Sin datos del mes actual.")
    except Exception as e:
        st.error(f"❌ Error Metas: {e}")
