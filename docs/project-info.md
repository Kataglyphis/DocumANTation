# Project Information

## Development Tooling

- `uv` manages local Python environments and command execution.
- `ruff` provides linting and formatting checks.
- `ty` provides static type checks for the Python build logic.
- Sphinx builds the repository documentation site.

## External Dependencies

- `pandoc` for Markdown-to-LaTeX or Markdown-to-PDF conversion
- LuaLaTeX and related TeX tooling for final PDF generation
- `beamerthemeawesome` as the presentation theme submodule
- `smile` as an additional presentation theme submodule

This repository is also the single source of truth for the shared Kataglyphis
docs theme (`sphinx-kataglyphis-theme/`) and docs tooling (`docs-tooling/`),
which downstream repositories consume as a submodule.

## Contribution Flow

1. Fork the repository.
2. Create a feature branch.
3. Make the code and documentation changes together.
4. Run the relevant checks and document builds.
5. Open a pull request.

## License

This project is released under the MIT License.

## Contact

- Jonas Heinle - [@Cataglyphis_](https://twitter.com/Cataglyphis_) - jonasheinle@googlemail.com
- Project repository: <https://github.com/Kataglyphis/Kataglyphis-mdToPdf>
