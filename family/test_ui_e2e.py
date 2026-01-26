import time
import json
import os
import sys

try:
    import requests
except Exception as e:
    print('requests not installed in venv:', e)
    sys.exit(1)

SERVER = 'http://127.0.0.1:5001'

# create a small CSV with three rows to test reorder
csv_content = 'Hook,Hashtags,LongTailKeywords,FilePath\nRow A,#a,kw_a,\nRow B,#b,kw_b,\nRow C,#c,kw_c,\n'

tmp_csv = os.path.join(os.getcwd(), 'test_upload_ui.csv')
with open(tmp_csv, 'w', encoding='utf-8') as f:
    f.write(csv_content)
print('Wrote', tmp_csv)

# upload
with open(tmp_csv, 'rb') as fh:
    r = requests.post(SERVER + '/upload_csv', files={'file': ('test.csv', fh)})
print('upload_csv', r.status_code, r.text)
js = r.json()
filename = js.get('filename')
if not filename:
    print('upload failed')
    sys.exit(1)

# preview
r = requests.get(SERVER + '/csv_preview', params={'filename': filename})
print('preview', r.status_code)
data = r.json()
headers = data.get('headers')
rows = data.get('rows')
print('headers:', headers)
print('rows before:', [r.get('Hook') for r in rows])

# simulate drag-reorder: move first row to end
if rows:
    first = rows.pop(0)
    rows.append(first)

# edit first row Hook
if rows:
    rows[0]['Hook'] = 'Edited via UI E2E'

print('rows after edit/reorder:', [r.get('Hook') for r in rows])

# save and run (process 1 row to be quick)
payload = {
    'filename': filename,
    'rows_json': json.dumps(rows),
    'headers_json': json.dumps(headers),
    'src': '',
    'out': '',
    'rows': '1'
}
try:
    r = requests.post(SERVER + '/save_and_run', data=payload)
    print('save_and_run', r.status_code, r.text)
    job = r.json()
    job_id = job.get('job_id')
    if not job_id:
        print('no job id; response:', job)
        sys.exit(1)
except Exception as e:
    print('save_and_run error', e)
    sys.exit(1)

# poll status
start = time.time()
while True:
    time.sleep(2)
    r = requests.get(SERVER + '/status/' + job_id)
    if r.status_code != 200:
        print('status request failed', r.status_code, r.text)
        break
    s = r.json()
    print('status', s.get('status'))
    if s.get('status') in ('completed', 'failed'):
        print('outputs:', s.get('outputs'))
        log = s.get('log','')
        print('log tail:\n', '\n'.join(log.splitlines()[-30:]))
        break
    if time.time() - start > 300:
        print('timeout waiting for job')
        break

print('E2E test finished')
