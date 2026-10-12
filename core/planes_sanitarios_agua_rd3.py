"""
AQUA-CORE: HYGIEIA · PLANES SANITARIOS DEL AGUA Y CONTROL DE LEGIONELLA
Marco Regulatorio:
- Real Decreto 3/2023 (Criterios técnico-sanitarios de la calidad del agua de consumo humano - PSA)
- Real Decreto 487/2022 (Prevención y control de la legionelosis en instalaciones de riesgo)
- Guías de la Organización Mundial de la Salud (OMS) para la Calidad del Agua Potable
Director Técnico: Kelvin Jesús Flores Yarihuaman (MECES Nivel 3 / EQF Level 7)
"""

from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class AnaliticaAguaConsumoRD3:
    punto_muestreo: str = "Red de Distribución Urbana - Sector 3"
    cloro_libre_residual_mg_l: float = 0.65       # Rango legal: 0.20 - 1.00 mg/L
    turbidez_unf: float = 1.2                     # Límite en red: <= 4.0 UNF
    ph: float = 7.45                              # Rango: 6.5 - 9.5
    conductividad_us_cm: float = 480.0            # Límite: <= 2500 uS/cm
    e_coli_ufc_100ml: int = 0                     # Límite: 0 UFC/100ml
    enterococos_ufc_100ml: int = 0                # Límite: 0 UFC/100ml
    suma_20_pfas_ug_l: float = 0.02               # Límite RD 3/2023: <= 0.10 ug/L
    cloratos_mg_l: float = 0.08                   # Límite: <= 0.25 mg/L


@dataclass
class InspeccionLegionellaRD487:
    tipo_instalacion: str = "ACS_CON_RETORNO"     # "ACS_CON_RETORNO", "TORRE_REFRIGERACION", "CONDENSADOR_EVAPORATIVO"
    temp_acumulador_c: float = 62.0               # Exigencia RD 487/2022: >= 60.0 °C
    temp_grifo_alejado_c: float = 52.5            # Exigencia RD 487/2022: >= 50.0 °C
    recuento_legionella_ufc_l: float = 0.0        # < 100 normal; 100-1000 alerta; > 1000 choque
    biocida_residual_mg_l: float = 0.50           # Desinfectante residual en circuito


