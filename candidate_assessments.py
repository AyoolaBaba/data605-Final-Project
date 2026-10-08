#!/usr/bin/env python
# coding: utf-8

# In[216]:


import boto3
from pprint import pprint
import pandas as pd
import numpy as np
from io import StringIO
import json
from candidates_info import connect_to_mysql


# In[2]:


# Get list of all objects from the bucket
s3_client = boto3.client('s3')
bucket_name = 'data605-final-project'

paginator = s3_client.get_paginator('list_objects_v2')

all_objects = []

for page in paginator.paginate(Bucket=bucket_name):
    all_objects.extend(page.get('Contents', []))


# In[3]:


# Load all objects using get_object method
all_jsons = []

for obj in all_objects:
    if not obj['Key'].endswith('.json'):
        continue

    response = s3_client.get_object(
        Bucket=bucket_name,
        Key=obj['Key']
    )

    # 
    res = json.loads(response['Body'].read().decode('utf-8'))
    all_jsons.append(res)


# In[111]:


# Verify that there are 3105 JSON files
print(len(all_jsons))


# In[112]:


# Check for and remove duplicates
print('Before:', len(all_jsons))

seen = set()
unique_jsons = []

for person in all_jsons:
    person_key = json.dumps(person, sort_keys=True)

    if person_key not in seen:
        seen.add(person_key)
        unique_jsons.append(person)

print('After:', len(unique_jsons))
print('Duplicates removed:', len(all_jsons) - len(unique_jsons))


# In[113]:


all_jsons = unique_jsons


# In[114]:


df_list = []
df = pd.DataFrame(all_jsons)


# In[115]:


df


# In[116]:


# Drop columns with multiple values in one cell
columns_to_drop = ['tech_self_score', 'strengths', 'weaknesses']
df = df.drop(columns=columns_to_drop)
df


# In[117]:


# Change yes and no to booleans
df['self_development'] = df['self_development'].map({
    'Yes': True,
    'No': False
})

df['geo_flex'] = df['geo_flex'].map({
    'Yes': True,
    'No': False
})

df['financial_support_self'] = df['financial_support_self'].map({
    'Yes': True,
    'No': False
})


# In[118]:


df


# In[119]:


# Change result column to pass with a Boolean value 
df = df.rename(columns={'result': 'pass'})


# In[120]:


df['pass'] = df['pass'].map({
    'Pass': True,
    'Fail': False
})
df


# In[121]:


df.head()


# In[122]:


df.info()


# In[123]:


df.duplicated().sum()


# In[124]:


# Clean the formatting of dates
df['date'] = df['date'].str.replace('//', '/', regex=False)


# In[125]:


# Convert date column to datetime
df['date'] = pd.to_datetime(df['date'], dayfirst=True)
df.info()


# In[126]:


# Check if anyone has missing tech self scores
for person in all_jsons:
    if 'tech_self_score' not in person:
        print(person['name'])


# In[127]:


tech_list = []
for person in all_jsons:
    name = person['name']
    date = person['date']
    
    if 'tech_self_score' not in person:
        continue
        
    for skill, self_score in person['tech_self_score'].items():
        tech_list.append([name, date, skill, self_score])

tech_df = pd.DataFrame(tech_list, columns=['name', 'date', 'skill', 'self_score'])


# In[128]:


tech_df


# In[129]:


# Clean the formatting of dates
tech_df['date'] = tech_df['date'].str.replace('//', '/', regex=False)


# In[130]:


# Convert date column to datetime
tech_df['date'] = pd.to_datetime(tech_df['date'], dayfirst=True)
tech_df.info()


# In[131]:


tech_df


# In[132]:


strength_list = []
for person in all_jsons:
    name = person['name']
    date = person['date']
    
    if 'strengths' not in person:
        continue
        
    for strength in person['strengths']:
        strength_list.append([name, date, strength])


# In[133]:


strength_df = pd.DataFrame(strength_list,columns=['name', 'date', 'strength'])
strength_df


# In[134]:


# Clean the formatting of dates
strength_df['date'] = strength_df['date'].str.replace('//', '/', regex=False)


# In[135]:


# Convert date column to datetime
strength_df['date'] = pd.to_datetime(strength_df['date'], dayfirst=True)
strength_df.info()


# In[136]:


weakness_list = []
for person in all_jsons:
    name = person['name']
    date = person['date']
    
    if 'weaknesses' not in person:
        continue
        
    for weakness in person['weaknesses']:
        weakness_list.append([name, date, weakness])


