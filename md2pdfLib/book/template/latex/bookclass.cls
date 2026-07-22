%% Based on wissdoc.cls by Roland Bless, 1996-2001
%% bless@telematik.informatik.uni-karlsruhe.de
%%
%% Adapted by: Timo Rohrberg, 2009
%% timo.rohrberg@student.kit.edu
%%
%% Additions by: Thorsten Haberecht, IPD - Chair Prof. Böhm, 2010
%% thorsten.haberecht@kit.edu
%% Additions by: Jonas Heinle, 2023 for own book project

\NeedsTeXFormat{LaTeX2e}										% We do need LaTeX2e
\ProvidesClass{md2pdfLib/book/template/latex/bookclass}
\LoadClass[a4paper,11pt,titlepage,openany,oneside]{scrbook}	% Class based on scrbook
\PassOptionsToPackage{nopatch=footnote}{microtype}
% IM Style: Add openany,oneside to avoid blank pages after every chapter

%\RequirePackage{ngerman}										% New german orthography



%% -------------------------------
%% |          Packages           |
%% -------------------------------

\usepackage{fontspec}

% Main font — single source of truth: style/brand.json
\input{brand-fonts.tex}
\brandSetMainFont

\usepackage{booktabs}
\usepackage{multirow}
\usepackage[table,xcdraw]{xcolor}
\usepackage[margin=25mm]{geometry}
\usepackage{ragged2e}
\usepackage{makecell}
\usepackage{tabularray}
\usepackage{tabularx}

\usepackage{graphicx}
\usepackage{vmargin}          % Adjust margins in a simple way
\usepackage{rotating}
\usepackage[automark,headsepline=false,footsepline=false,singlespacing=true]{scrlayer-scrpage}
%\usepackage{subfigure}
\usepackage{caption}
\usepackage{subcaption}
\usepackage{url}
\usepackage[absolute,overlay]{textpos}
\usepackage{tikz}
\usepackage{algorithm}		  % Code-Listings
\usepackage{algorithmic}	  % Code-Listings
% see http://www.ctan.org/tex-archive/macros/latex/contrib/algorithm2e/algorithm2e.pdf
% for more sophisticated algorithm listings

% define for real number symbol
\usepackage{amssymb}
\usepackage{amsmath}
\usepackage{amsthm}

\theoremstyle{definition}
\newtheorem{definition}{Definition}[section]

\usepackage{enumitem}

% included for importing paths to my .pdf_tex files
\usepackage{import}
\usepackage{transparent}

\usepackage{fontawesome} % for icons

%% -------------------------------
%% |         New colors          |
%% -------------------------------
% Main theme color — single source of truth: style/brand.json
% (defines brandAccent + the greenAccent/myGreenAccent/basecolor aliases).
\input{brand-colors.tex}
% The `listings` palette (c_code_style.tex) uses the brandSyntax* colours from
% brand-colors.tex, so hand-written listings match pandoc-rendered code blocks.
\colorlet{symbolcolor}{greenAccent}

\usepackage[raiselinks=true,
	bookmarks=true,
	bookmarksopenlevel=1,
	bookmarksopen=true,
	bookmarksnumbered=true,
	hyperfootnotes=false,
	hyperindex=true,
	plainpages=false,
	pdfpagelabels=true,
	pdfborder={0.5 0.5 0.5},
	colorlinks=true,
	allbordercolors=greenAccent,
	linkbordercolor=greenAccent,
	citebordercolor=greenAccent]{hyperref}

%% IM Packages
\usepackage{setspace} % 1.5 line spacing
\onehalfspacing
\setlength{\footheight}{\baselineskip}

%\usepackage{natbib} % Bibliography style

