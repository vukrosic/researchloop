#AI research workflow

Goal:
- Increase research throughput using AI-assisted experimentation.

Helping AI researchers create a lot higher research throuput with AI.

These files will instruct AI and researcher on how to do it.

1. Decide temporary research frame to prevent infinite paper reading:
- I want to improve optimizer efficiency for small transformers.
- I want  to reduce attention memory usage.


so the first step is to write 1 sentence:
- We are researching optimizer improvements for sub-1B transformers under fixed compute.
This sentence will help AI quickly reject irrelevant stuff (4/5 AI automation possibility)

So write one sentence, a measurable claim:
- Muon-style updates improve validation loss versus AdamW on small transformers under fixed compute.
- Attention residual routing reduces loss without increasing inference cost.


The boundary decides:
- what papers matter
- what experiments matter
- what benchmarks matter
- what metrics matter
- what success means

So, the first tool is: what exact claim are you trying to test? And then immediately after, how would you measure success or failure? 

Without prioritizing boundary the system can not prioritize anything.



2. Read papers

- existing approaches
- assumptions
- mechanisms
- unexplored gaps
- contradictions
- reproducibility