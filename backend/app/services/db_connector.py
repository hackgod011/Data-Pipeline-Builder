"""Connect to external databases (SQLite file or PostgreSQL DSN), run a query,
and return a pandas DataFrame for schema detection.

SSRF prevention: hostnames that resolve to RFC-1918 or loopback addresses are
blocked when using network database types (PostgreSQL).
"""
import ipaddress
import re
import socket
import urllib.parse
from pathlib import Path

import pandas as pd

BLOCKED_CIDRS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]

ALLOWED_PORTS = {5432, 5433, 5439, 3306, 1433}  # PG, PG-alt, Redshift, MySQL, MSSQL


def _check_host(host: str) -> None:
    """Raise ValueError if the host resolves to an internal/loopback IP."""
    try:
        resolved = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise ValueError(f"Cannot resolve host: {host}")

    for info in resolved:
        raw_ip = info[4][0]
        try:
            ip = ipaddress.ip_address(raw_ip)
        except ValueError:
            continue
        for cidr in BLOCKED_CIDRS:
            if ip in cidr:
                raise ValueError(
                    f"Connections to internal address {raw_ip} ({host}) are not allowed"
                )


def _validate_postgres_dsn(dsn: str) -> None:
    parsed = urllib.parse.urlparse(dsn)
    host = parsed.hostname or ""
    port = parsed.port

    if not host:
        raise ValueError("No hostname in connection string")
    if port and port not in ALLOWED_PORTS:
        raise ValueError(f"Port {port} is not allowed. Allowed: {sorted(ALLOWED_PORTS)}")

    _check_host(host)


def query_sqlite(db_path: str, query: str) -> pd.DataFrame:
    """Run a SQL query against a SQLite file and return a DataFrame."""
    path = Path(db_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"SQLite file not found: {db_path}")
    # Sanitise: only allow alphanumeric + safe path chars
    if re.search(r"[;&|`$]", db_path):
        raise ValueError("Invalid characters in database path")

    import sqlite3
    con = sqlite3.connect(str(path))
    try:
        return pd.read_sql_query(query, con)
    finally:
        con.close()


def query_postgres(dsn: str, query: str) -> pd.DataFrame:
    """Run a SQL query against a PostgreSQL database and return a DataFrame."""
    _validate_postgres_dsn(dsn)
    try:
        import psycopg2
    except ImportError as e:
        raise RuntimeError("psycopg2-binary is required for PostgreSQL connections") from e

    con = psycopg2.connect(dsn)
    try:
        return pd.read_sql_query(query, con)
    finally:
        con.close()


def query_database(db_type: str, connection_string: str, query: str) -> pd.DataFrame:
    db_type = db_type.lower().strip()
    if db_type == "sqlite":
        return query_sqlite(connection_string, query)
    elif db_type in {"postgresql", "postgres"}:
        return query_postgres(connection_string, query)
    else:
        raise ValueError(f"Unsupported database type: {db_type!r}. Use 'sqlite' or 'postgresql'.")
