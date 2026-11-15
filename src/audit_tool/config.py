"""Versioned and JSON-serializable transformation policy definitions."""
from dataclasses import asdict, dataclass, field
import json

STRATEGIES = frozenset({"placeholder", "mask", "keep", "surrogate", "date_shift", "generalize"})


@dataclass(frozen=True)
class TransformConfig:
    name: str
    seed: str = "issue18-research-seed"
    age_band_width: int = 5
    # The same document gets one reproducible offset in [365,1095] or [-1095,-365].
    date_shift_min_days: int = 365
    date_shift_max_days: int = 1095
    per_category: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if self.age_band_width <= 0 or self.age_band_width > 50:
            raise ValueError("Invalid age band width")
        if self.date_shift_min_days < 1 or self.date_shift_max_days < self.date_shift_min_days:
            raise ValueError("Invalid document date offset range")
        if not self.seed:
            raise ValueError("Seed must not be empty")
        if any(value not in STRATEGIES for value in self.per_category.values()):
            raise ValueError("Unsupported strategy")

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, value: dict) -> "TransformConfig":
        return cls(**value)

    @classmethod
    def from_json(cls, value: str) -> "TransformConfig":
        return cls.from_dict(json.loads(value))


CATEGORY_STRATEGIES = {
    "person": "surrogate", "contact": "surrogate", "id": "surrogate",
    "date": "date_shift", "age": "generalize", "place": "generalize",
    "employer": "generalize", "profession": "generalize", "title": "placeholder",
    "unknown": "placeholder",
}


def standard_pipelines(seed: str = "issue18-research-seed") -> list[TransformConfig]:
    return [
        TransformConfig(name="P0_mask", seed=seed,
                        per_category={k: "mask" for k in CATEGORY_STRATEGIES}),
        TransformConfig(name="P1_placeholder", seed=seed,
                        per_category={k: "placeholder" for k in CATEGORY_STRATEGIES}),
        TransformConfig(name="P2_surrogate", seed=seed,
                        per_category=dict(CATEGORY_STRATEGIES)),
        TransformConfig(name="P3_keep_quasi", seed=seed,
                        per_category={**CATEGORY_STRATEGIES, "age": "keep", "place": "keep",
                                      "profession": "keep", "employer": "keep"}),
    ]
