"""
Script to generate a summary report of 311 service requests and code violations.
"""

import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

sqlite_db = "data/311_service_requests.db"
report_file = "report.txt"


def generate_report() -> str:
    """
    Generate a summary report of 311 service requests and code violations.

    Returns:
        The report as a string.
    """
    with sqlite3.connect(sqlite_db) as conn:
        cursor = conn.cursor()

        # Total service requests
        cursor.execute("SELECT COUNT(*) FROM public_cases_fc")
        total_requests = cursor.fetchone()[0]

        # Service requests with matching code violations (violation_count > 0)
        cursor.execute("""
            SELECT COUNT(*) FROM violation_counts 
            WHERE violation_count > 0
        """)
        requests_with_violations = cursor.fetchone()[0]

        # Service requests with status 'Open'
        cursor.execute("SELECT COUNT(*) FROM public_cases_fc WHERE status = 'Open' or status = 'open'")
        open_requests = cursor.fetchone()[0]

        # Calculate percentages
        pct_with_violations = (requests_with_violations / total_requests * 100) if total_requests > 0 else 0
        pct_open = (open_requests / total_requests * 100) if total_requests > 0 else 0

    # Build report
    report = f"""311 Service Requests Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 50}

Total Service Requests: {total_requests:,}

Service Requests with Code Violations: {requests_with_violations:,} ({pct_with_violations:.1f}%)

Service Requests with Status 'Open': {open_requests:,} ({pct_open:.1f}%)
"""
    return report


def main() -> None:
    """
    Generate and save the report.
    """
    report = generate_report()
    
    # Save to file
    with open(report_file, 'w') as f:
        f.write(report)
    
    logger.info(f"Report saved to {report_file}")


if __name__ == "__main__":
    main()
