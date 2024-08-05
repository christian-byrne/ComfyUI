

# Validation Errors

Node authors will sometimes make mistakes which causes validation to fail and the node to not be added to the DB or loaded.

| Repo | Issue | Fix PR | Resolved |
| --- | --- | --- | --- |
| [ImpactPack](https://github.com/ltdrdata/ComfyUI-Impact-Pack) | `ImpactLogger.input.required.data` has tuple with two strings | [#674](https://github.com/ltdrdata/ComfyUI-Impact-Pack/pull/674) | July 17, 2024 |
| [ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use) | `ipadapterApplyFromParams.input.cache_mode` extra input spec dict | [#258](https://github.com/yolain/ComfyUI-Easy-Use/pull/258) |  July 17, 2024 | 
| [ComfyUI-DeepFuze](https://github.com/SamKhoze/ComfyUI-DeepFuze) | `DeepFuzeFaceSwap.required.reference_face_index` extra input spec dict | [#38](https://github.com/SamKhoze/ComfyUI-DeepFuze/pull/38) | _ |
| [ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use) | `XYplot_Negative_Cond.input.optional.negative_1` is string instead of tuple | [#270](https://github.com/yolain/ComfyUI-Easy-Use/pull/270) | July 27, 2024 |
| [mikey_nodes](https://github.com/bash-j/mikey_nodes) | `haldCLUT.return_names` is string instead of tuple | [#31](https://github.com/bash-j/mikey_nodes/pull/31) | July 27, 2024 |
| [ComfyUI-HelperNodes](https://github.com/teward/ComfyUI-Helper-Nodes) | Nodes have null `return_names` from base class | | _ |


# Always Initialize White List

Edit the whitelist in [`load_custom_node`](./nodes.py) function of `nodes.py`.

| Module | Reason(s) |
| --- | --- |
| rgthree-comfy | 1c |
| cg-use-everywhere | 3 |
| comfy_mtb | 1a |
| ComfyUI-Manager | 3 |
| cg-image-picker | 2 |
| ComfyUI-Inspire-Pack | 4 |
| ComfyUI-Impact-Pack | 4 |
| bilbox-comfyui | 1b |
| comfyui-mixlab-nodes | 1a |
| AIGODLIKE-ComfyUI-Translation | 1b, 3 |


### Reasons (Required)

1. Module interacts with frontend via backend, and it happens whether or not their nodes are being used 
   1. Creating routes on PromptServer for a background service
   2. Calls external APIs in order to initialize frontend services that are unrelated to any particular node
   3. Frontend extension files are managed by backend service
   
2. A newly downloaded module imports an older module (e.g., a custom node imports `nodes.latent`, so we need to always initialize `nodes.latent`)

### Reasons (Optional)

These depend on whether you want to allow the feature or not:

3. Module does some backend background job unrelated to any particular node, and you want to ensure that background job is always running (e.g., ComfyUI-Manager)

4. Module either manages dependencies or self-updates and you want to allow that
 
### NOT Reasons

These do not require always initializing the module:

- Module has many frontend features, but those features don't require adding routes or interacting with a server

- Module calls external API on backend in order to intialize service for a particular node (e.g., websocket_image_save example node)

