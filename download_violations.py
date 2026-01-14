"""
Script to download code violations from the City of Philadelphia's Carto database, in batches.
"""

import requests
import logging
import sqlite3

sqlite_db = "data/311_service_requests.db"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_violations(limit: int, offset: int) -> list[dict]:
    """
    Download violations from the City of Philadelphia's Carto database, in batches.

    Args:
        limit: the number of records to download in each batch
        offset: the offset of the records to download from the start of the dataset

    Returns:
        list of dicts, the violations in the batch
    """
    query = f"""SELECT 
        cartodb_id, opa_account_num, casecreateddate
        FROM violations
        WHERE casecreateddate >= '2025-01-01'
        AND casecreateddate < '2026-01-01'
        ORDER BY cartodb_id
        LIMIT {limit}
        OFFSET {offset}
    """

    logger.info(f"Downloading violations from {offset} to {offset + limit}")
    logger.debug(f"Query: {query}")
    url = f"https://phl.carto.com/api/v2/sql?q={query}"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.json()['rows']


def init_database() -> None:
    """
    Initialize the violations table in the SQLite database.
    """
    with sqlite3.connect(sqlite_db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                cartodb_id INTEGER PRIMARY KEY,
                opa_account_num TEXT,
                casecreateddate TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_violations_opa ON violations(opa_account_num)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_violations_date ON violations(casecreateddate)")
        conn.commit()
    logger.info("Violations table initialized")


def save_data(data: list[dict]) -> None:
    """
    Save the violations data to the SQLite database.

    Args:
        data: list of violation records
    """
    data_tuples = [
        (row['cartodb_id'], row['opa_account_num'], row['casecreateddate'])
        for row in data
    ]

    with sqlite3.connect(sqlite_db) as conn:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT OR IGNORE INTO violations (cartodb_id, opa_account_num, casecreateddate) VALUES (?, ?, ?)",
            data_tuples
        )
        conn.commit()


def main() -> None:
    """
    Main function to download the violations.
    """
    init_database()
    offset = 0
    limit = 10000
    total = 0

    while True:
        data = get_violations(limit, offset)
        if len(data) == 0:
            logger.info("No more data to download")
            break
        save_data(data)
        total += len(data)
        logger.info(f"Downloaded {total} violations so far")
        offset += limit

    logger.info(f"Violations download complete. Total: {total} records.")


if __name__ == "__main__":
    main()
