from dataclasses import dataclass
from time import time


@dataclass
class TokenBucket:
    capacity: int
    refill_rate_per_second: float
    tokens: float
    last_refill_at: float

    @classmethod
    def full(cls, *, capacity: int, refill_rate_per_second: float) -> "TokenBucket":
        return cls(
            capacity=capacity,
            refill_rate_per_second=refill_rate_per_second,
            tokens=float(capacity),
            last_refill_at=time(),
        )

    def allow(self, *, cost: int = 1, now: float | None = None) -> bool:
        current_time = now if now is not None else time()
        elapsed = max(current_time - self.last_refill_at, 0)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate_per_second)
        self.last_refill_at = current_time
        if self.tokens < cost:
            return False
        self.tokens -= cost
        return True
