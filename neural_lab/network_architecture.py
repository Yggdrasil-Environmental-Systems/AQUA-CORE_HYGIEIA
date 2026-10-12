"""
==============================================================================
AQUA-CORE: HYGIEIA | NEURAL LAB · DEEP NEURAL OPERATORS & DIGITAL TWIN
Module: neural_lab.network_architecture
Architectures:
  1. HygieiaPINNSurrogate (Open-Core): Physics-Informed Neural Network with
     Fourier Feature Embeddings, Arrhenius Kinetic PDE Residuals & RD 3/2023 Bounds.
  2. HygieiaPIGNNTwin (Enterprise): Physics-Informed Graph Neural Network
     (PI-GNN) Spatial Twin with Kirchhoff Flow Continuity & CTE DB-HS 4 Hydraulics.
Framework: Universal Core Platform Standard (UCPS-v1) · Yggdrasil-OS
Director Técnico: Kelvin Jesús Flores Yarihuaman (MECES 3 / EQF Level 7)
Estándares: RD 3/2023 · RD 487/2022 · PERTE Agua · EU AI Act (Reg. 2024/1689 Art. 14)
==============================================================================

Mathematical Formulation:
1. Kinetic PDE Transport & Decay (EPANET-MSX / Arrhenius Bulk-Wall formulation):
     ∂C/∂t + u · ∇C = - k_bulk(T) · C - (4·k_w(T)/D) · C
   PINN Loss enforces the differential constraint via Autograd:
     R_kinetic(x, t) = ∂C_pred/∂t + k_eff(T, D) · C_pred = 0

2. Disinfection Byproduct Synthesis (THMs Non-Linear Formation):
     TTHM(t) = α · (TOC)^β · (C_consumed)^γ · (T/20)^δ · (pH - 6)^ε <= 100 µg/L

3. Thermal Inactivation of Legionella pneumophila (Bigelow D_T-z Model):
     log10(N/N_0) = - t / D_T(T)  where D_T(T) = D_60 · 10^((60 - T)/z)

4. Spatial Graph Twin (Kirchhoff Continuity & Loop Energy Laws):
     ∑_{j ∈ N(i)} Q_{ij} = q_i   (Kirchhoff Mass Continuity at Junctions)
     ∑_{loop} h_{f, ij} = 0       (Kirchhoff Energy Balance across Closed Loops)
"""

from typing import Tuple, Dict, Any, Optional, List
import math
import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


if TORCH_AVAILABLE:

    class FourierFeatureEmbedding(nn.Module):
        """
        Mapeo de Fourier de alta frecuencia para mitigar el sesgo espectral (Spectral Bias)
        en redes PINN neuronales (Rahaman et al., 2019; Tancik et al., 2020).
        Permite capturar frentes de onda térmicos y decaimientos hiperbólicos de cloro.
        """

        def __init__(self, in_features: int, num_frequencies: int = 16, scale: float = 2.0):
            super().__init__()
            self.in_features = in_features
            self.num_frequencies = num_frequencies
            # Matriz de frecuencias aleatorias fija (inductiva gaussiana)
            B = torch.randn(in_features, num_frequencies) * scale
            self.register_buffer("B", B)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x: [Batch, in_features]
            proj = 2.0 * math.pi * torch.matmul(x, self.B)
            return torch.cat([x, torch.sin(proj), torch.cos(proj)], dim=-1)


    class ResidualDenseBlock(nn.Module):
        """
        Bloque denso residual con normalización de capas (LayerNorm) y activación GELU
        para estabilidad en backpropagation de segundo orden (Autograd PINN).
        """

        def __init__(self, dim: int, dropout: float = 0.05):
            super().__init__()
            self.fc1 = nn.Linear(dim, dim)
            self.ln1 = nn.LayerNorm(dim)
            self.fc2 = nn.Linear(dim, dim)
            self.ln2 = nn.LayerNorm(dim)
            self.act = nn.GELU()
            self.dropout = nn.Dropout(dropout)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            residual = x
            out = self.act(self.ln1(self.fc1(x)))
            out = self.dropout(out)
            out = self.ln2(self.fc2(out))
            return self.act(out + residual)


    # ============================================================================
    # 1. OPEN-CORE MODEL: HygieiaPINNSurrogate
    # ============================================================================

    class HygieiaPINNSurrogate(nn.Module):
        """
        Physics-Informed Neural Network (PINN) para Modelado Cinético Sub-milisegundo.
        Entrada X: [C0, TOC, pH, T, D_mm, t_h] (6 características físico-químicas)
        Salida Y: [Cloro_Residual_mg_L, TTHM_ug_L, Legionella_Log_Surv] (3 variables)
        Garantías Físicas:
          - No negatividad de cloro y THMs.
          - Monotonía de decaimiento (C(t) <= C0).
          - Cumplimiento de barrera legal RD 3/2023 & RD 487/2022.
        """

        def __init__(
            self,
            in_features: int = 6,
            out_features: int = 3,
            hidden_dim: int = 128,
            num_blocks: int = 3,
            num_frequencies: int = 16,
            dropout: float = 0.05
        ):
            super().__init__()
            self.fourier_embed = FourierFeatureEmbedding(in_features, num_frequencies=num_frequencies)
            embed_dim = in_features + 2 * num_frequencies

            self.in_proj = nn.Linear(embed_dim, hidden_dim)
            self.blocks = nn.ModuleList([
                ResidualDenseBlock(hidden_dim, dropout=dropout)
                for _ in range(num_blocks)
            ])

            # Cabezales especializados desacoplados
            self.head_cloro = nn.Sequential(
                nn.Linear(hidden_dim, 64),
                nn.GELU(),
                nn.Linear(64, 1)
            )
            self.head_tthm = nn.Sequential(
                nn.Linear(hidden_dim, 64),
                nn.GELU(),
                nn.Linear(64, 1),
                nn.Softplus()  # THMs siempre no negativos
            )
            self.head_legionella = nn.Sequential(
                nn.Linear(hidden_dim, 64),
                nn.GELU(),
                nn.Linear(64, 1)
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """
            Inferencia directa.
            x: Tensor [Batch, 6] -> [c0, toc, ph, temp_c, diametro_mm, tiempo_h]
            """
            c0 = x[:, 0:1]
            embedded = self.fourier_embed(x)
            h = F.gelu(self.in_proj(embedded))
            for block in self.blocks:
                h = block(h)

            # 1. Cloro: Sigmoid relativo normalizado a [0, c0] para garantizar C(t) <= C0 y C(t) >= 0
            decay_factor = torch.sigmoid(self.head_cloro(h))
            c_pred = c0 * decay_factor

            # 2. THMs: No negativos, acoplados al cloro consumido
            tthm_pred = self.head_tthm(h)

            # 3. Supervivencia Legionella: log10(N/N0) <= 0 (siempre reducción o mantenimiento)
            legionella_raw = self.head_legionella(h)
            leg_pred = -F.softplus(legionella_raw)  # strictly <= 0

            return torch.cat([c_pred, tthm_pred, leg_pred], dim=-1)

        def compute_pinn_loss(
            self,
            x: torch.Tensor,
            y_true: torch.Tensor,
            phys_params: torch.Tensor,
            lambda_pde: float = 0.20,
            lambda_legal: float = 0.15
        ) -> Dict[str, torch.Tensor]:
            """
            Función de pérdida multi-objetivo con regularización informada por la física
            y barreras penales del Real Decreto 3/2023 y Real Decreto 487/2022.
            
            x: [Batch, 6] -> requiere gradiente en la dimensión de tiempo (idx=5)
            y_true: [Batch, 3]
            phys_params: [Batch, 4] -> [k_bulk_h, k_wall_h, k_eff_h, d_t_h]
            """
            # Habilitar autograd en x_time para derivar analíticamente dC/dt
            x_var = x.clone().detach().requires_grad_(True)
            y_pred = self.forward(x_var)

            c_pred = y_pred[:, 0:1]
            tthm_pred = y_pred[:, 1:2]
            leg_pred = y_pred[:, 2:3]

            c_true = y_true[:, 0:1]
            tthm_true = y_true[:, 1:2]
            leg_true = y_true[:, 2:3]

            # 1. Pérdida Supervisada de Datos (MSE)
            loss_data_c = F.mse_loss(c_pred, c_true)
            loss_data_tthm = F.mse_loss(tthm_pred, tthm_true)
            loss_data_leg = F.mse_loss(leg_pred, leg_true)
            loss_data = loss_data_c + (loss_data_tthm * 0.01) + (loss_data_leg * 0.05)

            # 2. Autograd PINN: Residuo de la Ecuación Cinética de Arrhenius (dC/dt + k_eff*C = 0)
            grad_c = torch.autograd.grad(
                outputs=c_pred.sum(),
                inputs=x_var,
                create_graph=True,
                retain_graph=True
            )[0]
            # La derivada dC/dt está en la columna 5 (tiempo_h)
            dc_dt = grad_c[:, 5:6]
            k_eff = phys_params[:, 2:3]
            pde_residual = dc_dt + (k_eff * c_pred)
            loss_pde = F.mse_loss(pde_residual, torch.zeros_like(pde_residual))

            # Monotonía: la concentración no puede auto-generarse (dc/dt <= 0)
            loss_monotonicity = torch.mean(F.relu(dc_dt) ** 2)

            # 3. Barrera Regulatoria Legal (ASTRAEA Inductive Biases):
            # RD 3/2023: Cloro residual libre debe estar en [0.20, 1.00] mg/L
            violation_c_min = F.relu(0.20 - c_pred)
            violation_c_max = F.relu(c_pred - 1.00)
            # RD 3/2023: TTHM no debe exceder 100 ug/L
            violation_tthm = F.relu(tthm_pred - 100.0)
            # RD 487/2022: Si T >= 60°C y t >= 0.1h, Legionella debe estar abatida (log <= -4)
            temp_c = x_var[:, 3:4]
            tiempo_h = x_var[:, 5:6]
            mask_thermal = (temp_c >= 60.0) & (tiempo_h >= 0.1)
            violation_legionella = F.relu(leg_pred + 4.0) * mask_thermal.float()

            loss_legal = torch.mean(violation_c_min**2 + violation_c_max**2) + \
                         0.01 * torch.mean(violation_tthm**2) + \
                         torch.mean(violation_legionella**2)

            # Pérdida total acoplada
            loss_total = loss_data + (lambda_pde * (loss_pde + loss_monotonicity)) + (lambda_legal * loss_legal)

            return {
                "loss_total": loss_total,
                "loss_data": loss_data,
                "loss_pde": loss_pde,
                "loss_monotonicity": loss_monotonicity,
                "loss_legal": loss_legal,
                "rmse_cloro": torch.sqrt(loss_data_c),
                "rmse_tthm": torch.sqrt(loss_data_tthm)
            }


    # ============================================================================
    # 2. ENTERPRISE MODEL: HygieiaPIGNNTwin (Graph Spatial Operator)
    # ============================================================================

    class EdgePhysicsMessagePassing(nn.Module):
        """
        Capa de paso de mensajes informada por la física en aristas de tubería.
        Modela el caudal direccional Q_ij y la pérdida de carga por fricción Δh_ij
        según la formulación inducida de Hazen-Williams / Darcy-Weisbach:
           Δh_ij = r_ij * sign(Q_ij) * |Q_ij|^1.852
        """

        def __init__(self, node_dim: int, edge_dim: int, hidden_dim: int = 64):
            super().__init__()
            self.msg_net = nn.Sequential(
                nn.Linear(2 * node_dim + edge_dim, hidden_dim),
                nn.GELU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.GELU()
            )
            # Predice caudal Q_ij y pérdida de carga Δh_ij en el tramo
            self.head_flow = nn.Linear(hidden_dim, 1)
            self.head_headloss = nn.Linear(hidden_dim, 1)

        def forward(self, v_src: torch.Tensor, v_dst: torch.Tensor, e_attr: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            cat_feat = torch.cat([v_src, v_dst, e_attr], dim=-1)
            h = self.msg_net(cat_feat)
            q_ij = self.head_flow(h)
            dh_ij = self.head_headloss(h)
            return h, q_ij, dh_ij


    class HygieiaPIGNNTwin(nn.Module):
        """
        Physics-Informed Graph Neural Network (PI-GNN) Digital Twin para Sectores Hidráulicos (DMA-04).
        Modela la red completa de distribución interior y hospitalaria (10 nudos de control).
        
        Variables Nodales:
          Entrada: [Cota, Volumen, Cloro_Base, Demanda_Base, Temp, pH, Hora_Dia] (7 características)
          Salida: [Presion_mca, Edad_Agua_h, Cloro_Residual_mg_L, Riesgo_Legionella] (4 variables)
          
        Leyes Físicas Invariantes:
          1. Conservación de Masa de Kirchhoff (Continuidad en nudos): ∑ Q_in - ∑ Q_out - q_nodo = 0
          2. Ley de Circuitos Cerrados de Kirchhoff (Balance de pérdidas de carga en anillos): ∑ Δh = 0
          3. Límites CTE DB-HS 4: Presión de servicio entre 15 mca y 50 mca.
        """

        def __init__(
            self,
            num_nodes: int = 10,
            node_in_dim: int = 7,
            edge_in_dim: int = 3,
            hidden_dim: int = 64,
            num_layers: int = 2,
            out_dim: int = 4
        ):
            super().__init__()
            self.num_nodes = num_nodes
            self.node_embed = nn.Linear(node_in_dim, hidden_dim)
            self.edge_embed = nn.Linear(edge_in_dim, hidden_dim // 2)

            self.mp_layers = nn.ModuleList([
                EdgePhysicsMessagePassing(hidden_dim, hidden_dim // 2, hidden_dim=hidden_dim)
                for _ in range(num_layers)
            ])
            self.gru_update = nn.GRUCell(hidden_dim, hidden_dim)

            # Cabezales nodales
            self.head_pressure = nn.Sequential(
                nn.Linear(hidden_dim, 32),
                nn.GELU(),
                nn.Linear(32, 1)
            )
            self.head_water_age = nn.Sequential(
                nn.Linear(hidden_dim, 32),
                nn.GELU(),
                nn.Linear(32, 1),
                nn.Softplus()  # La edad del agua es estrictamente no negativa
            )
            self.head_chlorine = nn.Sequential(
                nn.Linear(hidden_dim, 32),
                nn.GELU(),
                nn.Linear(32, 1),
                nn.Sigmoid()   # Normalizado entre [0, Cloro_Base_Max]
            )
            self.head_legionella_risk = nn.Sequential(
                nn.Linear(hidden_dim, 32),
                nn.GELU(),
                nn.Linear(32, 1),
                nn.Sigmoid()   # Índice de riesgo en [0, 1]
            )

        def forward(
            self,
            node_feats: torch.Tensor,
            edge_indices: torch.Tensor,
            edge_attrs: torch.Tensor
        ) -> Dict[str, torch.Tensor]:
            """
            Inferencia sobre el grafo hidrosanitario.
            node_feats: [N_nodes, node_in_dim]
            edge_indices: [2, N_edges] (src, dst)
            edge_attrs: [N_edges, edge_in_dim]
            """
            n_nodes = node_feats.shape[0]
            h_nodes = F.gelu(self.node_embed(node_feats))
            e_emb = F.gelu(self.edge_embed(edge_attrs))

            src_idx, dst_idx = edge_indices[0], edge_indices[1]
            q_edges = None
            dh_edges = None

            for mp in self.mp_layers:
                v_src = h_nodes[src_idx]
                v_dst = h_nodes[dst_idx]
                msg, q_edges, dh_edges = mp(v_src, v_dst, e_emb)

                # Agregación espacial de mensajes en nodos de destino
                aggr_msg = torch.zeros_like(h_nodes)
                aggr_msg.index_add_(0, dst_idx, msg)

                # Actualización de estado latente mediante GRU
                h_nodes = self.gru_update(aggr_msg, h_nodes)

            # Inferencia de cabezales nodales
            # Presión base inducida por cota (Cota_0 - Cota_i) + modulación de red
            cota_msnm = node_feats[:, 0:1]
            cota_ref = cota_msnm.max()
            presion_estatica = (cota_ref - cota_msnm) * 1.0  # 1 m de columna de agua por metro de cota
            delta_p = self.head_pressure(h_nodes)
            presion = 35.0 + presion_estatica + delta_p  # Centrado en consigna hospitalaria 3.5 bar (35 mca)

            water_age = self.head_water_age(h_nodes)
            cloro_base = node_feats[:, 2:3]
            cloro = cloro_base * self.head_chlorine(h_nodes)
            risk = self.head_legionella_risk(h_nodes)

            node_predictions = torch.cat([presion, water_age, cloro, risk], dim=-1)

            return {
                "node_predictions": node_predictions,
                "presion_mca": presion,
                "edad_agua_h": water_age,
                "cloro_mg_l": cloro,
                "riesgo_legionella": risk,
                "edge_flows": q_edges,
                "edge_headlosses": dh_edges
            }

        def compute_pignn_loss(
            self,
            pred: Dict[str, torch.Tensor],
            target_nodes: torch.Tensor,
            edge_indices: torch.Tensor,
            demands: torch.Tensor,
            loops: Optional[List[List[int]]] = None,
            lambda_continuity: float = 0.25,
            lambda_legal: float = 0.20
        ) -> Dict[str, torch.Tensor]:
            """
            Pérdida acoplada para el Gemelo Digital Enterprise:
            - Error cuadrático en estados nodales (presión, edad agua, cloro).
            - Conservación de masa de Kirchhoff: balance de caudal en cada nudo = demanda.
            - Conservación de energía de Kirchhoff: suma de pérdidas de carga en circuito cerrado = 0.
            - Barreras legales CTE DB-HS 4 y RD 3/2023.
            """
            node_pred = pred["node_predictions"]
            q_edges = pred["edge_flows"]
            dh_edges = pred["edge_headlosses"]

            # 1. Pérdida supervisada de datos
            loss_data = F.mse_loss(node_pred, target_nodes)

            # 2. Conservación de Masa de Kirchhoff en nudos:
            # ∑ Q_in - ∑ Q_out = Demanda_i
            src_idx, dst_idx = edge_indices[0], edge_indices[1]
            n_nodes = node_pred.shape[0]
            net_flow = torch.zeros(n_nodes, 1, device=node_pred.device)

            if q_edges is not None:
                net_flow.index_add_(0, dst_idx, q_edges)
                net_flow.index_add_(0, src_idx, -q_edges)

            loss_continuity = F.mse_loss(net_flow, demands)

            # 3. Conservación de Energía de Kirchhoff en anillos cerrados (loops)
            loss_energy = torch.tensor(0.0, device=node_pred.device)
            if loops and dh_edges is not None:
                loop_losses = []
                for loop_edges in loops:
                    sum_dh = dh_edges[loop_edges].sum()
                    loop_losses.append(sum_dh ** 2)
                if loop_losses:
                    loss_energy = torch.stack(loop_losses).mean()

            # 4. Cumplimiento Regulatorio Legal:
            # CTE DB-HS 4: Presión en grifo terminal debe estar en [15, 50] mca
            p_pred = pred["presion_mca"]
            violation_p_min = F.relu(15.0 - p_pred)
            violation_p_max = F.relu(p_pred - 50.0)
            # RD 3/2023: Cloro en red debe estar en [0.20, 1.00] mg/L
            c_pred = pred["cloro_mg_l"]
            violation_c_min = F.relu(0.20 - c_pred)
            violation_c_max = F.relu(c_pred - 1.00)

            loss_legal = torch.mean(violation_p_min**2 + violation_p_max**2) + \
                         torch.mean(violation_c_min**2 + violation_c_max**2)

            loss_total = loss_data + (lambda_continuity * loss_continuity) + (0.10 * loss_energy) + (lambda_legal * loss_legal)

            return {
                "loss_total": loss_total,
                "loss_data": loss_data,
                "loss_continuity": loss_continuity,
                "loss_energy": loss_energy,
                "loss_legal": loss_legal,
                "rmse_presion": torch.sqrt(F.mse_loss(p_pred, target_nodes[:, 0:1])),
                "rmse_cloro": torch.sqrt(F.mse_loss(c_pred, target_nodes[:, 2:3]))
            }

else:
    # Dummy fallback if PyTorch is not available
    class HygieiaPINNSurrogate:
        pass
    class HygieiaPIGNNTwin:
        pass
