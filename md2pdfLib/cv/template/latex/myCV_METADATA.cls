%% Copyright 2016 Christophe Roger
%
% Author: 
% Jonas Heinle
% based on template of Christophe Roger (Darwiin)
%
% This work may be distributed and/or modified under the
% conditions of the LaTeX Project Public License, either version 1.3c
% of this license or (at your option) any later version.
% The latest version of this license is in
%   http://www.latex-project.org/lppl.txt
% and version 1.3 or later is part of all distributions of LaTeX
% version 2005/12/01 or later.
%
% This work has the LPPL maintenance status `maintained'.

\ProvidesClass{myCV_METADATA}[2026/07/21 v0.1.0 'Jonas Heinle CV' Class]

\LoadClass[letterpaper]{article}

\newif\if@showLinks   \@showLinksfalse

% The accent is not an option: it comes from style/brand.json via
% brand-colors.tex (basecolor := brandAccent), shared with the book, the
% slides and the website. The upstream template's green/red/indigo/orange/
% monochrome options each hardcoded their own basecolor and would have
% silently overridden the brand.
\DeclareOption{alternative}{
	\def\@alternative{alternate}
}

\DeclareOption{showLinks}{ \@showLinkstrue}

% Main document language. Every section file carries an English and a German
% variant behind \IfLanguageName, so the language is a build-time switch over
% one set of sources rather than two parallel CVs. Select it as a class option
% without editing cv.tex:
%   lualatex "\PassOptionsToClass{german}{myCV_METADATA}\input{cv.tex}"
% which is what CV_LANG=german in scripts/build_in_container.sh does.
% French stays loaded for \foreignlanguage but is not a main-language choice:
% the section files have no French text to select.
\def\cv@mainlang{english}
\def\cv@datestyle{en-US}
\DeclareOption{english}{\def\cv@mainlang{english}\def\cv@datestyle{en-US}}
\DeclareOption{german}{\def\cv@mainlang{ngerman}\def\cv@datestyle{ngerman}}

\ProcessOptions

% Dependences
%A Few Useful Packages
% \edef so the chosen language reaches babel as text, not as a macro name.
\edef\cv@babelopts{french,ngerman,english,main=\cv@mainlang}
\expandafter\RequirePackage\expandafter[\cv@babelopts]{babel}
% No inputenc shim: LuaLaTeX reads UTF-8 natively; luainputenc was a leftover
% from the template's pdflatex days and fights fontspec.
\RequirePackage{fontspec} 					                 % for loading fonts
\RequirePackage{url,parskip} 	    % other packages for formatting
\RequirePackage[dvipsnames]{xcolor}
% geometry alone controls the page: fullpage was loaded too and immediately
% overridden by geometry's margins.
\RequirePackage[margin=1.5cm]{geometry}
\RequirePackage{fontawesome}
\RequirePackage{hyperref}
\RequirePackage{titlesec}
\RequirePackage{array}
\RequirePackage{enumitem}
\RequirePackage{longtable}
\RequirePackage{etoolbox}
\RequirePackage{tikz}
\RequirePackage[skins]{tcolorbox}
\RequirePackage{fancyhdr}

\RequirePackage[
	german = guillemets,%quotes,<- I'd like to have both quot. marks in the same document
	autostyle = true,
	autopunct,
	csdisplay = true,
]{csquotes}

\RequirePackage{iflang}
% Date style follows the main language, so a German CV does not print US dates.
\expandafter\RequirePackage\expandafter[\cv@datestyle]{datetime2}

% Brand colours and fonts — single source of truth: style/brand.json.
% Found via TEXINPUTS (see scripts/build_in_container.sh), so this class does
% not need to know where the style directory sits relative to the build dir.
\input{brand-colors.tex}   % basecolor := brandAccent, linkcolor := brandLink
\input{brand-fonts.tex}    % \brandSetMainFont / \brandSetMonoFont
% Neutral greys/blacks are deliberately per-document, not brand tokens
% (see style/README.md "Deliberately not brand-wide").
\colorlet{headingcolor}{black}
\definecolor{darkGrey}{HTML}{989898}

% linkcolor comes from brand-colors.tex (brandLink) -- shared with the book and slides.
\colorlet{accentcolor}{basecolor}
\colorlet{symbolcolor}{basecolor}

% Setup hyperref package, and colours for links
\if@showLinks
	\hypersetup{%
		breaklinks
	}%
\else
	\hypersetup{%
		pdfborder = {0 0 0},
		breaklinks
	}%
\fi

% Setup fancyhdr package
\fancyhf{}
\fancyhfoffset{0em}
% Remove head rule
\renewcommand{\headrulewidth}{0pt}
\pagestyle{fancy}

% Setup CV sections
\titleformat{\section}{\Large\raggedright}{}{0em}{}[\titlerule]
\titlespacing{\section}{0pt}{2pt}{2pt}

% Configure list
\setlist[itemize,1]{label=\faAngleRight, nosep, leftmargin=2em}
\setlist[itemize,2]{label=\faAngleRight, nosep, leftmargin=1.5em}

% Setup Array : new column type
\newcolumntype{R}[1]{>{\hfill}m{#1}}

% Setup fonts
\defaultfontfeatures{Ligatures=TeX}%Mapping=tex-text
%

% Fonts are brand-wide: both come from style/brand.json via brand-fonts.tex.
% This used to branch on a `localFont` option that loaded a vendored copy of
% Source Sans Pro from data/cv/fonts/; both branches ended up calling
% \brandSetMainFont, so the option and the 1.8 MB of OTFs were dead weight.
\brandSetMainFont
\brandSetMonoFont

%New length definition
\newlength{\rightcolumnlength}
\setlength{\rightcolumnlength}{14.8cm}

\newlength{\leftcolumn}
\setlength{\leftcolumn}{2.5cm}

% Font Awesome icons aliases
\newcommand{\mailSymbol}{\faAt}
\newcommand{\locationSymbol}{\faMapMarker}
\newcommand{\infoSymbol}{\faInfo}
\newcommand{\linkedinSymbol}{\faLinkedin}
\newcommand{\mobileSymbol}{\faMobilePhone}
\newcommand{\githubSymbol}{\faGithub}
\newcommand{\youtubeSymbol}{\faYoutube}
\newcommand{\linkSymbol}{\faLink}

\newcommand\link[2]{\color{linkcolor}\href{#1}{#2}\color{Black} }

% Create a tag
% Usage: \cvtag{<tag label>}
\newcommand{\cvtag}[1]{%
	\tikz[baseline]\node[anchor=base,draw=darkGrey!70,rounded corners=0.5ex,inner xsep=1ex,inner ysep =0.55ex,text height=1.3ex,text depth=.25ex]{#1};
}

% Render author's name
% Usage: \user{<firstanme>}{<lastname>}
\newcommand\user[2]{\color{headingcolor}{\LARGE #1 \textbf{\textbf{#2}}}\color{Black}}

% Render a text with its symbol
% Usage; \socialtext{<icon>}{<label>}
\newcommand{\socialtext}[2]{\mbox{\textcolor{symbolcolor}{#1}\hspace{0.5em}#2\hspace{1em}}}

% Render a link with its symbol
% Usage; \sociallink{<icon>}{<label>}
\newcommand{\sociallink}[3]{\mbox{\textcolor{symbolcolor}{#1}\hspace{0.5em}\link{#2}{#3}\hspace{1em}}}

% Define author's name
% Usage: \name{<firstname>}{<lastname>}
% Usage: \firstname{<firstname>}
% Usage: \lastname{<lastname>}
% Usage: \familyname{<familyname>}
\newcommand*{\name}[2]{\def\@firstname{#1}\def\@lastname{#2}}
\newcommand*{\firstname}[1]{\def\@firstname{#1}}
\newcommand*{\lastname}[1]{\def\@lastname{#1}}
\newcommand*{\familyname}[1]{\def\@lastname{#1}}
\def\@familyname{\@lastname}

% Define author's tagline
% Usage: \tagline{<tag line>}
\newcommand*{\tagline}[1]{\def\@tagline{#1}}

% Define author's photo
% Usage \photo{<diameter>}{<photo>}
\newcommand{\photo}[2]{\def\@photo{#2}\def\@photodiameter{#1}}

% Render author's address
% Usage: \address{<address>}
\newcommand*{\address}[1]{\socialtext{\locationSymbol}{#1}}

% Render author's infos
% Usage: \infos{<infos>}
\newcommand*{\infos}[1]{\socialtext{\infoSymbol}{#1}}

% Render author's linked-in (optional)
% Usage: \linkedin{<linked-in-nick>}
\newcommand*{\linkedin}[1]{\sociallink{\linkedinSymbol}{https://www.linkedin.com/in/#1/}{linkedin.com/in/#1}}

% Render author's personal website (optional)
% Usage: \personalLink{<website-without-http://www.>}
\newcommand*{\personalLink}[1]{\sociallink{\linkSymbol}{http://www.#1}{#1}}


% Render author's github (optional)
% Usage: \github{<github-nick>}
\newcommand*{\github}[1]{\sociallink{\githubSymbol}{https://www.github.com/#1}{github.com/#1}}           % Github icon + URL

% Render author's youtube (optional)
% Usage: \youtube{<github-nick>}
\newcommand*{\youtube}[1]{\sociallink{\youtubeSymbol}{https://youtube.com/@#1}{youtube.com/@#1}}           % Github icon + URL

% Render author's email (optional)
% Usage: \email{<email adress>}
\newcommand*{\email}[1]{\sociallink{\mailSymbol}{mailto:#1}{#1}}

% Render author's mobile phone (optional)
% Usage: \smartphone{<mobile phone number>}
\newcommand*\smartphone[1]{\socialtext{\mobileSymbol}{#1}}

% Render author's tagline
\newcommand\resumetitle[1]{
	\ifundef{\@alternative}{
		\par{
			\bigskip\center{\Large \color{headingcolor}\textbf{#1}\color{Black}}\par
		}
		\bigskip
	}{
		\color{headingcolor}\textbf{\large{#1}}\color{black}
	}
}

\newcommand\idphoto{
	\setlength{\fboxrule}{2pt}
	\setlength{\fboxsep}{0pt}
	\textcolor{basecolor}{\fbox{\tikz{\path[fill overzoom image={\@photo}]rectangle (0.9\linewidth,0.64\linewidth)}}}%
}

% Define social entries to print in header
\newcommand{\socialinfo}[1]{\def\@socialinfo{#1}}

% Render CV header
% Needs \@firstname, \@lastname and \@tagline to be defined
\newcommand*{\makecvheader}{
\ifundef{\@alternative}{
\ifundef{\@photodiameter}{
	\begin{minipage}{\linewidth}
}{
	\begin{minipage}{\dimexpr\linewidth-\@photodiameter+2em}
		}
		\color{headingcolor}\user{\@firstname}{\@lastname}\color{black}\\
		\small{\@socialinfo}
	\end{minipage}
	\ifdef{\@photodiameter}{
		\begin{minipage}{\@photodiameter}
			\idphoto
		\end{minipage}
	}{}
	\resumetitle{\@tagline}
}{
	\ifundef{\@photodiameter}{
		\begin{minipage}{\linewidth}
	}{
		\begin{minipage}{\dimexpr\linewidth-\@photodiameter - 4.5em}
			}
			\color{headingcolor}\user{\@firstname}{\@lastname}\\
			\resumetitle{\@tagline}
			\smallskip\\
			\small{\@socialinfo}
		\end{minipage}
		\ifdef{\@photodiameter}{
			\begin{minipage}{\@photodiameter}
				\vspace{0.5cm}
				\idphoto
			\end{minipage}
		}{}
		\bigskip
	}
}

% Define a footer for CV
% Usage: \makecvfooter{<left>}{<center>}{<right>}
\newcommand*{\makecvfooter}[3]{%
	\fancyfoot{}
	\fancyfoot[L]{#1}
	\fancyfoot[C]{#2}
	\fancyfoot[R]{#3}
}

% Resume part title definition
\newcommand\sectionTitle[2]{\section{\texorpdfstring{\color{basecolor}#2\enspace \color{headingcolor}\textbf{#1}}{#1}}}

% Define the 'keywords' environment
\newenvironment{keywords}{%
	\renewcommand{\arraystretch}{1.1}

	\begin{tabular}{>{}r>{}p{13cm}}
		}{%
	\end{tabular}
}

% Render a scholarshipentry in the scolarship environment
% Usage: \scholarshipentry{<date>}{<description>}
\newcommand\keywordsentry[2]{
	\textbf{#1} &   #2\\
}

\newcolumntype{E}{>{\raggedright\arraybackslash}p{\rightcolumnlength}}

% Define the 'experiences' environment
\newenvironment{experiences}{%
	\begin{longtable}{R{\leftcolumn}|E}
		}{%
	\end{longtable}
}

% Render an experience in the experiences environment
% Usage: 
% \experience
%  {<End date>}      {<Title>}{<Enterprise>}{<Country>}
%  {<Start date}     {
%                      <Experience description (Could be a list)>
%                    }
%                    {<Technology list>}
\newcommand\experience[7]{
	\textbf{#1}    & \textbf{#2, \textsc{#3}, #4}   			   \\*
	\textbf{#5}    & \begin{minipage}[t]{\rightcolumnlength}
		#6
	\end{minipage}								   \\*
	& \footnotesize{\foreach \n in {#7}{\cvtag{\n}}} \\
}

% Render an education in the education environment
% Usage: 
% \education
%  {<End date>}      {<Title>}{<Enterprise>}{<Country>}
%  {<Start date}    {Grade} 
%                   {
%                      <Experience description (Could be a list)>
%                    }
%                    {<Technology list>}
\newcommand\education[8]{
	\textbf{#1}    & \textbf{#2, \textsc{#3}, #4}   			   \\*
	\textbf{#5}    & #6                                            \\*
	& \begin{minipage}[t]{\rightcolumnlength}
		#7
	\end{minipage}								   \\*
	& \footnotesize{\foreach \n in {#8}{\cvtag{\n}}} \\
}

\newcommand\emptySeparator{\multicolumn{2}{c}{}\\}

% Define the 'projects' environment
\newenvironment{projects}{%
	\begin{center}
		\begin{longtable}{l}
			}{%
		\end{longtable}
	\end{center}
}

% Define the 'project' entry in the 'projects' environment
% Usage:
% \project
%   {<Project name>}{<dates>}
%   {<link1> <link2>}
%   {<Project description>}
%   {<techno1>,<techno2>}
\newcommand\project[5]{
	\vspace{0.25cm}
	\begin{minipage}[t]{\dimexpr(\linewidth - 3em)}%{\dimexpr(\linewidth - 3em)}%
		\textbf{\textsc{#1}} \hfill \textsc{#2}\smallskip\\ %\newline
		#3\newline %\newline
		#4\smallskip\\%\newline
		\footnotesize{\foreach \n in {#5}{\cvtag{\n}}}
	\end{minipage}
	\\
}


\newcommand*\twocolumnsection[2]{
	\begin{minipage}[t]{\dimexpr(\linewidth/2) - 3em}
		\raggedright
		#1
	\end{minipage}
	\hfill
	\begin{minipage}[t]{\dimexpr(\linewidth/2) - 3em}
		\raggedright
		#2
	\end{minipage}
}

\newcommand*\threecolumnsection[3]{
	\begin{minipage}[t]{\dimexpr(\linewidth/4) - 2em}
		#1
	\end{minipage}
	\hfill
	\begin{minipage}[t]{\dimexpr(\linewidth/4) - 2em}
		#2
	\end{minipage}
	\hfill
	\begin{minipage}[t]{\dimexpr(\linewidth/2) + 3em}
		#3
	\end{minipage}
}

% Define the 'referencees' environment
\newenvironment{referees}{%
}{%
	\hfill
	\bigskip
}

\newcommand*\referee[5]{
	\hspace{1em}
	\begin{minipage}[t]{\dimexpr(\linewidth/3) - 3em}
		\begin{tabular}{>{}l >{}l}
			\multicolumn{2}{l}{\textbf{#1}}          \\
			\multicolumn{2}{l}{\emph{#2}}            \\%, \textsc{#3}
			\multicolumn{2}{l}{\textsc{#3}}          \\
			\quad \mailSymbol & \href{mailto:#4}{#4} \\
			\quad \faPhone    & #5                   \\
		\end{tabular}
	\end{minipage}%
}

\RequirePackage{pgffor}
\RequirePackage{accsupp}

\colorlet{accent}{basecolor} %
\colorlet{emphasis}{black}
\colorlet{heading}{black}
\colorlet{headingrule}{black}
\colorlet{subheading}{emphasis}
\colorlet{body}{black!80!white}
\colorlet{name}{heading}
\colorlet{tagline}{headingcolor}

\usetikzlibrary{arrows}


%% ========
%   1st parameter = rotation
%   2nd parameter = outer radius
%   3th parameter = inner radius
%   4th parameter = array of entries
%% ========
\newcommand{\wheelchart}[4][0]{%
	\begingroup\centering
	\def\innerradius{#3}%
	\def\outerradius{#2}%
	% Calculate total
	\pgfmathsetmacro{\totalnum}{0}%
	\foreach \value/\colour/\name in {#4} {%
			\pgfmathparse{\value+\totalnum}%
			\global\let\totalnum=\pgfmathresult%
		}%
	\begin{tikzpicture}

		% Calculate the thickness and the middle line of the wheel
		\pgfmathsetmacro{\wheelwidth}{\outerradius-\innerradius}
		\pgfmathsetmacro{\midradius}{(\outerradius+\innerradius)/2}
		\pgfmathsetmacro{\totalrot}{-90 + #1}

		% Rotate so we start from the top
		\begin{scope}[rotate=\totalrot]

			% Loop through each value set. \cumnum keeps track of where we are in the wheel
			\pgfmathsetmacro{\cumnum}{0}
			\foreach \value/\width/\colour/\name in {#4} {
					\pgfmathsetmacro{\newcumnum}{\cumnum + \value/\totalnum*360}

					% Calculate the percent value
					\pgfmathsetmacro{\percentage}{\value/\totalnum*100}
					% Calculate the mid angle of the colour segments to place the labels
					\pgfmathsetmacro{\midangle}{-(\cumnum+\newcumnum)/2}

					% This is necessary for the labels to align nicely
					\pgfmathparse{
						(-\midangle>180?"west":"east")
					} \edef\textanchor{\pgfmathresult}
					\pgfmathparse{
						(-\midangle>180?"flush left":"flush right")
					} \edef\textalign{\pgfmathresult}
					\pgfmathsetmacro\labelshiftdir{1-2*(-\midangle<180)}

					% Draw the color segments. Somehow, the \midrow units got lost, so we add 'pt' at the end. Not nice...
					\filldraw[draw=white,fill=\colour] (-\cumnum:\outerradius) arc (-\cumnum:-(\newcumnum):\outerradius) --
					(-\newcumnum:\innerradius) arc (-\newcumnum:-(\cumnum):\innerradius) -- cycle;

					% Draw the data labels
					% v1.6: Use accsupp so that the numeric number is copied/pasted too
					\draw  [*-,thin,emphasis] node [append after command={(\midangle:\midradius pt) -- (\midangle:\outerradius + 1ex) -- (\tikzlastnode)}] at (\midangle:\outerradius + 1ex) [xshift=\labelshiftdir*0.5cm,inner sep=1ex, outer sep=0pt, text width=\width,anchor=\textanchor,align=\textalign,font=\small,text=body]{\BeginAccSupp{method=pdfstringdef,ActualText={\name: \value}}\name\EndAccSupp{}};
					% Set the old cumulated angle to the new value
					\global\let\cumnum=\newcumnum
				}
		\end{scope}
		%      \draw[gray] (0,0) circle (\outerradius) circle (\innerradius);
	\end{tikzpicture}\par
	\endgroup
}
