"""
AQUA-CORE: HYGIEIA · OPEN-CORE PUBLIC EDITION
=============================================
Ecosistema: Yggdrasil Environmental Systems
Director Técnico & Autor: Kelvin Jesús Flores Yarihuaman (MECES Nivel 3 · EQF Level 7)
DOI Permanente (CERN / Zenodo): 10.5281/zenodo.23321969
Licencia: Creative Commons Attribution 4.0 International (CC-BY 4.0) / MIT

Marco Regulatorio Auditado:
- Real Decreto 3/2023, de 10 de enero (Calidad del Agua de Consumo Humano - PSA)
- Real Decreto 487/2022, de 21 de junio (Prevención y Control de Legionelosis)
- Orden DCA/1079/2026 (Saneamiento Temporal y Puntos de Agua en Emergencia)
- Orden TED/934/2022 (PERTE de Digitalización del Ciclo del Agua - Balance IWA)
- Directiva (UE) 2020/2184 & Reglamento (UE) 2024/1689 (AI Act Art. 14 HITL)
"""

import sys
import os
import math
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Configuración de rutas e importación del ecosistema
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

try:
    import freyja_ui
except Exception:
    freyja_ui = None

# Motores periciales de cálculo analítico y red neuronal informada por la física (Open-Core)
from core.planes_sanitarios_agua_rd3 import HygieiaSanitaryWaterEngine, AnaliticaAguaConsumoRD3
from core.modelo_cinetico_cloracion_thms import ModeloCineticoCloroTHM, ParametrosAguaRed
from core.evaluador_legionella_rd487 import EvaluadorLegionellaRD487, MedicionInstalacionACS
from core.gemelo_digital_redes_perte import GemeloDigitalRedesPERTE, SectorHidrometricoDMA
from core.saneamiento_temporal_emergencia import (
    DimensionadorSaneamientoEmergencia,
    ParametrosPuntoAguaTemporal,
    ParametrosSaneamientoAutonomo
)
from core.hygieia_pinn_surrogate import HygieiaPINNSurrogateModel
from physics.sentinel_sidecar import PhysicsSentinelSidecar

