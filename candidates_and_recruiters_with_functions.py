import boto3
import pandas as pd
import mysql.connector

s3 = boto3.client("s3")

bucket_name = "data605-final-project"
prefix = "Talent/"


# -------------------- Test 1
# Used to check which CSV files are available in the Talent folder in S3

# paginator = s3.get_paginator("list_objects_v2")

# for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
#     for file in page.get("Contents", []):
#         key = file["Key"]

#         if key.endswith(".csv"):
#             print(key)


# -------------------- Test 2
# Used to test reading one candidate CSV file from S3

# file_key = "Talent/April2019Applicants.csv"

# response = s3.get_object(
#     Bucket=bucket_name,
#     Key=file_key
# )

# df = pd.read_csv(response["Body"])

# print(df.head())
# print(df.shape)


# Load all monthly candidate CSV files from S3 and combine them into one DataFrame

def load_candidate_data(s3, bucket_name, prefix):
    candidate_dataframes = []

    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        for file in page.get("Contents", []):
            key = file["Key"]

            if key.endswith("Applicants.csv"):
                response = s3.get_object(
                    Bucket=bucket_name,
                    Key=key
                )

                monthly_df = pd.read_csv(response["Body"])

                # Fill missing month values using the month and year from the CSV filename
                file_name = key.split("/")[-1]
                month_year = file_name.replace("Applicants.csv", "")
                month_year = month_year[:-4] + " " + month_year[-4:]

                monthly_df["month"] = monthly_df["month"].fillna(month_year)

                candidate_dataframes.append(monthly_df)

    df = pd.concat(candidate_dataframes, ignore_index=True)

    return df

# Clean the candidates DataFrame

def clean_candidate_data(df):
    # Remove the invited_date column as it is not required
    df = df.drop(columns=["invited_date"])

    # Rename columns to match the ERD
    df = df.rename(columns={
        "id": "candidate_id",
        "dob": "date_of_birth",
        "uni": "university"
    })

    # Convert date_of_birth to datetime format
    df["date_of_birth"] = pd.to_datetime(
        df["date_of_birth"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    # Replace missing values in string columns with "Not given", excluding invited_by
    string_columns = df.select_dtypes(
        include=["object", "string"]
    ).columns

    string_columns = string_columns.drop("invited_by")

    df[string_columns] = df[string_columns].fillna("Not given")

    # Correct misspelled recruiter names in the candidates data
    df["invited_by"] = df["invited_by"].replace({
        "Fifi Etton": "Fifi Eton",
        "Bruno Belbrook": "Bruno Bellbrook"
    })

    return df


# Create recruiters DataFrame and replace recruiter names with recruiter IDs

def create_recruiters_dataframe(df):
    recruiters_df = (
        df["invited_by"]
        .dropna()
        .drop_duplicates()
        .reset_index(drop=True)
        .to_frame(name="recruiter_name")
    )

    recruiters_df["recruiter_id"] = recruiters_df.index + 1

    recruiters_df = recruiters_df[
        ["recruiter_id", "recruiter_name"]
    ]

    df = df.merge(
        recruiters_df,
        left_on="invited_by",
        right_on="recruiter_name",
        how="left"
    )

    df = df.rename(columns={
        "recruiter_id": "invited_by_recruiter_id"
    })

    df = df.drop(columns=[
        "invited_by",
        "recruiter_name"
    ])

    df["invited_by_recruiter_id"] = (
        df["invited_by_recruiter_id"]
        .astype("Int64")
    )

    return df, recruiters_df


# Check the candidates and recruiters DataFrames

# print("Candidates:")
# print(df.head())
# print(df.shape)

# print("\nRecruiters:")
# print(recruiters_df)

# print("\nMissing values:")
# print(df.isnull().sum())

# Check candidates DataFrame column names for MySQL 'candidates' table creation
# print(df.columns.tolist())

# print(df.dtypes)

# Connect to the MySQL database

def connect_to_mysql():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        database="data605_final_project"
    )

    cursor = connection.cursor()

    return connection, cursor


# Insert recruiters DataFrame into the MySQL 'recruiters' table

def insert_recruiters(cursor, connection, recruiters_df):
    insert_recruiter = """
    INSERT IGNORE INTO recruiters (
        recruiter_id,
        recruiter_name
    )
    VALUES (%s, %s)
    """

    recruiter_data = [
        (int(row.recruiter_id), row.recruiter_name)
        for row in recruiters_df.itertuples(index=False)
    ]

    cursor.executemany(insert_recruiter, recruiter_data)

    connection.commit()

    print("Recruiters inserted into MySQL")


# Insert candidates DataFrame into the MySQL 'candidates' table

def insert_candidates(cursor, connection, df):
    insert_candidate = """
    INSERT IGNORE INTO candidates (
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
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    candidate_data = [
        (
            int(row.candidate_id),
            row.name,
            row.gender,
            row.date_of_birth,
            row.email,
            row.city,
            row.address,
            row.postcode,
            row.phone_number,
            row.university,
            row.degree,
            row.month,
            None if pd.isna(row.invited_by_recruiter_id)
            else int(row.invited_by_recruiter_id)
        )
        for row in df.itertuples(index=False)
    ]

    cursor.executemany(insert_candidate, candidate_data)

    connection.commit()

    print("Candidates inserted into MySQL")


# Run the candidate and recruiter ETL process

def main():
    df = load_candidate_data(s3, bucket_name, prefix)

    df = clean_candidate_data(df)

    df, recruiters_df = create_recruiters_dataframe(df)

    connection, cursor = connect_to_mysql()

    insert_recruiters(cursor, connection, recruiters_df)

    insert_candidates(cursor, connection, df)

    cursor.close()
    connection.close()


if __name__ == "__main__":
    main()