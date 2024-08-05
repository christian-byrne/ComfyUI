# Performance Notes for ComfyUI

## Speed

### Startup

#### Not Lazy Loading

- All modules are loaded into memory when the program starts.
- The only actual module method being called is from the server's `object_info` endponit handler.
  - The node and module specs can be cached, and then lazily loaded by default to massively decrease startup time and also marginally improve memory usage.

## Memory

- Too Many File Descriptors: 
  - The epoll interface manages file descriptors, which represent network connections and other I/O resources.
  - opens many connections simultaneously without properly closing them
- Memory Leaks
  - the profiler points to epoll.poll(), but memory leak might be happening elsewhere. E.g., accumulating data in a global variable or not releasing resources properly after tasks are complete.
- Inefficient Event Loop Management:
  - event loop is overloaded with long-running tasks or not configured optimally, 
    - it might not be able to handle I/O events efficiently -> leading to increased memory pressure
- Memory is also hurt by [Not Lazy Loading](#not-lazy-loading) issue

### Obj Graph Analysis

In order of growth/end size:
- Functions
  - either creating new functions or accumulating large amounts of data within tuples.
  - Dynamic Function Creation
    - decorators
    - lambda
    - nested functions
  - Closures:
    - functions capturing large amounts of data in their enclosing scopes 
      - This can keep references to that data alive, preventing it from being garbage collected
- Tuples
  - Large Tuples: 
    - creating or accumulating very large tuples?
      - Tuples are immutable, so modifying them involves creating new tuples, which can lead to memory pressure.
  - Caching: 
    - using tuples for caching? Check cache limits
- OrderedDict
  - config, vocab, model config
  - Appropriate Usage
    - Is an OrderedDict truly necessary? If ordering aspect unneeded, consider using a regular dictionary to save some memory.
  - Unnecessary Accumulation
    - adding data to the OrderedDict without removing older entries? can lead to unbounded growth.
- Dicts and lists
  -  have also grown, but to a lesser extent.
- Sets emerged
  - Legitimate Use Case:
    - using sets for deduplication or membership testing? valid use cases.
    - converting lists or other sequences to sets when it's not needed? This creates extra objects and consumes memory.
- ReferenceType
  - might be expected 