# In[137]:


weakness_df = pd.DataFrame(weakness_list,columns=['name', 'date', 'weakness'])
weakness_df


# In[138]:


# Clean the formatting of dates
weakness_df['date'] = weakness_df['date'].str.replace('//', '/', regex=False)


# In[139]:


# Convert date column to datetime
weakness_df['date'] = pd.to_datetime(weakness_df['date'], dayfirst=True)
weakness_df.info()


# In[140]:


tech_df.duplicated().sum()


# In[141]:


strength_df.duplicated().sum()


# In[142]:


weakness_df.duplicated().sum()


# In[143]:


sparta_df = pd.read_csv('sparta_day_clean.csv')
sparta_df


# In[144]:


sparta_df.duplicated().sum()


# In[145]:


names_a = set(df["name"].dropna())
names_b = set(sparta_df["name"].dropna())


# In[146]:


print("Names in both:", len(names_a & names_b))
print("Only in df1:", len(names_a - names_b))
print("Only in df2:", len(names_b - names_a))


# In[147]:


sparta_df.info()


# In[148]:


sparta_df['date'] = pd.to_datetime(sparta_df['date'])


# In[149]:


sparta_df.info()


# In[150]:


sparta_df["name"] = sparta_df["name"].replace({
    "L'Urette Daveley": "Lurette Daveley"
})


# In[151]:


df["name"] = df["name"].replace({
    "L;Urette Daveley": "Lurette Daveley"
})


# In[152]:


joined_df = df.merge(
    sparta_df,
    on='name',
    how='outer'
)


# In[153]:


joined_df


# In[154]:


joined_df.duplicated().sum()


# In[155]:


joined_df.isna().sum()


# In[156]:


joined_df


# In[157]:


joined_df[joined_df['date_y'].isna()==True]


# In[158]:


joined_df["date_y"] = joined_df["date_y"].fillna(joined_df["date_x"])


# In[159]:


joined_df[joined_df['date_y'].isna()==True]


# In[160]:


columns_to_drop = ['date_x', 'name_key', 'source_file']
joined_df = joined_df.drop(columns=columns_to_drop)
joined_df


# In[161]:


joined_df = joined_df.rename(columns={'date_y': 'date'})
joined_df


# In[162]:


stream_map = {
    "Data": 1,
    "Business": 2,
    "Engineering": 3
}

joined_df["course_interest"] = joined_df["course_interest"].map(stream_map)
joined_df


# In[163]:


joined_df["course_interest"] = joined_df["course_interest"].astype("Int64")
joined_df


# In[164]:


names_to_check = [
    "Julia Llorens",
    "Orly Lorens",
    "Megan Hallihan",
    "Maxy Halligan",
    "Guido Lassells",
    "Dodie Lassells",
    "Derby Mcglashan",
    "Debby McGlynn",
    "Mozelle Grinnov",
    "Chandler Grinov"
]

joined_df[joined_df["name"].isin(names_to_check)]


# In[165]:


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

for current_df in [
    joined_df,
    weakness_df,
    strength_df,
    tech_df
]:
    current_df["name"] = current_df["name"].replace(name_corrections)


# In[166]:


joined_df["name"] = joined_df["name"].replace({
    "Keen Bentham3": "Keen Bentham",
    "L;Urette Daveley": "Lurette Daveley"
})


# In[167]:


connection, cursor = connect_to_mysql()

cursor.execute("""
    SELECT candidate_id, name
    FROM candidates
""")

candidate_lookup = pd.DataFrame(
    cursor.fetchall(),
    columns=["candidate_id", "name"]
)

cursor.close()
connection.close()

def add_candidate_ids(current_df, candidate_lookup):
    return current_df.merge(
        candidate_lookup,
        on="name",
        how="left",
        validate="many_to_one"
    )


# In[168]:


candidate_lookup


# In[169]:


joined_df = joined_df.merge(
    candidate_lookup,
    on="name",
    how="left"
)


# In[170]:


joined_df


# In[171]:


joined_df[joined_df["name"]=='Lurette Daveley']


# In[172]:


joined_df[joined_df["candidate_id"].isna()]


# In[173]:


name_corrections = {
    "Keen Bentham3": "Keen Bentham",
    "L'Urette Daveley": "Lurette Daveley",
    "L;Urette Daveley": "Lurette Daveley",
    "L'Urette Davely": "Lurette Daveley",
    "L;Urette Davely": "Lurette Daveley"
}

