import requests
import re
import pandas as pd
import subprocess
import os


def get_entity(rid):
    bdrcCore = 'http://purl.bdrc.io/ontology/core'
    bdrcResource = 'http://purl.bdrc.io/resource'
    prefLabel = 'http://www.w3.org/2004/02/skos/core#prefLabel'
    sameAs = 'http://www.w3.org/2002/07/owl#sameAs'
    rdfType = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
    personGender = f'{bdrcCore}/personGender'
    personEvent = f'{bdrcCore}/personEvent'
    personBirth = f'{bdrcCore}/PersonBirth'
    personDeath = f'{bdrcCore}/PersonDeath'
    personStudentOf = f'{bdrcCore}/personStudentOf'
    personTeacherOf = f'{bdrcCore}/personTeacherOf'
    onYear = f'{bdrcCore}/onYear'
    genderMale = f'{bdrcResource}/GenderMale'
    genderFemale = f'{bdrcResource}/GenderFemale'

    url = f'https://purl.bdrc.io/query/graph/ResInfo-SameAs?R_RES=bdr%3A{rid}&format=json'
    res = requests.get(url)

    if not res.ok:
        return None

    results = {
        'names_en': [],
        'names_zh': [],
        'names_bo': [],
        'names_bo_unicode': [],
        'gender': None,
        'birth': None,
        'death': None,
        'teachers': [],
        'students': [],
        'tol': None
    }

    data = res.json()

    # check if this is a redirect
    admindata = data[f'http://purl.bdrc.io/admindata/{rid}']
    if 'http://purl.bdrc.io/ontology/admin/replaceWith' in admindata:
        return None

    bdrc_resource_key = f'http://purl.bdrc.io/resource/{rid}'
    bdrc_resource = data[bdrc_resource_key]
    for key, values in bdrc_resource.items():
        if key == prefLabel:
            for name in values:
                if name['lang'] == 'zh-hant' or name['lang'] == 'zh-hans':
                    results['names_zh'] += [name['value']]
                elif name['lang'] == 'en':
                    results['names_en'] += [name['value'].capitalize()]
                elif name['lang'] == 'bo-x-ewts':
                    results['names_bo'] += [name['value']]
                else:
                    results['names_en'] += [name['value'].capitalize()]
        elif key == sameAs:
            for uri in values:
                if uri['value'].startswith('http://api.treasuryoflives.org'):
                    results['tol'] = uri['value'][44:]
        elif key == personGender:
            if values[0]['value'] == genderMale:
                results['gender'] = 'M'
            elif values[0]['value'] == genderFemale:
                results['gender'] = 'F'
        elif key == personEvent:
            for event in values:
                if not event['value'] in data: continue
                event_resource = data[event['value']]
                if rdfType in event_resource:
                    if event_resource[rdfType][0]['value'] == personBirth:
                        if onYear in event_resource:
                            results['birth'] = event_resource[onYear][0][
                                'value']
                    elif event_resource[rdfType][0]['value'] == personDeath:
                        if onYear in event_resource:
                            results['death'] = event_resource[onYear][0][
                                'value']
        elif key == personStudentOf:
            for teacher in values:
                if teacher['value'].startswith(
                        'http://purl.bdrc.io/resource/P'):
                    results['teachers'] += [teacher['value'][29:]]
        elif key == personTeacherOf:
            for student in values:
                if student['value'].startswith(
                        'http://purl.bdrc.io/resource/P'):
                    results['students'] += [student['value'][29:]]

    results['names_en'] = [x.replace('/', '') for x in results['names_en']]
    results['names_en'] = [
        re.sub(r'\(.*\)', '', x) for x in results['names_en']
    ]
    for name_en in results['names_en']:
        shortened_name = re.sub(r'^.*\s\d{2,3}\s', '', name_en).strip()
        if shortened_name != '' and not shortened_name in results['names_en']:
            results['names_en'].append(shortened_name)

    names_bo = []
    for name_bo in results['names_bo']:
        shortened_name = re.sub(r'^.*\s\d{2,3}\s', '', name_bo).strip()
        shortened_name = re.sub(r'\(.*\)', '', shortened_name).strip()
        if shortened_name != '':
            names_bo.append(shortened_name)
        else:
            names_bo.append(name_bo)
    results['names_bo'] = names_bo

    names_bo_unicode = []
    names_bo = []
    names_pronounce = []
    for name_bo in results['names_bo']:
        unicode, pronounce = wylie2unicode(name_bo)
        if (not pronounce in results['names_en']) and (not '?' in pronounce):
            names_pronounce.append(pronounce)
        names_bo_unicode.append(unicode)
        if name_bo[-1] == '/':
            names_bo.append(name_bo[:-1])
        else:
            names_bo.append(name_bo)
    results['names_en'] = names_pronounce + results['names_en']
    results['names_bo_unicode'] = names_bo_unicode
    results['names_bo'] = names_bo

    return results


def wylie2unicode(wylie):
    wylie1 = wylie.strip()
    if wylie1[-1] != '/': wylie1 += '/'
    with open('Lingua-BO-Wylie/bin/input', 'w') as f:
        f.write(wylie1)
    os.chdir('./Lingua-BO-Wylie/bin')
    subprocess.run(['./wylie.pl', 'input', 'output_unicode'])
    subprocess.run(['./pronounce.pl', 'input', 'output_en'])
    os.chdir('../..')
    with open('Lingua-BO-Wylie/bin/output_unicode') as f:
        unicode = f.read()
    with open('Lingua-BO-Wylie/bin/output_en') as f:
        en = f.read()
        en = ' '.join([x.capitalize() for x in en.split(' ')])
    subprocess.run(['rm', 'Lingua-BO-Wylie/bin/input'])
    subprocess.run(['rm', 'Lingua-BO-Wylie/bin/output_unicode'])
    subprocess.run(['rm', 'Lingua-BO-Wylie/bin/output_en'])

    return unicode, en


def add_item(df, bdrc_id):
    if bdrc_id in list(df['bdrc_id']):
        print(f'{bdrc_id} (existed)')
        return df

    if len(list(df['bdrc_id'])) % 100 == 0:
        df.to_csv('bdrc.csv', index=False)

    results = get_entity(bdrc_id)
    print(bdrc_id)

    if results is None: return df

    df = df.append({
        'bdrc_id': bdrc_id,
        'en': '|'.join(results['names_en']),
        'zh': '|'.join(results['names_zh']),
        'bo': '|'.join(results['names_bo']),
        'bo_unicode': '|'.join(results['names_bo_unicode']),
        'gender': results['gender'],
        'birth': results['birth'],
        'death': results['death'],
        'teachers': '|'.join(results['teachers']),
        'students': '|'.join(results['students']),
        'tol': results['tol']
    },
                   ignore_index=True)

    return df


if __name__ == '__main__':
    df = pd.read_csv('bdrc.csv')

    id_range = [f'P{i}' for i in range(1, 10)]
    for i in id_range:
        df = add_item(df, i)

    df.to_csv('bdrc.csv', index=False)