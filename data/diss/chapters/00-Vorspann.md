<!-- Ab hier Kopfzeile verwenden, da bereits mehrere Seiten eines Kapitels vorliegen -->
\pagestyle{headings}	

\ifpublishing 
<!-- Vorwort des Autors ----------------------------------------------------------------------------------------- -->
\phantomsection
<!-- Verringert Zeilenabstand im ToC -->
\addtocontents{toc}{\protect\vspace{-1ex}} 
\chapter*{Vorwort} 
<!-- Erzeugt Lesezeichen "Vorwort" im PDF -->
\pdfbookmark{Vorwort}{Vorwort} 
\label{cha:Vorwort}
<!-- ----- -->
Dies ist eine Vorlage zur Erstellung einer Dissertation, Masterarbeit oder Bachelorarbeit, welche sich an den Vorgaben der Uni Stuttgart und Fraunhofer IPA orientiert.
An dieser Stelle möchte ich mich bei allen Kollegen bedanken, die mir gutes Feedback und Unterstützung zur Verbesserung der Vorlage beigetragen haben.
Insbesondere Stefan Gerstmayr hat hier einen wesentlichen Beitrag geleistet, sowohl auf der Code Seite als auch mit Ideen zur Anfertigung der Dissertation. 
Vielen Dank auch an alle Bug-Reporter, um die Vorlage zu verbessern

\textbf{Danke euch!}


<!-- ----- -->
\fi 


<!-- Kurzfassung ------------------------------------------------------------------------------------------------ -->
\phantomsection
<!-- Verringert Zeilenabstand im ToC -->
\addtocontents{toc}{\protect\vspace{-1ex}} 

\ifpublishing
\chapter*{Kurzfassung}
<!-- Erzeugt Lesezeichen "Kurzfassung" im PDF -->
\pdfbookmark{Kurzfassung}{Kurzfassung} 
<!-- % hier sind wir im manuskript modus -->
\else 
\addchap{Kurzfassung}
\fi
\label{cha:kurzfassung}
<!-- ----- -->

\blindtext

<!-- ----- -->


<!-- Abstract -------------------------------------------------------------------------------------------------- -->
\phantomsection
<!-- Verringert Zeilenabstand im ToC -->
\addtocontents{toc}{\protect\vspace{-1ex}} 

\ifpublishing
\chapter*{Abstract}
<!-- Erzeugt Lesezeichen "Abstract" im PDF--------------------------------- -->
\pdfbookmark{Abstract}{Abstract} 
\else
\addchap{Abstract}
\fi
\label{cha:Abstract}

\blindtext

<!-- ----- -->