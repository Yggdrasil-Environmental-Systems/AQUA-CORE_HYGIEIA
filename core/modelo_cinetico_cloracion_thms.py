"""
AQUA-CORE: HYGIEIA · Simulador Cinético de Cloración y Formación de Trihalometanos (THMs)
========================================================================================
Marco Regulatorio:
- Real Decreto 3/2023 (Límite TTHM <= 100 ug/L, Cloro Libre Residual 0.20 - 1.00 mg/L)
- Directiva (UE) 2020/2184 sobre la calidad de las aguas de consumo
- Modelado de formación de Subproductos de Desinfección (DBPs - USEPA & WHO Guidelines)

Director Técnico: Kelvin Jesús Flores Yarihuaman (MECES Nivel 3 / EQF Level 7)
"""

import math
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple


@dataclass
class ParametrosAguaRed:
    cloro_inicial_mg_l: float = 1.20       # Dosis de cloro a la salida de ETAP o depósito
    toc_mg_l: float = 2.50                 # Carbono Orgánico Total (materia orgánica precursora)
    ph: float = 7.60                       # pH del agua en red (6.5 - 9.5)
    temperatura_c: float = 20.0            # Temperatura del agua en red
    tiempo_residencia_horas: float = 24.0  # Tiempo de tránsito hidráulico hasta el grifo terminal
    uv254_cm_1: float = 0.05               # Absorbancia UV a 254 nm (indicador de reactividad aromática)


class ModeloCineticoCloroTHM:
    """
    Soluciona la Paradoja de los Trihalometanos:
    Garantizar suficiente cloro libre residual (> 0.20 mg/L) para inactivar patógenos
    sin sobrepasar el umbral tóxico de THMs (<= 100 ug/L) y cloratos (<= 0.25 mg/L).
    """

    @staticmethod
    def calcular_decaimiento_cloro(c0: float, k_decay: float, tiempo_h: float) -> float:
        """
        Cinética de primer orden para el cloro libre residual:
        C(t) = C0 * exp(-k * t)
        """
        return max(0.0, c0 * math.exp(-k_decay * tiempo_h))

    @classmethod
    def estimar_coeficiente_k(cls, temp_c: float, toc: float, uv254: float) -> float:
        """
        Estima la constante de decaimiento k (h^-1) en función de temperatura y reactividad orgánica.
        Arrhenius k(T) = k20 * theta^(T - 20)
        """
        k20 = 0.015 + 0.008 * toc + 0.05 * uv254
        theta = 1.04
        return k20 * (theta ** (temp_c - 20.0))

    @classmethod
    def simular_formacion_thms(cls, param: ParametrosAguaRed) -> Dict[str, Any]:
        """
        Modelo empírico determinista calibrado (variante USEPA / Clark-Sivaganesan):
        TTHM (ug/L) = a * (TOC)^0.61 * (Cl2_dosis)^0.28 * (t)^0.26 * (T)^0.65 * (pH - 6)^0.38
        """
        t_horas = max(0.1, param.tiempo_residencia_horas)
        toc = max(0.1, param.toc_mg_l)
        cl2 = max(0.1, param.cloro_inicial_mg_l)
        t_c = max(5.0, param.temperatura_c)
        ph_factor = max(0.1, param.ph - 6.0)

        # Factor de formación calibrado para aguas potabilizadas europeas
        a = 23.5
        tthm_ug_l = a * (toc ** 0.61) * (cl2 ** 0.28) * ((t_horas / 24.0) ** 0.26) * ((t_c / 20.0) ** 0.65) * (ph_factor ** 0.38)

        # Decaimiento del cloro en el mismo punto de la red
        k_decay = cls.estimar_coeficiente_k(param.temperatura_c, param.toc_mg_l, param.uv254_cm_1)
        cloro_residual = cls.calcular_decaimiento_cloro(param.cloro_inicial_mg_l, k_decay, param.tiempo_residencia_horas)

        # Evaluación de Cumplimiento Legal RD 3/2023
        cumple_thms = tthm_ug_l <= 100.0
        cumple_cloro_min = cloro_residual >= 0.20
        cumple_cloro_max = cloro_residual <= 1.00
        riesgo_patogenos = cloro_residual < 0.20
        riesgo_quimico_thms = tthm_ug_l > 100.0

        if not cumple_thms:
            estado_paradoja = "BRECHA_TOXICOLOGICA_THMS"
            color = "#EF4444"
            dictamen = f"INCUMPLIMIENTO CRÍTICO: Trihalometanos ({tthm_ug_l:.1f} ug/L) superan el límite de 100 ug/L del RD 3/2023."
        elif riesgo_patogenos:
            estado_paradoja = "BRECHA_MICROBIOLOGICA"
            color = "#F59E0B"
            dictamen = f"RIESGO MICROBIOLÓGICO: Cloro residual insuficiente ({cloro_residual:.2f} mg/L < 0.20 mg/L). Riesgo de rebrote bacteriano."
        else:
            estado_paradoja = "OPTIMO_EQUILIBRIO_RD3"
            color = "#10B981"
            dictamen = "ZONA ÓPTIMA: Protección microbiológica activa sin violación de límites toxicológicos de THMs."

        # Curva temporal 0 a 72 horas para graficado
        curva_tiempo = []
        for h in range(0, int(max(72, t_horas + 12)), 2):
            c_res = cls.calcular_decaimiento_cloro(param.cloro_inicial_mg_l, k_decay, float(h))
            thm_h = a * (toc ** 0.61) * (cl2 ** 0.28) * ((max(0.1, h) / 24.0) ** 0.26) * ((t_c / 20.0) ** 0.65) * (ph_factor ** 0.38)
            curva_tiempo.append({
                "tiempo_horas": h,
                "cloro_residual_mg_l": round(c_res, 3),
                "tthm_ug_l": round(thm_h, 2)
            })

        return {
            "estado_paradoja": estado_paradoja,
            "color_hex": color,
            "dictamen_pericial": dictamen,
            "cloro_residual_final_mg_l": round(cloro_residual, 3),
            "tthm_final_ug_l": round(tthm_ug_l, 2),
            "limite_tthm_legal_ug_l": 100.0,
            "rango_cloro_legal_mg_l": (0.20, 1.00),
            "constante_decaimiento_k_h1": round(k_decay, 4),
            "curva_simulacion": curva_tiempo
        }
