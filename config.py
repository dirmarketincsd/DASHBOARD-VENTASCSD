from urllib.parse import quote

# ── CONFIGURACIÓN GLOBAL ───────────────────────────────────────────────────────
SHEET_ID      = "1-KjGMIPUGcMynGfTYM7P68E_k0ylcZYeg0Wmgwd-36Q"
CAMP_SHEET_ID = "1RXbgTLoybDjfHUtnC0DC7dmvL9lHME005m9SqqYRouY"
PLOT_CFG      = dict(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
EQUIPOS_BASE  = {'ORLANDITO': 'USA', 'CAROLINA': 'USA', 'DANIELA': 'España', 'EVELYN': 'España'}

# Cambia estos 3 cada mes nuevo
PERIODO_LABEL = "Junio 2026"
SHEET_MES_USA = "VENTAS MES DE JUNIO - USA"
SHEET_MES_ESP = "VENTAS MES DE JUNIO - España"

META_DIARIA   = 3
META_SEMANAL  = 36
META_MENSUAL  = 144


def sheet_url(nombre):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre)}"


def camp_sheet_url(nombre):
    return f"https://docs.google.com/spreadsheets/d/{CAMP_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre)}"