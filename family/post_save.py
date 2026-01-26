import requests, json
BASE='http://127.0.0.1:5001'
filename='ef78332a_hooks.csv'
# fetch preview
r=requests.get(BASE+'/csv_preview', params={'filename':filename}); print('preview', r.status_code, r.text)
# load rows
p=r.json(); rows=p.get('rows') or [{'Hook':'X','Hashtags':'#x','LongTailKeywords':'x','FilePath':''}]
rows[0]['Hook']='Scripted Save'
headers=p.get('headers') or list(rows[0].keys())
print('headers',headers)
print('rows before', [r.get('Hook') for r in rows])
# save and run
data={'filename':filename,'rows_json':json.dumps(rows),'headers_json':json.dumps(headers),'src':'','out':'','rows':'1'}
r=requests.post(BASE+'/save_and_run', data=data)
print('save_and_run', r.status_code, r.text)
