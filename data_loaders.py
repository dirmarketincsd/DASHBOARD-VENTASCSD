import csv
import io

import pandas as pd
import requests
import streamlit as st

from config import EQUIPOS_BASE, sheet_url, camp_sheet_url


def _leer_csv_robusto(url):
    """
    Lee un CSV publicado de Google Sheets tolerando filas con distinto
    número de columnas (común cuando hay tablas auxiliares a la derecha
    de la tabla principal). pd.read_csv falla con ParserError en estos
    casos; csv.reader no.
    """
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    resp.encoding = 'utf-8'
    reader = csv.reader(io.StringIO(resp.text))
    rows = list(reader)
    max_len = max((len(r) for r in rows), default=0)
    rows_padded = [r + [''] * (max_len - len(r)) for r in rows]
    return pd.DataFrame(rows_padded)

import csv
import io

import pandas as pd
import requests
import streamlit as st

from config import EQUIPOS_BASE, sheet_url, camp_sheet_url


def _leer_csv_robusto(url):
    """
    Lee un CSV publicado de Google Sheets tolerando filas con distinto
    número de columnas (común cuando hay tablas auxiliares a la derecha
    de la tabla principal). pd.read_csv falla con ParserError en estos
    casos; csv.reader no.
    """
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    resp.encoding = 'utf-8'
    reader = csv.reader(io.StringIO(resp.text))
    rows = list(reader)
    max_len = max((len(r) for r in rows), default=0)
    rows_padded = [r + [''] * (max_len - len(r)) for r in rows]
    return pd.DataFrame(rows_padded)


