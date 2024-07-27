> [!TIP]
>
> Strongly recommend using with the new frontend: `--front-end-version Comfy-Org/ComfyUI_frontend@latest`
> 

# Errors

### `RuntimeError: Cannot register a resource into a frozen router` when initializing nodes that add routes

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



### `pydantic_core._pydantic_core.ValidationError` when loading node defs from db

- Sometimes node's fail type validation because the node author accidentally defined a tuple like `RETURN_NAMES = ("name")`
  - [Example](https://github.com/bash-j/mikey_nodes/pull/31), [Example](https://github.com/yolain/ComfyUI-Easy-Use/pull/270)
- In general, the type def may need adjusting or to be loosened in some cases.