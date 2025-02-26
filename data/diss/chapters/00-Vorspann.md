\pagestyle{headings}	%Ab hier Kopfzeile verwenden, da bereits mehrere Seiten eines Kapitels vorliegen

\ifpublishing 
% Vorwort des Autors -----------------------------------------------------------------------------------------
\phantomsection
\addtocontents{toc}{\protect\vspace{-1ex}} % Verringert Zeilenabstand im ToC
\chapter*{Vorwort} 
\pdfbookmark{Vorwort}{Vorwort} % Erzeugt Lesezeichen "Vorwort" im PDF
\label{cha:Vorwort}
%-----
Dies ist eine Vorlage zur Erstellung einer Dissertation, Masterarbeit oder Bachelorarbeit, welche sich an den Vorgaben der Uni Stuttgart und Fraunhofer IPA orientiert.
An dieser Stelle möchte ich mich bei allen Kollegen bedanken, die mir gutes Feedback und Unterstützung zur Verbesserung der Vorlage beigetragen haben.
Insbesondere Stefan Gerstmayr hat hier einen wesentlichen Beitrag geleistet, sowohl auf der Code Seite als auch mit Ideen zur Anfertigung der Dissertation. 
Vielen Dank auch an alle Bug-Reporter, um die Vorlage zu verbessern

\textbf{Danke euch!}


%-----
\fi 


% Kurzfassung ------------------------------------------------------------------------------------------------
\phantomsection
\addtocontents{toc}{\protect\vspace{-1ex}} % Verringert Zeilenabstand im ToC

\ifpublishing
\chapter*{Kurzfassung}
\pdfbookmark{Kurzfassung}{Kurzfassung} % Erzeugt Lesezeichen "Kurzfassung" im PDF
\else % hier sind wir im manuskript modus
\addchap{Kurzfassung}
\fi
\label{cha:kurzfassung}
%-----

\blindtext

%-----


% Abstract --------------------------------------------------------------------------------------------------
\phantomsection
\addtocontents{toc}{\protect\vspace{-1ex}} % Verringert Zeilenabstand im ToC

\ifpublishing
\chapter*{Abstract}
\pdfbookmark{Abstract}{Abstract} % Erzeugt Lesezeichen "Abstract" im PDF---------------------------------
\else
\addchap{Abstract}
\fi
\label{cha:Abstract}

\blindtext

%-----