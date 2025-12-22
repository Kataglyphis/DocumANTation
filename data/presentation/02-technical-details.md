# Technical details

## Demo roadmap (3 minutes)

1. Edit a slide in Markdown
2. Build the PDF in Docker
3. Show the final deck + theme

## System overview

- Flutter/Dart app as the UI layer
- Content lives in Markdown (Git)
- PDF output is generated via pandoc + LaTeX

## Pipeline (Markdown $\rightarrow$ PDF)

- Inputs: ordered `data/presentation/*.md`
- Template: awesome-beamer theme
- Engine: `lualatex`
- Citations: BibTeX + `--citeproc`

## Why Docker for the build?

- Same toolchain on Windows/Linux/CI
- Fonts + LaTeX packages are pinned
- Reproducible output for YouTube recordings

## Practical details

- Code blocks: `minted` (needs `-shell-escape`)
- Citations: keep sources in `refs.bib`
- Resource paths: images can live next to the repo

## Code example: build the PDF (Docker)

```bash
docker run --rm \
	-v "${PWD}/md2pdfLib:/md2pdfLib" \
	-v "${PWD}/data:/data" \
	ghcr.io/kataglyphis/kataglyphis_md2pdf \
	bash -lc "cd /md2pdfLib/presentation; ./scripts/update_own_sty.sh; python ./scripts/md2beamerpdf.py"
```

## Code example: Rust (tiny CLI-like utility)

```rust
fn main() {
		let args: Vec<String> = std::env::args().collect();
		let name = args.get(1).map(|s| s.as_str()).unwrap_or("world");
		println!("Hello, {name}!");
}
```

## Code example: Dart (Flutter-friendly model)

```dart
class Project {
	final String title;
	final List<String> tags;

	const Project({required this.title, required this.tags});

	String get headline => '$title (${tags.join(", ")})';
}

void main() {
	const p = Project(title: 'md→pdf', tags: ['pandoc', 'latex', 'docker']);
	print(p.headline);
}
```

## Code example: C++ (small data transform)

```cpp
#include <iostream>
#include <string>

std::string slugify(std::string s) {
	for (char& c : s) {
		if (c == ' ') c = '-';
		else c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
	}
	return s;
}

int main() {
	std::cout << slugify("Hello Meetup") << "\n";
}
```

## Trade-offs

- `-shell-escape` is powerful (use only in trusted builds)
- LaTeX builds can be slower than pure HTML
- Template work is “real LaTeX” (but reusable)

## Takeaways

- Markdown keeps content portable
- Flutter keeps UI consistent across targets
- Docker keeps builds reproducible
