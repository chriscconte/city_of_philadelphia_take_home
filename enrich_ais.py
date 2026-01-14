"""
Script to enrich 311 service request addresses with OPA account numbers from the Philadelphia AIS API.
"""

import requests
import logging
import sqlite3
from typing import Generator
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def lookup_ais(address: str, session: requests.Session) -> tuple[str, str]:
    """
    Look up an address in the Philadelphia AIS API and return the OPA account number.

    Args:
        address: the address to look up
        session: shared requests session for connection reuse

    Returns:
        tuple of (address, opa_account_num) - empty string if not found
    """
    encoded_address = quote(address)
    url = f"https://api.phila.gov/ais/v2/search/{encoded_address}"

    response = session.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    if 'features' in data and len(data['features']) > 0:
        properties = data['features'][0].get('properties', {})
        opa_account_num = properties.get('opa_account_num', '')
        logger.debug(f"Found OPA account {opa_account_num} for {address}")
        return address, opa_account_num
    else:
        return address, ""


def lookup_ais_batch(addresses: list[str], session: requests.Session, max_workers: int = 10) -> dict[str, str]:
    """
    Look up a batch of addresses in parallel using a shared session.

    Args:
        addresses: the addresses to look up
        session: shared requests session for connection reuse
        max_workers: number of parallel threads

    Returns:
        a dictionary of addresses to OPA account numbers
    """
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_address = {
            executor.submit(lookup_ais, addr, session): addr
            for addr in addresses
        }
        
        for future in as_completed(future_to_address):
            address = future_to_address[future]
            try:
                addr, opa = future.result()
                results[addr] = opa
            except Exception as e:
                logger.warning(f"Error looking up {address}: {e}")
                results[address] = ""
    
    return results


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
    
    batch_size = 50
    batch = []
    total = 0
    
    with requests.Session() as session:
        for address in get_unique_addresses():
            batch.append(address)
            if len(batch) >= batch_size:
                results = lookup_ais_batch(batch, session, max_workers=10)
                for addr, opa in results.items():
                    save_ais_data(addr, opa)
                total += len(batch)
                logger.info(f"Processed {total} addresses")
                batch = []
        
        # Handle remaining addresses
        if batch:
            results = lookup_ais_batch(batch, session, max_workers=10)
            for addr, opa in results.items():
                save_ais_data(addr, opa)
            total += len(batch)
    
    logger.info(f"Enrichment complete. Processed {total} addresses.")


if __name__ == "__main__":
    main()
