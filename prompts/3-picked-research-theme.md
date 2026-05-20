# Example Output: 3 Picked Research Directions

This is the expected shape of the Direction Narrowing MVP output.

The example assumes the user has:

- 1 consumer GPU
- PyTorch experience
- interest in small transformers
- a goal of producing a realistic first research project
- limited time for experiments

The citations below are example paper-note IDs. In a real run, each ID must point to a paper note with citation, claim, tested setup, limitations, and relevance.

## Constraint Profile

```json
{
  "compute": "1 consumer GPU, limited memory",
  "time_budget": "8-12 hours this week, pilots should finish in 1-3 hours",
  "skills": ["PyTorch", "basic training loops", "can modify configs"],
  "interests": ["transformer efficiency", "training stability", "small models"],
  "goal_type": "first publishable or portfolio-grade research result",
  "existing_codebase": "small transformer training repo",
  "baseline_state": "needs one documented AdamW baseline",
  "recommended_regime": "small controlled ablations on 20M-200M parameter transformers",
  "excluded_regimes": [
    "large MoE training",
    "long-context systems work",
    "RL-heavy reasoning experiments",
    "multi-node training"
  ]
}
```

## Direction 1: Optimizer Behavior For Small Transformers

### Fit

This fits a single-GPU researcher because optimizer comparisons can be run on small models, have clear metrics, and do not require a new architecture stack.

### Why It Matters

Many optimizer claims are made at scales or settings that students cannot reproduce. A careful small-scale wall-clock-controlled comparison can still be useful if it explains where the claim does or does not transfer.

### First Papers

- P1: Muon-style optimizer paper note — tested non-Adam update behavior in one regime.
- P2: LLM optimizer comparison paper note — compared optimizer behavior for larger language models.
- P3: Small-transformer AdamW baseline paper note — documents stable small-model training baselines.

### Candidate Grounded Gap

No cited paper in the current notes tests Muon-style updates on sub-100M transformers under equal wall-clock budget against AdamW.

### Provenance

- Evidence from P1: Muon-style updates were tested, but not on the user's small language-model regime.
- Evidence from P2: LLM optimizer behavior was studied, but the note says the evaluated models were larger than the user's feasible range.
- Evidence from P3: AdamW small-transformer baselines exist, but the note does not include Muon-style comparisons.

### Missing Axis

Small language models below 100M parameters under fixed wall-clock budget.

### Measurable Question

Does a Muon-style optimizer improve validation loss or time-to-loss-threshold over AdamW for a 50M transformer under equal wall-clock budget, same data order, same token budget, and same seeds?

### Minimum Pilot

Run AdamW and Muon-style training for 2 seeds each on the same 50M model, same dataset slice, same token budget, and same wall-clock cap.

### Kill Condition

Kill or downgrade the direction if Muon-style updates do not improve validation loss, stability, or time-to-threshold in the 2-seed pilot.

### Score

| Axis | Score | Reason |
| --- | ---: | --- |
| Novelty | 4 | The exact small-model wall-clock regime appears missing from current notes. |
| Feasibility | 5 | Requires optimizer changes and controlled runs, not new infrastructure. |
| Compute fit | 5 | Designed for one GPU and short pilots. |
| Clarity | 5 | Metric and baseline are straightforward. |
| Scientific value | 4 | Useful if it clarifies whether optimizer claims transfer downscale. |
| Risk | 3 | Optimizer results can be seed-sensitive. |
| Dependency count | 4 | Needs baseline repo plus one optimizer implementation. |
| Iteration speed | 4 | Pilots can be short. |
| Reproducibility | 4 | Same seeds, same data order, same wall-clock cap are easy to report. |
| Total | 38/45 | Best first bet. |

## Direction 2: Normalization And Stability In Small Transformers

### Fit

This fits the user because normalization changes are local code edits, can be tested with short training runs, and often expose stability differences before full-scale training.

### Why It Matters

Training stability is a real bottleneck for small experimental repos. A result that identifies which normalization variant improves stability under constrained batch size could be educational and practically useful.

### First Papers

- P4: Transformer normalization comparison paper note — compares pre-norm, post-norm, or related variants.
- P5: Small-batch training stability paper note — discusses instability when batch size or memory is constrained.
- P6: Efficient transformer training paper note — includes training-stability claims but limited small-model coverage.

### Candidate Grounded Gap

The current notes do not show a controlled comparison of normalization variants for small transformers when batch size is constrained by single-GPU memory.

### Provenance

