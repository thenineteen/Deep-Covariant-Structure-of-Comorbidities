import pandas as pd
import numpy as np

def rename_df_columns(df) -> pd.DataFrame:    
    """Tidying raw df of ICD-10 codes. Replace column headings with ints 0-11"""
    
    df = df.drop('Unnamed: 0', 1)
    column_names_conversion = {'primarydiagnosiscode1': 0}
    for i in range(2, 13):
        name = 'diagnosiscode'+str(i)
        column_names_conversion[name] = i-1
    df = df.rename(columns=column_names_conversion).set_index('patient_id')
    return df

def merge_duplicate_patients(df) -> pd.DataFrame:
    """
        Takes df of patient codes (rows) and each patient's ICD codes and merges based on duplicate patient codes
    """
    duplicateIndex = df.index.duplicated(keep=False)
    duplicatedDf = df[duplicateIndex]
    notDuplicatedDf = df[~duplicateIndex]
    duplicatedIds = set(duplicatedDf.index)
    
    duplicatedPatientDicts = []
    for singleId in duplicatedIds:
        codes = set(duplicatedDf.loc[singleId].values.flatten())-set([np.nan])
        patientDict = {'patient_id': singleId}
        patientDict.update(enumerate(codes))
        duplicatedPatientDicts.append(patientDict)
        
    mergedDuplicatePatientDf = pd.DataFrame(duplicatedPatientDicts).set_index('patient_id')
    return pd.concat([notDuplicatedDf, mergedDuplicatePatientDf])