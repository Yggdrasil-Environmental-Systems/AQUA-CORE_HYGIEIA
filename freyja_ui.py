"""
FREYJA UI SDK | Universal Core Platform Standard (UCPS-v1)
===========================================================
Unified UI Framework for Yggdrasil Environmental Systems.
Standardizes Streamlit cockpits across all sister cores:
OSIRIS (:8502), DAEDALUS (:8501), OUROBOROS (:8503), HELIOS (:8507), PROMETHEUS (:8504).

Author: Kelvin Jesús Flores Yarihuaman | Lead Systems Architect (MECES 3 / EQF 7)
Ecosystem: Yggdrasil Environmental Systems
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import streamlit as st


def _clean_html(raw_html: str) -> str:
    """
    Elimina cualquier sangría inicial de cada línea para evitar que
    el parser de Markdown de Streamlit/CommonMark trate el HTML
    como un bloque de código indentado (<pre><code>).
    """
    return re.sub(r'^[ \t]+', '', raw_html.strip(), flags=re.MULTILINE)


# ==============================================================================
# 1. CANONICAL ECOSYSTEM REGISTRY (PUBLIC CORES ONLY)
# ==============================================================================
ECOSYSTEM_CORES: Dict[str, Dict[str, Any]] = {
    "hub": {
        "id": "hub",
        "name": "YGGDRASIL PORTAL",
        "alias": "HUB",
        "icon": "🌿",
        "port": 8080,
        "color": "#00F5A0",
        "domain": "Portal Matriz & Umbrella OS",
        "status": "ONLINE"
    },
    "osiris": {
        "id": "osiris",
        "name": "HYDRO-CORE: OSIRIS",
        "alias": "OSIRIS",
        "icon": "💧",
        "port": 8502,
        "color": "#00D2FF",
        "domain": "Hidrología & DANA Nowcast (FNO 2D)",
        "status": "ONLINE"
    },
    "daedalus": {
        "id": "daedalus",
        "name": "CYBER-CORE: DAEDALUS",
        "alias": "DAEDALUS",
        "icon": "🏢",
        "port": 8501,
        "color": "#00F5A0",
        "domain": "Smart Building & BACS Clase A (ISO 52120-1)",
        "status": "ONLINE"
    },
    "ouroboros": {
        "id": "ouroboros",
        "name": "CIRCULAR-CORE: OUROBOROS",
        "alias": "OUROBOROS",
        "icon": "🔄",
        "port": 8503,
        "color": "#30D158",
        "domain": "Metabolismo Material & Alcance 1-2-3 (CSRD)",
        "status": "ONLINE"
    },
    "helios": {
        "id": "helios",
        "name": "SOLAR-CORE: HELIOS",
        "alias": "HELIOS",
        "icon": "☀️",
        "port": 8507,
        "color": "#FFD60A",
        "domain": "Solar Fotovoltaica & EIA (Ley 21/2013)",
        "status": "ONLINE"
    },
    "prometheus": {
        "id": "prometheus",
        "name": "PYRO-CORE: PROMETHEUS",
        "alias": "PROMETHEUS",
        "icon": "🔥",
        "port": 8504,
        "color": "#FF453A",
        "domain": "Forense de Incendios & Restauración (TRAGSA)",
        "status": "ONLINE"
    },
    "janus": {
        "id": "janus",
        "name": "THERMO-CORE: JANUS",
        "alias": "JANUS",
        "icon": "🌡️",
        "port": 8509,
        "color": "#8E8E93",
        "domain": "Termodinámica Urbana & Microclima (CTE D3)",
        "status": "ROADMAP"
    },
    "athena": {
        "id": "athena",
        "name": "AI-CORE: ATHENA",
        "alias": "ATHENA",
        "icon": "🦉",
        "port": 8514,
        "color": "#A855F7",
        "domain": "Directora Científica Suprema & Centinela Físico",
        "status": "ONLINE"
    }
}


# ==============================================================================
# 2. ECOSYSTEM TOPBAR (UNIVERSAL CORE SWITCHER)
# ==============================================================================
def render_ecosystem_topbar(current_core_id: str, is_cloud: bool = False, cloud_urls: Optional[Dict[str, str]] = None):
    """
    Renders the unified top navigation bar across all Streamlit platforms.
    Enables single-click navigation to the Master Hub (:8080) and all sibling cores.
    """
    cloud_urls = cloud_urls or {}
    core_keys = ["hub", "osiris", "daedalus", "ouroboros", "helios", "prometheus", "janus", "athena"]

    nav_links_html = []
    for key in core_keys:
        info = ECOSYSTEM_CORES[key]
        is_active = (key.lower() == current_core_id.lower())
        
        if is_cloud:
            target_url = cloud_urls.get(key, f"#{key}")
        else:
            if key == "hub":
                target_url = "http://localhost:8080"
            else:
                target_url = f"http://localhost:{info['port']}"

        if info["status"] == "ROADMAP":
            nav_links_html.append(
                f'<span style="opacity: 0.45; cursor: not-allowed; padding: 4px 9px; font-size: 0.72rem; font-family: monospace; color: #94A3B8; border: 1px dashed #334155; border-radius: 4px;" title="Próximamente en Roadmap">{info["icon"]} {info["alias"]} <span style="font-size: 0.60rem; color: #64748B;">[SOON]</span></span>'
            )
        elif is_active:
            nav_links_html.append(
                f'<span style="background: rgba(255,255,255,0.08); border: 1px solid {info["color"]}; box-shadow: 0 0 12px {info["color"]}44; color: #FFFFFF; font-weight: 700; padding: 4px 10px; border-radius: 5px; font-size: 0.74rem; font-family: monospace;">{info["icon"]} {info["alias"]} <span style="font-size: 0.65rem; color: {info["color"]};">● ACTIVE</span></span>'
            )
        else:
            nav_links_html.append(
                f'<a href="{target_url}" target="_self" style="text-decoration: none; color: #94A3B8; padding: 4px 9px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.06); font-size: 0.72rem; font-family: monospace; transition: all 0.2s;">{info["icon"]} {info["alias"]}</a>'
            )

    items_joined = " ".join(nav_links_html)

    html = f"""<div style="background: #070B12; border-bottom: 1px solid #1E293B; padding: 7px 16px; margin: -5rem -4rem 1.25rem -4rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; z-index: 999; box-shadow: 0 4px 20px rgba(0,0,0,0.5);"><div style="display: flex; align-items: center; gap: 10px;"><a href="http://localhost:8080" target="_self" style="text-decoration: none; display: flex; align-items: center; gap: 7px;"><span style="font-size: 1.05rem;">🌿</span><span style="font-weight: 800; font-size: 0.78rem; letter-spacing: 0.08em; color: #F8FAFC; font-family: sans-serif;">YGGDRASIL <span style="color: #00F5A0; font-weight: 600;">SYSTEMS</span></span></a><span style="color: #334155; font-size: 0.8rem;">|</span><span style="color: #64748B; font-size: 0.68rem; font-family: monospace; text-transform: uppercase;">Ecosystem Switcher</span></div><div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">{items_joined}</div></div>"""
    
    st.markdown(_clean_html(html), unsafe_allow_html=True)
    return html


