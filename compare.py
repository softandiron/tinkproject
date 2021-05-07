import pandas as pd
df1 = pd.read_excel('test.xlsx').fillna('sergey')
df2 = pd.read_excel('tinkoffReport_2021.May.06.xlsx').fillna('sergey')
df1 = df1.drop(df1.columns[0], axis=1)
df2 = df2.drop(df2.columns[0], axis=1)
print((df1==df2).all().all())