import pandas as pd
from executive_orders import get_executive_orders_list, get_executive_orders_by_docket
from lawsuits import get_dockets, get_courts
import pandas as pd

def get_lawsuits_by_executive_order():
    dockets = get_dockets()
    courts = get_courts()

    # Join dockets with courts
    # court_id in dockets = id in courts
    # More info on .concat() vs .merge(): https://stackoverflow.com/questions/38256104/differences-between-merge-and-concat-in-pandas
    # .concat() is recommended for joining homogenous dfs, while merge() is good for joining complementary dfs
    docket_combined_data = dockets.merge(courts, left_on='court_id', right_on='id', suffixes=('_docket', '_court'))

    # Join with imported docket_to_executive_order csv
    # I went thru the Complaint Document for each docket (found at absolute url in combined_data df)
    # and wrote down Executive order references
    # Eventually, I'd like to automate this process
    eo_by_docket = get_executive_orders_by_docket()
    info_by_eo = get_executive_orders_list()
    eo_combined_data = eo_by_docket.merge(info_by_eo, left_on='related_executive_orders', right_on='title').reset_index(
        drop=True)

    # Check that EO names match between eo_by_docket and info_by_eo
    # count of each docket in eo_by_docket should match count in eo_combined_data. this means no rows were dropped in the above merge
    count_by_docket_df_1 = eo_by_docket['docket_id'].value_counts().to_frame()
    count_by_docket_df_2 = eo_combined_data['docket_id'].value_counts().to_frame()

    count_comparison = count_by_docket_df_1.merge(count_by_docket_df_2, on='docket_id')
    count_comparison['diff'] = abs(count_comparison['count_x'] - count_comparison['count_y'])

    all_data = docket_combined_data.merge(eo_combined_data, left_on='id_docket', right_on='docket_id').reset_index(drop=True)

    keep_cols = ['id_docket', 'case_name', 'absolute_url', 'date_filed', 'date_modified', 'court_type', 'court_name',
                 'related_executive_orders', 'document_number', 'html_url', 'publication_date']

    rename_cols = {'id_docket': 'docket_id',
                   'absolute_url': 'case_url',
                   'date_filed': 'date_case_filed',
                   'date_modified': 'date_case_modified',
                   'related_executive_orders': 'executive_order',
                   'document_number': 'executive_order_document_number',
                   'html_url': 'eo_url',
                   'publication_date': 'eo_publication_date'}

    all_data = all_data[keep_cols]
    all_data = all_data.rename(columns=rename_cols)

    executive_orders_with_lawsuits = all_data['executive_order'].unique()
    executive_orders_with_no_lawsuits = info_by_eo[~info_by_eo['title'].isin(executive_orders_with_lawsuits)]['title']

    return {'eos_with_lawsuits': all_data, 'eos_with_no_lawsuits': executive_orders_with_no_lawsuits}


def save_data():
    data = get_lawsuits_by_executive_order()

    with pd.ExcelWriter('../../data/processed/executive_orders_with_and_without_lawsuits.xlsx') as writer:
        data['eos_with_lawsuits'].to_excel(writer, 'eos_with_lawsuits')
        data['eos_with_no_lawsuits'].to_excel(writer, 'eos_with_no_lawsuits')



# TODO: Add latest_status and executive_order_referenced columns to combined_data
# #Downloading docket resources to get (1) latest update/status (info within latest docket entry) and (2) Executive order referenced in initial Complaint document
# Examples of statuses: Appeal
# Using PACER Data API
# https://www.courtlistener.com/help/api/rest/pacer/
# https://judiciallearningcenter.org/state-courts-vs-federal-courts/
# PACER applies to federal courts only (US District Courts, US Court of Appeals, and U.S. Supreme Court)
# State Courts (e.g.) - Missouri Circuit Courts, Missouri Court of Appeals, Missouri Supreme Court

if __name__ == '__main__':
    save_data()