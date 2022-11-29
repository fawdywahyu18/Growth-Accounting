# script to run growth_accounting.py

from growth_accounting import *

# Import File
excel_file = pd.ExcelFile('Data Provinsi Input.xlsx')
list_sheet = excel_file.sheet_names
nlag_input = 1
nlagq_input = 4

# Running Function
hasil_ga_tahunan = estimasi_ga_tahunan('Data Provinsi Input.xlsx',list_sheet[0])
hasil_ga_triwulan = estimasi_ga_triwulan('Data Provinsi Input Triwulan.xlsx', list_sheet[0])
hasil_dekade_tahunan = average_growth(hasil_ga_tahunan, frekuensi='AS', tahun_awal=1993)
hasil_dekade_triwulan = average_growth(hasil_ga_tahunan, frekuensi='QS', tahun_awal=2006)

# Export Data
export_excel(hasil_ga_tahunan, list_sheet[0], tahunan=True)
export_excel(hasil_ga_triwulan, list_sheet[0], tahunan=False)
export_excel_average(hasil_dekade_tahunan, list_sheet[0], tahunan=True)
export_excel_average(hasil_dekade_triwulan, list_sheet[0], tahunan=False)