# ── CARGA VENTAS DIARIAS ───────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def cargar_ventas_diarias():
    """
    Lee la pestaña 'Ventas diarias' del Google Sheet.
    Columnas reales (A→O):
    FECHA | DIA | RESPONSABLE | VALORACIONES |
    LEADS WPP ESPAÑA | LEADS IG ES | LEADS WPP USA | LEADS IG USA |
    LEADS GOOGLE | LEADS TIKTOK | LEADS LANDING |
    FINANCIAMIENTO | NO FINANCIAMIENTO | LEADS QUEMADOS | DEPOSITOS HOY
    """
    try:
        url = sheet_url("Ventas diarias")
        raw = _leer_csv_robusto(url)

        # ── Buscar fila header ─────────────────────────────────────────────────
        header_idx = None
        for i in range(min(15, len(raw))):
            vals = [str(v).strip().upper() for v in raw.iloc[i].tolist()]
            if 'RESPONSABLE' in vals and ('FECHA' in vals or 'DIA' in vals):
                header_idx = i
                break

        if header_idx is None:
            for i in range(min(15, len(raw))):
                vals = [str(v).strip().upper() for v in raw.iloc[i].tolist()]
                if any(x in vals for x in ['DANIELA', 'EVELYN', 'CAROLINA']):
                    header_idx = i - 1
                    break

        if header_idx is None:
            header_idx = 3

        # ── Tomar solo las 15 columnas principales (A→O) ──────────────────────
        df = raw.iloc[header_idx + 1:, :15].copy()
        df.columns = [
            'FECHA', 'DIA', 'RESPONSABLE', 'VALORACIONES',
            'LEADS WPP ESPAÑA', 'LEADS IG ES', 'LEADS WPP USA', 'LEADS IG USA',
            'LEADS GOOGLE', 'LEADS TIKTOK', 'LEADS LANDING',
            'FINANCIAMIENTO', 'NO FINANCIAMIENTO',
            'LEADS QUEMADOS', 'DEPOSITOS HOY',
        ]
        df = df.reset_index(drop=True)

        # ── Renombrar a nombres internos del dashboard ─────────────────────────
        rename = {
            'FECHA':              'Fecha',
            'DIA':                'Dia_Texto',
            'RESPONSABLE':        'Responsable',
            'VALORACIONES':       'Valoraciones',
            'LEADS WPP ESPAÑA':   'Leads WPP España',
            'LEADS IG ES':        'Leads IG ES',
            'LEADS WPP USA':      'Leads WPP USA',
            'LEADS IG USA':       'Leads IG USA',
            'LEADS GOOGLE':       'Leads Google',
            'LEADS TIKTOK':       'Leads TikTok',
            'LEADS LANDING':      'Leads Landing',
            'FINANCIAMIENTO':     'Financiamiento',
            'NO FINANCIAMIENTO':  'No Financiamiento',
            'LEADS QUEMADOS':     'Leads Quemados',
            'DEPOSITOS HOY':      'Cierres',
        }
        df = df.rename(columns=rename)

        # ── Fecha ──────────────────────────────────────────────────────────────
        if 'Fecha' in df.columns:
            df['Fecha'] = df['Fecha'].astype(str).str.strip()
            df['Fecha'] = df['Fecha'].replace({'nan': '', 'None': '', 'N/A': ''})
            df['Fecha'] = df['Fecha'].replace('', None)
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
            df['Fecha'] = df['Fecha'].ffill()

        # ── Día texto ──────────────────────────────────────────────────────────
        if 'Dia_Texto' in df.columns:
            df['Dia_Texto'] = df['Dia_Texto'].astype(str).str.strip()
            df['Dia_Texto'] = df['Dia_Texto'].replace({'nan': '', 'None': '', 'N/A': ''})
            df['Dia_Texto'] = df['Dia_Texto'].replace('', None)
            df['Dia_Texto'] = df['Dia_Texto'].ffill()

        # ── Responsable y Grupo_Pais ───────────────────────────────────────────
        if 'Responsable' in df.columns:
            df = df[df['Responsable'].notna()]
            df['Responsable'] = df['Responsable'].astype(str).str.strip().str.upper()
            df = df[~df['Responsable'].isin(['', 'NAN', 'N/A', 'RESPONSABLE', 'TOTAL', 'TOTALES'])]

            def asignar_grupo(r):
                resp = str(r.get('Responsable', '')).upper()
                sede = str(r.get('Sede', '')).upper()
                if resp in EQUIPOS_BASE:
                    return EQUIPOS_BASE[resp]
                if any(x in sede for x in ['MADRID', 'BARCELONA', 'VALENCIA', 'ALICANTE', 'MALAGA', 'BILBAO', 'ESPAÑA']):
                    return 'España'
                if any(x in sede for x in ['DALLAS', 'HOUSTON', 'ORLANDO', 'JERSEY', 'ANGELES', 'MIAMI', 'USA']):
                    return 'USA'
                return 'Por Clasificar'

            df['Grupo_Pais'] = df.apply(asignar_grupo, axis=1)

        # ── Filtrar filas sin fecha ────────────────────────────────────────────
        if 'Fecha' in df.columns:
            df = df[df['Fecha'].notna()]

        # ── Día semana ─────────────────────────────────────────────────────────
        DIAS_NORM = {
            'LUNES': 'Lunes', 'MARTES': 'Martes',
            'MIERCOLES': 'Miércoles', 'MIÉRCOLES': 'Miércoles',
            'JUEVES': 'Jueves', 'VIERNES': 'Viernes',
            'SABADO': 'Sábado', 'SÁBADO': 'Sábado', 'DOMINGO': 'Domingo',
        }
        if 'Dia_Texto' in df.columns:
            df['Dia_Semana'] = df['Dia_Texto'].astype(str).str.strip().str.upper().map(DIAS_NORM).fillna('Sin dato')
        elif 'Fecha' in df.columns:
            nombres = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            df['Dia_Semana'] = df['Fecha'].dt.dayofweek.map(lambda x: nombres[x])
        else:
            df['Dia_Semana'] = 'Sin dato'

        if 'Semana' not in df.columns:
            df['Semana'] = '1'
        df['Semana'] = df['Semana'].astype(str).str.strip()

        # ── Columnas numéricas ─────────────────────────────────────────────────
        cols_num = [
            'Valoraciones',
            'Leads WPP España', 'Leads IG ES', 'Leads WPP USA', 'Leads IG USA',
            'Leads Google', 'Leads TikTok', 'Leads Landing',
            'Financiamiento', 'No Financiamiento',
            'Leads Quemados', 'Cierres',
        ]
        for col in cols_num:
            if col in df.columns:
                serie = df[col].astype(str).str.strip()
                serie = serie.replace(
                    {'N/A': '0', 'n/a': '0', 'NA': '0', 'nan': '0', 'None': '0', '': '0'},
                    regex=False,
                )
                serie = serie.str.replace('[^0-9.-]', '', regex=True).replace('', '0')
                df[col] = pd.to_numeric(serie, errors='coerce').fillna(0).clip(lower=0).astype(int)
            else:
                df[col] = 0

        # Columna Venta Dia Siguiente no existe en el sheet nuevo → poner en 0
        df['Venta Dia Siguiente'] = 0

        return df

    except Exception as e:
        st.error(f"❌ Error ventas diarias: {e}")
        return pd.DataFrame()


