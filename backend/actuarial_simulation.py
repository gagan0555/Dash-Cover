"""
Dash-Cover — Actuarial Simulation Engine
=========================================
Monte Carlo simulation for parametric income insurance sustainability analysis.

Model Parameters (from README Section 6):
  - Base Premium:        ₹25/week
  - Max Daily Payout:    ₹600 (Standard tier)
  - Zone Risk Multiplier: 0.8x – 1.5x
  - Coverage Tier:       Standard (1.4x multiplier on premium)
  - Poisson λ:           0.05 red-alert events per zone per week

Outputs:
  1. Total Premiums vs Total Payouts
  2. Loss Ratio (target < 0.70)
  3. Probability of Ruin
  4. Sensitivity table across Zone Risk Multipliers
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Tuple

# ─── Simulation Configuration ───────────────────────────────────────────────

@dataclass
class SimulationConfig:
    """All tuneable knobs for the Monte Carlo engine."""
    n_workers: int = 5_000
    n_weeks: int = 52
    n_simulations: int = 1_000          # number of Monte Carlo paths

    # Pricing parameters (README §6)
    base_premium_per_week: float = 25.0  # ₹25/week floor
    coverage_tier_multiplier: float = 1.4  # Standard tier
    max_daily_payout: float = 600.0      # ₹600/disrupted day (Standard)

    # Disruption parameters
    poisson_lambda: float = 0.05         # red-alert events per zone per week
    avg_disrupted_hours: float = 6.0     # average hours lost per event
    avg_hourly_earning: float = 100.0    # ₹100/hr (~₹800/day ÷ 8hr)

    # Zone risk multiplier (default; swept in sensitivity analysis)
    zone_risk_multiplier: float = 1.0

    # Ruin analysis
    initial_pool_capital: float = 0.0    # start from premiums only (no reserve)

    # Reproducibility
    seed: int = 42


# ─── Core Simulation Engine ─────────────────────────────────────────────────

@dataclass
class SimulationResult:
    """Container for a single Monte Carlo run's outputs."""
    total_premiums: float = 0.0
    total_payouts: float = 0.0
    loss_ratio: float = 0.0
    peak_deficit: float = 0.0
    ruin_occurred: bool = False          # pool balance went ≤ 0 at any week
    weekly_pool_balance: np.ndarray = field(default_factory=lambda: np.array([]))


def run_single_simulation(cfg: SimulationConfig, rng: np.random.Generator) -> SimulationResult:
    """
    Simulate one full 52-week path for the entire worker pool.

    For each week:
      1. Collect premiums from all active workers.
      2. Sample the number of red-alert events via Poisson(λ).
      3. For each event, determine how many workers are affected
         (zone overlap modelled as ~15-25% of the pool).
      4. Calculate payouts: min(hourly_earning × disrupted_hours, daily_cap).
      5. Track cumulative pool balance for ruin detection.
    """
    adjusted_premium = (
        cfg.base_premium_per_week
        * cfg.zone_risk_multiplier
        * cfg.coverage_tier_multiplier
    )

    total_premiums = 0.0
    total_payouts = 0.0
    pool_balance = cfg.initial_pool_capital
    weekly_balances = np.zeros(cfg.n_weeks)
    ruin_occurred = False
    peak_deficit = 0.0

    for week in range(cfg.n_weeks):
        # ── Step 1: Collect premiums ──
        week_premiums = cfg.n_workers * adjusted_premium
        total_premiums += week_premiums
        pool_balance += week_premiums

        # ── Step 2: Sample red-alert events this week ──
        n_events = rng.poisson(cfg.poisson_lambda)

        week_payouts = 0.0
        for _ in range(n_events):
            # ── Step 3: Determine affected workers ──
            # Zone overlap: 15-25% of pool affected per event
            affected_fraction = rng.uniform(0.15, 0.25)
            n_affected = int(cfg.n_workers * affected_fraction)

            # ── Step 4: Calculate payouts per affected worker ──
            # Disrupted hours vary per worker (normal around avg, clipped to [2, 10])
            disrupted_hours = rng.normal(cfg.avg_disrupted_hours, 1.5, size=n_affected)
            disrupted_hours = np.clip(disrupted_hours, 2.0, 10.0)

            # Raw payout = hourly_earning × disrupted_hours
            raw_payouts = cfg.avg_hourly_earning * disrupted_hours

            # Cap at max daily payout
            capped_payouts = np.minimum(raw_payouts, cfg.max_daily_payout)

            week_payouts += capped_payouts.sum()

        total_payouts += week_payouts
        pool_balance -= week_payouts

        # ── Step 5: Track ruin ──
        weekly_balances[week] = pool_balance
        if pool_balance <= 0:
            ruin_occurred = True
            peak_deficit = min(peak_deficit, pool_balance)

    loss_ratio = total_payouts / total_premiums if total_premiums > 0 else float('inf')

    return SimulationResult(
        total_premiums=total_premiums,
        total_payouts=total_payouts,
        loss_ratio=loss_ratio,
        peak_deficit=peak_deficit,
        ruin_occurred=ruin_occurred,
        weekly_pool_balance=weekly_balances,
    )


