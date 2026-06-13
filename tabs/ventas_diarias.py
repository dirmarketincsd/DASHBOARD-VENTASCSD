from datetime import date

import pandas as pd
import streamlit as st

from config import EQUIPOS_BASE
from data_loaders import cargar_ventas_mes


def render(ctx):
    df_base         = ctx['df_base']
    df_filtrado     = ctx['df_filtrado']
    modo_fecha      = ctx['modo_fecha']
    fecha_ini       = ctx['fecha_ini']
    fecha_fin       = ctx['fecha_fin']
    semana_sel      = ctx['semana_sel']
    dia_sel         = ctx['dia_sel']
    grupo_sel       = ctx['grupo_sel']
    responsable_sel = ctx['responsable_sel']

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
        cols_vis = [
            'Fecha', 'Dia_Semana', 'Responsable', 'Grupo_Pais',
            'Leads WPP', 'Leads IG', 'Leads Formulario', 'Leads Google',
            'Leads Landing', 'Leads TikTok',
            'Financiamiento', 'No Financiamiento', 'Otros',
            'Valoraciones', 'Venta Dia Siguiente', 'Cierres',
        ]
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
        })
        totales = {c: df_show[c].sum() if c in df_show.columns else '' for c in df_show.columns}
        totales['Fecha'] = '📊 TOTAL'; totales['Día'] = ''; totales['Responsable'] = ''; totales['Grupo'] = ''
        df_final = pd.concat([df_show, pd.DataFrame([totales])], ignore_index=True)
        st.markdown("#### 📋 Registros por Fecha")
        st.dataframe(df_final, use_container_width=True, hide_index=True)
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Descargar CSV", data=csv, file_name=f"ventas_{date.today()}.csv", mime="text/csv")

    # ── VENTAS DEL MES ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📅 Valoraciones del Mes")

    def render_tabla_mes(df_mes, pais, color):
        if df_mes is None or df_mes.empty:
            st.info(f"Sin datos {pais}.")
            return
        st.markdown(f"<div style='color:{color};font-weight:800;font-size:1rem;margin-bottom:8px'>{pais}</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**📅 Agendados**")
            cols_ag = ['Sede'] + [c for c in ['Sem1_Ag','Sem2_Ag','Sem3_Ag','Sem4_Ag','Sem5_Ag','Total_Ag','% Conv'] if c in df_mes.columns]
            df_ag = df_mes[cols_ag].copy()
            new_cols = ['Sede']
            for c in cols_ag[1:]:
                if c == 'Total_Ag':  new_cols.append('Total')
                elif c == '% Conv':  new_cols.append('% Conv')
                else:                new_cols.append(c.replace('Sem','S').replace('_Ag',''))
            df_ag.columns = new_cols
            st.dataframe(df_ag, use_container_width=True, hide_index=True)
        with c2:
            st.markdown("**✅ Realizados**")
            cols_re = ['Sede'] + [c for c in ['Sem1_Re','Sem2_Re','Sem3_Re','Sem4_Re','Sem5_Re','Total_Re'] if c in df_mes.columns]
            df_re = df_mes[cols_re].copy()
            new_cols_re = ['Sede']
            for c in cols_re[1:]:
                if c == 'Total_Re': new_cols_re.append('Total')
                else:               new_cols_re.append(c.replace('Sem','S').replace('_Re',''))
            df_re.columns = new_cols_re
            st.dataframe(df_re, use_container_width=True, hide_index=True)

    if grupo_sel in ('Todos', 'USA'):
        render_tabla_mes(cargar_ventas_mes('USA'), '🇺🇸 USA', '#7c6af7')
        st.markdown("<br>", unsafe_allow_html=True)

    if grupo_sel in ('Todos', 'España'):
        render_tabla_mes(cargar_ventas_mes('España'), '🇪🇸 España', '#00d4aa')