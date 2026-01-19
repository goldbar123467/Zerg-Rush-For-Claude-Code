"""Metric collector for training logging and aggregation."""

from collections import defaultdict
from typing import Optional


class MetricCollector:
    """Collects and aggregates training metrics.

    Simple metric collection with running statistics.
    Not thread-safe (designed for single-process use).
    """

    def __init__(self):
        """Initialize the metric collector."""
        self.metrics: dict[str, list[tuple[int, float]]] = defaultdict(list)

    def log(self, name: str, value: float, step: int) -> None:
        """Log a metric value at a given step.

        Args:
            name: Name of the metric (e.g., 'loss', 'accuracy')
            value: The metric value to log
            step: Training step number
        """
        self.metrics[name].append((step, value))

    def get_summary(self) -> dict[str, float]:
        """Return mean of each metric.

        Returns:
            Dictionary mapping metric names to their mean values.
        """
        summary = {}
        for name, values in self.metrics.items():
            if values:
                mean_val = sum(v for _, v in values) / len(values)
                summary[name] = mean_val
        return summary

    def get_latest(self, name: str) -> Optional[tuple[int, float]]:
        """Get the most recent value for a metric.

        Args:
            name: Name of the metric

        Returns:
            Tuple of (step, value) or None if no values logged.
        """
        if name in self.metrics and self.metrics[name]:
            return self.metrics[name][-1]
        return None

    def get_values(self, name: str) -> list[tuple[int, float]]:
        """Get all values for a metric.

        Args:
            name: Name of the metric

        Returns:
            List of (step, value) tuples.
        """
        return list(self.metrics.get(name, []))

    def clear(self, name: Optional[str] = None) -> None:
        """Clear metrics.

        Args:
            name: If provided, clear only this metric. Otherwise clear all.
        """
        if name is not None:
            if name in self.metrics:
                self.metrics[name].clear()
        else:
            self.metrics.clear()

    def print_summary(self) -> None:
        """Print a formatted summary of all metrics."""
        summary = self.get_summary()
        if not summary:
            print("No metrics logged.")
            return

        print("=" * 40)
        print("Metric Summary")
        print("=" * 40)
        for name, mean_val in sorted(summary.items()):
            count = len(self.metrics[name])
            print(f"  {name}: {mean_val:.4f} (n={count})")
        print("=" * 40)

    def __len__(self) -> int:
        """Return total number of logged values across all metrics."""
        return sum(len(v) for v in self.metrics.values())

    def __repr__(self) -> str:
        """Return string representation."""
        metric_names = list(self.metrics.keys())
        return f"MetricCollector(metrics={metric_names}, total_values={len(self)})"
