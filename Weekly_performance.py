import boto3
import pandas as pd
from sqlalchemy import create_engine, text
import pymysql
import mysql.connector
import os

def weekly_performance_csv():
    """Taking weekly performances from 36 cohorts and transforming into long format for each student"""

    # Importing s3 bucket to take data from
    s3_client = boto3.client('s3')
    bucket_name = "data605-final-project"

    # Taking out specifically the cohort data
    academy_bucket_contents = s3_client.list_objects_v2(
        Bucket=bucket_name,
        Prefix="Academy/"
    )

    # Creating a list to add data to, in order to transform into a data frame
    all_records = []

    # Adding trainers to a unique list to be used later
    trainers = set()
    cohorts = set()
    streams = set()

    cohort_dict = []

    # Running through each entry in the bucket with academy prefix
    for content in academy_bucket_contents['Contents']:

        cohort_info = {}

        # Pulling the object from S3
        csv_object = s3_client.get_object(
            Bucket=bucket_name,
            Key=content['Key']
        )
        csv_body = csv_object['Body']

        # Getting the csv title to be used as the cohort title
        csv_key = content['Key'][8:][:-4]
        csv_key = csv_key.split('_')
        cohort_title = csv_key[0] + " " + csv_key[1]
        stream_title = csv_key[0]

        # Adding cohort and streams to set to get a list of unique entries
        streams.add(stream_title)
        cohorts.add(cohort_title)

        # Reading in the csv for each cohort
        df = pd.read_csv(csv_body)

        # As the week number is dynamic, creating a unique list
        # of all the entries to be worked through later
        weeks = set()

        cohort_info['cohort_name'] = cohort_title
        cohort_info['stream_name'] = stream_title

        valid_trainers = df["trainer"].dropna().unique()
        if len(valid_trainers) > 0:
            trainer = valid_trainers[0]
            if trainer == "Ely Kely":
                trainer = "Elly Kelly"
            cohort_info["trainer_name"] = trainer
            trainers.add(trainer)
        else:
            cohort_info["trainer_name"] = "Not given"


        for col in df.columns:
            if "_W" in col:
                week_num = int(col.split("_W")[1])
                weeks.add(week_num)

        sorted_weeks = sorted(list(weeks))


        # Working through each row
        for _, row in df.iterrows():

            name = row.get("name")


            # Setting up the correct name
            if name == "Gerhard Mcgrath":
                name = "Gerhard McGrath"
            elif name == "Prentice Van Der Hoeven":
                name = "Prentice Van der Hoeven"
            elif name == "Merrill Mckie":
                name = "Merrill McKie"
            elif name == "Dina Mcgookin":
                name = "Dina McGookin"
            elif name == "Robinett Mcphate":
                name = "Robinett McPhate"
            elif name == "Reg Mcreynold":
                name = "Reg McReynold"
            elif name == "Haskell Mcdonnell":
                name = "Haskell McDonnell"
            elif name == "Haroun Mccrohon":
                name = "Haroun McCrohon"
            elif name == "Heindrick Mckiddin":
                name = "Heindrick McKiddin"
            elif name == "Brenna Mcgroarty":
                name = "Brenna McGroarty"
            elif name == "Magda Mckirton":
                name = "Magda McKirton"
            elif name == "Terrie Mackibbon":
                name = "Terrie MacKibbon"
            elif name == "Cherrita Mcgilleghole":
                name = "Cherrita McGilleghole"
            elif name == "Deirdre Van Den Velde":
                name = "Deirdre Van den Velde"
            elif name == "Derby Mcglashan":
                name = "Derby McGlashan"

            # Determining if a student is a drop out
            drop_out = "No"

            # If the entry for analytic performance is NaN,
            # setting drop out to Yes
            for j in sorted_weeks:
                if pd.isna(row.get(f'Analytic_W{j}')):
                    drop_out = "Yes"
                    break

            # Working through the long row and slicing weekly
            # information from each, then appending week by week
            for j in sorted_weeks:

                # To ensure no empty values are added
                # into the final dataframe
                if pd.isna(row.get(f'Analytic_W{j}')) is False:
                    all_records.append({
                        'candidate_name': name,
                        'cohort_name': cohort_title,
                        'week_number': j,
                        'analytic_score': row.get(f'Analytic_W{j}'),
                        'independent_score': row.get(f'Independent_W{j}'),
                        'determined_score': row.get(f'Determined_W{j}'),
                        'professional_score': row.get(f'Professional_W{j}'),
                        'studious_score': row.get(f'Studious_W{j}'),
                        'imaginative_score': row.get(f'Imaginative_W{j}'),
                        'drop_out': drop_out
                    })
        cohort_dict.append(cohort_info)

    # Returning the final in dataframe format
    return pd.DataFrame(all_records), trainers, cohorts, streams, cohort_dict