st.set_page_config(
    page_title="HYGIEIA | Open-Core DSS Planes Sanitarios del Agua · RD 3/2023",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS de alta visibilidad e interactividad táctica
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@600;700;800&display=swap');
    
    .stApp {
        background-color: #070B12;
        color: #F8FAFC;
        font-family: 'Inter', sans-serif;
    }
    .c2-header {
        background: linear-gradient(135deg, rgba(11,18,31,0.95) 0%, rgba(13,75,83,0.30) 100%);
        border: 1px solid #00D2FF44;
        border-radius: 12px;
        padding: 22px 28px;
        margin-bottom: 22px;
    }
    .metric-card {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .status-badge-ok {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10B981;
        color: #34D399;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.88rem;
        display: inline-block;
    }
    .status-badge-warn {
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid #F59E0B;
        color: #FBBF24;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.88rem;
        display: inline-block;
    }
    .status-badge-crit {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid #EF4444;
        color: #F87171;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.88rem;
        display: inline-block;
    }

    [data-testid="stSlider"] {
        margin-bottom: 6px;
    }
    [data-testid="stSlider"] label p {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        color: #F8FAFC !important;
    }
    [data-testid="stSlider"] div[data-baseweb="slider"] {
        padding-top: 6px !important;
        padding-bottom: 6px !important;
    }
    [data-testid="stSlider"] div[data-baseweb="slider"] > div:first-child {
        background: #1E293B !important;
        height: 6px !important;
        border-radius: 4px !important;
    }
    [data-testid="stSlider"] div[data-baseweb="slider"] > div:first-child > div {
        background: linear-gradient(90deg, #0284C7 0%, #00D2FF 100%) !important;
        height: 6px !important;
        border-radius: 4px !important;
    }
    [data-testid="stSlider"] div[role="slider"] {
        background: #00D2FF !important;
        border: 2px solid #FFFFFF !important;
        box-shadow: 0 0 10px rgba(0, 210, 255, 0.9), 0 0 20px rgba(0, 210, 255, 0.4) !important;
        width: 18px !important;
        height: 18px !important;
    }
    [data-testid="stSlider"] div[role="slider"] > div,
    [data-testid="stSliderThumbValue"],
    [data-testid="stSlider"] [data-baseweb="slider"] div[style*="font-size"] {
        color: #00F5A0 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
        font-weight: 800 !important;
        background: #0B121F !important;
        border: 1px solid #00D2FF !important;
        border-radius: 4px !important;
        padding: 2px 6px !important;
    }
    [data-testid="stSliderTickBar"] {
        display: flex !important;
        justify-content: space-between !important;
        width: 100% !important;
        padding-top: 2px !important;
    }
    [data-testid="stSliderTickBar"] > div,
    [data-testid="stSlider"] div[data-baseweb="slider"] ~ div,
    [data-testid="stSlider"] div[data-baseweb="slider"] ~ div span,
    [data-testid="stSlider"] div[data-baseweb="slider"] ~ div div {
        color: #38BDF8 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.80rem !important;
        font-weight: 700 !important;
        opacity: 1 !important;
        visibility: visible !important;
    }
</style>
""", unsafe_allow_html=True)


def render_slider_scale(min_val: str, max_val: str, current_val: str, legal_hint: str = ""):
    """Renderiza una barra de escala numérica de alto contraste y legibilidad para sliders."""
    hint_html = f"<span style='color: #F59E0B; font-size: 0.70rem; font-weight: 600;'>{legal_hint}</span>" if legal_hint else ""
    scale_html = f"""<div style="display: flex; justify-content: space-between; align-items: center; font-family: 'JetBrains Mono', monospace; font-size: 0.74rem; color: #38BDF8; margin-top: -6px; margin-bottom: 12px; background: rgba(15,23,42,0.55); padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(56,189,248,0.20);">
        <span><strong style="color: #94A3B8;">MÍN:</strong> <code style="color: #38BDF8; background: transparent;">{min_val}</code></span>
        <div style="text-align: center;">{hint_html} <span style="color: #00F5A0; font-weight: 800; background: rgba(0,245,160,0.12); padding: 2px 7px; border-radius: 4px; border: 1px solid rgba(0,245,160,0.3); margin-left: 6px;">VALOR: {current_val}</span></div>
        <span><strong style="color: #94A3B8;">MÁX:</strong> <code style="color: #38BDF8; background: transparent;">{max_val}</code></span>
    </div>"""
    st.markdown(scale_html, unsafe_allow_html=True)

# Encabezado Oficial de Hygieia Open-Core
st.markdown("""
<div class="c2-header">
    <div style="font-size: 0.78rem; font-family: monospace; color: #00D2FF; letter-spacing: 0.14em; font-weight: 700;">
        AQUA-CORE_HYGIEIA · DIGITAL TWIN & WATER SANITARY ENGINE
    </div>
    <h1 style="margin: 4px 0 6px 0; font-size: 2.15rem; font-weight: 800; color: #FFFFFF;">
        HYGIEIA · Calidad del Agua, PSA, Legionella & Gemelo Open-Core
    </h1>
    <div style="color: #94A3B8; font-size: 0.92rem;">
        Motor de ingeniería y bioseguridad hídrica bajo Real Decreto 3/2023, Real Decreto 487/2022 y PERTE del Agua (3.000 M€).
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar Táctico
with st.sidebar:
    badge_path = ROOT_DIR / "assets" / "branding" / "badge_dark.png"
    if not badge_path.exists():
        badge_path = ROOT_DIR / "assets" / "branding" / "badge.png"
    if badge_path.exists():
        st.image(str(badge_path), use_container_width=True)

    st.markdown("### 💧 HYGIEIA")
    st.markdown("<div style='font-size: 0.85rem; color: #38BDF8; font-weight: 700; letter-spacing: 0.5px;'>SISTEMA DE SOPORTE A LA DECISIÓN (DSS)</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 0.78rem; color: #94A3B8; margin-top: 2px;'>Planes Sanitarios del Agua (PSA) · RD 3/2023</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 0.75rem; color: #64748B; margin-top: 2px;'>Yggdrasil Environmental Systems · Madrid</div>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("""
    <div style="background: rgba(13, 75, 83, 0.35); border: 1.5px solid #00D2FF55; border-radius: 8px; padding: 12px 14px; margin-bottom: 14px;">
        <div style="font-size: 0.70rem; color: #38BDF8; font-weight: 800; text-transform: uppercase; letter-spacing: 0.8px; font-family: 'JetBrains Mono', monospace;">MODO DE OPERACIÓN</div>
        <div style="font-size: 0.95rem; color: #F8FAFC; font-weight: 800; margin-top: 3px;">🔓 OPEN-CORE EDICIÓN PÚBLICA</div>
        <div style="font-size: 0.74rem; color: #94A3B8; margin-top: 4px; line-height: 1.35;">Physics-Informed Neural Network (PINN) · Cinética Arrhenius sub-milisegundo (&lt;15 ms)</div>
        <div style="margin-top: 8px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.08); font-size: 0.70rem; color: #0284C7; font-family: 'JetBrains Mono', monospace;">
            <strong>CERN / Zenodo:</strong> <a href="https://doi.org/10.5281/zenodo.23321969" target="_blank" style="color: #38BDF8; text-decoration: none;">10.5281/zenodo.23321969</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("#### 📍 Territorio & Demostrador Oficial")
    st.markdown("• **Ámbito:** Comunidad de Madrid (España)<br>"
                "• **Operadora Matriz:** Canal de Isabel II<br>"
                "• **Código Municipal INE:** <code>28079</code> (Madrid)<br>"
                "• **Zona SINAC:** <code>ES-ZA-28079-MADRID01</code><br>"
                "• **Edificio Prioritario:** Complejo Sanitario de Referencia (Clase A)", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("#### 📜 Normas Españolas / UE Activas")
    st.markdown("• **RD 3/2023:** Calidad Agua Consumo (PSA)<br>"
                "• **RD 487/2022:** Prevención Legionelosis<br>"
                "• **Orden TED/934/2022:** PERTE del Agua<br>"
                "• **Directiva (UE) 2020/2184:** Aguas Consumo", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("#### 📚 Base Científica Epistémica")
    st.markdown("• Inactivación de patógenos y desinfección<br>"
                "• Cinética electroquímica y ozonización<br>"
                "• Manual PSA de la OMS (2ª Edición)<br>"
                "• Ecología microbiana de fontanería interior", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("""
    👑 **Director Técnico Titular:**<br>
    **Kelvin Jesús Flores Yarihuaman**<br>
    _Máster Universitario en Ing. y Gestión Ambiental_<br>
    _MECES Nivel 3 · EQF Level 7_<br>
    _Art. 335 LEC / ISO 27037_<br>
    <div style="margin-top: 10px; display: flex; flex-direction: column; gap: 6px;">
        <a href="https://www.linkedin.com/in/kelvinflores-ingenieria" target="_blank" style="display: inline-flex; align-items: center; gap: 6px; text-decoration: none; color: #00D2FF; font-size: 0.78rem; font-family: 'JetBrains Mono', monospace; background: rgba(0, 210, 255, 0.08); border: 1px solid rgba(0, 210, 255, 0.3); padding: 5px 8px; border-radius: 6px;">
            <span>💼</span> <span>LinkedIn: Kelvin Flores</span>
        </a>
        <a href="https://www.linkedin.com/company/yggdrasil-environmental-systems" target="_blank" style="display: inline-flex; align-items: center; gap: 6px; text-decoration: none; color: #00F5A0; font-size: 0.78rem; font-family: 'JetBrains Mono', monospace; background: rgba(0, 245, 160, 0.08); border: 1px solid rgba(0, 245, 160, 0.3); padding: 5px 8px; border-radius: 6px;">
            <span>🏢</span> <span>LinkedIn: Yggdrasil Systems</span>
        </a>
    </div>
    """, unsafe_allow_html=True)

# 6 Pestañas Temáticas Canónicas Open-Core
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🚰 Planes Sanitarios (RD 3/2023)",
    "🧪 Paradoja THMs vs Patógenos",
    "🦠 Legionelosis (RD 487/2022)",
    "🌐 Balance Hídrico IWA (PERTE)",
    "🚨 Saneamiento Temporal (Orden DCA/1079/2026)",
    "🧠 Motor PINN & Bóveda Epistémica"
])

with tab1:
    st.markdown("### 🚰 Auditoría de Planes Sanitarios del Agua (PSA) · RD 3/2023")
    st.markdown("Evaluación pericial determinista de conformidad sanitaria bajo el **Real Decreto 3/2023** y la **Directiva (UE) 2020/2184**.")
    
    col_in1, col_in2, col_in3 = st.columns(3)
    with col_in1:
        st.markdown("##### 📍 Ubicación e Indicadores Clave")
        punto_muestreo = st.text_input("Punto de Muestreo", value="Red Canal de Isabel II - Madrid Centro / Castellana (INE 28079)")
        cloro_libre = st.slider("Cloro Libre Residual (mg/L)", min_value=0.0, max_value=2.5, value=0.65, step=0.05,
                                help="Exigencia legal RD 3/2023: 0.20 - 1.00 mg/L en red")
        render_slider_scale("0.00 mg/L", "2.50 mg/L", f"{cloro_libre:.2f} mg/L", "RD 3/2023: 0.20 - 1.00 mg/L")
        turbidez = st.slider("Turbidez (UNF)", min_value=0.0, max_value=8.0, value=1.20, step=0.1,
                             help="Límite máximo en red de distribución: <= 4.0 UNF")
        render_slider_scale("0.00 UNF", "8.00 UNF", f"{turbidez:.2f} UNF", "Límite legal: ≤ 4.0 UNF")
    
    with col_in2:
        st.markdown("##### ⚗️ Parámetros Físico-Químicos")
        ph = st.slider("pH del Agua", min_value=5.0, max_value=11.0, value=7.45, step=0.05,
                       help="Rango de calidad: 6.5 - 9.5")
        render_slider_scale("5.00 pH", "11.00 pH", f"{ph:.2f} pH", "Rango legal: 6.50 - 9.50")
        conductividad = st.number_input("Conductividad a 20°C (µS/cm)", min_value=50.0, max_value=4000.0, value=480.0, step=10.0,
                                        help="Límite legal: <= 2500 µS/cm")
        cloratos = st.number_input("Cloratos (mg/L)", min_value=0.0, max_value=1.5, value=0.08, step=0.01,
                                   help="Límite legal RD 3/2023: <= 0.25 mg/L")
    
    with col_in3:
        st.markdown("##### 🧫 Microbiología y Contaminantes Emergentes")
        e_coli = st.number_input("Escherichia coli (UFC/100ml)", min_value=0, max_value=100, value=0, step=1,
                                help="Límite legal: 0 UFC/100ml")
        enterococos = st.number_input("Enterococos (UFC/100ml)", min_value=0, max_value=100, value=0, step=1,
                                     help="Límite legal: 0 UFC/100ml")
        pfas_20 = st.number_input("Suma 20 PFAS (µg/L)", min_value=0.0, max_value=1.0, value=0.02, step=0.01,
                                  help="Límite legal RD 3/2023: <= 0.10 µg/L")

    analitica = AnaliticaAguaConsumoRD3(
        punto_muestreo=punto_muestreo,
        cloro_libre_residual_mg_l=cloro_libre,
        turbidez_unf=turbidez,
        ph=ph,
        conductividad_us_cm=conductividad,
        e_coli_ufc_100ml=e_coli,
        enterococos_ufc_100ml=enterococos,
        suma_20_pfas_ug_l=pfas_20,
        cloratos_mg_l=cloratos
    )

    dictamen = HygieiaSanitaryWaterEngine.auditar_calidad_agua_rd3(analitica)
    
    st.markdown("---")
    st.markdown("#### 📋 Telemetría Sanitaria y Huella Multiparamétrica en Tiempo Real")
    
    c_res1, c_res2, c_res3, c_res4 = st.columns(4)
    c_res1.metric("Cloro Libre", f"{dictamen['cloro_libre_mg_l']:.2f} mg/L", delta="Conforme (0.20-1.00)" if 0.20 <= dictamen['cloro_libre_mg_l'] <= 1.00 else "Desviación")
    c_res2.metric("Turbidez", f"{dictamen['turbidez_unf']:.2f} UNF", delta="Conforme (≤4.0)" if dictamen['turbidez_unf'] <= 4.0 else "Elevada", delta_color="inverse")
    c_res3.metric("pH", f"{dictamen['ph']:.2f}", delta="Conforme (6.5-9.5)" if 6.5 <= dictamen['ph'] <= 9.5 else "Desviación")
    c_res4.metric("Microbiología", "0 Incidencias" if dictamen['microbiologia_conforme'] else "PATÓGENOS DETECTADOS", delta_color="normal" if dictamen['microbiologia_conforme'] else "inverse")
    
    # ==============================================================================
    # GRÁFICA INTERACTIVA 1: RADAR HEXAGONAL DE HUELLA SANITARIA (RD 3/2023)
    # ==============================================================================
    pct_cloro = (cloro_libre / 1.00) * 100.0 if cloro_libre >= 0.20 else (cloro_libre / 0.20) * 50.0
    pct_turb = (turbidez / 4.0) * 100.0
    pct_ph = (abs(ph - 7.5) / 1.5) * 100.0
    pct_cond = (conductividad / 2500.0) * 100.0
    pct_cloratos = (cloratos / 0.25) * 100.0
    pct_pfas = (pfas_20 / 0.10) * 100.0

    categorias = [
        f"Cloro Libre<br>({cloro_libre:.2f} mg/L)",
        f"Turbidez<br>({turbidez:.2f} UNF)",
        f"Desviación pH<br>({ph:.2f})",
        f"Conductividad<br>({conductividad:.0f} µS/cm)",
        f"Cloratos<br>({cloratos:.2f} mg/L)",
        f"Suma 20 PFAS<br>({pfas_20:.2f} µg/L)"
    ]

    valores_muestra = [
        min(135.0, pct_cloro),
        min(135.0, pct_turb),
        min(135.0, pct_ph),
        min(135.0, pct_cond),
        min(135.0, pct_cloratos),
        min(135.0, pct_pfas)
    ]
    valores_c = valores_muestra + [valores_muestra[0]]
    cat_c = categorias + [categorias[0]]
    limite_c = [100.0] * len(cat_c)

    es_conforme_radar = (0.20 <= cloro_libre <= 1.00) and (turbidez <= 4.0) and (6.5 <= ph <= 9.5) and (conductividad <= 2500.0) and (cloratos <= 0.25) and (pfas_20 <= 0.10) and (e_coli == 0) and (enterococos == 0)

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=limite_c,
        theta=cat_c,
        name="Umbral Máximo Legal (100% RD 3/2023)",
        line=dict(color="#F59E0B", width=2, dash="dash"),
        fill='toself',
        fillcolor='rgba(245, 158, 11, 0.08)'
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=valores_c,
        theta=cat_c,
        name="Muestra en Tiempo Real",
        line=dict(color="#00F5A0" if es_conforme_radar else "#EF4444", width=3),
        fill='toself',
        fillcolor='rgba(0, 245, 160, 0.25)' if es_conforme_radar else 'rgba(239, 68, 68, 0.35)'
    ))
    fig_radar.update_layout(
        title=dict(
            text="<b>🕸️ HUELLA DIGITAL SANITARIA · CONFORMIDAD MULTIPARAMÉTRICA RD 3/2023</b>",
            font=dict(family="Space Grotesk, sans-serif", size=14, color="#F8FAFC")
        ),
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 130],
                tickvals=[25, 50, 75, 100, 125],
                ticktext=["25%", "50%", "75%", "100% LÍMITE", "125% ALERTA"],
                tickfont=dict(color="#94A3B8", size=9, family="JetBrains Mono"),
                gridcolor="#1E293B",
                linecolor="#334155"
            ),
            angularaxis=dict(
                tickfont=dict(color="#CBD5E1", size=10, family="JetBrains Mono"),
                gridcolor="#1E293B",
                linecolor="#334155"
            ),
            bgcolor="rgba(11, 18, 31, 0.85)"
        ),
        paper_bgcolor="#0A0E17",
        plot_bgcolor="#0A0E17",
        height=410,
        margin=dict(l=60, r=60, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=-0.16, xanchor="center", x=0.5, font=dict(color="#CBD5E1"))
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    if dictamen['calificacion_rd3_2023'] == "AGUA APTA PARA EL CONSUMO HUMANO":
        st.markdown(f'<div class="status-badge-ok">✅ {dictamen["calificacion_rd3_2023"]}</div>', unsafe_allow_html=True)
        st.success(dictamen['dictamen_psa'])
    else:
        st.markdown(f'<div class="status-badge-crit">🚨 {dictamen["calificacion_rd3_2023"]}</div>', unsafe_allow_html=True)
        st.error(dictamen['dictamen_psa'])
        st.markdown("##### ⚠️ Alertas Sanitarias Específicas:")
        for al in dictamen['alertas_sanitarias']:
            st.markdown(f"- 🔴 **{al}**")

# ==============================================================================
# TAB 2: PARADOJA DE LOS TRIHALOMETANOS (THMs) VS PATÓGENOS
# ==============================================================================

with tab2:
    st.markdown("### 🧪 Modelado Cinético: Paradoja THMs vs. Patógenos")
    st.markdown("""
    **El conflicto central del abastecimiento:** Garantizar suficiente desinfección residual ($C_{libre} \ge 0.20\ \text{mg/L}$)
    para prevenir la multiplicación de patógenos sin inducir la formación de subproductos carcinógenos
    ($\text{TTHMs} \le 100\ \mu\text{g/L}$ según el **RD 3/2023** y la **Directiva UE 2020/2184**).
    """)
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        c0_input = st.slider("Dosis Inicial Cloro $C_0$ (mg/L)", min_value=0.50, max_value=3.00, value=1.25, step=0.05,
                             help="Dosis a la salida de depósito o potabilizadora")
        render_slider_scale("0.50 mg/L", "3.00 mg/L", f"{c0_input:.2f} mg/L", "Salida Potabilizadora")
        toc_input = st.slider("TOC - Materia Orgánica Precursora (mg/L)", min_value=0.20, max_value=6.00, value=2.20, step=0.10,
                              help="Carbono Orgánico Total reactivo")
        render_slider_scale("0.20 mg/L", "6.00 mg/L", f"{toc_input:.2f} mg/L", "Precursor THMs")
    with col_p2:
        ph_input = st.slider("pH del Agua en Red", min_value=6.5, max_value=9.0, value=7.6, step=0.1,
                             help="A mayor pH se acelera la cinética de formación de THMs")
        render_slider_scale("6.50 pH", "9.00 pH", f"{ph_input:.2f} pH", "Cinética de Formación")
        temp_input = st.slider("Temperatura del Agua (°C)", min_value=8.0, max_value=32.0, value=21.0, step=1.0,
                               help="Efecto Arrhenius en el decaimiento de cloro y reacción")
        render_slider_scale("8.0 °C", "32.0 °C", f"{temp_input:.1f} °C", "Arrhenius Térmico")
    with col_p3:
        horas_input = st.slider("Tiempo de Tránsito / Residencia (horas)", min_value=1.0, max_value=72.0, value=28.0, step=1.0,
                                help="Tiempo hidráulico hasta el grifo terminal")
        render_slider_scale("1.0 h", "72.0 h", f"{horas_input:.0f} h", "Tránsito Hidráulico")
        uv254_input = st.number_input("Absorbancia UV254 (cm⁻¹)", min_value=0.01, max_value=0.20, value=0.045, step=0.005)

    params_red = ParametrosAguaRed(
        cloro_inicial_mg_l=c0_input,
        toc_mg_l=toc_input,
        ph=ph_input,
        temperatura_c=temp_input,
        tiempo_residencia_horas=horas_input,
        uv254_cm_1=uv254_input
    )

    sim_thm = ModeloCineticoCloroTHM.simular_formacion_thms(params_red)
    
    st.markdown("---")
    c_met1, c_met2, c_met3, c_met4 = st.columns(4)
    cloro_fin = sim_thm['cloro_residual_final_mg_l']
    thm_fin = sim_thm['tthm_final_ug_l']
    k_dec = sim_thm['constante_decaimiento_k_h1']
    
    c_met1.metric("Cloro en Grifo Terminal", f"{cloro_fin:.3f} mg/L",
                  delta="Conforme (>=0.20)" if cloro_fin >= 0.20 else "Sub-dosificado (<0.20)",
                  delta_color="normal" if cloro_fin >= 0.20 else "inverse")
    c_met2.metric("Concentración TTHMs", f"{thm_fin:.1f} µg/L",
                  delta="Conforme (<=100)" if thm_fin <= 100.0 else "TÓXICO (>100)",
                  delta_color="normal" if thm_fin <= 100.0 else "inverse")
    c_met3.metric("Constante Decaimiento (k)", f"{k_dec:.4f} h⁻¹")
    c_met4.metric("Diagnóstico Paradoja", sim_thm['estado_paradoja'].replace("_", " "))

    if sim_thm['estado_paradoja'] == "OPTIMO_EQUILIBRIO_RD3":
        st.markdown(f'<div class="status-badge-ok">✅ {sim_thm["dictamen_pericial"]}</div>', unsafe_allow_html=True)
    elif sim_thm['estado_paradoja'] == "BRECHA_MICROBIOLOGICA":
        st.markdown(f'<div class="status-badge-warn">⚠️ {sim_thm["dictamen_pericial"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-badge-crit">🚨 {sim_thm["dictamen_pericial"]}</div>', unsafe_allow_html=True)

    # Gráfico Cinético Temporal Dual (Plotly)
    df_curva = pd.DataFrame(sim_thm['curva_simulacion'])
    
    fig = go.Figure()
    # Curva Cloro
    fig.add_trace(go.Scatter(
        x=df_curva['tiempo_horas'], y=df_curva['cloro_residual_mg_l'],
        name="Cloro Residual C(t) [mg/L]",
        line=dict(color="#00D2FF", width=3),
        yaxis="y1"
    ))
    # Curva THMs
    fig.add_trace(go.Scatter(
        x=df_curva['tiempo_horas'], y=df_curva['tthm_ug_l'],
        name="TTHMs Formados [µg/L]",
        line=dict(color="#EF4444", width=3, dash="dot"),
        yaxis="y2"
    ))
    # Línea umbral legal Cloro (0.20 mg/L)
    fig.add_hline(y=0.20, line_dash="dash", line_color="#F59E0B", annotation_text="Límite Mínimo Cloro (0.20 mg/L)", yref="y1")
    # Línea umbral legal THMs (100 ug/L)
    fig.add_hline(y=100.0, line_dash="dash", line_color="#DC2626", annotation_text="Límite Máximo RD 3/2023 (100 µg/L)", yref="y2")

    fig.update_layout(
        title="Cinética de Decaimiento de Cloro vs. Formación Progresiva de THMs",
        template="plotly_dark",
        paper_bgcolor="#0A0E17",
        plot_bgcolor="#0A0E17",
        xaxis=dict(title="Tiempo de Tránsito Hidráulico en Red (Horas)"),
        yaxis=dict(title="Cloro Residual (mg/L)", range=[0, max(2.0, c0_input * 1.1)]),
        yaxis2=dict(title="Trihalometanos Totales (µg/L)", overlaying="y", side="right", range=[0, max(120, thm_fin * 1.2)]),
        legend=dict(x=0.02, y=0.98),
        margin=dict(l=40, r=40, t=50, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)


with tab3:
    st.markdown("### 🦠 Auditoría de Prevención y Control de Legionelosis · RD 487/2022")
    st.markdown("Evaluación pericial de instalaciones de riesgo y edificios prioritarios (hospitales, residencias, hoteles).")
    
    col_l1, col_l2, col_l3 = st.columns(3)
    with col_l1:
        st.markdown("##### 🏢 Instalación y Régimen")
        id_edificio = st.text_input("Identificador Edificio", value="Centro Sanitario Prioritario (Clase A - RD 487/2022) - Bloque Quirúrgico")
        tipo_sistema = st.selectbox("Tipo de Instalación", ["ACS_CON_RETORNO", "ACS_SIN_RETORNO", "TORRE_REFRIGERACION"])
        dias_purga = st.number_input("Días desde última purga de fondo", min_value=0, max_value=60, value=4, step=1,
                                     help="Exigencia: purga semanal de acumuladores para evitar lodos")
    
    with col_l2:
        st.markdown("##### 🌡️ Bioseguridad Térmica (RD 487/2022)")
        temp_acum = st.slider("Temp. Acumulador ACS (°C)", min_value=40.0, max_value=75.0, value=62.5, step=0.5,
                              help="Exigencia legal: >= 60.0 °C continuo")
        render_slider_scale("40.0 °C", "75.0 °C", f"{temp_acum:.1f} °C", "RD 487/2022: ≥ 60.0 °C")
        temp_ret = st.slider("Temp. Anillo Retorno (°C)", min_value=35.0, max_value=65.0, value=51.5, step=0.5,
                             help="Exigencia legal: >= 50.0 °C en retorno")
        render_slider_scale("35.0 °C", "65.0 °C", f"{temp_ret:.1f} °C", "RD 487/2022: ≥ 50.0 °C")
        temp_grifo = st.slider("Temp. Grifo Terminal Alejado (°C)", min_value=30.0, max_value=65.0, value=50.2, step=0.5,
                               help="Exigencia legal: >= 50.0 °C antes de 1 minuto")
        render_slider_scale("30.0 °C", "65.0 °C", f"{temp_grifo:.1f} °C", "RD 487/2022: ≥ 50.0 °C (<1 min)")
        temp_afch = st.slider("Temp. Agua Fría AFCH (°C)", min_value=8.0, max_value=30.0, value=18.5, step=0.5,
                              help="Exigencia legal: <= 20.0 °C")
        render_slider_scale("8.0 °C", "30.0 °C", f"{temp_afch:.1f} °C", "RD 487/2022: ≤ 20.0 °C")
    
    with col_l3:
        st.markdown("##### 🧪 Analítica de Legionella y Biocida")
        ufc_legionella = st.number_input("Recuento Legionella (UFC/L)", min_value=0.0, max_value=15000.0, value=0.0, step=50.0,
                                         help="<100 Conforme | 100-1000 Alerta preventiva | >1000 Choque inmediato")
        biocida_residual = st.slider("Biocida Residual (mg/L)", min_value=0.0, max_value=3.0, value=0.55, step=0.05)
        render_slider_scale("0.00 mg/L", "3.00 mg/L", f"{biocida_residual:.2f} mg/L", "Barrera Biocida")

    med_leg = MedicionInstalacionACS(
        identificador_edificio=id_edificio,
        tipo_sistema=tipo_sistema,
        temp_acumulador_c=temp_acum,
        temp_retorno_c=temp_ret,
        temp_grifo_alejado_c=temp_grifo,
        temp_afch_c=temp_afch,
        recuento_legionella_ufc_l=ufc_legionella,
        biocida_residual_mg_l=biocida_residual,
        dias_desde_ultima_purga=dias_purga
    )

    dict_leg = EvaluadorLegionellaRD487.auditar_instalacion(med_leg)
    
    st.markdown("---")
    st.markdown("#### 🌡️ Telemetría de Bioseguridad Térmica y Diagnóstico en Tiempo Real")
    c_leg1, c_leg2, c_leg3, c_leg4 = st.columns(4)
    c_leg1.metric("Score Bioseguridad", f"{dict_leg['score_bioseguridad']} / 100")
    c_leg2.metric("Estado de Alerta", dict_leg['nivel_alerta'].replace("_", " "))
    c_leg3.metric("Conformidad Global", "CONFORME" if dict_leg['conformidad_global'] else "DESVIACIÓN",
                  delta_color="normal" if dict_leg['conformidad_global'] else "inverse")
    c_leg4.metric("No Conformidades", f"{len(dict_leg['no_conformidades_formales'])}")

    # ==============================================================================
    # GRÁFICA INTERACTIVA 3: PERFIL TÉRMICO ACS VS ZONA DE RIESGO LEGIONELLA
    # ==============================================================================
    st.markdown("##### 📈 Perfil Térmico Longitudinal del Circuito ACS vs. Zonas de Proliferación (RD 487/2022)")
    
    nodos_acs = [
        "1. Acumulador ACS",
        "2. Salida Acometida",
        "3. Troncal Distribución",
        "4. Ramal Secundario",
        "5. Grifo Alejado",
        "6. Retorno Inicial",
        "7. Anillo Retorno (Bomba)",
        "8. Retorno a Caldera"
    ]
    
    t_acum_v = temp_acum
    t_grifo_v = temp_grifo
    t_ret_v = temp_ret
    
    temperaturas_acs = [
        round(t_acum_v, 1),
        round(t_acum_v - 1.2, 1),
        round(t_acum_v - 3.8, 1),
        round((t_acum_v + t_grifo_v) / 2.0, 1),
        round(t_grifo_v, 1),
        round((t_grifo_v + t_ret_v) / 2.0, 1),
        round(t_ret_v, 1),
        round(t_ret_v - 0.6, 1)
    ]

    colores_puntos = [
        "#00F5A0" if t >= 50.0 else "#EF4444" for t in temperaturas_acs
    ]

    fig_term = go.Figure()

    # Zonas Biológicas de Legionella pneumophila (Bandas de fondo)
    fig_term.add_hrect(y0=60.0, y1=80.0, fillcolor="rgba(16, 185, 129, 0.12)", layer="below", line_width=0, annotation_text="Zona Pasteurización Rápida (>60°C)", annotation_position="top left", annotation_font_size=9, annotation_font_color="#10B981")
    fig_term.add_hrect(y0=50.0, y1=60.0, fillcolor="rgba(0, 210, 255, 0.08)", layer="below", line_width=0, annotation_text="Zona de Inhibición Segura (50-60°C)", annotation_position="top left", annotation_font_size=9, annotation_font_color="#38BDF8")
    fig_term.add_hrect(y0=20.0, y1=50.0, fillcolor="rgba(239, 68, 68, 0.16)", layer="below", line_width=0, annotation_text="ZONA ROJA CRÍTICA: Proliferación Exponencial Legionella (20-50°C)", annotation_position="top left", annotation_font_size=9, annotation_font_color="#F87171")
    fig_term.add_hrect(y0=8.0, y1=20.0, fillcolor="rgba(56, 189, 248, 0.08)", layer="below", line_width=0, annotation_text="Zona AFCH Agua Fría (<20°C)", annotation_position="top left", annotation_font_size=9, annotation_font_color="#38BDF8")

    # Líneas de referencia legal RD 487/2022
    fig_term.add_hline(y=60.0, line_dash="dash", line_color="#10B981")
    fig_term.add_hline(y=50.0, line_dash="dash", line_color="#F59E0B")
    fig_term.add_hline(y=20.0, line_dash="dash", line_color="#38BDF8")

    # Traza ACS
    fig_term.add_trace(go.Scatter(
        x=nodos_acs,
        y=temperaturas_acs,
        mode="lines+markers+text",
        text=[f"<b>{t:.1f}°C</b>" for t in temperaturas_acs],
        textposition="top center",
        textfont=dict(family="JetBrains Mono", size=10, color="#FFFFFF"),
        line=dict(color="#00D2FF", width=3.5),
        marker=dict(size=12, color=colores_puntos, line=dict(color="#FFFFFF", width=2)),
        name="Perfil Térmico Red ACS"
    ))

    # Punto AFCH
    fig_term.add_trace(go.Scatter(
        x=["9. Red AFCH (Agua Fría)"],
        y=[temp_afch],
        mode="markers+text",
        text=[f"<b>{temp_afch:.1f}°C</b>"],
        textposition="top center",
        textfont=dict(family="JetBrains Mono", size=10, color="#FFFFFF"),
        marker=dict(size=14, color="#38BDF8" if temp_afch <= 20.0 else "#EF4444", symbol="diamond", line=dict(color="#FFFFFF", width=2)),
        name="Agua Fría AFCH"
    ))

    fig_term.update_layout(
        title="<b>MAPA TÉRMICO BIOSEGURIDAD: ACUMULADOR ➔ DISTRIBUCIÓN ➔ RETORNO (RD 487/2022)</b>",
        template="plotly_dark",
        paper_bgcolor="#0A0E17",
        plot_bgcolor="#0A0E17",
        xaxis=dict(title="Punto de Medición en Circuito del Edificio", gridcolor="#1E293B", tickfont=dict(family="JetBrains Mono", size=9, color="#CBD5E1")),
        yaxis=dict(title="Temperatura (°C)", range=[10.0, 75.0], gridcolor="#1E293B", tickfont=dict(family="JetBrains Mono", size=10, color="#CBD5E1")),
        margin=dict(l=40, r=40, t=50, b=50),
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_term, use_container_width=True)

    if dict_leg['nivel_alerta'] == "CONFORME_BIOSEGURA":
        st.markdown(f'<div class="status-badge-ok">✅ {dict_leg["protocolo_sanitario_rd487"]}</div>', unsafe_allow_html=True)
    elif dict_leg['nivel_alerta'] == "ALERTA_PREVENTIVA":
        st.markdown(f'<div class="status-badge-warn">⚠️ {dict_leg["protocolo_sanitario_rd487"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-badge-crit">🚨 {dict_leg["protocolo_sanitario_rd487"]}</div>', unsafe_allow_html=True)

    if len(dict_leg['no_conformidades_formales']) > 0:
        st.markdown("##### 🚨 Desglose de No Conformidades Normativas:")
        for nc in dict_leg['no_conformidades_formales']:
            st.markdown(f"- ⚠️ **[{nc['severidad']}] {nc['clausula']}:** {nc['descripcion']}<br>&nbsp;&nbsp;&nbsp;&nbsp;↳ _Acción pericial:_ `{nc['accion_inmediata']}`", unsafe_allow_html=True)

    if len(dict_leg['alertas_operativas']) > 0:
        st.markdown("##### ⚠️ Alertas Operativas:")
        for al_op in dict_leg['alertas_operativas']:
            st.markdown(f"- 🟡 {al_op}")

# ==============================================================================
# TAB 4: GEMELO DIGITAL Y BALANCE HÍDRICO PERTE (3.000 M€)
# ==============================================================================

with tab4:
    st.markdown("### 🌐 Gemelo Digital de Redes y Balance Hídrico PERTE (3.000 M€)")
    st.markdown("""
    Cálculo del balance hídrico estándar **IWA**, detección de fugas invisibles mediante **Caudal Mínimo Nocturno (MNF)**
    y generación del payload interoperable oficial para el **PERTE del Agua** (Orden TED/934/2022) y el **SINAC**.
    """)
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown("##### 🏙️ Topología del Sector Hidrométrico (DMA)")
        nombre_sector = st.text_input("Denominación del Sector", value="DMA-04 Madrid Norte / Castellana - Chamartín (Canal de Isabel II)")
        poblacion = st.number_input("Población Servida (habitantes)", min_value=100, max_value=500000, value=15400, step=500)
        longitud_red = st.number_input("Longitud de Red (km)", min_value=1.0, max_value=1000.0, value=38.5, step=0.5)
        presion_media = st.slider("Presión Media de Servicio (bar)", min_value=1.0, max_value=8.0, value=3.8, step=0.1)
        render_slider_scale("1.0 bar", "8.0 bar", f"{presion_media:.1f} bar", "CTE DB-HS 4: 1.5 - 5.0 bar")

    with col_d2:
        st.markdown("##### 📊 Telemetría Hidráulica y Caudales")
        vol_suministrado = st.number_input("Volumen Suministrado Diario (m³/día)", min_value=10.0, max_value=100000.0, value=3850.0, step=50.0)
        vol_facturado = st.number_input("Volumen Facturado / Registrado (m³/día)", min_value=10.0, max_value=100000.0, value=2950.0, step=50.0)
        mnf_caudal = st.number_input("Caudal Mínimo Nocturno MNF [02:00 - 04:00 AM] (m³/h)", min_value=0.0, max_value=1000.0, value=48.0, step=1.0)
        consumo_legitimo = st.number_input("Consumo Nocturno Legítimo Estimado (m³/h)", min_value=0.0, max_value=500.0, value=12.5, step=0.5)

    dma_sector = SectorHidrometricoDMA(
        nombre_sector=nombre_sector,
        poblacion_servida=poblacion,
        longitud_red_km=longitud_red,
        presion_media_bar=presion_media,
        volumen_suministrado_diario_m3=vol_suministrado,
        volumen_facturado_diario_m3=vol_facturado,
        caudal_minimo_nocturno_m3_h=mnf_caudal,
        consumo_legitimo_nocturno_m3_h=consumo_legitimo
    )

    balance = GemeloDigitalRedesPERTE.calcular_balance_hidrico_iwa(dma_sector)
    
    st.markdown("---")
    st.markdown("#### 💧 Indicadores de Eficiencia Hídrica IWA y PERTE")
    
    c_iwa1, c_iwa2, c_iwa3, c_iwa4 = st.columns(4)
    c_iwa1.metric("Agua No Registrada (ANR)", f"{balance['porcentaje_anr']}%",
                  delta="Meta PERTE (<15%)" if balance['cumple_meta_perte_15_porc'] else "Sobre Umbral (>15%)",
                  delta_color="normal" if balance['cumple_meta_perte_15_porc'] else "inverse")
    c_iwa2.metric("Pérdidas Reales (Fugas)", f"{balance['perdidas_reales_fugas_m3_dia']} m³/día")
    c_iwa3.metric("Pérdidas Aparentes", f"{balance['perdidas_aparentes_subcontaje_m3_dia']} m³/día")
    c_iwa4.metric("Pérdidas Específicas", f"{balance['perdidas_especificas_m3_km_dia']} m³/km/día")

    if balance['estado_perte'] == "EFICIENTE_SOSTENIBLE":
        st.markdown(f'<div class="status-badge-ok">✅ ESTADO PERTE: {balance["estado_perte"]}</div>', unsafe_allow_html=True)
    elif balance['estado_perte'] == "MODERADO_MEJORABLE":
        st.markdown(f'<div class="status-badge-warn">⚠️ ESTADO PERTE: {balance["estado_perte"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-badge-crit">🚨 ESTADO PERTE: {balance["estado_perte"]} (Alta Elegibilidad Subvención)</div>', unsafe_allow_html=True)
    
    st.info(f"📌 **Dictamen Técnico PERTE:** {balance['dictamen_perte']}")

    # ==============================================================================
    # GRÁFICA INTERACTIVA 4: DIAGRAMA DE FLUJO SANKEY IWA (ESTÁNDAR PERTE DEL AGUA)
    # ==============================================================================
    st.markdown("##### 🌊 Diagrama de Flujo y Balance Hídrico IWA (Estándar Oficial MITECO / PERTE)")
    
    v_sum = float(vol_suministrado)
    v_fact = float(vol_facturado)
    v_no_fact = max(5.0, round(v_sum * 0.02, 1))
    v_autorizado = v_fact + v_no_fact
    
    v_fugas = float(balance['perdidas_reales_fugas_m3_dia'])
    v_aparentes = float(balance['perdidas_aparentes_subcontaje_m3_dia'])
    v_perdidas_tot = v_fugas + v_aparentes

    labels_sankey = [
        f"0. Suministro Total DMA<br><b>{v_sum:,.0f} m³/día</b>",
        f"1. Consumo Autorizado<br><b>{v_autorizado:,.0f} m³/día</b>",
        f"2. Pérdidas de Agua (ANR)<br><b>{v_perdidas_tot:,.0f} m³/día</b>",
        f"3. Facturado Registrado<br><b>{v_fact:,.0f} m³/día</b>",
        f"4. Municipal No Facturado<br><b>{v_no_fact:,.0f} m³/día</b>",
        f"5. Pérdidas Aparentes (Subcontaje)<br><b>{v_aparentes:,.0f} m³/día</b>",
        f"6. Pérdidas Reales (Fugas Red)<br><b>{v_fugas:,.0f} m³/día</b>"
    ]

    colores_nodos = [
        "#00D2FF",  # 0 Suministro (Cian)
        "#10B981",  # 1 Autorizado (Verde)
        "#EF4444",  # 2 Pérdidas (Rojo)
        "#00F5A0",  # 3 Facturado (Esmeralda)
        "#38BDF8",  # 4 No Facturado (Azul)
        "#F59E0B",  # 5 Subcontaje (Ámbar)
        "#DC2626"   # 6 Fugas Físicas (Carmesí)
    ]

    source_indices = [0, 0, 1, 1, 2, 2]
    target_indices = [1, 2, 3, 4, 5, 6]
    valores_enlaces = [v_autorizado, v_perdidas_tot, v_fact, v_no_fact, v_aparentes, v_fugas]

    colores_enlaces = [
        "rgba(16, 185, 129, 0.40)",
        "rgba(239, 68, 68, 0.45)",
        "rgba(0, 245, 160, 0.40)",
        "rgba(56, 189, 248, 0.35)",
        "rgba(245, 158, 11, 0.40)",
        "rgba(220, 38, 38, 0.55)"
    ]

    fig_sankey = go.Figure(data=[go.Sankey(
        arrangement="snap",
        node=dict(
            pad=18,
            thickness=22,
            line=dict(color="#0B121F", width=1.5),
            label=labels_sankey,
            color=colores_nodos
        ),
        link=dict(
            source=source_indices,
            target=target_indices,
            value=valores_enlaces,
            color=colores_enlaces
        )
    )])

    fig_sankey.update_layout(
        title="<b>BALANCE HÍDRICO ESTÁNDAR IWA / MITECO: DESGLOSE DE CONSUMO VS. FUGAS INVISIBLES</b>",
        template="plotly_dark",
        paper_bgcolor="#0A0E17",
        plot_bgcolor="#0A0E17",
        font=dict(family="JetBrains Mono, monospace", size=10, color="#F8FAFC"),
        margin=dict(l=20, r=20, t=50, b=30),
        height=380
    )
    st.plotly_chart(fig_sankey, use_container_width=True)


with tab5:
    st.markdown("### 🚨 Saneamiento Temporal y Puntos de Agua en Emergencia")
    st.markdown("""
    **Mandato Pericial BOE-A-2026-21231 (BOE núm. 253 de 12/10/2026 · Orden DCA/1079/2026):**
    Parametrización determinista de requerimientos sanitarios para intervenciones de emergencia ambiental,
    habitacional y asentamientos temporales. Control estricto de cloro residual libre ($0.20 - 1.00$ mg/L)
    en depósitos móviles bajo el **RD 3/2023**, dimensionamiento de fosas sépticas estancas conforme a **UNE-EN 12566**
    y ratio de desinfección UV/cloración con coliformes fecales y *E. coli* $< 1\\ \\text{UFC}/100\\ \\text{mL}$
    para protección absoluta de acuíferos locales (**RD 1620/2007** y Ley de Aguas).
    """)

    sub_punto, sub_san = st.tabs([
        "🚛 Puntos de Agua Móviles y Depósitos de Emergencia (RD 3/2023)",
        "☣️ Saneamiento Autónomo, Fosas Estancas y Desinfección UV (Orden DCA/1079/2026)"
    ])

    with sub_punto:
        st.markdown("##### 📍 Control Técnico-Sanitario de Puntos de Suministro Móviles")
        col_pa1, col_pa2, col_pa3 = st.columns(3)
        with col_pa1:
            pa_id = st.text_input("ID Punto de Suministro", value="DEP-MOVIL-VALLECAS-01")
            pa_tipo = st.selectbox("Tipo de Depósito / Transporte", ["CISTERNA_MOVIL", "TANQUE_FLEXIBLE", "DEPOSITO_MODULAR_PEAD"], index=0)
            pa_vol = st.slider("Capacidad Útil Depósito (m³)", min_value=2.0, max_value=60.0, value=25.0, step=1.0)
            render_slider_scale("2.0 m³", "60.0 m³", f"{pa_vol:.1f} m³", "Volumen Útil")
        with col_pa2:
            pa_pob = st.number_input("Población Atendida (Habitantes)", min_value=10, max_value=2500, value=250, step=10)
            pa_dot = st.slider("Dotación Emergencia (L/hab·día)", min_value=15.0, max_value=120.0, value=50.0, step=5.0,
                              help="Mínimo SPHERE: 15 L/d; Recomendado OMS/Protección Civil: 50 L/d")
            render_slider_scale("15.0 L/hab·d", "120.0 L/hab·d", f"{pa_dot:.1f} L/hab·d", "Estándar OMS/SPHERE")
            pa_tiempo = st.slider("Tiempo Almacenamiento (horas)", min_value=1.0, max_value=120.0, value=24.0, step=2.0,
                                  help="Alerta sanitaria automática si supera 72 horas sin renovación")
            render_slider_scale("1.0 h", "120.0 h", f"{pa_tiempo:.0f} h", "Límite Estanqueidad: 72h")
        with col_pa3:
            pa_cloro = st.slider("Cloro Libre Residual Actual (mg/L)", min_value=0.00, max_value=2.00, value=0.55, step=0.05)
            render_slider_scale("0.00 mg/L", "2.00 mg/L", f"{pa_cloro:.2f} mg/L", "Rango legal: 0.20 - 1.00 mg/L")
            pa_turb = st.slider("Turbidez Muestra (UNF)", min_value=0.1, max_value=6.0, value=1.1, step=0.1)
            render_slider_scale("0.10 UNF", "6.00 UNF", f"{pa_turb:.2f} UNF", "Límite: ≤ 4.0 UNF")
            pa_ph = st.slider("pH Muestra", min_value=5.5, max_value=9.5, value=7.35, step=0.05)
            render_slider_scale("5.50 pH", "9.50 pH", f"{pa_ph:.2f} pH", "Rango legal: 6.50 - 9.50")

        punto_obj = ParametrosPuntoAguaTemporal(
            id_punto=pa_id,
            tipo_deposito=pa_tipo,
            volumen_deposito_m3=pa_vol,
            poblacion_atendida_hab=int(pa_pob),
            dotacion_l_hab_dia=pa_dot,
            cloro_libre_actual_mg_l=pa_cloro,
            turbidez_unf=pa_turb,
            ph=pa_ph,
            tiempo_estanqueidad_horas=pa_tiempo
        )

        res_punto = DimensionadorSaneamientoEmergencia.auditar_punto_agua_temporal(punto_obj)

        st.markdown("---")
        c_p1, c_p2, c_p3, c_p4 = st.columns(4)
        c_p1.metric("Autonomía Hídrica", f"{res_punto['autonomia_dias']:.1f} días", delta=f"{res_punto['consumo_diario_l_dia']:,.0f} L/día consumo")
        c_p2.metric("Cloro Libre Residual", f"{res_punto['cloro_actual_mg_l']:.2f} mg/L",
                    delta="Conforme (0.2-1.0)" if 0.20 <= res_punto['cloro_actual_mg_l'] <= 1.00 else "NO CONFORME",
                    delta_color="normal" if 0.20 <= res_punto['cloro_actual_mg_l'] <= 1.00 else "inverse")
        c_p3.metric("Dosis Correctora Cloro", f"{res_punto['dosis_correctora_g_cloro']:.1f} g Cl₂",
                    delta=f"{res_punto['ml_hipoclorito_15pct']:.0f} mL Hipoclorito 15%" if res_punto['dosis_correctora_g_cloro'] > 0 else "No requerida")
        c_p4.metric("Estado Estanqueidad", f"{pa_tiempo:.0f} h",
                    delta="Alerta >72h" if res_punto['alerta_estanqueidad_72h'] else "Fresco (<=72h)",
                    delta_color="inverse" if res_punto['alerta_estanqueidad_72h'] else "normal")

        if res_punto["conforme_rd3_dca1079"]:
            st.markdown(f'<div class="status-badge-ok">✅ {res_punto["dictamen_potabilidad"]} · SHA-256: <code>{res_punto["hash_trazabilidad"]}</code></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-badge-crit">🚨 {res_punto["dictamen_potabilidad"]} · SHA-256: <code>{res_punto["hash_trazabilidad"]}</code></div>', unsafe_allow_html=True)
            for nc in res_punto["no_conformidades"]:
                st.markdown(f"- 🔴 **[{nc['norma']}] {nc['parametro']}:** {nc['valor']} (Límite: {nc['limite']}) ➔ _Acción:_ `{nc['accion']}`")

    with sub_san:
        st.markdown("##### ☣️ Dimensionamiento de Fosas Sépticas Estancas y Depuración Biológica / UV")
        col_sa1, col_sa2, col_sa3 = st.columns(3)
        with col_sa1:
            sa_id = st.text_input("ID Sistema Saneamiento", value="SAN-EMERG-ASENTAMIENTO-01")
            sa_tec = st.selectbox("Tecnología de Tratamiento", [
                "MODULO_COMPACTO_BIOLOGICO_UV",
                "FOSA_SEPTICA_ESTANCA",
                "OXIDACION_TOTAL"
            ], index=0)
            sa_he = st.slider("Habitantes Equivalentes (HE)", min_value=10, max_value=600, value=150, step=10)
            render_slider_scale("10 HE", "600 HE", f"{sa_he} HE", "Carga Contaminante")
        with col_sa2:
            sa_dot_v = st.slider("Dotación Vertido (L/HE·día)", min_value=60.0, max_value=200.0, value=120.0, step=10.0)
            render_slider_scale("60.0 L/HE·d", "200.0 L/HE·d", f"{sa_dot_v:.0f} L/HE·d", "Aporte Hidráulico")
            sa_uv = st.slider("Fluencia / Dosis UV Aplicada (mJ/cm²)", min_value=10.0, max_value=90.0, value=48.0, step=2.0,
                             help="Dosis estándar biofísica: >= 40 mJ/cm² para inactivación de patógenos")
            render_slider_scale("10.0 mJ/cm²", "90.0 mJ/cm²", f"{sa_uv:.1f} mJ/cm²", "Norma: ≥ 40.0 mJ/cm²")
        with col_sa3:
            sa_dist = st.slider("Distancia a Acuífero / Sondeo (m)", min_value=10.0, max_value=150.0, value=65.0, step=5.0)
            render_slider_scale("10.0 m", "150.0 m", f"{sa_dist:.0f} m", "Distancia Mínima: ≥ 35-50 m")
            sa_terr = st.selectbox("Litología del Terreno", ["LIMOSO_ARCILLOSO", "ARENOSO_PERMEABLE", "ROCOSO_FRACTURADO"], index=0)
            sa_meses = st.selectbox("Frecuencia Vaciado Fangos (meses)", [6, 12, 24], index=1)

        san_obj = ParametrosSaneamientoAutonomo(
            id_sistema=sa_id,
            tipo_tecnologia=sa_tec,
            habitantes_equivalentes_he=sa_he,
            dotacion_vertido_l_he_dia=sa_dot_v,
            dosis_uv_mj_cm2=sa_uv,
            distancia_acuifero_o_sondeo_m=sa_dist,
            tipo_terreno=sa_terr,
            frecuencia_vaciado_fangos_meses=sa_meses
        )

        res_san = DimensionadorSaneamientoEmergencia.dimensionar_saneamiento_autonomo(san_obj)

        st.markdown("---")
        c_s1, c_s2, c_s3, c_s4 = st.columns(4)
        c_s1.metric("Volumen Útil Fosa (UNE-EN 12566)", f"{res_san['volumen_util_fosa_m3']:.1f} m³",
                    delta=f"{res_san['caudal_diario_m3_dia']:.1f} m³/día caudal")
        c_s2.metric("Coliformes Efluente (<1 UFC)", f"{res_san['coliformes_fecales_efluente_ufc_100ml']:.2f} UFC/100mL",
                    delta="Bioseguro (< 1 UFC)" if res_san['cumple_ratio_coliformes_menor_1'] else "SUPERADO (>= 1 UFC)",
                    delta_color="normal" if res_san['cumple_ratio_coliformes_menor_1'] else "inverse")
        c_s3.metric("Rendimiento Depuración", f"DBO₅ -{res_san['reduccion_dbo5_pct']}%",
                    delta=f"MES -{res_san['reduccion_mes_pct']}%")
        c_s4.metric("Protección Acuífero", f"{sa_dist:.0f} m",
                    delta="Distancia Insegura" if res_san['riesgo_acuifero_local'] else f"Seguro (>= {res_san['distancia_seguridad_minima_m']:.0f} m)",
                    delta_color="inverse" if res_san['riesgo_acuifero_local'] else "normal")

        if res_san["conforme_orden_dca1079_rd1620"]:
            st.markdown(f'<div class="status-badge-ok">✅ {res_san["dictamen_pericial_saneamiento"]} · SHA-256: <code>{res_san["hash_trazabilidad"]}</code></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-badge-crit">🚨 {res_san["dictamen_pericial_saneamiento"]} · SHA-256: <code>{res_san["hash_trazabilidad"]}</code></div>', unsafe_allow_html=True)
            for nc in res_san["no_conformidades"]:
                st.markdown(f"- 🔴 **[{nc['norma']}] {nc['parametro']}:** {nc['valor']} (Exigencia: {nc['limite']}) ➔ _Acción pericial:_ `{nc['accion']}`")

        # ==============================================================================
        # GRÁFICA INTERACTIVA 5: CINÉTICA DE INACTIVACIÓN UV (CHICK-WATSON)
        # ==============================================================================
        st.markdown("##### 🔬 Curva Cinética de Inactivación UV de Coliformes Fecales vs. Fluencia Aplicada (RD 1620/2007)")
        
        curva_data = res_san.get('curva_inactivacion', res_san.get('curva_inactivacion_uv', []))
        df_uv = pd.DataFrame(curva_data)
        fig_uv = go.Figure()

        # Curva de Coliformes Fecales
        fig_uv.add_trace(go.Scatter(
            x=df_uv['dosis_uv_mj_cm2'],
            y=df_uv['coliformes_ufc_100ml'],
            name="Recuento Coliformes Fecales (UFC/100 mL)",
            line=dict(color="#00D2FF", width=3),
            mode="lines+markers"
        ))

        # Punto operativo real
        fig_uv.add_trace(go.Scatter(
            x=[sa_uv],
            y=[res_san['coliformes_fecales_efluente_ufc_100ml']],
            name=f"Operación Actual ({sa_uv} mJ/cm²)",
            mode="markers+text",
            marker=dict(size=14, color="#00F5A0" if res_san['cumple_ratio_coliformes_menor_1'] else "#EF4444", symbol="star", line=dict(color="#FFFFFF", width=2)),
            text=[f"<b>{res_san['coliformes_fecales_efluente_ufc_100ml']:.2f} UFC</b>"],
            textposition="top right"
        ))

        # Línea de umbral legal (< 1 UFC / 100 mL)
        fig_uv.add_hline(
            y=1.0,
            line_dash="dash",
            line_color="#EF4444",
            annotation_text="Límite Máximo Orden DCA/1079/2026 (< 1.0 UFC/100 mL)",
            annotation_position="bottom right",
            annotation_font_color="#EF4444"
        )

        fig_uv.update_layout(
            title="<b>DECAIMIENTO CINÉTICO FRENTE A COLIFORMES FECALES Y E. COLI POR RADIACIÓN ULTRAVIOLETA</b>",
            template="plotly_dark",
            paper_bgcolor="#0A0E17",
            plot_bgcolor="#0A0E17",
            xaxis=dict(title="Dosis / Fluencia UV (mJ/cm²)", gridcolor="#1E293B", tickfont=dict(family="JetBrains Mono", size=10, color="#CBD5E1")),
            yaxis=dict(title="Concentración Coliformes (UFC/100 mL - Escala Log)", type="log", gridcolor="#1E293B", tickfont=dict(family="JetBrains Mono", size=10, color="#CBD5E1")),
            margin=dict(l=40, r=40, t=50, b=50),
            height=420,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_uv, use_container_width=True)

# ==============================================================================
# TAB 6: MOTORES NEURONALES (PINN OPEN-CORE & PI-GNN ENTERPRISE)
# ==============================================================================

# ==============================================================================
# TAB 6: MOTOR NEURONAL PINN OPEN-CORE & BÓVEDA EPISTÉMICA
# ==============================================================================
with tab6:
    st.markdown("### 🧠 Motor Neuronal Físico (PINN Open-Core) & Bóveda Epistémica")
    st.markdown("""
    **Inteligencia Artificial de Grado Industrial Informada por la Física (Zero-Toy / Zero-BlackBox):**
    El operador neuronal **HygieiaPINNSurrogate** resuelve la cinética acoplada de decaimiento bulk/wall de Arrhenius,
    la formación de trihalometanos (TTHM) y la supervivencia de *Legionella pneumophila* con latencias inferiores a **15 ms**,
    gobernado bajo **ISO/IEC 42001**, **Reglamento (UE) 2024/1689 Art. 14 (HITL)** y contrastado con **RD 3/2023** y **RD 487/2022**.
    """)

    st.markdown("#### ⚡ HygieiaPINNSurrogate · Inferencia Dinámica Sub-milisegundo")
    st.markdown("""
    Resuelve la cinética acoplada de decaimiento bulk/wall de Arrhenius, síntesis no-lineal de trihalometanos (THMs)
    y muerte térmica de *Legionella pneumophila* mediante embeddings de Fourier y bloques densos residuales.
    """)
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        c0_pinn = st.slider("Dosis Inicial $C_0$ (mg/L)", 0.30, 2.50, 1.20, 0.05, key="pinn_c0")
        render_slider_scale("0.30 mg/L", "2.50 mg/L", f"{c0_pinn:.2f} mg/L", "Dosis C0")
        toc_pinn = st.slider("TOC Precursor Orgánico (mg/L)", 0.20, 5.00, 2.00, 0.10, key="pinn_toc")
        render_slider_scale("0.20 mg/L", "5.00 mg/L", f"{toc_pinn:.2f} mg/L", "Precursor THMs")
    with col_p2:
        ph_pinn = st.slider("pH en Red", 6.5, 9.0, 7.5, 0.1, key="pinn_ph")
        render_slider_scale("6.50 pH", "9.00 pH", f"{ph_pinn:.2f} pH", "pH en Red")
        temp_pinn = st.slider("Temperatura del Agua (°C)", 10.0, 70.0, 48.0, 1.0, key="pinn_temp")
        render_slider_scale("10.0 °C", "70.0 °C", f"{temp_pinn:.1f} °C", "Cinética Arrhenius")
    with col_p3:
        diam_pinn = st.selectbox("Diámetro Tubería (mm)", [15.0, 20.0, 28.0, 35.0, 50.0, 80.0, 100.0], index=4, key="pinn_diam")
        tiempo_pinn = st.slider("Tiempo de Residencia / Tránsito (h)", 0.5, 72.0, 16.0, 0.5, key="pinn_t")
        render_slider_scale("0.5 h", "72.0 h", f"{tiempo_pinn:.1f} h", "Tránsito Hidráulico")

    pinn_model = HygieiaPINNSurrogateModel()
    res_pinn = pinn_model.predict(c0_pinn, toc_pinn, ph_pinn, temp_pinn, diam_pinn, tiempo_pinn)

    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    c_val = res_pinn["cloro_residual_mg_l"]
    thm_val = res_pinn["tthm_ug_l"]
    leg_val = res_pinn["legionella_log_surv"]
    lat_ms = res_pinn["latencia_inferencia_ms"]

    m1.metric("Cloro Libre $C(t)$", f"{c_val:.3f} mg/L",
              delta="Conforme RD 3/2023" if (0.20 <= c_val <= 1.00) else "NO CONFORME",
              delta_color="normal" if (0.20 <= c_val <= 1.00) else "inverse")
    m2.metric("Trihalometanos TTHM", f"{thm_val:.1f} µg/L",
              delta="Conforme (<=100)" if thm_val <= 100.0 else "TÓXICO (>100)",
              delta_color="normal" if thm_val <= 100.0 else "inverse")
    m3.metric("Supervivencia Legionella", f"{leg_val:.2f} log10",
              delta="Abatida (<= -4.0)" if leg_val <= -4.0 else "Riesgo Proliferación",
              delta_color="normal" if leg_val <= -4.0 else "inverse")
    m4.metric("Latencia de Inferencia", f"{lat_ms:.2f} ms",
              delta="Ultra-rápido (<15 ms)" if lat_ms < 15.0 else "Inferencia CPU",
              delta_color="normal")

    # Curva Dinámica 48h
    curve_data = pinn_model.generate_decay_curve(c0_pinn, toc_pinn, ph_pinn, temp_pinn, diam_pinn, max_hours=48.0, n_points=50)
    fig_pinn = go.Figure()
    fig_pinn.add_trace(go.Scatter(
        x=curve_data["tiempo_h"], y=curve_data["cloro_residual_mg_l"],
        name="Cloro Residual C(t) [mg/L]",
        line=dict(color="#00D2FF", width=3),
        yaxis="y1"
    ))
    fig_pinn.add_trace(go.Scatter(
        x=curve_data["tiempo_h"], y=curve_data["tthm_ug_l"],
        name="TTHMs Sintetizados [µg/L]",
        line=dict(color="#EF4444", width=3, dash="dot"),
        yaxis="y2"
    ))
    fig_pinn.add_hline(y=0.20, line_dash="dash", line_color="#F59E0B", annotation_text="Límite Mínimo RD 3/2023 (0.20 mg/L)")
    fig_pinn.update_layout(
        title="Dinámica Temporal PINN: Advección, Decaimiento de Arrhenius y Síntesis de THMs (48h)",
        xaxis_title="Tiempo de Tránsito / Residencia (horas)",
        yaxis=dict(title=dict(text="Cloro Residual (mg/L)", font=dict(color="#00D2FF")), tickfont=dict(color="#00D2FF")),
        yaxis2=dict(title=dict(text="TTHM (µg/L)", font=dict(color="#EF4444")), tickfont=dict(color="#EF4444"), overlaying="y", side="right"),
        plot_bgcolor="rgba(15, 23, 42, 0.6)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F8FAFC"),
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_pinn, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🏛️ Matriz de Arquitectura Bimodal: Open-Core vs. Enterprise Suite")
    st.markdown("""
    | Dimensión / Módulo | 🔓 Open-Core (Esta Edición Pública) | 💼 Enterprise Suite (Despliegue Hospitalario / Operadoras) |
    | :--- | :--- | :--- |
    | **Licencia & Distribución** | MIT / CC-BY 4.0 · Acceso Abierto Comunitario | Licencia Corporativa Institucional / On-Premise Air-Gap |
    | **Motor de Auditoría PSA** | Estático determinista bajo RD 3/2023 | Continuo en tiempo real acoplado a SCADA / Telemetría |
    | **Cinética Bioquímica** | Arrhenius Bulk/Wall & Chick-Watson UV | Acoplada a modelos hidrodinámicos 2D/3D |
    | **Control de Legionella** | Inactivación decimal $D$ y $z$ en grifo/acumulador | Auditoría continua multi-nodo y zonificación hospitalaria |
    | **Balance Hídrico & Fugas** | Balance IWA & Diagrama de Sankey estándar | Detección acústica predictiva & Gemelo EPANET/WNTR |
    | **Acelerador Neuronal** | HygieiaPINNSurrogate (< 15 ms en CPU) | HygieiaPIGNNTwin (Graph Neural Network sobre DMA completa) |
    | **Actuación Hidráulica** | Cálculo teórico de volúmenes y tiempos | Actuación autónoma Smart-Flushing IoT (PPO RL / BACnet / LoRaWAN) |
    | **Exportación Oficial SINAC** | Restringido (Exclusivo operadores acreditados) | Generación oficial automatizada con hash criptográfico SHA-256 |
    | **Ingesta de Datos de Campo** | No disponible en entorno público web | Ingesta anonimizada forense bajo ISO/IEC 27037 & RGPD Art. 25 |
    | **Acreditación & Peritaje** | Fines docentes, científicos y consultoría | Dictámenes periciales vinculantes bajo Art. 335 LEC |
    """)

    st.markdown("---")
    col_bv1, col_bv2 = st.columns(2)
    with col_bv1:
        st.markdown("#### 📜 Bóveda Normativa Oficial (España & UE)")
        st.markdown("""
        • **Real Decreto 3/2023, de 10 de enero:** Criterios técnico-sanitarios del agua de consumo humano, control en edificios prioritarios y planes sanitarios del agua.<br>
        • **Real Decreto 487/2022, de 21 de junio:** Requisitos sanitarios para la prevención y el control de la legionelosis.<br>
        • **Orden DCA/1079/2026 (BOE núm. 253 de 12/10/2026):** Saneamiento temporal y puntos de agua en situaciones de emergencia.<br>
        • **Orden TED/934/2022:** Bases reguladoras del PERTE de digitalización del ciclo del agua.<br>
        • **Directiva (UE) 2020/2184:** Calidad de las aguas destinadas al consumo humano.<br>
        • **Reglamento (UE) 2024/1689 (AI Act):** Requisitos de IA de alto riesgo y supervisión humana efectiva (Art. 14 HITL).
        """, unsafe_allow_html=True)
    with col_bv2:
        st.markdown("#### 📚 Base Epistémica Seminal & Cita Científica")
        st.markdown("""
        • **WHO (OMS) 2023:** *Water Safety Plan Manual (2nd Edition) - Step-by-step risk management for drinking-water suppliers*.<br>
        • **Paranjape et al. (2020):** *Chlorine Disinfection & Legionella Thermal Inactivation Kinetics in Premise Plumbing*.<br>
        • **Falkinham et al. (2015):** *Ecology and Biofilm Interactions of Premise Plumbing Pathogens*.<br>
        • **IWA Specialist Group (2019):** *Standard International Water Loss Balance & Performance Indicators (ILI)*.
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style="background: rgba(15,23,42,0.8); border: 1px solid rgba(0,210,255,0.25); border-radius: 6px; padding: 10px 14px; margin-top: 10px;">
            <div style="font-size: 0.72rem; color: #38BDF8; font-weight: 700; font-family: 'JetBrains Mono', monospace;">CITA CIENTÍFICA OFICIAL (ZENODO / CERN):</div>
            <div style="font-size: 0.70rem; color: #94A3B8; font-family: 'JetBrains Mono', monospace; margin-top: 4px;">
                Flores Yarihuaman, K. J. (2026). <em>AQUA-CORE: HYGIEIA - Grey-Box Cyberphysical Digital Twin & Physics-Informed Neural Network (PINN)</em>. CERN Zenodo. DOI: <a href="https://doi.org/10.5281/zenodo.23321969" target="_blank" style="color: #00D2FF;">10.5281/zenodo.23321969</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🛡️ Centinela de Invariantes Físicas en Runtime (Physics Sentinel)")
    sentinel_inst = PhysicsSentinelSidecar(core_id="HYGIEIA")
    dna_ok, dna_hash = sentinel_inst.verify_dna_integrity()
    st.markdown(f"**Integridad DNA Científico:** {'✅ VÁLIDO' if dna_ok else '⚠️ ADULTERADO'} (`{dna_hash[:16]}...`) | **Invariantes Físicas Activas:** `{len(sentinel_inst.invariants)} leyes biofísicas`")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("##### 🔬 Verificación en Tiempo Real de Clamping:")
        val_test = st.number_input("Test Valor Cloro Libre (mg/L)", value=1.5, step=0.1, key="test_cl_in")
        clamped_v, was_mod, reason = sentinel_inst.clamp_value("cloro_libre_residual_mgl", val_test)
        if was_mod:
            st.warning(f"⚠️ Clamping Activado: {reason} ➔ {clamped_v:.2f} mg/L")
        else:
            st.success(f"✅ Valor admisible en Lex Artis: {clamped_v:.2f} mg/L")
    with col_t2:
        st.markdown("##### 📐 Leyes Físicas y Ecuaciones Gobernantes Embebidas:")
        for inv in sentinel_inst.invariants[:4]:
            st.markdown(f"• **{inv.get('nombre', 'Invariante')}:** `{inv.get('ecuacion_latex', '')}`", unsafe_allow_html=True)

st.markdown("---")

# ==============================================================================
# ESCUDO PERICIAL Y GOBERNANZA LEGAL OFICIAL (DOC-YES-LEGAL-2026-v2)
# ==============================================================================
if freyja_ui and hasattr(freyja_ui, "render_legal_shield"):
    freyja_ui.render_legal_shield(
        core_id="hygieia",
        doc_ref="HYGIEIA-C2-MECES3-2026-v1",
        cert_hash="SHA256:ISO27037-MECES3-AUTH"
    )
else:
    st.markdown("""
    <div style="font-size: 0.78rem; color: #64748B; border-top: 1px solid #1E293B; padding-top: 12px; margin-top: 20px;">
        AQUA-CORE_HYGIEIA · Sistema de Soporte a la Decisión (DSS) bajo Art. 14 Reglamento (UE) 2024/1689 (AI Act) y Art. 402 CP.<br>
        Supervisión pericial obligatoria: Kelvin Jesús Flores Yarihuaman (MECES Nivel 3 · EQF Level 7) · Art. 335 LEC.
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 12px 16px; margin-top: 16px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
    <div style="display: flex; align-items: center; gap: 8px; font-size: 0.82rem; color: #CBD5E1;">
        <span style="font-size: 1.1rem;">🏛️</span>
        <span><strong>Acreditación & Identidad Pericial:</strong> Kelvin Jesús Flores Yarihuaman (MECES 3 / EQF 7) · Yggdrasil Environmental Systems</span>
    </div>
    <div style="display: flex; gap: 10px;">
        <a href="https://www.linkedin.com/in/kelvinflores-ingenieria" target="_blank" style="display: inline-flex; align-items: center; gap: 6px; text-decoration: none; color: #00D2FF; font-size: 0.78rem; font-family: 'JetBrains Mono', monospace; background: rgba(0, 210, 255, 0.1); border: 1px solid rgba(0, 210, 255, 0.35); padding: 5px 10px; border-radius: 6px;">
            <span>💼</span> <span>LinkedIn Personal</span>
        </a>
        <a href="https://www.linkedin.com/company/yggdrasil-environmental-systems" target="_blank" style="display: inline-flex; align-items: center; gap: 6px; text-decoration: none; color: #00F5A0; font-size: 0.78rem; font-family: 'JetBrains Mono', monospace; background: rgba(0, 245, 160, 0.1); border: 1px solid rgba(0, 245, 160, 0.35); padding: 5px 10px; border-radius: 6px;">
            <span>🏢</span> <span>LinkedIn Corporativo</span>
        </a>
    </div>
</div>
""", unsafe_allow_html=True)
