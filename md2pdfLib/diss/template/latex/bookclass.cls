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
\ProvidesClass{bookclass}
\LoadClass[a4paper,11pt,titlepage,openany,oneside]{scrbook}	% Class based on scrbook
% IM Style: Add openany,oneside to avoid blank pages after every chapter

%\RequirePackage{ngerman}										% New german orthography



%% -------------------------------
%% |          Packages           |
%% -------------------------------

\usepackage{fontspec}

% Set the main font
\setmainfont{Roboto}

\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc} % Input in ISO 8859-1 (Latin1)

% for the big tables
\usepackage{booktabs}
\usepackage{multirow}
\usepackage[table,xcdraw]{xcolor}
\usepackage[margin=25mm]{geometry}
\usepackage{ragged2e}
\usepackage{makecell}
\usepackage{tabularray}
\usepackage{tabularx}

\usepackage{ae}               % Almost european, virtual T1-Font
\usepackage{graphicx}
\usepackage{vmargin}          % Adjust margins in a simple way
\usepackage{rotating}
\usepackage{fancyhdr}         % Define simple headings
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
% Main theme color 
\definecolor{greenAccent}{RGB}{105,240,174}
\definecolor{mygreen}{rgb}{0,0.6,0}
\definecolor{mygray}{rgb}{0.5,0.5,0.5}
\definecolor{mymauve}{rgb}{0.58,0,0.82}
\definecolor{amber}{rgb}{1.0, 0.49, 0.0}
\colorlet{symbolcolor}{greenAccent}
\colorlet{linkcolor}{blue}

