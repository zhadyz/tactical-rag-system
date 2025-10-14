"""
Performance timing utilities for detailed metrics
"""
import time
from typing import Dict, Optional
from contextlib import contextmanager


class StageTimer:
    """Track timing for different processing stages"""

    def __init__(self):
        self.stages: Dict[str, float] = {}
        self.start_time: Optional[float] = None
        self.current_stage: Optional[str] = None
        self.current_stage_start: Optional[float] = None

    def start(self):
        """Start overall timing"""
        self.start_time = time.time()
        self.stages = {}

    def start_stage(self, stage_name: str):
        """Start timing a specific stage"""
        if self.current_stage:
            # End previous stage
            self.end_stage()

        self.current_stage = stage_name
        self.current_stage_start = time.time()

    def end_stage(self):
        """End current stage timing"""
        if self.current_stage and self.current_stage_start:
            elapsed = (time.time() - self.current_stage_start) * 1000  # ms
            self.stages[self.current_stage] = elapsed
            self.current_stage = None
            self.current_stage_start = None

    def get_total_time(self) -> float:
        """Get total elapsed time in milliseconds"""
        if not self.start_time:
            return 0.0
        return (time.time() - self.start_time) * 1000

    def get_breakdown(self) -> Dict:
        """Get timing breakdown with percentages"""
        # Finish current stage if any
        if self.current_stage:
            self.end_stage()

        total_time = self.get_total_time()

        if total_time == 0:
            return {
                "total_ms": 0,
                "stages": {},
                "unaccounted_ms": 0
            }

        # Calculate unaccounted time
        accounted_time = sum(self.stages.values())
        unaccounted_time = total_time - accounted_time

        # Build breakdown with percentages
        breakdown = {
            "total_ms": round(total_time, 2),
            "stages": {
                name: {
                    "time_ms": round(time_ms, 2),
                    "percentage": round((time_ms / total_time) * 100, 1)
                }
                for name, time_ms in self.stages.items()
            },
            "unaccounted_ms": round(unaccounted_time, 2),
            "unaccounted_percentage": round((unaccounted_time / total_time) * 100, 1)
        }

        return breakdown

    @contextmanager
    def measure(self, stage_name: str):
        """Context manager for timing a code block"""
        self.start_stage(stage_name)
        try:
            yield
        finally:
            self.end_stage()


# Convenience function for simple timing
@contextmanager
def time_it(name: str = "operation"):
    """
    Simple timing context manager

    Usage:
        with time_it("my_operation") as timer:
            # do work
            pass
        print(f"Took {timer['elapsed_ms']:.2f}ms")
    """
    start = time.time()
    result = {"elapsed_ms": 0}

    try:
        yield result
    finally:
        result["elapsed_ms"] = (time.time() - start) * 1000
