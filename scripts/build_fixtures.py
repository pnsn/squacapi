

import json
'''assemble individual fixture files into single fixture to
    avoid race conditions
'''

with open('./app/fixtures/base.json') as f:
    base = json.load(f)
    print(type(base))

for file_name in ['core_user', 'alarms']:
    with open(f'./app/fixtures/{file_name}.json') as f:
        print(file_name)
        print("---------------------------------------------")
        j = json.load(f)
        print(type(j))
        base += j
        print(len(base))

with open('./app/fixtures/all.json', 'w') as json_file:
    json.dump(base, json_file)
