# Advanced Rendering Techniques

This chapter covers techniques that extend the basic pipeline into
production-quality real-time rendering: deferred shading, screen-space
effects, temporal accumulation, and GPU-driven rendering.

## Deferred Shading

Forward rendering evaluates lighting for every fragment of every object.
For $L$ lights and $N$ fragments, this is $O(N \times L)$. Deferred
shading decouples geometry from lighting:

1. **Geometry pass**: render all opaque objects into a G-buffer
   (screen-space textures storing position, normal, albedo, roughness,
   metallic).
2. **Lighting pass**: shade each pixel using the G-buffer data,
   independent of scene complexity.

```glsl
// Lighting pass fragment shader
layout(location = 0) in vec2 uv;
layout(location = 0) out vec4 outColor;

layout(binding = 0) uniform sampler2D gPosition;
layout(binding = 1) uniform sampler2D gNormal;
layout(binding = 2) uniform sampler2D gAlbedoMetallic;
layout(binding = 3) uniform sampler2D gRoughnessAO;

void main() {
    vec3 pos = texture(gPosition, uv).rgb;
    vec3 N = texture(gNormal, uv).rgb;
    vec3 albedo = texture(gAlbedoMetallic, uv).rgb;
    float metallic = texture(gAlbedoMetallic, uv).a;
    float roughness = texture(gRoughnessAO, uv).r;

    vec3 Lo = vec3(0.0);
    for (int i = 0; i < lightCount; i++) {
        Lo += evaluatePBR(pos, N, albedo, metallic, roughness, lights[i]);
    }
    outColor = vec4(Lo, 1.0);
}
```

The G-buffer's memory footprint is the main drawback: a typical
4-target G-buffer at 1080p consumes ~80 MB. Tiled deferred rendering
reduces this by processing the screen in tiles that fit in cache.

## Screen-Space Ambient Occlusion

SSAO approximates ambient occlusion by sampling the depth buffer around
each pixel and estimating how much of the hemisphere is occluded:

```glsl
float ssao(sampler2D depthMap, vec2 uv, vec3 N, mat4 proj,
           vec3 kernel[SAMPLES], float radius) {
    float occlusion = 0.0;
    float viewZ = linearizeDepth(texture(depthMap, uv).r);
    for (int i = 0; i < SAMPLES; i++) {
        vec3 samplePos = viewPos + kernel[i] * radius;
        vec4 offset = proj * vec4(samplePos, 1.0);
        offset.xyz /= offset.w;
        offset.xy = offset.xy * 0.5 + 0.5;
        float sampleDepth = linearizeDepth(texture(depthMap, offset.xy).r);
        float rangeCheck = smoothstep(0.0, 1.0,
            radius / abs(viewZ - sampleDepth));
        occlusion += (sampleDepth <= samplePos.z ? 1.0 : 0.0) * rangeCheck;
    }
    return 1.0 - (occlusion / float(SAMPLES));
}
```

The sample kernel is generated as random points on a hemisphere,
rotated per-pixel using a noise texture to break up banding. A blur
pass removes the remaining noise.

## Screen-Space Reflections

SSR ray-marches through the depth buffer to find reflections of
objects already visible on screen:

1. Compute the reflection direction from the view direction and normal.
2. March along the reflection direction in screen space.
3. At each step, compare the ray's depth to the depth buffer.
4. When the ray goes behind a surface, binary-search for the
   intersection point.

SSR cannot reflect objects outside the view frustum. A common
fallback is to blend SSR with environment map reflections using the
roughness and the ray's screen-space validity.

## Temporal Anti-Aliasing (TAA)

TAA accumulates multiple frames with sub-pixel jitter to produce
anti-aliased output at the cost of a single sample per pixel per
frame:

1. Jitter the projection matrix by a sub-pixel offset (Halton sequence).
2. Render the frame.
3. Reproject the previous frame using motion vectors.
4. Blend the current and reprojected previous frame.

```glsl
// Neighborhood clipping prevents ghosting
vec3 clipToAABB(vec3 history, vec3 current, vec3 minNeighbor, vec3 maxNeighbor) {
    vec3 p_clip = 0.5 * (maxNeighbor + minNeighbor);
    vec3 e_clip = 0.5 * (maxNeighbor - minNeighbor);
    vec3 v = history - p_clip;
    vec3 v_unit = v / e_clip;
    float a = max(abs(v_unit.x), max(abs(v_unit.y), abs(v_unit.z)));
    return a > 1.0 ? p_clip + v / a : history;
}
```

Neighborhood clamping (the function above) rejects history values
outside the current frame's color range, preventing ghosting at
disocclusions.

## GPU-Driven Rendering

Modern engines minimize CPU-GPU synchronization by generating draw
calls on the GPU itself:

1. **Frustum culling** in a compute shader: test each mesh's bounding
   volume against the frustum planes and write visible indices to a
   buffer.
2. **Indirect draw**: use `vkCmdDrawIndexedIndirect` with the culled
   buffer as the indirect argument source.
3. **Depth pre-pass**: render only depth for visible meshes to prime
   the depth buffer.
4. **Shading pass**: render visible meshes with depth test enabled
   (early-z rejects occluded fragments).

This approach scales to millions of objects with near-constant CPU
cost, as the CPU only records the initial dispatch.

## Volumetric Rendering

Fog, smoke, and light shafts require rendering participating media.
The radiative transfer equation describes light attenuation and
in-scattering along a ray:

$$
L(d) = L(0) \, e^{-\int_0^d \sigma_t \, ds} + \int_0^d e^{-\int_s^d \sigma_t \, ds'} \, \sigma_s \, L_i(s) \, ds
$$

Real-time implementations ray-march through a 3D froxel grid
(frustum-aligned voxel grid), accumulating scattering and extinction
at each step. The result is composited over the opaque scene using
the accumulated transmittance.

## Level of Detail

Mesh complexity is reduced at distance. Approaches:

- **Discrete LOD**: pre-authored mesh variants swapped at distance
  thresholds. Simple but can pop.
- **Continuous LOD (geomorphing)**: interpolate vertex positions
  between LOD levels to eliminate pops.
- **Nanite-style virtualized geometry**: a clustered LOD system that
  streams triangle clusters at per-pixel resolution, selecting the
  appropriate LOD per-cluster on the GPU. No authored LODs required.

The virtualized approach relies on compute-based culling, indirect
draws, and a streaming system that loads cluster data on demand.
