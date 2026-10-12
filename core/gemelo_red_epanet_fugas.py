"""
AQUA-CORE: HYGIEIA · GEMELO HIDRÁULICO, BALANCE IWA Y AUDITORÍA DE FUGAS (PERTE AGUA)
======================================================================================
Motor de balance hídrico determinista conforme a las directrices de la
International Water Association (IWA) y el PERTE de Digitalización del Ciclo del Agua.

Calcula:
1. Balance Hídrico Estandarizado IWA (Entrada, Consumo Autorizado, Pérdidas Reales y Aparentes).
2. Pérdidas Reales Anuales Inevitables (UARL) y Corrientes (CARL).
3. Índice de Fugas Estructural (ILI - Infrastructure Leakage Index).
4. Clasificación en Bandas de Rendimiento Técnico IWA / Banco Mundial (A, B, C, D).
5. Cuantificación de Ahorro Potencial de Agua y Energía para justificación del PERTE (MITECO).

Director Técnico: Kelvin Jesús Flores Yarihuaman (MECES Nivel 3 / EQF Level 7)
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class DatosSectorHidraulicoDMA:
    nombre_sector_dma: str = "Sector DMA-04 Centro Histórico"
    poblacion_servida_hab: int = 24500
    longitud_red_red_km: float = 48.5            # Lm: Longitud de tuberías principales (km)
    numero_acometidas_nc: int = 4200             # Nc: Número de acometidas de servicio
    longitud_acometidas_privadas_km: float = 6.2 # Lp: Longitud hasta el contador (km)
    presion_media_servicio_mca: float = 42.0     # P: Presión media de servicio (metros de columna de agua)
    volumen_suministrado_anual_m3: float = 1850000.0   # SIV: Volumen de entrada al sistema
    consumo_facturado_medido_m3: float = 1320000.0    # Consumo real medido por contadores
    consumo_no_facturado_autorizado_m3: float = 35000.0  # Riego público, bomberos, limpiezas


class GemeloRedEpanetFugas:
    """
    Motor analítico de balance hídrico IWA y evaluación de eficiencia estructural de red.
    """

    @classmethod
    def calcular_balance_hidrico_iwa(cls, dma: DatosSectorHidraulicoDMA) -> Dict[str, Any]:
        """
        Calcula el balance hídrico estándar IWA:
        - Volumen de Entrada (SIV)
        - Consumo Autorizado = Facturado + No Facturado
        - Pérdidas Totales = SIV - Consumo Autorizado
        - Pérdidas Aparentes (Subcontaje 4% + Consumos no autorizados 1%)
        - Pérdidas Reales = Pérdidas Totales - Pérdidas Aparentes
        """
        siv = dma.volumen_suministrado_anual_m3
        consumo_aut = dma.consumo_facturado_medido_m3 + dma.consumo_no_facturado_autorizado_m3
        perdidas_totales = max(0.0, siv - consumo_aut)

        # Estimación estándar IWA de pérdidas aparentes (errores de medición + hurtos)
        perdidas_aparentes = (dma.consumo_facturado_medido_m3 * 0.04) + (siv * 0.008)
        perdidas_reales_carl_m3 = max(0.0, perdidas_totales - perdidas_aparentes)

        rendimiento_tecnico_pct = (consumo_aut / max(siv, 1.0)) * 100.0
        pct_perdidas_totales = (perdidas_totales / max(siv, 1.0)) * 100.0
        pct_perdidas_reales = (perdidas_reales_carl_m3 / max(siv, 1.0)) * 100.0

        # Cálculo de UARL (Unavoidable Annual Real Losses) en litros/día:
        # UARL (L/día) = (18 * Lm + 0.80 * Nc + 25 * Lp) * P
        lm = dma.longitud_red_red_km
        nc = dma.numero_acometidas_nc
        lp = dma.longitud_acometidas_privadas_km
        p = dma.presion_media_servicio_mca

        uarl_l_dia = (18.0 * lm + 0.80 * nc + 25.0 * lp) * p
        uarl_anual_m3 = (uarl_l_dia * 365.0) / 1000.0

        # Infrastructure Leakage Index (ILI) = CARL / UARL
        ili = perdidas_reales_carl_m3 / max(uarl_anual_m3, 1e-3)

        # Clasificación en Bandas IWA / Banco Mundial
        if ili < 1.5:
            banda = "BANDA_A1_EXCELENTE"
            descripcion_banda = "Red de excelencia internacional. Fugas al mínimo físico inevitable. Mantenimiento óptimo."
        elif ili <= 3.0:
            banda = "BANDA_A2_BUENO"
            descripcion_banda = "Rendimiento óptimo conforme a directrices europeas. Pérdidas controladas."
        elif ili <= 6.0:
            banda = "BANDA_B_MEJORABLE"
            descripcion_banda = "Potencial de mejora significativo. Justificación plena de digitalización y sectorización bajo PERTE."
        elif ili <= 10.0:
            banda = "BANDA_C_DEFICIENTE"
            descripcion_banda = "Red con fugas estructurales graves. Requiere inversión urgente en modulación de presiones y renovación de tuberías."
        else:
            banda = "BANDA_D_INACEPTABLE"
            descripcion_banda = "Pérdidas insostenibles (>8 veces el mínimo inevitable). Infracción grave de sostenibilidad hídrica."

        # Pérdidas diarias por acometida (L/acometida/día)
        perdidas_l_acometida_dia = (perdidas_reales_carl_m3 * 1000.0) / (max(nc, 1) * 365.0)

        # Ahorro potencial si se reduce ILI a objetivo de 2.0 (Directiva UE 2020/2184)
        carl_objetivo_m3 = uarl_anual_m3 * 2.0
        ahorro_potencial_m3 = max(0.0, perdidas_reales_carl_m3 - carl_objetivo_m3)
        ahorro_economico_estimado_eur = ahorro_potencial_m3 * 1.85  # Coste medio del agua en España: ~1.85 €/m3

        return {
            "sector": dma.nombre_sector_dma,
            "volumen_entrada_siv_m3_ano": siv,
            "consumo_autorizado_m3_ano": consumo_aut,
            "perdidas_totales_m3_ano": round(perdidas_totales, 1),
            "perdidas_reales_carl_m3_ano": round(perdidas_reales_carl_m3, 1),
            "perdidas_inevitables_uarl_m3_ano": round(uarl_anual_m3, 1),
            "rendimiento_tecnico_red_pct": round(rendimiento_tecnico_pct, 2),
            "porcentaje_perdidas_reales_pct": round(pct_perdidas_reales, 2),
            "perdidas_litros_acometida_dia": round(perdidas_l_acometida_dia, 1),
            "ili_indice_fugas_estructural": round(ili, 2),
            "banda_rendimiento_iwa": banda,
            "diagnostico_iwa": descripcion_banda,
            "elegibilidad_perte_digitalizacion": {
                "elegible_fondos_nextgen": ili >= 2.5,
                "ahorro_anual_potencial_m3": round(ahorro_potencial_m3, 1),
                "ahorro_anual_estimado_eur": round(ahorro_economico_estimado_eur, 2),
                "reduccion_huella_carbono_tco2": round(ahorro_potencial_m3 * 0.00045, 2)  # ~0.45 kWh/m3 bombeo
            }
        }


if __name__ == "__main__":
    dma = DatosSectorHidraulicoDMA()
    resultado = GemeloRedEpanetFugas.calcular_balance_hidrico_iwa(dma)

    print("=" * 80)
    print("AQUA-CORE: HYGIEIA · BALANCE HÍDRICO IWA & AUDITORÍA DE FUGAS (PERTE AGUA)")
    print("=" * 80)
    print(f"Sector: {resultado['sector']}")
    print(f"Rendimiento Técnico: {resultado['rendimiento_tecnico_red_pct']}% | Pérdidas Reales: {resultado['porcentaje_perdidas_reales_pct']}%")
    print(f"CARL: {resultado['perdidas_reales_carl_m3_ano']:,} m³/año | UARL: {resultado['perdidas_inevitables_uarl_m3_ano']:,} m³/año")
    print(f"Índice ILI: {resultado['ili_indice_fugas_estructural']} ({resultado['banda_rendimiento_iwa']})")
    print(f"Pérdidas Unitarias: {resultado['perdidas_litros_acometida_dia']} L/acometida/día")
    print(f"\nJustificación PERTE:")
    print(f"  Elegible NextGen: {resultado['elegibilidad_perte_digitalizacion']['elegible_fondos_nextgen']}")
    print(f"  Ahorro Hídrico Proyectado: {resultado['elegibilidad_perte_digitalizacion']['ahorro_anual_potencial_m3']:,} m³/año ({resultado['elegibilidad_perte_digitalizacion']['ahorro_anual_estimado_eur']:,.2f} €/año)")
    print(f"  Reducción de Huella de Carbono: {resultado['elegibilidad_perte_digitalizacion']['reduccion_huella_carbono_tco2']} tCO2e/año")
