import boto3
import pandas as pd
import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()

# Make a file called .env in the same folder as this file and write: 
# MYSQL_PASSWORD=[Insert your own mysql password into here]

# -----------------------------
# SETTINGS
# -----------------------------

BUCKET_NAME = "data605-final-project"
PREFIX = "Talent/"
DATABASE_NAME = "data605_final_project"


# -----------------------------
# AWS S3
# -----------------------------

s3 = boto3.client("s3")


# -----------------------------
# LOAD CANDIDATE FILES
# -----------------------------

def load_candidate_data():
    candidate_dataframes = []

    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(
        Bucket=BUCKET_NAME,
        Prefix=PREFIX
    ):
        for file in page.get("Contents", []):
            key = file["Key"]

            if not key.endswith("Applicants.csv"):
                continue

            print(f"Loading: {key}")

            response = s3.get_object(
                Bucket=BUCKET_NAME,
                Key=key
            )

            monthly_df = pd.read_csv(
                response["Body"]
            )

            # Example:
            # April2019Applicants.csv -> April
            file_name = key.split("/")[-1]

            month_text = file_name.replace(
                "Applicants.csv",
                ""
            )

            month_name = (
                pd.Series([month_text])
                .str.extract(
                    r"([A-Za-z]+)",
                    expand=False
                )
                .iloc[0]
            )

            # Replace month completely
            monthly_df["month"] = month_name

            candidate_dataframes.append(
                monthly_df
            )

    if not candidate_dataframes:
        raise ValueError(
            "No applicant CSV files were found in S3."
        )

    df = pd.concat(
        candidate_dataframes,
        ignore_index=True
    )

    return df


# -----------------------------
# CLEAN CANDIDATE DATA
# -----------------------------

