"""Baseline world family implementations."""

from __future__ import annotations

import random

from pufopt.types import Params, WorldSpec
from pufopt.worlds.registry import WorldInstanceRecord, register_world_family


@register_world_family("lab_clean")
def sample_lab_clean(spec: WorldSpec, seed: int) -> WorldInstanceRecord:
    rng = random.Random(seed)
    params = dict(spec.params)
    params.setdefault("sensor_noise_sigma", 0.005)
    params.setdefault("temperature_shift_c", 0)
    params.setdefault("illumination_jitter", 0.01)
    params["sample_seed"] = seed
    params["observed_sensor_noise_sigma"] = round(
        float(params["sensor_noise_sigma"]) * (0.95 + 0.05 * rng.random()), 6
    )
    return WorldInstanceRecord(id=spec.id, params=_normalize(params))


@register_world_family("phone_reader_indoor")
def sample_phone_reader_indoor(spec: WorldSpec, seed: int) -> WorldInstanceRecord:
    rng = random.Random(seed)
    params = dict(spec.params)
    params.setdefault("sensor_noise_sigma", 0.03)
    params.setdefault("temperature_shift_c", 6)
    params.setdefault("illumination_jitter", 0.12)
    params.setdefault("angle_variation_deg", 9)
    params.setdefault("attacker_query_budget", 5000)
    params.setdefault("verifier_model", "honest")
    params["sample_seed"] = seed
    params["observed_sensor_noise_sigma"] = round(
        float(params["sensor_noise_sigma"]) * (0.9 + 0.2 * rng.random()), 6
    )
    params["observed_illumination_jitter"] = round(
        float(params["illumination_jitter"]) * (0.9 + 0.25 * rng.random()), 6
    )
    params["observed_angle_variation_deg"] = round(
        float(params["angle_variation_deg"]) * (0.9 + 0.25 * rng.random()), 6
    )
    return WorldInstanceRecord(id=spec.id, params=_normalize(params))


def _normalize(params: dict[str, object]) -> Params:
    return {str(key): value for key, value in params.items()}