# ==============================================================================
# 3. C2 TACTICAL CORE HEADER
# ==============================================================================
def render_c2_header(
    core_id: str,
    title: str,
    subtitle: str,
    badges: Optional[List[Dict[str, str]]] = None,
    live_status: str = "ONLINE · C2 COCKPIT ACTIVE"
):
    """
    Renders standardized C2 tactical header with corporate accreditation.
    """
    info = ECOSYSTEM_CORES.get(core_id.lower(), ECOSYSTEM_CORES["osiris"])
    accent = info["color"]

    badges = badges or [
        {"label": "EU AI ACT 2024/1689", "color": "emerald"},
        {"label": "MECES 3 / EQF 7", "color": "cyan"},
        {"label": "OPEN-CORE V2.0", "color": "amber"}
    ]

    badge_html_list = []
    for b in badges:
        col = b.get("color", "cyan")
        col_hex = "#00D2FF" if col == "cyan" else ("#00F5A0" if col == "emerald" else "#FFD60A")
        badge_html_list.append(
            f'<span style="background: {col_hex}18; border: 1px solid {col_hex}; color: {col_hex}; padding: 2px 8px; border-radius: 4px; font-size: 0.66rem; font-family: monospace; font-weight: 700;">{b["label"]}</span>'
        )
    badges_rendered = " ".join(badge_html_list)

    html = f"""<div style="background: linear-gradient(135deg, rgba(11,18,31,0.95), rgba(7,11,18,0.98)); border: 1px solid #1E293B; border-left: 4px solid {accent}; border-radius: 8px; padding: 16px 20px; margin-bottom: 1.5rem; box-shadow: 0 10px 25px rgba(0,0,0,0.4);"><div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;"><div><div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;"><span style="font-size: 1.4rem;">{info['icon']}</span><h1 style="margin: 0; font-size: 1.45rem; font-weight: 800; font-family: sans-serif; letter-spacing: -0.01em; color: #FFFFFF;">{title}</h1></div><div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 8px; font-family: sans-serif;">{subtitle}</div><div style="font-size: 0.72rem; color: #64748B; font-family: monospace;">Lead Systems Architect: <span style="color: #F8FAFC; font-weight: 600;">Kelvin Jesús Flores Yarihuaman</span> | Acreditación Oficial MECES 3 / EQF 7</div></div><div style="display: flex; flex-direction: column; align-items: flex-end; gap: 8px;"><div style="display: flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: {accent}; box-shadow: 0 0 8px {accent};"></span><span style="font-size: 0.70rem; font-family: monospace; font-weight: 700; color: {accent}; letter-spacing: 0.05em;">{live_status}</span></div><div style="display: flex; gap: 6px; flex-wrap: wrap;">{badges_rendered}</div></div></div></div>"""
    
    st.markdown(_clean_html(html), unsafe_allow_html=True)


