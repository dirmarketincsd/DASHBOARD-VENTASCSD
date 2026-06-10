import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import PLOT_CFG, PERIODO_LABEL
from data_loaders import cargar_usa


def render(ctx):
    st.markdown(f"### 🇺🇸 Ventas USA — {PERIODO_LABEL}")
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
            fig_u2 = px.pie(df_usa, values='Realizados', names='Sede', hole=0.5, color_discrete_sequence=px.colors.sequential.Purples)
            fig_u2.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_u2, use_container_width=True)
        u3,u4 = st.columns(2)
        with u3:
            st.markdown("#### 📊 % Conversión por Sede")
            df_usa_conv = df_usa[df_usa['Agendados']>0].copy()
            df_usa_conv['% Conversión'] = pd.to_numeric(df_usa_conv['% Conversión'], errors='coerce').fillna(0)
            if not df_usa_conv.empty and df_usa_conv['% Conversión'].sum() > 0:
                fig_u3 = px.bar(df_usa_conv, x='Sede', y='% Conversión', color='% Conversión', color_continuous_scale='purples', text='% Conversión')
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
            fig_u4 = px.bar(df_leads_usa, x='Sede', y='Leads WPP+IG', color='Leads WPP+IG', color_continuous_scale='purples')
            fig_u4.update_layout(coloraxis_showscale=False, **PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_u4, use_container_width=True)
        st.markdown("---")
        st.dataframe(df_usa, use_container_width=True, hide_index=True)
