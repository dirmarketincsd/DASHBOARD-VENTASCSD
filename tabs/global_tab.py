import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import PLOT_CFG, PERIODO_LABEL
from data_loaders import cargar_global


def render(ctx):
    st.markdown(f"### 🌍 Resumen Global — {PERIODO_LABEL}")
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
        fig_p = px.pie(df_pais, values='Total', names='País', hole=0.5, color_discrete_sequence=['#00d4aa','#7c6af7'])
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
            fig_g4 = px.bar(df_cv, x='Sede', y='% Conversión', color='País', text='% Conversión',
                            color_discrete_map={'🇪🇸 España':'#00d4aa','🇺🇸 USA':'#7c6af7'})
            fig_g4.update_traces(texttemplate='%{text}%')
            fig_g4.update_layout(**PLOT_CFG, margin=dict(t=20,b=0,l=0,r=0))
            st.plotly_chart(fig_g4, use_container_width=True)
        else:
            st.info("Sin datos de conversión.")
    st.markdown("---")
    st.dataframe(df_global.sort_values(['País','Realizados'],ascending=[True,False]),
                 use_container_width=True, hide_index=True)
