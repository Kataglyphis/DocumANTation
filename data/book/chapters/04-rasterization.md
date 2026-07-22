# Rasterization

Rasterization converts vector primitives -- typically triangles -- into
discrete fragments that correspond to pixel locations. It is the bridge
between the continuous world of geometry and the discrete world of the
framebuffer.

## Triangle Setup

Before rasterization begins, the hardware computes edge equations for
each triangle. Given vertices $\mathbf{v}_0, \mathbf{v}_1, \mathbf{v}_2$
in screen space, the edge function for edge $i$ evaluates whether a
point is inside, outside, or on the edge:

$$
E_i(x, y) = (x - x_i)(y_{i+1} - y_i) - (y - y_i)(x_{i+1} - x_i)
$$

A point is inside the triangle when all three edge functions have the
same sign (for a consistently wound triangle).

## Coverage Rules

When a pixel center lies exactly on a shared edge, the coverage rule
determines which triangle claims it. The top-left rule assigns the
pixel to the triangle whose edge is a top edge (horizontal, above the
triangle) or a left edge (descending left-to-right).

This guarantees:

- Every pixel is claimed by exactly one triangle (no gaps, no overlaps).
- Adjacent triangles tile perfectly without z-fighting at shared edges.

## Barycentric Coordinates

For a point $\mathbf{p}$ inside triangle $\mathbf{v}_0\mathbf{v}_1\mathbf{v}_2$,
the barycentric coordinates $(\lambda_0, \lambda_1, \lambda_2)$ satisfy:

$$
\mathbf{p} = \lambda_0 \mathbf{v}_0 + \lambda_1 \mathbf{v}_1 + \lambda_2 \mathbf{v}_2
$$

with $\lambda_0 + \lambda_1 + \lambda_2 = 1$ and $\lambda_i \geq 0$.

Barycentric coordinates are computed from the edge functions:

$$
\lambda_i = \frac{E_i(\mathbf{p})}{E_i(\mathbf{v}_{i+2})}
$$

These coordinates interpolate any per-vertex attribute across the triangle:

$$
\text{attr}(\mathbf{p}) = \lambda_0 \cdot \text{attr}_0 + \lambda_1 \cdot \text{attr}_1 + \lambda_2 \cdot \text{attr}_2
$$

## Perspective-Correct Interpolation

Screen-space barycentric interpolation of attributes produces affine
(incorrect) results when the triangle is not parallel to the screen
plane. The correct interpolation divides each attribute by $w$ before
interpolating, then multiplies by the interpolated $1/w$:

$$
\text{attr}_{correct}(\mathbf{p}) = \frac{\lambda_0 \frac{\text{attr}_0}{w_0} + \lambda_1 \frac{\text{attr}_1}{w_1} + \lambda_2 \frac{\text{attr}_2}{w_2}}{\frac{\lambda_0}{w_0} + \frac{\lambda_1}{w_1} + \frac{\lambda_2}{w_2}}
$$

Modern hardware performs this correction automatically. The GPU
interpolates $1/w$ linearly and uses it to perspective-correct all
varyings.

## Back-Face Culling

Triangles whose vertices wind clockwise in screen space (when the
application specifies counter-clockwise as front-facing) face away
from the camera and can be discarded before rasterization. For closed
meshes, this eliminates roughly half the triangles:

```c
float cross2d(float ax, float ay, float bx, float by) {
    return ax * by - ay * bx;
}

bool is_front_facing(float x0, float y0, float x1, float y1,
                     float x2, float y2) {
    return cross2d(x1 - x0, y1 - y0, x2 - x0, y2 - y0) > 0.0f;
}
```

In Vulkan, the cull mode and front-face winding are set in the
rasterization state:

```c
VkPipelineRasterizationStateCreateInfo raster = {
    .sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO,
    .cullMode = VK_CULL_MODE_BACK_BIT,
    .frontFace = VK_FRONT_FACE_COUNTER_CLOCKWISE,
    .polygonMode = VK_POLYGON_MODE_FILL,
};
```

## Clipping

Primitives that cross the view frustum boundaries must be clipped before
rasterization. The Sutherland-Hodgman algorithm clips a polygon against
each frustum plane sequentially. A triangle can produce up to a
7-sided polygon after clipping against all six planes.

Guard-band clipping optimizes this: triangles entirely within an
extended region (the guard band) skip clipping entirely. Only
triangles that cross the guard band boundary are clipped. Most
triangles in a typical scene fall within the guard band.

## Subpixel Precision and Sampling

Modern GPUs support multisample anti-aliasing (MSAA), where each pixel
has multiple sample points. The rasterizer tests each sample point
against the edge equations independently. A triangle covering 2 of 4
samples contributes 50% of its color to the final pixel (after the
resolve pass).

The minimum precision for sub-pixel coordinates is typically 8 bits
(256 sub-pixel positions per pixel), which is sufficient to avoid
visible popping during slow camera movement.

## Tile-Based Rasterization

Mobile GPUs (and some desktop architectures) use tile-based deferred
rendering: the screen is divided into small tiles (e.g., 16x16 pixels),
and each tile is rasterized and shaded entirely in on-chip memory before
being flushed to the framebuffer. This dramatically reduces memory
bandwidth, at the cost of a binning pass that sorts triangles into
tiles.

## Conservative Rasterization

Standard rasterization may miss thin triangles that pass between sample
points. Conservative rasterization generates fragments for every pixel
that a triangle's bounding box overlaps, even if no sample point is
inside the triangle. This is useful for:

- Voxelization (no holes in the voxelized mesh)
- Shadow map generation (no light leaking through thin geometry)
- Visibility buffers (no missed occluders)

## Performance Considerations

The rasterizer is rarely the bottleneck on modern desktop GPUs, but
several practices maximize throughput:

- **Avoid long thin triangles**: they cover many tiles but few pixels
  per tile, wasting tile setup.
- **Pre-clip on the CPU** when possible: the hardware clipper serializes
  the pipeline.
- **Use indexed drawing**: shared vertices are transformed once and
  reused across triangles.
- **Minimize overdraw**: sort opaque objects front-to-back so the depth
  test rejects fragments early.