# ── CARGA LEADS POR SEDE (tabla auxiliar en hoja 'Ventas diarias') ────────────
@st.cache_data(ttl=60)
def cargar_leads_por_sede():
    """
    Busca, en cualquier parte de la hoja 'Ventas diarias', las filas tipo
    'LEADS BARCELONA' / 'LEADS HOUSTON' (etiqueta en una celda, valor en la
    celda justo debajo, misma columna) y las agrupa en España / USA.
    """
    SEDES_ESP = ['BARCELONA', 'MALAGA', 'MÁLAGA', 'BILBAO', 'MADRID', 'VALENCIA', 'ALICANTE']
    SEDES_USA = ['HOUSTON', 'DALLAS', 'NEW JERSEY', 'NEW JERSY', 'LOS ANGELES', 'ANGELES', 'ORLANDO']

    def _norm(sede):
        s = sede.upper()
        if s == 'MÁLAGA':                          return 'Malaga'
        if s in ('NEW JERSY', 'NEW JERSEY'):       return 'New Jersey'
        if s in ('ANGELES', 'LOS ANGELES'):        return 'Los Angeles'
        return s.capitalize()

    try:
        url = sheet_url("Ventas diarias")
        raw = _leer_csv_robusto(url)

        leads_esp = {}
        leads_usa = {}

        n_rows, n_cols = raw.shape
        for i in range(n_rows):
            for j in range(n_cols):
                val = str(raw.iat[i, j]).strip().upper()
                if not val.startswith('LEADS '):
                    continue
                sede_txt = val.replace('LEADS ', '').strip()
                if i + 1 >= n_rows:
                    continue
                val_num = str(raw.iat[i + 1, j]).strip()
                try:
                    num = float(val_num.replace(',', '.'))
                except (ValueError, AttributeError):
                    continue

                if sede_txt in SEDES_ESP:
                    leads_esp[_norm(sede_txt)] = num
                elif sede_txt in SEDES_USA:
                    leads_usa[_norm(sede_txt)] = num

        return leads_esp, leads_usa

    except Exception as e:
        st.error(f"❌ Error leads por sede: {e}")
        return {}, {}


# ── CARGA ESPAÑA MAYO ──────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_españa():
    try:
        url = sheet_url("España mayo 2026")
        raw = pd.read_csv(url, header=None)
        sedes = ['ALICANTE', 'BARCELONA', 'VALENCIA', 'MADRID', 'MALAGA', 'BILBAO']
        data_esp = []
        for i in range(len(raw)):
            val = str(raw.iloc[i, 0]).strip().upper().replace(' ', '')
            for sede in sedes:
                if val == sede or val == sede.replace(' ', ''):
                    fila = raw.iloc[i].dropna().tolist()
                    nums = []
                    for v in fila[1:]:
                        try:
                            n = float(str(v).replace(',', '.'))
                            if n >= 0: nums.append(n)
                        except:
                            pass
                    mid = len(nums) // 2
                    ag = sum(nums[:4]) if len(nums) >= 4 else sum(nums[:mid])
                    re = sum(nums[4:8]) if len(nums) >= 8 else sum(nums[mid:mid + 4])
                    data_esp.append({'Sede': sede.capitalize(), 'Agendados': ag, 'Realizados': re})
                    break
        if not data_esp:
            data_esp = [
                {'Sede': 'Alicante',  'Agendados': 10,   'Realizados': 7},
                {'Sede': 'Barcelona', 'Agendados': 13.5, 'Realizados': 12.5},
                {'Sede': 'Valencia',  'Agendados': 6,    'Realizados': 2},
                {'Sede': 'Madrid',    'Agendados': 5.5,  'Realizados': 4.5},
                {'Sede': 'Malaga',    'Agendados': 20.5, 'Realizados': 10.5},
                {'Sede': 'Bilbao',    'Agendados': 0,    'Realizados': 2.5},
            ]
        df = pd.DataFrame(data_esp)
        df['Agendados']  = pd.to_numeric(df['Agendados'],  errors='coerce').fillna(0)
        df['Realizados'] = pd.to_numeric(df['Realizados'], errors='coerce').fillna(0)
        df['% Conversión'] = df.apply(
            lambda r: round(r['Realizados'] / r['Agendados'] * 100, 1) if r['Agendados'] > 0 else 0, axis=1
        )
        return df
    except:
        df = pd.DataFrame([
            {'Sede': 'Alicante',  'Agendados': 10,   'Realizados': 7},
            {'Sede': 'Barcelona', 'Agendados': 13.5, 'Realizados': 12.5},
            {'Sede': 'Valencia',  'Agendados': 6,    'Realizados': 2},
            {'Sede': 'Madrid',    'Agendados': 5.5,  'Realizados': 4.5},
            {'Sede': 'Malaga',    'Agendados': 20.5, 'Realizados': 10.5},
            {'Sede': 'Bilbao',    'Agendados': 0,    'Realizados': 2.5},
        ])
        df['% Conversión'] = df.apply(
            lambda r: round(r['Realizados'] / r['Agendados'] * 100, 1) if r['Agendados'] > 0 else 0, axis=1
        )
        return df