for current_df in [
    df,
    sparta_df,
    weakness_df,
    strength_df,
    tech_df
]:
    current_df["name"] = current_df["name"].replace(name_corrections)


# In[174]:


def add_candidate_ids(current_df, candidate_lookup):
    ambiguous_names = [
        "Shurlocke Cringle",
        "Nicolette Bonehill"
    ]

    unique_lookup = candidate_lookup[
        ~candidate_lookup["name"].isin(ambiguous_names)
    ]

    return current_df.merge(
        unique_lookup,
        on="name",
        how="left",
        validate="many_to_one"
    )


# In[175]:


joined_df = add_candidate_ids(joined_df, candidate_lookup)
weakness_df = add_candidate_ids(weakness_df, candidate_lookup)
strength_df = add_candidate_ids(strength_df, candidate_lookup)
tech_df = add_candidate_ids(tech_df, candidate_lookup)


# In[176]:


duplicate_names = candidate_lookup[
    candidate_lookup["name"].duplicated(keep=False)
].sort_values("name")

print(duplicate_names)


# In[177]:


names_to_check = [
    "Shurlocke Cringle",
    "Nicolette Bonehill"
]

dataframes = {
    "df": df,
    "sparta_df": sparta_df,
    "joined_df": joined_df,
    "weakness_df": weakness_df,
    "strength_df": strength_df,
    "tech_df": tech_df
}

for df_name, current_df in dataframes.items():
    matches = current_df[
        current_df["name"].isin(names_to_check)
    ]

    if not matches.empty:
        print(f"\n--- {df_name} ---")
        print(matches)


# In[178]:


for current_df in [
    weakness_df,
    strength_df,
    tech_df
]:
    current_df.loc[
        current_df["name"] == "Nicolette Bonehill",
        "candidate_id"
    ] = 1170

    current_df.loc[
        current_df["name"] == "Shurlocke Cringle",
        "candidate_id"
    ] = 3137


# In[179]:


print(weakness_df["candidate_id"].isna().sum())
print(strength_df["candidate_id"].isna().sum())
print(tech_df["candidate_id"].isna().sum())


# In[180]:


for df_name, current_df in {
    "weakness_df": weakness_df,
    "strength_df": strength_df,
    "tech_df": tech_df
}.items():

    missing = current_df[
        current_df["candidate_id"].isna()
    ]

    print(f"\n--- {df_name} ---")
    print(missing["name"].value_counts())


# In[181]:


weakness_df[weakness_df['name']=='Shurlocke Cringle']


# In[182]:


strength_df[strength_df['name']=='Shurlocke Cringle']


# In[183]:


tech_df[tech_df['name']=='Shurlocke Cringle']


# In[184]:


weakness_df[weakness_df['name']=='Nicolette Bonehill']


# In[185]:


joined_df[joined_df['name']=='Nicolette Bonehill']


# In[186]:


joined_df[joined_df['name']=='Shurlocke Cringle']


# In[187]:


keep_rows = (
    # Keep everyone who isn't one of the two duplicate-name cases
    ~joined_df["name"].isin([
        "Nicolette Bonehill",
        "Shurlocke Cringle"
    ])

    # Nicolette: February = 1170
    | (
        (joined_df["name"] == "Nicolette Bonehill")
        & (joined_df["date"] == "2019-02-05")
        & (joined_df["candidate_id_x"] == 1170)
    )

    # Nicolette: November = 3522
    | (
        (joined_df["name"] == "Nicolette Bonehill")
        & (joined_df["date"] == "2019-11-19")
        & (joined_df["candidate_id_x"] == 3522)
    )

    # Shurlocke: January = 1498
    | (
        (joined_df["name"] == "Shurlocke Cringle")
        & (joined_df["date"] == "2019-01-31")
        & (joined_df["candidate_id_x"] == 1498)
    )

    # Shurlocke: May = 3137
    | (
        (joined_df["name"] == "Shurlocke Cringle")
        & (joined_df["date"] == "2019-05-21")
        & (joined_df["candidate_id_x"] == 3137)
    )
)

joined_df = joined_df[keep_rows].copy()


# In[188]:


joined_df


# In[189]:

def populate_lookup_tables():
    connection, cursor = connect_to_mysql()

    try:
        # Tech skills
        tech_skills = [
            "C#", "C++", "Java", "JavaScript", "PHP",
            "Python", "R", "Ruby", "SPSS"
        ]

        cursor.executemany(
            "INSERT INTO tech_skills (skill_name) VALUES (%s)",
            [(skill,) for skill in tech_skills]
        )

        # Strengths
        strengths = [
            "Altruism",
            "Ambitious",
            "Charisma",
            "Collaboration",
            "Competitive",
            "Composure",
            "Consistent",
            "Courteous",
            "Creative",
            "Critical Thinking",
            "Curious",
            "Determined",
            "Efficient",
            "Empathy",
            "Independent",
            "Innovative",
            "Listening",
            "Organisation",
            "Passionate",
            "Patient",
            "Perfectionism",
            "Problem Solving",
            "Rational",
            "Reliable",
            "Versatile"
        ]

        cursor.executemany(
            "INSERT INTO strengths (strength_name) VALUES (%s)",
            [(strength,) for strength in strengths]
        )

        # Weaknesses
        weaknesses = [
            "Anxious",
            "Chaotic",
            "Chatty",
            "Competitive",
            "Controlling",
            "Conventional",
            "Critical",
            "Distracted",
            "Immature",
            "Impatient",
            "Impulsive",
            "Indecisive",
            "Indifferent",
            "Intolerant",
            "Introverted",
            "Overbearing",
            "Passive",
            "Perfectionist",
            "Procrastination",
            "Selfish",
            "Sensitive",
            "Slow",
            "Stubborn",
            "Undisciplined"
        ]

        cursor.executemany(
            "INSERT INTO weaknesses (weakness_name) VALUES (%s)",
            [(weakness,) for weakness in weaknesses]
        )

        connection.commit()
        print("Lookup tables populated successfully.")

    except Exception as e:
        connection.rollback()
        print("Failed. Changes rolled back.")
        raise e

    finally:
        cursor.close()
        connection.close()

populate_lookup_tables()

connection, cursor = connect_to_mysql()

cursor.execute("SELECT skill_id, skill_name FROM tech_skills")
skill_lookup = pd.DataFrame(
    cursor.fetchall(),
    columns=["skill_id", "skill_name"]
)

cursor.execute("SELECT strength_id, strength_name FROM strengths")
strength_lookup = pd.DataFrame(
    cursor.fetchall(),
    columns=["strength_id", "strength_name"]
)

cursor.execute("SELECT weakness_id, weakness_name FROM weaknesses")
weakness_lookup = pd.DataFrame(
    cursor.fetchall(),
    columns=["weakness_id", "weakness_name"]
)

cursor.close()
connection.close()


# In[190]:


tech_df = tech_df.merge(
    skill_lookup,
    left_on="skill",
    right_on="skill_name",
    how="left"
)
tech_df


# In[191]:


strength_df = strength_df.merge(
    strength_lookup,
    left_on="strength",
    right_on="strength_name",
    how="left"
)
strength_df


# In[192]:


weakness_df = weakness_df.merge(
    weakness_lookup,
    left_on="weakness",
    right_on="weakness_name",
    how="left"
)
weakness_df


# In[193]:


ambiguous_names = [
    "Nicolette Bonehill",
    "Shurlocke Cringle"
]

unique_candidate_lookup = candidate_lookup[
    ~candidate_lookup["name"].isin(ambiguous_names)
]

for current_df in [tech_df, strength_df, weakness_df]:
    # can't reassign current_df itself back to the originals here
    pass


# In[194]:


print(strength_df.isna().sum())


# In[195]:


print(weakness_df.isna().sum())


# In[196]:


print(tech_df.isna().sum())


# In[197]:


candidate_strengths_df = strength_df[
    ["candidate_id", "strength_id"]
].copy()

candidate_weaknesses_df = weakness_df[
    ["candidate_id", "weakness_id"]
].copy()

candidate_tech_scores_df = tech_df[
    ["candidate_id", "skill_id", "self_score"]
].copy()


# In[198]:


candidate_strengths_df


# In[199]:


candidate_weaknesses_df


# In[200]:


joined_df[joined_df['name']=='Keen Bentham']


# In[201]:


keen_mask = joined_df["name"] == "Keen Bentham"

keen_rows = joined_df.loc[keen_mask]

keen_fixed = keen_rows.apply(
    lambda col: col.dropna().iloc[0]
    if not col.dropna().empty
    else pd.NA
)


# In[202]:


keen_fixed["date"] = pd.Timestamp("2019-06-19")


# In[203]:


joined_df = joined_df.loc[~keen_mask]

joined_df = pd.concat(
    [joined_df, keen_fixed.to_frame().T],
    ignore_index=True
)


# In[204]:


joined_df[joined_df['name']=='Keen Bentham']


# In[205]:


joined_df.isna().sum()


