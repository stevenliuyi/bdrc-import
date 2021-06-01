import pandas as pd

df = pd.read_csv('bdrc.csv')
retrieved = '+2021-05-09T00:00:00Z/11'

qs_file = open('qs.txt', 'w')

for idx, row in df.iterrows():
    print(idx)
    qs = 'CREATE\n'
    bdrc_id = row['bdrc_id']

    ref = f'S248\tQ30324366\tS2477\t"{bdrc_id}"\tS813\t{retrieved}'

    qs += 'LAST\tP31\tQ5\n'
    qs += f'LAST\tP2477\t"{bdrc_id}"\n'
    if not pd.isna(row['tol']):
        tol_id = row['tol']
        qs += f'LAST\tP4138\t"{int(tol_id)}"\t{ref}\n'
    if not pd.isna(row['en']):
        en = row['en'].split('|')
        qs += f'LAST\tLen\t"{en[0]}"\n'
        if len(en) > 1:
            en_aliases = '|'.join(en[1:])
            qs += f'LAST\tAen\t"{en_aliases}"\n'
    if not pd.isna(row['zh']):
        zh = row['zh'].split('|')
        qs += f'LAST\tLzh\t"{zh[0]}"\n'
        if len(zh) > 1:
            zh_aliases = '|'.join(zh[1:])
            qs += f'LAST\tAzh\t"{zh_aliases}"\n'
    if not pd.isna(row['bo_unicode']):
        bo = row['bo_unicode'].split('|')
        bo_wylie = row['bo'].split('|')
        qs += f'LAST\tLbo\t"{bo[0]}"\n'
        qs += f'LAST\tP1559\tbo:"{bo[0]}"\tP4187\t"{bo_wylie[0]}"\t{ref}\n'
        if len(bo) > 1:
            bo_aliases = '|'.join(bo[1:])
            qs += f'LAST\tAbo\t"{bo_aliases}"\n'
    if not pd.isna(row['gender']):
        if row['gender'] == 'M':
            qs += f'LAST\tP21\tQ6581097\t{ref}\n'
        elif row['gender'] == 'F':
            qs += f'LAST\tP21\tQ6581072\t{ref}\n'
    if not pd.isna(row['birth']):
        birth = int(row['birth'])
        qs += f'LAST\tP569\t+{birth}-01-01T00:00:00Z/9\t{ref}\n'
    if not pd.isna(row['death']):
        death = int(row['death'])
        qs += f'LAST\tP570\t+{death}-01-01T00:00:00Z/9\t{ref}\n'

    qs_file.write(qs)

qs_file.close()