# ── CARGA USA MAYO ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_usa():
    try:
        url = sheet_url("usa mayo 2026")
        raw = pd.read_csv(url, header=None)
        sedes       = ['DALLAS', 'HOUSTON', 'NEW JERSY', 'ORLANDO', 'ANGELES']
        sedes_label = ['Dallas', 'Houston', 'New Jersey', 'Orlando', 'Los Angeles']
        data_usa = []
        for i in range(len(raw)):
            val = str(raw.iloc[i, 0]).strip().upper().replace(' ', '')
            for j, sede in enumerate(sedes):
                if val == sede.replace(' ', '') or sede.replace(' ', '') in val:
                    fila = raw.iloc[i].dropna().tolist()
                    nums = []
                    for v in fila[1:]:
                        try:
                            n = float(str(v).replace(',', '.'))
                            if 0 < n < 50: nums.append(n)
                        except:
                            pass
                    ag = sum(nums[:4]) if len(nums) >= 4 else (sum(nums) if nums else 0)
                    re = sum(nums[4:8]) if len(nums) >= 8 else 0
                    data_usa.append({'Sede': sedes_label[j], 'Agendados': ag, 'Realizados': re})
                    break
        if not data_usa:
            data_usa = [
                {'Sede': 'Dallas',      'Agendados': 8.5,  'Realizados': 6.5},
                {'Sede': 'Houston',     'Agendados': 4,    'Realizados': 7.5},
                {'Sede': 'New Jersey',  'Agendados': 6.5,  'Realizados': 4.5},
                {'Sede': 'Orlando',     'Agendados': 3.5,  'Realizados': 4.5},
                {'Sede': 'Los Angeles', 'Agendados': 11.5, 'Realizados': 13.5},
            ]
        df = pd.DataFrame(data_usa)
        df['Agendados']  = pd.to_numeric(df['Agendados'],  errors='coerce').fillna(0)
        df['Realizados'] = pd.to_numeric(df['Realizados'], errors='coerce').fillna(0)
        df['% Conversión'] = df.apply(
            lambda r: round(r['Realizados'] / r['Agendados'] * 100, 1) if r['Agendados'] > 0 else 0, axis=1
        )
        return df
    except:
        df = pd.DataFrame([
            {'Sede': 'Dallas',      'Agendados': 8.5,  'Realizados': 6.5},
            {'Sede': 'Houston',     'Agendados': 4,    'Realizados': 7.5},
            {'Sede': 'New Jersey',  'Agendados': 6.5,  'Realizados': 4.5},
            {'Sede': 'Orlando',     'Agendados': 3.5,  'Realizados': 4.5},
            {'Sede': 'Los Angeles', 'Agendados': 11.5, 'Realizados': 13.5},
        ])
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


