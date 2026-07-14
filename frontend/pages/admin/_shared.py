import streamlit as st


def _metric_card(label: str, value, delta: str = "", color: str = "#6C63FF"):
    st.markdown(
        f"""
        <div style='background:#1A1D2E; border-radius:10px; padding:1.1rem 1.4rem;
                    border-left:4px solid {color};'>
            <p style='color:#9B97C9; font-size:.8rem; margin:0;'>{label}</p>
            <p style='font-size:2rem; font-weight:700; margin:.1rem 0 0;
                      color:#E8E8F0;'>{value}</p>
            {f"<p style='color:{color}; font-size:.8rem; margin:0;'>{delta}</p>" if delta else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _badge(text: str, color: str):
    return (
        f"<span style='background:{color}22; color:{color}; border:1px solid {color}55; "
        f"border-radius:12px; padding:2px 10px; font-size:.78rem;'>{text}</span>"
    )


def _plotly_dark_layout(fig):
    fig.update_layout(
        plot_bgcolor="#0F1117",
        paper_bgcolor="#1A1D2E",
        font_color="#E8E8F0",
        xaxis=dict(gridcolor="#2A2D3E"),
        yaxis=dict(gridcolor="#2A2D3E"),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig