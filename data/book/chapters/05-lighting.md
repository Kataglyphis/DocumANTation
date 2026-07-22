# Lighting and Shading

Lighting models determine how surfaces interact with light. The choice
of model trades physical accuracy against computational cost: real-time
applications use local models that approximate global effects, while
offline rendering solves the full light transport equation.

## The Rendering Equation

Kajiya's rendering equation (1986) describes the complete light
transport at a surface point:

$$
L_o(\mathbf{x}, \omega_o) = L_e(\mathbf{x}, \omega_o) + \int_\Omega f_r(\mathbf{x}, \omega_i, \omega_o) \, L_i(\mathbf{x}, \omega_i) \, (\omega_i \cdot \mathbf{n}) \, d\omega_i
$$

where:

- $L_o$ is the outgoing radiance in direction $\omega_o$
- $L_e$ is the emitted radiance (light sources)
- $f_r$ is the bidirectional reflectance distribution function (BRDF)
- $L_i$ is the incoming radiance from direction $\omega_i$
- $\omega_i \cdot \mathbf{n}$ is the cosine of the incident angle

Every lighting model in this chapter is an approximation of this
integral.

## Phong Reflection Model

The Phong model decomposes reflected light into three components:

$$
I = k_a I_a + k_d I_d \max(\mathbf{L} \cdot \mathbf{N}, 0) + k_s I_s \max(\mathbf{R} \cdot \mathbf{V}, 0)^{\alpha}
$$

| Term | Meaning |
|:-----|:--------|
| Ambient ($k_a I_a$) | Constant fill light approximation |
| Diffuse ($k_d I_d$) | Lambertian scattering, view-independent |
| Specular ($k_s I_s$) | Mirror-like reflection, view-dependent |

The specular exponent $\alpha$ controls the highlight size: large
values produce tight, sharp highlights (polished surfaces), while
small values produce broad, soft highlights (rough surfaces).

```glsl
vec3 phong(vec3 N, vec3 L, vec3 V, vec3 lightColor,
           float ka, float kd, float ks, float shininess) {
    float diff = max(dot(N, L), 0.0);
    vec3 R = reflect(-L, N);
    float spec = pow(max(dot(R, V), 0.0), shininess);
    return ka * lightColor + kd * diff * lightColor + ks * spec * lightColor;
}
```

## Blinn-Phong

Blinn's modification replaces the reflection vector with the half-angle
vector, which is cheaper to compute and produces smoother highlights:

$$
\mathbf{H} = \frac{\mathbf{L} + \mathbf{V}}{\|\mathbf{L} + \mathbf{V}\|}
$$

