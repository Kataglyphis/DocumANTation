# The Vulkan API

Vulkan is a low-overhead, explicit graphics and compute API. Unlike
OpenGL, which hides driver behavior behind a state machine, Vulkan
exposes the GPU's resource model directly: the application manages
memory, synchronization, and pipeline state explicitly. This control
enables better performance at the cost of more code.

## Core Concepts

### Instances and Devices

```c
VkInstanceCreateInfo instInfo = {
    .sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
    .pApplicationInfo = &appInfo,
    .enabledLayerCount = layerCount,
    .ppEnabledLayerNames = layers,
    .enabledExtensionCount = extCount,
    .ppEnabledExtensionNames = extensions,
};
vkCreateInstance(&instInfo, NULL, &instance);
```

A physical device represents a GPU. A logical device is the application's
handle to that GPU, created with specific queue families and extensions:

```c
float queuePriority = 1.0f;
VkDeviceQueueCreateInfo queueInfo = {
    .sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
    .queueFamilyIndex = graphicsFamily,
    .queueCount = 1,
    .pQueuePriorities = &queuePriority,
};
VkDeviceCreateInfo devInfo = {
    .sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
    .queueCreateInfoCount = 1,
    .pQueueCreateInfos = &queueInfo,
    .enabledExtensionCount = devExtCount,
    .ppEnabledExtensionNames = devExtensions,
};
vkCreateDevice(physicalDevice, &devInfo, NULL, &device);
```

### Command Buffers

All GPU work is recorded into command buffers, which are submitted to
queues for execution. Recording is CPU-side; execution is GPU-side:

```c
VkCommandBufferBeginInfo beginInfo = {
    .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
    .flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT,
};
vkBeginCommandBuffer(cmd, &beginInfo);

vkCmdBeginRenderPass(cmd, &rpBegin, VK_SUBPASS_CONTENTS_INLINE);
vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline);
vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS,
                        pipelineLayout, 0, 1, &descriptorSet, 0, NULL);
vkCmdBindVertexBuffers(cmd, 0, 1, &vertexBuffer, &offset);
vkCmdBindIndexBuffer(cmd, indexBuffer, 0, VK_INDEX_TYPE_UINT32);
vkCmdDrawIndexed(cmd, indexCount, 1, 0, 0, 0);
vkCmdEndRenderPass(cmd);

vkEndCommandBuffer(cmd);
```

### Synchronization

Vulkan does not guarantee execution or memory visibility order between
commands. The application must express dependencies explicitly:

**Pipeline barriers** synchronize stages within a command buffer:

```c
VkImageMemoryBarrier barrier = {
    .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
    .srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
    .dstAccessMask = VK_ACCESS_SHADER_READ_BIT,
    .oldLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
    .newLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
    .image = colorImage,
    .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 },
};
vkCmdPipelineBarrier(cmd,
    VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
    VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,
    0, 0, NULL, 0, NULL, 1, &barrier);
```

**Semaphores** synchronize between queue submissions (e.g., image
acquisition before rendering, rendering before presentation).

**Fences** signal the CPU when the GPU has completed a submission.

### Render Passes

A render pass describes the attachments (color, depth, resolve),
subpasses, and dependencies for a rendering operation:

```c
VkAttachmentDescription colorAttachment = {
    .format = swapchainFormat,
    .samples = VK_SAMPLE_COUNT_1_BIT,
    .loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR,
    .storeOp = VK_ATTACHMENT_STORE_OP_STORE,
    .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
    .finalLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
};
```

Render passes enable tile-based GPUs to keep the entire frame in
on-chip memory, avoiding costly framebuffer reads and writes.

## Descriptor Sets

Descriptors bind resources (buffers, images, samplers) to shader
bindings. They are organized into sets, each corresponding to a
`layout(set = N)` in the shader:

```c
VkDescriptorSetLayoutBinding bindings[] = {
    { 0, VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, 1, VK_SHADER_STAGE_ALL, NULL },
    { 1, VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 1, VK_SHADER_STAGE_FRAGMENT_BIT, NULL },
};
```

Descriptor sets are allocated from pools and updated with
`vkUpdateDescriptorSets`. For frequently changing descriptors,
push descriptors or descriptor indexing (bindless) avoid the
update cost.

## Memory Management

Vulkan exposes the GPU's memory hierarchy directly. The application
queries memory types and allocates from heaps with specific properties:

| Property | Meaning |
|:---------|:--------|
| `DEVICE_LOCAL` | Fast GPU memory (VRAM) |
| `HOST_VISIBLE` | CPU-mappable |
| `HOST_COHERENT` | No explicit flush/invalidate needed |

The optimal strategy allocates large blocks from `DEVICE_LOCAL` memory
and sub-allocates for individual resources, using a memory allocator
like Vulkan Memory Allocator (VMA).

## Dynamic Rendering

Vulkan 1.3 introduced `VK_KHR_dynamic_rendering`, which removes the
need for render pass and framebuffer objects. Rendering is specified
inline:

```c
VkRenderingAttachmentInfo colorAttachment = {
    .sType = VK_STRUCTURE_TYPE_RENDERING_ATTACHMENT_INFO,
    .imageView = colorView,
    .imageLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
    .loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR,
    .storeOp = VK_ATTACHMENT_STORE_OP_STORE,
    .clearValue = { .color = {{ 0.0f, 0.0f, 0.0f, 1.0f }} },
};
VkRenderingInfo renderingInfo = {
    .sType = VK_STRUCTURE_TYPE_RENDERING_INFO,
    .renderArea = { {0, 0}, {width, height} },
    .layerCount = 1,
    .colorAttachmentCount = 1,
    .pColorAttachments = &colorAttachment,
};
vkCmdBeginRendering(cmd, &renderingInfo);
```

This simplifies the API considerably for applications that do not need
the tile-based optimization that render passes provide on mobile GPUs.

## Synchronization2

`VK_KHR_synchronization2` (Vulkan 1.3) replaces the barrier API with
a more explicit and less error-prone interface:

```c
VkImageMemoryBarrier2 barrier = {
    .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2,
    .srcStageMask = VK_PIPELINE_STAGE_2_COLOR_ATTACHMENT_OUTPUT_BIT,
    .srcAccessMask = VK_ACCESS_2_COLOR_ATTACHMENT_WRITE_BIT,
    .dstStageMask = VK_PIPELINE_STAGE_2_FRAGMENT_SHADER_BIT,
    .dstAccessMask = VK_ACCESS_2_SHADER_READ_BIT,
    .oldLayout = VK_IMAGE_LAYOUT_ATTACHMENT_OPTIMAL,
    .newLayout = VK_IMAGE_LAYOUT_READ_ONLY_OPTIMAL,
    .image = colorImage,
    .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 },
};
VkDependencyInfo dep = {
    .sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO,
    .imageMemoryBarrierCount = 1,
    .pImageMemoryBarriers = &barrier,
};
vkCmdPipelineBarrier2(cmd, &dep);
```

The key improvement: stage masks and access masks are co-located in the
same structure, eliminating the most common synchronization bug (mismatched
stage/access pairs).
