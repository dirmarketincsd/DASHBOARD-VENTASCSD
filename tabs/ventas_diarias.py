from datetime import date

import pandas as pd
import streamlit as st

from config import EQUIPOS_BASE
from data_loaders import cargar_ventas_mes
from config import sheet_url


@st.cache_data(ttl=300)
def cargar_tabla_detallada(pais: str):
    """
    Lee 'usa mayo 2026' o 'España mayo 2026' y extrae la tabla de
    AGENDADOS y REALIZADOS con columnas por tipo de diseño y semana.
    """
    nombre = "usa mayo 2026" if pais == "USA" else "España mayo 2026"
    try:
        url = sheet_url(nombre)
        raw = pd.read_csv(url, header=None)

        COLS_TIPOS = ['Diseño Resina', 'Imp. Ceromero', 'Cem. Ceromero',
                      'Imp. Ceramica', 'Cem. Ceramica', 'Extractif.', 'Garantias']

        if pais == "USA":
            sedes = ['DALLAS', 'HOUSTON', 'NEW JERSY', 'ORLANDO', 'ANGELES']
            sedes_label = ['Dallas', 'Houston', 'New Jersey', 'Orlando', 'Los Angeles']
        else:
            sedes = ['ALICANTE', 'BARCELONA', 'VALENCIA', 'MADRID', 'MALAGA', 'BILBAO']
            sedes_label = ['Alicante', 'Barcelona', 'Valencia', 'Madrid', 'Malaga', 'Bilbao']

        # Encontrar fila de sedes (AGENDADOS)
        ag_rows = {}
        re_rows = {}

        for i in range(len(raw)):
            val = str(raw.iloc[i, 0]).strip().upper().replace(' ', '')
            for j, sede in enumerate(sedes):
                if val == sede.replace(' ', '') or sede.replace(' ', '') in val:
                    fila = [str(v).strip() for v in raw.iloc[i].tolist()]
                    def to_num(v):
                        try: return float(v.replace(',', '.'))
                        except: return 0.0
                    nums = [to_num(v) for v in fila[1:] if v not in ('', 'nan', 'None')]

                    # Agendados: primeras 28 posiciones (4 semanas x 7 cols)
                    ag_data = nums[:28] if len(nums) >= 28 else nums + [0] * (28 - len(nums))
                    # Realizados: siguientes 28
                    re_data = nums[28:56] if len(nums) >= 56 else (nums[28:] if len(nums) > 28 else [0] * 28)
                    re_data = re_data + [0] * (28 - len(re_data))

                    ag_rows[sedes_label[j]] = ag_data
                    re_rows[sedes_label[j]] = re_data
                    break

        return ag_rows, re_rows, COLS_TIPOS

    except Exception as e:
        st.error(f"Error cargando tabla detallada {pais}: {e}")
        return {}, {}, []


def render_tabla_detallada(ag_rows, re_rows, cols_tipos, color, pais):
    if not ag_rows:
        st.info(f"Sin datos {pais}.")
        return

    semanas = ['S1', 'S2', 'S3', 'S4']
    n = len(cols_tipos)  # 7

    # Construir DataFrame AGENDADOS
    ag_records = []
    for sede, nums in ag_rows.items():
        row = {'Sede': sede}
        for s_i, sem in enumerate(semanas):
            for t_i, tipo in enumerate(cols_tipos):
                idx = s_i * n + t_i
                row[f'{sem} · {tipo}'] = nums[idx] if idx < len(nums) else 0
        ag_records.append(row)
    df_ag = pd.DataFrame(ag_records)

    # Totales agendados
    total_ag = {col: df_ag[col].sum() if col != 'Sede' else 'TOTAL' for col in df_ag.columns}
    df_ag = pd.concat([df_ag, pd.DataFrame([total_ag])], ignore_index=True)

    # Construir DataFrame REALIZADOS
    re_records = []
    for sede, nums in re_rows.items():
        row = {'Sede': sede}
        for s_i, sem in enumerate(semanas):
            for t_i, tipo in enumerate(cols_tipos):
                idx = s_i * n + t_i
                row[f'{sem} · {tipo}'] = nums[idx] if idx < len(nums) else 0
        re_records.append(row)
    df_re = pd.DataFrame(re_records)

    total_re = {col: df_re[col].sum() if col != 'Sede' else 'TOTAL' for col in df_re.columns}
    df_re = pd.concat([df_re, pd.DataFrame([total_re])], ignore_index=True)

    st.markdown(f"<div style='color:{color};font-weight:800;font-size:1rem;margin-bottom:8px'>{pais}</div>", unsafe_allow_html=True)

    st.markdown("**📅 Agendados**")
    st.dataframe(df_ag, use_container_width=True, hide_index=True)

    st.markdown("**✅ Realizados**")
    st.dataframe(df_re, use_container_width=True, hide_index=True)


