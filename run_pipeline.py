"""
Main pipeline script to download, enrich, and generate reports for Philadelphia 311 service requests.
"""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """
    Run the full data pipeline:
    1. Create data folder
    2. Download 311 service requests
    3. Download violations
    4. Enrich with AIS data (OPA account numbers)
    5. Enrich with violation counts
    6. Generate report
    """
    
    # Step 1: Create data folder
    logger.info("Step 1: Creating data folder...")
    os.makedirs("data", exist_ok=True)
    logger.info("Data folder ready")
    
    # Step 2: Download 311 service requests
    logger.info("Step 2: Downloading 311 service requests...")
    import download_311
    download_311.main()
    
    # Step 3: Download violations
    logger.info("Step 3: Downloading violations...")
    import download_violations
    download_violations.main()
    
    # Step 4: Enrich with AIS data
    logger.info("Step 4: Enriching addresses with AIS data...")
    import enrich_ais
    enrich_ais.main()
    
    # Step 5: Enrich with violation counts
    logger.info("Step 5: Enriching with violation counts...")
    import enrich_violations
    enrich_violations.main()
    
    # Step 6: Generate report
    logger.info("Step 6: Generating report...")
    import generate_report
    generate_report.main()
    
    logger.info("Pipeline complete!")


if __name__ == "__main__":
    main()
