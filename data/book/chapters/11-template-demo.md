# Template demo (showcase)

This chapter exists to showcase common elements and how they render with your current Pandoc to LuaLaTeX book template.

```{=latex}
% Add a few entries so the nomenclature/glossary pages show something
\nomenclature{API}{Application Programming Interface}
\nomenclature{CLI}{Command Line Interface}
```

## Typography

You can mix **bold**, *italic*, and `inline code`.

Raw LaTeX works too: \textsc{Small Caps}, \texttt{monospace}, and \underline{underline}.

A link: <https://pandoc.org/>

Jump to the [Math demo](#math-demo).

## Lists

Unordered:

- First level item
- Second item with a nested list
  - Nested bullet A
  - Nested bullet B
- Third item

Ordered:

1. Step one
2. Step two
3. Step three

## Blockquote

> A blockquote should stand out and keep the text readable.
> 
> You can use multiple paragraphs inside it.

## Code blocks

Python (syntax highlighting):

```python
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

    def norm2(self) -> float:
        return self.x**2 + self.y**2

print(Point(3, 4).norm2())
```

Rust:

```rust
#[derive(Debug, Clone, Copy)]
struct Point {
  x: f64,
  y: f64,
}

impl Point {
  fn norm2(self) -> f64 {
    self.x * self.x + self.y * self.y
  }
}

fn main() {
  let p = Point { x: 3.0, y: 4.0 };
  println!("norm2={}", p.norm2());
}
```

C:

```c
#include <stdio.h>

static int clamp_int(int x, int lo, int hi) {
  if (x < lo) return lo;
  if (x > hi) return hi;
  return x;
}

int main(void) {
  printf("%d\n", clamp_int(42, 0, 10));
  return 0;
}
```

C++:

```cpp
#include <iostream>
#include <vector>
#include <numeric>

int main() {
  std::vector<int> xs{1, 2, 3, 4};
  const int sum = std::accumulate(xs.begin(), xs.end(), 0);
  std::cout << "sum=" << sum << "\n";
}
```

Dart:

```dart
int fib(int n) {
  if (n <= 1) return n;
  var a = 0, b = 1;
  for (var i = 2; i <= n; i++) {
  final next = a + b;
  a = b;
  b = next;
  }
  return b;
}

void main() {
  print('fib(10)=${fib(10)}');
}
```

Bash:

```bash
# Build the book TeX file
uv run python build.py book book_output.tex

# Full build (with glossary + nomenclature) via helper script
chmod +x md2pdfLib/scripts/compile_with_glossaries.sh
./md2pdfLib/scripts/compile_with_glossaries.sh --type book
```

## Tables

| Column | Meaning | Example |
|:------ |:--------|:--------|
| `fg`   | Foreground color | black |
| `bg`   | Background color | lightgray |
| `wd`   | Width | `0.6\paperwidth` |

## Figures / Images

A regular figure with caption (uses an existing image from `data/book/images/`):

![Example figure caption](data/book/images/figure1.jpg){ width=65% }

## Glossary / Acronyms

If glossary entries exist, you can reference them via raw LaTeX commands, e.g. \gls{gpu}, \gls{bvh}, or \gls{nan}.

```{=latex}
This sentence uses some glossary/acronym entries: \gls{gpu}, \gls{bvh}, and \gls{nan}.
```

## Definition environment

```{=latex}
\begin{definition}
A \emph{template} is a reusable layout and style definition that ensures consistent rendering.
\end{definition}
```

## Algorithms

```{=latex}
\begin{algorithm}
\caption{Sum of a list}
\begin{algorithmic}
\STATE $s \leftarrow 0$
\FOR{each $x$ in list}
  \STATE $s \leftarrow s + x$
\ENDFOR
\RETURN $s$
\end{algorithmic}
\end{algorithm}
```

## Math demo {#math-demo}

Inline math: $E = mc^2$.

Display math:

$$
\int_0^1 x^2\,dx = \left[\frac{x^3}{3}\right]_0^1 = \frac{1}{3}
$$

## Footnotes

Footnotes work like this.[^note]

[^note]: This is a footnote. You can use it for small asides or references.

## Citations / Bibliography

A citation using your BibLaTeX database: [@Shirley2019].
