# CV profiles

One CV, several targets. A profile decides **which sections a build shows** and
**what the summary above them says** — nothing else. Everything a profile shows
comes from the same `section_*.tex` files, so a fact fixed once is fixed for
every application.

```bash
make cv                                  # default profile, English
make cv-all                              # default profile, both languages
make cv-mistral-rse                      # tailored, English
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

Each profile file opens with the posting's requirements and the section that
answers each one. Keep that up: a year from now it is the only record of why a
profile drops the sections it drops.

## Honesty

A tailored CV reorders and re-selects true facts. It does not acquire skills
the posting asks for. `mistral-rse` deliberately claims neither Kubernetes nor
SLURM although the posting names both — see the note at the top of
`../section_headline_mistral_rse.tex` before "fixing" that.
