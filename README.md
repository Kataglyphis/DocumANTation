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
- [Useful tools](#useful-tools)
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
uv run --with "sphinx>=8,<9" sphinx-build -W -b html docs docs/_build/html
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
./scripts/build_in_container.sh cv
```

## Dependencies
- [beamerthemeawesome](https://github.com/LukasPietzschmann/awesome-beamer) (git submodule)
- [smile](https://github.com/LukasPietzschmann/smile) (git submodule)

## Useful tools
- [pandoc](https://github.com/jgm/pandoc)

## Contributing
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

## Contact
Jonas Heinle - [@Cataglyphis_](https://twitter.com/Cataglyphis_) - jonasheinle@googlemail.com

Project Link: [https://github.com/Kataglyphis/Kataglyphis-mdToPdf](https://github.com/Kataglyphis/Kataglyphis-mdToPdf)
