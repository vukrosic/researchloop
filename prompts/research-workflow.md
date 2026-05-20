# AI Research Direction Narrowing Workflow

Goal:

Help a student or independent researcher choose a realistic, grounded AI research direction they can actually execute.

This is not the full autonomous research system yet.

The first product wedge is:

> I do not know what realistic research direction to pursue.

The system should take the user from vague interest to:

- 3 feasible research directions
- first papers to read
- one grounded candidate gap for each direction
- a ranked recommendation
- one measurable first question
- one cheap pilot protocol

The user should feel:

> This understands my situation and narrowed the search.

## Product Positioning

Say:

> AI helps students find realistic, grounded research directions they can execute.

Do not say:

> AI fully automates research.

The strongest value is:

- taste shaping
- feasibility filtering
- constraint-aware narrowing
- grounded gap generation
- realistic first questions

Experiment execution comes later. The first value is direction clarity.

## Workflow

### 1. Constraint Mapping

Do not generate research ideas first.

First collect the user's constraints:

- compute: GPU, accelerator, memory, cloud access, budget
- time: hours this week, typical experiment runtime, total project window
- skills: PyTorch, training loops, evaluation, math, systems, paper reading
- interests: optimizers, attention, architectures, inference, data, evals, interpretability
- goal type: publishable result, learning project, open-source contribution, benchmark improvement
- existing codebase: repo path, framework, baseline, datasets, scripts
- current evidence: prior runs, papers, notes, advisor feedback, known failures

Output a short structured profile.

Example:

```json
{
  "compute": "1x4090",
  "time_budget": "8 hours this week, 2 hour pilot runs",
  "skills": ["PyTorch", "training loops"],
  "interests": ["optimizers", "small transformers"],
  "goal_type": "publishable learning project",
  "recommended_regime": "small-scale controlled optimizer studies"
}
```

This profile decides what directions are allowed.

### 2. Direction Narrowing

Generate exactly 3 contrasting feasible directions by default.

Do not output 50 ideas.

Each direction must include:

- why it fits the user's constraints
- why it is scientifically interesting
- why it may be hard
- expected iteration speed
- required infrastructure complexity
- what papers to read first
- what result would matter

Good direction:

> Optimizer comparison for 50M-200M transformers under equal wall-clock budget.

Bad direction:

> Make transformers reason better.

The direction should be broad enough to survive literature reading, but narrow enough to reject irrelevant papers.

### 3. Literature Grounding

The system should not produce giant passive summaries.

For each anchor paper, extract:

```json
{
  "paper_id": "P1",
  "citation": "short paper citation or URL",
  "main_claim": "what the paper claims",
  "tested_setup": "model, task, data, scale, budget",
  "baselines": "what it compares against",
  "assumptions": "what must be true for the claim to matter",
  "limitations": "what the paper did not test",
  "missing_tests": "axes left unexplored",
  "reproducibility": "code/data/config availability",
  "direction_relevance": "why this paper matters for the user's constraints"
}
```

The user deeply reads 3-10 anchor papers.

The AI compresses the rest, but every important claim must point back to a paper note.

### 4. Grounded Gap Generation

AI should never output unsupported gaps.

Every gap must include at least one of:

- contradiction between papers
- missing axis
- unexplored regime
- weak experimental coverage
- untested baseline
- unreproduced claim

Every gap must include:

- gap statement
- evidence from paper notes
- citations
- why the gap matters
- smallest possible experiment
- kill condition

Grounded gap format:

```markdown
## Gap
No anchor paper tests Muon-style updates on sub-100M transformers under a fixed wall-clock budget.

## Evidence
- P1 tested Muon-style updates on vision transformers, not language-model pretraining.
- P2 tested optimizer changes for LLMs, but only at >1B parameters.
- P3 compared AdamW baselines for small transformers, but did not include Muon-style updates.

## Missing axis
Model scale below 100M parameters under fixed wall-clock budget.

## Why meaningful
This is the regime students and single-GPU researchers can actually run.

## Minimum experiment
Train the same 50M transformer with AdamW and Muon-style updates for the same wall-clock budget, same data order, same seeds, same token budget.

## Kill condition
Kill the direction if Muon-style updates do not improve validation loss, stability, or time-to-threshold in a 2-seed pilot.
```

Bad gap:

> Maybe Muon helps reasoning.

That has no evidence, no regime, no contradiction, no metric, and no kill condition.

### 5. Gap Verification

LLMs hallucinate gaps.

Every proposed gap needs a verifier pass before it becomes a research question.

The verifier checks:

- Was this already tested?
- Did the AI misunderstand a paper?
- Are the cited papers actually relevant?
- Is the metric measurable?
- Are baselines available?
- Does the user have the compute to test it?

Verifier output:

- `VERIFIED`: enough evidence to proceed
- `PARTIAL`: promising, but needs one more paper or baseline check
- `REJECTED`: already tested, unsupported, infeasible, or not meaningful

Rejected gaps should be kept as evidence, not hidden.

### 6. Gap Ranking

Not all true gaps are good gaps.

Score every verified or partial gap on:

| Axis | Meaning |
| --- | --- |
| Novelty | Has this already been explored? |
| Feasibility | Can this user test it? |
| Compute fit | Does it fit the user's machine or budget? |
| Clarity | Is the outcome measurable? |
| Scientific value | Would the result matter? |
| Risk | Is the signal likely to be noisy or ambiguous? |
| Dependency count | Does it require too many systems? |
| Iteration speed | Can the user test quickly? |
| Reproducibility | Can another person verify it? |

Default scoring:

- 1 = weak
- 2 = acceptable
- 3 = strong
- 4 = excellent
- 5 = unusually strong

The system should recommend the top 1 direction and keep 2 alternatives.

### 7. Question Definition

Convert the best gap into one measurable question.

Question must include:

- independent variable
- baseline
- metric
- regime
- constraint

Good question:

> Does Muon-style optimization improve validation loss over AdamW for 50M transformers under equal wall-clock budget on the same data and seeds?

Bad question:

> Does Muon make models smarter?

### 8. First Pilot Protocol

Only after the direction and question are grounded, define a cheap pilot.

Protocol must include:

- model
- dataset
- baseline
- intervention
- seeds
- runtime
- metrics
- logging
- expected cost
- success condition
- kill condition

The first pilot should reject bad ideas early.

## Mapping To AutoResearch-AI

This markdown MVP maps cleanly to existing product concepts:

- `topic`: collect constraints and create the one-sentence direction frame
- `paper-read`: turn papers into structured notes
- `hypothesis`: convert verified gaps into measurable questions
- `propose`: output exactly 3 feasible directions
- `rank`: score directions and gaps using the axes above

No new infrastructure is required for the first version.

The launchable MVP can be:

- one excellent prompt
- these three markdown files
- a simple page or CLI wrapper later
- a tutorial showing a student going from vague interest to one grounded direction
