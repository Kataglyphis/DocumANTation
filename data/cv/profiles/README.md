# CV profiles

One CV, several targets. A profile decides **which sections a build shows** and
**what the summary above them says** — nothing else. Everything a profile shows
comes from the same `section_*.tex` files, so a fact fixed once is fixed for
every application.

```bash
make cv                                  # default profile, English
make cv-all                              # default profile, both languages
make cv-mistral-rse                      # Research Software Engineer, Mistral, English
make cv-mistral-platform                 # Platform Engineer, Mistral Research Platform, English
make cv-amd-hpc                          # Lead HPC/AI Computational Scientist, AMD GENCI CoE, English
make cv-terabase-cv                      # Computer Vision Engineer, Bamboo, Terabase Energy, English
make cv-parallel-ai                      # AI Engineer, Parallel, English
make letter-parallel-ai                  # its cover letter (letters/parallel-ai.tex; see ../README.md)
make cv-c12-automation                   # AI Automation Engineer, C12 Quantum Electronics, English
make letter-c12-automation               # its cover letter
CV_PROFILE=mistral-rse CV_LANG=german ./scripts/build_in_container.sh cv
```

## What a profile file contains

Two macros, and optionally a layout flag:

| Macro | Meaning |
| --- | --- |
| `\cvTagline` | The line under the name in the header. Carries both languages via `\IfLanguageName`. |
| `\cvBody` | The ordered `\input{section_*}` list. This *is* the tailoring. |
| `\cvshowschoolfalse` | Optional. Drops the A-levels entry from `section_education.tex`. |
| `\cvshowthesislinesfalse` | Optional. Drops both thesis lines; degrees, dates, grades and subject tags stay. |
| `\cvshowteachingtitlefalse` | Optional. Suppresses the "Teaching and Mentoring" heading. |
| `\renewcommand{\cvFraunhoferOrder}` | Optional. The order of the Fraunhofer IPA bullets; list every `\cvFhg<Name>`, hidden ones too (see `cv.tex`). |
| `\renewcommand{\cvFhgTags}` | Optional. The Fraunhofer IPA tag row. One line is the budget: swap tags, do not add them, and check the row still fits (see `cv.tex`). |

The flags are declared in `cv.tex`, all default to *on*, and exist for one
reason: buying lines. They drop **detail**, never a dated entry — a CV with a
hole in its timeline costs more than a thesis title saves.

`\cvshowteachingtitlefalse` is the cheapest of the three. Input
`section_teaching_mentoring` directly after `section_experience` with the
heading off and the tutor post reads as one more job under Experiences — which
it is, and which is also more honest about it than a separate section. The
heading and its whitespace were most of what that section cost.

`cv.tex` reads `profiles/\cvprofile.tex` before `\begin{document}`, so a profile
may also redefine anything the class exposes. Keep that power for layout, not
for content.

## The rule that keeps this maintainable

**Profiles select sections. They do not fork prose.**

Role-specific wording lives in its own `section_headline_<profile>.tex`, which
the profile inputs instead of the general `section_headline.tex`. A per-profile
branch inside every section file is the same trap `../README.md` flags for
adding a third language: it multiplies every future edit by the number of
profiles, and the branches drift.

If a fact is true, it belongs in the shared section — for *every* profile, not
just the one that happens to need it today. Only the emphasis is per-profile.

## The page budget is the constraint

The CV is one page. Nine sections exist; four fit. That is the whole reason
profiles exist — picking the four is a per-application decision, and it used to
be made by commenting lines in and out of `cv.tex`.

The first thing to spill onto page two is the Languages/Hobbies/Publications
row at the bottom. **Rebuild and check the page count after any edit**, in both
languages: German sets roughly 10% longer than English, so an English build that
fits proves nothing about the German one.

## Profiles

| Profile | Target | Output |
| --- | --- | --- |
| `default` | General purpose; the pair published on jonasheinle.de | `CV_Jonas_Heinle_<language>.pdf` |
| `mistral-rse` | Research Software Engineer, Mistral AI (Paris) | `CV_Jonas_Heinle_Mistral_RSE.pdf` |
| `mistral-platform` | Platform Engineer, Research Platform team, Mistral AI (Paris/Warsaw/London) | `CV_Jonas_Heinle_Mistral_Platform.pdf` |
| `amd-hpc` | Lead HPC/AI Computational Scientist / Engineer, AMD GENCI Center of Excellence (Paris) | `CV_Jonas_Heinle_AMD_HPC.pdf` |
| `terabase-cv` | Computer Vision Engineer, Bamboo, Terabase Energy (Paris R&D hub, remote) | `CV_Jonas_Heinle_Terabase.pdf` |
| `parallel-ai` | AI Engineer, Parallel (Paris, on-site) | `CV_Jonas_Heinle_Parallel_AI.pdf` |
| `c12-automation` | AI Automation Engineer, C12 Quantum Electronics (Paris, on-site) | `CV_Jonas_Heinle_C12_AI_Automation.pdf` |

Each profile file opens with the posting's requirements and the section that
answers each one. Keep that up: a year from now it is the only record of why a
profile drops the sections it drops.

## Honesty

A tailored CV reorders and re-selects true facts. It does not acquire skills
the posting asks for. `mistral-rse` deliberately claims neither Kubernetes nor
SLURM although the posting names both — see the note at the top of
`../section_headline_mistral_rse.tex` before "fixing" that. The same holds for
`mistral-platform`: its posting names Bazel, Go and an orchestrator; Bazel
(LiteRT-LM) and Go (the AI-gateway WebAssembly plugins) are claimed, Kubernetes
is not — see the note in `../section_headline_mistral_platform.tex`.
`amd-hpc` is the same rule once more: its posting names MPI, HIP, OpenMP and
Fortran, and the profile claims none of them. CUDA and the quantum-physics
port are the GPU-programming and application-modernisation evidence instead —
see the note at the top of `../section_headline_amd_hpc.tex`.
`terabase-cv` applies the rule once more. Its posting names MLflow, DVC,
TensorFlow, segmentation, annotation tools, labeling-validation workflows,
B2B SaaS, GIS, digital twins and startup experience, and the profile claims
none of them. PyTorch was at first claimed only as far as the quantum-port
bullet showed it (GPU simulation, not deep-learning training). It became a
full claim on 2026-09-22, when the owner confirmed that every detection model
was trained in PyTorch. See the note at the top of
`../section_headline_terabase_cv.tex`.

`c12-automation` follows the same rule. Its posting names MCP servers, Prefect,
LangGraph, n8n, OVH, Tailscale, Ansible and Google Workspace, and the profile
claims none of them. Its cover letter names them as the tools the owner would
learn first.

A fact arriving late does not relax this. Go moved off the not-claimed list on
2026-09-04 because the work turned up, not because the posting wanted it.
AI-assisted review and AI-driven testing and debugging did the same on
2026-09-22 in `terabase-cv`, when the owner confirmed them as daily practice,
run privacy-first on self-hosted models. On 2026-09-23 the owner's answers
moved more onto the claimed side for `c12-automation`:

- agent skills built for the quantum computing team;
- the planner/executor agent loop;
- RAG, used for information retrieval, not a RAG system built;
- plain WireGuard, claimed in the letter only;
- an access-controlled AI gateway;
- the on-premises DGX systems;
- Python in every project;
- work with teams in quantum computing, biotech, mechanical engineering and
  electroplating.

See the notes at the top of `c12-automation.tex`.
