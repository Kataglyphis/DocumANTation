%-----------------------------------------------------------------------------------------------------
% In dieser Dokumentenklasse werden zwei verschiedene Stile - "manuskript" und publishing" - definiert, um der jeweiligen Situation ein geeignetes Layout zur Verfügung zu Stellen
% Ihr könnt natürlich hier Settings modifizieren und einbauen.

%-----------------------------------------------------------------------------------------------------
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{md2pdfLib/diss/template/thesis}[2021/07/01 - v1.0.0 LaTeX Dokumentklasse für IPA-Dissertationen by Nico Güttler]


% Options-Handling-----------------------------------------------------------------------------------

% 'manuskript'
\newif\ifmanuskript\manuskriptfalse

\DeclareOption{manuskript}{
	\PassOptionsToClass{
		a4paper, 						% Papierformat
		fontsize=12pt, 					% Schriftgröße (12-14pt laut Vorlage, 12pt könnte aber zu klein werden)
		twoside=on,						% zweiseitig
		headings=normal, 				% Größe der Überschriften verkleinern
		listof=totoc, 					% Verzeichnisse im Inhaltsverzeichnis aufführen
		numbers=noenddot,				% keine abschließenden Punkte bei Kapitelzahlen
		openany,						% Kapitel werden auf der nächstbesten Seite geöffnet. Twosided sonst nur auf ungeraden Seitenzahlen
	}{scrbook}	
	\manuskripttrue
}

% 'publishing'
\newif\ifpublishing\publishingfalse

\DeclareOption{publishing}{
	\PassOptionsToClass{
		a4paper,						% Papierformat
		fontsize=12pt, 					% Schriftgröße
		twoside=on,						% zweiseitig
		headings=normal, 				% Größe der Überschriften verkleinern
		listof=totoc, 					% Verzeichnisse im Inhaltsverzeichnis aufführen
		numbers=noenddot,				% keine abschließenden Punkte bei Kapitelzahlen
		openany,						% Kapitel werden auf der nächstbesten Seite geöffnet. Twosided sonst nur auf ungeraden Seitenzahlen
	}{scrbook}
	\publishingtrue		
}