- Evidence from P4: Normalization variants were compared, but not under the user's single-GPU batch constraint.
- Evidence from P5: Batch-constrained instability was discussed, but not tied to the same normalization variants.
- Evidence from P6: Efficient training claims mention stability, but the note does not include a small controlled normalization ablation.

### Missing Axis

Normalization choice under constrained batch size for small transformers.

### Measurable Question

Does changing normalization placement or variant reduce loss spikes and improve validation loss for a 50M transformer trained with a fixed small batch size?

### Minimum Pilot

Run baseline normalization and one alternative normalization variant for 2 seeds each, logging validation loss, gradient norm, loss spikes, and failed-step count.

### Kill Condition

Kill or downgrade the direction if the alternative normalization does not reduce instability metrics or improve validation loss compared with baseline.

### Score

| Axis | Score | Reason |
| --- | ---: | --- |
| Novelty | 3 | Normalization is studied, but the constrained small-regime angle may still be useful. |
| Feasibility | 4 | Local model edits are manageable. |
| Compute fit | 5 | Short pilots fit one GPU. |
| Clarity | 4 | Stability metrics must be defined carefully. |
| Scientific value | 3 | Useful, but may feel incremental unless the evidence is clean. |
| Risk | 3 | Signal may depend on training recipe. |
| Dependency count | 4 | Needs model-code edits and logging. |
| Iteration speed | 4 | Fast feedback from early training. |
| Reproducibility | 4 | Easy to report if configs are frozen. |
| Total | 34/45 | Strong backup direction. |

## Direction 3: Attention Efficiency Under Short Training Budgets

### Fit

This fits if the user wants architecture work, but it is more infrastructure-heavy than optimizer or normalization studies.

### Why It Matters

Attention efficiency is popular, but many ideas are tested in settings that are too large or too systems-heavy for students. A careful small-regime test can still be valuable if the metric is compute-adjusted.

### First Papers

- P7: Efficient attention paper note — claims memory or speed improvements.
- P8: Transformer architecture ablation paper note — compares architectural changes under controlled training.
- P9: Inference-efficiency benchmark paper note — defines throughput, memory, or latency metrics.

### Candidate Grounded Gap

The current notes do not show whether a lightweight attention modification improves validation loss per unit wall-clock time for small transformers under short training budgets.

### Provenance

- Evidence from P7: The efficient attention method was tested for memory or speed, but the note does not show small-transformer training-quality tradeoffs.
- Evidence from P8: Architecture ablations exist, but not for this attention method under short wall-clock budgets.
- Evidence from P9: Efficiency metrics exist, but the note does not connect them to small-model training outcomes.

### Missing Axis

Training-quality tradeoff for attention efficiency under short, student-scale budgets.

### Measurable Question

Does a lightweight attention modification improve validation loss per wall-clock hour without increasing memory use for a 50M transformer?

### Minimum Pilot

Implement the smallest attention change, run baseline and modified attention for 1-2 seeds, and compare validation loss, tokens per second, peak memory, and time-to-threshold.

### Kill Condition

Kill or downgrade the direction if the modification slows training, increases memory, or fails to match baseline validation loss in the pilot.

### Score

| Axis | Score | Reason |
| --- | ---: | --- |
| Novelty | 3 | Many attention ideas exist; the small-budget framing may be the only novelty. |
| Feasibility | 3 | Architecture changes can create bugs and confounds. |
| Compute fit | 4 | The pilot can be small, but debugging may be costly. |
| Clarity | 4 | Metrics are clear if speed and memory are logged. |
| Scientific value | 3 | Useful if the tradeoff is clean. |
| Risk | 2 | Higher implementation and confounding risk. |
| Dependency count | 2 | Needs model edits, profiling, and careful baselines. |
| Iteration speed | 3 | Debugging can slow the loop. |
| Reproducibility | 3 | Reproducible if implementation is simple and documented. |
| Total | 27/45 | Interesting, but not the best first bet. |

## Recommendation

Start with Direction 1: Optimizer Behavior For Small Transformers.

Why:

- It best fits a one-GPU setup.
- It has the clearest baseline: AdamW.
- It produces a measurable question quickly.
- It requires less infrastructure than architecture or attention changes.
- It can be killed fast if the signal is weak.

First next step:

Read these 3 papers or paper notes and fill structured notes before defining the pilot:

- P1: Muon-style optimizer paper note
- P2: LLM optimizer comparison paper note
- P3: Small-transformer AdamW baseline paper note

Then define the first exact question:

> Does a Muon-style optimizer improve validation loss or time-to-loss-threshold over AdamW for a 50M transformer under equal wall-clock budget, same data order, same token budget, and same seeds?

Do not run the pilot until the baseline and paper notes are filled.
