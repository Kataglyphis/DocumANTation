Table of Contents
1. About
2. Acknowledgements
2. Getting Started with this Template
3. Tips to writing a good CV
ABOUT---------------------------------------------------

ACKNOWLEDGMENTS-----------------------------------------
USA STEM CV Template
This template has been adapted from a template created by Christophe Roger (Darwiin). The further edits were made to make a more academic CV by USA standards include letter size and various sections. 

Tips on what to include at the bottom of this document.


Awesome Source CV [![Example](https://img.shields.io/badge/Exemple-pdf-blue.svg)](https://raw.githubusercontent.com/posquit0/Awesome-CV/master/examples/resume.pdf)
=================

## About

**Awesome Source Latex CV** is based on a CV template created by Alessandro Plasmati. The original template use _XeLaTeX_ engine and _[Fontin Sans](http://www.exljbris.com/fontinsans.html)_ font. 

More informations about the original Alessandro Plasmati template can be found here :

   -  [ Scribd ](http://fr.scribd.com/doc/16335667/Writing-your-Professional-CV-with-LaTeX)
   -  [ LaTeX Templates ](http://www.latextemplates.com/template/plasmati-graduate-cv)
   -  [ ShareLatex ](https://www.sharelatex.com/templates/cv-or-resume/professional-cv)

**Personal data** has moved on top of the first page just before the position and _[Fontin Sans](http://www.exljbris.com/fontinsans.html)_ font has been replaced by _[Source Sans Pro Font](https://github.com/adobe-fonts/source-sans-pro)_ from Adobe. _[Font Awesome](http://fontawesome.io/)_ icons are used to highlight important elements.

Unlike _Alessandro Plasmati_ CV template, all layout stuff in **Awesome Source Latex CV** has moved in the Latex class file _awesome-source-cv.cls_.

GETTING STARTED WITH THIS TEMPLATE ---------------------

You can edit online **Awesome Source Latex CV** on [Overleaf](https://www.overleaf.com/latex/templates/awesome-source-cv/wrdjtkkytqcw). Feel free to use my [referal link](https://www.overleaf.com/signup?ref=54c221604cd6) if you want to create your account.

## How to use **Awesome Source CV** latex class

### Construct the header

Outside of the `\socialinfo` wrapper you have to define the mandatory parameters `\name` and `\tagline`.

```latex
% Define author's name
% Usage: \name{<firstname>}{<lastname>}
% Mandatory
\name{Christophe}{ROGER}

% Define author's photo (optional)
% Usage \photo{<diameter>}{<photo>}
\photo{2.5cm}{darwiin}

% Define author's tagline
% Usage: \tagline{<tag line>} 
% Mandatory
\tagline{Chef de projet IT}
```

Most social network have their command to render a clickable link or a simple text entry.

```latex
% Render author's linked-in (optional)
% Usage: \linkedin{<linked-in-nick>}
\linkedin{christopheroger}

% Render author's viadeo(optional)
% Usage: \viadeo{<viadeo-nick>}
\viadeo{christopheroger}

% Render author's github (optional)
% Usage: \github{<github-nick>}
\github{darwiin}

% Render author's email (optional)
% Usage: \email{<email adress>}
\email{christophe.roger@mail.com}
```

Put these command in the `\socialinfo` wrapper. Feel free to add `\\` when you want to force a new line.

```latex
\socialinfo{
  \linkedin{christopheroger}
  \viadeo{christopheroger}
  \github{darwiin}\\
  \smartphone{+687 123 456}
  \email{christophe.roger@mail.com}\\
  \address{2 Rue du quartier, 98765 Ville, Pays}\\
  \infos{Né le 23 septembre 1982 (34 ans) à Nouméa, Nouvelle-Calédonie}
}
```

Use the `\makecvheader`command to generate the header.

```latex
\makecvheader
```

### Construct the _experiences_ section

To describe your experiences you have first to declare the `experiences` environment

```latex
% Begin a new experiences environment to use experience and consultantexperience macro
\begin{experiences}

% Here's go your experiences

\end{experiences}
```

Then you can describe your experiences using **\experience** and **\consultantexperience** entries. Each
entry must be separated by the **\emptyseparator** 

```latex
% Begin a new experiences environment to use experience and consultantexperience macro
\begin{experiences}

% The experience entry work as below and can be used to describe a job experience
  \experience
    {End date}      {Experience title}{Enterprise}{Country}
    {Begin date}    {
    				  experience details
                      \begin{itemize}
                        \item Item 1: _Item 1 description_
                        \item Item 2: _Item 2 description_
                        \item Item 3: _Item 3 description_
                      \end{itemize}
                    }
                    {Technology highlights}

% The emptyseparator macro is used to create white space in your experience
  \emptySeparator

% The consultantexperience macro is very similar to the experience macro, but offer you 
% the possibility tu put client details
  \consultantexperience
    {End date}        {Experience title}{Enterprise}{Country}
    {Begin date}      {Client job title}{Clent enterprise}
                    {
                      experience details
                      \begin{itemize}
                        \item Item 1: _Item 1 description_
                        \item Item 2: _Item 2 description_
                        \item Item 3: _Item 3 description_
                      \end{itemize}
                    }
                    {Technology highlights}
\end{experiences}
```

## License

Latex class file _awesome-source-cv.cls_ is published under the term of the [LPPL Version 1.3c](https://www.latex-project.org/lppl.txt).

All content files are published under the term of the [CC BY-SA 4.0 License](https://creativecommons.org/licenses/by-sa/4.0/legalcode).



TIPS to making a good CV /  Sections to include---------

Do's
Research and Teaching Interests
Education
Professional / Academic positions can separate
Publications / Posters / Presentations
Awards
Contact Info
Include current project and publications in progress
Teaching experience / tutoring / mentoring
Grants / Contributions to research grant writing
Professional initiative / outreach / professional service (creating events not being in a group)
Possible include references
Can include coursework but drop after time

Dont Include
DOB / marital status
misleading info
holes in time
headshot
do not overinflate


SECTIONS
CONTACT INFORMATION: phome, email, webpage url, address
EDUCATION: Degrees and certs since end of high school 
CERTIFICATIONS: Courseera / EdX / Rackham etc
AWARDS: Fellowships, grants, awards in general etc
PROFESSIONAL and ACADEMIC EXPERIENCE: grad researcher, internship, industry jobs
RESEARCH STATEMENT: research interests / experience < 6 lines
PUBLICATIONS:
- divide in journal vs conference
- peer reviewed or not
- do not mislead: show the complete authors' list
- you can clarify the practice in your discipline
- "Accepted for publication" manuscripts go here
Could report: 
   - Acceptance rates, and impact factors
   - Audience sizes
WORKS IN PROGRESS
- Papers /scholarly work you are working on, but has not been accepted yet
PRESENTATIONS AND POSTERS
PATENTS / PATENTS APPLICATIONS
GRANTS?
MENTORING
- Undergraduates / junior students
TEACHING EXPERIENCE
- Graduate instructor, grading
- Teaching evaluations?
- can include tutoring
- pedagogy statement? (<6 lines)
- guest lecturing
PROFESSIONAL SERVICE
- Reviewed Papers
- contributed to research grant proposals
- officer ina student group in your discipline or beyond
- could split within/outside university
OUTREACH
- Activities to engage people in your discipline who are not usually exposed to it
PRESS?
PROFESSTIONAL SOCIETIES
MENTORING
COMMUNITY SERVICE

LAYOUT
< 3 colors
Easy to find headers
full width for content if possible