def clean_candidate_data(df):

    # Rename columns
    df = df.rename(
        columns={
            "dob": "date_of_birth",
            "uni": "university"
        }
    )

    # Remove columns not needed
    # Keep invited_by for recruiter mapping
    columns_to_remove = [
        "id",
        "invited_date",
        "source_file"
    ]

    df = df.drop(
        columns=[
            column
            for column in columns_to_remove
            if column in df.columns
        ]
    )

    # Create unique candidate IDs
    df = df.reset_index(drop=True)

    df.insert(
        0,
        "candidate_id",
        range(1, len(df) + 1)
    )

    # -------------------------
    # Clean names
    # -------------------------

    if "name" in df.columns:
        df["name"] = (
            df["name"]
            .astype("string")
            .str.strip()
            .str.title()
        )
    name_corrections = {
    "Gerhard Mcgrath": "Gerhard McGrath",
    "Prentice Van Der Hoeven": "Prentice Van der Hoeven",
    "Merrill Mckie": "Merrill McKie",
    "Dina Mcgookin": "Dina McGookin",
    "Robinett Mcphate": "Robinett McPhate",
    "Reg Mcreynold": "Reg McReynold",
    "Haskell Mcdonnell": "Haskell McDonnell",
    "Haroun Mccrohon": "Haroun McCrohon",
    "Heindrick Mckiddin": "Heindrick McKiddin",
    "Brenna Mcgroarty": "Brenna McGroarty",
    "Magda Mckirton": "Magda McKirton",
    "Terrie Mackibbon": "Terrie MacKibbon",
    "Cherrita Mcgilleghole": "Cherrita McGilleghole",
    "Deirdre Van Den Velde": "Deirdre Van den Velde",
    "Derby Mcglashan": "Derby McGlashan"
    }

    df["name"] = df["name"].replace(name_corrections)

    df["name"] = df["name"].replace({
    "Keen Bentham3": "Keen Bentham",
    "L;Urette Daveley": "Lurette Daveley"
    })

    # -------------------------
    # Clean gender
    # -------------------------

    if "gender" in df.columns:
        df["gender"] = (
            df["gender"]
            .astype("string")
            .str.strip()
            .str.title()
        )

    # -------------------------
    # Clean date of birth
    # -------------------------

    if "date_of_birth" in df.columns:
        df["date_of_birth"] = pd.to_datetime(
            df["date_of_birth"],
            dayfirst=True,
            errors="coerce"
        )

    # -------------------------
    # Clean email
    # -------------------------

    if "email" in df.columns:
        df["email"] = (
            df["email"]
            .astype("string")
            .str.strip()
            .str.lower()
        )

    # -------------------------
    # Clean city
    # -------------------------

    if "city" in df.columns:
        df["city"] = (
            df["city"]
            .astype("string")
            .str.strip()
            .str.title()
        )

    # -------------------------
    # Clean address
    # -------------------------

    if "address" in df.columns:
        df["address"] = (
            df["address"]
            .astype("string")
            .str.strip()
        )

    # -------------------------
    # Clean postcode
    # -------------------------

    if "postcode" in df.columns:
        df["postcode"] = (
            df["postcode"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

    # -------------------------
    # Clean phone numbers
    # Keep only digits and +
    # -------------------------

    if "phone_number" in df.columns:
        df["phone_number"] = (
            df["phone_number"]
            .astype("string")
            .str.replace(
                r"[^\d+]",
                "",
                regex=True
            )
            .replace("", pd.NA)
        )

    # -------------------------
    # Clean university
    # -------------------------

    if "university" in df.columns:
        df["university"] = (
            df["university"]
            .astype("string")
            .str.strip()
            .str.title()
        )

    # -------------------------
    # Clean degree
    # -------------------------

    if "degree" in df.columns:
        df["degree"] = (
            df["degree"]
            .astype("string")
            .str.strip()
        )

    # -------------------------
    # Standardise month names
    # -------------------------

    if "month" in df.columns:

        month_mapping = {
            "Jan": "January",
            "Feb": "February",
            "Mar": "March",
            "Apr": "April",
            "Jun": "June",
            "Jul": "July",
            "Aug": "August",
            "Sep": "September",
            "Sept": "September",
            "Oct": "October",
            "Nov": "November",
            "Dec": "December"
        }

        df["month"] = (
            df["month"]
            .astype("string")
            .str.replace(
                r"\s\d{4}$",
                "",
                regex=True
            )
            .str.strip()
            .str.title()
            .replace(month_mapping)
        )

    # -------------------------
    # Clean recruiter names
    # -------------------------

    if "invited_by" in df.columns:

        df["invited_by"] = (
            df["invited_by"]
            .astype("string")
            .str.strip()
            .str.title()
        )

        # Correct known spelling mistakes
        df["invited_by"] = (
            df["invited_by"]
            .replace({
                "Fifi Etton": "Fifi Eton",
                "Bruno Belbrook": "Bruno Bellbrook"
            })
        )

        # Keep missing recruiter values as null
        df["invited_by"] = (
            df["invited_by"]
            .replace({
                "": pd.NA,
                "Nan": pd.NA,
                "<Na>": pd.NA
            })
        )

    # -------------------------
    # Fill missing string values
    # -------------------------

    string_columns = (
        df.select_dtypes(
            include=["object", "string"]
        )
        .columns
        .tolist()
    )

    # Do not fill invited_by
    # because missing recruiter should remain NULL
    if "invited_by" in string_columns:
        string_columns.remove(
            "invited_by"
        )

    df[string_columns] = (
        df[string_columns]
        .fillna("Not given")
    )

    return df


# -----------------------------
# CREATE RECRUITERS DATAFRAME
# -----------------------------

def create_recruiters_dataframe(df):

    if "invited_by" not in df.columns:
        raise ValueError(
            "The invited_by column was not found."
        )

    recruiters_df = (
        df["invited_by"]
        .dropna()
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
        .to_frame(
            name="recruiter_name"
        )
    )

    # Create recruiter IDs
    recruiters_df.insert(
        0,
        "recruiter_id",
        range(
            1,
            len(recruiters_df) + 1
        )
    )

    # Add recruiter IDs to candidates
    df = df.merge(
        recruiters_df,
        left_on="invited_by",
        right_on="recruiter_name",
        how="left",
        validate="many_to_one"
    )

    # Rename recruiter ID
    df = df.rename(
        columns={
            "recruiter_id":
            "invited_by_recruiter_id"
        }
    )

    # Remove recruiter names from candidates
    df = df.drop(
        columns=[
            "invited_by",
            "recruiter_name"
        ]
    )

    df["invited_by_recruiter_id"] = (
        df["invited_by_recruiter_id"]
        .astype("Int64")
    )

    # Final candidate columns
    final_columns = [
        "candidate_id",
        "name",
        "gender",
        "date_of_birth",
        "email",
        "city",
        "address",
        "postcode",
        "phone_number",
        "university",
        "degree",
        "month",
        "invited_by_recruiter_id"
    ]

    df = df[final_columns]

    return df, recruiters_df


# -----------------------------
# SHOW AND VALIDATE DATA
# -----------------------------

def validate_data(
    df,
    recruiters_df
):

    expected_months = {
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December"
    }

    duplicate_ids = (
        df["candidate_id"]
        .duplicated()
        .sum()
    )

    actual_months = set(
        df["month"]
        .dropna()
        .unique()
    )

    bad_months = (
        actual_months
        - expected_months
    )

    print(
        "\n============================"
    )
    print(
        "CLEANED CANDIDATES TABLE"
    )
    print(
        "============================"
    )

    print(
        df.head(50)
        .to_string(index=False)
    )

    print(
        "\n============================"
    )
    print(
        "RECRUITERS TABLE"
    )
    print(
        "============================"
    )

    print(
        recruiters_df
        .to_string(index=False)
    )

    print(
        "\n============================"
    )
    print(
        "COLUMN NAMES"
    )
    print(
        "============================"
    )

    print(
        df.columns.tolist()
    )

    print(
        "\n============================"
    )
    print(
        "MONTH VALUES"
    )
    print(
        "============================"
    )

    month_order = [
        month
        for month in [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December"
        ]
        if month in actual_months
    ]

    print(
        month_order
    )

    print(
        "\n============================"
    )
    print(
        "MISSING VALUES"
    )
    print(
        "============================"
    )

    print(
        df.isnull().sum()
    )

    print(
        "\n============================"
    )
    print(
        "CANDIDATE ID CHECK"
    )
    print(
        "============================"
    )

    print(
        "Duplicate candidate IDs:",
        duplicate_ids
    )

    print(
        "First candidate ID:",
        df["candidate_id"].min()
    )

    print(
        "Last candidate ID:",
        df["candidate_id"].max()
    )

    print(
        "Total rows:",
        len(df)
    )

    if duplicate_ids != 0:
        raise ValueError(
            "Duplicate candidate IDs still exist."
        )

    if bad_months:
        raise ValueError(
            f"Unexpected months: "
            f"{sorted(bad_months)}"
        )


# -----------------------------
# CONNECT TO MYSQL
# -----------------------------

def connect_to_mysql():

    connection = (
        mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password=os.getenv('MYSQL_PASSWORD')
        )
    )

    cursor = (
        connection.cursor()
    )

    # Create database
    cursor.execute(
        f"""
        CREATE DATABASE
        IF NOT EXISTS
        `{DATABASE_NAME}`
        """
    )

    cursor.execute(
        f"""
        USE `{DATABASE_NAME}`
        """
    )

    return connection, cursor


# -----------------------------
# INSERT RECRUITERS
# -----------------------------

def insert_recruiters(
    cursor,
    connection,
    recruiters_df
):

    insert_query = """
        INSERT INTO recruiters (
            recruiter_id,
            recruiter_name
        )
        VALUES (%s, %s)
    """

    recruiter_data = [
        (
            int(row.recruiter_id),
            row.recruiter_name
        )
        for row
        in recruiters_df.itertuples(
            index=False
        )
    ]

    cursor.executemany(
        insert_query,
        recruiter_data
    )

    connection.commit()

    print(
        f"{len(recruiter_data)} "
        f"recruiters inserted."
    )


# -----------------------------
# INSERT CANDIDATES
# -----------------------------

def insert_candidates(
    cursor,
    connection,
    df
):

    insert_query = """
        INSERT INTO candidates (
            candidate_id,
            name,
            gender,
            date_of_birth,
            email,
            city,
            address,
            postcode,
            phone_number,
            university,
            degree,
            month,
            invited_by_recruiter_id
        )
        VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s
        )
    """

    candidate_data = [
        (
            int(row.candidate_id),

            row.name,

            row.gender,

            None
            if pd.isna(
                row.date_of_birth
            )
            else row.date_of_birth.date(),

            row.email,

            row.city,

            row.address,

            row.postcode,

            None
            if pd.isna(
                row.phone_number
            )
            else row.phone_number,

            row.university,

            row.degree,

            row.month,

            None
            if pd.isna(
                row.invited_by_recruiter_id
            )
            else int(
                row.invited_by_recruiter_id
            )
        )

        for row
        in df.itertuples(
            index=False
        )
    ]

    cursor.executemany(
        insert_query,
        candidate_data
    )

    connection.commit()

    print(
        f"{len(candidate_data)} "
        f"candidates inserted."
    )


# -----------------------------
# SHOW MYSQL TABLES
# -----------------------------

def check_mysql_tables(
    cursor
):

    # Show recruiters
    cursor.execute(
        """
        SELECT *
        FROM recruiters
        ORDER BY recruiter_id
        """
    )

    recruiter_rows = (
        cursor.fetchall()
    )

    recruiters_table = (
        pd.DataFrame(
            recruiter_rows,
            columns=[
                "recruiter_id",
                "recruiter_name"
            ]
        )
    )

    print(
        "\n============================"
    )
    print(
        "MYSQL RECRUITERS TABLE"
    )
    print(
        "============================"
    )

    print(
        recruiters_table
        .to_string(index=False)
    )

    # Show candidates
    cursor.execute(
        """
        SELECT
            candidate_id,
            name,
            gender,
            date_of_birth,
            email,
            city,
            address,
            postcode,
            phone_number,
            university,
            degree,
            month,
            invited_by_recruiter_id

        FROM candidates

        ORDER BY candidate_id

        LIMIT 50
        """
    )

    candidate_rows = (
        cursor.fetchall()
    )

    candidates_table = (
        pd.DataFrame(
            candidate_rows,
            columns=[
                "candidate_id",
                "name",
                "gender",
                "date_of_birth",
                "email",
                "city",
                "address",
                "postcode",
                "phone_number",
                "university",
                "degree",
                "month",
                "invited_by_recruiter_id"
            ]
        )
    )

    print(
        "\n============================"
    )
    print(
        "MYSQL CANDIDATES TABLE"
    )
    print(
        "============================"
    )

    print(
        candidates_table
        .to_string(index=False)
    )

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM candidates
        """
    )

    total = (
        cursor.fetchone()[0]
    )

    print(
        "\nTotal candidates in MySQL:",
        total
    )


# -----------------------------
# MAIN
# -----------------------------

def main():

    connection = None
    cursor = None

    try:

        print(
            "Loading candidate data from S3..."
        )

        df = (
            load_candidate_data()
        )

        print(
            "\nCleaning candidate data..."
        )

        df = (
            clean_candidate_data(
                df
            )
        )

        print(
            "\nCreating recruiters..."
        )

        df, recruiters_df = (
            create_recruiters_dataframe(
                df
            )
        )

        print(
            "\nChecking cleaned data..."
        )

        validate_data(
            df,
            recruiters_df
        )

        print(
            "\nConnecting to MySQL..."
        )

        connection, cursor = (
            connect_to_mysql()
        )

        insert_recruiters(
            cursor,
            connection,
            recruiters_df
        )

        insert_candidates(
            cursor,
            connection,
            df
        )

        check_mysql_tables(
            cursor
        )

        print(
            "\nDONE"
        )

    finally:

        if cursor is not None:
            cursor.close()

        if (
            connection is not None
            and connection.is_connected()
        ):
            connection.close()


if __name__ == "__main__":
    main()