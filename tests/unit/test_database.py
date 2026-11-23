"""strata-python's standard database tests: the migrations run up and down on a scratch database, and the migrated
schema is exactly what the models say (a model change without its revision fails here, and in `strata-db check`)."""

from strata_python.db.testing import test_migrations, test_schema_matches_models  # noqa: F401
