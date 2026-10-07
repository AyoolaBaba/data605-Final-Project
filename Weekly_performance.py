import boto3
import pandas as pd


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