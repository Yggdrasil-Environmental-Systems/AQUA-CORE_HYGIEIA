"""
AQUA-CORE: HYGIEIA · Saneamiento Temporal y Puntos de Agua en Emergencia
========================================================================
Marco Regulatorio y Técnico:
- Orden DCA/1079/2026 (BOE-A-2026-21231 de 12/10/2026 · BOE núm. 253)
- Real Decreto 3/2023 (Criterios técnico-sanitarios del agua de consumo humano)
- Real Decreto 1620/2007 (Régimen jurídico de la reutilización de las aguas depuradas)
- Norma UNE-EN 12566 (Pequeñas instalaciones de depuración de aguas residuales)
- Estándares SPHERE / OMS para abastecimiento de agua y saneamiento en emergencias

Director Técnico: Kelvin Jesús Flores Yarihuaman (MECES Nivel 3 / EQF Level 7)
"""

import math
import hashlib
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class ParametrosPuntoAguaTemporal:
    """Parámetros de puntos de agua, depósitos móviles y redes temporales de abastecimiento."""
    id_punto: str = "DEP-MOVIL-EMERG-01"
    tipo_deposito: str = "CISTERNA_MOVIL"  # "CISTERNA_MOVIL", "TANQUE_FLEXIBLE", "DEPOSITO_MODULAR_PEAD"
    volumen_deposito_m3: float = 25.0       # Volumen total útil en m³
    poblacion_atendida_hab: int = 250       # Número de personas abastecidas
    dotacion_l_hab_dia: float = 50.0        # Dotación básica de emergencia (50 L/hab·día según OMS/SPHERE)
    cloro_libre_actual_mg_l: float = 0.55   # Rango legal RD 3/2023: 0.20 - 1.00 mg/L
    turbidez_unf: float = 1.1               # Límite RD 3/2023: <= 4.0 UNF
    ph: float = 7.35                        # Rango RD 3/2023: 6.5 - 9.5
    temperatura_c: float = 19.5             # Temperatura de agua almacenada
    tiempo_estanqueidad_horas: float = 18.0 # Tiempo transcurrido desde el último llenado


@dataclass
class ParametrosSaneamientoAutonomo:
    """Parámetros para dimensionamiento de saneamiento autónomo y depuración compacta."""
    id_sistema: str = "SAN-AUTONOMO-EMERG-01"
    tipo_tecnologia: str = "MODULO_COMPACTO_BIOLOGICO_UV"  # "FOSA_SEPTICA_ESTANCA", "MODULO_COMPACTO_BIOLOGICO_UV", "OXIDACION_TOTAL"
    habitantes_equivalentes_he: int = 150                 # Carga contaminante en HE
    dotacion_vertido_l_he_dia: float = 120.0              # Vertido estimado L/HE·día
    dbo5_afluente_mg_l: float = 320.0                     # Concentración típica DBO5 agua residual bruta
    mes_afluente_mg_l: float = 380.0                      # Materia en Suspensión entrada
    coliformes_fecales_entrada_ufc_100ml: float = 2.5e6   # Carga microbiológica afluente bruta
    dosis_uv_mj_cm2: float = 45.0                         # Dosis fluencia ultravioleta en mJ/cm²
    concentracion_hipoclorito_pct: float = 15.0           # Concentración comercial hipoclorito sódico (%)
    frecuencia_vaciado_fangos_meses: int = 12             # Periodicidad de retirada de lodos
    distancia_acuifero_o_sondeo_m: float = 65.0          # Distancia al punto de agua subterránea más cercano
    tipo_terreno: str = "LIMOSO_ARCILLOSO"                # "ARENOSO_PERMEABLE", "LIMOSO_ARCILLOSO", "ROCOSO_FRACTURADO"


