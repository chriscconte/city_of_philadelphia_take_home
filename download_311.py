"""
Script to download 311 service requests from the City of Philadelphia's Carto database, in batches of 1000 records.

"""

import requests
import logging
import sqlite3

sqlite_db = "data/311_service_requests.db"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_311_service_requests(limit: int, offset: int) -> list[dict]:
    """
    Download 311 service requests from the City of Philadelphia's Carto database, in batches of `limit` records, starting from `offset`.

    Args:
        limit: int, the number of records to download in each batch
        offset: int, the offset of the records to download from the start of the dataset

    Returns:
        list of dicts, the 311 service requests in the batch
    """
    
    query = f"""SELECT 
    service_request_id, status, address, requested_datetime
    FROM public_cases_fc
    WHERE
     requested_datetime >= '2025-01-01'
     AND requested_datetime < '2026-01-01'
     AND agency_responsible = 'License ' || chr(38) || ' Inspections'
    LIMIT {limit}
    OFFSET {offset}
    """

    logger.info(f"Downloading 311 service requests from {offset} to {offset + limit}")
    logger.debug(f"Query: {query}")
    url = f"https://phl.carto.com/api/v2/sql?q={query}"
    response = requests.get(url)
    return response.json()['rows']


def init_database() -> None:
    """
    Initialize the SQLite database. Create the table if it doesn't exist.

    Args:
        None
    
    Returns:
        None
    """
    with sqlite3.connect(sqlite_db) as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS public_cases_fc (service_request_id TEXT PRIMARY KEY, status TEXT, address TEXT, requested_datetime TEXT)")
        conn.commit()

def save_data(data: list[dict]) -> None:
    """
    Save the data to the SQLite database.

    Args:
        data: list[dict], the data to save
    
    Returns:
        None
    """
    # convert the data to a list of tuples
    data_tuples = [(row['service_request_id'], row['status'], row['address'], row['requested_datetime']) for row in data]

    with sqlite3.connect(sqlite_db) as conn:
        cursor = conn.cursor()
        cursor.executemany("INSERT INTO public_cases_fc (service_request_id, status, address, requested_datetime) VALUES (?, ?, ?, ?)", data_tuples)
        conn.commit()


def main() -> None:
    """
    Main function to download the 311 service requests.
    """
    init_database()
    offset = 0
    limit = 10000
    while True:
        data = get_311_service_requests(limit, offset)
        if len(data) == 0:
            logger.info("No more data to download")
            break
        save_data(data)
        offset += limit

    logger.info("311 service requests downloaded successfully")


if __name__ == "__main__":
    main()