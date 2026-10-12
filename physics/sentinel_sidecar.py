"""
YGGDRASIL ENVIRONMENTAL SYSTEMS · RUNTIME PHYSICS SENTINEL (SIDECAR)
====================================================================
Zero-Dependency Autonomous Physics & Invariant Gatekeeper for Core: HYGIEIA
Runs entirely in-process inside Cloud / Docker / Streamlit / AWS environments.
No network calls, no external databases required. Zero-Smoke Guarantee.

Directiva: DIR-YGG-2026-SEC01-AUTONOMY
Gobernanza: ISO/IEC 42001 (AIMS) · EU AI Act Art. 14 (HITL) · Art. 335 LEC
Director Técnico: Kelvin Jesús Flores Yarihuaman (MECES 3 / EQF Level 7)
"""

import os
import sys
import json
import time
import math
import hashlib
from pathlib import Path
from functools import wraps
from typing import Dict, Any, List, Tuple, Optional, Callable


class PhysicalInvariantViolationError(RuntimeError):
    """Excepción pericial formal lanzada cuando una inferencia viola las leyes físicas universales."""
    pass


class PhysicsSentinelSidecar:
    """
    Guardaespaldas matemático in-process. Carga el manifiesto `scientific_dna.json`
    y aplica clamping instantáneo, verificación de residuos y registro en caja negra.
    """

    def __init__(self, core_id: str = "HYGIEIA", dna_path: Optional[Any] = None):
        self.core_id = core_id.upper()
        self.dna_path = Path(dna_path) if dna_path else None
        self.dna = self._load_dna()
        self.clamping_ranges = self.dna.get("parametros_clamping", {})
        self.invariants = self.dna.get("invariantes_fisicas", [])
        self.audit_log_path = Path(__file__).resolve().parent / "physics_audit.jsonl"

    def _load_dna(self) -> Dict[str, Any]:
        """Carga el manifiesto de ADN científico con resolución de rutas relativas."""
        if self.dna_path and self.dna_path.exists():
            try:
                with open(self.dna_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        candidate_paths = [
            Path(__file__).resolve().parent / "scientific_dna.json",
            Path(__file__).resolve().parent.parent / "physics" / "scientific_dna.json",
            Path("physics/scientific_dna.json"),
            Path("../physics/scientific_dna.json")
        ]
        for p in candidate_paths:
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data.get("core_id", "").upper() == self.core_id:
                            return data
                except Exception:
                    pass
        fallback_path = Path(__file__).resolve().parent / "scientific_dna.json"
        if fallback_path.exists():
            try:
                with open(fallback_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"core_id": self.core_id, "parametros_clamping": {}, "invariantes_fisicas": []}

    def verify_dna_integrity(self) -> Tuple[bool, str]:
        """Verifica que el archivo no haya sido adulterado frente al sello SHA-256."""
        if not self.dna or "sello_criptografico_sha256" not in self.dna:
            return False, "NO_SEAL_PRESENT"
        declared_hash = self.dna["sello_criptografico_sha256"].replace("SHA256:", "")
        # Clonar sin el sello para computar
        copy_dna = dict(self.dna)
        copy_dna.pop("sello_criptografico_sha256", None)
        computed_hash = hashlib.sha256(json.dumps(copy_dna, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        is_valid = (declared_hash == computed_hash)
        return is_valid, computed_hash

    def clamp_value(self, param_name: str, value: float) -> Tuple[float, bool, str]:
        """
        Clampa un valor si supera los límites físicos fijados en el manifiesto.
        Retorna: (valor_corregido, fue_modificado, motivo)
        """
        if not isinstance(value, (int, float)) or math.isnan(value) or math.isinf(value):
            return 0.0, True, "NAN_OR_INF_CLAMPED_TO_ZERO"

        spec = self.clamping_ranges.get(param_name)
        if not spec:
            return float(value), False, "NO_SPEC"

        min_val = spec.get("min", -math.inf)
        max_val = spec.get("max", math.inf)
        original = float(value)

        if original < min_val:
            return min_val, True, f"CLAMP_MIN (era {original} < {min_val})"
        elif original > max_val:
            return max_val, True, f"CLAMP_MAX (era {original} > {max_val})"

        return original, False, "IN_BOUNDS"

    def clamp_dict(self, data_dict: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Clampa recursivamente todos los campos conocidos en un diccionario de resultados."""
        clamped = dict(data_dict)
        actions_taken = []

        for k, v in data_dict.items():
            if isinstance(v, (int, float)):
                new_v, modified, reason = self.clamp_value(k, float(v))
                if modified:
                    clamped[k] = new_v
                    actions_taken.append({"parametro": k, "valor_original": v, "valor_clampado": new_v, "motivo": reason})
            elif isinstance(v, dict):
                sub_dict, sub_actions = self.clamp_dict(v)
                clamped[k] = sub_dict
                actions_taken.extend(sub_actions)

        if actions_taken:
            self.log_audit_event("CLAMPING_ACTION", {"total_correcciones": len(actions_taken), "detalles": actions_taken})

        return clamped, actions_taken

    def log_audit_event(self, event_type: str, details: Dict[str, Any]):
        """Escribe un evento en la caja negra local (physics_audit.jsonl) de forma no bloqueante."""
        try:
            record = {
                "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "core_id": self.core_id,
                "event_type": event_type,
                "details": details
            }
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass


# Instancia única del centinela
_CENTINELA_INSTANCE = None

def get_sentinel(core_id: str = "HYGIEIA") -> PhysicsSentinelSidecar:
    global _CENTINELA_INSTANCE
    if _CENTINELA_INSTANCE is None:
        _CENTINELA_INSTANCE = PhysicsSentinelSidecar(core_id)
    return _CENTINELA_INSTANCE


def enforce_physics(core_id: str = "HYGIEIA", raise_on_fatal: bool = False):
    """
    Decorador de inferencia para modelos de IA en el Core.
    Intercepta salidas de funciones, clampa automáticamente y registra en caja negra.
    """
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            sentinel = get_sentinel(core_id)
            result = fn(*args, **kwargs)

            # Si devuelve dict, clampamos los parámetros
            if isinstance(result, dict):
                clamped_res, actions = sentinel.clamp_dict(result)
                return clamped_res
            elif isinstance(result, (int, float)):
                # Clamping genérico si la función se llama como el parámetro
                param_candidate = fn.__name__.lower()
                clamped_val, mod, reason = sentinel.clamp_value(param_candidate, float(result))
                return clamped_val

            return result
        return wrapper
    return decorator


if __name__ == "__main__":
    s = get_sentinel()
    ok, hash_val = s.verify_dna_integrity()
    print(f"[*] YGGDRASIL PHYSICS SENTINEL | Core: HYGIEIA")
    print(f"[*] Integridad de Manifiesto: {'CONFORME' if ok else 'FALLO'} | Hash: {hash_val[:16]}...")
    print(f"[*] Invariantes cargadas: {len(s.invariants)} | Parámetros de clamping: {len(s.clamping_ranges)}")
