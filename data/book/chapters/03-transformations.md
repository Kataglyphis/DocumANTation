# Transformations and Projections

Every vertex in a 3D scene passes through a chain of coordinate spaces
before it reaches the screen. Understanding these spaces -- and the
matrices that transform between them -- is essential for camera control,
animation, lighting, and debugging rendering artifacts.

## Coordinate Spaces

The standard chain is:

$$
\mathbf{v}_{model} \xrightarrow{\mathbf{M}} \mathbf{v}_{world} \xrightarrow{\mathbf{V}} \mathbf{v}_{view} \xrightarrow{\mathbf{P}} \mathbf{v}_{clip} \xrightarrow{\div w} \mathbf{v}_{ndc} \xrightarrow{viewport} \mathbf{v}_{screen}
$$

Each space serves a purpose:

| Space | Purpose | Origin |
|:------|:--------|:-------|
| Model | Per-object, as authored | Object center |
| World | Shared scene reference | Arbitrary |
| View | Camera-relative | Camera position |
| Clip | After projection, before divide | Homogeneous |
| NDC | Normalized, $[-1, 1]^3$ | Screen center |
| Screen | Pixel coordinates | Top-left or bottom-left |

## Model Matrix

The model matrix $\mathbf{M}$ places an object in the world. It is
typically composed from translation, rotation, and scale:

$$
\mathbf{M} = \mathbf{T} \cdot \mathbf{R} \cdot \mathbf{S}
$$

Rotation can be represented as Euler angles, a rotation matrix, or a
quaternion. Quaternions avoid gimbal lock and interpolate smoothly
(SLERP), making them the preferred representation for animation:

```c
typedef struct {
    float w, x, y, z;
} Quat;

static Quat quat_mul(Quat a, Quat b) {
    return (Quat){
        a.w*b.w - a.x*b.x - a.y*b.y - a.z*b.z,
        a.w*b.x + a.x*b.w + a.y*b.z - a.z*b.y,
        a.w*b.y - a.x*b.z + a.y*b.w + a.z*b.x,
        a.w*b.z + a.x*b.y - a.y*b.x + a.z*b.w,
    };
}

static Quat quat_normalize(Quat q) {
    float inv = 1.0f / sqrtf(q.w*q.w + q.x*q.x + q.y*q.y + q.z*q.z);
    return (Quat){ q.w*inv, q.x*inv, q.y*inv, q.z*inv };
}
```

## View Matrix

The view matrix $\mathbf{V}$ transforms world coordinates into
camera-relative coordinates. It is the inverse of the camera's
world-space transform:

$$
\mathbf{V} = \mathbf{M}_{camera}^{-1}
$$

A common construction uses the look-at formulation:

$$
\mathbf{V} = \begin{pmatrix}
\mathbf{r}_x & \mathbf{r}_y & \mathbf{r}_z & -\mathbf{r} \cdot \mathbf{e} \\
\mathbf{u}_x & \mathbf{u}_y & \mathbf{u}_z & -\mathbf{u} \cdot \mathbf{e} \\
-\mathbf{f}_x & -\mathbf{f}_y & -\mathbf{f}_z & \mathbf{f} \cdot \mathbf{e} \\
0 & 0 & 0 & 1
\end{pmatrix}
$$

where $\mathbf{f}$ is the forward direction, $\mathbf{r}$ is the right
vector, $\mathbf{u}$ is the up vector, and $\mathbf{e}$ is the eye
position.

## Projection Matrix

The projection matrix $\mathbf{P}$ maps the view frustum into clip
space. Two standard projections exist:

**Perspective** produces foreshortening -- distant objects appear
smaller. The standard perspective matrix for a symmetric frustum:

$$
\mathbf{P}_{persp} = \begin{pmatrix}
\frac{1}{a \tan(\frac{fov}{2})} & 0 & 0 & 0 \\
0 & \frac{1}{\tan(\frac{fov}{2})} & 0 & 0 \\
0 & 0 & -\frac{f+n}{f-n} & -\frac{2fn}{f-n} \\
0 & 0 & -1 & 0
\end{pmatrix}
$$

where $a$ is the aspect ratio, $fov$ is the vertical field of view,
and $n$, $f$ are the near and far clip planes.

**Orthographic** preserves parallel lines and relative sizes:

$$
\mathbf{P}_{ortho} = \begin{pmatrix}
\frac{2}{r-l} & 0 & 0 & -\frac{r+l}{r-l} \\
0 & \frac{2}{t-b} & 0 & -\frac{t+b}{t-b} \\
0 & 0 & \frac{-2}{f-n} & -\frac{f+n}{f-n} \\
0 & 0 & 0 & 1
\end{pmatrix}
$$

Orthographic projection is used for UI rendering, shadow map
generation, and technical illustration.

## The Homogeneous Divide

After the vertex shader outputs clip coordinates $(x_c, y_c, z_c, w_c)$,
the hardware performs the perspective divide:

$$
\mathbf{v}_{ndc} = \left(\frac{x_c}{w_c},\; \frac{y_c}{w_c},\; \frac{z_c}{w_c}\right)
$$

This is what creates the perspective effect: vertices further from the
camera have larger $w_c$ values, so their NDC coordinates are smaller,
pushing them toward the center of the screen.

## Viewport Transform

The final mapping from NDC to screen coordinates:

$$
x_{screen} = \frac{w_{viewport}}{2} \cdot x_{ndc} + x_{viewport} + \frac{w_{viewport}}{2}
$$

$$
y_{screen} = \frac{h_{viewport}}{2} \cdot y_{ndc} + y_{viewport} + \frac{h_{viewport}}{2}
$$

In Vulkan, the viewport transform is explicit and the Y-axis is inverted
compared to OpenGL (positive Y goes down), which must be accounted for
in the projection matrix or the viewport configuration.

## Normal Transformation

Normals do not transform the same way as positions. When a model matrix
includes non-uniform scaling, the normal must be multiplied by the
inverse transpose of the upper-left 3x3 submatrix:

$$
\mathbf{n}_{world} = (\mathbf{M}^{-1})^T \cdot \mathbf{n}_{model}
$$

For uniform scaling and rigid-body transforms (rotation + translation),
the inverse transpose equals the original matrix, and the simpler
multiplication $\mathbf{M}_{3\times3} \cdot \mathbf{n}$ suffices.

## Depth Precision

The perspective projection maps depth non-linearly: most of the depth
precision is concentrated near the near plane. This is a feature, not a
bug -- it matches the eye's depth perception. However, choosing too
small a near plane wastes precision:

$$
z_{ndc} = \frac{-(f+n) \cdot z_{view} - 2fn}{(f-n) \cdot (-z_{view})}
$$

A near plane of $0.01$ with a far plane of $1000$ allocates roughly
90% of the depth buffer's precision to the first 100 units. For scenes
with extreme depth ranges, a reversed-Z buffer (storing $1 - z$) or a
floating-point depth buffer mitigates z-fighting.