class HygieiaSanitaryWaterEngine:
    """
    Motor determinista pericial para auditoría y dictamen de Planes Sanitarios del Agua (PSA)
    y evaluación de riesgo de proliferación de Legionella.
    """

    @classmethod
    def auditar_calidad_agua_rd3(cls, analitica: AnaliticaAguaConsumoRD3) -> Dict[str, Any]:
        alertas = []

        # 1. Desinfección
        if analitica.cloro_libre_residual_mg_l < 0.20:
            alertas.append(f"Cloro libre insuficiente ({analitica.cloro_libre_residual_mg_l} mg/L < 0.20 mg/L). Riesgo microbiológico.")
        elif analitica.cloro_libre_residual_mg_l > 1.00:
            alertas.append(f"Sobre-cloración en red ({analitica.cloro_libre_residual_mg_l} mg/L > 1.00 mg/L). Formación de subproductos THMs.")

        # 2. Físico-Químicos
        if analitica.turbidez_unf > 4.0:
            alertas.append(f"Turbidez elevada ({analitica.turbidez_unf} UNF > 4.0 UNF). Pérdida de transparencia e interferencia de desinfección.")
        if not (6.5 <= analitica.ph <= 9.5):
            alertas.append(f"pH fuera de rango ({analitica.ph} fuera de 6.5 - 9.5). Riesgo de corrosión o incrustación.")

        # 3. Microbiológicos
        if analitica.e_coli_ufc_100ml > 0 or analitica.enterococos_ufc_100ml > 0:
            alertas.append("CONTAMINACIÓN FECAL DETECTADA: Incumplimiento crítico de bacterias indicadoras (E. coli / Enterococos).")

        # 4. Químicos Emergentes
        if analitica.suma_20_pfas_ug_l > 0.10:
            alertas.append(f"Superación del umbral de PFAS ({analitica.suma_20_pfas_ug_l} ug/L > 0.10 ug/L). Riesgo toxicológico persistente.")
        if analitica.cloratos_mg_l > 0.25:
            alertas.append(f"Exceso de cloratos ({analitica.cloratos_mg_l} mg/L > 0.25 mg/L).")

        apto_consumo = len(alertas) == 0

        return {
            "punto_muestreo": analitica.punto_muestreo,
            "cloro_libre_mg_l": analitica.cloro_libre_residual_mg_l,
            "turbidez_unf": analitica.turbidez_unf,
            "ph": analitica.ph,
            "microbiologia_conforme": (analitica.e_coli_ufc_100ml == 0 and analitica.enterococos_ufc_100ml == 0),
            "pfas_conforme": analitica.suma_20_pfas_ug_l <= 0.10,
            "total_alertas": len(alertas),
            "alertas_sanitarias": alertas,
            "calificacion_rd3_2023": "AGUA APTA PARA EL CONSUMO HUMANO" if apto_consumo else "AGUA NO APTA CON RIESGO PARA LA SALUD",
            "dictamen_psa": (
                "CONFORME RD 3/2023: Red en control operativo dentro de los parámetros de calidad sanitaria."
                if apto_consumo else
                f"NO CONFORME: Se requieren medidas correctoras inmediatas por {len(alertas)} desviaciones sanitarias."
            )
        }

    @classmethod
    def auditar_riesgo_legionella_rd487(cls, insp: InspeccionLegionellaRD487) -> Dict[str, Any]:
        alertas = []

        # 1. Régimen de Temperatura (Art. 7 y Anexo III RD 487/2022)
        if insp.tipo_instalacion == "ACS_CON_RETORNO":
            if insp.temp_acumulador_c < 60.0:
                alertas.append(f"Temperatura en acumulador insuficiente ({insp.temp_acumulador_c} °C < 60.0 °C). Foco de multiplicación térmica.")
            if insp.temp_grifo_alejado_c < 50.0:
                alertas.append(f"Temperatura en grifo terminal insuficiente ({insp.temp_grifo_alejado_c} °C < 50.0 °C). Circuito de retorno deficiente.")

        # 2. Recuento de Legionella
        ufc = insp.recuento_legionella_ufc_l
        if ufc < 100.0:
            nivel_accion = "NIVEL 1 (CONTROL RUTINARIO): Recuento < 100 UFC/L. Instalación en estado seguro."
        elif ufc <= 1000.0:
            nivel_accion = "NIVEL 2 (ALERTA INTERMEDIA): Recuento 100 - 1000 UFC/L. Revisión de biocida y purga preventiva."
            alertas.append("Presencia intermedia de Legionella (100 - 1000 UFC/L).")
        else:
            nivel_accion = "NIVEL 3 (PELIGRO SANITARIO): Recuento > 1000 UFC/L. Desinfección de choque y parada cautelar obligatoria."
            alertas.append(f"BROTE POTENCIAL: Recuento de Legionella crítico ({ufc} UFC/L > 1000 UFC/L).")

        conforme_instalacion = len(alertas) == 0

        return {
            "instalacion": insp.tipo_instalacion,
            "temp_acumulador_c": insp.temp_acumulador_c,
            "temp_terminal_c": insp.temp_grifo_alejado_c,
            "recuento_legionella_ufc_l": ufc,
            "nivel_accion_rd487": nivel_accion,
            "conforme_normativa_rd487": conforme_instalacion,
            "alertas_legionella": alertas,
            "dictamen_pericial_ppcl": (
                "CONFORME RD 487/2022: Instalación sanitariamente conforme con barrera térmica y biocida eficaz."
                if conforme_instalacion else
                f"NO CONFORME RD 487/2022: Requiere actuación inmediata en el Plan de Prevención y Control de Legionella (PPCL)."
            )
        }


if __name__ == "__main__":
    agua = AnaliticaAguaConsumoRD3()
    res_agua = HygieiaSanitaryWaterEngine.auditar_calidad_agua_rd3(agua)
    print("=" * 70)
    print("AQUA-CORE: HYGIEIA · DICTAMEN CALIDAD DEL AGUA (RD 3/2023)")
    print("=" * 70)
    print(f"Punto: {res_agua['punto_muestreo']} | Cloro libre: {res_agua['cloro_libre_mg_l']} mg/L")
    print(f"Calificación: {res_agua['calificacion_rd3_2023']}")

    legio = InspeccionLegionellaRD487()
    res_legio = HygieiaSanitaryWaterEngine.auditar_riesgo_legionella_rd487(legio)
    print("\n" + "=" * 70)
    print("AQUA-CORE: HYGIEIA · CONTROL DE LEGIONELLA (RD 487/2022)")
    print("=" * 70)
    print(f"Instalación: {res_legio['instalacion']} | Acumulador: {res_legio['temp_acumulador_c']} °C | Grifo: {res_legio['temp_terminal_c']} °C")
    print(f"Acción: {res_legio['nivel_accion_rd487']}")
    print(f"Dictamen: {res_legio['dictamen_pericial_ppcl']}")
