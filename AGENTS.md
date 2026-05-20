# AGENTS.md

Behavioral guidelines for AI coding agents working in this repository.

## 1. Think Before Coding
Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them. Do not pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what is confusing. Ask.

## 2. Simplicity First
Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No flexibility or configurability that was not requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: Would a senior engineer say this is overcomplicated? If yes, simplify.

## 3. Surgical Changes
Touch only what you must. Clean up only your own mess.

When editing existing code:
- Do not improve adjacent code, comments, or formatting.
- Do not refactor things that are not broken.
- Match existing style, even if you would do it differently.
- If you notice unrelated dead code, mention it. Do not delete it.

When your changes create orphans:
- Remove imports, variables, or functions that YOUR changes made unused.
- Do not remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution
Define success criteria. Loop until verified.

Transform tasks into verifiable goals:
- "Add validation" becomes "Write tests for invalid inputs, then make them pass"
- "Fix the bug" becomes "Write a test that reproduces it, then make it pass"
- "Refactor X" becomes "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]

Strong success criteria let you loop independently. Weak criteria require constant clarification.

## 5. Destructive Actions Need Explicit Instruction
Don't mutate state outside the working tree without being told to.

- Includes `git commit`, `git push`, `git rebase`, `git reset --hard`, `git clean`, branch or file deletion, and dependency installs that modify lockfiles.
- Drafting an artifact is not an instruction to apply it. Writing a commit message is not an instruction to commit. Writing a script is not an instruction to run it.
- Default action after producing an artifact is to present it. The user applies it.

## Project Commands
- Install dev tools: `python -m pip install -e ".[dev]"`
- Build artifact: `dictionary-normalizer --input input --output output/artifact.json`
- Validate artifact: `dictionary-normalizer --validate output/artifact.json`
- Test with coverage: `coverage run -m pytest tests && coverage report`
- Lint: `ruff check .`
- Format check: `ruff format --check .`
- Type check: `mypy src`

## Project Conventions
- `PROMPT.md` is the authoritative product and artifact contract. Treat schema changes as breaking and update the prompt before changing emitted JSON.
- Runtime code should stay dependency-free unless there is a clear need; dev-only tooling belongs in the `dev` extra and `requirements-dev.txt`.
- Generated artifacts belong under `output/`. Keep `output/.gitkeep`; do not commit generated JSON unless explicitly asked.
- `--refresh` must fail clearly unless every enabled source has a pinned `download_url` and matching SHA-256. Do not make refresh silently fall back to offline input.

## Watch Out
- Normalized words must remain lowercase ASCII alphabetic tokens only: `^[a-z]+$`.
- Do not write derived `counts` fields into artifacts. Counts are computed by consumers from bucket lengths.
- Keep blocklist filtering active; `src/dictionary_normalizer/data/blocked-server-words.txt` is the project-local server-name blocklist.
- `corpora-egyptian-gods` is disabled in `sources.toml` because the extracted source is polluted with non-name concepts. Do not re-enable it without curation.

## AI Artifacts
Do not commit scratch notes, plans, drafts, or transcripts to the repository. Do not reference local scratch workspaces in any committed file, including source code, comments, docstrings, or documentation. Follow local artifact conventions if the developer's environment provides them; otherwise keep these out of the tree entirely.