\usepackage[raiselinks=true,
	bookmarks=true,
	bookmarksopenlevel=1,
	bookmarksopen=true,
	bookmarksnumbered=true,
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

\newcommand\link[2]{\color{linkcolor}\href{#1}{#2}\color{blue} }

% Render a link with its symbol
% Usage; \sociallink{<icon>}{<label>}
\newcommand{\sociallink}[3]{\mbox{\textcolor{symbolcolor}{#1}\hspace{0.5em}\link{#2}{#3}\hspace{1em}}}

% Render author's github (optional)
% Usage: \github{<github-nick>}
\newcommand{\githubSymbol}{\faGithub}
\newcommand*{\github}[1]{\sociallink{\githubSymbol}{https://github.com/Kataglyphis/#1}{https://github.com/Kataglyphis/#1}}           % Github icon + URL

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
			\includegraphics[width=.3\textwidth]{md2pdfLib/book/template/latex/logos/Engine_logo.png}  % 
		\end{center}
		%\changefont{ppl}{m}{n}    % helvetica    (phv), % IM Style: palatino (ppl) 
		\vspace*{0.5cm}
		\begin{center}
			\Huge{\mytitle}\\
			\rule{0.05\textwidth}{0.5pt}\\
			\Large{\mytitleger}\\
			\vspace*{1cm}
			\huge{\myname}\\
			\small\github{GraphicsEngineVulkan}%\newline
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
				Jonas Heinle
			}
		\end{textblock}

		\begin{textblock}{10}[0,0](12,16.8)
			\large{
				\textbf{\url{www.jonasheinle.de}}
			}
		\end{textblock}
	\end{titlepage}
}



%% -------------------------------
%% |          Headings           |
%% -------------------------------
\pagestyle{fancy}
\renewcommand{\chaptermark}[1]{\markboth{\thechapter.\ #1}{}}
\fancyhf{}
%\fancyhead[LE,RO]{{\headfont\thepage}}						% Left/right header for even/odd pages
%\fancyhead[LO]{\headfont\nouppercase{\rightmark}}	% Header for left page (odd)
%\fancyhead[RE]{\headfont\nouppercase{\leftmark}}	% Header for right page (even)
\fancyhead[R]{\headfont\nouppercase{\rightmark}}   % Header for onesided Version
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.5pt}
\renewcommand{\footrulewidth}{0pt}
\fancypagestyle{plain}{%
	\fancyhf{}													% No Header and Footer fields
	\renewcommand{\headrulewidth}{0pt}
	\renewcommand{\footrulewidth}{0pt}
	\fancyfoot[C]{\thepage}
}
%% --- End of Headings ---



%% -------------------------------
%% |      Style of captions      |
%% -------------------------------
\renewcommand{\chaptername}{}

\renewcommand{\section}{%
	\@startsection{section}%
	{1}		% Structure level
	{0mm}	% Indention
	{2ex plus 1ex minus 1ex}			% Pre-Margin
	{0.5ex plus 0.5ex minus 0.5ex}		% Post-Margin
	{\chapterheadfont\Large\bfseries}	% Style
}
\renewcommand{\subsection}{%
	\@startsection{subsection}%
	{2}		% Structure level
	{0mm}	% Indention
	{1.5ex plus 1ex minus 0.5ex}		% Pre-Margin
	{0.3ex plus 0.3ex minus 0.3ex}		% Post-Margin
	{\chapterheadfont\large\bfseries}	% Style
}
\renewcommand{\subsubsection}{%
	\@startsection{subsubsection}%
	{3}		% Structure level
	{0mm}	% Indention
	{1.5ex plus 1ex minus 0.5ex}			% Pre-Margin
	{0.2ex plus 0.2ex minus 0.2ex}			% Post-Margin
	{\chapterheadfont\normalsize\bfseries}	% Style
}
\renewcommand{\paragraph}{%
	\@startsection{paragraph}%
	{4}		% Structure level
	{0mm}	% Indention
	{1.3ex plus 1ex minus 0.3ex}			% Pre-Margin
	{0.2ex plus 0.2ex minus 0.2ex}			% Post-Margin
	{\chapterheadfont\normalsize\bfseries}	% Style
}
\renewcommand{\subparagraph}{%
	\@startsection{subparagraph}%
	{5}		% Structure level
	{0mm}	% Indention
	{1ex plus 1ex minus 0.2ex}				% Pre-Margin
	{0.1ex plus 0.1ex minus 0.1ex}			% Post-Margin
	{\chapterheadfont\normalsize\bfseries}	% Style
}
%% --- End of captions style ---



%% ---------------------------------
%% |   Style of chapter captions   |
%% ---------------------------------
\newlength{\chapnolen}
\newlength{\chapparlen}
\newsavebox{\chapno}
\renewcommand{\@makechapterhead}[1]{
	%\vspace*{0.2\textheight}
	%\vskip 15\p@
	{\parindent \z@ \raggedright \normalfont
			\ifnum \c@secnumdepth >\m@ne
				\if@mainmatter
					\savebox{\chapno}{\chapterheadfont\huge\bfseries \thechapter.}
					\settowidth{\chapnolen}{\usebox{\chapno}}
					\parbox[t]{\chapnolen}{\usebox{\chapno}}\nobreak\leavevmode
				\fi
			\fi
			\interlinepenalty\@MM
			\setlength{\chapparlen}{\textwidth}
			\addtolength{\chapparlen}{-1.0\chapnolen}
			\addtolength{\chapparlen}{-2ex}
			\leavevmode\nobreak
			\parbox[t]{\chapparlen}{\raggedright\chapterheadfont\huge \bfseries #1\par\nobreak}
			%\vskip 40\p@
		}}

\renewcommand{\@makeschapterhead}[1]{
	\vspace*{50\p@}
	{\parindent \z@ \raggedright
		\normalfont
		\interlinepenalty\@M
		\chapterheadfont \huge \bfseries  #1\par\nobreak
		\vskip 40\p@
	}
}
%% --- End of chapter captions style ---



%% ---------------------------------
%% |  Style of content directory   |
%% ---------------------------------
\let\oldtableofcontents\tableofcontents
\renewcommand{\tableofcontents}{{\pdfbookmark{\contentsname}{\contentsname}\chapterheadfont\oldtableofcontents}}
\let\@olddottedtocline\@dottedtocline
\renewcommand{\@dottedtocline}[5]{\@olddottedtocline{#1}{#2}{#3}{#4}{\chapterheadfont #5}}
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
