# Texturing

Textures add detail to surfaces beyond what the mesh geometry provides.
A texture is a 2D (or 3D) array of texels that is sampled using
coordinates interpolated across the surface.

## UV Mapping

Each vertex carries 2D texture coordinates $(u, v)$ that map it to a
position on the texture. The rasterizer interpolates these coordinates
across the triangle, and the fragment shader uses them to look up
texel values.

UV unwrapping is the process of flattening a 3D mesh onto a 2D plane
with minimal distortion. Common approaches:

- **Box projection**: six axis-aligned projections, blended at seams.
- **Cylindrical/spherical**: suitable for roughly cylindrical or
  spherical objects.
- **Automatic unwrapping**: algorithms like ABF++ or LSCM minimize
  angle and area distortion.

## Texture Filtering

When a fragment maps to a non-integer texel coordinate, the GPU must
interpolate between neighboring texels:

| Filter | Method | Quality | Cost |
|:-------|:-------|:--------|:-----|
| Nearest | Single closest texel | Blocky | 1 sample |
| Linear | 2x2 bilinear blend | Smooth | 4 samples |
| Trilinear | Bilinear + mipmap lerp | No mip popping | 8 samples |
| Anisotropic | Elliptical footprint | Sharp at angles | Up to 16 samples |

Anisotropic filtering is essential for surfaces viewed at grazing
angles. Without it, a floor stretching to the horizon blurs into a
uniform color because the texture footprint becomes a long, thin
ellipse that standard bilinear filtering cannot represent.

In Vulkan, filtering is configured in the sampler:

```c
VkSamplerCreateInfo samplerInfo = {
    .sType = VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO,
    .magFilter = VK_FILTER_LINEAR,
    .minFilter = VK_FILTER_LINEAR,
    .mipmapMode = VK_SAMPLER_MIPMAP_MODE_LINEAR,
    .anisotropyEnable = VK_TRUE,
    .maxAnisotropy = 16.0f,
    .addressModeU = VK_SAMPLER_ADDRESS_MODE_REPEAT,
    .addressModeV = VK_SAMPLER_ADDRESS_MODE_REPEAT,
};
```

## Mipmapping

A mipmap chain is a pyramid of pre-filtered texture resolutions, each
half the size of the previous level. When a surface is far from the
camera, the GPU selects a smaller mip level, avoiding the aliasing
that occurs when many texels map to one pixel.

The mip level is chosen based on the screen-space derivatives of the
UV coordinates:

$$
\text{level} = \log_2\left(\max\left(\left\|\frac{\partial (u,v)}{\partial x}\right\|, \left\|\frac{\partial (u,v)}{\partial y}\right\|\right) \cdot \text{texSize}\right)
$$

Trilinear filtering linearly interpolates between the two nearest mip
levels, eliminating the visible transitions (mip popping) that occur
with nearest-level selection.

## Texture Types in PBR

A modern PBR material uses multiple texture maps, each encoding a
different physical property:

| Map | Channels | Purpose |
|:----|:---------|:--------|
| Albedo | RGB | Base color (diffuse for dielectrics, $F_0$ for metals) |
| Normal | RGB | Tangent-space normal perturbation |
| Metallic | R | Metalness (0 = dielectric, 1 = metal) |
| Roughness | R | Surface roughness (0 = mirror, 1 = rough) |
| Ambient Occlusion | R | Pre-computed indirect light occlusion |
| Emissive | RGB | Self-illumination color |
| Height/Displacement | R | Per-texel height offset (parallax or tessellation) |

These are often packed into fewer textures to reduce sampler count:

```glsl
// Common packing: metallic in B, roughness in G, AO in R
vec3 orm = texture(ormMap, uv).rgb;
float ao = orm.r;
float roughness = orm.g;
float metallic = orm.b;
```

## Parallax Occlusion Mapping

Normal maps add shading detail but do not displace the surface. Parallax
occlusion mapping (POM) offsets the UV coordinates based on a height
map, creating the illusion of geometric depth:

```glsl
vec2 parallaxUV(sampler2D heightMap, vec2 uv, vec3 viewDir,
                float scale, int minSteps, int maxSteps) {
    float height = texture(heightMap, uv).r;
    int steps = int(mix(maxSteps, minSteps,
                        abs(dot(vec3(0,0,1), viewDir))));
    float layerDepth = 1.0 / float(steps);
    float currentDepth = 0.0;
    vec2 P = viewDir.xy / viewDir.z * scale;
    vec2 deltaUV = P / float(steps);

    vec2 currentUV = uv;
    float currentH = texture(heightMap, currentUV).r;
    while (currentDepth < currentH) {
        currentUV -= deltaUV;
        currentH = texture(heightMap, currentUV).r;
        currentDepth += layerDepth;
    }

    vec2 prevUV = currentUV + deltaUV;
    float afterH = currentH - currentDepth;
    float beforeH = texture(heightMap, prevUV).r - currentDepth + layerDepth;
    float weight = afterH / (afterH - beforeH);
    return mix(currentUV, prevUV, weight);
}
```

## Environment Mapping

An environment map captures the surrounding light field as a texture.
Cube maps store six faces of a cube centered at a point; equirectangular
maps store a spherical projection as a single 2D texture.

For PBR, the environment map is pre-filtered into two components:

1. **Diffuse irradiance map**: the convolution of the environment with
   a cosine-weighted hemisphere, stored as a low-resolution cube map.
2. **Pre-filtered specular map**: the environment convolved with the
   GGX distribution at various roughness levels, stored in the mip
   chain of a cube map.

The specular lookup uses the roughness to select the mip level:

```glsl
vec3 specularEnv(samplerCube envMap, vec3 R, float roughness) {
    float mipLevel = roughness * MAX_MIP_LEVEL;
    return textureLod(envMap, R, mipLevel).rgb;
}
```

## Texture Compression

Uncompressed RGBA8 textures consume 4 bytes per texel. BC7 (Block
Compression 7) compresses to 1 byte per texel with minimal quality loss
for color textures. BC5 stores two channels (used for normal maps) at
0.5 bytes per texel. ASTC provides variable bit rates and is the
standard for mobile GPUs.

The GPU decompresses on the fly during sampling -- there is no CPU
decompression step and no memory cost beyond the compressed size.
