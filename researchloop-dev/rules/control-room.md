# Control Room Rules

- Keep the product package and the local dev control room separate.
- Do not add this folder to the npm package contents.
- Test the current local build with a packed tarball when you need exact reproducibility.
- Use a fresh empty lab folder for onboarding tests.
- Save transcripts and summaries here, not inside the product package.
- Prefer the smallest useful test first.
- If the agent has no repo context, let it discover the target folder itself.
- If the agent has no time budget yet, ask exactly one question and record the answer.
- Avoid generic sweep-first suggestions unless the repo history justifies them.
