import pandas as pd 
import os, fnmatch
import sys

bts_df = pd.DataFrame()
listOfFolders= os.listdir('./raw_data')
print(listOfFolders)
pattern = "*.csv"
# Check every folder in the list of folders
for folder in listOfFolders:
    if not folder.startswith("."): 
        listOfFiles = os.listdir('./raw_data/{}'.format(folder))

        # Check everyfile in that folder
        for files in listOfFiles:
            try:
                if fnmatch.fnmatch(files, pattern):
                    current_fn = "./raw_data/{}/{}".format(folder, files)
                    cur_df = pd.read_csv(current_fn)
                    bts_df = bts_df.append(cur_df)
                    print("processing: {}".format(current_fn))
                    bts_df = bts_df.dropna(subset=['reading_time'])
                    bts_df["unix_timestamp"] = pd.to_datetime(bts_df["reading_time"]).astype(int)
                    mean_time = bts_df["unix_timestamp"].mean()
                    min_time = bts_df["unix_timestamp"].min()
                    bts_df["norm_time"] = (bts_df["unix_timestamp"]-mean_time)/(3600*1000000000)
                    bts_df = bts_df.sort_values(by=['norm_time'])
                    bts_df.drop(["reading_time"], axis='columns', inplace=True)

                    bts_df_grouped = bts_df.groupby(["station_id","parameter_id"])
                    for key,item in bts_df_grouped:
                        if key[1] == 122:
                            sub_data = bts_df_grouped.get_group(key)
                            mean_val = sub_data['value'].mean()
                            sub_data['norm_value'] = sub_data['value']-mean_val
                            max_val = sub_data['norm_value'].max()
                            sub_data['norm_value'] = sub_data['norm_value']/max_val
                            sub_data.sort_values(by=['norm_time']).to_csv("./grouped_data/{}_{}_{}_.csv".format(folder, key[0],key[1]), index=False)
                            print("Finish: {}".format(key))
            except Exception as e:
                print(e)