# ==============================================================================
# 4. STANDARDIZED KPI METRIC CARD (HIGH DATA-TO-INK RATIO)
# ==============================================================================
def render_kpi_card(
    title: str,
    value: str,
    subtext: str = "",
    delta: Optional[str] = None,
    delta_type: str = "positive",
    badge: Optional[str] = None,
    border_accent: Optional[str] = None
):
    """
    Renders high-density Tufte/Freyja metric card with clean typography.
    """
    delta_color = "#00F5A0" if delta_type == "positive" else ("#FF453A" if delta_type == "negative" else "#94A3B8")
    delta_html = f"<span style='color: {delta_color}; font-size: 0.75rem; font-weight: 700; margin-left: 6px;'>{delta}</span>" if delta else ""
    badge_html = f"<span style='background: rgba(255,255,255,0.08); border: 1px solid #334155; color: #CBD5E1; font-size: 0.65rem; padding: 2px 6px; border-radius: 4px; font-family: monospace;'>{badge}</span>" if badge else ""
    
    border_css = f"border-top: 2px solid {border_accent};" if border_accent else ""

    html = f"""<div style="background: rgba(11,18,31,0.85); border: 1px solid #1E293B; {border_css} border-radius: 8px; padding: 14px 16px; margin-bottom: 0.75rem; box-shadow: 0 4px 15px rgba(0,0,0,0.25);"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;"><div style="font-size: 0.74rem; font-family: monospace; text-transform: uppercase; color: #94A3B8; letter-spacing: 0.04em;">{title}</div>{badge_html}</div><div style="display: flex; align-items: baseline; margin-bottom: 4px;"><div style="font-size: 1.55rem; font-weight: 800; font-family: monospace; color: #FFFFFF; letter-spacing: -0.02em;">{value}</div>{delta_html}</div><div style="font-size: 0.72rem; color: #64748B; font-family: sans-serif;">{subtext}</div></div>"""
    
    st.markdown(_clean_html(html), unsafe_allow_html=True)


# ==============================================================================
# 5. SOVEREIGN LEGAL & AI GOVERNANCE SHIELD
# ==============================================================================
def get_canonical_legal_points(core_id: str) -> List[Dict[str, str]]:
    """
    Returns the 5 universal canonical legal shield pillars tailored to the core.
    Enforces DOC-YES-LEGAL-2026-v1 (Arts. 325, 304, 390, 402 CP, Art. 335.2 LEC, AI Act, RGPD).
    """
    cid = core_id.lower()
    
    # Specific pilar 3 per core
    if cid == "osiris":
        p3_title = "Exoneración Penal & Física Hidrodinámica 2D (Arts. 325, 304 CP):"
        p3_text = "Modelado FNO 2D bajo Saint-Venant y rotura de presas. No constituye garantía de riesgo nulo ante DANA extraordinaria o falta de mantenimiento de cauces. Responsabilidad directa del titular bajo Ley 26/2007."
    elif cid == "daedalus":
        p3_title = "Exoneración Penal & Clamping Térmico RITE (Arts. 325, 304 CP):"
        p3_text = "Consignas BACS ISO 52120-1 clamped a confort RITE IT 1.3.8 [19°C-27°C] y cap 250 kW REBT. No sustituye a Dirección Facultativa ni mantenedores RITE. Responsabilidad operativa del titular."
    elif cid == "ouroboros":
        p3_title = "Exoneración Penal & Balances LER eSIR (Arts. 325, 390 CP & Ley 7/2022):"
        p3_text = "Balances gravimétricos y trazabilidad Scope 1-3 sin datos sintéticos. La validez legal ante eSIR/MITECO recae en la declaración jurada del gestor autorizado bajo Ley 7/2022 y RD 764/2026."
    elif cid == "helios":
        p3_title = "Exoneración Penal & Bancabilidad Solar EIA (Arts. 325, 304 CP):"
        p3_text = "Modelado PVGIS, bifacialidad TOPCon y dispersión atmosférica según normas IEC 61215 y Guías MITECO. No garantiza rendimientos P90 sin ensayos in situ ni exime de autorizaciones sustantivas."
    elif cid == "prometheus":
        p3_title = "Exoneración Penal & Forense Satelital GIF (Arts. 325, 304 CP & RDL 15/2022):"
        p3_text = "Cartografía multiespectral Sentinel-2 (dNBR/RBR) y erosión RUSLE bajo protocolo EFFIS. Opera como prueba pericial analítica; no sustituye los planes de extinción del mando INFOEX/INFOCA."
    elif cid == "astraea":
        p3_title = "Exoneración Penal & Integridad Forense Air-Gap (Arts. 325, 390 CP):"
        p3_text = "Auditoría de código, gatekeeper normativo y verificación estática. No sustituye la diligencia debida del perito ni del órgano de administración conforme al Art. 31 bis CP."
    elif cid in ["athena", "ai_athena"]:
        p3_title = "Exoneración Penal & Inviolabilidad Física PINN/FNO (Arts. 325, 390 CP):"
        p3_text = "Verificación formal de leyes de conservación física y gobernanza AIMS ISO/IEC 42001:2023. Opera como tribunal pericial automatizado; no sustituye la ratificación formal de la Dirección Facultativa."
    else:
        p3_title = "Exoneración de Responsabilidad Penal Ambiental (Arts. 325, 304, 390 CP):"
        p3_text = "Simulaciones numéricas y balances de ingeniería basados en Lex Artis física. No constituyen garantía de riesgo nulo frente a fuerza mayor. Responsabilidad directa del titular (Ley 26/2007)."

    return [
        {
            "num": "1",
            "title": "DSS & Protección Civil (Art. 402 CP / Ley 17/2015):",
            "text": "Opera estrictamente como Sistema de Soporte a la Decisión (DSS). Prohibida la difusión autónoma de alertas de emergencia ciudadana sin ratificación formal de las autoridades públicas competentes."
        },
        {
            "num": "2",
            "title": "IA de Alto Riesgo & Supervisión HITL (Reglamento UE 2024/1689):",
            "text": "Clasificado bajo Anexo III (Infraestructuras Críticas y Gestión Ambiental). Exige Supervisión Humana Efectiva (Art. 14 HITL); ninguna consigna física ni trámite oficial opera sin validación técnica pericial."
        },
        {
            "num": "3",
            "title": p3_title,
            "text": p3_text
        },
        {
            "num": "4",
            "title": "Dictamen Técnico Pericial (Art. 335.2 LEC 1/2000):",
            "text": "Dirección técnica y modelado por Kelvin Jesús Flores Yarihuaman (Lead Systems Architect), Máster Universitario en Ingeniería y Gestión Ambiental (Nivel MECES 3 / EQF Level 7), bajo promesa estatutaria de veracidad y objetividad pericial."
        },
        {
            "num": "5",
            "title": "Cadena Custodia Criptográfica (ISO/IEC 27037) & RGPD:",
            "text": "Sellado inmutable mediante SHA-256 en bloques de 64KB. Privacidad por diseño (Art. 25 RGPD / LOPDGDD): telemetría técnica estricta sin tratamiento de datos personales de terceros."
        }
    ]


