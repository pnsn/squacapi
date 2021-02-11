import json
'''assemble individual fixture files into single fixture. This 'should' be a
    one-off. Future fixture updates can be added by hand, either by hand, as
    would be easiest for permission, or by directly editing fixtures/all.json
'''

with open('./app/fixtures/base.json') as f:
    base = json.load(f)
# clean up base to remove models auth.group and auth.permission
# add models to blacklist to list as needed
model_blacklist = ['auth.permission']
base = [doc for doc in base if doc['model']
        not in model_blacklist]
for file_name in ['core_user', 'alarms']:
    with open(f'./app/fixtures/{file_name}.json') as f:
        j = json.load(f)
        base += j

with open('./app/fixtures/all.json', 'w') as json_file:
    json.dump(base, json_file)
