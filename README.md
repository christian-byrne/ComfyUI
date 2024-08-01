> [!TIP]
>
> Use with new frontend for type validation: `--front-end-version Comfy-Org/ComfyUI_frontend@latest`
> 

# Errors

> `RuntimeError: Cannot register a resource into a frozen router`
 
<details>
<summary>Details</summary>

From [aio-libs/aiohttp#1540](https://github.com/aio-libs/aiohttp/issues/1540):

- `aiohttp` server instance won't allow adding routes after the server has started receiving requests.
- You can add  logic somewhere to unfreeze the router for initailization of specific nodes, or just always unfreeze when initializing. For example:
    ```python
    @routes.get("/object_info")
    async def get_object_info(request):
        request.app.router._frozen = False
        res = await node_info(list(nodes.NODE_CLASS_MAPPINGS.keys()))
        request.app.router._frozen = True
        return res
    
    @routes.get("/object_info/{node_class}")
    async def get_object_info_node(request):
        node_class = request.match_info.get("node_class", None)
        if (node_class is not None) and (node_class in nodes.NODE_CLASS_MAPPINGS):
            request.app.router._frozen = False
            res = await node_info([node_class])
            request.app.router._frozen = True
            return res
        else:
            return web.json_response({})
    ```

</details>

---

> `pydantic_core._pydantic_core.ValidationError`

<details>
<summary>Details</summary>

Node authors will sometimes make mistakes which causes validation to fail and the node to not be loaded.

| Repo | Issue | Fix PR | Resolved |
| --- | --- | --- | --- |
| [ImpactPack](https://github.com/ltdrdata/ComfyUI-Impact-Pack) | `ImpactLogger.input.required.data` has tuple with two strings | [#674](https://github.com/ltdrdata/ComfyUI-Impact-Pack/pull/674) | July 17, 2024 |
| [ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use) | `ipadapterApplyFromParams.input.cache_mode` extra input spec dict | [#258](https://github.com/yolain/ComfyUI-Easy-Use/pull/258) |  July 17, 2024 | 
| [ComfyUI-DeepFuze](https://github.com/SamKhoze/ComfyUI-DeepFuze) | `DeepFuzeFaceSwap.required.reference_face_index` extra input spec dict | [#38](https://github.com/SamKhoze/ComfyUI-DeepFuze/pull/38) | _ |
| [ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use) | `XYplot_Negative_Cond.input.optional.negative_1` is string instead of tuple | [#270](https://github.com/yolain/ComfyUI-Easy-Use/pull/270) | July 27, 2024 |
| [mikey_nodes](https://github.com/bash-j/mikey_nodes) | `haldCLUT.return_names` is string instead of tuple | [#31](https://github.com/bash-j/mikey_nodes/pull/31) | July 27, 2024 |
| [ComfyUI-HelperNodes](https://github.com/teward/ComfyUI-Helper-Nodes) | Nodes have null `return_names` from base class | | _ |


</details>

---

# Known Problematic Modules

-

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

