# Introduction

Computer graphics is the discipline of generating images from data using
computational methods. It encompasses everything from the mathematical
foundations of projecting three-dimensional geometry onto a two-dimensional
screen, to the physical simulation of light transport, to the real-time
rendering of interactive virtual worlds.

This book introduces the fundamental concepts, algorithms, and modern APIs
that drive contemporary rendering. It is written for readers with a background
in computer science who want to understand what happens between submitting
geometry and receiving pixels -- and how to control every stage of that
process.

## What This Book Covers

The chapters follow the path of a primitive through the rendering pipeline:

1. **The Graphics Pipeline** -- the end-to-end journey from application data
   to framebuffer, covering both the fixed-function and programmable stages.
2. **Transformations** -- the linear algebra that moves vertices from model
   space through world, view, and clip space to screen coordinates.
3. **Rasterization** -- how triangles become fragments, including clipping,
   culling, and the sub-pixel rules that determine coverage.
4. **Lighting and Shading** -- local illumination models from Phong to
   physically based rendering, normal interpolation, and shadow generation.
5. **Texturing** -- mapping 2D images onto 3D surfaces, filtering, mipmapping,
   and the material parameter textures that drive modern PBR pipelines.
6. **Ray Tracing** -- the alternative paradigm: casting rays through pixels,
   intersecting geometry, and recursively simulating light transport.
7. **Shader Programming** -- writing GLSL and SPIR-V programs that execute on
   the GPU at each pipeline stage.
8. **The Vulkan API** -- explicit GPU programming with command buffers,
   descriptor sets, render passes, and synchronization.
9. **Advanced Rendering** -- deferred shading, screen-space ambient occlusion,
   shadow mapping, and temporal techniques.

## Prerequisites

Readers should be comfortable with:

- **Linear algebra**: vectors, matrices, dot and cross products.
- **C or C++**: the implementation language for every code example.
- **Basic GPU concepts**: parallelism, memory hierarchies, the difference
  between a CPU and a GPU.

Shader code is written in GLSL. Systems code targets Vulkan 1.3 with C.
Where the mathematics demands it -- radiometry, spherical harmonics,
Monte Carlo integration -- the required background is introduced inline.

## Conventions

Code blocks use syntax highlighting for the language indicated:

```c
#include <math.h>

static float luminance(float r, float g, float b) {
    return 0.2126f * r + 0.7152f * g + 0.0722f * b;
}
```

Mathematical expressions appear both inline ($\mathbf{p} = \mathbf{M}\mathbf{v}$)
and as display equations:

$$
\mathbf{p}_{clip} = \mathbf{P} \cdot \mathbf{V} \cdot \mathbf{M} \cdot \mathbf{v}_{model}
$$

Glossary entries are referenced where they first appear. The nomenclature
lists all mathematical symbols used throughout the book.

## About the Author

Jonas Heinle studied computer science at the Karlsruhe Institute of
Technology (KIT), specializing in computer graphics, geometry processing,
and anthropomatics. His Master's thesis investigated user-adaptive guidance
in mixed reality using eye tracking. His B.Sc. thesis addressed temporally
stable blue noise error distributions for real-time rendering. He maintains
a Vulkan and OpenGL renderer as an ongoing research platform for implementing
modern rendering techniques.
