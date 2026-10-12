"""
AQUA-CORE: HYGIEIA · Gemelo Digital de Redes y Balance Hídrico PERTE (3.000 M€)
=============================================================================
Marco Técnico y Regulatorio:
- PERTE de Digitalización del Ciclo del Agua (Orden TED/934/2022 y MITECO)
- Balance Hídrico Estándar IWA (International Water Association)
- Protocolo de Intercambio de Datos con SINAC (Ministerio de Sanidad)
- Reducción de Pérdidas de Agua en Redes Urbanas (Media España: 23,5% de fugas)

Director Técnico: Kelvin Jesús Flores Yarihuaman (MECES Nivel 3 / EQF Level 7)
"""

from dataclasses import dataclass
from typing import Dict, Any, List
import json
from datetime import datetime


@dataclass
class SectorHidrometricoDMA:
    nombre_sector: str = "Sector DMA-04 Centro Histórico"
    poblacion_servida: int = 15400
    longitud_red_km: float = 38.5
    presion_media_bar: float = 3.8
    volumen_suministrado_diario_m3: float = 3850.0  # Caudalímetro electromagnético de entrada
    volumen_facturado_diario_m3: float = 2950.0     # Contadores domiciliarios teleleídos
    caudal_minimo_nocturno_m3_h: float = 48.0       # Medido entre 02:00 y 04:00 AM (MNF)
    consumo_legitimo_nocturno_m3_h: float = 12.5    # Estimación de descargas e industrias nocturnas


class GemeloDigitalRedesPERTE:
    """
    Simulador determinista de balance hídrico, pérdidas reales y detección de fugas
    para interoperabilidad con el PERTE del Agua y SINAC.
    """

    @classmethod
    def calcular_balance_hidrico_iwa(cls, dma: SectorHidrometricoDMA) -> Dict[str, Any]:
        vol_sum = max(1.0, dma.volumen_suministrado_diario_m3)
        vol_fact = max(0.0, dma.volumen_facturado_diario_m3)

        # 1. Agua No Registrada (ANR / Non-Revenue Water - NRW)
        anr_m3_dia = max(0.0, vol_sum - vol_fact)
        porcentaje_anr = (anr_m3_dia / vol_sum) * 100.0

        # 2. Análisis del Caudal Mínimo Nocturno (MNF) para Fugas Invisibles
        caudal_fugas_nocturno_m3_h = max(0.0, dma.caudal_minimo_nocturno_m3_h - dma.consumo_legitimo_nocturno_m3_h)
        volumen_fugas_reales_dia_m3 = caudal_fugas_nocturno_m3_h * 24.0 * 0.90 # Factor de corrección de presión diurna

        # Pérdidas aparentes (subcontaje y consumos no medidos)
        volumen_perdidas_aparentes_m3 = max(0.0, anr_m3_dia - volumen_fugas_reales_dia_m3)

        # 3. Índice de Pérdidas por Kilómetro de Red (m3/km/día)
        perdidas_km_dia = anr_m3_dia / max(0.1, dma.longitud_red_km)

        # 4. Clasificación de Severidad PERTE
        # Meta PERTE: reducir pérdidas por debajo del 15% en redes urbanas
        if porcentaje_anr > 25.0:
            estado_perte = "CRITICO_VULNERABLE"
            color_hex = "#EF4444"
            recomendacion = "URGENTE: Sector con pérdidas superiores a la media nacional (23,5%). Prioridad 1 en elegibilidad de subvención PERTE para sectorización, sensores acústicos de fugas y válvulas reguladoras de presión (PRVs)."
        elif porcentaje_anr > 15.0:
            estado_perte = "MODERADO_MEJORABLE"
            color_hex = "#F59E0B"
            recomendacion = "Sector en zona intermedia. Despliegue de telelectura inteligente de contadores y control dinámico de presiones nocturnas."
        else:
            estado_perte = "EFICIENTE_SOSTENIBLE"
            color_hex = "#10B981"
            recomendacion = "Sector de alta eficiencia (<15% pérdidas). Cumple con los objetivos de digitalización y resiliencia de la Directiva UE 2020/2184."

        return {
            "nombre_sector": dma.nombre_sector,
            "porcentaje_anr": round(porcentaje_anr, 2),
            "anr_m3_dia": round(anr_m3_dia, 2),
            "perdidas_reales_fugas_m3_dia": round(volumen_fugas_reales_dia_m3, 2),
            "perdidas_aparentes_subcontaje_m3_dia": round(volumen_perdidas_aparentes_m3, 2),
            "perdidas_especificas_m3_km_dia": round(perdidas_km_dia, 2),
            "caudal_fugas_nocturno_m3_h": round(caudal_fugas_nocturno_m3_h, 2),
            "estado_perte": estado_perte,
            "color_hex": color_hex,
            "dictamen_perte": recomendacion,
            "cumple_meta_perte_15_porc": porcentaje_anr <= 15.0
        }

    @classmethod
    def generar_payload_interoperable_sinac(cls, dma: SectorHidrometricoDMA, balance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera el paquete de datos estructurado para sincronización con SINAC (Ministerio de Sanidad)
        y la plataforma de seguimiento del PERTE del Agua.
        """
        return {
            "version_protocolo": "SINAC-PERTE-v3.2",
            "timestamp": datetime.now().isoformat(),
            "zona_abastecimiento": {
                "denominacion": dma.nombre_sector,
                "poblacion_censada": dma.poblacion_servida,
                "longitud_red_km": dma.longitud_red_km,
                "presion_media_bar": dma.presion_media_bar
            },
            "indicadores_eficiencia_hidrica": {
                "volumen_suministrado_anual_m3": round(dma.volumen_suministrado_diario_m3 * 365, 0),
                "volumen_facturado_anual_m3": round(dma.volumen_facturado_diario_m3 * 365, 0),
                "rendimiento_tecnico_red_porc": round(100.0 - balance["porcentaje_anr"], 2),
                "agua_no_registrada_porc": balance["porcentaje_anr"],
                "volumen_fugas_estimado_m3_dia": balance["perdidas_reales_fugas_m3_dia"]
            },
            "certificacion_pericial": {
                "director_tecnico": "Kelvin Jesús Flores Yarihuaman",
                "credencial": "MECES Nivel 3 / EQF Level 7",
                "norma_referencia": "Real Decreto 3/2023 / Orden TED/934/2022"
            }
        }
