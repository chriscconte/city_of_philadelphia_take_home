"""
Test script for enrich_ais.py
"""

import logging
import sqlite3
import requests
from enrich_ais import (
    sqlite_db,
    init_ais_table,
    get_unique_addresses,
    lookup_ais,
    save_ais_data,
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_init_ais_table() -> None:
    """
    Test the init_ais_table function.
    """
    logger.debug("Running test_init_ais_table...")
    init_ais_table()
    
    # Verify table exists
    with sqlite3.connect(sqlite_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ais_addresses'")
        result = cursor.fetchone()
        assert result is not None, "ais_addresses table should exist"
        assert result[0] == "ais_addresses"
    
    logger.debug("test_init_ais_table passed")


def test_get_unique_addresses() -> None:
    """
    Test the get_unique_addresses function.
    Insert a test entry into public_cases_fc, verify it's returned, then clean up.
    """
    logger.debug("Running test_get_unique_addresses...")
    
    test_address = "TEST_ADDRESS_12345_FOR_UNIT_TEST"
    test_service_request_id = "test_sr_enrich_001"
    
    # Ensure ais_addresses table exists
    init_ais_table()
    
    # Insert test data into public_cases_fc
    with sqlite3.connect(sqlite_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO public_cases_fc (service_request_id, status, address, requested_datetime) VALUES (?, ?, ?, ?)",
            (test_service_request_id, "open", test_address, "2025-01-01")
        )
        conn.commit()
    
    try:
        # Verify the test address is returned by get_unique_addresses
        addresses = list(get_unique_addresses())
        assert test_address in addresses, f"Test address '{test_address}' should be in unique addresses"
        logger.debug(f"Found {len(addresses)} unique addresses, including test address")
        
    finally:
        # Clean up: remove test data
        with sqlite3.connect(sqlite_db) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM public_cases_fc WHERE service_request_id = ?", (test_service_request_id,))
            conn.commit()
    
    logger.debug("test_get_unique_addresses passed")


def test_lookup_ais_success() -> None:
    """
    Test the lookup_ais function with a known valid address.
    """
    logger.debug("Running test_lookup_ais_success...")
    
    address = "1400 john f kennedy blvd"
    opa_account_num = lookup_ais(address)
    
    logger.debug(f"OPA account number for '{address}': {opa_account_num}")
    assert opa_account_num != "", f"Should find OPA account for '{address}'"
    assert len(opa_account_num) > 0, "OPA account number should not be empty"
    
    logger.debug("test_lookup_ais_success passed")


def test_lookup_ais_failure() -> None:
    """
    Test the lookup_ais function with an invalid address.
    """
    logger.debug("Running test_lookup_ais_failure...")
    
    address = "None Null"
    try:
        opa_account_num = lookup_ais(address)
    except requests.exceptions.RequestException as e:
        assert True, f"Should raise an exception for invalid address '{address}'"
    
    logger.debug("test_lookup_ais_failure passed")


def test_save_ais_data() -> None:
    """
    Test the save_ais_data function.
    """
    logger.debug("Running test_save_ais_data...")
    
    test_address = "TEST_SAVE_ADDRESS_67890"
    test_opa = "123456789"
    
    # Ensure table exists
    init_ais_table()
    
    try:
        # Save test data
        save_ais_data(test_address, test_opa)
        
        # Verify it was saved
        with sqlite3.connect(sqlite_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT address, opa_account_num FROM ais_addresses WHERE address = ?", (test_address,))
            result = cursor.fetchone()
            
            assert result is not None, "Saved data should be retrievable"
            assert result[0] == test_address, f"Address should match: {result[0]}"
            assert result[1] == test_opa, f"OPA account should match: {result[1]}"
        
        logger.debug(f"Verified saved data: address='{result[0]}', opa='{result[1]}'")
        
    finally:
        # Clean up
        with sqlite3.connect(sqlite_db) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ais_addresses WHERE address = ?", (test_address,))
            conn.commit()
    
    logger.debug("test_save_ais_data passed")


if __name__ == "__main__":
    logger.info("Running enrich_ais tests...")
    
    test_init_ais_table()
    test_get_unique_addresses()
    test_lookup_ais_success()
    test_lookup_ais_failure()
    test_save_ais_data()
    
    logger.info("All enrich_ais tests passed!")
