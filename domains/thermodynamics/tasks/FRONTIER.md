# Thermodynamics Domain -- Frontier Questions
Domain agent: write here for thermodynamics-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-23 S509 (domain creation) | Active: 2

## Active

- **F-THERMO1**: Does the swarm obey a thermodynamic-like law?
  If information entropy of the lesson corpus increases monotonically over time (2nd law analog), then compaction is fighting entropy -- a Maxwell's demon spending tokens to maintain order. If entropy decreases, compaction creates order from noise. If neither trend holds, the thermodynamic analogy breaks down.
  **Test**: Measure Shannon entropy of lesson corpus at 5 time points (S100, S200, S300, S400, S500). Compute entropy per lesson and total corpus entropy. Plot trend. Separately measure entropy with and without compaction events.
  **Prediction**: Entropy per lesson increases monotonically (new lessons add disorder); total entropy increases but with compaction-induced dips (Maxwell's demon signature).
  **Falsification**: No consistent trend exists -- entropy fluctuates randomly with no monotonic component (R-squared < 0.3 on linear fit). The thermodynamic analogy adds no predictive power beyond "corpus grows."

- **F-THERMO2**: Is compaction a dissipative structure?
  Dissipative structures (Prigogine) maintain order by continuously dissipating energy. If compaction follows this pattern, the ratio of tokens processed (energy) to proxy-K reduction (order) should show a scaling relationship, and compaction should self-organize into a characteristic pattern rather than requiring manual tuning.
  **Test**: (a) Collect data from last 20 compact.py runs: tokens processed and proxy-K delta. (b) Fit power law: proxy-K-reduction = a * tokens^b. (c) Check if compaction cadence self-organizes (does the system signal when compaction is needed via proxy-K thresholds?).
  **Prediction**: Power law holds (R-squared > 0.6) with b < 1 (diminishing returns -- consistent with minimum entropy production). Compaction cadence is threshold-triggered, not manually scheduled.
  **Falsification**: No scaling relationship between processing cost and order produced (R-squared < 0.3). Compaction cadence is arbitrary with no self-organizing signal.

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
