import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm
from statsmodels.tsa.seasonal import STL
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

# Seasonal Adjusment (hanya untuk data triwulan/bulan)
def seas_adj(input_file, seasonality=5):
    # input_file: pandas series dengan index waktu
    # seasonality: int harus bilangan ganjil, kalau triwulan int=5
    
    stl_obj = STL(input_file, seasonality)
    stl_res = stl_obj.fit()
    
    seas_adj = stl_res.observed - stl_res.seasonal
    return seas_adj

# Estimate the share of kapital, labor and tech
# Create the variables
# N adalah populasi
# L adalah jumlah orang bekerja

def build_variabel(input_file, kapital_var):
    # input_file: dataframe, biasanya df_input
    # kapital_var : dataframe/series, output function kapital_pim/kapital_stok 
    
    gdp_per_cap = np.log(input_file['PDRB']/input_file['Populasi'])
    capital_per_gdp = np.log(kapital_var/input_file['PDRB'])
    rasio_wp_cap = input_file['Jumlah.Orang.Bekerja']/input_file['Populasi']

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
    
    # dependent_var = build_variabel(df_sadj_q, kapital_prov_pimq)['Dependent Var']
    # independent_var = build_variabel(df_sadj_q, kapital_prov_pimq)['Independent Var']
    
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
        coef_capital = np.abs(res.params[0])
        r_squared = r2_sm
    else:
        coef_capital = np.abs(lm_model.coef_[1])
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

def output_software_new(prov_share_input, output_growth_input, capital_growth_input,
                        labor_growth_input, tfp_growth_input, date_input):
    result_dict = {
        'Tahun' : date_input,
        'pertumbuhan output' : output_growth_input,
        'pertumbuhan capital' : capital_growth_input * (prov_share_input[0]/100),
        'pertumbuhan labor' : (prov_share_input[1]/100)*labor_growth_input,
        'pertumbuhan TFP' : tfp_growth_input,
        'peran kapital labor tech' : np.array(prov_share_input)
        }
    result_df = pd.DataFrame(dict([ (k,pd.Series(v)) for k,v in result_dict.items() ]))
    return result_df

# Running function
wd_backup = ''
wd_main = ''
wd = wd_main

excel_file = pd.ExcelFile(wd+'/Data Provinsi Input.xlsx')
list_sheet = excel_file.sheet_names

nlag_input = 1
dict_result = {}
for i in range(len(list_sheet)):
    df_input = pd.read_excel(wd+'/Data Provinsi Input.xlsx', sheet_name=list_sheet[i])
    kapital_prov = kapital_stok(df_input, 0.2, 0.05)
    kapital_prov_pim = kapital_pim(df_input, 0.05)
    provinsi_share = estimate_share(build_variabel(df_input, 
                                                   kapital_prov_pim)['Dependent Var'], 
                                    build_variabel(df_input, 
                                                   kapital_prov_pim)['Independent Var']) # share capital, labor, dan tfp
    np.sum(provinsi_share) # check whther the result equal to 100 or not
    output_growth = growth_rate(df_input['PDRB'], nlag_input)
    capital_growth = growth_rate(kapital_prov_pim, nlag_input)
    labor_growth = growth_rate(df_input['Jumlah.Orang.Bekerja'], nlag_input)
    tfp_growth = output_growth - (provinsi_share[0]/100)*capital_growth - (provinsi_share[1]/100)*labor_growth
    
    hasil_tfp = output_software_new(provinsi_share, output_growth, capital_growth, 
                                    labor_growth, tfp_growth, df_input['Date'])
    dict_result[list_sheet[i]] = hasil_tfp
    
writer = pd.ExcelWriter(wd+'/Output Software Tahunan.xlsx')
dict_result[list_sheet[0]].to_excel(writer, sheet_name='Jawa Barat')
dict_result[list_sheet[1]].to_excel(writer, sheet_name='Sumatra Selatan')
dict_result[list_sheet[2]].to_excel(writer, sheet_name='Bali')
writer.save()

# Running function data triwulan
excel_file_q = pd.ExcelFile(wd+'/Data Provinsi Input Triwulan.xlsx')
list_sheet_q = excel_file_q.sheet_names

