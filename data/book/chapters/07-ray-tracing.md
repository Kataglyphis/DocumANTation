# Ray Tracing

Ray tracing reverses the question of rasterization. Instead of asking
"which pixels does this triangle cover?", it asks "what does this pixel
see?" For each pixel, a ray is cast into the scene, and its intersections
with geometry determine the visible surface and its illumination.

## The Basic Algorithm

Whitted-style ray tracing (1980) recursively traces rays:

1. **Camera ray**: cast from the eye through the pixel center.
2. **Intersection**: find the closest object hit by the ray.
3. **Shading**: evaluate the lighting model at the hit point.
4. **Secondary rays**: cast reflection, refraction, and shadow rays.

```c
typedef struct {
    float t;
    Vec3 point;
    Vec3 normal;
    int material_id;
} Hit;

typedef struct {
    Vec3 origin;
    Vec3 dir;
} Ray;

static Vec3 trace(Ray ray, int depth) {
    if (depth <= 0) return (Vec3){0, 0, 0};

    Hit hit;
    if (!scene_intersect(ray, &hit))
        return sky_color(ray.dir);

    Vec3 color = shade(hit, ray);

    if (material_is_reflective(hit.material_id)) {
        Vec3 R = reflect(ray.dir, hit.normal);
        Ray refl = { .origin = hit.point, .dir = R };
        Vec3 refl_color = trace(refl, depth - 1);
        color = vec3_add(color, vec3_scale(refl_color, material_reflectance(hit.material_id)));
    }

    return color;
}
```

## Ray-Primitive Intersection

### Ray-Triangle

The Möller-Trumbore algorithm tests a ray against a triangle without
pre-computing the plane equation:

$$
\begin{pmatrix} -\mathbf{d} & \mathbf{e}_1 & \mathbf{e}_2 \end{pmatrix}
\begin{pmatrix} t \\ u \\ v \end{pmatrix} = \mathbf{o} - \mathbf{v}_0
$$

Solved via Cramer's rule. The hit is valid when $t > 0$, $u \geq 0$,
$v \geq 0$, and $u + v \leq 1$.

```c
static bool intersect_triangle(Ray ray, Vec3 v0, Vec3 v1, Vec3 v2,
                               float *t_out, float *u_out, float *v_out) {
    Vec3 e1 = vec3_sub(v1, v0);
    Vec3 e2 = vec3_sub(v2, v0);
    Vec3 h = vec3_cross(ray.dir, e2);
    float a = vec3_dot(e1, h);
    if (fabsf(a) < 1e-8f) return false;

    float f = 1.0f / a;
    Vec3 s = vec3_sub(ray.origin, v0);
    float u = f * vec3_dot(s, h);
    if (u < 0.0f || u > 1.0f) return false;

    Vec3 q = vec3_cross(s, e1);
    float v = f * vec3_dot(ray.dir, q);
    if (v < 0.0f || u + v > 1.0f) return false;

    float t = f * vec3_dot(e2, q);
    if (t < 1e-4f) return false;

    *t_out = t; *u_out = u; *v_out = v;
    return true;
}
```

### Ray-Sphere

The analytic solution intersects a ray with a sphere of radius $r$
centered at $\mathbf{c}$:

$$
t = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$

where $a = \mathbf{d} \cdot \mathbf{d}$, $b = 2(\mathbf{o} - \mathbf{c}) \cdot \mathbf{d}$,
$c = (\mathbf{o} - \mathbf{c}) \cdot (\mathbf{o} - \mathbf{c}) - r^2$.

## Acceleration Structures

A naive ray tracer tests every ray against every triangle -- $O(NR)$
for $N$ triangles and $R$ rays. Acceleration structures reduce this
to $O(R \log N)$ on average.

### Bounding Volume Hierarchy (BVH)

A BVH recursively partitions geometry into bounding boxes. Each
internal node stores an axis-aligned bounding box (AABB) enclosing
all its children. Leaf nodes contain a small number of triangles.

Ray traversal descends the tree, testing the ray against each node's
AABB using the slab method. Subtrees whose AABBs are not hit are
pruned entirely:

```c
static bool intersect_aabb(Ray ray, Vec3 bmin, Vec3 bmax, float *tmin_out) {
    float tmin = -INFINITY, tmax = INFINITY;
    for (int i = 0; i < 3; i++) {
        float invD = 1.0f / ray.dir.data[i];
        float t0 = (bmin.data[i] - ray.origin.data[i]) * invD;
        float t1 = (bmax.data[i] - ray.origin.data[i]) * invD;
        if (invD < 0.0f) { float tmp = t0; t0 = t1; t1 = tmp; }
        tmin = fmaxf(tmin, t0);
        tmax = fminf(tmax, t1);
        if (tmax < tmin) return false;
    }
    *tmin_out = tmin;
    return true;
}
```

BVH construction uses the Surface Area Heuristic (SAH) to choose split
planes that minimize the expected traversal cost:

$$
C_{split} = \frac{S_L}{S_P} N_L \cdot C_{isect} + \frac{S_R}{S_P} N_R \cdot C_{isect} + C_{traverse}
$$

where $S_L$, $S_R$, $S_P$ are the surface areas of the left child,
right child, and parent respectively.

### k-d Trees

k-d trees split space with axis-aligned planes. They are efficient for
point location and static scenes but do not handle large overlapping
primitives as well as BVHs. BVHs have largely superseded k-d trees in
modern ray tracers.

## Path Tracing

Whitted ray tracing produces perfect mirrors and glass but cannot
render diffuse interreflection (color bleeding) or soft shadows from
area lights. Path tracing (Kajiya, 1986) solves the full rendering
equation by Monte Carlo integration.

At each surface intersection, a path tracer samples one or more
directions according to the BRDF's probability distribution and
recursively traces new rays. The final pixel color is the average
of many such paths:

$$
L_o \approx \frac{1}{N} \sum_{i=1}^{N} \frac{f_r(\omega_i, \omega_o) \, L_i(\omega_i) \, (\omega_i \cdot \mathbf{n})}{p(\omega_i)}
$$

where $p(\omega_i)$ is the probability density of sampling direction
$\omega_i$.

### Noise and Convergence

Monte Carlo estimation produces noisy images that converge at rate
$O(1/\sqrt{N})$. Doubling the quality requires quadrupling the sample
count. Denoising algorithms (temporal accumulation, neural denoisers)
make real-time path tracing feasible at 1-4 samples per pixel.

### Importance Sampling

Sampling uniformly over the hemisphere wastes rays in directions that
contribute little light. Importance sampling draws directions from a
distribution proportional to the BRDF or the incoming radiance:

- **Cosine-weighted hemisphere**: matches the Lambertian BRDF.
- **GGX VNDF**: matches the microfacet distribution for specular.
- **Light sampling**: draws directions toward known light sources.

Multiple importance sampling (MIS) combines these strategies to reduce
variance without bias.

## Hardware Ray Tracing

NVIDIA RT cores, AMD Ray Accelerators, and Apple's ray tracing
support provide fixed-function hardware for BVH traversal and
ray-triangle intersection. The VK_KHR_ray_tracing_pipeline and
VK_KHR_ray_query extensions expose this through Vulkan:

- **Ray tracing pipeline**: a separate shader stage (ray generation,
  closest hit, miss, any hit, intersection) invoked by `traceRayEXT`.
- **Ray query**: inline intersection queries callable from any shader
  stage, enabling hybrid rendering (rasterization + ray-traced shadows
  or reflections).
