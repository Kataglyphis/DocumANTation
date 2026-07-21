<div align="center">
  <a href="https://jonasheinle.de">
    <img src="images/logo.png" alt="logo" width="200" />
  </a>

  <h1>Kataglyphis-mdToPdf</h1>

  <h4>Convert markdown to modern slide show or a4paper book. Combining the very light weight markdown language with all the power of LaTeX.</h4>
</div>

## Table of Contents
- [About The Project](#about-the-project)
- [Getting Started](#getting-started)
  - [Build Docker image](#build-docker-image)
  - [Build docs](#build-docs)
  - [Build presentation](#build-presentation)
  - [Build book](#build-book)
  - [Build CV](#build-cv)
- [Dependencies](#dependencies)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## About The Project
Formulate everything in markdown. Use LaTeX power via Pandoc. Containerized for reproducibility.

### Key Features
| Feature | Status |
| ------- | :----: |
| Docker image, make everything reproducible | ✔️ |
| LaTeX templates | ✔️ |
| Comprehensive python scripts | ✔️ |

## Getting Started

### Prerequisites
- **nerdctl** (or docker)
- **buildkitd** running (`systemctl --user status buildkit.service`)

```bash
git clone --recurse-submodules git@github.com:Kataglyphis/Kataglyphis-mdToPdf.git
```

### Build Docker image
```bash
nerdctl build . -t pandoc_all
```

### Build docs
```bash
uv run --extra docs sphinx-build -W -b html docs docs/_build/html
```

The generated HTML lands in `docs/_build/html/`.

### Build presentation
```bash
./scripts/build_in_container.sh beamer
```

### Build book
```bash
./scripts/build_in_container.sh book
```

Outputs land in `data/out/`.

Optional host shortcuts if `make` is installed:

```bash
make beamer
make book
make diss
make cv
```

Strict warning checks can be enabled for any build:

```bash
STRICT_WARNINGS=1 make book
STRICT_WARNINGS=1 ./scripts/build_in_container.sh cv
```

### Build CV
```bash
./scripts/build_in_container.sh cv                  # English
CV_LANG=german ./scripts/build_in_container.sh cv   # German
```

Both variants come from the same sources in `data/cv/` and land in `data/out/`
as `CV_Jonas_Heinle_<language>.pdf`. `make cv-all` builds the pair.

## Dependencies

Everything the builds need lives in the `pandoc_all` image built from the
[`Dockerfile`](Dockerfile); nothing has to be installed on the host but a
container runtime. `pandoc` and `uv` are version-pinned there (the pandoc `.deb`
additionally by SHA-256); the rest track Ubuntu 26.04.

### Document toolchain

| Component | License | Link |
| --- | --- | --- |
| Ubuntu 26.04 LTS (base image) | Various, mostly GPL-family | <https://ubuntu.com> |
| Pandoc | GPL-2.0-or-later | <https://github.com/jgm/pandoc> |
| TeX Live (`texlive-full`) | Collection; per package LPPL, GPL, X11, modified BSD | <https://tug.org/texlive/> |
| Latin Modern (`lmodern`) | GUST Font License (LPPL-style) | <http://www.gust.org.pl/projects/e-foundry/latin-modern> |
| Ghostscript | AGPL-3.0-or-later | <https://www.ghostscript.com/> |
| ImageMagick | ImageMagick License (Apache-2.0-style) | <https://imagemagick.org> |

### Python

| Component | License | Link |
| --- | --- | --- |
| Python 3 (`python3-full`, `python3-pip`) | PSF-2.0 | <https://www.python.org> |
| uv | Apache-2.0 OR MIT | <https://github.com/astral-sh/uv> |
| Pygments | BSD-2-Clause | <https://pygments.org> |

### Base utilities

| Component | License | Link |
| --- | --- | --- |
| GNU C Library locales (`locales`) | LGPL-2.1-or-later | <https://www.gnu.org/software/libc/> |
| curl | curl (MIT/X-style) | <https://curl.se> |
| GNU Wget | GPL-3.0-or-later | <https://www.gnu.org/software/wget/> |
| ca-certificates | MPL-2.0 (CA bundle), GPL-2.0-or-later (packaging) | <https://packages.ubuntu.com/ca-certificates> |
| less | GPL-3.0-or-later or Less License | <https://www.greenwoodsoftware.com/less/> |
| sudo | ISC (with BSD-2/3-Clause parts) | <https://www.sudo.ws> |

### Vendored LaTeX themes

Git submodules, copied into the image's `texmf` tree at build time.

| Component | License | Link |
| --- | --- | --- |
| awesome-beamer | BSD-3-Clause | [fork](https://github.com/Kataglyphis/awesome-beamer) of [LukasPietzschmann/awesome-beamer](https://github.com/LukasPietzschmann/awesome-beamer) |
| smile | BSD-3-Clause | [fork](https://github.com/Kataglyphis/smile) of [LukasPietzschmann/smile](https://github.com/LukasPietzschmann/smile) |

Ghostscript is the only copyleft-network license in the set. It is invoked as a
separate program and nothing here links against it, so it does not reach the
documents this repo produces or the repo's own terms.

## Contributing
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Released under the MIT License — see [LICENSE](LICENSE). The third-party
components listed under [Dependencies](#dependencies) keep their own licenses.

## Contact
Jonas Heinle - [@Cataglyphis_](https://twitter.com/Cataglyphis_) - jonasheinle@googlemail.com

Project Link: [https://github.com/Kataglyphis/Kataglyphis-mdToPdf](https://github.com/Kataglyphis/Kataglyphis-mdToPdf)