nlagq_input = 4
dict_result_q = {}
for i in range(len(list_sheet_q)):
    df_input_q = pd.read_excel(wd+'/Data Provinsi Input Triwulan.xlsx', 
                               sheet_name=list_sheet_q[i])
    df_input_q.index = df_input_q['Date']
    df_input_q_nd = df_input_q.drop(['Date'], axis=1)
    pmtb_q = df_input_q_nd['PMTB']
    pdrb_q = df_input_q_nd['PDRB']

    sadj_pmtb = seas_adj(pmtb_q, 5)
    sadj_pdrb = seas_adj(pdrb_q, 5)
    df_sadj_q = df_input_q_nd.copy()
    df_sadj_q['PMTB'] = sadj_pmtb
    df_sadj_q['PDRB'] = sadj_pdrb
    
    kapital_provq = kapital_stok(df_sadj_q, 0.2, 0.05)
    kapital_prov_pimq = kapital_pim(df_sadj_q, 0.05)
    provinsi_shareq = estimate_share(build_variabel(df_sadj_q, 
                                                   kapital_prov_pimq)['Dependent Var'], 
                                     build_variabel(df_sadj_q, 
                                                   kapital_prov_pimq)['Independent Var']) # share capital, labor, dan tfp
    output_growthq = growth_rate(df_sadj_q['PDRB'], nlagq_input).reset_index().iloc[:,1]
    capital_growthq = growth_rate(kapital_prov_pimq, nlagq_input).reset_index().iloc[:,1]
    labor_growthq = growth_rate(df_sadj_q['Jumlah.Orang.Bekerja'], nlagq_input).reset_index().iloc[:,1]
    tfp_growthq = output_growthq - (provinsi_shareq[0]/100)*capital_growthq - (provinsi_shareq[1]/100)*labor_growthq
    
    hasil_tfpq = output_software_new(provinsi_shareq, output_growthq, capital_growthq, 
                                     labor_growthq, tfp_growthq, df_sadj_q.index)
    dict_result_q[list_sheet_q[i]] = hasil_tfpq

writer = pd.ExcelWriter(wd+'/Output Software Triwulan.xlsx')
dict_result_q[list_sheet_q[0]].to_excel(writer, sheet_name='Jawa Barat')
dict_result_q[list_sheet_q[1]].to_excel(writer, sheet_name='Sumatra Selatan')
dict_result_q[list_sheet_q[2]].to_excel(writer, sheet_name='Bali')
writer.save()

# Pembagian periode per grup dan dibuat tabel
def average_growth(input_df, frekuensi='AS', tahun_awal='2006'):
    # input_df = dict_result['Bali_2010p']
    # frekuensi: str
    # tahun_awal: str
    
    # input_df = dict_result_q['Bali_2010p']
    # frekuensi = 'QS'
    # tahun_awal = '2006'
    
    # tahun_awal = input_df['Tahun'][0]
    # tahun_awal_str = tahun_awal.astype(str)
    input_df['date_index'] = pd.date_range(start=f'{tahun_awal}-01-01', 
                                           periods=np.size(input_df, axis=0), 
                                           freq=frekuensi)
    input_df.set_index('date_index', inplace=True)
    input_df = input_df.drop(columns=['Tahun'])
    input_df_slice = input_df.iloc[:,:4]
    # indeks_waktu = input_df.index
    # tahun_akhir_dt = indeks_waktu[-1]
    
    list_pembagian_waktu = [(input_df.index>=f'{tahun_awal}-01-01') & (input_df.index<'2000-01-01'),
                            (input_df.index>='2000-01-01') & (input_df.index<'2010-01-01'),
                            (input_df.index>='2010-01-01') & (input_df.index<'2020-01-01'),
                            input_df.index>='2020-01-01']
    list_nama_grup = ['1990an', '2000an', '2010an', '2020an']
    
    rata2_per_grup = {}
    for t in range(len(list_pembagian_waktu)):
        time_cond = list_pembagian_waktu[t]
        data_potong = input_df_slice.loc[time_cond]
        rata2_per_kolom = np.mean(data_potong, axis=0)
        rata2_per_grup[list_nama_grup[t]] = rata2_per_kolom
    
    result_df_rata2 = pd.DataFrame(rata2_per_grup)
    return result_df_rata2

dict_result_tabel_tahunan = {}
dict_result_tabel_triwulan = {}
for s in range(len(list_sheet)):
    df_olah = dict_result[list_sheet[s]]
    df_olah_q = dict_result_q[list_sheet_q[s]]
    hasil_tabel_tahunan = average_growth(df_olah, 'AS', '1993')
    hasil_tabel_triwulan = average_growth(df_olah_q, 'QS', '2006')
    dict_result_tabel_tahunan[list_sheet[s]] = hasil_tabel_tahunan
    dict_result_tabel_triwulan[list_sheet_q[s]] = hasil_tabel_triwulan
    
writer = pd.ExcelWriter(wd+'/Output Software Tabel Rata2 Tahunan.xlsx')
dict_result_tabel_tahunan[list_sheet[0]].to_excel(writer, sheet_name='Jawa Barat')
dict_result_tabel_tahunan[list_sheet[1]].to_excel(writer, sheet_name='Sumatra Selatan')
dict_result_tabel_tahunan[list_sheet[2]].to_excel(writer, sheet_name='Bali')
writer.save()

writer = pd.ExcelWriter(wd+'/Output Software Tabel Rata2 Triwulan.xlsx')
dict_result_tabel_triwulan[list_sheet_q[0]].to_excel(writer, sheet_name='Jawa Barat')
dict_result_tabel_triwulan[list_sheet_q[1]].to_excel(writer, sheet_name='Sumatra Selatan')
dict_result_tabel_triwulan[list_sheet_q[2]].to_excel(writer, sheet_name='Bali')
writer.save()

