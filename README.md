# 311 L&I Performance Analysis

A pipeline for analyzing Philadelphia 311 service requests assigned to Licenses & Inspections (L&I) and matching them against property code violations.

## Overview

This project downloads 311 service request data, enriches it with property information from the AIS API, and cross-references it with code violations to generate performance metrics.

---

## Task List

### 1. Download 311 Tickets
- [x] Create a script to download 311 tickets for 2025 assigned to L&I
- [x] Add downloaded records to a local data store. 
- [x] **Decision needed:** Storage format (Python pickle, SQLite, or PostgreSQL)
  - SQLite: Portable, queryable, good for ~50k records

### 2. Enrich with AIS Property Data
- [ ] Iterate through _all addresses_ in the 311 collection (~50k records, ?how many unique `address` values?) ~45k unique addresses
- [ ] Query the AIS API using the `address` field
- [ ] Extract and store `opa_account_num` in the local data store, keyed by address. This will be used to match the 311 tickets to the code violations, for O(1) lookup time.
- [x] **Open questions:**
  - How to handle NULL/empty address fields?
    - Skip these records for now
  - How to handle duplicate `opa_account_num` (multiple violations at the same address)?
    - opa_account num is not a unique identifier, this is not a problem. Note that we can populate multiple tickets with the same opa_account_num, as a performance optimization.

This step was taking a long time, so I have parallelized the process.

### 3. Match with Code Violations
- [ ] Iterate through the collection again
- [ ] Use `opa_account_num` to query the property code violations dataset
- [ ] Store matches in the local data store
- [x] **Open questions:**
    - how to handle multiple violations at the opa_account_num?
        - See below for different approaches. We will use Approach 2: each violation can 'validate' multiple tickets. Note that we can 'validate' multiple tickets with a single violation, as a performance optimization.


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
    - SQLite is a good option for a local data store for ~50k records
2. **NULL addresses:** Skip, log, or attempt geocoding via alternate fields?
    - Skip these records for now
3. **Duplicate OPA numbers:** Aggregate stats, or track individual request-to-violation mappings?
    - See below for different approaches. We will use Approach 2: each violation can 'validate' multiple tickets.
4. **Rate limiting:** Does the AIS API have rate limits we need to respect?
    - No, the AIS API does not have rate limits.



# Different Approaches for Matching 311 Tickets to Code Violations

## Approach 1: One-to-One Mapping (assuming a single 311 ticket per violation at the same address. If there are multiple tickets at the same address, the ticket is mapped to the first violation _that has not been mapped to another ticket_.)
- Each 311 ticket is mapped to one code violation
- If there are multiple violations at the same address, the ticket is mapped to the first violation.
- if there are multiple tickets at the same address, the ticket is mapped to the first violation _that has not been mapped to another ticket_.

Example of two tickets, two violations.
ticket A: violation 1
ticket B: violation 2

Example of two tickets, one violation.
ticket A: violation 1
ticket B: [No Match]

Example of one ticket, two violations.
ticket A: violation 1


## Approach 2: One-to-Many Mapping (assuming a single 311 ticket is mapped to multiple code violations at the same address. if there are multiple tickets at the same address, the ticket is mapped to all violations)
- Each 311 ticket is mapped to multiple code violations.
- if there are multiple tickets at the same address, the ticket is mapped to all violations.
- If there are multiple violations at the same address, the ticket is mapped to all violations.


in the case of this analysis, we can just store a count of the number of violations for each ticket.

Example of two tickets, two violations.
ticket A: violation count = 2
ticket B: violation count = 2

Example of two tickets, one violation.
ticket A: violation count = 1
ticket B: violation count = 1

Even simpler, we can just store a boolean value for whether the ticket has been mapped to a violation.

ticket A: mapped to violation = True
ticket B: mapped to violation = True

This seems like a reasonable approach for this analysis, seeing as we are interested in how many tickets mapped to a violation, and not specifically which violations each ticket is mapped to. If multiple tickets are submitted for the same violation, that still counts as a 'success'.



# Experimentation with the api calls


``` q=SELECT cartodb_id FROM public_cases_fc WHERE requested_datetime BETWEEN '01-Jan-2025’ AND '31-Dec-2025’ and address is not null group by address
```

``` q=SELECT cartodb_id FROM public_cases_fc WHERE requested_datetime BETWEEN '01-Jan-2025’ AND '31-Dec-2025’
```

``` https://phl.carto.com/api/v2/sql?q=SELECT%20*%20FROM%20public_cases_fc%20WHERE%20requested_datetime%20BETWEEN%20%2701-Jan-2025%27%20AND%20%2731-Dec-2025%27%20LIMIT%2010
```