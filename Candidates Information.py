import boto3
import pandas as pd

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


# Remove the invited_date column as it is not required

df = df.drop(columns=["invited_date"])


# -------------------- Test 3
# Used to check that all monthly CSV files were combined correctly

# print(df.head())
# print(df.shape)
# print("Missing values in month:", df["month"].isnull().sum())


# -------------------- Test 4
# Used to check data quality before cleaning

# df.info()

# print("\nMissing values:")
# print(df.isnull().sum())

# print("\nDuplicate rows:")
# print(df.duplicated().sum())


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


# -------------------- Test 5
# Used to display rows where date_of_birth is missing

# print(
#     df.loc[
#         df["date_of_birth"].isna(),
#         ["candidate_id", "name", "date_of_birth"]
#     ]
# )

# print(df.dtypes)


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


# Create recruiters DataFrame from unique recruiter names

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


# Replace recruiter names in candidates with recruiter IDs

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


# Check the final candidates and recruiters DataFrames

print("Candidates:")
print(df.head())
print(df.shape)

print("\nRecruiters:")
print(recruiters_df)

print("\nMissing values:")
print(df.isnull().sum())