# ── CARGA TAREAS KOMMO ────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def cargar_tareas():
    try:
        url = sheet_url("TAREAS KOMMO")
        raw = pd.read_csv(url, header=None)
        header_idx = 0
        for i in range(min(5, len(raw))):
            vals = [str(v).strip().upper() for v in raw.iloc[i].tolist()]
            if 'RESPONSABLE' in vals and 'TIPO' in vals:
                header_idx = i
                break
        rows = []
        current_resp = None
        SKIP = {'', 'NAN', 'NONE', 'RESPONSABLE', 'TOTAL', 'TOTALES'}
        for i in range(header_idx + 1, len(raw)):
            row  = raw.iloc[i]
            col_a = str(row.iloc[0]).strip().upper() if len(row) > 0 else ''
            col_b = str(row.iloc[1]).strip().upper() if len(row) > 1 else ''
            col_c = str(row.iloc[2]).strip()          if len(row) > 2 else ''
            col_d = str(row.iloc[3]).strip()          if len(row) > 3 else ''
            if col_a and col_a not in SKIP and col_b in ('', 'NAN', 'TIPO'):
                current_resp = col_a
                continue
            if col_a and col_a not in SKIP and col_b and col_b not in ('', 'NAN', 'TIPO'):
                current_resp = col_a
                tipo = col_b
                try:    cantidad = int(float(col_c)) if col_c not in ('', 'NAN') else 0
                except: cantidad = 0
                fecha = col_d if col_d not in ('', 'NAN') else ''
                rows.append({'Responsable': current_resp, 'Tipo': tipo, 'Cantidad': cantidad, 'Fecha': fecha})
                continue
            if (not col_a or col_a in SKIP) and col_b and col_b not in ('', 'NAN', 'TIPO') and current_resp:
                tipo = col_b
                try:    cantidad = int(float(col_c)) if col_c not in ('', 'NAN') else 0
                except: cantidad = 0
                fecha = col_d if col_d not in ('', 'NAN') else ''
                rows.append({'Responsable': current_resp, 'Tipo': tipo, 'Cantidad': cantidad, 'Fecha': fecha})
        df = pd.DataFrame(rows)
        if df.empty:
            return pd.DataFrame()
        df = df[df['Cantidad'] > 0]
        return df
    except Exception as e:
        st.error(f"Error tareas: {e}")
        return pd.DataFrame()


# ── CARGA VENTAS CERRADAS ──────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def cargar_ventas_cerradas():
    try:
        url = sheet_url("Ventas diarias")
        raw = pd.read_csv(url, header=None)
        data_usa  = []
        data_esp  = []
        header_row = None
        usa_col    = None
        esp_col    = None
        for i in range(min(10, len(raw))):
            for j in range(len(raw.columns)):
                val = str(raw.iloc[i, j]).strip().upper()
                if 'VENTA CERRADA' in val and 'USA' in val:
                    usa_col    = j
                    header_row = i + 1
                if 'VENTA CERRADA' in val and 'ESPA' in val:
                    esp_col = j
        if header_row is None:
            return pd.DataFrame(), pd.DataFrame()
        if usa_col is not None:
            for i in range(header_row + 1, len(raw)):
                row   = raw.iloc[i]
                resp  = str(row.iloc[usa_col]).strip()
                tipo  = str(row.iloc[usa_col + 1]).strip() if usa_col + 1 < len(row) else ''
                vend  = str(row.iloc[usa_col + 2]).strip() if usa_col + 2 < len(row) else ''
                sede  = str(row.iloc[usa_col + 3]).strip() if usa_col + 3 < len(row) else ''
                total = str(row.iloc[usa_col + 4]).strip() if usa_col + 4 < len(row) else ''
                if resp and resp not in ['nan', '', 'RESPONSABLE']:
                    try:    total = float(total)
                    except: total = 0
                    data_usa.append({'Responsable': resp, 'Tipo de Diseño': tipo, 'Vendido En': vend, 'Sede': sede, 'Total': total})
        if esp_col is not None:
            for i in range(header_row + 1, len(raw)):
                row   = raw.iloc[i]
                resp  = str(row.iloc[esp_col]).strip()
                tipo  = str(row.iloc[esp_col + 1]).strip() if esp_col + 1 < len(row) else ''
                vend  = str(row.iloc[esp_col + 2]).strip() if esp_col + 2 < len(row) else ''
                sede  = str(row.iloc[esp_col + 3]).strip() if esp_col + 3 < len(row) else ''
                total = str(row.iloc[esp_col + 4]).strip() if esp_col + 4 < len(row) else ''
                if resp and resp not in ['nan', '', 'RESPONSABLE']:
                    try:    total = float(total)
                    except: total = 0
                    data_esp.append({'Responsable': resp, 'Tipo de Diseño': tipo, 'Vendido En': vend, 'Sede': sede, 'Total': total})
        return pd.DataFrame(data_usa), pd.DataFrame(data_esp)
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()


