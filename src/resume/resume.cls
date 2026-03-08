\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{resume}[2026/03/08 Minimal resume class]
\LoadClass[10pt,letterpaper]{article}
\RequirePackage[hidelinks]{hyperref}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\pagestyle{empty}
\makeatletter
\newcommand{\@resumename}{}
\newcommand{\@resumeaddress}{}
\newcommand{\name}[1]{\gdef\@resumename{#1}}
\newcommand{\address}[1]{\gdef\@resumeaddress{#1}}
\AtBeginDocument{%
  \thispagestyle{empty}%
  \begingroup
    \centering
    {\LARGE\bfseries \@resumename\par}%
    \vspace{0.35em}%
    {\normalsize \@resumeaddress\par}%
  \endgroup
  \vspace{0.6em}%
}
\makeatother
\newenvironment{rSection}[1]{%
  \vspace{0.45em}%
  {\large\bfseries #1\par}%
  \vspace{0.2em}%
  \hrule
  \vspace{0.45em}%
}{%
  \vspace{0.2em}%
}
\endinput