# Academy of Delphi: ETL Pipeline

An ETL pipeline for the fictional Sparta Global *Academy of Delphi*. It reads raw
recruitment and academy data from AWS S3, cleans it with Python, stores it in a
MySQL database, and makes it ready for analysis and a dashboard.

## Goals

- Read raw data from S3 **without editing or deleting it**
- Clean and transform the data with Python (`pandas`)
- Store it in a relational MySQL database
- Provide a **single person view**: everything we know about one candidate
- Answer business questions with SQL and a dashboard
- *Extension:* automatically handle new files arriving in S3

## The data

The academy process the data describes:

1. Candidates apply and their contact details are collected
2. They are invited to an assessment day (Sparta Day) and assessed
3. Successful candidates start in the academy, in a cohort on a stream
4. Each week, trainees are scored (out of 8), and low scorers can drop out

| S3 prefix | Contents |
|-----------|----------|
| `Talent/` | Monthly applicant files, e.g. `April2019Applicants.csv` |
| `Academy/` | One file per cohort, with weekly scores for each trainee |

The original files are only ever read.

## How the pipeline works

```
S3 bucket (raw CSVs)  ->  Extract (boto3)  ->  Transform (pandas)  ->  Load  ->  MySQL
```

## Database design

*(ERD image here, e.g. `![ERD](docs/erd.png)`)*

| Table | Purpose |
|-------|---------|
| `recruiters` | One row per recruiter |
| `candidates` | One row per applicant, linked to the recruiter who invited them |
| `streams` | Academy streams: Data, Business, Engineering |
| `trainers` | One row per trainer |
| `cohorts` | One row per cohort, linked to a stream and a trainer |
| `weekly_performances` | One row per candidate per week, with six trait scores and a drop-out flag |

Key relationships:

- `candidates.invited_by_recruiter_id` references `recruiters.recruiter_id`
- `cohorts.stream_id` references `streams.stream_id`
- `cohorts.trainer_id` references `trainers.trainer_id`
- `weekly_performances` references `candidates` and `cohorts`

## Scripts

### `candidates_etl.py`

1. **Extract:** reads every `*Applicants.csv` in `Talent/` and combines them. The month comes from the file name.
2. **Transform:**
   - Renames columns (`dob` to `date_of_birth`, `uni` to `university`)
   - Drops unused columns and generates a unique `candidate_id`
   - Standardises names, gender, email, city, postcode, university and month
   - Parses dates of birth and cleans phone numbers (digits and `+` only)
   - Corrects misspelt recruiter names and builds the `recruiters` table
   - Fills missing text with "Not given" (a missing recruiter stays `NULL`)
3. **Validate:** checks for duplicate IDs and unexpected months, and prints the results.
4. **Load:** creates the `recruiters` and `candidates` tables, inserts the data, and prints what is in MySQL.

### `weekly_performance_etl.py`

1. **Extract:** reads each cohort file in `Academy/`. The file name gives the stream and cohort.
2. **Transform:** converts each cohort file from wide format (one column per week) to long format (one row per candidate per week), corrects name capitalisation, and flags trainees who dropped out (missing weekly scores).
3. **Load:** fills `streams`, `trainers` and `cohorts`, looks up candidate and cohort IDs, then fills `weekly_performances`.

## Getting started

**Requirements:** Python 3.13, MySQL, and AWS credentials with read access to the bucket.

```bash
git clone https://github.com/AyoolaBaba/data605-Final-Project.git
cd data605-Final-Project
python -m venv .venv
source .venv/bin/activate
pip install boto3 pandas mysql-connector-python sqlalchemy pymysql cryptography
aws configure
```

**Passwords:** never commit passwords or keys.

- `candidates_etl.py` asks for your MySQL password when it runs.
- `weekly_performance_etl.py` reads it from an environment variable:

```bash
export MYSQL_PASSWORD="your-password"
```

**Run order**

1. Run `candidates_etl.py`. It creates the database `data605_final_project` and the `recruiters` and `candidates` tables.
2. Create the remaining tables (`streams`, `trainers`, `cohorts`, `weekly_performances`) using the team's schema script.
3. Run `weekly_performance_etl.py`. It needs the candidates to exist already.

**Re-running:** both scripts clear their tables on each run, so they are safe to repeat. Because `weekly_performances` points at `candidates`, clear `weekly_performances` before re-running `candidates_etl.py`.

## Example queries

**Candidates with no recruiter recorded**

```sql
SELECT candidate_id, name, invited_by_recruiter_id
FROM candidates
WHERE invited_by_recruiter_id IS NULL;
```

**Number of candidates invited by each recruiter**

```sql
SELECT r.recruiter_id, r.recruiter_name, COUNT(c.candidate_id) AS total_candidates
FROM recruiters AS r
LEFT JOIN candidates AS c
    ON r.recruiter_id = c.invited_by_recruiter_id
GROUP BY r.recruiter_id, r.recruiter_name
ORDER BY r.recruiter_id;
```

**Candidates by month, in calendar order**

```sql
SELECT month, COUNT(*) AS total_candidates
FROM candidates
GROUP BY month
ORDER BY FIELD(month, 'January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December');
```

**Single person view** (everything about one candidate)

```sql
SELECT c.*, r.recruiter_name,
       co.cohort_name, s.stream_name, t.trainer_name,
       w.week_number, w.analytic_score, w.independent_score, w.determined_score,
       w.professional_score, w.studious_score, w.imaginative_score, w.drop_out
FROM candidates AS c
LEFT JOIN recruiters AS r ON c.invited_by_recruiter_id = r.recruiter_id
LEFT JOIN weekly_performances AS w ON w.candidate_id = c.candidate_id
LEFT JOIN cohorts AS co ON w.cohort_id = co.cohort_id
LEFT JOIN streams AS s ON co.stream_id = s.stream_id
LEFT JOIN trainers AS t ON co.trainer_id = t.trainer_id
WHERE c.candidate_id = 1
ORDER BY w.week_number;
```

## Project status

| Area | Status |
|------|--------|
| Candidates and recruiters ETL | Done |
| Weekly performance ETL | Done |
| Assessment data (Sparta Day) | In progress |
| Single person view | Query drafted |
| Dashboard and business questions | Not started |
| Extension: handle new S3 files | Not started |

*(Update this table to match your board.)*

## Ways of working

- **Scrum:** one sprint per working day, with a board tracking user stories
- **Git flow:** work happens on feature branches, merged into `main` through reviewed pull requests

## Tables each team worked on

| Name | Work |
|------|------|
| *Ayoola, Quaresh and Stella* | *Candidates and recruiters* |
| *Baahand, Adbi and Luke* | *Strengths and weaknesses and overall json + txt file cleaning* |
| *Dominic, Quadrulla and Muhammad* | *Weekly performance, Cohort and Trainer information and streams tables* |

## Next steps

1. Finish loading the assessment data
2. Make candidate names in the weekly data match those in `candidates`, so every trainee links to a candidate
3. Finalise the single person view
4. Choose business questions and build the dashboard
5. Extension: process new files as they arrive in S3
