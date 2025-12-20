<div align="center">
  <a href="https://jonasheinle.de">
    <img src="images/logo.png" alt="logo" width="200" />
  </a>

  <h1>Kataglyphis-mdToPdf</h1>

  <h4>Convert markdown to modern slide show or a4paper book. Combining the very light weight markdown language with all the power of LaTeX.</h4>
</div>

<h4 align="center"><a href="https://jonasheinle.de" target="_blank"></a></h4>

<!-- [![Linux build](https://github.com/Kataglyphis/GraphicsEngineVulkan/actions/workflows/Linux.yml/badge.svg)](https://github.com/Kataglyphis/GraphicsEngineVulkan/actions/workflows/Linux.yml)
[![Windows build](https://github.com/Kataglyphis/GraphicsEngineVulkan/actions/workflows/Windows.yml/badge.svg)](https://github.com/Kataglyphis/GraphicsEngineVulkan/actions/workflows/Windows.yml) -->
[![TopLang](https://img.shields.io/github/languages/top/Kataglyphis/mdToPdf)]() 
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/donate/?hosted_button_id=BX9AVVES2P9LN)
[![Twitter](https://img.shields.io/twitter/follow/Cataglyphis_?style=social)](https://twitter.com/Cataglyphis_)
[![YouTube](https://img.shields.io/youtube/channel/subscribers/UC3LZiH4sZzzaVBCUV8knYeg?style=social)](https://www.youtube.com/channel/UC3LZiH4sZzzaVBCUV8knYeg)

## Table of Contents
- [About The Project](#about-the-project)
  - [Key Features](#key-features)
  - [Dependencies](#dependencies)
  - [Useful tools](#useful-tools)
- [Getting Started](#getting-started)
  - [Building docker image](#building-docker-image)
  - [Windows](#windows)
  - [Linux](#linux)
  - [Build presentation](#build-presentation)
  - [Build book](#build-book)
  - [Build book with glossary entries](#build-book-with-glossary-entries)
  - [Build CV](#build-cv)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [How i created my customized pandoc latex template](#how-i-created-my-customized-pandoc-latex-template)
- [Tests](#tests)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)
- [Acknowledgements](#acknowledgements)
- [Literature](#literature)

<!-- ABOUT THE PROJECT -->
## About The Project
Formulating everything you need in markdown is very light weight and efficient. 
This can be an enormous productivity bust for oneself. Nevertheless one would miss the power of LaTeX 
with its unique ecosystem which is perfect for writing scientific content (paper, books, presentation). 
This project is using the amazing pandoc library which is the exact right tool to combine both worlds. </br>
You can immediately get started an use my customized templates for generating nice 
looking books, papers or presentations. I provide detailed steps how to use it and 
how to reproduce everything. The main environment is containerized thanks to Docker.
Therefore everything can much simpler be reproduced.

What is nicer than writing in pure, simple markdown? <br>
No worries about latex but with all the power of it!

### Key Features

<!-- ❌  -->
|          Feature                           |   Implement Status |
| ------------------------------------------ | :----------------: |
| Docker image, make everything reproducible |         ✔️         |
| LaTeX templates                            |         ✔️         |
| Comprehensive python scripts               |         ✔️         |

### Dependencies
This enumeration also includes submodules.

For my beamer latex project I use the following latex templates: 
* [beamerthemeawesome](https://github.com/LukasPietzschmann/awesome-beamer) theme from LukasPietzschmann as a starting point and customized it for my needs.
* [smile](https://github.com/LukasPietzschmann/smile) theme from LukasPietzschmann as a starting point and customized it for my needs.

* [Roboto font](https://fonts.google.com/specimen/Roboto) just a very nice font

### Useful tools

* [pandoc](https://github.com/jgm/pandoc)

<!-- GETTING STARTED -->
## Getting Started

### Building docker image
For building my docker image I use sth. like this:
```bash
docker build . -t ghcr.io/kataglyphis/kataglyphis_md2pdf
```

### WINDOWS
Command works in powershell but not on cmd.
```powershell
  cd Kataglyphis-mdToPdf
  docker run -it --rm -v ${PWD}/md2pdfLib:/md2pdfLib -v ${PWD}/data:/data --name mypandoc -h mypandoc ghcr.io/kataglyphis/kataglyphis_md2pdf
```
### LINUX 
Tested on ubuntu. Fedora etc. might have little differences. Idk
```bash
  cd Kataglyphis-mdToPdf
  docker run -it --rm -v ${PWD}/md2pdfLib:/md2pdfLib -v ${PWD}/data:/data --name mypandoc -h mypandoc ghcr.io/kataglyphis/kataglyphis_md2pdf
```

### Build presentation

Place all .md files in the data/presentation/chapters/ folder

Run following command at the very first time and whenever you change your .sty files (this updates the latex repo):
```bash
  chmod +x md2pdfLib/presentation/scripts/update_own_sty.sh
  ./md2pdfLib/presentation/scripts/update_own_sty.sh
```

```bash
  uv run python md2pdfLib/presentation/scripts/md2beamerpdf.py 2>&1 | tee data/out/beamer.log
```


### Build book
If no glossary is needed one can just run the following command:

```bash
  OUTPUT_NAME=output.pdf
  uv run python md2pdfLib/book/scripts/md2pdf.py $OUTPUT_NAME 2>&1 | tee data/out/book.log
```

#### Build book with glossary entries

For now we must invoke lualatex by ourselves if we want to print latex gloassary
entries. Therefore the workflow changes to the following:
Execute the bash script for making life easy:

```bash
  chmod +x md2pdfLib/book/scripts/compile_with_glossaries_and_nomenclature.sh
  ./md2pdfLib/book/scripts/compile_with_glossaries_and_nomenclature.sh
```

or run steps manually:

```bash
  # CHANGE TO OUTPUT TO .tex in this script first
  # then call this script to export a .tex file
  uv run python md2pdfLib/book/scripts/md2pdf.py 2>&1 | tee data/out/book.log
  # assuming the output is named book_output.tex
  lualatex data/out/book_output.tex
  makeglossaries book_output
  makeindex book_output.nlo -s nomencl.ist -o book_output.nls
  lualatex data/out/book_output.tex
  lualatex data/out/book_output.tex
```

### Build CV
```bash
  cd data/cv
  lualatex cv.tex
```

### Prerequisites

### Installation

1. Clone the repo
   ```bash
   git clone --recurse-submodules git@github.com:Kataglyphis/mdToPdf.git
   ```

   ```bash
   git submodule update --init --recursive
   ```

### How i created my customized pandoc latex template
This project aims to provide an unique style for the pdf layouts.
Therefore I had to produce my own pandoc template.latex file.
The following steps are guiding you through the customization steps
so you can reproduce everything:

I assume you already cloned the repo and the terminal points to the directory.

* export standart .latex file used by pandoc:
```bash
  pandoc -D latex > md2pdfLib/presentation/pandoc/custom.tex
```

* Delete *ignorenonframetext* out of the \documentclass options.
* Add custom colors right before \usetheme (in my case my favorite \definecolor{myGreenAccent}{RGB}{105, 240, 174}) 


## Tests

<!-- ROADMAP -->
## Roadmap
Upcoming :)
<!-- See the [open issues](https://github.com/othneildrew/Best-README-Template/issues) for a list of proposed features (and known issues). -->



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


<!-- LICENSE -->
## License

<!-- CONTACT -->
## Contact

Jonas Heinle - [@Cataglyphis_](https://twitter.com/Cataglyphis_) - jonasheinle@googlemail.com

Project Link: [https://github.com/Kataglyphis/...](https://github.com/Kataglyphis/...)


<!-- ACKNOWLEDGEMENTS -->
## Acknowledgements
Huge shoutout to Lukas Pietzschmann for his latex template.


## Literature 

Some very helpful literature, tutorials, etc. 

LaTeX
* [Custom modern LaTeX .sty template](https://github.com/LukasPietzschmann/awesome-beamer)
* [LaTeX template overview](https://github.com/martinbjeldbak/ultimate-beamer-theme-list)

Pandoc
* [The Art of Book Creation with Pandoc](https://medium.com/@sydasif78/book-creation-with-pandoc-and-markdown-893c7d72cb35)
* [my-pandoc-book GitHub Repo](https://github.com/sydasif/my-pandoc-book)
* [Kofler Pandoc bible](https://kofler.info/free-ebooks/pandoc2.pdf)

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/othneildrew/Best-README-Template.svg?style=for-the-badge
[contributors-url]: https://github.com/othneildrew/Best-README-Template/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/othneildrew/Best-README-Template.svg?style=for-the-badge
[forks-url]: https://github.com/othneildrew/Best-README-Template/network/members
[stars-shield]: https://img.shields.io/github/stars/othneildrew/Best-README-Template.svg?style=for-the-badge
[stars-url]: https://github.com/othneildrew/Best-README-Template/stargazers
[issues-shield]: https://img.shields.io/github/issues/othneildrew/Best-README-Template.svg?style=for-the-badge
[issues-url]: https://github.com/othneildrew/Best-README-Template/issues
[license-shield]: https://img.shields.io/github/license/othneildrew/Best-README-Template.svg?style=for-the-badge
[license-url]: https://github.com/othneildrew/Best-README-Template/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/jonas-heinle-0b2a301a0/
