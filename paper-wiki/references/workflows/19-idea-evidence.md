# Workflow 19: idea-evidence

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 19: idea-evidence

### Purpose
Build the dedicated evidence pack that `idea-create` consumes. This is an idea-generation input workflow, not a replacement for `direction-review` or a general survey report. Every full evidence pack must combine both local vault evidence and a network evidence path.

### Input
- Required: research topic text or a topic brief at `workspace/research-briefs/{topic_slug}-research-brief.md`
- Optional: direction, scope constraints, excluded directions, or an existing related `idea-survey` report

### Steps

1. Read the topic brief when it exists; otherwise assemble a working brief from the user request.
2. Extract scope, constraints, prior attempts, non-goals, and the current working direction.
3. Aggregate local evidence from canonical pages, source Markdown, existing reports, indexes, and any relevant `idea-survey` output.
4. Run the network evidence path by reusing existing retrieval workflows such as `web-find` and `web-digest`; do not introduce a new retrieval primitive here.
5. Deduplicate and screen a topic-relevant external pool, selecting at least 50 suitable network papers for the evidence pack.
6. Deep-read all 50 selected network papers beyond metadata or abstract skim, capturing contribution, mechanism, assumptions, experiments, results, limitations, future work, and topic relevance.
7. Synthesize idea-oriented structures:
   - gap map
   - contradiction map
   - transfer opportunities
   - underexplored design space
   - negative space or over-crowded directions to avoid
8. Generate `library/reports/idea/{topic_slug}-idea-evidence-{date}.md` using `templates/generic/idea_evidence.md`.

### Required Handoff to `idea-create`
- topic brief snapshot
- local evidence landscape
- screened external corpus and exclusion notes
- deep-read notes for all 50 selected network papers
- gap, contradiction, transfer-opportunity, and negative-space synthesis

### Reviewer Routing
When a second-opinion evidence check is needed, use a Codex-compatible MCP reviewer first, otherwise a fresh independent agent when the runtime supports it, otherwise degraded local analysis. Label degraded local analysis in the output.

### Conference Seed Mode

Internal conditional mode of Workflow 19. Not a separate workflow. Do not advertise in the workflow catalog or README. Activate only when called by Workflow 20's hidden conference-paper activation gate, or when the user explicitly asks idea-evidence to build evidence from a provided conference paper file.

#### Activation Conditions

All conditions below must be true to activate this mode:

1. The user is asking for idea generation, journal adaptation, or evidence construction from a specific paper.
2. The user explicitly provides a local paper file path or attached paper file in the request.
3. The file is explicitly or plausibly a conference paper.

If conditions 1 and 2 are true but condition 3 is unclear, ask one clarification: "Should I treat this file as a conference paper for conference-to-journal adaptation?"

Never activate this mode from: a paper title only, a DOI only, a URL only, a general mention of a conference, an existing file discovered in the workspace without the user providing it, or a normal topic brief with no paper file.

#### Conference Paper Detection

Treat the file as a conference paper if any high-confidence signal is present.

High confidence:
1. The user explicitly says it is a conference paper.
2. The title page, metadata, header, footer, or citation block names a known conference/proceedings venue.
3. The paper contains wording such as "Proceedings of", "In Proceedings", "Conference on", "accepted at", or an official conference acronym/year.

Medium confidence (path keyword triggers inspection, not automatic classification):
4. The file path or filename contains a conference venue keyword: neurips/nips, icml, iclr, cvpr, iccv, eccv, acl, emnlp, naacl, aaai, ijcai, kdd, sigir, www/thewebconf, chi, uist, sigmod, vldb, isca, osdi, sosp, usenix, ecc, interspeech.

Negative signals (override medium-confidence path keywords when present in paper metadata):
- IEEE Transactions, ACM Transactions, Elsevier journal name, Springer journal name
- volume/issue journal metadata, "Journal of ...", "Transactions on ..."

If signals conflict, ask one clarification before proceeding.

#### Scope Exemption

This mode is exempt from the normal broad idea-evidence requirement to deep-read ≥50 network papers, unless the user explicitly requests a full broad evidence pack.

#### Inputs

- `conference_paper_path` (required)
- Optional: target journals, target domain, topic constraints

#### Output

A conference-journal evidence pack saved to `library/reports/idea/{topic_slug}-conf-journal-adaptation-{date}.md` using `templates/generic/conf_journal_adaptation.md`. This pack can be consumed by Workflow 20 idea-create.

#### Steps

1. **Verify the conference seed.**
   - If an absolute path is provided, use it directly.
   - If a relative path is provided, resolve from the vault root first; if not found, resolve from the user's stated location.
   - If the file is attached to the message, use the attachment directly.
   - If the file cannot be located, ask: "Cannot find the file. Please provide the full path."
   - Confirm the file exists and is readable.
   - Identify title, authors, year, venue, and publication type.
   - Apply the conference paper detection heuristics above.
   - If journal/proceedings signals conflict, ask one clarification.

2. **Extract the seed method.**
   - Read abstract, introduction, method, experiments, limitations, and conclusion.
   - Extract the core technical mechanism, assumptions, input/output setting, claimed advantages, datasets, baselines, and missing validation.
   - Summarize the method as a compact method profile.

3. **Establish journal target context.**
   - If target journals are provided, use them.
   - Otherwise infer plausible journals from the paper domain.
   - Use `journal-report` when venue expectations are needed.
   - Record expected journal standards: validation depth, robustness, application fit, theory, reproducibility, ablations, and domain-specific requirements.

4. **Search recent journal comparators.**
   - Use `web-find` to collect a screened candidate pool, normally 40-80 candidate records when available.
   - Prefer recent journal papers from the last 3-5 years, adjusted for field pace.
   - Use three search lanes:
     - method-similar: papers using comparable technical mechanisms
     - task-similar: papers solving the same problem or benchmark
     - venue-similar: papers from target or adjacent journals
   - Do not rely only on citation search; fresh conference papers may have few citations.

5. **Deep-read focused comparators.**
   - Use `web-digest` on 15-25 journal papers by default.
   - Use at least 10 when credible comparators exist.
   - If fewer than 10 credible comparators exist, continue and explicitly report the evidence limitation.
   - Prioritize direct method overlap, task overlap, target-journal relevance, and strong baselines.

6. **Build the comparison matrix.**
   - Compare the conference method against journal methods by: mechanism, task, assumptions, validation, data, performance, robustness, interpretability, efficiency, and domain fit.
   - Record both conference advantages and journal advantages.
   - Separate verified evidence from inferred judgments.

7. **Assess gap polarity.**
   - Classify the case as one of: `conference-advantaged`, `journal-advantaged`, `mixed`, `insufficient evidence`.
   - If journal methods are stronger, explicitly state that the time-gap thesis does not hold for this case.
   - This classification determines the idea-generation strategy in Workflow 20.

8. **Synthesize adaptation opportunities.**
   - Identify how the conference method could be adapted for journal expectations.
   - Include combination opportunities when journal methods are stronger or complementary.
   - Include validation, robustness, domain-specific, theoretical, benchmark, and deployment-oriented adaptation paths.

9. **Produce the evidence pack.**
   - Include: source conference paper profile, inferred or provided target journals, journal comparator set, comparison matrix, gap polarity assessment, conference advantages, journal advantages, adaptation opportunity map, evidence limitations, handoff notes for idea-create.
   - Save to `library/reports/idea/{topic_slug}-conf-journal-adaptation-{date}.md`.
   - Use `templates/generic/conf_journal_adaptation.md` as the report scaffold.

