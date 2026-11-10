"""Fail closed before tests create, migrate, or clear any tables."""
from sqlalchemy.engine import make_url


def validate_test_database_url(test_url: str | None, application_url: str | None = None):
    if not test_url:
        raise RuntimeError("TEST_DATABASE_URL is required; DATABASE_URL is never a fallback")
    url = make_url(test_url)
    if url.get_backend_name() != "postgresql" or not (url.database or "").endswith("_test"):
        raise RuntimeError("Tests require a PostgreSQL database whose name ends with _test")
    if application_url:
        application = make_url(application_url)
        def endpoint(value):
            host = (value.host or "localhost").lower()
            if host in {"127.0.0.1", "::1"}:
                host = "localhost"
            return host, value.port or 5432, value.database
        if endpoint(url) == endpoint(application):
            raise RuntimeError("Test and application database must be different")
    return url.set(drivername="postgresql+psycopg")
