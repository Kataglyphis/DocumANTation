# Primitives Showcase

This chapter exercises every custom environment available in the
Kataglyphis-DocumANTation pipeline. Each block below is written in pure
Markdown fenced-div syntax — no raw LaTeX — and renders identically in the
book, the beamer slides, and (where applicable) the Sphinx website.

## Admonitions

::: {.note title="Brand consistency"}
All four outputs (book, slides, PowerPoint, website) share the same
`brand.json`. Change one colour, rebuild, and every output rebrands.
:::

::: {.warning title="Common Vulkan pitfall"}
Barrier stage/access mismatch is the single most common synchronization bug.
Always verify that the `srcStageMask` covers the pipeline stage that wrote the
resource.
:::

::: {.tip title="Performance"}
Prefer push constants over UBOs for data that changes per draw call and fits
in 128 bytes. Push constants avoid descriptor set updates entirely.
:::

::: {.important title="Memory safety"}
Never free a `VkDeviceMemory` object while a command buffer referencing it is
still pending. Use fences or semaphores to guarantee the GPU has finished.
:::

::: {.example title="Minimal compute dispatch"}
A compute pipeline with a single shader stage, one descriptor set, and push
constants is the fastest path for GPU-side work that does not need a
framebuffer.
:::

## Theorems and proofs

::: definition
A **BRDF** (Bidirectional Reflectance Distribution Function) $f_r(\omega_i,
\omega_o)$ describes the ratio of reflected radiance in direction $\omega_o$
to incident irradiance from direction $\omega_i$ at a surface point.
:::

::: theorem
The rendering equation (Kajiya 1986) states that the outgoing radiance
$L_o(x, \omega_o)$ at a surface point $x$ in direction $\omega_o$ is:

$$L_o(x, \omega_o) = L_e(x, \omega_o) + \int_{\Omega} f_r(x, \omega_i, \omega_o) \, L_i(x, \omega_i) \, (\omega_i \cdot n) \, d\omega_i$$
:::

::: corollary
For a perfectly diffuse (Lambertian) surface with albedo $\rho$, the BRDF
reduces to the constant $f_r = \rho / \pi$.
:::

::: proof
Energy conservation requires $\int_\Omega f_r \cos\theta_i \, d\omega_i \leq 1$.
For a constant BRDF $f_r = c$, the integral evaluates to $c \cdot \pi$, so
$c \leq 1/\pi$. Setting $c = \rho/\pi$ with $\rho \in [0,1]$ satisfies this.
:::

## Code blocks with titles

```glsl {.listing title="vertex_shader.glsl"}
#version 450

layout(location = 0) in vec3 inPosition;
layout(location = 1) in vec2 inTexCoord;

layout(location = 0) out vec2 fragTexCoord;

layout(push_constant) uniform PushConstants {
    mat4 modelViewProj;
} pc;

void main() {
    gl_Position = pc.modelViewProj * vec4(inPosition, 1.0);
    fragTexCoord = inTexCoord;
}
```

```rust {.listing title="src/gpu/device.rs"}
pub fn create_device(instance: &ash::Instance, physical: vk::PhysicalDevice)
    -> Result<(ash::Device, vk::Queue), GpuError>
{
    let queue_priority = [1.0_f32];
    let queue_info = vk::DeviceQueueCreateInfo::default()
        .queue_family_index(0)
        .queue_priorities(&queue_priority);

    let device_info = vk::DeviceCreateInfo::default()
        .queue_create_infos(std::slice::from_ref(&queue_info));

    let device = unsafe { instance.create_device(physical, &device_info, None)? };
    let queue = unsafe { device.get_device_queue(0, 0) };

    Ok((device, queue))
}
```

## Two-column layouts

::: {.columns}

::: {.column}
**Forward rendering**

- Simple, single pass per object
- No intermediate buffers
- Limited to O(n) lights cheaply
:::

::: {.column}
**Deferred rendering**

- G-Buffer pass + lighting pass
- Supports O(1000s) lights
- Higher memory bandwidth
:::

:::

## Code with line numbers

```rust {.listing title="src/render/pipeline.rs" linenos="true"}
pub struct RenderPipeline {
    device: Arc<Device>,
    layout: vk::PipelineLayout,
    graphics: vk::Pipeline,
    compute: vk::Pipeline,
}

impl RenderPipeline {
    pub fn new(device: Arc<Device>) -> Result<Self> {
        let layout = device.create_pipeline_layout()?;
        let graphics = device.create_graphics_pipeline(&layout)?;
        let compute = device.create_compute_pipeline(&layout)?;
        Ok(Self { device, layout, graphics, compute })
    }
}
```

## Tab sets (multi-language comparison)

::: {.tab-set}

::: {.tab title="Rust"}
**Rust** provides memory safety without garbage collection via ownership
and borrowing. The `Arc<Device>` pattern enables shared GPU resource
handles across threads.
:::

::: {.tab title="C++"}
**C++** gives direct control over memory layout and GPU resource
lifetimes. RAII patterns (`std::unique_ptr`) manage Vulkan handles.
:::

::: {.tab title="GLSL"}
**GLSL** shaders run on the GPU. `layout(push_constant)` provides
the fastest uniform path — no descriptor set update needed.
:::

:::

## Glossary terms from Markdown

The [GPU]{.gls} processes vertices through the rasterization stage.
A [BRDF]{.nomen def="Bidirectional Reflectance Distribution Function"}
describes how light reflects off a surface. [SSAO]{.nomen def="Screen-Space
Ambient Occlusion"} approximates ambient light using depth buffer samples.

## Summary

Every block above was written in pure Markdown — no `{=latex}` raw blocks,
no `\begin{...}` escapes. The Pandoc Lua filter `brand-divs.lua` maps the
fenced divs to LaTeX environments in the PDF build and preserves them as
HTML divs for the Sphinx website.
