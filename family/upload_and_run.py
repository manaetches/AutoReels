import requests, time, json, os
BASE='http://127.0.0.1:5001'
csv_path=os.path.join(os.path.dirname(__file__),'..','..','test_upload_ui.csv')
csv_path=os.path.abspath(csv_path)
print('Using CSV:',csv_path)
if not os.path.exists(csv_path):
    raise SystemExit('CSV not found')
# upload
with open(csv_path,'rb') as fh:
    files={'csv':fh}
    r=requests.post(BASE+'/upload_csv', files=files)
print('upload', r.status_code, r.text)
rj=r.json()
filename=rj.get('filename')
if not filename:
    raise SystemExit('upload failed')
# preview
r=requests.get(BASE+'/csv_preview', params={'filename':filename})
print('preview', r.status_code)
p=r.json()
print('headers:', p.get('headers'))
rows=p.get('rows') or []
print('rows before:', [r.get('Hook') for r in rows])
# edit rows: change first Hook and rotate
if rows:
    rows[0]['Hook']='Uploaded via script'
    rows = [rows[0]] + rows[2:]+rows[1:2]
else:
    rows=[{'Hook':'Uploaded via script','Hashtags':'#test','LongTailKeywords':'test','FilePath':''}]
print('rows after edit:', [r.get('Hook') for r in rows])
headers = p.get('headers') or list(rows[0].keys())
# save and run
data={'filename':filename,'rows_json':json.dumps(rows),'headers_json':json.dumps(headers),'src':'D:\\reels-dev\\mixkit\\women\\family','out':'D:\\reels-dev\\mixkit\\women\\family\\ADHD_output_reel','rows':'3'}
r=requests.post(BASE+'/save_and_run', data=data)
print('save_and_run', r.status_code, r.text)
j=r.json()
job_id=j.get('job_id')
if not job_id:
    raise SystemExit('failed to queue job: '+r.text)
print('queued', job_id)
# poll
deadline=time.time()+300
while time.time()<deadline:
    r=requests.get(BASE+f'/status/{job_id}')
    if r.status_code!=200:
        print('status err', r.status_code, r.text)
        break
    s=r.json()
    print('status', s.get('status'))
    if s.get('status') in ('completed','failed'):
        print('final outputs:', s.get('outputs'))
        print('log tail:\n', s.get('log','')[-1000:])
        break
    time.sleep(3)
else:
    print('timeout waiting for job')

print('done')
