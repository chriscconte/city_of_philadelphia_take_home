"""
Script to enrich 311 service request addresses with OPA account numbers from the Philadelphia AIS API.
"""

import requests
import logging
import sqlite3
from urllib.parse import quote

sqlite_db = "data/311_service_requests.db"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_ais_table() -> None:
    """
    Initialize the AIS enrichment table. Create the table if it doesn't exist.
    """
    with sqlite3.connect(sqlite_db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ais_addresses (
                address TEXT PRIMARY KEY,
                opa_account_num TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    logger.info("AIS addresses table initialized")


def get_unique_addresses(batch_size: int = 1000) -> Generator[str, None, None]:
    """
    Yield unique addresses from the public_cases_fc table that haven't been enriched yet.

    Args:
        batch_size: number of addresses to fetch per batch from the database.

    Yields:
        unique address strings
    """
    with sqlite3.connect(sqlite_db) as conn:
        cursor = conn.cursor()
        offset = 0
        while True:
            cursor.execute("""
                SELECT DISTINCT p.address 
                FROM public_cases_fc p
                LEFT JOIN ais_addresses a ON p.address = a.address
                WHERE a.address IS NULL AND p.address IS NOT NULL
                LIMIT ? OFFSET ?
            """, (batch_size, offset))
            results = cursor.fetchall()
            if not results:
                break
            for row in results:
                yield row[0]
            offset += batch_size

def lookup_ais(address: str) -> str:
    """
    Look up an address in the Philadelphia AIS API and return the OPA account number.

    Args:
        address: the address to look up

    Returns:
        the OPA account number, or empty string if not found
    """
    encoded_address = quote(address)
    url = f"https://api.phila.gov/ais/v2/search/{encoded_address}"
    

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    if 'features' in data and len(data['features']) > 0:
        properties = data['features'][0].get('properties', {})
        opa_account_num = properties.get('opa_account_num', '')
        logger.debug(f"Found OPA account {opa_account_num} for {address}")
        return opa_account_num
    else:
        return ""


def save_ais_data(address: str, opa_account_num: str) -> None:
    """
    Save the AIS data to the database. If the address already exists, replace the OPA account number.

    Args:
        address: the address
        opa_account_num: the OPA account number
    """
    with sqlite3.connect(sqlite_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO ais_addresses (address, opa_account_num, created_at, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (address, opa_account_num)
        )
        conn.commit()


def main() -> None:
    """
    Main function to enrich addresses with OPA account numbers.
    """
    init_ais_table()
    addresses = get_unique_addresses()
    
    for i, address in enumerate(addresses):
        if i % 100 == 0:
            logger.info(f"Processing address {i + 1} of {len(addresses)}")
        try:
            opa_account_num = lookup_ais(address)
            save_ais_data(address, opa_account_num)
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error looking up {address}: {e}")
    
    logger.info(f"Enrichment complete. Processed {len(addresses)} addresses.")


if __name__ == "__main__":
    main()
