# 311 L&I Performance Analysis

## Overview

This project downloads 311 service request data, enriches it with property information from the AIS API, and cross-references it with code violations to generate some simple metrics.

This project is repeatable, and can be run with the following command:
```
python run_pipeline.py
```

In doing so, it will download 311 and code violation data, enrich the 311 data with property information from the AIS API, and match the 311 data to the code violation data to generate a report. Note, that it can be run with the parameter `--clean` to clean the database and start from scratch. 



## Results (Completed)

- Total Service Requests: 45,656
- Service Requests with Code Violations: 19,631 (43.0%)
- Service Requests with Status 'Open': 18,374 (40.2%)

The report is saved in the project root directory, and is based on 2025 data.

## Technologies Used

I have used python3 for this project, as I am comfortable with it, and it is a good fit for the task, with it's built in logging, sqlite3, and threading capabilities.

I have used the following python libraries:
- requests
- sqlite3
- logging

I have used the following tools:
- Git for version control
- Cursor for an IDE

## Future Improvements
- Coalesce the sqlite database calls into a single ORM file. This will improve readability and maintainability of the code.
- Some of the addresses in the 311 collection are not valid, and there is no fallback for these. I have skipped these for now, but we could look into some data cleaning techniques to handle these cases.

## Task List (Completed)

I have broken down the task into a series of smaller tasks, listed below. Each of these tasks is a python script, with a main function, and a set of helper functions.

I have, when possible, included the decision points I made, and the rationale for my decisions.

### 1. Download 311 Tickets
- [x] Create a script to download 311 tickets for 2025 assigned to L&I
  - I have incorporated batching to the script, to prevent putting too much into memory at once. 
  - Here, and elsewhere, I have also only downloaded the columns that are needed for the analysis, to speed up the process.
- [x] Add downloaded records to a local data store. 
- [x] **Decision needed:** Storage format (Python pickle, SQLite, or PostgreSQL)
  - SQLite: Portable, queryable, good for ~50k records. It's built in to python, relational, and easy to use/tear down.

### 2. Enrich with AIS Property Data
- [x] Iterate through _all addresses_ in the 311 collection (~50k records, 28,388 unique addresses)
  - Again, batching to prevent putting too much into memory at once.
- [x] Query the AIS API using the `address` field
  - This step was taking a long time, so I have parallelized the process. 10 threads at a time allowed me to get the job done in a reasonable amount of time, while not messing with the default threading behavior of requests. **Note**, I have since increased the number of threads to 300, to speed up the process. This seems to not be an issue for the AIS API.
- [x] Extract and store `opa_account_num` in the local data store, keyed by address. This will be used to match the 311 tickets to the code violations, for O(1) lookup time.
  - I used a seperate table for this, instead of adding a column to the 311 tickets table. I think this improves readability, and there's a slight performance improvement due to the smaller table size.
- [x] **questions:**
  - How to handle NULL/empty address fields?
    - Skip these records for now. This is a reasonable assumption, as the 311 tickets are not assigned to a specific address, and the AIS API is not designed to handle this.
  - How to handle duplicate `opa_account_num` (multiple violations at the same address)?
    - opa_account num is not a unique identifier, this is not a problem. Note that we can populate multiple tickets with the same opa_account_num, as a performance optimization.

### 3. Download Code Violations

Matching the opa_account_num to the code violations _can_ be done via the carto api, but it requires a lot of HTTP requests, on the order of ten requests per address (searching for violations with opa_account_num IN (1, 2, 3...)).

It makes more sense to download the code violations dataset, and match the opa_account_num to the code violations in our own database, so that is what I have done.



- [x] Download the property code violations dataset
  - Again, batching to prevent putting too much into memory at once, and only downloading the columns that are needed for the analysis.
- [x] Store the property code violations in a local data store.

### 4. Match with Code Violations

This script has an interesting decision point: how to handle multiple violations at the same opa_account_num? I have listed the different approaches I considered in the appendix. We will use Approach 2: each violation can 'validate' multiple tickets. Note that we can 'validate' multiple tickets with a single violation, as a performance optimization.

- [x] Write a script to match the 311 tickets to the code violations.
  - Again, batching to prevent putting too much into memory at once.
  - I have incorporated a count of the number of violations for each ticket, to make the report more readable.
- [x] **Open questions:**
    - how to handle multiple violations at the opa_account_num?
        - See below for different approaches. We will use Approach 2: each violation can 'validate' multiple tickets. Note that we can 'validate' multiple tickets with a single violation, as a performance optimization.


### 5. Generate Report
- [x] Write a script to answer the following questions:
  - How many service requests were captured?
  - What percentage have a matching code violation?
  - What percentage of service requests have status "open"?
- [x] Output results to a text file saved in the local data store

