"""HierarchyMemory — shared scratchpad used across all three tiers.

Design
------
Workers write their outputs keyed by (domain, worker_name).
Mid-level agents read their domain's memory to synthesise.
Root agent reads the full snapshot for cross-domain reasoning.

This makes the information flow explicit and inspectable:
  Worker executes → writes to memory
  Mid-level reads memory → produces domain synthesis
  Root reads syntheses → produces final answer
"""


class HierarchyMemory:
    """Thread-safe shared memory store for the hierarchical pipeline.

    Structure
    ---------
    _store: {
        domain_name (str): {
            worker_name (str): output (str)
        }
    }
    """

    def __init__(self):
        self._store: dict[str, dict[str, str]] = {}

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def write(self, domain: str, worker_name: str, content: str) -> None:
        """Worker writes its output into the shared store."""
        self._store.setdefault(domain, {})[worker_name] = content

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def read_domain(self, domain: str) -> dict[str, str]:
        """Mid-level agent reads all worker outputs for its domain."""
        return dict(self._store.get(domain, {}))

    def read_all(self) -> dict[str, dict[str, str]]:
        """Root agent reads all domain outputs for cross-domain synthesis."""
        return {domain: dict(workers) for domain, workers in self._store.items()}

    # ------------------------------------------------------------------
    # Introspection (for UI display)
    # ------------------------------------------------------------------

    def entry_count(self) -> int:
        return sum(len(workers) for workers in self._store.values())

    def domain_names(self) -> list[str]:
        return list(self._store.keys())

    def __repr__(self) -> str:
        parts = [f"{d}: {list(ws.keys())}" for d, ws in self._store.items()]
        return f"HierarchyMemory({', '.join(parts)})"
