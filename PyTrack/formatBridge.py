# -*- coding: utf-8 -*-

from etDataReader import read_edf, read_idf, read_tobii
from sqlalchemy import create_engine
from datetime import datetime
import pandas as pd
import numpy as np
import json
import os


def getColHeaders():
    """
    """
    return ["Timestamp", "StimulusName", "EventSource", "GazeLeftx", "GazeRightx", "GazeLefty", "GazeRighty", "PupilLeft", "PupilRight", "FixationSeq", "SaccadeSeq", "Blink"]


def eyeLinkToBase(filename, stim_list=None, start='START', stop=None):
    """
    Bridge function that converts ASCII (asc) EyeLink eye tracking data files to the base CSV format that the framework uses.

    Parameters
    ----------
    filename : str 
        Full file name (with path) of the data file
    
    stim_list : list (str)
        Name of stimuli as a list of strings. If there are n trials/events found in the data, the length of stim_list should be n containing the names of stimuli for each trial/event.

    start : str
        Marker for start of event in the .asc file. Default value is 'START'.
    
    stop : str
        Marker for end of event in the .asc file. Default value is None. If None, new event/trial will start when start trigger is detected again.

    Returns
    -------
    df : pandas DataFrame  
        Pandas dataframe of the data in the framework friendly base csv format 
    """

    col_headers = getColHeaders()

    print("Converting EyeLink ASC file to Pandas CSV: ", filename.split("/")[-1])

    data = read_edf(filename, start=start, stop=stop, missing=-1)
    df = pd.DataFrame(columns=col_headers)

    i = 0
    for d in data:
        temp_dict = dict.fromkeys(col_headers)

        temp_dict['Timestamp'] = d['trackertime']

        if stim_list == None:
            temp_dict['StimulusName'] = ['stimulus_' + str(i)] * len(temp_dict['Timestamp'])
        else:
            temp_dict['StimulusName'] = [stim_list[i]] * len(temp_dict['Timestamp'])

        temp_dict['EventSource'] = ['ET'] * len(temp_dict['Timestamp'])
        temp_dict['GazeLeftx'] = d['x_l']
        temp_dict['GazeRightx'] = d['x_r']
        temp_dict['GazeLefty'] = d['y_l']
        temp_dict['GazeRighty'] = d['y_r']
        temp_dict['PupilLeft'] = d['size_l']
        temp_dict['PupilRight'] = d['size_r']
        temp_dict['FixationSeq'] = np.ones(len(temp_dict['Timestamp'])) * -1
        temp_dict['SaccadeSeq'] = np.ones(len(temp_dict['Timestamp'])) * -1
        temp_dict['Blink'] = np.ones(len(temp_dict['Timestamp'])) * -1
        
        cnt = 0
        for e in d['events']['Efix']:
            ind_start = np.where(temp_dict['Timestamp'] == e[0])[0][0]
            ind_end = np.where(temp_dict['Timestamp'] == e[1])[0][0]
            temp_dict['FixationSeq'][ind_start : ind_end + 1] = cnt
            cnt += 1

        cnt = 0
        for e in d['events']['Esac']:
            ind_start = np.where(temp_dict['Timestamp'] == e[0])[0][0]
            ind_end = np.where(temp_dict['Timestamp'] == e[1])[0][0]
            temp_dict['SaccadeSeq'][ind_start : ind_end + 1] = cnt
            cnt += 1
        
        cnt = 0
        for e in d['events']['Eblk']:
            ind_start = np.where(temp_dict['Timestamp'] == e[0])[0][0]
            ind_end = np.where(temp_dict['Timestamp'] == e[1])[0][0]
            temp_dict['Blink'][ind_start : ind_end + 1] = cnt
            cnt += 1
        
        for m in d['events']['msg']:
            if 'Stim Key' in m[1]:
                temp_dict['StimulusName'] = [m[1].strip("\n").split(":")[1].strip(" ")] * len(temp_dict['Timestamp'])
                break

        df = df.append(pd.DataFrame.from_dict(temp_dict, orient='index').transpose(), ignore_index=True, sort=False)
        del(temp_dict)
        
        i += 1

    return df


