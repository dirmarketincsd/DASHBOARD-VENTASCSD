from datetime import timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import PLOT_CFG
from data_loaders import cargar_campanas


def render(ctx):
    hoy_ts     = ctx['hoy_ts']
    modo_fecha = ctx['modo_fecha']
    fecha_ini  = ctx['fecha_ini']
    fecha_fin  = ctx['fecha_fin']

    st.markdown("""
    <div style="margin-bottom:15px">
        <div style="color:#c9a84c;font-size:0.75rem;text-transform:uppercase;letter-spacing:2px;font-weight:700">Marketing & Analytics</div>
        <div style="color:#ffffff;font-size:1.6rem;font-weight:800">📢 Rendimiento de Campañas Meta Ads</div>
        <div style="color:#c9a84c;font-size:0.85rem">🇺🇸 USA · 🇪🇸 España · Datos reales desde Meta Ads · Valores en COP</div>
    </div>""", unsafe_allow_html=True)

    df_camp_raw = cargar_campanas()

    if df_camp_raw.empty:
        st.warning("⚠️ Sin datos de campañas. Verifica que el Google Sheet de Meta Ads sea público o esté compartido.")
    else:
        # Aplicar filtros del sidebar
        df_camp = df_camp_raw.copy()
        if 'Fecha' in df_camp.columns:
            if modo_fecha == "Día específico" and fecha_ini is not None:
                df_camp = df_camp[df_camp['Fecha'].dt.date == fecha_ini.date()]
            elif modo_fecha == "Rango de fechas" and fecha_ini is not None:
                df_camp = df_camp[(df_camp['Fecha'] >= fecha_ini) & (df_camp['Fecha'] <= fecha_fin)]

        def s_sum(df, col):
            return int(df[col].sum()) if not df.empty and col in df.columns else 0

        # KPIs — Hoy vs Ayer
        df_hoy_c  = df_camp_raw[df_camp_raw['Fecha'].dt.date == hoy_ts.date()] if 'Fecha' in df_camp_raw.columns else pd.DataFrame()
        df_ayer_c = df_camp_raw[df_camp_raw['Fecha'].dt.date == (hoy_ts - timedelta(days=1)).date()] if 'Fecha' in df_camp_raw.columns else pd.DataFrame()

        inv_hoy     = s_sum(df_hoy_c, 'Inversion')
        inv_ayer    = s_sum(df_ayer_c, 'Inversion')
        cont_hoy    = s_sum(df_hoy_c, 'Nuevos_Contactos')
        cont_ayer   = s_sum(df_ayer_c, 'Nuevos_Contactos')
        conv_hoy    = s_sum(df_hoy_c, 'Conversaciones')
        clicks_hoy  = s_sum(df_hoy_c, 'Clicks_Link')
        alcance_hoy = s_sum(df_hoy_c, 'Alcance')
        cpl_hoy     = round(inv_hoy / cont_hoy) if cont_hoy > 0 else 0

        k1,k2,k3,k4,k5,k6 = st.columns(6)
        k1.metric("💸 Inversión Hoy",    f"${inv_hoy:,.0f}",   delta=f"{inv_hoy-inv_ayer:+,.0f}" if inv_ayer else None)
        k2.metric("👥 Nuevos Contactos", cont_hoy,             delta=cont_hoy - cont_ayer if cont_ayer else None)
        k3.metric("💬 Conversaciones",   conv_hoy)
        k4.metric("🖱️ Link Clicks",      clicks_hoy)
        k5.metric("👁️ Alcance",          f"{alcance_hoy:,}")
        k6.metric("💰 CPL Hoy (COP)",    f"${cpl_hoy:,.0f}")

        st.markdown("---")

        # Por Campaña
        st.markdown("### 📊 Rendimiento por Campaña")
        if not df_camp.empty and 'Campaña' in df_camp.columns and 'País' in df_camp.columns:
            df_by_camp = df_camp.groupby(['Campaña','País']).agg(
                Inversión      = ('Inversion',       'sum'),
                Alcance        = ('Alcance',          'sum'),
                Clicks         = ('Clicks_Link',      'sum'),
                Conversaciones = ('Conversaciones',   'sum'),
                Contactos      = ('Nuevos_Contactos', 'sum'),
                Engagement     = ('Engagement',       'sum'),
                Días           = ('Fecha',            'nunique'),
            ).reset_index()
            df_by_camp['CPL'] = df_by_camp.apply(
                lambda r: round(r['Inversión'] / r['Contactos']) if r['Contactos'] > 0 else 0, axis=1
            )
            df_by_camp['CTR %'] = df_by_camp.apply(
                lambda r: round(r['Clicks'] / r['Alcance'] * 100, 2) if r['Alcance'] > 0 else 0, axis=1
            )
            df_by_camp = df_by_camp.sort_values('Contactos', ascending=False)

            c1, c2 = st.columns(2)
            with c1:
                fig_bc1 = go.Figure()
                fig_bc1.add_trace(go.Bar(name='Nuevos Contactos', x=df_by_camp['Campaña'], y=df_by_camp['Contactos'],      marker_color='#00d4aa'))
                fig_bc1.add_trace(go.Bar(name='Conversaciones',   x=df_by_camp['Campaña'], y=df_by_camp['Conversaciones'], marker_color='#7c6af7'))
                fig_bc1.update_layout(barmode='group', **PLOT_CFG, margin=dict(t=20,b=120,l=0,r=0), xaxis=dict(tickangle=-25))
                st.plotly_chart(fig_bc1, use_container_width=True)
            with c2:
                fig_bc2 = px.pie(
                    df_by_camp[df_by_camp['Inversión']>0],
                    values='Inversión', names='Campaña', hole=0.5,
                    color_discrete_sequence=['#7c6af7','#00d4aa','#c9a84c','#f7a76c','#ff6b6b','#5bc8ef']
                )
                fig_bc2.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
                st.plotly_chart(fig_bc2, use_container_width=True)

            st.dataframe(
                df_by_camp[['Campaña','País','Días','Inversión','Alcance','Clicks','Conversaciones','Contactos','CPL','CTR %','Engagement']],
                use_container_width=True, hide_index=True
            )

        st.markdown("---")

        # Por Sede / Ciudad
        st.markdown("### 📍 Rendimiento por Sede / Ciudad")
        if not df_camp.empty and 'Sede' in df_camp.columns and 'País' in df_camp.columns:
            df_by_sede = df_camp.groupby(['Sede','País']).agg(
                Inversión      = ('Inversion',       'sum'),
                Alcance        = ('Alcance',          'sum'),
                Clicks         = ('Clicks_Link',      'sum'),
                Conversaciones = ('Conversaciones',   'sum'),
                Contactos      = ('Nuevos_Contactos', 'sum'),
            ).reset_index()
            df_by_sede['CPL'] = df_by_sede.apply(
                lambda r: round(r['Inversión'] / r['Contactos']) if r['Contactos'] > 0 else 0, axis=1
            )
            df_by_sede = df_by_sede.sort_values('Contactos', ascending=False)

            s1, s2 = st.columns(2)
            with s1:
                st.markdown("#### 👥 Contactos por Sede")
                fig_s1 = px.bar(
                    df_by_sede, x='Sede', y='Contactos', color='País', text='Contactos',
                    color_discrete_map={'🇺🇸 USA':'#7c6af7','🇪🇸 España':'#00d4aa'}
                )
                fig_s1.update_traces(textposition='outside')
                fig_s1.update_layout(**PLOT_CFG, margin=dict(t=20,b=60,l=0,r=0))
                st.plotly_chart(fig_s1, use_container_width=True)
            with s2:
                st.markdown("#### 💰 CPL por Sede (COP)")
                df_cpl_s = df_by_sede[df_by_sede['CPL']>0].sort_values('CPL')
                fig_s2 = px.bar(
                    df_cpl_s, x='Sede', y='CPL',
                    color='CPL', color_continuous_scale='reds_r', text='CPL'
                )
                fig_s2.update_traces(texttemplate='$%{text:,.0f}')
                fig_s2.update_layout(coloraxis_showscale=False, **PLOT_CFG, margin=dict(t=20,b=60,l=0,r=0))
                st.plotly_chart(fig_s2, use_container_width=True)

            st.dataframe(df_by_sede, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Tendencia Diaria
        st.markdown("### 📈 Tendencia Diaria")
        if not df_camp_raw.empty and 'Fecha' in df_camp_raw.columns and 'Inversion' in df_camp_raw.columns:
            df_daily = df_camp_raw.groupby('Fecha').agg(
                Inversión      = ('Inversion',       'sum'),
                Contactos      = ('Nuevos_Contactos','sum'),
                Conversaciones = ('Conversaciones',  'sum'),
                Clicks         = ('Clicks_Link',     'sum'),
                Alcance        = ('Alcance',         'sum'),
            ).reset_index().sort_values('Fecha')
            df_daily['CPL'] = df_daily.apply(
                lambda r: round(r['Inversión']/r['Contactos']) if r['Contactos']>0 else 0, axis=1
            )

            d1, d2 = st.columns(2)
            with d1:
                st.markdown("#### 👥 Contactos y Conversaciones diarias")
                fig_d1 = go.Figure()
                fig_d1.add_trace(go.Scatter(x=df_daily['Fecha'], y=df_daily['Contactos'],
                    name='Nuevos Contactos', line=dict(color='#00d4aa', width=2), mode='lines+markers'))
                fig_d1.add_trace(go.Scatter(x=df_daily['Fecha'], y=df_daily['Conversaciones'],
                    name='Conversaciones', line=dict(color='#7c6af7', width=2), mode='lines+markers'))
                fig_d1.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
                st.plotly_chart(fig_d1, use_container_width=True)
            with d2:
                st.markdown("#### 💸 Inversión Diaria (COP)")
                fig_d2 = px.bar(df_daily, x='Fecha', y='Inversión',
                    color='Inversión', color_continuous_scale='teal')
                fig_d2.update_layout(coloraxis_showscale=False, **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
                st.plotly_chart(fig_d2, use_container_width=True)

            st.markdown("#### 💡 CPL Diario (COP)")
            fig_cpl = go.Figure()
            fig_cpl.add_trace(go.Scatter(
                x=df_daily['Fecha'], y=df_daily['CPL'],
                fill='tozeroy', line=dict(color='#c9a84c', width=2),
                name='CPL', mode='lines+markers'
            ))
            fig_cpl.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_cpl, use_container_width=True)

        st.markdown("---")
        st.caption("📌 Datos desde Google Sheet conectado a Meta Ads · Valores en pesos colombianos (COP) · Se actualiza cada 60 seg")
