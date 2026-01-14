"""
Script to enrich 311 service requests with code violation counts using local database.
"""

import logging
import sqlite3

sqlite_db = "data/311_service_requests.db"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_violations_table() -> None:
    """
    Initialize the violation counts table. Create the table if it doesn't exist.
    """
    with sqlite3.connect(sqlite_db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS violation_counts (
                service_request_id TEXT PRIMARY KEY,
                opa_account_num TEXT,
                violation_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    logger.info("Violation counts table initialized")


def compute_violation_counts() -> None:
    """
    Compute violation counts for all service requests that have OPA account numbers.
    Uses a single SQL query to join and count efficiently.
    """
    with sqlite3.connect(sqlite_db) as conn:
        cursor = conn.cursor()
        
        # Insert violation counts for all service requests in one query
        cursor.execute("""
            INSERT OR REPLACE INTO violation_counts 
                (service_request_id, opa_account_num, violation_count, created_at, updated_at)
            SELECT 
                p.service_request_id,
                a.opa_account_num,
                COUNT(v.cartodb_id) as violation_count,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            FROM public_cases_fc p
            INNER JOIN ais_addresses a ON p.address = a.address
            LEFT JOIN violations v ON a.opa_account_num = v.opa_account_num
                AND v.casecreateddate > p.requested_datetime
            WHERE a.opa_account_num IS NOT NULL
              AND a.opa_account_num != ''
            GROUP BY p.service_request_id, a.opa_account_num
        """)
        
        row_count = cursor.rowcount
        conn.commit()
        
    logger.info(f"Computed violation counts for {row_count} service requests")


def main() -> None:
    """
    Main function to enrich service requests with violation counts.
    """
    init_violations_table()
    compute_violation_counts()
    logger.info("Enrichment complete.")


if __name__ == "__main__":
    main()
