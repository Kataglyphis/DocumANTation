# Examples

## Template rendering: quick overview

- **Bold**, *italic*, ~~strikethrough~~, `inline code`, and normal text.
- Mixed: **`inline code in bold?`** (check how this renders)
- Symbols: `->`, `=>`, `!=`, `<=`, `>=`, `::`, `λ`, `∑`, `→`, `←`.

---

## Lists

### Unordered

- First level
- Second item
  - Nested item A
  - Nested item B with `inline code`
- Third item

### Ordered

1. Step one
2. Step two
3. Step three

---

## Quotes / Callouts

> This is a blockquote.
>
> - With a list inside
> - And a **highlighted** word
>
> And a second paragraph to see spacing.

---

## Table

| Column | Example | Notes |
|---:|:---:|:---|
| 1 | `code` | right aligned header |
| 2 | **bold** | centered header |
| 3 | *italic* | left aligned header |

---

## Math

Inline math: $E = mc^2$.

Block math:

$$
\sum_{k=1}^{n} k = \frac{n(n+1)}{2}
$$

---

## Links + Footnotes

- Link: https://github.com/Kataglyphis
- Markdown link: [GitHub](https://github.com)

A footnote example.[^1]

[^1]: This is the footnote text.

---

## Image

![Background image test](data/presentation/images/shrek.jpg)

---

## Code (wrapping stress test)

The next code block contains very long lines to confirm wrapping (no overflow).

```bash
# A long line (should wrap nicely instead of overflowing):
export REALLY_LONG_ENV_VARIABLE_NAME_THAT_SHOULD_WRAP="this-is-a-very-very-very-very-very-long-value-that-keeps-going-to-test-line-wrapping" && echo "$REALLY_LONG_ENV_VARIABLE_NAME_THAT_SHOULD_WRAP"

# Another long command:
docker run --rm -v "${PWD}/md2pdfLib:/md2pdfLib" -v "${PWD}/data:/data" ghcr.io/kataglyphis/kataglyphis_md2pdf bash -lc "cd /md2pdfLib/presentation && python ./scripts/md2beamerpdf.py"
```

---

## Code (Python)

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class User:
    name: str
    roles: list[str]

def headline(user: User) -> str:
    return f"{user.name} ({', '.join(user.roles)})"

print(headline(User(name="Ada", roles=["admin", "speaker"])))
```

---

## Code (Rust)

```rust
fn main() {
    let args: Vec<String> = std::env::args().collect();
    let name = args.get(1).map(|s| s.as_str()).unwrap_or("world");
    println!("Hello, {name}!");
}
```

---

## Code (Dart)

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

---

## Code (C++)

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

---

## Code (JSON/YAML)

```json
{
  "name": "mdToPdf",
  "theme": "github-dark",
  "features": ["wrap", "syntax-highlighting", "beamer"]
}
```

```yaml
service:
  name: md2pdf
  engine: lualatex
  highlight: md2pdfLib/pygments.theme
```

---

## Code (LaTeX)

```tex
% This is a tiny LaTeX snippet
\textbf{Bold} and \textit{italic}.

\[
  \int_0^\infty e^{-x} \, dx = 1
\]
```

---

## Code (SQL)

```sql
SELECT
    language,
    COUNT(*) AS snippets
FROM
    code_blocks
WHERE
    length(source) > 120
GROUP BY
    language
ORDER BY
    snippets DESC;
```

---

## Edge cases

- Unicode in code: `md→pdf`, `λ`, `äöüß`
- Long inline code should wrap too (or at least not break layout): `this_is_a_really_long_inline_identifier_that_might_force_overflow_in_some_templates_so_we_test_it_here`