def smiToBase(filename, stim_list=None, start='START', stop=None):
    """
    Bridge function that converts SMI (text ascii generated from idf) raw eye tracking data files to the base CSV format that the framework uses.

    Parameters
    ----------
    filename : str 
        Full file name (with path) of the data file
    
    stim_list : list (str)
        Name of stimuli as a list of strings. If there are n trials/events found in the data, the length of stim_list should be n containing the names of stimuli for each trial/event.

    start : str
        Marker for start of event in the .asc file. Default value is 'START'.
    
    stop : str
        Marker for end of event in the .asc file. Default value is None. If None, new event/trial will start when start trigger is detected again.

    Returns
    -------
    df : pandas DataFrame  
        Pandas dataframe of the data in the framework friendly base csv format 
    """
    
    col_headers = getColHeaders()
    
    print("Converting SMI IDF file to Pandas CSV: ", filename.split("/")[-1])

    data = read_idf(filename, start=start, stop=stop, missing=-1.0, debug=True)
    print(len(data))
    df = pd.DataFrame(columns=col_headers)

    i = 0
    for d in data:
        temp_dict = dict.fromkeys(col_headers)

        temp_dict['Timestamp'] = d['trackertime']
        
        if stim_list == None:
            temp_dict['StimulusName'] = ['stimulus_' + str(i)] * len(temp_dict['Timestamp'])
        else:
            temp_dict['StimulusName'] = [stim_list[i]] * len(temp_dict['Timestamp'])
        
        temp_dict['EventSource'] = ['ET'] * len(temp_dict['Timestamp'])
        temp_dict['GazeLeftx'] = d['x_l']
        temp_dict['GazeRightx'] = d['x_r']
        temp_dict['GazeLefty'] = d['y_l']
        temp_dict['GazeRighty'] = d['y_r']
        temp_dict['PupilLeft'] = d['size_l']
        temp_dict['PupilRight'] = d['size_r']
        temp_dict['FixationSeq'] = np.ones(len(temp_dict['Timestamp'])) * -1
        temp_dict['SaccadeSeq'] = np.ones(len(temp_dict['Timestamp'])) * -1
        temp_dict['Blink'] = np.ones(len(temp_dict['Timestamp'])) * -1
        
        fix_cnt = 0
        sac_cnt = 0
        prev_end = 0
        for e in d['events']['Efix']:
            ind_start = np.where(temp_dict['Timestamp'] == e[0])[0][0]
            ind_end = np.where(temp_dict['Timestamp'] == e[1])[0][0]
            temp_dict['FixationSeq'][ind_start : ind_end + 1] = fix_cnt
            fix_cnt += 1
            if prev_end != ind_start:
                temp_dict['SaccadeSeq'][prev_end + 1 : ind_start + 1] = sac_cnt
                sac_cnt += 1
            prev_end = ind_end

        cnt = 0
        for e in d['events']['Eblk']:
            ind_start = np.where(temp_dict['Timestamp'] == e[0])[0][0]
            ind_end = np.where(temp_dict['Timestamp'] == e[1])[0][0]
            temp_dict['Blink'][ind_start : ind_end + 1] = cnt
            cnt += 1

        df = df.append(pd.DataFrame.from_dict(temp_dict, orient='index').transpose(), ignore_index=True, sort=False)
        del(temp_dict)

        i += 1

    df.to_csv(filename.split('.')[0] + '.csv') 
    return df
    return


def tobiiToBase(filename, stim_list=None, start='START', stop=None):
    """
    Bridge function that converts Tobii eye tracking data files to the base CSV format that the framework uses.

    Parameters
    ----------
    filename : str 
        Full file name (with path) of the data file
    
    stim_list : list (str)
        Name of stimuli as a list of strings. If there are n trials/events found in the data, the length of stim_list should be n containing the names of stimuli for each trial/event.

    start : str
        Marker for start of event in the .asc file. Default value is 'START'.
    
    stop : str
        Marker for end of event in the .asc file. Default value is None. If None, new event/trial will start when start trigger is detected again.

    Returns
    -------
    df : pandas DataFrame  
        Pandas dataframe of the data in the framework friendly base csv format 
    """