\usepackage{comment}
\usepackage{adjustbox}
\usepackage[most]{tcolorbox}
\newtcolorbox[blend into=figures]{myfigure}[2][]{float=htb,title={#2},#1}
% this is for rotate tables
\usepackage{lscape}
\usepackage{wrapfig}

%% --- End of Packages ---



%% -------------------------------
%% |        Declarations         |
%% -------------------------------
\DeclareGraphicsExtensions{.svg}
%% --- End of Declarations ---


%% -------------------------------
%% |         New commands        |
%% -------------------------------
%\newcommand{\changefont}[3]{\fontfamily{#1} \fontseries{#2} \fontshape{#3} \selectfont}
%\renewcommand*{\headfont}{\slshape}
%\newcommand{\captionfont}{}
\newcommand{\chapterheadfont}{}
\newcommand{\blankpage}{
	\clearpage{\pagestyle{empty}\cleardoublepage}
}

\newcommand\link[2]{\color{linkcolor}\href{#1}{#2}\color{black} }

% Render a link with its symbol
% Usage; \sociallink{<icon>}{<label>}
\newcommand{\sociallink}[3]{\mbox{\textcolor{symbolcolor}{#1}\hspace{0.5em}\link{#2}{#3}\hspace{1em}}}

% Render author's github (optional)
% Usage: \github{<github-nick>}
\providecommand{\githubSymbol}{\faGithub}
\providecommand{\githubBase}{https://github.com/Kataglyphis}
\providecommand*{\github}[1]{\sociallink{\githubSymbol}{\githubBase/#1}{\githubBase/#1}}

%% --- End of New Commands ---



%% -------------------------------
%% |      Globale Settings       |
%% -------------------------------
\setcounter{secnumdepth}{3} % Numbering also for \subsubsections
\setcounter{tocdepth}{3}    % Register \subsubsections in content directory

\setpapersize{A4}
\setmarginsrb{3cm}{1cm}{3cm}{1cm}{6mm}{7mm}{5mm}{15mm}

\parindent 0cm                     % Do not indent beginning of paragraph
\parskip1.5ex plus0.5ex minus0.5ex % Margin between paragraphs
%% --- End of global Settings ---


%% -------------------------------
%% |          Title page         |
%% -------------------------------

% Personal info — use \providecommand so metadata can override
\providecommand{\myauthor}{Jonas Heinle}
\providecommand{\myurl}{www.jonasheinle.de}
\providecommand{\mytitle}{}
\providecommand{\mytitleger}{}
\providecommand{\myname}{Jonas Heinle}
\providecommand{\submissiontime}{}
\providecommand{\reviewerone}{}
\providecommand{\reviewertwo}{}
\providecommand{\titlelogo}{md2pdfLib/book/template/latex/logos/Engine_logo.png}

% coordinates for the bg shape on the titlepage
\newcommand{\mydiameter}{20}
\newcommand{\xone}{-15}
\newcommand{\xtwo}{160}
\newcommand{\yone}{15}
\newcommand{\ytwo}{-253}

% Define the custom \maketitle command
\renewcommand{\maketitle}{
	\begin{titlepage}
		% bg shape
		\begin{tikzpicture}[overlay]
			\draw[color=gray]
			(\xone mm, \yone mm)
			-- (\xtwo mm, \yone mm)
			arc (90:0:\mydiameter pt)
			-- (\xtwo mm + \mydiameter pt , \ytwo mm)
			-- (\xone mm + \mydiameter pt , \ytwo mm)
			arc (270:180:\mydiameter pt)
			-- (\xone mm, \yone mm);
		\end{tikzpicture}
		\begin{center}
			\includegraphics[width=.3\textwidth]{\titlelogo}
		\end{center}
		%\changefont{ppl}{m}{n}    % helvetica    (phv), % IM Style: palatino (ppl) 
		\vspace*{0.5cm}
		\begin{center}
			\Huge{\mytitle}\par
			\rule{0.05\textwidth}{0.5pt}\par
			\Large{\mytitleger}\par
			\vspace*{1cm}
			\huge{\myname}\par
			\small\github{GraphicsEngineVulkan}
			\vspace*{1cm}
		\end{center}
		%\vspace*{1cm}
		\Large{
			% \begin{center}
			% 	\begin{tabular}[ht]{l c l}
			% 		Reviewer:        & \hfill & \reviewerone \\
			% 		Second Reviewer: & \hfill & \reviewertwo \\
			% 	\end{tabular}
			% \end{center}
		}

		\vspace{1.cm}
		\begin{center}
			\large{\submissiontime}
			% \iflanguage{english}{Duration:}{Bearbeitungszeit:} \timestart \hspace*{0.25cm}
			% -- \hspace*{0.25cm} 
			% \timeend}
		\end{center}

		\begin{textblock}{10}[0,0](5,16.8)
			\large{
				\myauthor
			}
		\end{textblock}

		\begin{textblock}{10}[0,0](12,16.8)
			\large{
				\textbf{\url{\myurl}}
			}
		\end{textblock}
	\end{titlepage}
}



%% -------------------------------
%% |          Headings           |
%% -------------------------------
\pagestyle{scrheadings}
\clearpairofpagestyles
\renewcommand{\chaptermark}[1]{\markright{\thechapter.\ #1}}
\ohead{\headmark}
\cfoot{\pagemark}
%% --- End of Headings ---



%% -------------------------------
%% |    Section Formatting        |
%% -------------------------------
\renewcommand{\chaptername}{}

\setkomafont{chapter}{\chapterheadfont\huge\bfseries}
\setkomafont{section}{\chapterheadfont\Large\bfseries}
\setkomafont{subsection}{\chapterheadfont\large\bfseries}
\setkomafont{subsubsection}{\chapterheadfont\normalsize\bfseries}
\setkomafont{paragraph}{\chapterheadfont\normalsize\bfseries}
\setkomafont{subparagraph}{\chapterheadfont\normalsize\bfseries}

\RedeclareSectionCommand[
	indent=0mm,
	beforeskip=2ex plus 1ex minus 1ex,
	afterskip=0.5ex plus 0.5ex minus 0.5ex
]{section}
\RedeclareSectionCommand[
	indent=0mm,
	beforeskip=1.5ex plus 1ex minus 0.5ex,
	afterskip=0.3ex plus 0.3ex minus 0.3ex
]{subsection}
\RedeclareSectionCommand[
	indent=0mm,
	beforeskip=1.5ex plus 1ex minus 0.5ex,
	afterskip=0.2ex plus 0.2ex minus 0.2ex
]{subsubsection}
\RedeclareSectionCommand[
	runin=false,
	afterindent=false,
	indent=0mm,
	beforeskip=1.3ex plus 1ex minus 0.3ex,
	afterskip=0.2ex plus 0.2ex minus 0.2ex
]{paragraph}
\RedeclareSectionCommand[
	runin=false,
	afterindent=false,
	indent=0mm,
	beforeskip=1ex plus 1ex minus 0.2ex,
	afterskip=0.1ex plus 0.1ex minus 0.1ex
]{subparagraph}

\renewcommand*{\chapterformat}{\thechapter\autodot\enskip}
\renewcommand*{\chapterlinesformat}[3]{%
	\raggedchapter
	\IfArgIsEmpty{#2}{#3}{\@hangfrom{#2}{#3}}%
}
%% --- End of headings ---



%% ---------------------------------
%% |  Style of content directory   |
%% ---------------------------------
\let\oldtableofcontents\tableofcontents
\renewcommand{\tableofcontents}{{\pdfbookmark{\contentsname}{\contentsname}\chapterheadfont\oldtableofcontents}}
\renewcommand*{\@pnumwidth}{3em}
\let\@olddottedtocline\@dottedtocline
\renewcommand{\@dottedtocline}[5]{\@olddottedtocline{#1}{#2}{#3}{#4}{\chapterheadfont #5}}
\DeclareTOCStyleEntry[pagenumberwidth=3em]{tocline}{chapter}
\DeclareTOCStyleEntry[numwidth=30pt,pagenumberwidth=3em]{tocline}{section}
\DeclareTOCStyleEntry[numwidth=40pt,pagenumberwidth=3em]{tocline}{subsection}
%% --- End of content directory style ---


%% ----------------------------------
%% |  Style of appendix numbering   |
%% ----------------------------------
\renewcommand\appendix{\par
	\setcounter{section}{0}% 
	\setcounter{subsection}{0}% 
	\setcounter{figure}{0}%
	\renewcommand\thesection{\Alph{section}}% 
	\renewcommand\thefigure{\Alph{section}.\arabic{figure}}
	\renewcommand\thetable{\Alph{section}.\arabic{table}}}
%% --- End of appenix numbering style ---


%% **** END OF CLASS ****
