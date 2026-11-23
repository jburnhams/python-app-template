"""Unit-suite only: the hypothesis profile (the shared fixtures are in tests/conftest.py and the strata-python plugin)."""

from hypothesis import HealthCheck, settings

settings.register_profile(
    "unit", deadline=None, max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
settings.load_profile("unit")
