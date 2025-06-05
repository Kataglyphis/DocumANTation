\setstretch{1.5} %FIXME: \onehalfspacing funktioniert nicht mit eigenem Font? (aber \doublespacing und \singlespacing gehen)
\addtocontents{toc}{\protect\vspace{-1ex}} % Verringert Zeilenabstand im ToC

\appendix
\chapter{Abbildungen}
\label{chap:A-Abbildungen}
<!-- % -->
\bigskip\noindent
\begin{minipage}{\textwidth}
	\centering
	\includegraphics{awesome.jpg}
	\captionsetup{type=figure}
	\captionof{figure}{Awesome-Meme}
\end{minipage}
<!-- % -->
\bigskip\noindent
\begin{minipage}{\textwidth}
	\centering
	\includegraphics{example-image-b}
	\captionsetup{type=figure}
	\captionof{figure}{Ein weiteres Bild.}
\end{minipage}
<!-- % -->