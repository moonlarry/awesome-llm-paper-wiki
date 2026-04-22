# Examples

This directory contains example configuration and reference files.

## Files

| File | Description |
|------|-------------|
| `config.example.json` | Example vault configuration — copy this to your vault root as `config.json` |

---

## Quick Walkthrough

### Step 1: Clone and Install

```bash
git clone https://github.com/YOUR_USERNAME/paper-llm-wiki.git
bash paper-llm-wiki/install.sh --platform claude   # or codex / gemini
```

### Step 2: Initialize a Vault

```bash
bash paper-llm-wiki/install.sh --init-vault ~/my-papers
```

Or tell your agent:
```
Initialize a paper vault at ~/my-papers
```

The vault will be created with this structure:
```
~/my-papers/
├── paper/          ← put your Markdown papers here
├── library/        ← LLM-generated outputs
│   └── reports/
│       └── paper/  ← single-paper reading notes
├── schema/         ← tag taxonomy, journal aliases
├── templates/      ← report templates
├── workspace/      ← logs, cache, manifests
├── config.json     ← vault configuration
└── paper-library.md  ← dashboard
```

### Step 3: Add Papers

Place your Markdown paper files in `paper/YourDirection/`:
```
paper/
└── ExampleDirection/
    ├── paper1.md
    └── paper2.md
```

### Step 4: Scan and Organize

Tell your agent:
```
Scan papers
```

This runs `scripts/scan_sources.py` and detects all Markdown files. Then:
```
Organize by journal
```

Papers are sorted into `paper/ExampleDirection/JOURNAL/`, `paper/ExampleDirection/JPS/`, etc.

### Step 5: Ingest

```
Ingest all papers
```

The agent reads each paper, extracts metadata, assigns tags, and creates a canonical page in `library/papers/ExampleDirection/`.

### Step 6: Read One Paper

```
Read this paper: library/papers/ExampleDirection/example.md
```

The agent generates a structured single-paper reading note under `library/reports/paper/`.

### Step 7: Generate Reports

```
JOURNAL journal report
```

Produces `library/reports/journal/JOURNAL-report-2026-04-19.md` with topic trends, method landscape, high-value papers, and research gaps.

```
Recommend submission for my-draft.md
```

Scores candidate journals across 6 dimensions and recommends the top 5.

---

## Customizing `config.json`

The key settings to change:

```json
{
  "output_lang": "zh",        // "zh" (Chinese) or "en" (English)
  "directions": ["ExampleDirection"],  // your research direction folders under paper/
  "templates": {
    "domain_min_papers": 10   // papers needed before domain templates are generated
  }
}
```

## Adding Journal Aliases

Edit `schema/journal_aliases.json` in your vault:

```json
{
  "Nature Energy": "NatEnergy",
  "Journal of Power Sources": "JPS",
  "My Custom Journal Name": "MCJ"
}
```

## Adding Keyword Rules

Edit `schema/keyword_rules.json` in your vault to auto-tag papers:

```json
{
  "rules": [
    { "pattern": "task a|problem a", "tag": "TaskA estimation", "dimension": "task" },
    { "pattern": "LSTM|long short-term memory", "tag": "LSTM", "dimension": "method" },
    { "pattern": "dataset a|dataset b", "tag": "benchmark dataset", "dimension": "dataset" }
  ]
}
```
