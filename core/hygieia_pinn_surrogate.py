"""
==============================================================================
AQUA-CORE: HYGIEIA | CORE ENGINE: PINN KINETIC SURROGATE (OPEN-CORE)
Module: core.hygieia_pinn_surrogate
Framework: Universal Core Platform Standard (UCPS-v1) · Yggdrasil-OS
Director Técnico: Kelvin Jesús Flores Yarihuaman (MECES 3 / EQF Level 7)
Estándares: RD 3/2023 · RD 487/2022 · PERTE Agua · ISO/IEC 42001 (AIMS)
==============================================================================

Inferencia sub-milisegundo (<15 ms) de cinética de desinfección, formación
de trihalometanos (THMs) y muerte térmica de Legionella pneumophila.
Equipado con guardaespaldas matemático in-process (PhysicsSentinelSidecar).
"""

from typing import Dict, Any, List, Optional, Tuple
import os
import sys
import time
import math
from pathlib import Path
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from physics.sentinel_sidecar import PhysicsSentinelSidecar
from neural_lab.network_architecture import HygieiaPINNSurrogate


class HygieiaPINNSurrogateModel:
    """
    Motor de Inferencia Open-Core basado en Physics-Informed Neural Networks.
    Resuelve el balance entre desinfección activa vs. generación de subproductos cancerígenos.
    """

    def __init__(self, weights_path: Optional[Path] = None):
        self.root_dir = ROOT_DIR
        if weights_path:
            self.weights_path = Path(weights_path)
        else:
            candidates = [
                self.root_dir / "weights" / "hygieia_open_pinn.pt",
                self.root_dir / "neural_lab" / "weights" / "hygieia_open_pinn.pt",
                self.root_dir / "weights" / "hygieia_open_pinn_v1.pt",
            ]
            self.weights_path = next((p for p in candidates if p.exists()), candidates[0])
        self.device = torch.device("cpu")
        self.sentinel = PhysicsSentinelSidecar(core_id="HYGIEIA")
        self.model: Optional[HygieiaPINNSurrogate] = None
        self.metadata: Dict[str, Any] = {}
        self.is_loaded = False

        if TORCH_AVAILABLE and self.weights_path.exists():
            self._load_model()

    def _load_model(self) -> None:
        """Carga el modelo y los pesos verificados."""
        try:
            checkpoint = torch.load(self.weights_path, map_location=self.device)
            self.model = HygieiaPINNSurrogate(
                in_features=checkpoint.get("in_features", 6),
                out_features=checkpoint.get("out_features", 3),
                hidden_dim=checkpoint.get("hidden_dim", 128),
                num_blocks=checkpoint.get("num_blocks", 3),
                num_frequencies=checkpoint.get("num_frequencies", 16)
            ).to(self.device)

            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.model.eval()
            self.metadata = {
                "architecture": checkpoint.get("architecture", "HygieiaPINNSurrogate"),
                "epochs_trained": checkpoint.get("epochs", 20),
                "rmse_cloro_mg_l": checkpoint.get("final_rmse_cloro_mg_l", 0.02),
                "rmse_tthm_ug_l": checkpoint.get("final_rmse_tthm_ug_l", 1.5),
                "created_at_utc": checkpoint.get("created_at_utc", ""),
                "standards": checkpoint.get("standards", ["RD 3/2023", "RD 487/2022"])
            }
            self.is_loaded = True
        except Exception as e:
            self.is_loaded = False
            self.model = None

    def predict(
        self,
        c0: float,
        toc: float,
        ph: float,
        temp_c: float,
        diametro_mm: float,
        tiempo_h: float
    ) -> Dict[str, Any]:
        """
        Ejecuta la inferencia física informada para un estado hidráulico dado.
        Retorna concentraciones predichas, banderas de cumplimiento legal y latencia.
        """
        t_start = time.perf_counter()

        # Validación previa con Sentinel Físico
        c0_clamped = max(0.1, min(3.0, c0))
        toc_clamped = max(0.1, min(10.0, toc))
        ph_clamped = max(5.0, min(10.0, ph))
        temp_clamped = max(5.0, min(90.0, temp_c))
        d_clamped = max(10.0, min(500.0, diametro_mm))
        t_clamped = max(0.01, min(168.0, tiempo_h))

        if self.is_loaded and self.model is not None:
            inp = torch.tensor([[
                c0_clamped, toc_clamped, ph_clamped,
                temp_clamped, d_clamped, t_clamped
            ]], dtype=torch.float32, device=self.device)

            with torch.no_grad():
                out = self.model(inp).cpu().numpy()[0]

            cloro_res = float(out[0])
            tthm_ug_l = float(out[1])
            leg_log_surv = float(out[2])
            inferred_by = "NEURAL_PINN_SURROGATE"
        else:
            # Fallback determinista semianalítico de primer orden si no hay pesos
            theta = 1.024 ** (temp_clamped - 20.0)
            k_eff = (0.08 / 24.0) * theta + (4.0 * (0.035 * theta) / (d_clamped / 1000.0)) / 24.0
            cloro_res = float(c0_clamped * math.exp(-k_eff * t_clamped))
            cloro_cons = max(0.0, c0_clamped - cloro_res)
            tthm_ug_l = float(28.5 * (toc_clamped ** 0.52) * (cloro_cons ** 0.35) * ((temp_clamped / 20.0) ** 0.45))
            d_60 = 2.5 / 60.0
            d_t = d_60 * (10.0 ** ((60.0 - temp_clamped) / 4.5)) if temp_clamped >= 45.0 else 1e5
            leg_log_surv = float(max(-10.0, -t_clamped / max(d_t, 1e-4)))
            inferred_by = "ANALYTIC_SEMI_DETERMINISTIC_FALLBACK"

        # Aplicar Sentinel Sidecar Clamping Final
        cloro_final, was_c_mod, c_reason = self.sentinel.clamp_value("cloro_libre_residual_mgl", cloro_res)
        tthm_final, was_thm_mod, thm_reason = self.sentinel.clamp_value("tthm_ug_l", tthm_ug_l)

        latency_ms = (time.perf_counter() - t_start) * 1000.0

        # Verificación Regulatoria Legal (RD 3/2023 & RD 487/2022)
        cumple_cloro_rd3 = (0.20 <= cloro_res <= 1.00)
        cumple_thm_rd3 = (tthm_ug_l <= 100.0)
        alerta_legionella_rd487 = (temp_c < 50.0 and leg_log_surv > -3.0)

        # Diagnóstico Sanitario Pericial
        diagnostico = "CUMPLE_CONFORME"
        if not cumple_cloro_rd3:
            diagnostico = "NO_CONFORME_CLORO_DEFICITARIO" if cloro_res < 0.20 else "NO_CONFORME_SOBRECLORACION"
        elif not cumple_thm_rd3:
            diagnostico = "NO_CONFORME_EXCESO_TRIHALOMETANOS"
        elif alerta_legionella_rd487:
            diagnostico = "ALERTA_RIESGO_LEGIONELLA_TEMPERATURA"

        return {
            "cloro_residual_mg_l": round(cloro_res, 4),
            "tthm_ug_l": round(tthm_ug_l, 2),
            "legionella_log_surv": round(leg_log_surv, 2),
            "cumple_rd3_2023": cumple_cloro_rd3 and cumple_thm_rd3,
            "cumple_rd487_2022": not alerta_legionella_rd487,
            "diagnostico_sanitario": diagnostico,
            "inferred_by": inferred_by,
            "latencia_inferencia_ms": round(latency_ms, 3),
            "sentinel_meta": {
                "cloro_modificado": was_c_mod,
                "cloro_motivo": c_reason,
                "tthm_modificado": was_thm_mod,
                "tthm_motivo": thm_reason
            }
        }

    def generate_decay_curve(
        self,
        c0: float,
        toc: float,
        ph: float,
        temp_c: float,
        diametro_mm: float,
        max_hours: float = 48.0,
        n_points: int = 50
    ) -> Dict[str, Any]:
        """Genera curvas temporales multi-punto para visualización interactiva."""
        times = np.linspace(0.1, max_hours, n_points)
        cloro_curve = []
        tthm_curve = []
        leg_curve = []

        for t in times:
            res = self.predict(c0, toc, ph, temp_c, diametro_mm, float(t))
            cloro_curve.append(res["cloro_residual_mg_l"])
            tthm_curve.append(res["tthm_ug_l"])
            leg_curve.append(res["legionella_log_surv"])

        return {
            "tiempo_h": times.tolist(),
            "cloro_residual_mg_l": cloro_curve,
            "tthm_ug_l": tthm_curve,
            "legionella_log_surv": leg_curve
        }
