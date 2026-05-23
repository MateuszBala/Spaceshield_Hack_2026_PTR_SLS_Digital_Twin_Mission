# Repo Structure

Wywolanie:

```bash
bash init_repo_structure.sh nazwa-pakietu
```

```text
NAZWA_REPO/
├── .claude/
│    ├── agents/
│    ├── commands/
│    ├── CLAUDE.md
│    ├── settings.json
│    └── settings.local.json
├── .gitignore
├── .github/
│    ├── copilot-instructions.md
│    ├── get_review.sh
│    └── PULL_REQUEST_TEMPLATE.md
├── configs/
│    └── .gitkeep
├── docker/
│    └── .gitkeep
├── docs/
│    ├── api/
│    │    └── .gitkeep
│    ├── architecture/
│    │    └── .gitkeep
│    ├── decisions/
│    │    └── .gitkeep
│    ├── development/
│    │    └── .gitkeep
│    ├── goal/
│    │    ├── CONCEPT.md
│    │    ├── ROADMAP.md
│    │    └── PROGRESS.md
│    ├── rules/
│    │    └── COMMIT_CONVENTIONS.md
│    ├── runbooks/
│    │    └── .gitkeep
│    └── version/
│         ├── VERSION.md
│         └── CHANGELOG.md
├── grafana/
│    └── .gitkeep
├── migrations/
│    └── .gitkeep
├── protos/
│    └── .gitkeep
├── runtime-configs/
│    └── .gitkeep
├── scripts/
│    ├── bootstrap/
│    │    ├── ENVIRONMENT_SETUP.md
│    │    └── init_environment.sh
│    ├── dev/
│    │    └── .gitkeep
│    ├── ops/
│    │    └── .gitkeep
│    ├── proto/
│    │    └── .gitkeep
│    └── systemd/
│         └── .gitkeep
├── src/
│    ├── CLAUDE.md
│    └── nazwa-pakietu/
│         └── __init__.py
├── tests/
│    ├── .gitkeep
│    ├── integration/
│    │     └── __init__.py
│    ├── soak/
│    │     └── __init__.py
│    └── unit/
│         └── __init__.py
├── CLAUDE.md
├── README.md
├── Makefile
└── pyproject.toml
```

Uwaga:
- Skrypt nie nadpisuje istniejacych plikow.
- Dla zgodnosci z Python, nazwa pakietu z '-' jest zapisywana jako '_' w katalogu src/.