def render_tabla_html(df_final, cols_ok_renombradas):
    """
    Renderiza df_final como tabla HTML con encabezados de 2 niveles:
    'Leads WPP' fusionado sobre 'USA' / 'España', 'Leads IG' fusionado
    sobre 'ES' / 'USA', igual que las celdas combinadas en el Google Sheet.
    """
    # Definición de grupos: (etiqueta_superior, [(col_df, etiqueta_sub), ...]) o None para columna simple
    GRUPOS = [
        ('Fecha',            [('Fecha', None)]),
        ('Día',              [('Día', None)]),
        ('Responsable',      [('Responsable', None)]),
        ('Leads WPP',        [('Leads WPP USA', 'USA'), ('Leads WPP España', 'España')]),
        ('Leads IG',         [('Leads IG ES', 'ES'), ('Leads IG USA', 'USA')]),
        ('Leads Formulario', [('Leads Formulario', None)]),
        ('Leads Google',     [('Leads Google', None)]),
        ('Leads Landing',    [('Leads Landing', None)]),
        ('Leads TikTok',     [('Leads TikTok', None)]),
        ('Financiamiento',   [('Financiamiento', None)]),
        ('No Financiamiento',[('No Financiamiento', None)]),
        ('Otros',            [('Otros', None)]),
        ('Valoraciones',     [('Valoraciones', None)]),
        ('Presupuestado',    [('Presupuestado', None)]),
        ('Depósitos',        [('Depósitos', None)]),
    ]
    # Filtrar solo grupos cuyas columnas existen en df_final
    grupos_ok = []
    for etiqueta, subcols in GRUPOS:
        subcols_ok = [(c, s) for c, s in subcols if c in df_final.columns]
        if subcols_ok:
            grupos_ok.append((etiqueta, subcols_ok))

    th_style    = "background:#1a1500;color:#c9a84c;border:1px solid #3a3320;padding:8px 10px;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.5px;white-space:nowrap"
    th_sub_style= "background:#0d0d0d;color:#8b9bb4;border:1px solid #3a3320;padding:6px 10px;font-size:0.74rem;white-space:nowrap"
    td_style    = "border:1px solid #2a2a2a;padding:6px 10px;font-size:0.82rem;color:#e8e8e8;white-space:nowrap"
    td_total    = "border:1px solid #2a2a2a;padding:6px 10px;font-size:0.82rem;color:#c9a84c;font-weight:800;white-space:nowrap;background:#1a1500"

    # Fila 1: etiquetas superiores (colspan = nro de subcolumnas; rowspan=2 si no hay sub-etiquetas)
    fila1 = "<tr>"
    for etiqueta, subcols in grupos_ok:
        if len(subcols) == 1 and subcols[0][1] is None:
            fila1 += f'<th style="{th_style}" rowspan="2">{etiqueta}</th>'
        else:
            fila1 += f'<th style="{th_style}" colspan="{len(subcols)}">{etiqueta}</th>'
    fila1 += "</tr>"

    # Fila 2: sub-etiquetas (solo para grupos con más de 1 subcolumna)
    fila2 = "<tr>"
    for etiqueta, subcols in grupos_ok:
        if len(subcols) == 1 and subcols[0][1] is None:
            continue
        for _, sub in subcols:
            fila2 += f'<th style="{th_sub_style}">{sub}</th>'
    fila2 += "</tr>"

    # Filas de datos
    filas_html = ""
    for _, row in df_final.iterrows():
        es_total = str(row.get('Fecha', '')).startswith('📊')
        estilo = td_total if es_total else td_style
        filas_html += "<tr>"
        for _, subcols in grupos_ok:
            for col, _ in subcols:
                val = row[col]
                filas_html += f'<td style="{estilo}">{val}</td>'
        filas_html += "</tr>"

    tabla_html = f"""
    <div style="overflow-x:auto;border-radius:10px;border:1px solid #3a3320">
    <table style="border-collapse:collapse;width:100%">
        <thead>{fila1}{fila2}</thead>
        <tbody>{filas_html}</tbody>
    </table>
    </div>
    """
    st.markdown(tabla_html, unsafe_allow_html=True)


def render(ctx):
    df_base         = ctx['df_base']
    df_filtrado     = ctx['df_filtrado']
    modo_fecha      = ctx['modo_fecha']
    fecha_ini       = ctx['fecha_ini']
    fecha_fin       = ctx['fecha_fin']
    semana_sel      = ctx['semana_sel']
    dia_sel         = ctx['dia_sel']
    responsable_sel = ctx['responsable_sel']

    partes = []
    if modo_fecha=="Día específico" and fecha_ini: partes.append(fecha_ini.strftime('%d/%m/%Y'))
    elif modo_fecha=="Rango de fechas" and fecha_ini: partes.append(f"{fecha_ini.strftime('%d/%m')}→{fecha_fin.strftime('%d/%m')}")
    elif modo_fecha=="Semana": partes.append(f"Semana {semana_sel}")
    if dia_sel!="Todos": partes.append(dia_sel)
    if responsable_sel!="Todos": partes.append(responsable_sel)
    desc = " · ".join(partes) if partes else "Todos los registros"
    st.markdown(f"### 📊 {desc}")

    if df_filtrado.empty:
        st.warning("⚠️ Sin registros para estos filtros.")
    else:
        cols_vis = [
            'Fecha', 'Dia_Semana', 'Responsable',
            'Leads WPP USA', 'Leads WPP España', 'Leads IG ES', 'Leads IG USA',
            'Leads Formulario', 'Leads Google',
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
        })
        totales = {c: df_show[c].sum() if c in df_show.columns else '' for c in df_show.columns}
        totales['Fecha'] = '📊 TOTAL'; totales['Día'] = ''; totales['Responsable'] = ''
        df_final = pd.concat([df_show, pd.DataFrame([totales])], ignore_index=True)
        st.markdown("#### 📋 Registros por Fecha")
        render_tabla_html(df_final, cols_ok)
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Descargar CSV", data=csv, file_name=f"ventas_{date.today()}.csv", mime="text/csv")

    # ── VALORACIONES DEL MES ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📅 Valoraciones del Mes")

    ag_rows, re_rows, cols_tipos = cargar_tabla_detallada('USA')
    render_tabla_detallada(ag_rows, re_rows, cols_tipos, '#7c6af7', '🇺🇸 USA')
    st.markdown("<br>", unsafe_allow_html=True)

    ag_rows, re_rows, cols_tipos = cargar_tabla_detallada('España')
    render_tabla_detallada(ag_rows, re_rows, cols_tipos, '#00d4aa', '🇪🇸 España')