# In[207]:


joined_df = joined_df.drop(columns=["candidate_id_y"])
joined_df = joined_df.rename(
    columns={"candidate_id_x": "candidate_id"}
)


# In[209]:


candidate_assessments_df = joined_df[
    [
        "candidate_id",
        "pass",
        "date",
        "location",
        "psychometric_score",
        "presentation_score",
        "self_development",
        "geo_flex",
        "financial_support_self",
        "course_interest"
    ]
].copy()


# In[210]:


candidate_assessments_df = candidate_assessments_df.rename(columns={
    "date": "assessment_date",
    "location": "assessment_location",
    "course_interest": "stream_interest_id"
})


# In[220]:


def to_mysql_value(value):
    # Missing values -> SQL NULL
    if pd.isna(value):
        return None

    # Pandas Timestamp -> normal Python datetime
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    # NumPy types -> normal Python types
    if isinstance(value, np.generic):
        return value.item()

    return value


def load_candidate_tables(
    candidate_assessments_df,
    candidate_strengths_df,
    candidate_weaknesses_df,
    candidate_tech_scores_df
):
    connection, cursor = connect_to_mysql()

    try:
        # ---------------------------------
        # Candidate assessments
        # ---------------------------------

        assessment_sql = """
        INSERT INTO candidate_assessments (
            candidate_id,
            pass,
            assessment_date,
            assessment_location,
            psychometric_score,
            presentation_score,
            self_development,
            geo_flex,
            financial_support_self,
            stream_interest_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        assessments = candidate_assessments_df.rename(
            columns={"pass": "pass_result"}
        )

        assessment_data = [
            (
                to_mysql_value(row.candidate_id),
                to_mysql_value(row.pass_result),
                to_mysql_value(row.assessment_date),
                to_mysql_value(row.assessment_location),
                to_mysql_value(row.psychometric_score),
                to_mysql_value(row.presentation_score),
                to_mysql_value(row.self_development),
                to_mysql_value(row.geo_flex),
                to_mysql_value(row.financial_support_self),
                to_mysql_value(row.stream_interest_id)
            )
            for row in assessments.itertuples(index=False)
        ]

        cursor.executemany(
            assessment_sql,
            assessment_data
        )

        print("Candidate assessments inserted.")


        # ---------------------------------
        # Candidate strengths
        # ---------------------------------

        strength_sql = """
        INSERT INTO candidate_strengths (
            candidate_id,
            strength_id
        )
        VALUES (%s, %s)
        """

        strength_data = [
            (
                to_mysql_value(row.candidate_id),
                to_mysql_value(row.strength_id)
            )
            for row in candidate_strengths_df.itertuples(index=False)
        ]

        cursor.executemany(
            strength_sql,
            strength_data
        )

        print("Candidate strengths inserted.")


        # ---------------------------------
        # Candidate weaknesses
        # ---------------------------------

        weakness_sql = """
        INSERT INTO candidate_weaknesses (
            candidate_id,
            weakness_id
        )
        VALUES (%s, %s)
        """

        weakness_data = [
            (
                to_mysql_value(row.candidate_id),
                to_mysql_value(row.weakness_id)
            )
            for row in candidate_weaknesses_df.itertuples(index=False)
        ]

        cursor.executemany(
            weakness_sql,
            weakness_data
        )

        print("Candidate weaknesses inserted.")


        # ---------------------------------
        # Candidate tech scores
        # ---------------------------------

        tech_sql = """
        INSERT INTO candidate_tech_self_scores (
            candidate_id,
            skill_id,
            self_score
        )
        VALUES (%s, %s, %s)
        """

        tech_data = [
            (
                to_mysql_value(row.candidate_id),
                to_mysql_value(row.skill_id),
                to_mysql_value(row.self_score)
            )
            for row in candidate_tech_scores_df.itertuples(index=False)
        ]

        cursor.executemany(
            tech_sql,
            tech_data
        )

        print("Candidate tech scores inserted.")


        # Commit everything together
        connection.commit()

        print("\nAll four tables loaded successfully.")


    except Exception as error:
        connection.rollback()

        print("Load failed. Changes rolled back.")
        print(error)

        raise


    finally:
        cursor.close()
        connection.close()


# In[222]:


def candidate_assessments_main():
    load_candidate_tables(
    candidate_assessments_df,
    candidate_strengths_df,
    candidate_weaknesses_df,
    candidate_tech_scores_df
    )


# In[223]:


if __name__ == "__main__":
    candidate_assessments_main()


# In[ ]:




