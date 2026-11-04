# performance benchmarks

`tooling/benchmarks/runtime.py` measures representative framework operations:
constructing a 10,000-row `DataTable`, serializing and diffing a 1,000-child
component tree, serializing the wire tree to JSON, filtering/sorting 10,000
in-memory rows, and delivering concurrent events to 50 independent sessions.

Run the informational benchmark from the repository root:

```bash
uv run python tooling/benchmarks/runtime.py --iterations 20 --warmups 3
```

The JSON output includes the Python version, platform, workload sizes, median
latency, and operations per second. For comparisons, use the same Python build,
machine, power mode, and command. These microbenchmarks do not model network
latency, database query plans, browser rendering, or production concurrency;
they are not service-level objectives and CI does not enforce hardware-specific
latency thresholds. CI runs a short smoke invocation to keep the benchmark
executable as code evolves.
