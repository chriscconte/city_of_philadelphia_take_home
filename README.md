# 311 L&I Performance Analysis

A pipeline for analyzing Philadelphia 311 service requests assigned to Licenses & Inspections (L&I) and matching them against property code violations.

## Overview

This project downloads 311 service request data, enriches it with property information from the AIS API, and cross-references it with code violations to generate performance metrics.

---

## Task List

### 1. Download 311 Tickets
- [ ] Create a script to download 311 tickets for 2025 assigned to L&I
- [ ] Add downloaded records to a local data store
- [ ] **Decision needed:** Storage format (Python pickle, SQLite, or PostgreSQL)
  - Pickle: Simple, fast for Python, but not queryable
  - SQLite: Portable, queryable, good for ~50k records
  - PostgreSQL: Scalable, but requires server setup

### 2. Enrich with AIS Property Data
- [ ] Iterate through the 311 collection (~50k records)
- [ ] Query the AIS API using the `address` field
- [ ] Extract and store `opa_account_num` for each service request
- [ ] **Open questions:**
  - How to handle NULL/empty address fields?
  - How to handle duplicate `opa_account_num` (multiple service requests at the same address)?

### 3. Match with Code Violations
- [ ] Iterate through the collection again
- [ ] Use `opa_account_num` to query the property code violations dataset
- [ ] Store matches in the local data store
- [ ] **Open questions:**
    - how to handle multiple violations at the opa_account_num?


### 4. Generate Report
- [ ] Write a script to answer the following questions:
  - How many service requests were captured?
  - What percentage have a matching code violation?
  - What percentage of service requests have status "open"?
- [ ] Output results to a text file saved in the local data store

### 5. Dockerize the Pipeline
- [ ] Wrap all scripts and dependencies in a Dockerfile
- [ ] Enable execution via: `docker container run 311_LI_performance`

---

## Data Sources

| Dataset | Source |
|---------|--------|
| 311 Service Requests | [OpenDataPhilly](https://www.opendataphilly.org/datasets/311-service-and-information-requests/) |
| AIS API | [Philadelphia AIS](https://github.com/CityOfPhiladelphia/ais) |
| Property Code Violations | [OpenDataPhilly](https://www.opendataphilly.org/datasets/code-violations/) |

---

## Project Structure (Planned)

```
cop_take_home/
├── README.md
├── Dockerfile
├── requirements.txt
├── scripts/
│   ├── download_311.py
│   ├── enrich_ais.py
│   ├── match_violations.py
│   └── generate_report.py
├── data/
│   └── (local data store)
└── output/
    └── report.txt
```

---

## Usage

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run individual scripts
python scripts/download_311.py
python scripts/enrich_ais.py
python scripts/match_violations.py
python scripts/generate_report.py
```

### Docker
```bash
# Build the image
docker build -t 311_li_performance .

# Run the pipeline
docker container run 311_li_performance
```

---

## Open Questions

1. **Storage format:** What's the best storage solution for ~50k records with enrichment?
2. **NULL addresses:** Skip, log, or attempt geocoding via alternate fields?
3. **Duplicate OPA numbers:** Aggregate stats, or track individual request-to-violation mappings?
4. **Rate limiting:** Does the AIS API have rate limits we need to respect?=