# ── CARGA AGENDA PENDIENTE ─────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def cargar_agenda_pendiente():
    try:
        url = sheet_url("Ventas diarias")
        raw = pd.read_csv(url, header=None)
        data_usa = []
        data_esp = []
        for i in range(min(50, len(raw))):
            for j in range(len(raw.columns)):
                val = str(raw.iloc[i, j]).strip().upper()
                if 'AGENDA PENDIENTE' in val and 'USA' in val:
                    header_row = i + 1
                    for k in range(header_row + 1, len(raw)):
                        row   = raw.iloc[k]
                        resp  = str(row.iloc[j]).strip()
                        dep   = str(row.iloc[j + 1]).strip() if j + 1 < len(row) else ''
                        fecha = str(row.iloc[j + 2]).strip() if j + 2 < len(row) else ''
                        tipo  = str(row.iloc[j + 3]).strip() if j + 3 < len(row) else ''
                        if resp and resp not in ['nan', '', 'RESPONSABLE']:
                            data_usa.append({'Responsable': resp, 'Depósito': dep, 'Fecha Pendiente': fecha, 'Tipo de Diseño': tipo})
                if 'AGENDA PENDIENTE' in val and 'ESPA' in val:
                    header_row = i + 1
                    for k in range(header_row + 1, len(raw)):
                        row   = raw.iloc[k]
                        resp  = str(row.iloc[j]).strip()
                        dep   = str(row.iloc[j + 1]).strip() if j + 1 < len(row) else ''
                        fecha = str(row.iloc[j + 2]).strip() if j + 2 < len(row) else ''
                        tipo  = str(row.iloc[j + 3]).strip() if j + 3 < len(row) else ''
                        if resp and resp not in ['nan', '', 'RESPONSABLE']:
                            data_esp.append({'Responsable': resp, 'Depósito': dep, 'Fecha Pendiente': fecha, 'Tipo de Diseño': tipo})
        return pd.DataFrame(data_usa), pd.DataFrame(data_esp)
    except:
        return pd.DataFrame(), pd.DataFrame()


# ── CARGA CAMPAÑAS META ADS ────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def cargar_campanas():
    try:
        dfs = []
        for tab, pais in [("USA 26", "🇺🇸 USA"), ("ESPAÑA 26", "🇪🇸 España")]:
            try:
                url = camp_sheet_url(tab)
                raw = pd.read_csv(url, header=None)
                header_idx = 0
                for i in range(min(5, len(raw))):
                    vals = [str(v).strip().lower() for v in raw.iloc[i].tolist()]
                    if 'campaign name' in vals:
                        header_idx = i
                        break
                df = pd.read_csv(url, skiprows=header_idx, header=0)
                df.columns = [str(c).strip() for c in df.columns]
                rename_map = {
                    'Campaign name':                      'Campaña',
                    'Ad set name':                        'Conjunto',
                    'Date':                               'Fecha',
                    'Clicks (all)':                       'Clicks',
                    'CTR (all)':                          'CTR',
                    'Frequency':                          'Frecuencia',
                    'Reach':                              'Alcance',
                    'Amount spent':                       'Inversion',
                    'CPC (cost per link click)':          'CPC',
                    'Cost per new messaging connection':  'Costo_Conexion',
                    'Link clicks':                        'Clicks_Link',
                    'Messaging conversations started':    'Conversaciones',
                    'New messaging contacts':             'Nuevos_Contactos',
                    'Post engagement':                    'Engagement',
                }
                df = df.rename(columns=rename_map)

                if 'Campaña' not in df.columns and len(df.columns) >= 14:
                    nuevas = ['Campaña', 'Conjunto', 'Fecha', 'Clicks', 'CTR', 'Frecuencia',
                              'Alcance', 'Inversion', 'CPC', 'Costo_Conexion', 'Clicks_Link',
                              'Conversaciones', 'Nuevos_Contactos', 'Engagement']
                    df.columns = nuevas + list(df.columns[14:])

                df['País'] = pais
                for col in ['Clicks', 'CTR', 'Frecuencia', 'Alcance', 'Inversion', 'CPC',
                            'Costo_Conexion', 'Clicks_Link', 'Conversaciones', 'Nuevos_Contactos', 'Engagement']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(
                            df[col].astype(str).str.replace(',', '.', regex=False),
                            errors='coerce',
                        ).fillna(0)
                if 'Fecha' in df.columns:
                    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
                    df = df[df['Fecha'].notna()]
                if 'Campaña' in df.columns:
                    df = df[df['Campaña'].notna()]
                    df = df[~df['Campaña'].astype(str).str.strip().isin(['', 'nan', 'None', 'Campaign name'])]
                    df = df[df['Alcance'] > 0]

                def extraer_sede(conjunto):
                    c = str(conjunto).upper()
                    if 'HOUSTON'   in c: return 'Houston'
                    if 'DALLAS'    in c: return 'Dallas'
                    if 'ANGELES'   in c: return 'Los Angeles'
                    if 'ORLANDO'   in c: return 'Orlando'
                    if 'JERSEY'    in c or 'JEERSEY' in c: return 'New Jersey'
                    if 'MIAMI'     in c: return 'Miami'
                    if 'ALICANTE'  in c: return 'Alicante'
                    if 'BARCELONA' in c: return 'Barcelona'
                    if 'MADRID'    in c: return 'Madrid'
                    if 'VALENCIA'  in c: return 'Valencia'
                    if 'MALAGA'    in c or 'MÁLAGA' in c: return 'Málaga'
                    if 'BILBAO'    in c: return 'Bilbao'
                    return 'Global'

                df['Sede'] = df['Conjunto'].apply(extraer_sede)
                dfs.append(df)
            except:
                continue
        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error campañas: {e}")
        return pd.DataFrame()