def convertToBase(filename, sensor_type, device, stim_list=None, start='START', stop=None):
    """
    """

    file_type = filename.split('.')[1]

    if sensor_type == 'EyeTracker':
        if device == 'eyelink':
            return eyeLinkToBase(filename, stim_list, start=start, stop=stop)
        
        elif device == 'smi':
            return smiToBase(filename, stim_list, start=start, stop=stop)

        elif device == 'tobii':
            return tobiiToBase(filename, stim_list, start=start, stop=stop)
        
        else:
            print("Sorry " + sensor_type + " data format not supported!\n")
            return
    
    else:
        print("Sorry " + sensor_type + " not supported!\n")


def db_create(source_folder, database_name, dtype_dictionary=None, na_strings=None):
    """
    """
    
    all_files = os.listdir(source_folder) 
    
    newlist = []
    for names in all_files:
        if names.endswith(".csv"):
            newlist.append(names)

    database = "sqlite:///" + database_name + ".db"
    csv_database = create_engine(database)

    for file in newlist:

        print("Creating sql file for: ", file)

        file_name = source_folder + "/" + file

        length = len(file)
        file_name_no_extension = file[:length-4]
        table_name = file_name_no_extension.replace(' ','_') #To ensure table names dont haves spaces

        chunksize = 100000
        i = 0
        j = 1
        for df in pd.read_csv(file_name, chunksize=chunksize, iterator=True,na_values = na_strings, dtype=dtype_dictionary):
            
            #SQL columns ideally should not have ' ', '/', '(', ')'

            df = df.rename(columns={c: c.replace(' ', '_') for c in df.columns})
            df = df.rename(columns={c: c.replace('/', '') for c in df.columns})
            df = df.rename(columns={c: c.replace('(', '') for c in df.columns})
            df = df.rename(columns={c: c.replace(')', '') for c in df.columns})

            df.index += j
            i+=1
            df.to_sql(table_name, csv_database, if_exists='append',index = True, index_label = "Index")
            j = df.index[-1] + 1


def generateCompatibleFormat(exp_info, device, data_path, stim_list_mode="NA", start='START', stop=None):
    """
    """
    
    if os.path.isdir(data_path):
        
        if not os.path.isdir(data_path + "/csv_files/"):
            os.makedirs(data_path + "/csv_files/")

        stim = None

        if stim_list_mode == "common":
            stim = np.loadtxt(data_path + "/" + "stim_file.txt", dtype=str)

        subjects = {"Subjects":{"Group1":[]}}

        for f in os.listdir(data_path):
            if os.path.isdir(data_path + "/" + f):
                continue
            
            print("Converting to base csv formate: ", f)

            if stim_list_mode == "diff":
                stim = np.loadtxt(data_path + "/stim/" + f.split(".")[0] + ".txt", dtype=str)
            
            df = convertToBase(data_path + "/" + f, sensor_type='EyeTracker', device=device, stim_list=stim, start=start, stop=stop)
            df.to_csv(data_path + "/csv_files/" + f.split(".")[0] + ".csv")
            subjects["Subjects"]["Group1"].append(f.split(".")[0])

        if stim_list_mode == "NA":
            stimuli = {"Stimuli":{"Type1":[]}}
            for s in np.unique(df["StimulusName"]):
                stimuli["Stimuli"]["Type1"].append(s)

            with open(exp_info, 'r') as json_f:
                json_dict = json.load(json_f)

            json_dict.update(subjects)
            json_dict.update(stimuli)

            with open(exp_info, 'w') as json_f:
                json.dump(json_dict, json_f, indent=4)

        source_folder = data_path + "/csv_files/"

        with open(exp_info, "r") as json_f:
            json_data = json.load(json_f)

        db_create(source_folder, json_data["Experiment_name"])

    else:

        print("Converting to base csv formate: ", data_path.split("/")[-1])

        stim = None
        if stim_list_mode != "NA":
            stim = np.loadtxt("stim_file.txt", dtype=str)
        
        df = convertToBase(data_path, sensor_type='EyeTracker', device=device, stim_list=stim, start=start, stop=stop)
        df.to_csv(data_path.split(".")[0] + ".csv")

# generateCompatibleFormat("test_formats.json", device='smi', data_path="/home/upamanyu/Documents/NTU_Creton/Data/EyeTracking/smi_eyetracker_freeviewing.txt", start="103", stop="203")