% Unknown Options-----------------------------------------------------------------------------------
\DeclareOption*{%
	\ClassWarning{md2pdfLib/diss/template/thesis}{Unknown option `\CurrentOption'}} 
		
% Execute Options-----------------------------------------------------------------------------------
\ProcessOptions\relax %führt die oben gesetzten Optionen aus

% Unterdrückung unnötiger Warnungen------------------------------------------------------------------
\RequirePackage[immediate]{silence}
\WarningFilter{remreset}{The remreset package}
\WarningFilter{latex}{You have requested, on input line 22, version}

% Lade Grund-Klasse-----------------------------------------------------------------------------------
\LoadClass{scrbook}

%Mathe Paket
% Nötiger pandoc fix
\disable@package@load{amssymb}{}%
\RequirePackage{unicode-math} % Paket muss sehr früh geladen werden, sonst gibt es Fehlermeldungen

% Sprackpaket + Umlaute--------------------------------------------------------------------------------
\RequirePackage[main=ngerman,ngerman]{babel} 			% Sprachpaket [Hauptsprache, Zweitsprache]
\RequirePackage[babel, german=guillemets]{csquotes}		% Zitate und Silbentrennung
\RequirePackage[utf8]{luainputenc}						% Enconding
\RequirePackage{fontspec}								% Für Font settings!!!! Loaded by unicode-amth
\RequirePackage{textcomp}

% Schriftsettings------------------------------------------------------------------------------------
% Lade Frutiger Font--------------------------------------
% Wenn ihr die Schriftarten aus ./Vorlagen/fonts (alle markieren, als Admin installieren) installiert, könnt ihr die folgenden Zeilen auskommentieren. Diese laden den Fonts direkt aus dem ./Vorlagen/fotns ordner lokal
\setmainfont{FrutigerFhG}[
	Path=md2pdfLib/diss/template/fonts/Frutiger/,
	Extension = .ttf,
	UprightFont=*-Roman,
	BoldFont=*-Bold,		
	ItalicFont=*-Italic,
	BoldItalicFont=*-BoldItalic,
]
% Der LT COM Font wird an der ein oder anderen Stelle gewollt verwendet (Fraunhofer Vorgabe)
\newfontfamily{\FrutigerLTCOM}{FrutigerLTCom}[
	Path=md2pdfLib/diss/template/fonts/Frutiger/,
	Extension = .ttf,
	UprightFont=*-Light, 	% Frutiger 
	BoldFont=*-Bold,		
	ItalicFont=*-LightItalic,
	BoldItalicFont=*-BoldItalic,
]
\setkomafont{disposition}{\FrutigerLTCOM\rmfamily}	% Ändert die Schriftart für Chapter, Section usw. mit einem Befehl
% \setmathfont{GFS Neohellenic Math} %Ändert den Mathefont


% Änderung der Schriftgröße für Kapitel etc., Fraunhofer hätte gerne alle gleich groß, außer Kapitel
\setkomafont{chapter}{\Huge} 
\setkomafont{section}{\large}
\setkomafont{subsection}{\large}
\setkomafont{subsubsection}{\large}
\setkomafont{paragraph}{\large}
\setkomafont{subparagraph}{\large}

% Änderung des Abstands zwischen Chapter/Section etc. und Text. Will Fraunhofer so haben!
\renewcommand*\chapterformat{\makebox[2cm][l]{\thechapter\autodot\hfil}}
\renewcommand*\sectionformat{\makebox[2cm][l]{\thesection\autodot\hfil}}
\renewcommand*\subsectionformat{\makebox[2cm][l]{\thesubsection\autodot\hfil}}
\renewcommand*\subsubsectionformat{\makebox[2cm][l]{\thesubsubsection\autodot\hfil}}
\RedeclareSectionCommand[beforeskip=-1\baselineskip]{chapter}

\RequirePackage{amsmath}
\RequirePackage{nicefrac}						% schöne Brüche für z.B. im Text

% Weitere Typo Settings--------------------------------------------------------------------------------
\setcounter{secnumdepth}{3} 				% Setzt Nummerierung bis Ebene "3"
\setcounter{tocdepth}{3}					% Nummerierung von bis Ebene "3" auch im Inhaltsverzeichnis
\RequirePackage[all]{nowidow}				% Vermeindung von Schusterjungen, Hurenkinder etc
\RequirePackage{setspace} 	% Packet zur Definition des Zeilenabstandes -> Zeilenabstand 1,5 Zeilen
\linespread{1.25} %brauch man um Wordspacing 1.5 zu erhalten
\RequirePackage[activate={true,nocompatibility}, final,tracking=true, factor=1100,babel=true]{microtype} 					% verbesserter Randausgleich
\RequirePackage[hyphens]{xurl} 				% passt lange URLs an, z.B. für das Literaturverzeichnis
\urlstyle{same}
\raggedbottom  % Sorgt beim Dokumenttyp book dafür, daß kein Ausgleich des unteren Seitenrandes durch Dehnung der Absatzabstände durchgeführt wird

% Grafiken-----------------------------------------------------------------------------------------------------
\RequirePackage[final]{graphicx} 			% Einbinden von JPG-Grafiken ermölichen
\RequirePackage[font=small]{caption}		% verbiegt den Link von Float-Umgebungen 
\RequirePackage{subcaption}
\RequirePackage{float}						% Fließumgebung
\graphicspath{% hier liegen die Bilder des Dokuments
			{data/diss/graphics/images/}
			{data/diss/graphics/plots/}
			{data/diss/graphics/drawings/}
			}

%Tabellen-----------------------------------------------------------------------------------------------------
\RequirePackage{array}				% extended implementation of the array and tabular environments
\RequirePackage{tabularx}			% Basis Tabellenpaket
\RequirePackage{multirow}			% Zellen Zusammenfassen etc.
\RequirePackage{booktabs} 			% Verbesserte horizontale Linien in Tabellen
\RequirePackage{longtable}			% Lange Tabellen, meistens für seitenübergreifende genutzt
\RequirePackage{pdflscape}			% Paket für Querformat Tabellen
\RequirePackage{enumitem}			% control basic list environments: enumerate, itemize and description

%Neue Spaltentypen mit Zeilenumbruch für Tabellen
\newcolumntype{L}[1]{>{\raggedright\let\newline\\\arraybackslash\hspace{0pt}}p{#1}}
\newcolumntype{C}[1]{>{\centering\let\newline\\\arraybackslash\hspace{0pt}}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\let\newline\\\arraybackslash\hspace{0pt}}p{#1}}

%verschiedene Pakete für Latex Codes--------------------------------------------------------
\RequirePackage{calc}				% Führt Rechenoperationen in {} ein z.B. \{textwidth -4pt}
\RequirePackage{xpatch}				% kann Befehle umpatchen
\RequirePackage{xargs}  			% Use more than one optional parameter in a new commands
\RequirePackage{etoolbox}			% toolbox of programming facilities

\RequirePackage[locale = DE, per-mode=symbol,detect-all, separate-uncertainty, range-phrase ={ bis }]{siunitx}			% Paket für SI-Einheiten (FIXME detect-all könnte probleme machen bei SIRange)

% Spezielle Nummerierung von Grafiken, Tabel etc. ------------------------------------------------------
\numberwithin{equation}{chapter} 	%	Kapitel.Nummer-der-Gleichung
\numberwithin{figure}{chapter}		%	Kapitel.Nummer-der-Figure
\numberwithin{table}{chapter}		%	Kapitel.Nummer-der-Tabelle

% Literaturstil IPA-------------------------------------------------------------------------------------
\RequirePackage{md2pdfLib/diss/template/mypackages/bibl/biblatexIPA}

\addbibresource{md2pdfLib/diss/template/Literatur.bib}			% hier deine .bib Datei verlinken
%\addbibresource{Literaturverzeichnis/Literatur2.bib}  		% du kannst auch mehrere einbinden


% PDF-Layout und Funktionalität -----------------------------------------------------------------------------------------------------
\RequirePackage{hyperref}
\hypersetup{bookmarksopen=true,
			bookmarksnumbered = true, 	% show numbers
			bookmarksopenlevel=2,		% Festlegen der Tiefe der Bookmarks (2==section)
			pdfstartview={FitV},		% Fits the height of the page to the window.
			pdfnewwindow=true, 			% links in new PDF window
			pdfpagelayout=SinglePage, 	% Displays a single page; advancing flips the page
			colorlinks=true,			% Farben aktivieren, keine Kästchen drum rum
			linkcolor={[rgb]{0.125, 0.4, 0.705882}},
			citecolor={[rgb]{0.17, 0.63, 0.17}},
			filecolor={[rgb]{1.0, 0.36, 0.05}},
			urlcolor={[rgb]{0.89, 0.47, 0.76}},
			hidelinks, % Wer es bunt haben will zum Schreiben, muss dieses Feld auskommentieren
}
%-------------------------------------------------------------------------------------------

% Sonstige Pakete--------------------------------------------------------------------------------------
\RequirePackage[table, dvipsnames]{xcolor}	% Farbigen Text ermöglichen: no options allowed because of hyperref

\RequirePackage[german, textsize=footnotesize, backgroundcolor=blue!20!white, colorinlistoftodos,prependcaption, bordercolor=red]{todonotes} %Todo Notes

% Abkürzungen, Formelzeichen & Symbole, Index---------------------------------------------------------
\RequirePackage{md2pdfLib/diss/template/mypackages/glossary/glossaryNCG}
\DeclareTOCStyleEntry[indent=0pt]{tocline}{figure} % Abbildungsverzeichnis Einrücken verhindern
\DeclareTOCStyleEntry[indent=0pt]{tocline}{table} % Tabellenverzeichnis Einrücken verhindern


% Layout der Kopf und Fußzeile-------------------------------------------
\RequirePackage[headsepline=1pt, automark, singlespacing]{scrlayer-scrpage}
\pagestyle{scrheadings}

\clearpairofpagestyles 									%Lösche Plain und Headings style komplett

\KOMAoptions{
	headsepline=true,   								% header line
	footsepline=false,          						% footer line
	cleardoublepage=empty,  							% set empty pages
	plainheadsepline=false, 							% deactivate header line for plain pages
	plainfootsepline=false								% deactivate footer for plain pages
}

\setkomafont{pagehead}{\FrutigerLTCOM\normalfont}		% Die Schriftart im Header ändern
\setkomafont{pagenumber}{\FrutigerLTCOM\normalfont}		% Die Schriftart im Header ändern

\automark[chapter]{chapter} 							% Linke Seite Kapitel Rechte Seite Section
\ihead{\headmark}										% Was in Kopfzeile stehen soll
\ohead{\pagemark}										% Seitenzahl außen, oben rechtsn

\RequirePackage{pdfpages} % PDFs einbinden; muss nach xcolor geladen werden, da sonst Fehler

% Code Listings (bitte dann herauslöschen)----------------------------------------------------
\RequirePackage{listings}
\lstset{%
	basicstyle=\small\ttfamily,language={[LaTeX]TeX},   numbersep=2mm, numbers=left, numberstyle=\small, % number style
	breaklines=true,frame=single,framexleftmargin=10mm, xleftmargin=10mm,
	prebreak = \raisebox{0ex}[0ex][0ex]{\ensuremath{\hookleftarrow}},
	backgroundcolor=\color{green!5},frameround=fttt,escapeinside=??,
	rulecolor=\color{red},
	morekeywords={% Give key words h
		maketitle},
	keywordstyle=\color[rgb]{0,0,1},                    % keywords
	commentstyle=\color[rgb]{0.133,0.545,0.133},    % comments
	stringstyle=\color[rgb]{0.627,0.126,0.941}  % strings
	%columns=fullflexible   
}%

% delete me later
\RequirePackage{blindtext}

% Hier könntest du das geometry-Paket einbinden. Dadurch werden alle KOMA Satzspiegel Berechnungen überschrieben--------------------------
\ifmanuskript
	\RequirePackage[a4paper, asymmetric, left=20mm, right=20mm, bottom=30mm, top=30mm, bindingoffset=5mm]{geometry} %
\else
	\RequirePackage[a4paper, asymmetric, left=20mm, right=20mm, bottom=30mm, top=30mm, bindingoffset=10mm]{geometry} %
\fi

% Nachträgliche Verbesserungen von verschiedenen Paketen----------------------------------------------
\RequirePackage{scrhack} %muss ganz am Ende geladen werden, da es diverse macros umdefiniert

\renewcommand{\maketitle}{%
  \begin{titlepage}
    \input{md2pdfLib/diss/template/titlepage.tex}
  \end{titlepage}
}

\endinput
%% End of file `thesis.cls'. 