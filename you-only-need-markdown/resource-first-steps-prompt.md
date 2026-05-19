# Resource and First Steps Prompt

These are instructions for the AI to help with the first step of research.

```text
You are helping an AI PhD student start a serious research project.

Keep it simple. Do not propose experiments yet. First help me understand what I have, what I am missing, and what the next small steps should be.

Help me build:

1. My one-sentence research frame.
   Example: "I am studying optimizer improvements for sub-1B transformers under fixed compute."
   [add more examples here]

2. After we talk about one-sentence research frame, only after we have multiple options, then you will help me figure out the claim I want to test more precisely.
   Example: "Muon-style updates improve validation loss versus AdamW under the same compute budget."

Somewhere within this process, you will ask me for this information that I may have:
   - code repo
   - baseline result
   - dataset
   - compute/GPU
   - papers or notes
   - advisor or collaborator feedback
   - time budget and or time budget for the next week

If there is anything else you think is important, you can talk to me and ask me.