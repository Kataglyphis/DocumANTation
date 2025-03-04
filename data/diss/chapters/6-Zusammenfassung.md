\chapter{Zusammenfassung}
\label{cha:Zusammenfassung}

Bekannte Fehler:
\begin{itemize}[noitemsep]
	\item Frutiger bietet keinen Mathe-Font, aktuell wird der standard Mathe Font verwendet. Bei SI Einheiten mit siunitx werden negative Exponenten nicht richtig dargestellt
	\item der Befehl \lstinline[language={[LaTeX]TeX},basicstyle=\ttfamily]{\onehalfspacing} funtkioniert bei Frutiger nicht; komischerweise funktionieren \lstinline[language={[LaTeX]TeX},basicstyle=\ttfamily]{\singlespacing} und \lstinline[language={[LaTeX]TeX},basicstyle=\ttfamily]{\doublespacing}. Workaround ist den Befehl \lstinline[language={[LaTeX]TeX},basicstyle=\ttfamily]{\setstretch} zu verwenden
\end{itemize}