# ── HELPER ─────────────────────────────────────────────────────────────────────
def get_val(df, col):
    return int(df[col].sum()) if not df.empty and col in df.columns else 0


# ── CARGA VENTAS MES (AGENDADOS / REALIZADOS POR SEDE) ─────────────────────────
@st.cache_data(ttl=300)
def cargar_ventas_mes(pais: str):
    """
    Lee 'VENTAS MES DE JUNIO - USA' o 'VENTAS MES DE JUNIO - España'
    y devuelve un DataFrame con columnas:
    Sede, Sem1_Ag … Sem5_Ag, Total_Ag, Sem1_Re … Sem5_Re, Total_Re, % Conv
    """
    nombre = f"VENTAS MES DE JUNIO - {pais}"
    try:
        url = sheet_url(nombre)
        raw = pd.read_csv(url, header=None)

        SEDES_USA = ['DALLAS', 'HOUSTON', 'NEW JERSEY', 'ORLANDO', 'LOS ANGELES']
        SEDES_ESP = ['ALICANTE', 'BARCELONA', 'VALENCIA', 'MADRID', 'MALAGA', 'BILBAO']
        sedes_target = SEDES_USA if pais == 'USA' else SEDES_ESP

        rows = []
        for i in range(len(raw)):
            val = str(raw.iloc[i, 0]).strip().upper()
            for sede in sedes_target:
                if val == sede or sede in val:
                    fila = [str(v).strip() for v in raw.iloc[i].tolist()]

                    def to_num(v):
                        try: return float(v.replace(',', '.'))
                        except: return 0.0

                    nums = [to_num(v) for v in fila[1:] if v not in ('', 'nan', 'None', 'TOTAL', 'TOTALES')]
                    ag       = nums[0:5] if len(nums) >= 5 else (nums + [0] * (5 - len(nums)))
                    total_ag = nums[5]   if len(nums) > 5  else sum(ag)
                    re       = nums[6:11] if len(nums) >= 11 else ([0] * 5)
                    total_re = nums[11]   if len(nums) > 11  else sum(re)
                    rows.append({
                        'Sede':     sede.capitalize(),
                        'Sem1_Ag':  ag[0], 'Sem2_Ag': ag[1], 'Sem3_Ag': ag[2],
                        'Sem4_Ag':  ag[3], 'Sem5_Ag': ag[4], 'Total_Ag': total_ag,
                        'Sem1_Re':  re[0], 'Sem2_Re': re[1], 'Sem3_Re': re[2],
                        'Sem4_Re':  re[3], 'Sem5_Re': re[4], 'Total_Re': total_re,
                    })
                    break

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        total_row = {col: df[col].sum() if col != 'Sede' else 'TOTAL' for col in df.columns}
        df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
        df['% Conv'] = df.apply(
            lambda r: f"{round(r['Total_Re'] / r['Total_Ag'] * 100, 1)}%" if r['Total_Ag'] > 0 else '—', axis=1
        )
        return df
    except Exception as e:
        st.error(f"❌ Error ventas mes {pais}: {e}")
        return pd.DataFrame()