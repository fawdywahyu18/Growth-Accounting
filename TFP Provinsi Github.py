import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm
# from datetime import datetime

# Functions to generate capital stock
# Pendekatan menggunakan saving rate
def kapital_stok(input_file, saving_rate, depreciation_rate):
    # input file : dataframe. Input adalah dataframe yang berisi pdrb dan pmtb
    # saving rate: float dengan range 0-1
    # depreciation rate: float dengan range 0-1
    
    pmtb = input_file['PMTB']
    pdrb = input_file['PDRB']
    
    lag_pdrb = input_file['PDRB'].shift(1)
    mean_pdrb_growth = np.mean((pdrb - lag_pdrb)/lag_pdrb)
    
    delta_k = saving_rate*pdrb - depreciation_rate*pmtb
    kapital = pmtb
    for i in range(len(kapital)):
        if i==0:
            kapital[i] = pmtb[i]/(mean_pdrb_growth + depreciation_rate)
            continue
        kapital[i] = delta_k[i] + kapital[i-1]
    
    return kapital

# Pendekatan menggunakan Perpetual Inventory
def kapital_pim(input_file, depreciation_rate):
    # input file : dataframe. Input adalah dataframe yang berisi pdrb dan pmtb
    # depreciation rate: float dengan range 0-1
    
    pmtb = input_file['PMTB']
    pdrb = input_file['PDRB']
    
    lag_pdrb = input_file['PDRB'].shift(1)
    mean_pdrb_growth = np.mean((pdrb - lag_pdrb)/lag_pdrb)
    
    kapital = pmtb
    for i in range(len(kapital)):
        if i==0:
            kapital[i] = pmtb[i]/(mean_pdrb_growth + depreciation_rate)
            continue
        kapital[i] = kapital[i] = (1-depreciation_rate)*kapital[i-1] + pmtb[i]
    
    return kapital

# Estimate the share of kapital, labor and tech
# Create the variables
# N adalah populasi
# L adalah jumlah orang bekerja

def build_variabel(kapital_var):
    gdp_per_cap = np.log(df_input['PDRB']/df_input['Populasi'])
    capital_per_gdp = np.log(kapital_var/df_input['PDRB'])
    rasio_wp_cap = df_input['Jumlah.Orang.Bekerja']/df_input['Populasi']

    if np.mean(rasio_wp_cap)<1:
        wp_per_cap = np.log(1+rasio_wp_cap)
    elif np.mean(rasio_wp_cap)>1:
        wp_per_cap = np.log(rasio_wp_cap)

    dep_var = gdp_per_cap
    indep_var = pd.DataFrame()
    indep_var['Capital Output Ratio'] = capital_per_gdp
    indep_var['Working Person per Capita'] = wp_per_cap
    indep_var = indep_var.fillna(0) # bisa diganti
    variabel_dict = {
        'Dependent Var': dep_var,
        'Independent Var': indep_var
        }
    return variabel_dict

    
def estimate_share(dependent_var, independent_var, cons=False):
    # dependent_var : dataframe, berisi variabel dependen
    # independent_var : dataframe, berisi variabel independen
    # nocons : bool, True jika estimasi dengan konstan False jika estimasi tanpa constant
    
    # dependent_var = dep_var
    # independent_var = indep_var
    # cons = False
    
    dependent_var = build_variabel(kapital_prov_pim)['Dependent Var']
    independent_var = build_variabel(kapital_prov_pim)['Independent Var']
    
    dep_mat = dependent_var.to_numpy(dtype=float)
    indep_mat = independent_var.to_numpy(dtype=float)
    
    # regression
    if cons==False:
        lm_model = LinearRegression(fit_intercept=cons).fit(indep_mat, dep_mat)
        mod = sm.OLS(dependent_var, independent_var)
    else:
        lm_model = LinearRegression(fit_intercept=True).fit(indep_mat, dep_mat)
        indep_var_cons = sm.add_constant(independent_var)
        mod = sm.OLS(dependent_var, indep_var_cons)
    
    # R Squared
    res = mod.fit()
    r2_sm = res.rsquared_adj # r_squared from scikit learn
    r2 = lm_model.score(indep_mat, dep_mat) # r_squared from statsmodels
    
    if r2<0:
        coef_capital = res.params[0]
        r_squared = r2_sm
    else:
        coef_capital = lm_model.coef_[1]
        r_squared = r2
    
    # Estimate share of capital, labor and tech
    alpha = (coef_capital/(1+coef_capital)) * r_squared
    share_labor = r_squared - alpha
    share_tech = 1-r_squared
    result_share =[(alpha*100), (share_labor*100), (share_tech*100)]
    result_round = [np.round(x, 2) for x in result_share]
    
    return result_round

# Find the growth rate of TFP (Total Factor Productivity)
# Directly from dep and indep var
# Harusnya dihitung dari pertumbuhan output, kapital dan labor saja.
def growth_rate(input_file, nlag=1):
    # input_file = dataframe
    # nlag = int, berisi jumlah lag untuk diestimasi tingkat pertumbuhannya
    
    lag_var = input_file.shift(nlag)
    output_file = (input_file - lag_var)/lag_var
    
    return output_file

def output_software(nlag_):
    provinsi_share = estimate_share(build_variabel(kapital_prov_pim)['Dependent Var'], 
                                    build_variabel(kapital_prov_pim)['Independent Var']) # share capital, labor, dan tfp
    np.sum(provinsi_share) # check whther the result equal to 100 or not
    output_growth = growth_rate(df_input['PDRB'], nlag_)
    capital_growth = growth_rate(kapital_prov_pim, nlag_)
    labor_growth = growth_rate(df_input['Jumlah.Orang.Bekerja'], nlag_)
    tfp_growth = output_growth - (provinsi_share[0]/100)*capital_growth - (provinsi_share[1]/100)*labor_growth

    result_dict = {
        'Tahun' : df_input['Date'],
        'pertumbuhan output' : output_growth,
        'pertumbuhan capital' : capital_growth * (provinsi_share[0]/100),
        'pertumbuhan labor' : (provinsi_share[1]/100)*labor_growth,
        'pertumbuhan TFP' : tfp_growth,
        'peran kapital labor tech' : np.array(provinsi_share)
        }
    result_df = pd.DataFrame(dict([ (k,pd.Series(v)) for k,v in result_dict.items() ]))
    return result_df


# Running function
wd_backup = ''
wd_main = ''
wd = wd_backup

excel_file = pd.ExcelFile(wd+'/Data Provinsi Input.xlsx')
list_sheet = excel_file.sheet_names

dict_result = {}
for i in range(len(list_sheet)):
    df_input = pd.read_excel(wd+'/Data Provinsi Input.xlsx', sheet_name=list_sheet[i])
    kapital_prov = kapital_stok(df_input, 0.2, 0.05)
    kapital_prov_pim = kapital_pim(df_input, 0.05)

    hasil_tfp = output_software(1)
    dict_result[list_sheet[i]] = hasil_tfp
    
writer = pd.ExcelWriter(wd+'/Output Software.xlsx')
dict_result[list_sheet[0]].to_excel(writer, sheet_name='Jawa Barat')
dict_result[list_sheet[1]].to_excel(writer, sheet_name='Sumatra Selatan')
dict_result[list_sheet[2]].to_excel(writer, sheet_name='Bali')
writer.save()