$$
I_{spec} = k_s I_s \max(\mathbf{N} \cdot \mathbf{H}, 0)^{\alpha'}
$$

The Blinn-Phong exponent $\alpha'$ must be approximately $4\times$ the
Phong exponent to produce highlights of the same size.

## Gouraud vs. Phong Shading

**Gouraud shading** computes the lighting equation at each vertex and
interpolates the resulting colors across the triangle. It is cheap but
misses specular highlights that fall in the interior of a large triangle.

**Phong shading** interpolates the normal across the triangle and
evaluates the lighting equation per fragment. It captures interior
highlights correctly at the cost of per-pixel computation.

Modern GPUs make per-fragment shading the default; Gouraud shading is
only used for flat-shaded or unlit geometry.

## Normal Mapping

Surface detail finer than the mesh resolution is encoded in a normal
map: a texture storing per-texel normal perturbations in tangent space.
The fragment shader transforms these normals into world space using a
TBN matrix:

$$
\mathbf{TBN} = \begin{pmatrix} \mathbf{T} & \mathbf{B} & \mathbf{N} \end{pmatrix}
$$

where $\mathbf{T}$ is the tangent, $\mathbf{B}$ is the bitangent, and
$\mathbf{N}$ is the geometric normal.

```glsl
vec3 getNormal(sampler2D normalMap, vec2 uv,
               vec3 N, vec3 T, vec3 B) {
    vec3 tangentNormal = texture(normalMap, uv).xyz * 2.0 - 1.0;
    mat3 TBN = mat3(normalize(T), normalize(B), normalize(N));
    return normalize(TBN * tangentNormal);
}
```

The tangent and bitangent are computed from UV gradients during mesh
loading, or derived in the vertex shader using partial derivatives.

## Physically Based Rendering

PBR replaces empirical models with physically motivated BRDFs that
obey energy conservation and reciprocity.

### Cook-Torrance BRDF

The microfacet model treats a surface as a collection of tiny perfect
mirrors. Only those microfacets oriented along the half-angle vector
reflect light toward the viewer:

$$
f_r = \frac{D(\mathbf{H}) \, F(\mathbf{V}, \mathbf{H}) \, G(\mathbf{L}, \mathbf{V}, \mathbf{H})}{4 \, (\mathbf{N} \cdot \mathbf{L}) \, (\mathbf{N} \cdot \mathbf{V})}
$$

| Factor | Models |
|:-------|:-------|
| $D$ (Normal distribution) | Roughness: how microfacet normals cluster around $\mathbf{N}$ |
| $F$ (Fresnel) | Reflectance increases at grazing angles |
| $G$ (Geometry/Shadowing) | Microfacets occlude each other |

The GGX/Trowbridge-Reitz distribution is the current standard for $D$:

$$
D_{GGX}(\mathbf{H}) = \frac{\alpha^2}{\pi \left((\mathbf{N} \cdot \mathbf{H})^2 (\alpha^2 - 1) + 1\right)^2}
$$

where $\alpha$ is the roughness parameter ($0$ = mirror, $1$ = rough).

### Fresnel-Schlick

The full Fresnel equations are expensive. Schlick's approximation is
accurate enough for real-time rendering:

$$
F(\mathbf{V}, \mathbf{H}) = F_0 + (1 - F_0)(1 - \mathbf{V} \cdot \mathbf{H})^5
$$

$F_0$ is the reflectance at normal incidence: approximately $0.04$ for
dielectrics and the linear albedo for metals.

### Metallic-Roughness Workflow

The most common PBR parameterization uses two scalar textures:

- **Metallic** ($0$ = dielectric, $1$ = metal): controls whether the
  surface reflects colored (metal) or uncolored (dielectric) specular.
- **Roughness** ($0$ = smooth, $1$ = rough): controls the GGX $\alpha$.

The albedo texture stores the base color, which is the diffuse color
for dielectrics and the $F_0$ for metals.

## Shadows

### Shadow Mapping

The most widely used real-time shadow technique. A depth map is rendered
from the light's perspective; during the main pass, each fragment's
position is projected into the light's clip space and compared against
the stored depth:

```glsl
float shadowFactor(sampler2D shadowMap, vec4 lightSpacePos,
                   mat4 lightVP, vec3 worldPos, vec3 N, vec3 L) {
    vec3 projCoords = lightSpacePos.xyz / lightSpacePos.w;
    projCoords = projCoords * 0.5 + 0.5;
    float closestDepth = texture(shadowMap, projCoords.xy).r;
    float currentDepth = projCoords.z;
    float bias = max(0.005 * (1.0 - dot(N, L)), 0.001);
    return currentDepth - bias > closestDepth ? 0.0 : 1.0;
}
```

Shadow acne (self-shadowing artifacts) is mitigated by a depth bias.
Peter-panning (shadows detaching from objects) is the trade-off when
the bias is too large. Percentage-closer filtering (PCF) softens the
shadow edges by sampling a neighborhood and averaging.

### Cascaded Shadow Maps

For directional lights (sunlight), the shadow map must cover the entire
view frustum. Cascaded shadow maps split the frustum into depth slices,
each with its own shadow map at a different resolution. Near slices get
high resolution; far slices get lower resolution.
