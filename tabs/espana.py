import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import PLOT_CFG, PERIODO_LABEL
from data_loaders import cargar_españa


def render(ctx):
    st.markdown(f"### 🇪🇸 Ventas España — {PERIODO_LABEL}")
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
            fig_e2 = px.pie(df_e2, values='Realizados', names='Sede', hole=0.5, color_discrete_sequence=px.colors.sequential.Teal)
            fig_e2.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_e2, use_container_width=True)
        e3,e4 = st.columns(2)
        with e3:
            st.markdown("#### 📊 % Conversión por Sede")
            df_conv = df_esp[df_esp['Agendados']>0].copy()
            df_conv['% Conversión'] = pd.to_numeric(df_conv['% Conversión'], errors='coerce').fillna(0)
            if not df_conv.empty and df_conv['% Conversión'].sum() > 0:
                fig_e3 = px.bar(df_conv, x='Sede', y='% Conversión', color='% Conversión', color_continuous_scale='teal', text='% Conversión')
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
            fig_e4 = px.bar(df_leads_esp, x='Sede', y=['Leads WPP','Leads IG'], barmode='group', color_discrete_sequence=['#00d4aa','#7c6af7'])
            fig_e4.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_e4, use_container_width=True)
        st.markdown("---")
        st.dataframe(df_esp, use_container_width=True, hide_index=True)
