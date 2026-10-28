import json
import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict
from uuid import UUID, uuid4

from dotenv import dotenv_values
from langgraph.graph import END, START, StateGraph

from backend.app.config import ROOT

BRIEF_KEYS = ['UPSTAGE_API_KEY'] + [part + suffix for part in (
    'BUSINESS_STRATEGY', 'FINANCE_MANAGEMENT', 'WORKFORCE_ESG', 'COMPANY_BRIEF') for suffix in ('_AGENT_ID', '_CONFIG_ID')]
PERSONAL_KEYS = ['CANDIDATE_UPSTAGE_API_KEY'] + [part + suffix for part in ('CV', 'JD', 'CONTRIBUTION') for suffix in ('_AGENT_ID', '_CONFIG_ID')]


def agent_settings():
    values = dotenv_values(ROOT / '.env')
    return {key: str(values.get(key, os.getenv(key, '')) or '').strip() for key in BRIEF_KEYS + PERSONAL_KEYS}


def now():
    return datetime.now(timezone.utc).isoformat()


class JobFailure(Exception):
    def __init__(self, code):
        self.code = code


class JobState(TypedDict, total=False):
    job: dict
    directory: Path
    request: dict
    result: dict


def run_process(request, directory, stopped):
    request_path = directory / 'request.json'
    request_path.write_text(json.dumps(request, ensure_ascii=False), encoding='utf-8')
    environment = {key: value for key, value in os.environ.items() if not key.startswith(('GOOGLE_', 'SERVICE_'))}
    environment.update(agent_settings())
    environment.update(PYTHONIOENCODING='utf-8', LANGSMITH_TRACING='false', LANGCHAIN_TRACING_V2='false')
    process = subprocess.Popen([sys.executable, '-m', 'backend.app.agent_worker', str(request_path)],
                               cwd=ROOT, env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    started = time.monotonic()
    try:
        while process.poll() is None:
            if stopped.wait(.3):
                raise JobFailure('INTERRUPTED')
            if time.monotonic() - started > 5400:
                raise JobFailure('TIMEOUT')
        response_path = directory / 'response.json'
        if process.returncode != 0 or not response_path.is_file():
            raise JobFailure('AGENT_FAILED')
        response = json.loads(response_path.read_text(encoding='utf-8'))
        if response.get('error'):
            raise JobFailure(response['error'])
        return response['result']
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


class JobManager:
    """SQLite queue + a single local worker. Interrupted runs are not retried automatically."""

    def __init__(self, settings, db, runner=None):
        self.settings, self.db = settings, db
        self.runner = runner or run_process
        self.stopped = threading.Event()
        self.wake = threading.Event()
        self.thread = None
        graph = StateGraph(JobState)
        graph.add_node('prepare', self.prepare)
        graph.add_node('invoke_agents', self.invoke_agents)
        graph.add_node('persist_result', self.persist_result)
        graph.add_edge(START, 'prepare')
        graph.add_edge('prepare', 'invoke_agents')
        graph.add_edge('invoke_agents', 'persist_result')
        graph.add_edge('persist_result', END)
        self.graph = graph.compile()

    def start(self):
        with self.db.connect() as conn:
            conn.execute("UPDATE analysis_jobs SET status='failed',error_code='INTERRUPTED',stage='서버 재시작으로 중단됨',finished_at=? WHERE status='running'", (now(),))
            pending = {row[0] for row in conn.execute("SELECT id FROM analysis_jobs WHERE status IN ('queued','running')")}
        root = self.settings.data_dir / 'jobs'
        if root.exists():
            for directory in root.iterdir():
                try:
                    UUID(directory.name)
                except ValueError:
                    continue
                if directory.is_dir() and not directory.is_symlink() and directory.name not in pending:
                    shutil.rmtree(directory)
        self.thread = threading.Thread(target=self.loop, daemon=True, name='dart-agent-worker')
        self.thread.start()

    def close(self):
        self.stopped.set()
        self.wake.set()
        if self.thread:
            self.thread.join(timeout=8)

    def loop(self):
        while not self.stopped.is_set():
            if not self.run_one():
                self.wake.wait(.8)
                self.wake.clear()

    def run_one(self):
        with self.db.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            row = conn.execute("SELECT * FROM analysis_jobs WHERE status='queued' ORDER BY created_at,id LIMIT 1").fetchone()
            if not row:
                return False
            job = dict(row)
            conn.execute("UPDATE analysis_jobs SET status='running',stage='입력 자료 확인 중' WHERE id=?", (job['id'],))
        directory = self.settings.data_dir / 'jobs' / str(UUID(job['id']))
        try:
            directory.mkdir(parents=True, exist_ok=False)
            self.graph.invoke({'job': job, 'directory': directory})
        except Exception as error:
            code = error.code if isinstance(error, JobFailure) else 'AGENT_FAILED'
            with self.db.connect() as conn:
                conn.execute("UPDATE analysis_jobs SET status='failed',stage='분석 실패',error_code=?,finished_at=? WHERE id=? AND status='running'", (code, now(), job['id']))
        finally:
            if directory.exists() and directory.parent.resolve() == (self.settings.data_dir / 'jobs').resolve():
                shutil.rmtree(directory)
        return True

    def prepare(self, state):
        job, directory = state['job'], state['directory']
        request = {'job_id': job['id'], 'job_type': job['job_type'], 'target_role': job['target_role'], 'work_dir': str(directory), 'database': str(self.db.path)}
        with self.db.connect() as conn:
            for label in ('report', 'cv', 'jd'):
                doc_id = job[label + '_document_id']
                if not doc_id:
                    continue
                row = conn.execute('SELECT * FROM documents WHERE id=? AND user_id=?', (doc_id, job['user_id'])).fetchone()
                if not row:
                    raise JobFailure('INPUT_MISSING')
                target = directory / (label + '.pdf')
                shutil.copyfile(self.settings.data_dir / 'files' / row['storage_key'], target)
                request[label + '_path'] = str(target)
                request[label + '_name'] = row['original_name']
            if job['job_type'] == 'personal':
                brief = conn.execute('SELECT result_json FROM company_briefs WHERE id=? AND user_id=?', (job['brief_id'], job['user_id'])).fetchone()
                if not brief:
                    raise JobFailure('INPUT_MISSING')
                facts_path = directory / 'company_facts.json'
                facts_path.write_text(json.dumps(json.loads(brief[0])['facts'], ensure_ascii=False), encoding='utf-8')
                request['facts_path'] = str(facts_path)
        return {'request': request}

    def invoke_agents(self, state):
        return {'result': self.runner(state['request'], state['directory'], self.stopped)}

    def persist_result(self, state):
        job, result = state['job'], state['result']
        if not isinstance(result, dict) or not isinstance(result.get('markdown'), str) or not result['markdown'].strip():
            raise JobFailure('INVALID_RESULT')
        result_id = str(uuid4())
        with self.db.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            if job['job_type'] == 'brief':
                if not isinstance(result.get('brief'), dict) or not isinstance(result.get('facts'), dict) or not isinstance(result['facts'].get('facts'), list) or not result['facts']['facts']:
                    raise JobFailure('INVALID_RESULT')
                name = result['facts'].get('company_name') or result['brief'].get('company_name') or '기업명 미확인'
                if isinstance(name, list):
                    name = str(name[0]) if name else '기업명 미확인'
                conn.execute('''INSERT INTO company_briefs(id,user_id,report_document_id,company_name,result_json,created_at)
                    VALUES(?,?,?,?,?,?)''', (result_id, job['user_id'], job['report_document_id'], str(name), json.dumps(result, ensure_ascii=False), now()))
                report = conn.execute('SELECT pages FROM documents WHERE id=?', (job['report_document_id'],)).fetchone()
                for fact in result['facts'].get('facts', []):
                    evidence = fact.get('evidence', {}) if isinstance(fact, dict) else {}
                    page = evidence.get('original_page')
                    if isinstance(page, int) and 1 <= page <= report['pages'] and evidence.get('quote'):
                        conn.execute('''INSERT INTO evidence(id,user_id,document_id,brief_id,page,quote,section)
                            VALUES(?,?,?,?,?,?,?)''', (str(uuid4()), job['user_id'], job['report_document_id'], result_id, page, str(evidence['quote']), str(evidence.get('section', ''))))
            else:
                conn.execute('''INSERT INTO personal_analyses(id,user_id,brief_id,cv_document_id,jd_document_id,target_role,result_json,created_at)
                    VALUES(?,?,?,?,?,?,?,?)''', (result_id, job['user_id'], job['brief_id'], job['cv_document_id'], job['jd_document_id'], job['target_role'], json.dumps(result, ensure_ascii=False), now()))
            conn.execute("UPDATE analysis_jobs SET status='succeeded',stage='분석 완료',result_id=?,finished_at=? WHERE id=?", (result_id, now(), job['id']))
        return {}