def weekly_performance_main():
    # ---------------- Connecting to the database ----------------

    db_user = 'root'
    db_password = os.getenv('MYSQL_PASSWORD')
    db_host = 'localhost'
    db_database = 'data605_final_project'

    engine = create_engine(
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_database}"
    )

    try:
        with engine.begin() as connection:
            connection.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            connection.execute(text("TRUNCATE TABLE weekly_performances;"))
            connection.execute(text("TRUNCATE TABLE cohorts;"))
            connection.execute(text("TRUNCATE TABLE trainers;"))
            connection.execute(text("TRUNCATE TABLE streams;"))
            connection.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        print("Successfully truncated existing tables.")
    except Exception as e:
        print("Failed to truncate tables:", e)


    #  ---------------- Retrieving the Data from the functions ----------------

    weekly_performance_df, trainers, cohorts, streams, cohort_dict = weekly_performance_csv()

    trainers_df = pd.DataFrame(trainers, columns= ['trainer_name'])
    streams_df = pd.DataFrame([
        {"stream_id": 1, "stream_name": "Data"},
        {"stream_id": 2, "stream_name": "Business"},
        {"stream_id": 3, "stream_name": "Engineering"}
        # Add any other streams you have
    ])

    cohort_df = pd.DataFrame(cohort_dict)

    cohort_df = cohort_df.drop_duplicates(subset=["cohort_name"]).reset_index(
        drop=True
    )

    # ---------------- Uploading Primary Data ----------------
    try:
        trainers_df.to_sql(name = 'trainers', con = engine, if_exists = 'append', index = False)
        print("Successfully outputted trainers")

        streams_df.to_sql(name = 'streams', con = engine, if_exists = 'append', index = False)
        print("Successfully outputted streams")

    except Exception as e:
        print("Failed", e)

    # ---------------- Cohort Referencing ----------------

    trainer_lookup = pd.read_sql("SELECT trainer_id, trainer_name FROM trainers", con = engine)

    trainer_map = dict(zip(trainer_lookup['trainer_name'], trainer_lookup['trainer_id']))
    stream_map = dict(zip(streams_df["stream_name"], streams_df["stream_id"]))

    cohort_df['trainer_id'] = cohort_df['trainer_name'].map(trainer_map)
    cohort_df['stream_id'] = cohort_df['stream_name'].map(stream_map)

    cohort_df.drop(columns = ['trainer_name', 'stream_name'], inplace = True)

    cohort_df.to_sql(name='cohorts', con=engine, if_exists='append', index=False)
    print("Successfully outputted cohorts")


    # ---------------- Weekly Scores Referencing ----------------

    cohort_lookup = pd.read_sql("SELECT cohort_id, cohort_name FROM cohorts", con = engine)
    candidate_lookup = pd.read_sql("SELECT candidate_id, name FROM candidates", con = engine)

    cohort_map = dict(zip(cohort_lookup["cohort_name"], cohort_lookup["cohort_id"]))
    candidate_map = dict(zip(candidate_lookup["name"], candidate_lookup["candidate_id"]))

    weekly_performance_df["cohort_id"] = weekly_performance_df["cohort_name"].map(cohort_map)
    weekly_performance_df["candidate_id"] = weekly_performance_df["candidate_name"].map(candidate_map)

    # # Check if the missing performance names are anywhere in the original candidates dataframe
    # missing_names = weekly_performance_df[
    #     ~weekly_performance_df["candidate_name"].isin(candidate_lookup["name"])
    # ]["candidate_name"].unique()
    #
    # print("Unmatched names:", missing_names)
    #
    # print("Null check for IDs:")
    # print(weekly_performance_df[["cohort_id", "candidate_id"]].isnull().sum())
    #
    weekly_performance_df.drop(columns = ['cohort_name', 'candidate_name'], inplace = True)

    weekly_performance_df.to_sql(name='weekly_performances', con = engine, if_exists = 'append', index = False)
    print("Successfully outputted weekly_performances")

    # import difflib
    #
    # unmatched_names = weekly_performance_df[
    #     weekly_performance_df["candidate_id"].isna()\
    # ]["candidate_name"].unique()
    #
    # valid_names = candidate_lookup["name"].tolist()
    #
    # print(f"Found {len(unmatched_names)} unique unmatched names.\n")
    # print(f"{'Performance Name (Unmatched)':<30} | {'Closest Candidate Match':<30}")
    # print("-" * 65)
    #
    # for name in unmatched_names:
    #   matches = difflib.get_close_matches(name, valid_names, n=1, cutoff=0.6)
    #   closest = matches[0] if matches else "--- NO MATCH ---"
    #   print(f"{name:<30} | {closest:<30}")