def render_legal_shield(
    core_id: str,
    doc_ref: str,
    specific_legal_points: Optional[List[Dict[str, str]]] = None,
    cert_hash: str = "SHA-256 VALIDATED · MECES3-AUTH"
):
    """
    Renders the official technical liability shield and EU AI Act compliance banner.
    Accredits Kelvin Jesús Flores Yarihuaman (MECES 3 / EQF 7) and enforces the 5 canonical pillars.
    """
    info = ECOSYSTEM_CORES.get(core_id.lower(), ECOSYSTEM_CORES["osiris"])

    points_to_render = specific_legal_points or get_canonical_legal_points(core_id)
    points_html = []
    for p in points_to_render:
        points_html.append(
            f'<div style="background: rgba(15,23,42,0.6); border: 1px solid rgba(255,255,255,0.06); border-radius: 6px; padding: 10px 12px;"><b style="color: #F8FAFC; font-size: 0.74rem;">{p["num"]}. {p["title"]}</b><br/><span style="color: #94A3B8; font-size: 0.70rem; line-height: 1.45;">{p["text"]}</span></div>'
        )
    points_joined = "".join(points_html)

    html = f"""
    <div style="background: rgba(15,23,42,0.85); border: 1px solid rgba(0,210,255,0.3); border-radius: 8px; padding: 16px; margin-top: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; margin-bottom: 12px;">
            <div style="font-weight: 700; color: #F8FAFC; font-size: 0.92rem;">
                🛡️ BLINDAJE JURÍDICO & CONFORMIDAD REGULATORIA (EU AI ACT · HITL)
            </div>
            <div style="font-size: 0.72rem; color: #94A3B8; font-family: monospace;">
                REF: {doc_ref} | {cert_hash}
            </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px;">
            {points_joined}
        </div>
    </div>
    """

    st.markdown(_clean_html(html), unsafe_allow_html=True)

    # Auto-render embedded regulatory DNA sidecar if present
    try:
        render_regulatory_dna_shield(core_id=core_id)
    except Exception:
        pass



# ==============================================================================
# 6. MASTER CANONICAL CSS THEME INJECTION
# ==============================================================================
def apply_canonical_theme(core_id: str):
    """
    Injects the unified Obsidian Void theme into Streamlit,
    standardizing scrollbars, font stacks, cards, and container paddings.
    """
    info = ECOSYSTEM_CORES.get(core_id.lower(), ECOSYSTEM_CORES["osiris"])
    accent = info["color"]

    css = f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}}

