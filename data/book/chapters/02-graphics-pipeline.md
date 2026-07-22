# The Graphics Pipeline

The graphics pipeline is the sequence of transformations that converts a
scene description -- vertices, textures, lights, camera parameters -- into
a raster image. Understanding this pipeline is the prerequisite for
everything that follows: every optimization, every visual effect, every
API call is ultimately a lever on one of its stages.

## Overview

The modern programmable pipeline has the following stages:

```
Application → Vertex Shader → Tessellation → Geometry Shader →
Clipping → Rasterization → Fragment Shader → Output Merger → Framebuffer
```

Not every stage is mandatory. Tessellation and geometry shaders are optional
extensions. The application stage runs on the CPU; everything from the
vertex shader onward runs on the GPU.

## Application Stage

The application prepares draw calls: it updates game state, performs
animation, culls invisible objects, and batches geometry into command
buffers. This is the only stage that runs on the CPU, and it is where
the programmer has the most flexibility.

Key responsibilities:

- **Scene management**: maintaining the spatial data structures (BVHs,
  octrees, BSP trees) that enable efficient visibility determination.
- **Animation**: skeletal deformation, morph targets, particle systems.
- **Draw call submission**: binding pipelines, descriptor sets, vertex
  buffers, and issuing indexed or indirect draws.

## Vertex Processing

The vertex shader transforms each vertex from model space to clip space.
It receives per-vertex attributes (position, normal, UV coordinates) and
outputs a position in homogeneous clip coordinates along with any
interpolants the fragment shader needs.

```glsl
#version 460

layout(location = 0) in vec3 inPosition;
layout(location = 1) in vec3 inNormal;
layout(location = 2) in vec2 inTexCoord;

layout(set = 0, binding = 0) uniform CameraUBO {
    mat4 view;
    mat4 projection;
} camera;

layout(push_constant) uniform PushConstants {
    mat4 model;
} push;

layout(location = 0) out vec3 fragNormal;
layout(location = 1) out vec2 fragTexCoord;
layout(location = 2) out vec3 fragWorldPos;

void main() {
    vec4 worldPos = push.model * vec4(inPosition, 1.0);
    fragWorldPos = worldPos.xyz;
    fragNormal = mat3(push.model) * inNormal;
    fragTexCoord = inTexCoord;
    gl_Position = camera.projection * camera.view * worldPos;
}
```

The GPU executes vertex shaders in parallel across thousands of vertices
simultaneously. Each invocation is independent -- it cannot read another
vertex's output. This data-parallel design is what makes GPUs fast.

## Tessellation

Optional. The tessellation control shader (hull shader) determines how
much to subdivide a patch; the tessellation primitive generator performs
the subdivision; the tessellation evaluation shader (domain shader)
computes the final position of each generated vertex.

Tessellation enables level-of-detail adaptation on the GPU: a surface
close to the camera gets more triangles than one far away, without the
CPU having to manage multiple mesh resolutions.

## Geometry Processing

Optional. The geometry shader receives an entire primitive (point, line,
or triangle) and can emit zero or more primitives. It is useful for:

- Generating billboard quads from point sprites
- Extruding silhouette edges for shadow volumes
- Visualizing normals as lines

In practice, geometry shaders are often slower than compute shaders for
the same task, because their output is variable-length and the hardware
must allocate buffer space conservatively.

## Clipping

Primitives that lie partially or entirely outside the view frustum are
clipped against the six frustum planes. The Sutherland-Hodgman algorithm
clips a polygon against one plane at a time, producing new vertices at
intersection points.

After clipping, the homogeneous divide converts clip coordinates to
normalized device coordinates (NDC):

$$
\mathbf{p}_{ndc} = \left(\frac{x_c}{w_c},\; \frac{y_c}{w_c},\; \frac{z_c}{w_c}\right)
$$

Vertices with $w_c \leq 0$ are behind the camera and are discarded.

## Rasterization

Triangles in NDC are mapped to screen coordinates and converted into
fragments. For each triangle, the rasterizer determines which pixels it
covers, using a coverage rule (typically top-left) to ensure each pixel
is claimed by exactly one triangle at shared edges.

Per-fragment attributes (normals, texture coordinates, colors) are
interpolated across the triangle using barycentric coordinates. The
interpolation is perspective-correct: attributes are divided by $w$
before interpolation and multiplied back after, preventing the affine
warp that would otherwise occur on steep surfaces.

## Fragment Processing

The fragment shader computes the color of each fragment. This is where
lighting, texturing, and most visual effects occur:

```glsl
#version 460

layout(location = 0) in vec3 fragNormal;
layout(location = 1) in vec2 fragTexCoord;
layout(location = 2) in vec3 fragWorldPos;

layout(set = 1, binding = 0) uniform sampler2D albedoMap;
layout(set = 1, binding = 1) uniform sampler2D normalMap;

layout(location = 0) out vec4 outColor;

void main() {
    vec3 albedo = texture(albedoMap, fragTexCoord).rgb;
    vec3 N = normalize(fragNormal);
    vec3 L = normalize(vec3(1.0, 2.0, 3.0));
    float NdotL = max(dot(N, L), 0.0);
    outColor = vec4(albedo * (0.1 + 0.9 * NdotL), 1.0);
}
```

Fragment shaders run millions of times per frame (once per covered pixel
per draw call). They are the most performance-critical stage in a
typical real-time pipeline.

## Output Merger

The final stage combines the fragment shader's output with the existing
framebuffer contents:

- **Depth test**: discard fragments behind already-rendered geometry.
- **Stencil test**: conditional writes based on stencil buffer state.
- **Blending**: combine source and destination colors (for transparency,
  particle effects, deferred decals).

The order of operations matters: depth testing before blending ensures
that opaque geometry occludes transparent geometry correctly.

## Summary

The graphics pipeline is a sequence of parallel, mostly independent
transformations. The CPU feeds it; the GPU executes it. Every rendering
technique -- from a simple textured triangle to a global illumination
simulation -- is a specific configuration of these stages.
