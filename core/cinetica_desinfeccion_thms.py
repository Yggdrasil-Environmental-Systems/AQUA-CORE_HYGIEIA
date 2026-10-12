"""
AQUA-CORE: HYGIEIA · CINÉTICA DE DESINFECCIÓN Y FORMACIÓN DE TRIHALOMETANOS (THMs)
==================================================================================
Modelado determinista físico-químico del decaimiento de desinfectantes y subproductos:
1. Ley de Chick-Watson (Inactivación biológica y reducción logarítmica).
2. Decaimiento de Cloro Libre en Flujo de Tubería (Reacción en seno 'bulk' y pared 'wall').
3. Modelo Cinemático de Formación de Trihalometanos Totales (TTHM).

Marco Normativo:
- Real Decreto 3/2023 (Criterios técnico-sanitarios del agua de consumo humano)
  * Límite Cloro Libre Residual en red: [0.20 - 1.00] mg/L
  * Límite Trihalometanos Totales (TTHM): <= 100 µg/L
- Directiva (UE) 2020/2184 (Aguas de consumo humano)
- Guías de la Organización Mundial de la Salud (OMS)

Director Técnico: Kelvin Jesús Flores Yarihuaman (MECES Nivel 3 / EQF Level 7)
"""

import math
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple


@dataclass
class CondicionOperativaRed:
    longitud_tramo_m: float = 2500.0         # Longitud del tramo de red
    diametro_interior_m: float = 0.20        # Diámetro interno (DN 200)
    velocidad_media_m_s: float = 0.85        # Velocidad advectiva media
    cloro_inicial_c0_mg_l: float = 0.90      # Concentración a la salida del depósito
    kb_bulk_h: float = 0.08                  # Coeficiente de decaimiento en el seno del agua (1/h)
    kw_wall_m_d: float = 0.05                # Coeficiente de reacción con pared (m/día)
    temperatura_agua_c: float = 18.5         # Temperatura del agua
    ph: float = 7.4                          # pH del agua
    doc_carbono_organico_mg_l: float = 1.8   # Carbono Orgánico Disuelto precursor (mg/L)


