# Test Scenarios

## 1. Blank Folder

- Agent sees an empty folder.
- Agent asks the target-selection question.
- Agent offers a demo repo fallback.

## 2. Real Repo

- Agent sees a real repo.
- Agent uses the current folder.
- Agent inspects existing history before suggesting experiments.

## 3. Local Build

- Agent installs ResearchLoop from the current local tarball.
- Agent does not rely on the published npm release.

## 4. First Experiment

- Agent proposes a concrete first experiment.
- Agent does not default to generic sweep-only advice.

## 5. Logging

- Transcript is saved.
- Short summary is saved.
- Any onboarding gaps are recorded.
