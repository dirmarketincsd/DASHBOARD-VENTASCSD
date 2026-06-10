import streamlit as st


def render_embudo_horizontal(titulo, etapas_vals, color_borde):
    st.markdown(f'<div style="color:{color_borde};font-size:0.8rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px">{titulo}</div>', unsafe_allow_html=True)
    items_html = ""
    for i, (etapa, val) in enumerate(etapas_vals):
        color_val = color_borde if str(val) != "—" and str(val) != "0" else "#555566"
        items_html += f"""
        <div style="display:inline-flex;flex-direction:column;align-items:center;justify-content:center;
                    background:linear-gradient(135deg,#0d0d0d,#1a1500);border:1px solid {color_borde};
                    border-radius:14px;padding:22px 20px;min-width:150px;min-height:110px;
                    text-align:center;vertical-align:top;
                    box-shadow:0 4px 15px rgba(0,0,0,0.3)">
            <div style="color:#8b9bb4;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.8px;
                        margin-bottom:12px;white-space:nowrap">{etapa}</div>
            <div style="color:{color_val};font-size:2.4rem;font-weight:800;line-height:1">{val}</div>
        </div>"""
        if i < len(etapas_vals) - 1:
            items_html += f"""
        <div style="display:inline-flex;align-items:center;justify-content:center;
                    padding:0 6px;vertical-align:top;margin-top:30px">
            <span style="color:{color_borde};font-size:1.5rem;font-weight:300">→</span>
        </div>"""
    st.markdown(f'<div style="overflow-x:auto;white-space:nowrap;padding-bottom:8px">{items_html}</div>', unsafe_allow_html=True)
