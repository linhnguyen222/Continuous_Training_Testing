import pandas as pd 
import os, fnmatch


bts_df = pd.DataFrame()

listOfFiles = os.listdir('./raw_data')
pattern = "*.csv"
for files in listOfFiles:
    if fnmatch.fnmatch(files, pattern):
        cur_df = pd.read_csv("./raw_data/{}".format(files))
        bts_df = bts_df.append(cur_df)
        print(bts_df.shape[0])
bts_df["unix_timestamp"] = pd.to_datetime(bts_df["reading_time"]).astype(int)
bts_df_grouped = bts_df.groupby(["station_id","parameter_id"])


