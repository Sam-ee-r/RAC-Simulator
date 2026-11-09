"""Normal-agent state machine for Algorithm 1 (running-sum ratio consensus with recovery).

Timing convention (matches the paper's Phi_i[k] / delta_ij[k] indexing):

  * At the start of step k, self.lam == lambda_i[k] and self.gam == gamma_i[k].
  * Step k receives Phi_j[k-1] from every in-neighbor j. Those messages carry
    lambda_j[k], gamma_j[k], which the receiver stores as delta_ij[k], omega_ij[k].
  * Step k computes y_i[k], z_i[k], then lambda_i[k+1], and emits Phi_i[k].
"""
from __future__ import annotations

from dataclasses import dataclass, field

EPS_Z = 1e-12


@dataclass(frozen=True)
class Phi:
    """Information set Phi_i[k] broadcast to all out-neighbors (paper Eq. 6).

    A         : detected set A_i[k]
    own_next  : (delta_ii[k+1|k], omega_ii[k+1|k]) = (lambda_i[k+1], gamma_i[k+1])
    seen      : {j: (delta_ij[k|k], omega_ij[k|k])} for j in N_i^- U {i}
                (what i received at time k; detectors use it to cross-check two-hop values)
    """
    A: frozenset
    own_next: tuple
    seen: dict = field(default_factory=dict)


class Agent:
    def __init__(self, i: int, x0: float, in_nbrs, out_nbrs):
        self.i = i
        self.x0 = float(x0)
        self.in_nbrs = list(in_nbrs)
        self.out_nbrs = list(out_nbrs)

        self.A: set[int] = set()              # cumulative detected set A_i[k]
        self.M_in = set(self.in_nbrs)         # M_i^-[k]
        self.M_out = set(self.out_nbrs)       # M_i^+[k]

        self.y = self.x0                      # y_i[k]
        self.z = 1.0                          # z_i[k]
        self.lam = 0.0                        # lambda_i[k]
        self.gam = 0.0                        # gamma_i[k]
        self.delta = {j: 0.0 for j in self.in_nbrs + [i]}   # delta_ij[k]
        self.omega = {j: 0.0 for j in self.in_nbrs + [i]}   # omega_ij[k]
        self.k = 0

    # ---- step 0 -----------------------------------------------------------
    def init_message(self) -> Phi:
        d = len(self.M_out)
        self.lam = self.y / (1 + d)           # lambda_i[1]
        self.gam = self.z / (1 + d)           # gamma_i[1]
        self.k = 1
        seen = {j: (0.0, 0.0) for j in self.in_nbrs + [self.i]}
        return Phi(A=frozenset(), own_next=(self.lam, self.gam), seen=seen)

    # ---- steps k >= 1 -----------------------------------------------------
    def step(self, inbox: dict, newly_detected: set) -> Phi:
        """inbox: {j: Phi_j[k-1] or None}. newly_detected: IDs flagged by the detector at step k."""
        k = self.k
        i = self.i

        # silence is treated as detection (paper: A_i[1] = in-neighbors that sent nothing)
        silent = {j for j in self.in_nbrs if inbox.get(j) is None}
        self.A |= set(newly_detected) | silent

        M_in_new = set(self.in_nbrs) - self.A
        M_out_new = set(self.out_nbrs) - self.A
        newly_in = self.M_in - M_in_new       # Delta M_i^-[k]
        newly_out = self.M_out - M_out_new    # Delta M_i^+[k]

        delta_prev, omega_prev = dict(self.delta), dict(self.omega)
        for j in M_in_new:
            self.delta[j], self.omega[j] = inbox[j].own_next
        self.delta[i], self.omega[i] = self.lam, self.gam   # own running sum lambda_i[k]

        # Eq. 8: average over trusted in-neighbors and self
        trusted = M_in_new | {i}
        y = sum(self.delta[j] - delta_prev[j] for j in trusted)
        z = sum(self.omega[j] - omega_prev[j] for j in trusted)

        # Eq. 9 (Case 1): remove everything previously received from newly detected in-neighbors
        y -= sum(delta_prev[j] for j in newly_in)
        z -= sum(omega_prev[j] for j in newly_in)

        # Eq. 10 (Case 2): take back what was already sent to newly detected out-neighbors
        y += len(newly_out) * self.lam
        z += len(newly_out) * self.gam

        self.M_in, self.M_out = M_in_new, M_out_new
        self.y, self.z = y, z

        d = len(self.M_out)
        lam_next = self.lam + y / (1 + d)
        gam_next = self.gam + z / (1 + d)
        seen = {j: (self.delta[j], self.omega[j]) for j in trusted}
        msg = Phi(A=frozenset(self.A), own_next=(lam_next, gam_next), seen=seen)

        self.lam, self.gam = lam_next, gam_next
        self.k += 1
        return msg

    @property
    def estimate(self) -> float:
        """r_i[k] = y_i[k] / z_i[k]"""
        return self.y / self.z if abs(self.z) > EPS_Z else float("nan")