class DimensionadorSaneamientoEmergencia:
    """
    Motor determinista pericial para cumplimiento de la Orden DCA/1079/2026,
    Real Decreto 3/2023 y Real Decreto 1620/2007.
    """

    @classmethod
    def auditar_punto_agua_temporal(cls, punto: ParametrosPuntoAguaTemporal) -> Dict[str, Any]:
        """
        Evalúa la conformidad del punto de agua móvil y calcula dosificación de compensación.
        """
        alertas = []
        no_conformidades = []
        cloro = punto.cloro_libre_actual_mg_l
        vol_l = punto.volumen_deposito_m3 * 1000.0

        # Consumo diario total
        consumo_diario_l = punto.poblacion_atendida_hab * punto.dotacion_l_hab_dia
        autonomia_dias = round(vol_l / max(1.0, consumo_diario_l), 2)

        # 1. Auditoría Cloro Residual Libre (RD 3/2023: 0.20 - 1.00 mg/L)
        dosis_correctora_g_cloro = 0.0
        ml_hipoclorito_15pct = 0.0

        if cloro < 0.20:
            alerta_msg = f"Déficit crítico de cloro residual ({cloro:.2f} mg/L < 0.20 mg/L). Riesgo microbiológico inminente."
            alertas.append(alerta_msg)
            no_conformidades.append({
                "norma": "Real Decreto 3/2023 Art. 13 & Orden DCA/1079/2026",
                "parametro": "Cloro Libre Residual",
                "valor": f"{cloro:.2f} mg/L",
                "limite": "0.20 - 1.00 mg/L",
                "accion": "Dosificación de choque correctora inmediata."
            })
            # Llevar el cloro al punto óptimo de 0.60 mg/L
            cloro_objetivo = 0.60
            delta_cloro = cloro_objetivo - cloro
            # Masa Cl2 (g) = Delta(mg/L) * Vol(m³)
            dosis_correctora_g_cloro = round(delta_cloro * punto.volumen_deposito_m3, 2)
            # Hipoclorito 15% activo (150 g Cl2 / L)
            ml_hipoclorito_15pct = round((dosis_correctora_g_cloro / 150.0) * 1000.0, 1)

        elif cloro > 1.00:
            alertas.append(f"Sobre-cloración en depósito ({cloro:.2f} mg/L > 1.00 mg/L). Riesgo de sabor y subproductos THMs.")
            no_conformidades.append({
                "norma": "Real Decreto 3/2023 Anexo I",
                "parametro": "Cloro Libre Residual",
                "valor": f"{cloro:.2f} mg/L",
                "limite": "0.20 - 1.00 mg/L",
                "accion": "Dilución con agua de renovación o desgasificación."
            })

        # 2. Turbidez (RD 3/2023 <= 4.0 UNF en red, ideal <= 1.0 UNF para UV)
        if punto.turbidez_unf > 4.0:
            alertas.append(f"Turbidez inadmisible ({punto.turbidez_unf:.1f} UNF > 4.0 UNF). Requiere filtración previa.")
            no_conformidades.append({
                "norma": "Real Decreto 3/2023 Anexo I",
                "parametro": "Turbidez",
                "valor": f"{punto.turbidez_unf:.1f} UNF",
                "limite": "<= 4.0 UNF",
                "accion": "Instalar filtro de lecho de arena / cartuchos 5 µm."
            })

        # 3. pH (RD 3/2023: 6.5 - 9.5)
        if not (6.5 <= punto.ph <= 9.5):
            alertas.append(f"pH fuera de rango normativo ({punto.ph:.2f}).")
            no_conformidades.append({
                "norma": "Real Decreto 3/2023",
                "parametro": "pH",
                "valor": f"{punto.ph:.2f}",
                "limite": "6.50 - 9.50",
                "accion": "Corrección de equilibrio carbocalcónico."
            })

        # 4. Tiempo de estanqueidad sin renovación
        alerta_estanqueidad = False
        if punto.tiempo_estanqueidad_horas > 72.0:
            alerta_estanqueidad = True
            alertas.append(f"Almacenamiento estático prolongado ({punto.tiempo_estanqueidad_horas:.0f} h > 72 h). Obligatoria renovación o purga perimetral.")

        apto = len(no_conformidades) == 0

        # Huella de trazabilidad
        raw_hash = f"{punto.id_punto}|{punto.volumen_deposito_m3}|{cloro}|{datetime.utcnow().isoformat()}"
        hash_forense = hashlib.sha256(raw_hash.encode()).hexdigest()[:16].upper()

        return {
            "id_punto": punto.id_punto,
            "tipo_deposito": punto.tipo_deposito,
            "volumen_m3": punto.volumen_deposito_m3,
            "consumo_diario_l_dia": consumo_diario_l,
            "autonomia_dias": autonomia_dias,
            "cloro_actual_mg_l": cloro,
            "turbidez_unf": punto.turbidez_unf,
            "ph": punto.ph,
            "conforme_rd3_dca1079": apto,
            "dictamen_potabilidad": (
                "AGUA APTA PARA EL CONSUMO HUMANO (RD 3/2023 & DCA/1079/2026)"
                if apto else
                "AGUA NO CONFORME EN PUNTO TEMPORAL - REQUIERE MEDIDAS CORRECTORAS"
            ),
            "dosis_correctora_g_cloro": dosis_correctora_g_cloro,
            "ml_hipoclorito_15pct": ml_hipoclorito_15pct,
            "total_no_conformidades": len(no_conformidades),
            "no_conformidades": no_conformidades,
            "alertas": alertas,
            "alerta_estanqueidad_72h": alerta_estanqueidad,
            "hash_trazabilidad": hash_forense
        }

    @classmethod
    def dimensionar_saneamiento_autonomo(cls, san: ParametrosSaneamientoAutonomo) -> Dict[str, Any]:
        """
        Dimensiona fosas sépticas estancas, módulos compactos y desinfección UV según UNE-EN 12566
        y ratios de bioseguridad de la Orden DCA/1079/2026 y RD 1620/2007.
        """
        alertas = []
        no_conformidades = []

        # Caudal afluente diario
        q_diario_m3 = (san.habitantes_equivalentes_he * san.dotacion_vertido_l_he_dia) / 1000.0
        q_horario_medio_m3_h = q_diario_m3 / 24.0

        # 1. Dimensionamiento Hidráulico Fosa Séptica Estanca (UNE-EN 12566-1)
        # Tiempo de Retención Hidráulica (HRT): mínimo 36h a 48h
        hrt_dias = 2.0 if san.habitantes_equivalentes_he < 50 else 1.5
        vol_sedimentacion_m3 = q_diario_m3 * hrt_dias

        # Volumen de lodos (0.18 m³/HE·año)
        tasa_lodos_m3_he_ano = 0.18
        vol_lodos_m3 = san.habitantes_equivalentes_he * tasa_lodos_m3_he_ano * (san.frecuencia_vaciado_fangos_meses / 12.0)

        vol_util_minimo_m3 = round(max(3.0, vol_sedimentacion_m3 + vol_lodos_m3), 2)
        dimension_largo_m = round(math.pow(vol_util_minimo_m3 * 2.0, 1/3), 2)
        dimension_ancho_m = round(dimension_largo_m / 2.0, 2)
        calado_agua_m = round(vol_util_minimo_m3 / (dimension_largo_m * dimension_ancho_m), 2)

        # 2. Rendimiento Depuración Biológica (DBO5 y MES)
        if san.tipo_tecnologia == "FOSA_SEPTICA_ESTANCA":
            rend_dbo5_pct = 40.0
            rend_mes_pct = 65.0
            rend_coliformes_base_log = 1.0  # 90% reducción primaria
        elif san.tipo_tecnologia == "MODULO_COMPACTO_BIOLOGICO_UV":
            rend_dbo5_pct = 88.0
            rend_mes_pct = 92.0
            rend_coliformes_base_log = 2.5  # 99.7% reducción biológica previa
        else: # OXIDACION_TOTAL
            rend_dbo5_pct = 94.0
            rend_mes_pct = 95.0
            rend_coliformes_base_log = 3.0

        dbo5_efluente_mg_l = round(san.dbo5_afluente_mg_l * (1.0 - rend_dbo5_pct / 100.0), 1)
        mes_efluente_mg_l = round(san.mes_afluente_mg_l * (1.0 - rend_mes_pct / 100.0), 1)

        # 3. Cinética de Inactivación Ultravioleta (Chick-Watson UV Modificada)
        # N = N_0 * 10^(-k_uv * D_uv / ln(10))
        # Para coliformes fecales / E. coli: constante cinética k_uv ~ 0.22 cm²/mJ
        k_uv = 0.22
        # Carga remanente antes de UV
        n_prev_uv = san.coliformes_fecales_entrada_ufc_100ml * math.pow(10, -rend_coliformes_base_log)
        
        # Reducción logarítmica adicional por radiación UV
        log_reduccion_uv = (k_uv * san.dosis_uv_mj_cm2) / math.log(10.0)
        coliformes_finales_ufc_100ml = n_prev_uv * math.pow(10, -log_reduccion_uv)
        coliformes_finales_ufc_100ml = round(max(0.0, coliformes_finales_ufc_100ml), 4)

        # Criterio estricto de la Orden DCA/1079/2026: < 1 UFC/100 mL
        cumple_desinfeccion_estricta = coliformes_finales_ufc_100ml < 1.0

        if not cumple_desinfeccion_estricta:
            # Calcular dosis UV mínima requerida para alcanzar < 1 UFC/100 mL
            log_req_total = math.log10(max(1.0, san.coliformes_fecales_entrada_ufc_100ml))
            log_req_uv = max(0.0, log_req_total - rend_coliformes_base_log)
            dosis_uv_necesaria_mj_cm2 = round((log_req_uv * math.log(10.0)) / k_uv, 1)

            alertas.append(
                f"Desinfección insuficiente: Coliformes ({coliformes_finales_ufc_100ml:.2f} UFC/100 mL >= 1.0 UFC/100 mL). "
                f"Se requiere elevar dosis UV a >= {dosis_uv_necesaria_mj_cm2} mJ/cm² o añadir cloración de barrera."
            )
            no_conformidades.append({
                "norma": "Orden DCA/1079/2026 & RD 1620/2007 Anexo I.A",
                "parametro": "Coliformes Fecales / E. coli",
                "valor": f"{coliformes_finales_ufc_100ml:.2f} UFC/100 mL",
                "limite": "< 1 UFC/100 mL",
                "accion": f"Aumentar fluencia UV a >= {dosis_uv_necesaria_mj_cm2} mJ/cm²."
            })
        else:
            dosis_uv_necesaria_mj_cm2 = san.dosis_uv_mj_cm2

        # 4. Verificación de Riesgo Hidrogeológico a Acuíferos Locales
        dist_min_legal = 50.0 if san.tipo_terreno == "ARENOSO_PERMEABLE" else 35.0
        riesgo_acuifero = False
        if san.distancia_acuifero_o_sondeo_m < dist_min_legal:
            riesgo_acuifero = True
            alertas.append(
                f"DISTANCIA INSEGURA AL ACUÍFERO: {san.distancia_acuifero_o_sondeo_m} m < {dist_min_legal} m reglamentarios. "
                "Exigencia estricta de estanqueidad total certificada UNE-EN 12566 sin infiltración."
            )
            no_conformidades.append({
                "norma": "Orden DCA/1079/2026 & Ley de Aguas Art. 100",
                "parametro": "Distancia de Seguridad Hidrogeológica",
                "valor": f"{san.distancia_acuifero_o_sondeo_m:.1f} m",
                "limite": f">= {dist_min_legal:.1f} m",
                "accion": "Instalar estanqueidad certificada sin infiltración o reubicar fosa."
            })

        apto_global = len(no_conformidades) == 0

        # Curva de inactivación cinética UV para gráficos
        dosis_sim = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]
        curva_inactivacion = []
        for d in dosis_sim:
            log_red = (k_uv * d) / math.log(10.0)
            ufc_sim = n_prev_uv * math.pow(10, -log_red)
            curva_inactivacion.append({
                "dosis_uv_mj_cm2": d,
                "coliformes_ufc_100ml": round(ufc_sim, 4),
                "log_inactivacion": round(log_red + rend_coliformes_base_log, 2)
            })

        raw_hash = f"{san.id_sistema}|{san.habitantes_equivalentes_he}|{coliformes_finales_ufc_100ml}|{datetime.utcnow().isoformat()}"
        hash_forense = hashlib.sha256(raw_hash.encode()).hexdigest()[:16].upper()

        return {
            "id_sistema": san.id_sistema,
            "tecnologia": san.tipo_tecnologia,
            "habitantes_equivalentes_he": san.habitantes_equivalentes_he,
            "caudal_diario_m3_dia": round(q_diario_m3, 3),
            "caudal_medio_m3_h": round(q_horario_medio_m3_h, 3),
            "volumen_util_fosa_m3": vol_util_minimo_m3,
            "dimensiones_estimadas_m": {
                "largo_m": dimension_largo_m,
                "ancho_m": dimension_ancho_m,
                "calado_agua_m": calado_agua_m
            },
            "tiempo_retencion_hidraulica_dias": hrt_dias,
            "reduccion_dbo5_pct": rend_dbo5_pct,
            "dbo5_efluente_mg_l": dbo5_efluente_mg_l,
            "reduccion_mes_pct": rend_mes_pct,
            "mes_efluente_mg_l": mes_efluente_mg_l,
            "dosis_uv_aplicada_mj_cm2": san.dosis_uv_mj_cm2,
            "dosis_uv_recomendada_mj_cm2": dosis_uv_necesaria_mj_cm2,
            "coliformes_fecales_efluente_ufc_100ml": coliformes_finales_ufc_100ml,
            "cumple_ratio_coliformes_menor_1": cumple_desinfeccion_estricta,
            "riesgo_acuifero_local": riesgo_acuifero,
            "distancia_seguridad_minima_m": dist_min_legal,
            "conforme_orden_dca1079_rd1620": apto_global,
            "dictamen_pericial_saneamiento": (
                "CONFORME ORDEN DCA/1079/2026: Saneamiento autónomo bioseguro con protección total de acuíferos."
                if apto_global else
                "NO CONFORME: Desviación sanitaria en ratio de desinfección o distancia de protección hidrogeológica."
            ),
            "total_no_conformidades": len(no_conformidades),
            "no_conformidades": no_conformidades,
            "alertas": alertas,
            "curva_inactivacion": curva_inactivacion,
            "curva_inactivacion_uv": curva_inactivacion,
            "hash_trazabilidad": hash_forense
        }
