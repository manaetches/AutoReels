import time
import json
import os

try:
    import requests
except Exception:
    requests = None

SERVER = 'http://127.0.0.1:5001'

csv_content = 'Hook,Hashtags,LongTailKeywords,FilePath\nTest hook 1,#tag1,keyword1,\n'

# write temp csv
tmp_csv = os.path.join(os.getcwd(), 'test_upload.csv')
with open(tmp_csv, 'w', encoding='utf-8') as f:
    f.write(csv_content)

print('CSV written to', tmp_csv)

if requests:
    # upload
    with open(tmp_csv, 'rb') as fh:
        r = requests.post(SERVER + '/upload_csv', files={'file': ('test.csv', fh)})
    print('upload_csv status', r.status_code, r.text)
    js = r.json()
    filename = js.get('filename')

    # preview
    r = requests.get(SERVER + '/csv_preview', params={'filename': filename})
    print('preview', r.status_code, r.text)
    data = r.json()
    rows = data.get('rows', [])
    if rows:
        rows[0]['Hook'] = 'Edited Hook Test'

    # save and run
    payload = {
        'filename': filename,
        'rows_json': json.dumps(rows),
        'src': '',
        'out': '',
        'rows': '1'
    }
    try:
        r = requests.post(SERVER + '/save_and_run', data=payload)
        print('save_and_run', r.status_code, r.text)
        job = r.json()
        job_id = job.get('job_id')
        print('job id', job_id)
    except Exception as e:
        print('save_and_run failed', e)
        raise

    # poll
    while True:
        time.sleep(2)
        r = requests.get(SERVER + '/status/' + job_id)
        js = r.json()
        print('status', js.get('status'))
        if js.get('status') in ('completed','failed'):
            print('final outputs', js.get('outputs'))
            print('log tail:\n', '\n'.join(js.get('log','').splitlines()[-20:]))
            break
else:
    print('requests not available in venv; please install requests and re-run')