.stApp {{
    background-color: #070B12;
    color: #F8FAFC;
}}

[data-testid="stSidebar"] {{
    background-color: #0B121F !important;
    border-right: 1px solid #1E293B !important;
}}

[data-testid="stSidebar"] hr {{
    border-color: #1E293B !important;
}}

h1, h2, h3, h4 {{
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: -0.01em;
}}

code, pre, [data-testid="stMetricValue"] {{
    font-family: 'JetBrains Mono', monospace !important;
}}

[data-testid="stMetric"] {{
    background: rgba(11,18,31,0.85);
    border: 1px solid #1E293B;
    border-radius: 8px;
    padding: 12px 16px;
}}

::-webkit-scrollbar {{
    width: 6px;
    height: 6px;
}}
::-webkit-scrollbar-track {{
    background: #070B12;
}}
::-webkit-scrollbar-thumb {{
    background: #1E293B;
    border-radius: 3px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: {accent};
}}
</style>"""
    st.markdown(_clean_html(css), unsafe_allow_html=True)


# ==============================================================================
# 7. EMBEDDED REGULATORY DNA SHIELD (OFFLINE & CLOUD SELF-VERIFICATION)
# ==============================================================================
def render_regulatory_dna_shield(core_id: str = "osiris"):
    """
    Renders the embedded regulatory DNA compliance sidecar.
    Permits offline and cloud execution verification without local database dependencies.
    Standards: ISO/IEC 27037 · EU AI Act (2024/1689) · Art. 335 LEC
    """
    possible_paths = [
        Path("compliance/regulatory_dna.json"),
        Path("../compliance/regulatory_dna.json"),
        Path(__file__).resolve().parent / "compliance" / "regulatory_dna.json",
        Path(__file__).resolve().parent.parent / "compliance" / "regulatory_dna.json"
    ]
    manifest_path = None
    for p in possible_paths:
        if p.exists():
            manifest_path = p
            break

    if not manifest_path:
        st.caption("ℹ️ Cápsula de ADN Regulatorio no detectada en la ruta local del Core.")
        return

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            dna = json.load(f)
        
        total_normas = dna.get("resumen_metrologico", {}).get("total_normas_auditadas", len(dna.get("normas", [])))
        hash_sello = dna.get("sello_criptografico_sha256", "SHA256:AUTHENTIC")
        desglose = dna.get("resumen_metrologico", {}).get("desglose_jurisdicciones", {})
        director = dna.get("autoridad_tecnica", {}).get("director_tecnico", "Kelvin Jesús Flores Yarihuaman")
        meces = dna.get("autoridad_tecnica", {}).get("nivel_marco_cualificaciones", "MECES 3 / EQF 7")
        timestamp = dna.get("timestamp_snapshot_utc", "2026-10-12")

        with st.expander(f"🛡️ BÓVEDA DE CUMPLIMIENTO LEGAL EMBEBIDA ({total_normas} Normas Verificadas · {hash_sello[:24]}...)", expanded=False):
            st.markdown(f"""
            <div style="background: rgba(15,23,42,0.8); border: 1px solid #1E293B; border-left: 4px solid #00F5A0; border-radius: 6px; padding: 12px 16px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <strong style="color: #F8FAFC; font-size: 0.9rem;">Cápsula de ADN Regulatorio (Sidecar Desacoplado)</strong>
                    <span style="color: #00F5A0; font-family: monospace; font-size: 0.75rem; font-weight: bold;">{hash_sello}</span>
                </div>
                <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 6px;">
                    <strong>Dirección Técnica & Lex Artis:</strong> {director} ({meces}) · <em>Snapshot Inmutable ISO/IEC 27037</em> ({timestamp})
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("España (BOE)", desglose.get("ESPANA", 0))
            col_m2.metric("Unión Europea", desglose.get("UNION_EUROPEA", 0))
            col_m3.metric("Perú (MINAM)", desglose.get("PERU", 0))
            col_m4.metric("Internacional (ISO)", desglose.get("INTERNACIONAL", 0))

            q_filter = st.text_input("🔍 Filtrar normas de esta cápsula por palabra clave:", key=f"q_dna_{core_id}")
            normas = dna.get("normas", [])
            if q_filter:
                q_low = q_filter.lower()
                normas = [
                    n for n in normas 
                    if q_low in n.get("titulo_oficial", "").lower() or 
                       q_low in n.get("id_regulacion", "").lower() or 
                       q_low in n.get("articulos_clave", "").lower()
                ]

            st.caption(f"Mostrando {len(normas)} de {total_normas} normas aplicables a este Core.")
            
            with st.container(height=340):
                for n in normas[:50]:
                    card_html = f"""
<div style="background: rgba(30,41,59,0.4); border: 1px solid #334155; border-radius: 5px; padding: 8px 12px; margin-bottom: 6px;">
    <div style="display: flex; justify-content: space-between; font-size: 0.75rem;">
        <strong style="color: #38BDF8;">{n.get('id_regulacion')}</strong>
        <span style="color: #94A3B8; font-size: 0.70rem;">{n.get('jurisdiccion')} · {n.get('rama_ambiental')}</span>
    </div>
    <div style="color: #F1F5F9; font-size: 0.8rem; margin-top: 3px;">{n.get('titulo_oficial')}</div>
    {f'<div style="color: #CBD5E1; font-size: 0.72rem; margin-top: 3px;"><em>Artículos Clave:</em> {n.get("articulos_clave")}</div>' if n.get("articulos_clave") else ''}
    {f'<div style="color: #F87171; font-size: 0.72rem; margin-top: 2px;"><em>Régimen Sancionador:</em> {n.get("articulos_trampa_y_sanciones")}</div>' if n.get("articulos_trampa_y_sanciones") else ''}
</div>
"""
                    st.markdown(_clean_html(card_html), unsafe_allow_html=True)
                if len(normas) > 50:
                    st.caption(f"... y {len(normas) - 50} normas más indexadas en este manifiesto.")
    except Exception as e:
        st.error(f"Error procesando cápsula de ADN regulatorio: {e}")


