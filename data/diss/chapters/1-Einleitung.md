\chapter{Einleitung}
\label{cha:Einleitung}

\section{Das \LaTeX und TeXstudio-Setup}
\label{Texstudio-Setup}

Für einen (halbwegs) problemlosen Einstieg in die Vorlage empfehle ich folgende Schritte zu beachten!

\begin{itemize}[noitemsep]
	\item Benutze MiKTeX \url{https://miktex.org/download} (on-the-fly package installation) + TeXstudio \url{https://www.texstudio.org}
	\item Lade das TeXstudio-Profil TexStudioSettings.txsprofile (Optionen->Profil laden) aus dem Ordner ./Vorlagen/settings
	\item Installiere die Frutiger-Fonts aus ./Vorlagen/Fonts (optional, da nochmal explizit geladen wird)
	\item Öffne die Datei Diss\textunderscore Main.tex, wähle deinen Stil [manuskript] oder [publishing] in der angelegten Dokumentenklasse
	\item Kompilieren
\end{itemize}

\section{Aufbau der Vorlage}
\label{sec:Aufbau-der-Vorlage}
Diese Vorlage bietet eine grobe Strukturierung für ein größeres \LaTeX Projekt. Die wichtigste Datei ist die thesis.cls im Ordner ./Vorlagen, in welcher stilistische als auch funktionale Pakete geladen und Formate definiert werden. Ebenso bietet diese Vorlage eine Anleitung, wie das Literaturverzeichnis im IPA-Stil (./Vorlagen/mypackages/bibl) erstellt wird.


\subsection{Dokumentenklasse und deren Optionen}
\label{sec:Dokumentenklasse}
In der Diss\textunderscore Main.tex könnt ihr eure Version auswählen. Die Unterschiede liegen vor allem in der Reihenfolge der Kapitel im Vorspann, sowie der Bundstegkorrektur zum Drucken. In der \textit{manuskript}-Version wird zudem am Ende die Eigenständigkeitserklärung geladen.

\begin{small}
\begin{lstlisting}
% Eigene Klasse definiert: Hier sind auch die usepackages und weitere Settings enthalten
\documentclass[manuskript]{Vorlagen/thesis} % Optionen: "publishing" or "manuskript"
\end{lstlisting}
\end{small}
