"""
AQUA-CORE: HYGIEIA · EVALUADOR FORENSE DE RIESGO DE LEGIONELLA (RD 487/2022)
============================================================================
Motor de diagnóstico y prescripción técnica para:
- Planes de Prevención y Control de Legionella (PPCL)
- Planes Sanitarios de Legionela (PSL)
- Evaluación de Barreras Térmicas, Purgas y Dosificación de Biocidas

Marco Legal Oficial:
- Real Decreto 487/2022, de 21 de junio (BOE-A-2022-10297)
- Norma UNE 100030:2017 (Prevención de Legionella en instalaciones)
- Directiva (UE) 2020/2184 (Agua de consumo)

Director Técnico: Kelvin Jesús Flores Yarihuaman (MECES Nivel 3 / EQF Level 7)
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class PuntoMuestreoTermico:
    identificador: str
    ubicacion: str
    temperatura_c: float
    tipo_punto: str  # "ACUMULADOR_ACS", "RETORNO_ACS", "GRIFO_TERMINAL_ACS", "RED_FRIA_AFCH", "TORRE_REFRIGERACION"


@dataclass
class AnaliticaMicrobiologicaLegionella:
    fecha_toma: str
    laboratorio_acreditado_iso17025: str
    recuento_legionella_spp_ufc_l: float
    serogrupo_detectado: Optional[str] = None  # "L. pneumophila serogrupo 1" (el más virulento)
    biocida_residual_mg_l: float = 0.50        # Concentración de biocida (cloro, dióxido de cloro, monocloramina)
    turbidez_circuito_unf: float = 0.8
    hierro_total_mg_l: float = 0.05            # Nutriente crítico para biofilm


class EvaluadorRiesgoLegionellaRD487:
    """
    Evaluador determinista pericial conforme al Anexo III y Artículos 6, 7 y 8 del RD 487/2022.
    """

    @classmethod
    def auditar_barrera_termica(cls, puntos: List[PuntoMuestreoTermico]) -> Dict[str, Any]:
        """
        Verifica el cumplimiento de los límites térmicos obligatorios:
        - Acumulador ACS: >= 60.0 °C
        - Retorno y Grifos terminales ACS: >= 50.0 °C
        - Agua Fría de Consumo Humano (AFCH): <= 20.0 °C
        """
        desviaciones = []
        resumen_puntos = []

        for p in puntos:
            conforme = True
            norma_ref = ""
            if p.tipo_punto == "ACUMULADOR_ACS":
                norma_ref = ">= 60.0 °C (Art. 7.2 RD 487/2022)"
                if p.temperatura_c < 60.0:
                    conforme = False
                    desviaciones.append(f"DEFICIT TÉRMICO en {p.identificador} ({p.ubicacion}): {p.temperatura_c}°C < 60.0°C. Multiplicación activa de Legionella.")
            elif p.tipo_punto in ("RETORNO_ACS", "GRIFO_TERMINAL_ACS"):
                norma_ref = ">= 50.0 °C (Art. 7.2 RD 487/2022)"
                if p.temperatura_c < 50.0:
                    conforme = False
                    desviaciones.append(f"DEFICIT TÉRMICO en {p.identificador} ({p.ubicacion}): {p.temperatura_c}°C < 50.0°C. Retorno deficiente o estancamiento en ramal.")
            elif p.tipo_punto == "RED_FRIA_AFCH":
                norma_ref = "<= 20.0 °C (Art. 7.1 RD 487/2022)"
                if p.temperatura_c > 20.0:
                    conforme = False
                    desviaciones.append(f"CALENTAMIENTO INDESEADO en {p.identificador} ({p.ubicacion}): {p.temperatura_c}°C > 20.0°C. Proximidad a conductos de calefacción.")

            resumen_puntos.append({
                "id": p.identificador,
                "ubicacion": p.ubicacion,
                "temp_c": p.temperatura_c,
                "norma_exigida": norma_ref,
                "conforme": conforme
            })

        return {
            "total_puntos_inspeccionados": len(puntos),
            "total_desviaciones_termicas": len(desviaciones),
            "barrera_termica_integra": len(desviaciones) == 0,
            "desviaciones": desviaciones,
            "detalle_puntos": resumen_puntos
        }

    @classmethod
    def clasificar_nivel_accion_microbiologico(
        cls,
        analitica: AnaliticaMicrobiologicaLegionella,
        tipo_instalacion: str = "ACS"
    ) -> Dict[str, Any]:
        """
        Clasifica el recuento bacteriano en los 3 Niveles de Acción del Anexo III del RD 487/2022:
        - Nivel 1: < 100 UFC/L (Normal)
        - Nivel 2: 100 - 1.000 UFC/L (Alerta intermedia)
        - Nivel 3: > 1.000 UFC/L (Peligro sanitario)
        """
        ufc = analitica.recuento_legionella_spp_ufc_l
        acciones_obligatorias = []
        nivel = "NIVEL_1"
        gravedad = "BAJA"

        if ufc < 100.0:
            nivel = "NIVEL_1_NORMALIDAD"
            gravedad = "CONTROL_RUTINARIO"
            acciones_obligatorias.append("Continuar programa de mantenimiento preventivo y registro en libro oficial.")
        elif ufc <= 1000.0:
            nivel = "NIVEL_2_ALERTA_INTERMEDIA"
            gravedad = "MEDIA_ALERTA"
            acciones_obligatorias.extend([
                "Revisión inmediata de temperatura y residual de biocida en circuito.",
                "Purga de fondo de acumuladores y griferías terminales de bajo uso.",
                "Limpieza y desinfección preventiva del sector afectado en plazo < 7 días.",
                "Remuestreo de confirmación a los 15-30 días."
            ])
        else:
            nivel = "NIVEL_3_PELIGRO_SANITARIO"
            gravedad = "CRÍTICA_EMERGENCIA"
            acciones_obligatorias.extend([
                "PARADA CAUTELAR O RESTRICCIÓN DE USO de duchas / puntos de aerosolización.",
                "Comunicación obligatoria a la Autoridad Sanitaria competente.",
                "DESINFECCIÓN DE CHOQUE (Térmica a >70°C o Hipercloración a 20-50 mg/L) según Anexo IV.",
                "Limpieza mecánica profunda de depósitos, desincrustación de difusores y sustitución de elementos porosos.",
                "Remuestreo obligatorio previo a la reapertura de la instalación."
            ])

        # Factor agravante si es Serogrupo 1
        alerta_serogrupo = None
        if analitica.serogrupo_detectado and "serogrupo 1" in analitica.serogrupo_detectado.lower():
            alerta_serogrupo = "ALERTA MÁXIMA DE VIRULENCIA: Detectada cepa Legionella pneumophila SG1, responsable del 85% de casos clínicos de legionelosis."

        return {
            "recuento_ufc_l": ufc,
            "nivel_accion_rd487": nivel,
            "gravedad": gravedad,
            "acciones_legales_obligatorias": acciones_obligatorias,
            "alerta_cepa_virulenta": alerta_serogrupo,
            "biocida_residual_mg_l": analitica.biocida_residual_mg_l,
            "conformidad_biocida": 0.20 <= analitica.biocida_residual_mg_l <= 1.00
        }

    @classmethod
    def emitir_dictamen_pericial_legionella(
        cls,
        edificio_nombre: str,
        es_edificio_prioritario: bool,
        puntos_termicos: List[PuntoMuestreoTermico],
        analitica: AnaliticaMicrobiologicaLegionella
    ) -> Dict[str, Any]:
        """
        Emite el Dictamen Pericial Oficial visado bajo el Art. 335 de la Ley de Enjuiciamiento Civil.
        """
        res_termico = cls.auditar_barrera_termica(puntos_termicos)
        res_micro = cls.clasificar_nivel_accion_microbiologico(analitica)

        conforme_global = res_termico["barrera_termica_integra"] and (res_micro["nivel_accion_rd487"] == "NIVEL_1_NORMALIDAD")

        modalidad_plan = "PLAN SANITARIO DE LEGIONELA (PSL - Enfoque Riesgo Completo)" if es_edificio_prioritario else "PLAN DE PREVENCIÓN Y CONTROL DE LEGIONELLA (PPCL)"

        dictamen_texto = (
            f"DICTAMEN FAVORABLE: La instalación en '{edificio_nombre}' cumple con las barreras térmicas y el recuento "
            f"bacteriano reglamentario del Real Decreto 487/2022. Estado conforme con el {modalidad_plan}."
            if conforme_global else
            f"DICTAMEN DESFAVORABLE CON MANDATO DE ACCIÓN: Se detectaron {res_termico['total_desviaciones_termicas']} desviaciones térmicas "
            f"y recuento en {res_micro['nivel_accion_rd487']}. Se exige ejecución inmediata de medidas de contingencia conforme a Lex Artis."
        )

        return {
            "fecha_emision": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "director_tecnico": "Kelvin Jesús Flores Yarihuaman (MECES Nivel 3 / EQF Level 7)",
            "edificio": edificio_nombre,
            "tipo_edificio": "EDIFICIO PRIORITARIO (Hospitalario / Sociosanitario)" if es_edificio_prioritario else "INSTALACIÓN INDUSTRIAL / TERCIARIA",
            "modalidad_gestion_rd487": modalidad_plan,
            "calificacion_global": "CONFORME RD 487/2022" if conforme_global else "NO CONFORME - ACCIÓN OBLIGATORIA",
            "resumen_termico": res_termico,
            "resumen_microbiologico": res_micro,
            "dictamen_pericial_conclusivo": dictamen_texto
        }


if __name__ == "__main__":
    puntos = [
        PuntoMuestreoTermico("ACUM-01", "Central Térmica - Acumulador 1", 63.5, "ACUMULADOR_ACS"),
        PuntoMuestreoTermico("RET-01", "Circuito Retorno Sector Este", 52.0, "RETORNO_ACS"),
        PuntoMuestreoTermico("GRIFO-12", "Habitación 304 - Grifo Terminal", 48.2, "GRIFO_TERMINAL_ACS"),
        PuntoMuestreoTermico("AFCH-01", "Acometida Agua Fría Aljibe", 17.8, "RED_FRIA_AFCH")
    ]
    analitica = AnaliticaMicrobiologicaLegionella(
        fecha_toma="2026-10-10",
        laboratorio_acreditado_iso17025="LAB-SANIDAD-MADRID-09",
        recuento_legionella_spp_ufc_l=450.0,
        serogrupo_detectado="Legionella pneumophila serogrupo 1",
        biocida_residual_mg_l=0.35
    )

    dictamen = EvaluadorRiesgoLegionellaRD487.emitir_dictamen_pericial_legionella(
        edificio_nombre="Hospital Sanitario Modelo - Madrid",
        es_edificio_prioritario=True,
        puntos_termicos=puntos,
        analitica=analitica
    )

    print("=" * 80)
    print("AQUA-CORE: HYGIEIA · DICTAMEN PERICIAL RD 487/2022 (CONTROL DE LEGIONELLA)")
    print("=" * 80)
    print(f"Edificio: {dictamen['edificio']} | Modalidad: {dictamen['modalidad_gestion_rd487']}")
    print(f"Calificación: {dictamen['calificacion_global']}")
    print(f"Nivel de Acción Microbiológico: {dictamen['resumen_microbiologico']['nivel_accion_rd487']}")
    print(f"Desviaciones Térmicas: {dictamen['resumen_termico']['total_desviaciones_termicas']}")
    print(f"\nConclusión Pericial:\n{dictamen['dictamen_pericial_conclusivo']}")
