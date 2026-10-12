"""
AQUA-CORE: HYGIEIA · Evaluador Pericial de Riesgo de Legionelosis (RD 487/2022)
==============================================================================
Marco Regulatorio:
- Real Decreto 487/2022 (Requisitos sanitarios para la prevención y control de la legionelosis)
- Guía Técnica del Ministerio de Sanidad para Prevención de Legionelosis
- Norma UNE 100030:2017 (Prevención y control de la proliferación y diseminación de Legionella)
- Responsabilidad procesal y civil del titular en edificios prioritarios (Hospitales, Residencias, Hoteles)

Director Técnico: Kelvin Jesús Flores Yarihuaman (MECES Nivel 3 / EQF Level 7)
"""

from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class MedicionInstalacionACS:
    identificador_edificio: str = "Complejo Hospitalario Metropolitano - Bloque Quirúrgico"
    tipo_sistema: str = "ACS_CON_RETORNO"  # "ACS_CON_RETORNO", "ACS_SIN_RETORNO", "TORRE_REFRIGERACION"
    temp_acumulador_c: float = 62.5       # Exigencia RD 487/2022: >= 60.0 °C continuo
    temp_retorno_c: float = 51.8          # Exigencia RD 487/2022: >= 50.0 °C
    temp_grifo_alejado_c: float = 50.5    # Exigencia RD 487/2022: >= 50.0 °C antes de 1 min
    temp_afch_c: float = 18.0             # Agua Fría Consumo Humano: <= 20.0 °C
    recuento_legionella_ufc_l: float = 0.0 # UFC/L: <100 conforme; 100-1000 alerta; >1000 choque
    biocida_residual_mg_l: float = 0.50   # Concentración de biocida (cloro/dióxido/monocloramina)
    dias_desde_ultima_purga: int = 3      # Exigencia: purga semanal de fondo de acumulador


class EvaluadorLegionellaRD487:
    """
    Evaluador determinista de conformidad sanitaria y riesgo legal bajo RD 487/2022.
    """

    @classmethod
    def auditar_instalacion(cls, med: MedicionInstalacionACS) -> Dict[str, Any]:
        no_conformidades = []
        alertas = []
        score_seguridad = 100

        # 1. Auditoría Térmica de Acumulación (Barrera Primaria)
        if med.temp_acumulador_c < 60.0:
            deficit_acum = 60.0 - med.temp_acumulador_c
            score_seguridad -= min(40, int(deficit_acum * 8))
            no_conformidades.append({
                "clausula": "RD 487/2022 Anexo III (Temperatura Acumulador)",
                "severidad": "CRÍTICA",
                "descripcion": f"Temperatura en acumulador ({med.temp_acumulador_c:.1f} °C) inferior a los 60.0 °C obligatorios.",
                "accion_inmediata": "Aumentar consigna de caldera/intercambiador térmico inmediatamente a >= 60 °C."
            })

        # 2. Auditoría Térmica de Retorno
        if med.tipo_sistema == "ACS_CON_RETORNO":
            if med.temp_retorno_c < 50.0:
                deficit_ret = 50.0 - med.temp_retorno_c
                score_seguridad -= min(25, int(deficit_ret * 5))
                no_conformidades.append({
                    "clausula": "RD 487/2022 Anexo III (Temperatura Retorno)",
                    "severidad": "GRAVE",
                    "descripcion": f"Temperatura en anillo de retorno ({med.temp_retorno_c:.1f} °C) inferior a 50.0 °C.",
                    "accion_inmediata": "Equilibrar hidráulicamente el circuito de retorno y aislar conducciones térmicamente."
                })

        # 3. Auditoría en Grifo Terminal más Alejado
        if med.temp_grifo_alejado_c < 50.0:
            deficit_term = 50.0 - med.temp_grifo_alejado_c
            score_seguridad -= min(25, int(deficit_term * 5))
            no_conformidades.append({
                "clausula": "RD 487/2022 Anexo III (Puntos Terminales)",
                "severidad": "GRAVE",
                "descripcion": f"Punto terminal más alejado ({med.temp_grifo_alejado_c:.1f} °C) no alcanza los 50.0 °C.",
                "accion_inmediata": "Revisar pérdidas de carga y balanceo térmico en montantes finales."
            })

        # 4. Agua Fría de Consumo Humano (AFCH)
        if med.temp_afch_c > 20.0:
            score_seguridad -= 15
            alertas.append(f"Agua fría a {med.temp_afch_c:.1f} °C (> 20.0 °C). Zona de proliferación potencial de Legionella.")

        # 5. Criterio Microbiológico (UFC/L de Legionella pneumophila)
        ufc = med.recuento_legionella_ufc_l
        if ufc >= 1000.0:
            score_seguridad = 0
            nivel_alerta = "EMERGENCIA_CHOQUE"
            color_hex = "#EF4444"
            protocolo_sanitario = (
                "INTERVENCIÓN INMEDIATA REQUERIDA (RD 487/2022 Art. 13):\n"
                "1. Clausura cautelar del uso de duchas y aerosolizadores en el sector afectado.\n"
                "2. Desinfección de choque térmica (70 °C durante 2 horas en todos los terminales) "
                "o hipercloración de choque (20-30 mg/L cloro libre durante 2-4 horas con posterior purga total).\n"
                "3. Toma de muestras de verificación a los 15 días de la desinfección."
            )
        elif ufc >= 100.0:
            score_seguridad -= 35
            nivel_alerta = "ALERTA_PREVENTIVA"
            color_hex = "#F59E0B"
            protocolo_sanitario = (
                "ACCIÓN CORRECTIVA EN 15 DÍAS (RD 487/2022):\n"
                "1. Limpieza y purga profunda del acumulador y tramos terminales estancados.\n"
                "2. Verificación de nivel de biocida residual (> 0.40 mg/L).\n"
                "3. Re-muestreo confirmatorio en 15 días naturales."
            )
        else:
            nivel_alerta = "CONFORME_BIOSEGURA"
            color_hex = "#10B981"
            protocolo_sanitario = "Instalación en régimen bioseguro de control continuo y mantenimiento preventivo ordinario."

        # 6. Mantenimiento y Purgas
        if med.dias_desde_ultima_purga > 7:
            score_seguridad -= 10
            alertas.append(f"Purga de fondo de acumulador demorada ({med.dias_desde_ultima_purga} días > 7 días estipulados).")

        score_seguridad = max(0, min(100, score_seguridad))

        return {
            "nivel_alerta": nivel_alerta,
            "color_hex": color_hex,
            "score_bioseguridad": score_seguridad,
            "no_conformidades_formales": no_conformidades,
            "alertas_operativas": alertas,
            "protocolo_sanitario_rd487": protocolo_sanitario,
            "conformidad_global": len(no_conformidades) == 0 and ufc < 100.0
        }
