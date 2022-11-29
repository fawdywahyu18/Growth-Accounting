from setuptools import setup

setup(
    name='growth_accounting',
    version='0.1.0',
    py_modules=['growth_accounting'],
    install_requires=[
        'et-xmlfile==1.1.0',
        'joblib==1.2.0',
        'numpy==1.23.3',
        'openpyxl==3.0.10',
        'packaging==21.3',
        'pandas==1.5.0',
        'patsy==0.5.3',
        'pyparsing==3.0.9',
        'python-dateutil==2.8.2',
        'pytz==2022.6',
        'scikit-learn==1.1.2',
        'scipy==1.9.3',
        'six==1.16.0',
        'statsmodels==0.13.2',
        'threadpoolctl==3.1.0'
    ],
    entry_points='''
        [console_scripts]
        growth_accounting=growth_accounting:growth_accounting
    ''',
)