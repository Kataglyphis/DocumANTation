\chapter{Literatur-, Abkürzungs- und Symbolverzeichnis}
\label{cha:Literaturverzeichnis-erstellen}

\section{Literaturverzeichnis}
\label{sec:Literaturverzeichnis}
Um das Literaturverzeichnis im IPA-Stil zu erstellen, wurden eigene Bib-Macros erstellt, welche ihr in (./Vorlagen/mypackages/bibl) findet. Die biblatexIPA.sty wird in der thesis.cls an dieser Stelle geladen
%
\begin{small}
\begin{lstlisting}
% Literaturstil IPA----------------
\RequirePackage{md2pdfLib/diss/template/mypackages/bibl/biblatexIPA}
\addbibresource{data/diss/latex/Literatur.bib}		% hier deine .bib Datei verlinken
\end{lstlisting}
\end{small}
%
Solltet ihr den Pfad der biblatexIPA.sty ändern, müsst ihr in selbiger Datei die Pfade anpassen.
%
\begin{small}
\begin{lstlisting}
\RequirePackage[backend=biber,
bibstyle=md2pdfLib/diss/template/mypackages/bibl/iso-authoryearIPA, 	% <-- Hier Pfad ändern
citestyle=md2pdfLib/diss/template/mypackages/bibl/iso-authoryearIPA, 	% <-- Hier Pfad ändern
datamodel = md2pdfLib/diss/template/mypackages/bibl/iso-authoryearIPA,	% <-- Hier Pfad ändern
]{biblatex} 	% eigene .bib Enträge
\end{lstlisting}
\end{small}
%
In den einzelnen iso-authoryear.* Dateien könnt ihr noch die provide Pfade anpassen, um Warnungen zu verhindern.

%noch der nocite Befehl um alle .bib Einträge aufzurufen
\nocite{*}

\section{Hinweise für die Citavi-Datenbank + Export zu \LaTeX}
\label{sec:Hinweise-CITAVI}

\begin{itemize}[noitemsep]
	\item Kurzbelege (shorthands) ohne Jahresangabe, Latex fügt diese aus den Jahres-Feldern hinzu.
	\item Falls keine Jahresangaben vorhanden, dann bitte o.\,J. in Jahresfeld eintragen
	\item Kurzbelege werden in LaTeX immer bevorzugt genutzt
	\item Kurzbelegfunktion aktivieren (Extras->Optionen->Zitation)
	\item Kurzbeleg-Makro KurzbelegeLaTeX.ckd importieren und Kurzbelege automatisch generieren lassen
	\item Manuelle Änderungen von Kurzbelegen (In die Zelle gehen und F9 drücken->Kurzbeleg anpassen)
	\item Datumsangaben in deutschen Format dd.mm.yyy \bzw für Zeitraum dd.mm.yyyy-dd.mm.yyyy (ohne Leerzeichen!). Ein Makro (DeclareSourcemap) wandelt alles zunächst ins ISO Format um, bevor es von biblatex verarbeitet wird.
	\item Kopiere die Exportvorlage exportIPAStyle.CitaviTX in C:/Users/\%USERNAME\%/AppData/Local/Swiss Academic Software/Citavi 6/Settings/Mappings
	\item Bei dem Export \textbf{keine} der drei BibTeX-Optionen nutzen!
\end{itemize}


\section{Cite-Befehle}
\label{sec:Cite-Befehle}
\lstinline[language={[LaTeX]TeX},basicstyle=\ttfamily]{\cite} -> \cite{Bauer.2021} 
\noindent
\lstinline[language={[LaTeX]TeX},basicstyle=\ttfamily]{\parencite} -> \parencite{Bauernhansl.2017}
\noindent
\lstinline[language={[LaTeX]TeX},basicstyle=\ttfamily]{\textcite} -> \textcite{Bauernhansl.2017}

Achtung Bug in \lstinline[language={[LaTeX]TeX},basicstyle=\ttfamily]{\textcite} bei Patenten (und vermutlich auch Gesetzen). Als derzeitigen Workaround könnt ihr \lstinline[language={[LaTeX]TeX},basicstyle=\ttfamily]{\textcitepatent} verwenden.

\textcitepatent{Cudazzo.2013}

\section{Symbol- und Abkürzungsverzeichnis erstellen}
\label{sec:Symbol-undAbkuerzungsverzeichnis-erstellen}

\label{subsec:Beispiel-fuer-Abkuerzungen-und-Symbole}
Neue Funktion in dieser Vorlage ist das Abkürzungs- und Symbolverzeichnis. Die Einträge werden im Ordner ./Indexing definiert.
Wenn ihr die Symbole sauber trennen wollt, dann nutzt type=latin für lateinische und type=greek für die griechischen. Ganz wichtig!

Eine Abkürzung, wie \zB für Computational Fluid Dynamics \gls{acro:CFD} wird folgendermaßen in der Abkuerzungen.tex definiert.

\begin{small}
\begin{lstlisting}
\newglossaryentry{⟨label ⟩}{type=\acronymtype,
name={⟨abbrv ⟩},
description={⟨long⟩},
text={⟨abbrv ⟩},
first={⟨long⟩ (⟨abbrv ⟩)},
plural={⟨abbrv ⟩\glspluralsuffix},
firstplural={⟨long⟩\glspluralsuffix\space (⟨abbrv ⟩\glspluralsuffix)},
⟨key-val list⟩}
\end{lstlisting}
\end{small}

\begin{small}
\begin{lstlisting}
\newglossaryentry{acro:IPA}{type=\acronymtype,
	name={IPA},
	description={Fraunhofer-Institut für Produktionstechnik und Automatisierung},
	text={IPA},
}
\end{lstlisting}
\end{small}
Das Schubmodul \gls{symb:Schubmodul} ist ein lateinisches Symbol und wird über type=latin dem lateinischen Verzeichnis zugeordnet.

\begin{small}
\begin{lstlisting}
% G - Schubmodul
\newglossaryentry{symb:Schubmodul}{
	name={\ensuremath{G}},
	description={Schubmodul},
	symbol={MPa},
	type=latin
}
\end{lstlisting}
\end{small}
Die Kreisfrequenz \gls{symb:omega} ist ein griechisches Symbol und wird über type=greek dem griechischen Verzeichnis zugeordnet.

\begin{small}
\begin{lstlisting}
% W-Omega
\newglossaryentry{symb:omega}{
	name={\ensuremath{\omega}},
	description={Kreisfrequenz},
	symbol={\si{\per\second}},
	type=greek
}
\end{lstlisting}
\end{small}
Es können beliebig viele Verzeichnisse erstellt werden. Folgt dem entsprechenden Code und führt zusätzliche Makros in die TeXstudio Erstellungsprozedur ein.