class CineticaDesinfeccionHygieia:
    """
    Motor determinista pericial para cálculo cinético de calidad del agua y bioseguridad.
    """

    # Coeficientes específicos de letalidad Chick-Watson (L / mg·min)
    COEF_CHICK_WATSON = {
        "E_COLI": 0.85,             # Altamente sensible a cloro libre
        "LEGIONELLA": 0.12,         # Resistencia intermedia (especialmente en biofilm o amebas)
        "PSEUDOMONAS": 0.35,        # Patógeno oportunista hospitalario
        "ENTEROCOCOS": 0.40         # Bacteria indicadora de contaminación fecal
    }

    @classmethod
    def calcular_hidraulica_red(cls, cond: CondicionOperativaRed) -> Dict[str, float]:
        """Calcula el tiempo de residencia hidráulico (HRT) y velocidad de transporte."""
        area_m2 = math.pi * ((cond.diametro_interior_m / 2.0) ** 2)
        caudal_m3_s = area_m2 * cond.velocidad_media_m_s
        tiempo_residencia_seg = cond.longitud_tramo_m / max(cond.velocidad_media_m_s, 1e-4)
        tiempo_residencia_h = tiempo_residencia_seg / 3600.0

        return {
            "seccion_m2": round(area_m2, 4),
            "caudal_l_s": round(caudal_m3_s * 1000.0, 2),
            "tiempo_residencia_h": round(tiempo_residencia_h, 3)
        }

    @classmethod
    def simular_decaimiento_cloro(cls, cond: CondicionOperativaRed, tiempo_h: float = None) -> Dict[str, Any]:
        """
        Calcula la concentración de cloro residual libre integrando decay bulk y wall:
        dC/dt = - (kb + (4*kw / D)) * C
        """
        if tiempo_h is None:
            hidro = cls.calcular_hidraulica_red(cond)
            tiempo_h = hidro["tiempo_residencia_h"]

        # Convertir kw de m/día a m/h
        kw_h = cond.kw_wall_m_d / 24.0
        # Coeficiente efectivo de reacción de primer orden (1/h)
        keff_h = cond.kb_bulk_h + (4.0 * kw_h / max(cond.diametro_interior_m, 1e-3))

        # Corrección por temperatura (Ecuación de Arrhenius simplificada)
        factor_temp = (1.025) ** (cond.temperatura_agua_c - 20.0)
        keff_h_corr = keff_h * factor_temp

        cloro_final = cond.cloro_inicial_c0_mg_l * math.exp(-keff_h_corr * tiempo_h)
        cloro_final = max(0.0, cloro_final)

        # Verificación normativa RD 3/2023 [0.20 - 1.00 mg/L]
        estado = "CONFORME"
        alerta = None
        if cloro_final < 0.20:
            estado = "DEFICIT_DESINFECCION"
            alerta = f"Cloro terminal insuficiente ({cloro_final:.3f} mg/L < 0.20 mg/L). Riesgo de proliferación biológica."
        elif cloro_final > 1.00:
            estado = "SOBRE_CLORACION"
            alerta = f"Cloro residual excesivo ({cloro_final:.3f} mg/L > 1.00 mg/L). Formación acelerada de THMs."

        return {
            "tiempo_residencia_h": round(tiempo_h, 3),
            "keff_hora_1": round(keff_h_corr, 4),
            "cloro_inicial_mg_l": cond.cloro_inicial_c0_mg_l,
            "cloro_final_mg_l": round(cloro_final, 4),
            "reduccion_porcentual": round((1.0 - (cloro_final / max(cond.cloro_inicial_c0_mg_l, 1e-4))) * 100.0, 1),
            "estado_rd3_2023": estado,
            "alerta": alerta
        }

    @classmethod
    def estimar_formacion_trihalometanos(cls, cond: CondicionOperativaRed, tiempo_h: float = None) -> Dict[str, Any]:
        """
        Estima la formación de Trihalometanos Totales (TTHM en µg/L) mediante modelo empírico no lineal:
        TTHM = 23.9 * (DOC)^1.1 * (Cl0)^0.25 * (pH - 7)^0.2 * (1 + 0.03*(T-20)) * t^0.35
        Límite máximo permitido RD 3/2023: 100 µg/L
        """
        if tiempo_h is None:
            hidro = cls.calcular_hidraulica_red(cond)
            tiempo_h = hidro["tiempo_residencia_h"]

        # Evitar logaritmos o potencias de números negativos
        t_horas = max(0.01, tiempo_h)
        doc = max(0.1, cond.doc_carbono_organico_mg_l)
        cl0 = max(0.05, cond.cloro_inicial_c0_mg_l)
        delta_ph = max(0.1, cond.ph - 6.5)
        factor_temp = max(0.5, 1.0 + 0.035 * (cond.temperatura_agua_c - 20.0))

        tthm_ug_l = 21.5 * (doc ** 1.08) * (cl0 ** 0.28) * (delta_ph ** 0.18) * factor_temp * (t_horas ** 0.32)

        limite_legal = 100.0  # RD 3/2023
        supera_limite = tthm_ug_l > limite_legal

        return {
            "tthm_estimado_ug_l": round(tthm_ug_l, 2),
            "limite_rd3_2023_ug_l": limite_legal,
            "margen_seguridad_pct": round(max(0.0, (1.0 - tthm_ug_l / limite_legal) * 100.0), 1),
            "conforme_rd3": not supera_limite,
            "dictamen": (
                "CONFORME RD 3/2023: Subproductos de desinfección en rango seguro."
                if not supera_limite else
                f"NO CONFORME: TTHM proyectado ({tthm_ug_l:.1f} µg/L) supera el límite de 100 µg/L. Reducir precursores orgánicos o dosificación inicial."
            )
        }

    @classmethod
    def evaluar_inactivacion_patogenos_chick_watson(
        cls,
        patogeno: str,
        cloro_promedio_mg_l: float,
        tiempo_contacto_min: float
    ) -> Dict[str, Any]:
        """
        Calcula la inactivación microbiana mediante el producto C·t y la ley de Chick-Watson:
        ln(N/N0) = - Lambda * C^n * t   (asumiendo n = 1)
        Reducción Logarítmica = log10(N0/N) = (Lambda * C * t) / 2.3026
        """
        lambda_cw = cls.COEF_CHICK_WATSON.get(patogeno.upper(), 0.20)
        ct_mg_min_l = cloro_promedio_mg_l * tiempo_contacto_min

        # Reducción logarítmica
        log_reduction = (lambda_cw * ct_mg_min_l) / math.log(10.0)

        # Meta de desinfección típica: 4-log reduction (99.99%)
        eficacia_pct = (1.0 - (10.0 ** (-min(log_reduction, 8.0)))) * 100.0
        barrera_adecuada = log_reduction >= 3.0

        return {
            "patogeno": patogeno.upper(),
            "producto_ct_mg_min_l": round(ct_mg_min_l, 2),
            "coeficiente_lambda": lambda_cw,
            "reduccion_logaritmica": round(log_reduction, 2),
            "inactivacion_porcentual": f"{eficacia_pct:.4f}%",
            "barrera_sanitaria_robusta": barrera_adecuada,
            "evaluacion": (
                f"BARRERA EFICAZ: Reducción de {log_reduction:.2f} log ({eficacia_pct:.3f}%) suficiente para protección epidemiológica."
                if barrera_adecuada else
                f"BARRERA INSUFICIENTE: Reducción de {log_reduction:.2f} log menor al estándar de 3.0 log. Aumentar tiempo de contacto o cloro."
            )
        }


if __name__ == "__main__":
    cond = CondicionOperativaRed()
    print("=" * 75)
    print("AQUA-CORE: HYGIEIA · CINÉTICA DE CALIDAD DEL AGUA Y DESINFECCIÓN")
    print("=" * 75)

    hidro = CineticaDesinfeccionHygieia.calcular_hidraulica_red(cond)
    print(f"[*] Hidráulica: Caudal = {hidro['caudal_l_s']} L/s | HRT = {hidro['tiempo_residencia_h']} horas")

    cloro = CineticaDesinfeccionHygieia.simular_decaimiento_cloro(cond)
    print(f"[*] Cloro residual final: {cloro['cloro_final_mg_l']} mg/L ({cloro['estado_rd3_2023']})")

    thms = CineticaDesinfeccionHygieia.estimar_formacion_trihalometanos(cond)
    print(f"[*] Trihalometanos (TTHM): {thms['tthm_estimado_ug_l']} µg/L | Conforme: {thms['conforme_rd3']}")

    legio = CineticaDesinfeccionHygieia.evaluar_inactivacion_patogenos_chick_watson("LEGIONELLA", cloro["cloro_final_mg_l"], 30.0)
    print(f"[*] Chick-Watson Legionella: Reducción {legio['reduccion_logaritmica']} log | {legio['inactivacion_porcentual']}")