def run_monte_carlo(cfg: SimulationConfig) -> List[SimulationResult]:
    """Run N Monte Carlo simulations and return all results."""
    rng = np.random.default_rng(cfg.seed)
    results = []
    for _ in range(cfg.n_simulations):
        result = run_single_simulation(cfg, rng)
        results.append(result)
    return results


# ─── Analysis Functions ─────────────────────────────────────────────────────

def compute_aggregate_metrics(results: List[SimulationResult]) -> dict:
    """Compute summary statistics across all Monte Carlo paths."""
    loss_ratios = np.array([r.loss_ratio for r in results])
    ruin_flags = np.array([r.ruin_occurred for r in results])
    total_premiums = np.array([r.total_premiums for r in results])
    total_payouts = np.array([r.total_payouts for r in results])

    return {
        "mean_total_premiums": np.mean(total_premiums),
        "mean_total_payouts": np.mean(total_payouts),
        "mean_loss_ratio": np.mean(loss_ratios),
        "median_loss_ratio": np.median(loss_ratios),
        "std_loss_ratio": np.std(loss_ratios),
        "p5_loss_ratio": np.percentile(loss_ratios, 5),
        "p95_loss_ratio": np.percentile(loss_ratios, 95),
        "max_loss_ratio": np.max(loss_ratios),
        "probability_of_ruin": np.mean(ruin_flags),
        "n_simulations": len(results),
    }


def sensitivity_analysis(
    multiplier_range: np.ndarray = None,
    base_cfg: SimulationConfig = None,
) -> pd.DataFrame:
    """
    Sweep the Zone Risk Multiplier from 1.0 to 1.5 and measure
    how the Loss Ratio and Probability of Ruin respond.

    Higher multiplier → higher premiums → lower loss ratio (more sustainable).
    """
    if multiplier_range is None:
        multiplier_range = np.arange(1.0, 1.55, 0.05)
    if base_cfg is None:
        base_cfg = SimulationConfig()

    rows = []
    for mult in multiplier_range:
        cfg = SimulationConfig(
            n_workers=base_cfg.n_workers,
            n_weeks=base_cfg.n_weeks,
            n_simulations=base_cfg.n_simulations,
            base_premium_per_week=base_cfg.base_premium_per_week,
            coverage_tier_multiplier=base_cfg.coverage_tier_multiplier,
            max_daily_payout=base_cfg.max_daily_payout,
            poisson_lambda=base_cfg.poisson_lambda,
            avg_disrupted_hours=base_cfg.avg_disrupted_hours,
            avg_hourly_earning=base_cfg.avg_hourly_earning,
            zone_risk_multiplier=round(mult, 2),
            initial_pool_capital=base_cfg.initial_pool_capital,
            seed=base_cfg.seed,
        )
        results = run_monte_carlo(cfg)
        metrics = compute_aggregate_metrics(results)
        rows.append({
            "Zone Risk Multiplier": round(mult, 2),
            "Adj. Weekly Premium (Rs.)": round(
                cfg.base_premium_per_week * mult * cfg.coverage_tier_multiplier, 2
            ),
            "Mean Loss Ratio": round(metrics["mean_loss_ratio"], 4),
            "Median Loss Ratio": round(metrics["median_loss_ratio"], 4),
            "P95 Loss Ratio": round(metrics["p95_loss_ratio"], 4),
            "Prob. of Ruin (%)": round(metrics["probability_of_ruin"] * 100, 2),
            "Mean Premiums (Rs.)": round(metrics["mean_total_premiums"], 0),
            "Mean Payouts (Rs.)": round(metrics["mean_total_payouts"], 0),
        })

    return pd.DataFrame(rows)


