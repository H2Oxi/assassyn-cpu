# Assassyn-CPU: **C**o-designed **P**ipeline **U**nits for Assassyn

Assassyn-CPU builds on the upstream [assassyn](./assassyn) project to explore
AI-assisted RISC-V pipeline design. The repository keeps the reference
assassyn sources as a submodule and layers CPU-specific generators, design
notes, and regression tests on top of the shared toolchain.

---

## Getting Started

### Clone & Initialize

1. Clone this repository and enter the workspace:

   ```sh
   git clone <your-fork-or-origin> assassyn-cpu
   cd assassyn-cpu
   ```

2. Pull in the upstream tooling:

   ```sh
   git submodule update --init --recursive
   ```

### Environment Setup

`setup-env.sh` mirrors the submodule’s setup script and wires the environment to
use the embedded assassyn checkout:

```sh
source setup-env.sh
```

This exports `ASSASSYN_HOME`, extends `PYTHONPATH`, and adds cached simulator
artifacts to the path if they exist.

### Sanity Check

Validate the environment and Python bindings before working on CPU generators:

```sh
python test/unit-test/test_env.py
```

The script confirms the expected environment variables and attempts to import
`assassyn`, failing fast if the wrapper library is missing.

---

## Repository Layout

```
- assassyn/                 # Upstream assassyn project (git submodule)
- impl/
  `- gen-cpu/               # AI-assisted pipeline generator and helpers
     |- design.md           # High-level design notes and milestones
     |- main.py             # Entry point for CPU generation workflows
     |- pipestage.py        # Pipeline stage abstractions
     `- submodules.py       # Reusable submodule descriptions
- test/
  |- unit-test/             # Unit-level sanity suites (env checks, etc.)
  `- ci-test/               # Placeholder for end-to-end CI scenarios
- docs/
  |- rv32i.md               # RISC-V RV32I planning notes
  `- rv32i.csv              # Supporting tabular data
- resources/                # Reserved for design-time assets
- scripts/                  # Reserved for project-specific automation
- setup-env.sh              # Environment loader pointing at the submodule
```

---

## Development Workflow

- **Design in stages:** Author architectural notes and decomposition plans in
  `impl/gen-cpu/design.md` to guide AI-assisted module generation.
- **Prototype generators:** Use `impl/gen-cpu/main.py` together with the
  pipeline building blocks (`pipestage.py`, `submodules.py`) to iterate on
  CPU pipelines.
- **Leverage assassyn tooling:** Reuse `assassyn`’s Make targets (`build-all`,
  `test-all`, etc.) when you need the full backend stack, and keep the wrapper
  library up-to-date as generators evolve.
- **Extend tests early:** Add new regressions under `test/unit-test/` or
  `test/ci-test/` so the environment script remains the first guardrail.

---

## todo in the future

- 更高效的提供架构抽象
- 更精确的docs以节约tokens
- 提供更规范化的可定制开发框架

