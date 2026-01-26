from flask import Flask, request, jsonify, render_template_string, send_from_directory
import os
import uuid
import threading
import queue
import time
import json
import csv
import subprocess
import sys

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOADS, exist_ok=True)

# storage files
JOBS_FILE = os.path.join(UPLOADS, 'jobs.json')
CSV_STORE_FILE = os.path.join(UPLOADS, 'csv_store.json')

jobs_lock = threading.Lock()
task_queue = queue.Queue()


def _load_json(p):
    try:
        with open(p, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    except Exception:
        return {}


def _save_json(p, data):
    try:
        with open(p, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
    except Exception:
        pass


uploaded_csvs = _load_json(CSV_STORE_FILE)
jobs = _load_json(JOBS_FILE)


def save_csv_store():
    _save_json(CSV_STORE_FILE, uploaded_csvs)


def save_jobs(js=None):
    _save_json(JOBS_FILE, js or jobs)


def worker_loop():
    # worker: launches the CLI pipeline (app.py) using the same Python interpreter
    py = sys.executable
    app_py = os.path.join(BASE_DIR, 'app.py')
    while True:
        job_id = task_queue.get()
        with jobs_lock:
            job = jobs.get(job_id)
            if not job:
                continue
            job['status'] = 'running'
            job.setdefault('log', '')
            job['log'] += '\n[worker] started'
            save_jobs()
        try:
            # build command; app.py should accept CLI args like --csv and --music or handle defaults
            cmd = [py, app_py, '--csv', job.get('csv_path')]
            if job.get('music'):
                cmd += ['--music', job.get('music')]
            if job.get('out'):
                cmd += ['--out', job.get('out')]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=BASE_DIR)
            # stream stdout and update job log/output live
            for line in proc.stdout:
                line = line.rstrip('\n')
                with jobs_lock:
                    job.setdefault('log', '')
                    job.setdefault('outputs', [])
                    job['log'] += '\n' + line
                    # look for lines like: Created: <path>
                    if line.startswith('Created:'):
                        path = line.split('Created:', 1)[1].strip()
                        if path:
                            job['outputs'].append(path)
                    save_jobs()
            ret = proc.wait()
            with jobs_lock:
                if ret == 0:
                    job['status'] = 'completed'
                    job['log'] += '\n[worker] process exited 0'
                else:
                    job['status'] = 'failed'
                    job['log'] += f"\n[worker] process exited {ret}"
                save_jobs()
        except Exception as e:
            with jobs_lock:
                job['status'] = 'failed'
                job.setdefault('log', '')
                job['log'] += '\n[worker] exception: ' + str(e)
                save_jobs()


INDEX_HTML = '''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reels Generator</title>
<style>body{background:#061124;color:#e6eef6;font-family:Arial;padding:18px} .card{background:#071426;padding:12px;border-radius:8px;max-width:1100px;margin:12px auto} label{display:block;margin:8px 0} input[type=text], input[type=number]{width:100%;padding:6px;border-radius:4px;border:1px solid #123}</style>
</head><body>
<div class="card">
<h1>Reels Generator</h1>
<form id="form" enctype="multipart/form-data">
<label>CSV: <input type="file" id="csvfile" name="csv" accept=".csv"></label>
<label>Audio (optional): <input type="file" id="audio" name="audio" accept="audio/*"></label>
<label>Video source directory (on server): <input type="text" id="srcdir" placeholder="e.g. D:\\reels-dev\\mixkit\\women\\family"></label>
<label>Video output directory (on server): <input type="text" id="outdir" placeholder="e.g. D:\\reels-dev\\mixkit\\women\\family\\ADHD_output_reel"></label>
<label>Rows to process: <input type="number" id="rowscount" value="3" min="1" style="width:80px"></label>
<div style="margin-top:8px"><button id="upload">Upload CSV</button> <button id="run">Upload+Run</button></div>
</form>
<div style="margin-top:12px"><strong>Last response / status</strong></div>
<pre id="out" style="height:260px;overflow:auto;background:#021018;padding:8px;border-radius:6px"></pre>
<script>
async function postForm(url, fd){ const r=await fetch(url,{method:'POST',body:fd}); return r.json(); }
window.currentFilename = null;
document.getElementById('upload').onclick = async function(e){ e.preventDefault(); const f=document.getElementById('csvfile').files[0]; if(!f) return alert('pick csv'); const fd=new FormData(); fd.append('csv', f); const j=await postForm('/upload_csv', fd); if(j && j.filename){ window.currentFilename = j.filename; const p = await fetch('/csv_preview?filename='+encodeURIComponent(j.filename)); const pj = await p.json(); document.getElementById('out').textContent = 'Uploaded: ' + j.filename + '\n\n' + JSON.stringify(pj, null, 2); } else { document.getElementById('out').textContent = JSON.stringify(j, null, 2); } }

document.getElementById('run').onclick = async function(e){ e.preventDefault(); if(!window.currentFilename) return alert('Upload a CSV first');
    try{
        const src = document.getElementById('srcdir').value || '';
        const out = document.getElementById('outdir').value || '';
        const rowsCount = parseInt(document.getElementById('rowscount').value || '3', 10);
        const audioFile = document.getElementById('audio').files[0];
        // fetch preview rows to use as the edited rows
        const pv = await fetch('/csv_preview?filename='+encodeURIComponent(window.currentFilename));
        const preview = await pv.json();
        if(preview.error) return alert(preview.error);
        const rows = preview.rows || [];
        const fd = new FormData();
        fd.append('filename', window.currentFilename);
        fd.append('rows_json', JSON.stringify(rows));
        fd.append('rows', String(rowsCount));
        if(src) fd.append('src', src);
        if(out) fd.append('out', out);
        if(audioFile) fd.append('audio', audioFile);
        const r = await fetch('/save_and_run', { method: 'POST', body: fd });
        const jr = await r.json();
        document.getElementById('out').textContent = JSON.stringify(jr, null, 2);
        if(jr.job_id){
            // start polling status
            (async function poll(id){
                for(let i=0;i<120;i++){
                    const s = await fetch('/status/'+id); const sj = await s.json(); document.getElementById('out').textContent = JSON.stringify(sj, null, 2);
                    if(sj.status === 'completed' || sj.status === 'failed') break;
                    await new Promise(res=>setTimeout(res,2000));
                }
            })(jr.job_id);
        }
    }catch(err){ document.getElementById('out').textContent = 'Error: '+String(err); }
}
</script>
</div>
</body></html>'''


@app.route('/')
def index():
    return render_template_string(INDEX_HTML)


@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    f = request.files.get('file') or request.files.get('csv')
    if not f:
        return jsonify({'error':'no file'}), 400
    uid = uuid.uuid4().hex[:8]
    filename = f'{uid}_hooks.csv'
    path = os.path.join(UPLOADS, filename)
    f.save(path)
    try:
        with open(path, 'r', encoding='utf-8-sig', newline='') as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
            headers = reader.fieldnames or []
        uploaded_csvs[filename] = {'headers': headers, 'rows': rows}
        save_csv_store()
    except Exception:
        uploaded_csvs[filename] = {'headers': [], 'rows': []}
        save_csv_store()
    return jsonify({'filename': filename})


@app.route('/csv_preview')
def csv_preview():
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'error':'missing filename'}), 400
    path = os.path.join(UPLOADS, filename)
    if not os.path.exists(path):
        return jsonify({'error':'not found'}), 404
    try:
        if filename in uploaded_csvs:
            entry = uploaded_csvs[filename]
            return jsonify({'headers': entry.get('headers', []), 'rows': entry.get('rows', [])})
        with open(path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            headers = reader.fieldnames or []
        uploaded_csvs[filename] = {'headers': headers, 'rows': rows}
        save_csv_store()
        return jsonify({'headers': headers, 'rows': rows})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/save_and_run', methods=['POST'])
def save_and_run():
    filename = request.form.get('filename')
    rows_json = request.form.get('rows_json')
    src_dir = request.form.get('src') or None
    out_dir = request.form.get('out') or None
    rows_count = int(request.form.get('rows') or 3)
    if not filename or not rows_json:
        return jsonify({'error':'missing filename or rows_json'}), 400
    path = os.path.join(UPLOADS, filename)
    try:
        rows = json.loads(rows_json)
    except Exception as e:
        return jsonify({'error':'invalid rows_json: '+str(e)}), 400
    headers_json = request.form.get('headers_json')
    try:
        if headers_json:
            headers = json.loads(headers_json)
        elif rows:
            headers = list(rows[0].keys())
        else:
            headers = ['Hook','Hashtags','LongTailKeywords','FilePath']
        tmp = path + '.tmp'
        with open(tmp, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        os.replace(tmp, path)
        uploaded_csvs[filename] = {'headers': headers, 'rows': rows}
        save_csv_store()
    except Exception as e:
        return jsonify({'error':'write failed: '+str(e)}), 500
    # optional audio
    music_path = None
    audio_file = request.files.get('audio')
    if audio_file and audio_file.filename:
        music_path = os.path.join(UPLOADS, f'{uuid.uuid4().hex}_audio' + os.path.splitext(audio_file.filename)[1])
        audio_file.save(music_path)
    job_id = uuid.uuid4().hex
    job = {
        'id': job_id,
        'csv_path': path,
        'music': music_path,
        'src': src_dir,
        'out': out_dir,
        'rows': rows_count,
        'status': 'queued',
        'log': '',
        'outputs': []
    }
    with jobs_lock:
        jobs[job_id] = job
        save_jobs()
    task_queue.put(job_id)
    return jsonify({'job_id': job_id})


@app.route('/api/csvs', methods=['GET'])
def api_list_csvs():
    out = []
    for name, entry in uploaded_csvs.items():
        out.append({'filename': name, 'headers': entry.get('headers', []), 'rows': len(entry.get('rows', []))})
    return jsonify({'csvs': out})


@app.route('/api/csv/<filename>', methods=['GET', 'DELETE', 'POST'])
def api_csv_item(filename):
    if request.method == 'GET':
        entry = uploaded_csvs.get(filename)
        if not entry:
            return jsonify({'error':'not found'}), 404
        return jsonify({'filename': filename, 'headers': entry.get('headers', []), 'rows': entry.get('rows', [])})
    if request.method == 'DELETE':
        if filename in uploaded_csvs:
            uploaded_csvs.pop(filename, None)
            p = os.path.join(UPLOADS, filename)
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
            save_csv_store()
            return jsonify({'ok': True})
        return jsonify({'error':'not found'}), 404
    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({'error':'invalid json'}), 400
    headers = payload.get('headers') or []
    rows = payload.get('rows') or []
    uploaded_csvs[filename] = {'headers': headers, 'rows': rows}
    save_csv_store()
    try:
        p = os.path.join(UPLOADS, filename)
        with open(p, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
    except Exception:
        pass
    return jsonify({'ok': True})


@app.route('/status/<job_id>')
def status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({'error':'job not found'}), 404
    return jsonify({'id':job_id,'status':job.get('status'),'log':job.get('log'),'outputs':job.get('outputs')})


@app.route('/download')
def download():
    path = request.args.get('path')
    if not path or not os.path.exists(path):
        return 'Not found', 404
    directory = os.path.dirname(path)
    filename = os.path.basename(path)
    return send_from_directory(directory, filename, as_attachment=True)


if __name__ == '__main__':
    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()
    app.run(port=5001, debug=False)