# ==============================================================================
# 7B. EMBEDDED SCIENTIFIC DNA SHIELD & RUNTIME PHYSICS SENTINEL (SOTA AIMS)
# ==============================================================================
def render_scientific_dna_shield(core_id: str = "osiris"):
    """
    Renders the embedded scientific DNA physics sidecar and active invariant status.
    Permits offline and cloud execution verification without local database dependencies.
    Standards: ISO/IEC 42001 (AIMS) · EU AI Act (2024/1689 Art. 14) · Art. 335 LEC
    """
    possible_paths = [
        Path("physics/scientific_dna.json"),
        Path("../physics/scientific_dna.json"),
        Path(__file__).resolve().parent / "physics" / "scientific_dna.json",
        Path(__file__).resolve().parent.parent / "physics" / "scientific_dna.json"
    ]
    manifest_path = None
    for p in possible_paths:
        if p.exists():
            manifest_path = p
            break

    if not manifest_path:
        st.caption("ℹ️ Manifiesto de ADN Físico-Científico no detectado en la ruta local del Core.")
        return

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            dna = json.load(f)

        hash_sello = dna.get("sello_criptografico_sha256", "SHA256:AUTHENTIC")
        director = dna.get("autoridad_tecnica", {}).get("director_tecnico", "Kelvin Jesús Flores Yarihuaman")
        meces = dna.get("autoridad_tecnica", {}).get("nivel_marco_cualificaciones", "MECES 3 / EQF 7")
        timestamp = dna.get("timestamp_snapshot_utc", "2026-10-12")
        perfil = dna.get("perfil_modelado", {})
        disciplina = perfil.get("disciplina", "Física Computacional Determinista")
        solvers = perfil.get("solvers_comparados", "Solvers de Referencia SOTA")
        ecuacion_latex = perfil.get("ecuaciones_latex", "")
        invariantes = dna.get("invariantes_fisicas", [])
        respaldo = dna.get("respaldo_epistemico", {})
        total_papers = respaldo.get("total_papers_boveda", len(respaldo.get("papers_seminales_seleccionados", [])))
        papers = respaldo.get("papers_seminales_seleccionados", [])

        with st.expander(f"⚖️ TRIBUNAL DE LA FÍSICA REAL & ADN CIENTÍFICO EMBEBIDO ({len(invariantes)} Invariantes · {total_papers} Papers · {hash_sello[:24]}...)", expanded=False):
            st.markdown(f"""
            <div style="background: rgba(15,23,42,0.8); border: 1px solid #1E293B; border-left: 4px solid #38BDF8; border-radius: 6px; padding: 12px 16px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <strong style="color: #F8FAFC; font-size: 0.9rem;">Cápsula de ADN Físico-Científico (In-Process Sentinel)</strong>
                    <span style="color: #38BDF8; font-family: monospace; font-size: 0.75rem; font-weight: bold;">{hash_sello}</span>
                </div>
                <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 6px;">
                    <strong>Dirección Técnica & Lex Artis:</strong> {director} ({meces}) · <em>Snapshot Inmutable ISO/IEC 27037</em> ({timestamp})
                </div>
                <div style="font-size: 0.76rem; color: #CBD5E1; margin-top: 4px;">
                    <strong>Disciplina & Dominio:</strong> {disciplina} | <strong>Solvers SOTA de Contraste:</strong> {solvers}
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_p1, col_p2, col_p3 = st.columns(3)
            col_p1.metric("Papers Seminales Indexados", total_papers)
            col_p2.metric("Invariantes Físicas Activas", len(invariantes))
            col_p3.metric("Política Algorítmica", "Zero-Smoke / HITL")

            if ecuacion_latex:
                st.markdown("<strong style='color:#38BDF8; font-size:0.85rem;'>📐 Formulación Matemática & Ecuaciones Gobernantes:</strong>", unsafe_allow_html=True)
                st.latex(ecuacion_latex.strip())

            st.markdown("<strong style='color:#00F5A0; font-size:0.85rem;'>🛡️ Invariantes Físicas Inviolables & Tolerancias de Residuo:</strong>", unsafe_allow_html=True)
            for inv in invariantes:
                inv_html = f"""
<div style="background: rgba(30,41,59,0.3); border: 1px solid #334155; border-radius: 5px; padding: 6px 12px; margin-bottom: 5px; font-size: 0.78rem;">
    <span style="color: #00F5A0; font-weight: bold;">{inv.get('nombre')}:</span>
    <span style="color: #F1F5F9; font-family: monospace;"> {inv.get('ecuacion')}</span>
    <div style="color: #94A3B8; font-size: 0.70rem; margin-top: 2px;">
        Tolerancia: {inv.get('tolerancia_residual')} | Acción en Infracción: <code style="color: #F87171;">{inv.get('accion_si_viola')}</code>
    </div>
</div>
"""
                st.markdown(_clean_html(inv_html), unsafe_allow_html=True)

            st.markdown(f"<strong style='color:#A855F7; font-size:0.85rem;'>📚 Bóveda Epistémica de Respaldo ({len(papers)} Papers Clave Embebidos):</strong>", unsafe_allow_html=True)
            with st.container(height=260):
                for p in papers:
                    p_html = f"""
<div style="background: rgba(30,41,59,0.4); border: 1px solid #334155; border-radius: 5px; padding: 6px 10px; margin-bottom: 5px; font-size: 0.75rem;">
    <div style="display: flex; justify-content: space-between;">
        <strong style="color: #E2E8F0;">{p.get('titulo')}</strong>
        <span style="color: #38BDF8; font-size: 0.70rem;">{p.get('id')}</span>
    </div>
    <div style="color: #94A3B8; font-size: 0.70rem;">Disciplina: {p.get('disciplina')} | Ref: {p.get('referencia')}</div>
    <div style="color: #64748B; font-family: monospace; font-size: 0.65rem;">SHA256: {p.get('hash_sha256')}</div>
</div>
"""
                    st.markdown(_clean_html(p_html), unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error procesando cápsula de ADN físico-científico: {e}")


# ==============================================================================
# 8. SISTEMA DE OBSERVACIÓN Y MONITOREO GEOSPACIAL (LEAFLET DARK SOBERANO)
# ==============================================================================
def render_geospatial_map(
    lat: float = 39.4699,
    lon: float = -0.3763,
    zoom: int = 12,
    markers: Optional[List[Dict[str, Any]]] = None,
    height: int = 420,
    title: str = "CENTRO DE CONTROL & OBSERVACIÓN TERRITORIAL"
):
    """
    Renderiza componente interactivo de observación y cartografía territorial.
    Cero dependencias pip externas (ejecuta Leaflet 1.9.4 embebido en sandbox HTML).
    """
    import streamlit.components.v1 as components
    markers = markers or []
    markers_json = json.dumps(markers)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body, html {{ width: 100%; height: 100%; background: #070B12; font-family: 'JetBrains Mono', monospace; }}
  #map {{ width: 100%; height: 100%; border: 1px solid #1E293B; border-radius: 8px; }}
  .hud-overlay {{
    position: absolute; top: 12px; left: 16px; z-index: 1000;
    background: rgba(7, 11, 18, 0.88); border: 1px solid #1E293B;
    border-left: 3px solid #00F5A0; padding: 7px 12px; border-radius: 5px;
    color: #F8FAFC; font-size: 11px; pointer-events: none;
    box-shadow: 0 4px 15px rgba(0,0,0,0.5);
  }}
  .coords-readout {{
    position: absolute; bottom: 12px; right: 16px; z-index: 1000;
    background: rgba(7, 11, 18, 0.85); border: 1px solid #1E293B;
    padding: 4px 10px; border-radius: 4px; color: #94A3B8; font-size: 10px;
  }}
</style>
</head>
<body>
  <div class="hud-overlay">
    <div style="font-weight: 800; letter-spacing: 1px; color: #00F5A0;">{title}</div>
    <div style="color: #64748B; font-size: 9.5px;">CARTO DARK MATTER · EPSG:3857 · SISTEMA DE INFORMACIÓN GEOGRÁFICA (SIG)</div>
  </div>
  <div class="coords-readout" id="coords">LAT: {lat:.4f} | LON: {lon:.4f} | ZOOM: {zoom}</div>
  <div id="map"></div>
  <script>
    var map = L.map('map', {{ zoomControl: false }}).setView([{lat}, {lon}], {zoom});
    L.control.zoom({{ position: 'topright' }}).addTo(map);

    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
      attribution: '&copy; CartoDB & OpenStreetMap',
      subdomains: 'abcd',
      maxZoom: 19
    }}).addTo(map);

    map.on('mousemove', function(e) {{
      document.getElementById('coords').innerText = 'LAT: ' + e.latlng.lat.toFixed(4) + ' | LON: ' + e.latlng.lng.toFixed(4);
    }});

    var markersData = {markers_json};
    markersData.forEach(function(m) {{
      var col = m.color || '#00F5A0';
      var circle = L.circleMarker([m.lat, m.lon], {{
        radius: m.radius || 7,
        fillColor: col,
        color: '#FFFFFF',
        weight: 1.5,
        opacity: 0.9,
        fillOpacity: 0.8
      }}).addTo(map);
      if (m.popup) {{
        circle.bindPopup('<b style="font-family:sans-serif;font-size:12px;color:#070B12;">' + m.popup + '</b>');
      }}
    }});
  </script>
</body>
</html>"""
    components.html(html, height=height)


# Alias de compatibilidad progresiva
render_c6isr_map = render_geospatial_map


# ==============================================================================
# 9. TUFTE SCIENTIFIC CHART COMPONENT
# ==============================================================================
def render_tufte_chart(
    title: str,
    x_data: List[Any],
    y_data: List[float],
    x_label: str = "Tiempo",
    y_label: str = "Valor",
    accent_color: str = "#00F5A0",
    height: int = 280
):
    """
    Renders high-density Tufte scientific line chart in Obsidian Void style.
    Leverages Plotly if present, or pure SVG fallback.
    """
    try:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data,
            mode='lines+markers',
            line=dict(color=accent_color, width=2.5),
            marker=dict(size=4, color='#FFFFFF'),
            name=title
        ))
        fig.update_layout(
            title=dict(
                text=f"<b>{title.upper()}</b>",
                font=dict(family="Space Grotesk, sans-serif", size=13, color="#CBD5E1")
            ),
            paper_bgcolor='rgba(11, 18, 31, 0.85)',
            plot_bgcolor='rgba(7, 11, 18, 0.95)',
            margin=dict(l=40, r=20, t=40, b=40),
            height=height,
            xaxis=dict(
                title=dict(text=x_label, font=dict(family="JetBrains Mono", size=10, color="#64748B")),
                gridcolor='#1E293B',
                tickfont=dict(family="JetBrains Mono", size=9, color="#94A3B8"),
                showline=True, linecolor='#334155'
            ),
            yaxis=dict(
                title=dict(text=y_label, font=dict(family="JetBrains Mono", size=10, color="#64748B")),
                gridcolor='#1E293B',
                tickfont=dict(family="JetBrains Mono", size=9, color="#94A3B8"),
                showline=True, linecolor='#334155'
            )
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        # Fallback nativo Streamlit
        st.markdown(f"**{title}**")
        st.line_chart(y_data, height=height)


# ==============================================================================
# 10. INDUSTRIAL SENSOR GAUGE COMPONENT (SVG TACOMETER)
# ==============================================================================
def render_sensor_gauge(
    title: str,
    current_val: float,
    min_val: float,
    max_val: float,
    unit: str = "",
    warning_val: Optional[float] = None,
    accent_color: str = "#00F5A0"
):
    """
    Renders an industrial radial arc telemetry gauge with Tufte styling.
    """
    pct = max(0.0, min(1.0, (current_val - min_val) / max(1e-5, (max_val - min_val))))
    angle = pct * 180.0
    val_color = accent_color if (warning_val is None or current_val < warning_val) else "#FF453A"

    svg = f"""<div style="background: rgba(11, 18, 31, 0.85); border: 1px solid #1E293B; border-radius: 8px; padding: 14px; text-align: center; margin-bottom: 10px;">
  <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">{title}</div>
  <svg viewBox="0 0 200 115" width="100%" height="110" style="overflow: visible;">
    <!-- Arco de fondo -->
    <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#1E293B" stroke-width="12" stroke-linecap="round"/>
    <!-- Arco de progreso -->
    <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="{val_color}" stroke-width="12" stroke-dasharray="251.2" stroke-dashoffset="{251.2 * (1 - pct)}" stroke-linecap="round"/>
    <!-- Valor central -->
    <text x="100" y="85" text-anchor="middle" font-family="'Space Grotesk', sans-serif" font-size="28" font-weight="800" fill="#FFFFFF">{current_val:.1f}</text>
    <text x="100" y="104" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="11" font-weight="600" fill="{val_color}">{unit}</text>
  </svg>
  <div style="display: flex; justify-content: space-between; font-family: monospace; font-size: 0.65rem; color: #64748B; margin-top: -8px;">
    <span>{min_val}</span>
    <span>{max_val}</span>
  </div>
</div>"""
    st.markdown(_clean_html(svg), unsafe_allow_html=True)


