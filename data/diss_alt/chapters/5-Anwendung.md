\cleardoublepage
\chapter{Praktische Tipps beim Arbeiten mit \LaTeX}
\label{cha:Anwendung}

Tipps und Tricks:
\begin{itemize}[noitemsep]
	\item Benutze das siunitx paket (bereits geladen) konsequent
	\item Benutze die Befehle für Abkürzungen, wie \zB \ua damit das spacing richtig gesetzt wird
	\item ...
\end{itemize}

\section{Grafiken und Tabellen einbinden}
\label{sec:How-to-2Figure-Einbinden}
In diesem Abschnitt habe ich euch ein paar Beispiele zum Einfügen von Grafiken eingefügt. Anstelle der subcaptionbox könnt ihr natürlich auch subfigure verwenden.
<!-- % -->
\begin{figure}[ht]
	\centering
	\includegraphics[width=\textwidth]{example-image-a}
	\caption[Dies ist eine Kurzüberschrift der Figure 1]{Dies ist ein Beispiel um eine Grafiken nebeneinander in eine Figure-Umgebung zu packen.}
	\label{fig:How-to-1Figure-Einbinden}
\end{figure}
<!-- % -->

<!-- % -->
\begin{figure}[ht]
	\centering
	\subcaptionbox{Subcaption A}{\includegraphics[width=0.49\textwidth]{example-image-a}\label{fig:example-image-a1}}\hfill%
	\subcaptionbox{Subcaption B}{\includegraphics[width=0.49\textwidth]{example-image-b}\label{fig:example-image-b1}}
	\caption[Dies ist eine Kurzüberschrift der Figure 2]{Dies ist ein Beispiel um zwei Grafiken nebeneinander in eine Figure-Umgebung zu packen.}
	\label{fig:How-to-2Figure-Einbinden}
\end{figure}
<!-- % -->

\begin{figure}[ht]
	\centering
	\begin{minipage}[c]{\textwidth}
		\subcaptionbox{Subcaption A}{\includegraphics[width=0.49\textwidth]{example-image-a}\label{fig:example-image-a2}}\hfill%
		\subcaptionbox{Subcaption B}{\includegraphics[width=0.49\textwidth]{example-image-b}\label{fig:example-image-b2}}
	\end{minipage}%
	\vspace{0.25cm}
	\begin{minipage}[c]{\textwidth}
		\subcaptionbox{Subcaption C}{\includegraphics[width=0.49\textwidth]{example-image-a}\label{fig:example-image-c2}}\hfill%
		\subcaptionbox{Subcaption D}{\includegraphics[width=0.49\textwidth]{example-image-b}\label{fig:example-image-d2}}
		\caption[Dies ist eine Kurzüberschrift der Figure 3]{Dies ist ein Beispiel um vier Grafiken in eine Figure-Umgebung zu packen.}
	\end{minipage}%
	\label{fig:How-to-4Figure-Einbinden}
\end{figure}
<!-- % -->

<!-- % -->
\begin{table}[htb]
	\centering
	\small %nutze \small um die Schriftgröße etwas zu reduzieren
	\caption[Dies ist eine Kurzüberschrift für Tabellen]{Beispiel für eine größere Tabelle}	
	\begin{tabularx}{\textwidth}{@{} p{0.3\textwidth}p{0.2\textwidth}p{0.2\textwidth}p{0.2\textwidth} @{}} %@{} verhindert Indentationen
		\toprule
		\textbf{Typ} 			& \textbf{Wert 1} 						& \textbf{Bool} & \textbf{Wert 3} \\
		\midrule
		\textbf{Kategorie 1} 	& & & \\
		\enspace Parameter 1	& \SI{1}{\meter\per\second} 			& True			& Isolator (ideal)\\
		
		&&&\\[-2ex]
		\midrule
		\textbf{Kategorie 2} 	& & &\\
		\enspace Parameter 1	& \SI{1e-4}{\kilo\gram\per\second} (hier font bug)	\num{1e4}	& False			& Isolator (ideal)\\
		\enspace Parameter 2	& \SI{2e16}{\degreeCelsius}  	& True			& Isolator (ideal)\\
		
		&&&\\[-2ex]
		\midrule
		\textbf{Kategorie 3}	& & &\\
		\enspace Parameter 1	& \na  									& False 		& Isolator (ideal)\\
		
		&&&\\[-2ex]
		\midrule
		\textbf{Kategorie 4} 	& & &\\
		\enspace Parameter 2 	& \na 									& True 			& \SI{0}{\volt}\\
		\enspace Parameter 3 	& \SI{5000}{\radian\per\second}			& True 			& \SI{65000}{\volt}\\
		\bottomrule	
	\end{tabularx}
	\label{tab:Beispieltabelle}
\end{table}
<!-- % -->

\section{Mathefont}
\label{sec:mathFont}
Leider gibt es für die Schriftart Frutiger keinen Mathefont, sodass für Gleichungen \etc auf eine andere Schriftart zurückgegriffen werden muss. Nach Rücksprache mit der Bibliothek kann Euler VM, CM Bright oder Helvetica verwendet werden. Jedoch kann keine dieser Schriftarten zusammen mit dem unicode-math Paket verwendet werden. Teilweise, wie bei CM Bright, erscheinen mathematische Symbole in nicht-vektorisierter Form, was natürlich für einen \LaTeX Benutzer garnicht geht. Ich habe mich daher für die Schriftart GFS Neohellenic Math entschieden, welche direkt über unicode-math geladen wird. Leider passt diese auch nicht perfekt zum Frutiger Font, ist aber meiner Meinung nach derzeit der beste Kompromiss. Falls jemand eine bessere Lösung findet, gerne her damit.

\blindmathpaper