# ─── Pretty Printing ────────────────────────────────────────────────────────

def print_banner(title: str):
    width = 72
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_metrics(metrics: dict, cfg: SimulationConfig):
    print_banner("DASH-COVER ACTUARIAL SIMULATION — AGGREGATE RESULTS")

    print(f"""
  Configuration
  ---------------------------------------------
  Workers:              {cfg.n_workers:,}
  Horizon:              {cfg.n_weeks} weeks
  Monte Carlo Paths:    {cfg.n_simulations:,}
  Base Premium:         Rs.{cfg.base_premium_per_week}/week
  Zone Risk Multiplier: {cfg.zone_risk_multiplier}x
  Coverage Tier:        Standard ({cfg.coverage_tier_multiplier}x)
  Poisson lambda:       {cfg.poisson_lambda}
  Max Daily Payout:     Rs.{cfg.max_daily_payout}
    """)

    sustainable = metrics["mean_loss_ratio"] < 0.70
    status = "[SUSTAINABLE]" if sustainable else "[!! UNSUSTAINABLE]"

    print(f"""  Financial Summary
  ---------------------------------------------
  Mean Total Premiums:  Rs.{metrics['mean_total_premiums']:,.0f}
  Mean Total Payouts:   Rs.{metrics['mean_total_payouts']:,.0f}
  Net Surplus (Mean):   Rs.{metrics['mean_total_premiums'] - metrics['mean_total_payouts']:,.0f}

  Loss Ratio Analysis
  ---------------------------------------------
  Mean Loss Ratio:      {metrics['mean_loss_ratio']:.4f}  {status}
  Median Loss Ratio:    {metrics['median_loss_ratio']:.4f}
  Std Dev:              {metrics['std_loss_ratio']:.4f}
  5th Percentile:       {metrics['p5_loss_ratio']:.4f}
  95th Percentile:      {metrics['p95_loss_ratio']:.4f}
  Worst Case:           {metrics['max_loss_ratio']:.4f}

  Solvency
  ---------------------------------------------
  Probability of Ruin:  {metrics['probability_of_ruin'] * 100:.2f}%
    """)


def print_sensitivity_table(df: pd.DataFrame):
    print_banner("SENSITIVITY ANALYSIS -- Zone Risk Multiplier Sweep (1.0x -> 1.5x)")
    print()
    print(df.to_string(index=False))
    print()

    # Find the break-even multiplier (first row where loss ratio < 0.70)
    sustainable_rows = df[df["Mean Loss Ratio"] < 0.70]
    if not sustainable_rows.empty:
        breakeven = sustainable_rows.iloc[0]["Zone Risk Multiplier"]
        print(f"  -> Minimum sustainable multiplier (Loss Ratio < 0.70): {breakeven}x")
    else:
        print("  -> [!!] No tested multiplier achieves Loss Ratio < 0.70")

    print()


# ─── Entry Point ─────────────────────────────────────────────────────────────

def main():
    print_banner("INITIALIZING DASH-COVER ACTUARIAL SIMULATION ENGINE")
    print("  Monte Carlo · Poisson Triggers · Ruin Theory · Sensitivity Sweep")
    print()

    # ── Phase 1: Baseline simulation (multiplier = 1.0) ──
    cfg = SimulationConfig()
    print("  > Running baseline simulation (1,000 paths x 5,000 workers x 52 weeks)...")
    results = run_monte_carlo(cfg)
    metrics = compute_aggregate_metrics(results)
    print_metrics(metrics, cfg)

    # -- Phase 2: Sensitivity analysis --
    print("  > Running sensitivity sweep across Zone Risk Multipliers...")
    sensitivity_df = sensitivity_analysis(base_cfg=cfg)
    print_sensitivity_table(sensitivity_df)

    # ── Phase 3: Export results to CSV ──
    sensitivity_df.to_csv("backend/sensitivity_analysis.csv", index=False)
    print("  > Results exported to backend/sensitivity_analysis.csv")

    print_banner("SIMULATION COMPLETE")

    return metrics, sensitivity_df


if __name__ == "__main__":
    main()