### 6. Dockerize the Pipeline
- [ ] Wrap all scripts and dependencies in a Dockerfile
- [ ] Enable execution via: `docker container run 311_LI_performance`


I have written a python script to run the pipeline in order. 
```
python run_pipeline.py
```

The report is saved in the project root directory. The report is also printed to the console, as well as the logs.

Docker is not enabled for this project. Though it is not possible to test the pipeline in a container, the docker file would roughly look like this:
```
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "run_pipeline.py"]

```

The docker file would be built and run with the following commands:
```
docker build -t 311_LI_performance .
docker container run 311_LI_performance
```

The report would be saved in the project root directory.

---

## Data Sources

| Dataset | Source |
|---------|--------|
| 311 Service Requests | [OpenDataPhilly](https://www.opendataphilly.org/datasets/311-service-and-information-requests/) |
| AIS API | [Philadelphia AIS](https://github.com/CityOfPhiladelphia/ais) |
| Property Code Violations | [OpenDataPhilly](https://www.opendataphilly.org/datasets/code-violations/) |

---

## Project Structure

```
city_of_philadelphia_take_home/
├── README.md
├── run_pipeline.py
├── requirements.txt
├── download_311.py
├── download_violations.py
├── enrich_ais.py
├── enrich_violations.py
├── match_violations.py
├── generate_report.py
├── data/
│   └── (local data store)

```

## Questions I have answered

1. **Storage format:** What's the best storage solution for ~50k records with enrichment?
    - SQLite is a good option for a local data store for ~50k records
2. **NULL addresses:** Skip, log, or attempt geocoding via alternate fields?
    - Skip these records for now
3. **Duplicate OPA numbers:** Aggregate stats, or track individual request-to-violation mappings?
    - See below for different approaches. We will use Approach 2: each violation can 'validate' multiple tickets.
4. **Rate limiting:** Does the AIS API have rate limits we need to respect?
    - No, the AIS API does not have rate limits.

## Rate Limiting
The AIS API does not have rate limits.  

# Appendix A: Different Approaches for Matching 311 Tickets to Code Violations

Seeing as there may be multiple requests per address, and multiple violations per address, there are a couple ways to estimate if service requests resulted in a code violation. (which I'm calling 'validating' the request below)

I am also going to limit the validation by date, so that service requests can only be validated by violations that were issued after the service request was made.

Service Request A: Address A, Jan 3, 2025
Violation: Address A, Jan 1, 2025

In this case, Service Request A is not validated by the violation, as the violation was issued before the service request was made.

## Approach 1: One-to-Many Mapping 

If there are multiple requests at the same address, and one violation, we will count all requests as 'validated' by the violation. 

```
Service Request A: Address A, Jan 1, 2025
Service Request B: Address A, Jan 2, 2025

Violation: Address A, Jan 3, 2025
```

In this case, we would count Service Request A and Service Request B as 'validated' by the violation.

```
Service Request A: Address A, Jan 1, 2025, validated by Violation: Address A, Jan 3, 2025
Service Request B: Address A, Jan 2, 2025, validated by Violation: Address A, Jan 3, 2025


Total Service Requests: 2
Total Requests with Code Violations: 2
```

This seems like a reasonable approach for this analysis, seeing as we are interested in how many tickets mapped to a violation, and not specifically which violations each ticket is mapped to. If multiple tickets are submitted for the same violation, that still counts as a 'success'.


## Approach 2: One-to-One Mapping 

If there are multiple requests at the same address, and one violation, we will count the first request as 'validated' by the violation.

```
Service Request A: Address A, Jan 1, 2025
Service Request B: Address A, Jan 2, 2025
Violation: Address A, Jan 3, 2025
```

In this case, we would count Service Request A as 'validated' by the violation.

```
Service Request A: Address A, Jan 1, 2025, validated by Violation: Address A, Jan 3, 2025
Service Request B: Address A, Jan 2, 2025, [No Match]

Service Request Count: 2
Validated Request Count: 1
```

This approach is more conservative, and more complicated. I'm not sure it's more accurate, and after talking with stakeholders, they seemed to prefer Approach 1.

# Appendix B: Experimentation with the api calls


``` 
q=SELECT cartodb_id FROM public_cases_fc WHERE requested_datetime BETWEEN '01-Jan-2025’ AND '31-Dec-2025’ and address is not null group by address
```

``` 
q=SELECT cartodb_id FROM public_cases_fc WHERE requested_datetime BETWEEN '01-Jan-2025’ AND '31-Dec-2025’
```

``` 
https://phl.carto.com/api/v2/sql?q=SELECT%20*%20FROM%20public_cases_fc%20WHERE%20requested_datetime%20BETWEEN%20%2701-Jan-2025%27%20AND%20%2731-Dec-2025%27%20LIMIT%2010
```