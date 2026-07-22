# Shader Programming

Shaders are small programs that execute on the GPU at specific stages
of the graphics pipeline. They are the primary mechanism for
customizing rendering behavior: lighting, materials, post-processing,
and compute tasks are all implemented in shaders.

## Shader Stages

| Stage | Input | Output | Purpose |
|:------|:------|:-------|:--------|
| Vertex | Per-vertex attributes | Clip position + varyings | Transform geometry |
| Tessellation Control | Patch vertices | Patch control points | Set subdivision level |
| Tessellation Evaluation | Generated vertex | Clip position + varyings | Evaluate subdivided surface |
| Geometry | Whole primitive | 0+ primitives | Generate/modify geometry |
| Fragment | Interpolated varyings | Per-fragment data | Compute pixel color |
| Compute | Work group | Shared/global memory | General-purpose GPU computation |

## GLSL Essentials

### Data Types

GLSL provides scalar, vector, and matrix types:

```glsl
float f = 1.0;
vec3 position = vec3(0.0, 1.0, 0.0);
mat4 transform = mat4(1.0);  // identity
ivec2 pixelCoord = ivec2(1920, 1080);
```

Vectors support component-wise arithmetic and swizzling:

```glsl
vec4 color = vec4(1.0, 0.5, 0.0, 1.0);
vec3 rgb = color.rgb;
float alpha = color.a;
vec4 bgra = color.bgra;  // swizzle
```

### Qualifiers

```glsl
layout(location = 0) in vec3 inPosition;     // vertex attribute
layout(location = 0) out vec3 fragColor;      // fragment output
layout(set = 0, binding = 0) uniform UBO {    // uniform buffer
    mat4 mvp;
} ubo;
layout(push_constant) uniform Push {          // push constants
    float time;
} push;
```

### Built-in Functions

GLSL provides a rich standard library:

```glsl
float len = length(v);              // Euclidean norm
vec3 n = normalize(v);              // unit vector
float d = dot(a, b);                // dot product
vec3 c = cross(a, b);               // cross product
vec3 r = reflect(I, N);             // reflection
vec3 refracted = refract(I, N, eta); // refraction
float t = smoothstep(edge0, edge1, x); // Hermite interpolation
vec4 texel = texture(sampler, uv);  // texture sampling
```

## Push Constants vs. UBOs vs. SSBOs

| Mechanism | Size | Update cost | Use case |
|:----------|:-----|:------------|:---------|
| Push constants | 128-256 bytes | Free (inline in command buffer) | Per-draw parameters |
| UBO | Up to 64 KB | Descriptor set binding | Camera, lights |
| SSBO | Up to 2 GB | Descriptor set binding | Large read/write data |

Push constants are the fastest uniform mechanism: they are embedded
directly in the command buffer and require no descriptor set update.

```glsl
layout(push_constant) uniform PushConstants {
    mat4 model;       // 64 bytes
    vec4 tint;        // 16 bytes
    uint materialId;  // 4 bytes
} push;               // Total: 84 bytes (within 128-byte minimum)
```

## Compute Shaders

Compute shaders execute outside the graphics pipeline. They operate on
work groups -- blocks of invocations that share local memory:

```glsl
#version 460
layout(local_size_x = 64, local_size_y = 1, local_size_z = 1) in;

layout(set = 0, binding = 0) buffer InputBuffer {
    float data[];
} input_buf;

layout(set = 0, binding = 1) buffer OutputBuffer {
    float data[];
} output_buf;

void main() {
    uint idx = gl_GlobalInvocationID.x;
    output_buf.data[idx] = data[idx] * 2.0;
}
```

Dispatched from the CPU:

```c
vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, computePipeline);
vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_COMPUTE,
                        layout, 0, 1, &descriptorSet, 0, NULL);
vkCmdDispatch(cmd, (N + 63) / 64, 1, 1);
```

Common uses: particle simulation, image processing, culling, mesh
generation, and post-processing effects.

## Subgroup Operations

Modern GPUs support subgroup (warp/wavefront) operations that let
invocations within a subgroup communicate without shared memory:

```glsl
#extension GL_KHR_shader_subgroup_arithmetic : enable

float sum = subgroupAdd(value);       // reduce across subgroup
float min_val = subgroupMin(value);   // minimum across subgroup
bool any_true = subgroupAny(flag);     // any invocation's flag is true
uint ballot = subgroupBallot(flag);   // bitmask of active invocations
```

Subgroup operations are essential for GPU-driven rendering, tiled
light culling, and prefix-sum based compaction.

## Shader Compilation

GLSL source is compiled to SPIR-V (Standard Portable Intermediate
Representation) offline using `glslangValidator` or `glslc`:

```bash
glslc -fshader-stage=vert shader.vert -o shader.vert.spv
glslc -fshader-stage=frag shader.frag -o shader.frag.spv
```

SPIR-V is the binary intermediate representation consumed by Vulkan.
It can be further optimized with `spirv-opt`:

```bash
spirv-opt -O shader.vert.spv -o shader.vert.opt.spv
```

The Vulkan driver translates SPIR-V to the GPU's native ISA at pipeline
creation time. This is different from OpenGL, where the driver compiles
GLSL source at runtime.
