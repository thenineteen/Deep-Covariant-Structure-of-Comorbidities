import numpy as np
import pandas as pd
import itertools

class ICD10Converter:
    def __init__(self, df, look_up_table):
        self.plain_df = df
        self.look_up_table = look_up_table
        self.convert(df)
    
    def make_keep_mask(self, df):
        """ KEEP - create mask of values which we do not want to prune at the end """
        look_up_table = self.look_up_table
        keep_code_df = look_up_table[look_up_table['Action'] == 'keep']
        keep_input_codes = keep_code_df['input']
        keep_input_mask = df.isin(keep_input_codes.values)
#         self._keep_input_mask = keep_input_mask
        return keep_input_mask
    
    def apply_parent(self, df):
        parent_df = df
        look_up_table = self.look_up_table
        
        look_up_table_short = look_up_table[look_up_table['Action'] == 'parent']
        input_codes_short = look_up_table_short['input']
        
        #Expand to include possible translations - eg for A04, we expand this to A040, A041, A042...
        input_codes_expanded_nested = [[code+str(i) for i in range(10)] for code in input_codes_short]
        input_codes_expanded_flat = list(itertools.chain.from_iterable(input_codes_expanded_nested))
        
        for code, expanded_code in zip(input_codes_short, input_codes_expanded_nested):
            code_mask = parent_df.isin(expanded_code)
            parent_df[code_mask] = code

        parent_input_mask = parent_df.isin(input_codes_expanded_flat)
        
        return {'df': parent_df, 'mask': parent_input_mask}
    
    def apply_lookup_prune(self, df):
        pruned_df = df
        look_up_table = self.look_up_table

        look_up_table_prune = look_up_table[look_up_table['Action'] == 'prune']
        prune_input_codes = look_up_table_prune['input']
        code_masks = []
        for code in prune_input_codes:
            code_mask = pruned_df.apply(lambda x: x.str.startswith(code[:3]))
            code_mask = code_mask.fillna(False)
            # code_mask_minus_keep = np.logical_and(code_mask, ~keep_input_mask)
            # Codes which are marked to keep are excluded from being changed
            # No longer needed - check done before to check no clashes - keep shouldn't be combined with
            # any other actions
            code_masks.append(code_mask)
            pruned_df[code_mask] = code[:3]
        pruned_mask = np.logical_or.reduce(code_masks)

        return {'df': pruned_df, 'mask': pruned_mask}

    def apply_merge(self, df):
        merged_df = df
        look_up_table = self.look_up_table
        look_up_table_merge = look_up_table[look_up_table['Action'] == 'merge']
        input_codes = look_up_table_merge['input']
        output_codes = look_up_table_merge['output']
        merged_df = merged_df.replace(list(input_codes), list(output_codes))
        #TODO - check if needs to be removed
        # try:
        #     merged_df = merged_df.set_index('patient_id')
        # except KeyError:
        #     pass # May have already been set

        merge_mask = (~(merged_df.fillna(1) == df.fillna(1)))
        return {'df': merged_df, 'mask': merge_mask}

    def make_remains_keep_mask(self, df):
        rk_df = df
        look_up_table = self.look_up_table
        look_up_table_rk = look_up_table[look_up_table['Action'] == 'remains keep']
        rk_input_codes = look_up_table_rk['input']
        rk_input_mask = rk_df.isin(rk_input_codes.values)
        return rk_input_mask
    
    def make_prune_mask(self, masks_to_combine):
        # Prune everyting else
        no_prune_mask_np = np.logical_or.reduce(masks_to_combine)
        no_prune_mask = pd.DataFrame(no_prune_mask_np, columns = self.plain_df.columns, index = self.plain_df.index)
        to_prune_mask = ~no_prune_mask
        return to_prune_mask
    
    def truncate_if_not_nan(self, value):
        try:
            return value[:3]
        except TypeError:
            if np.isnan(value):
                return None
            else:
                raise TypeError('value given must either be slicable with [:X], or nan')

    def apply_global_prune(self, df, to_prune_mask):
        df[to_prune_mask] = df[to_prune_mask].applymap(self.truncate_if_not_nan)
        return df
    
    def convert(self, df):
        masks = {}
        df_stages = {}

        masks['keep'] = self.make_keep_mask(df)

        parent_dict = self.apply_parent(df)
        masks['parent'] = parent_dict['mask']
        df_stages['parent'] = parent_dict['df']

        lookup_prune_dict = self.apply_lookup_prune(parent_dict['df'])
        masks['lookup_prune'] = lookup_prune_dict['mask']
        df_stages['lookup_prune'] = lookup_prune_dict['df']

        merge_dict = self.apply_merge(lookup_prune_dict['df'])
        masks['merge'] = merge_dict['mask']
        df_stages['merge'] = merge_dict['df']

        masks['remains_keep'] =  self.make_remains_keep_mask(merge_dict['df'])

        to_prune_mask = self.make_prune_mask(list(masks.values()))
        converted_df = self.apply_global_prune(merge_dict['df'], to_prune_mask)
        df_stages['converted'] = converted_df
        
        print(1)
        self.converted_df = converted_df
        self.masks = masks
        self.df_stages = df_stages

        # return converted_df

if __name__ == "__main__":
    first_path = '/Volumes/Encrypted/Deep-Covariant-Structure-of-Comorbidities/'

    pre_df = pd.read_csv(first_path+'Preprocessing/Data/patientsIn_Anon_diagnoses_only_duplicates_merged.csv', dtype='str') 

    look_up_table_raw = pd.read_csv(first_path+'Preprocessing/ICD10/ICD10 Preprocessing Exceptions.csv', engine='python')

    def tidy_look_up_df(df):
        df = df.dropna(axis=0, how='all').reset_index()
        rename_column_map = {"ICD10 Codes":"input",
                            "If required, give new category name": "output",
                            "further merging is possible: other and unspecified super categories": "super"}
        df = df.rename(columns=rename_column_map)
        df['output'] = df['output'].str.replace('.','').str.strip()
        df['input'] = df['input'].str.replace('.','').str.strip()
        
        try:
            df = df.drop(['index'], axis=1)
        except KeyError:
            pass #May have already been dropped
        return df

    look_up_table = tidy_look_up_df(look_up_table_raw)

    converter = ICD10Converter(pre_df, look_up_table)
    converter.convert(pre_df)