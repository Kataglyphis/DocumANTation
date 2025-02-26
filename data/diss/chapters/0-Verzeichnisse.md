\microtypesetup{protrusion=false} % deaktiviere protusion vom microtyping Paket

% Inhaltsverzeichnis-------------------------------------------------------------------------
\cleardoublepage
\phantomsection
\pdfbookmark{Inhaltsverzeichnis}{} % wird für die Navigationsleiste in PDF-Readern benötigt
\tableofcontents% Verzeichnis erstellen

% Abkürzungen (benutzt makeindex)-------------------------------------------------------------
\phantomsection
\ifmanuskript
\addtocontents{toc}{\protect\vspace{-1ex}} % Verringert Zeilenabstand im ToC
\fi
\printglossary[type=acronyms, style=mylistBoldSymbGrouped, title=Abkürzungsverzeichnis]
\addcontentsline{toc}{chapter}{Abkürzungsverzeichnis}

% Formelzeichen (benutzt makeindex)-----------------------------------------------------------
\phantomsection
\addtocontents{toc}{\protect\vspace{-1ex}} % Verringert Zeilenabstand im ToC
\addchap{Symbolverzeichnis}
\setglossarysection{section} % wechsle zu section-level für die Utnerteilung
\printglossary[type=greek, style=mytab_SymbEinDescr, title=Griechische Symbole]
\printglossary[type=latin, style=mytab_SymbEinDescr, title=Lateinische Symbole] 


% Abbildungs-Verzeichnis-----------------------------------------------------------------------
\phantomsection
\addtocontents{toc}{\protect\vspace{-1ex}} % Verringert Zeilenabstand im ToC
\listoffigures


% Tabellen-Verzeichnis-------------------------------------------------------------------------
\phantomsection
\addtocontents{toc}{\protect\vspace{-1ex}} % Verringert Zeilenabstand im ToC
\listoftables

\microtypesetup{protrusion=true} % aktiviere protusion vom microtyping Paket