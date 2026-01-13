import sys
import logging
import sqlite3
from download_311 import get_311_service_requests, init_database, save_data
sqlite_db = "data/311_service_requests.db"
logger = logging.getLogger(__name__)

def test_get_311_service_requests() -> None:
    """
    Test the get_311_service_requests function.
    """
    logger.debug("Running test_get_311_service_requests...")
    data = get_311_service_requests(2, 0)
    logger.debug(data)
    assert len(data) == 2
    assert data[0]['service_request_id'] is not None
    assert data[0]['status'] is not None
    assert data[0]['address'] is not None
    assert data[0]['requested_datetime'] is not None
    logger.debug("test_download_311 passed")

def test_init_database() -> None:
    """
    Test the init_database function.
    """
    logger.debug("Running test_init_database...")
    init_database()
    with sqlite3.connect(sqlite_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM public_cases_fc")
        data = cursor.fetchall()
        logger.debug(data)
    logger.debug("test_init_database passed")

def test_save_data() -> None:
    """
    Test the save_data function.
    """
    logger.debug("Running test_save_data...")
    data = [
        {
            'service_request_id': 'test_1',
            'status': 'open',
            'address': '123 Main St, Philadelphia, PA 19101',
            'requested_datetime': '2025-01-01'
        },
        {
            'service_request_id': 'test_2',
            'status': 'closed',
            'address': '123 Main St, Philadelphia, PA 19101',
            'requested_datetime': '2025-01-02'
        }
    ]
    save_data(data)
    with sqlite3.connect(sqlite_db) as conn:
        cursor = conn.cursor()
        assert len(data) == 2
        cursor.execute("SELECT * FROM public_cases_fc WHERE service_request_id = 'test_1'")
        data = cursor.fetchone()
        logger.debug(data)
        assert data[0] == 'test_1'
        assert data[1] == 'open'
        assert data[2] == '123 Main St, Philadelphia, PA 19101'
        assert data[3] == '2025-01-01'
        
        cursor.execute("SELECT * FROM public_cases_fc WHERE service_request_id = 'test_2'")
        data = cursor.fetchone()
        logger.debug(data)
        assert data[0] == 'test_2'
        assert data[1] == 'closed'
        assert data[2] == '123 Main St, Philadelphia, PA 19101'
        assert data[3] == '2025-01-02'

        # delete the data
        cursor.executemany("DELETE FROM public_cases_fc WHERE service_request_id = ?", [('test_1',), ('test_2',)])
        conn.commit()
    logger.debug("test_save_data passed")


if __name__ == "__main__":
    logger.info("Running tests...")
    logger.setLevel(logging.DEBUG)
    test_init_database()
    test_save_data()
    logger.info("Tests completed successfully")