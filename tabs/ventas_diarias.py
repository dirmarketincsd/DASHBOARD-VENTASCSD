from datetime import date

import pandas as pd
import streamlit as st

from config import EQUIPOS_BASE
from components import render_embudo_horizontal
from data_loaders import (
    cargar_tareas,
    cargar_ventas_cerradas,
    cargar_agenda_pendiente,
)


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
        cols_vis = ['Fecha','Dia_Semana','Responsable','Grupo_Pais',
                    'Leads WPP','Leads IG','Leads Formulario','Leads Landing','Leads TikTok',
                    'Valoraciones','Venta Dia Siguiente','Cierres']
        cols_ok  = [c for c in cols_vis if c in df_filtrado.columns]
        df_show  = df_filtrado[cols_ok].copy()
        if 'Fecha' in df_show.columns:
            df_show = df_show.sort_values('Fecha', ascending=True)
            df_show['Fecha'] = df_show['Fecha'].dt.strftime('%d/%m/%Y')
        df_show = df_show.rename(columns={
            'Venta Dia Siguiente':'Presupuestado', 'Cierres':'Depósitos',
            'Dia_Semana':'Día', 'Grupo_Pais':'Grupo'
        })
        totales = {c: df_show[c].sum() if c in df_show.columns else '' for c in df_show.columns}
        totales['Fecha'] = '📊 TOTAL'; totales['Día'] = ''; totales['Responsable'] = ''; totales['Grupo'] = ''
        df_final = pd.concat([df_show, pd.DataFrame([totales])], ignore_index=True)
        st.markdown("#### 📋 Registros por Fecha")
        st.dataframe(df_final, use_container_width=True, hide_index=True)
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Descargar CSV", data=csv, file_name=f"ventas_{date.today()}.csv", mime="text/csv")

        # ── VENTAS DEL MES ─────────────────────────────────────────────────
        from data_loaders import cargar_ventas_mes
        from config import PERIODO_LABEL

        st.markdown("---")
        st.markdown(f"### 📅 Ventas del Mes · {PERIODO_LABEL}")

        def render_tabla_mes(df_mes, pais, color):
            if df_mes.empty:
                st.info(f"Sin datos {pais}.")
                return
            st.markdown(f"<div style='color:{color};font-weight:800;font-size:0.9rem;margin-bottom:6px'>{pais}</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**📅 Agendados**")
                df_ag = df_mes[['Sede','S1_Ag','S2_Ag','S3_Ag','S4_Ag','S5_Ag','Total_Ag','% Conv']].copy()
                df_ag.columns = ['Sede','S1','S2','S3','S4','S5','Total','% Conv']
                st.dataframe(df_ag, use_container_width=True, hide_index=True)
            with c2:
                st.markdown("**✅ Realizados**")
                df_re = df_mes[['Sede','S1_Re','S2_Re','S3_Re','S4_Re','S5_Re','Total_Re']].copy()
                df_re.columns = ['Sede','S1','S2','S3','S4','S5','Total']
                st.dataframe(df_re, use_container_width=True, hide_index=True)

        if grupo_sel in ('Todos', 'USA'):
            render_tabla_mes(cargar_ventas_mes('USA'), '🇺🇸 USA', '#7c6af7')

        if grupo_sel in ('Todos', 'España'):
            render_tabla_mes(cargar_ventas_mes('España'), '🇪🇸 España', '#00d4aa')

        st.markdown("---")
        st.markdown("### 🔻 Embudos de Ventas")

        df_esp_emb = df_filtrado[df_filtrado['Grupo_Pais']=='España'] if 'Grupo_Pais' in df_filtrado.columns else pd.DataFrame()
        df_usa_emb = df_filtrado[df_filtrado['Grupo_Pais']=='USA']    if 'Grupo_Pais' in df_filtrado.columns else pd.DataFrame()

        leads_esp = int(df_esp_emb['Leads WPP'].sum() + df_esp_emb['Leads IG'].sum()) if not df_esp_emb.empty else 0
        val_esp   = int(df_esp_emb['Valoraciones'].sum())        if not df_esp_emb.empty else 0
        pres_esp  = int(df_esp_emb['Venta Dia Siguiente'].sum()) if not df_esp_emb.empty else 0
        dep_esp   = int(df_esp_emb['Cierres'].sum())             if not df_esp_emb.empty else 0

        leads_usa = int(df_usa_emb['Leads WPP'].sum() + df_usa_emb['Leads IG'].sum()) if not df_usa_emb.empty else 0
        val_usa   = int(df_usa_emb['Valoraciones'].sum())        if not df_usa_emb.empty else 0
        pres_usa  = int(df_usa_emb['Venta Dia Siguiente'].sum()) if not df_usa_emb.empty else 0
        dep_usa   = int(df_usa_emb['Cierres'].sum())             if not df_usa_emb.empty else 0

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
        render_embudo_horizontal("🇺🇸 Embudo USA", etapas_usa, "#7c6af7")

        st.markdown("---")

        st.markdown("### 📋 Tareas para Hoy")
        df_tareas = cargar_tareas()
        if not df_tareas.empty:
            ASESORES = ['DANIELA', 'EVELYN', 'CAROLINA']
            t_col1, t_col2 = st.columns(2)
            for idx, asesor in enumerate(ASESORES):
                df_a  = df_tareas[df_tareas['Responsable'] == asesor] if 'Responsable' in df_tareas.columns else pd.DataFrame()
                grupo = EQUIPOS_BASE.get(asesor, 'Por Clasificar')
                color = "#00d4aa" if grupo == 'España' else "#7c6af7"
                col_use = t_col1 if idx % 2 == 0 else t_col2
                with col_use:
                    st.markdown(f"""
                    <div style="background:linear-gradient(135deg,#0d0d0d,#1a1500);border:1px solid {color};
                                border-radius:12px;padding:14px 18px;margin-bottom:14px">
                        <div style="color:{color};font-weight:800;font-size:0.95rem;margin-bottom:12px">👤 {asesor}</div>
                    """, unsafe_allow_html=True)
                    if not df_a.empty and 'Tipo' in df_a.columns:
                        tipos_unicos = df_a['Tipo'].unique().tolist()
                        cols_t = st.columns(min(len(tipos_unicos), 3))
                        for i, tipo in enumerate(tipos_unicos):
                            cant = int(df_a[df_a['Tipo'] == tipo]['Cantidad'].sum())
                            EMOJIS = {
                                'VALORACION': '💻', 'VALORACION VIRTUAL': '💻',
                                'SEGUIMIENTO': '📞', 'PRESUPUESTAR': '💵',
                                'AGENDAR': '📅', 'COLOCAR DATOS': '📝',
                                'SOPORTE HUMANO': '🤝',
                            }
                            emoji = EMOJIS.get(tipo.upper(), '📌')
                            cols_t[i % 3].metric(f"{emoji} {tipo.capitalize()}", cant)
                    else:
                        st.info("Sin tareas registradas.")
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("📝 Sin tareas registradas.")

        st.markdown("#### 🏆 Ranking de Valoraciones")
        if not df_base.empty and 'Responsable' in df_base.columns and 'Valoraciones' in df_base.columns:
            df_rank_val = df_base.groupby('Responsable')['Valoraciones'].sum().reset_index()
            df_rank_val = df_rank_val[df_rank_val['Valoraciones'] > 0].sort_values('Valoraciones', ascending=False)
            total_val = df_rank_val['Valoraciones'].sum()
            if total_val > 0:
                df_rank_val['%'] = (df_rank_val['Valoraciones'] / total_val * 100).round(1)
                df_rank_val['Grupo'] = df_rank_val['Responsable'].map(lambda x: EQUIPOS_BASE.get(x,'Por Clasificar'))
                for _, row in df_rank_val.iterrows():
                    color = "#00d4aa" if row['Grupo'] == 'España' else "#7c6af7"
                    p = row['%']
                    st.markdown(f"""
                    <div style="background:linear-gradient(135deg,#0d0d0d,#1a1500);border:1px solid #2a2000;
                                border-radius:10px;padding:10px 16px;margin-bottom:6px">
                        <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                            <span style="color:white;font-weight:700">👤 {row['Responsable']}</span>
                            <span style="color:{color};font-weight:700">{int(row['Valoraciones'])} val. · {p}%</span>
                        </div>
                        <div style="background:#1e2340;border-radius:6px;height:10px">
                            <div style="height:10px;border-radius:6px;background:{color};width:{p}%"></div>
                        </div>
                    </div>""", unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("### ✅ Ventas Cerradas")
        df_vc_usa, df_vc_esp = cargar_ventas_cerradas()
        vc1, vc2 = st.columns(2)
        with vc1:
            st.markdown("<div style='color:#7c6af7;font-weight:800;font-size:0.9rem;margin-bottom:8px'>🇺🇸 USA</div>", unsafe_allow_html=True)
            if not df_vc_usa.empty:
                st.dataframe(df_vc_usa, use_container_width=True, hide_index=True)
                st.metric("💰 Total USA", f"${df_vc_usa['Total'].sum():,.0f}")
            else:
                st.info("Sin ventas cerradas USA.")
        with vc2:
            st.markdown("<div style='color:#00d4aa;font-weight:800;font-size:0.9rem;margin-bottom:8px'>🇪🇸 España</div>", unsafe_allow_html=True)
            if not df_vc_esp.empty:
                st.dataframe(df_vc_esp, use_container_width=True, hide_index=True)
                st.metric("💰 Total España", f"${df_vc_esp['Total'].sum():,.0f}")
            else:
                st.info("Sin ventas cerradas España.")

        st.markdown("---")

        st.markdown("### 📅 Agenda Pendiente")
        df_ag_usa, df_ag_esp = cargar_agenda_pendiente()
        ag1, ag2 = st.columns(2)
        with ag1:
            st.markdown("<div style='color:#7c6af7;font-weight:800;font-size:0.9rem;margin-bottom:8px'>🇺🇸 USA</div>", unsafe_allow_html=True)
            if not df_ag_usa.empty:
                st.dataframe(df_ag_usa, use_container_width=True, hide_index=True)
            else:
                st.info("Sin agenda pendiente USA.")
        with ag2:
            st.markdown("<div style='color:#00d4aa;font-weight:800;font-size:0.9rem;margin-bottom:8px'>🇪🇸 España</div>", unsafe_allow_html=True)
            if not df_ag_esp.empty:
                st.dataframe(df_ag_esp, use_container_width=True, hide_index=True)
            else:
                st.info("Sin agenda pendiente España.")
