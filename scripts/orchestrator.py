"""Ideation Lite: standard-library-only, sequential approval-bound task runner."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
GATES = ('problem', 'goals', 'criteria', 'scope', 'consistency')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def save(path, state):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temp, path)


def validate(plan):
    require(isinstance(plan, dict), 'Plan must be an object')
    require(isinstance(plan.get('title'), str) and plan['title'].strip(), 'Missing title')
    require(Path(plan.get('cwd', '')).is_absolute() and Path(plan['cwd']).is_dir(),
            'cwd must be an existing absolute directory')
    for gate in GATES:
        evidence = plan.get('assessment', {}).get(gate)
        require(isinstance(evidence, str) and evidence.strip(), 'Missing evidence: ' + gate)
    for group in ('steps', 'checks'):
        items = plan.get(group)
        require(isinstance(items, list) and items, group + ' must be nonempty')
        for item in items:
            require(isinstance(item, dict), 'Task must be an object')
            for key in ('title', 'command'):
                require(isinstance(item.get(key), str) and item[key].strip(), 'Missing ' + key)
            timeout = item.get('timeout', 300)
            require(type(timeout) is int and 1 <= timeout <= 86400, 'Invalid timeout')


def shell():
    found = shutil.which('pwsh') or shutil.which('powershell')
    require(found, 'PowerShell is required')
    return found


def execute(item, cwd, log):
    payload = json.dumps({'cwd': cwd, 'command': item['command']}, ensure_ascii=False)
    with log.open('wb') as output:
        process = subprocess.Popen([shell(), '-NoLogo', '-NoProfile', '-NonInteractive',
                                    '-ExecutionPolicy', 'Bypass', '-File',
                                    str(Path(__file__).with_name('executor.ps1'))],
                                   stdin=subprocess.PIPE, stdout=output, stderr=subprocess.STDOUT)
        try:
            process.communicate(payload.encode('utf-8'), timeout=item.get('timeout', 300))
            return process.returncode
        except subprocess.TimeoutExpired:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                process.kill()
            process.communicate()
            return 124
        except BaseException:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                process.kill()
            process.wait()
            raise


def run_group(state, path, group, retry):
    for index, item in enumerate(state['plan'][group]):
        record = state[group][index]
        if record['status'] == 'passed':
            continue
        require(record['status'] == 'pending' or retry,
                'Previous failure/interruption: inspect logs; use --retry only if safe')
        record.update(status='running', started=time.time())
        state['phase'] = 'execution' if group == 'steps' else 'review'
        save(path, state)
        log = path.parent / (group + '-' + str(index + 1) + '.log')
        code = execute(item, state['plan']['cwd'], log)
        record.update(status='passed' if code == 0 else 'failed', exit_code=code,
                      log=str(log), ended=time.time())
        save(path, state)
        print(json.dumps({'task': item['title'], **record}, ensure_ascii=False))
        require(code == 0, 'Stopped at failed ' + group + '; see ' + str(log))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', required=True, help='Absolute state.json outside skill directory')
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('init').add_argument('--request', required=True)
    sub.add_parser('plan').add_argument('--file', required=True)
    sub.add_parser('status')
    approve = sub.add_parser('approve')
    approve.add_argument('--sha', required=True)
    approve.add_argument('--approval-text', required=True)
    for name in ('run', 'review'):
        sub.add_parser(name).add_argument('--retry', action='store_true')
    sub.add_parser('finish').add_argument('--review-text', required=True)
    args = parser.parse_args()
    path = Path(args.state)
    require(path.is_absolute(), '--state must be absolute')
    require(not path.is_relative_to(Path(__file__).resolve().parents[1]),
            'Store task state outside the installed skill')
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix('.lock')
    try:
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise ValueError('State locked; if owner stopped, inspect before removing ' + str(lock))
    try:
        os.write(handle, str(os.getpid()).encode())
        if args.action == 'init':
            require(not path.exists(), 'State already exists')
            state = {'version': 1, 'phase': 'assessment', 'request': args.request}
        else:
            state = read(path)
            require(state.get('version') == 1, 'Unsupported state version')
        if args.action == 'plan':
            require(state['phase'] in ('assessment', 'approval'),
                    'Start a new state for changes after execution or approval')
            plan = read(args.file)
            validate(plan)
            state.update(plan=plan, sha=digest(plan), phase='approval', approval=None,
                         steps=[{'status': 'pending'} for _ in plan['steps']],
                         checks=[{'status': 'pending'} for _ in plan['checks']])
        elif args.action == 'approve':
            require(state['phase'] == 'approval', 'No plan awaiting approval')
            require(args.sha == state['sha'] == digest(state['plan']), 'Plan digest mismatch')
            require(args.approval_text.strip(), 'Explicit human approval text required')
            state.update(phase='approved', approval={'sha': args.sha,
                         'text': args.approval_text, 'time': time.time()})
        elif args.action in ('run', 'review', 'finish'):
            validate(state['plan'])
            require(state.get('approval') and state['approval']['sha'] ==
                    state['sha'] == digest(state['plan']), 'Unapproved or changed plan')
            if args.action == 'run':
                require(state['phase'] in ('approved', 'execution'), 'Cannot run in this phase')
                run_group(state, path, 'steps', args.retry)
                state['phase'] = 'review'
            elif args.action == 'review':
                require(state['phase'] == 'review' and
                        all(x['status'] == 'passed' for x in state['steps']), 'Execution incomplete')
                run_group(state, path, 'checks', args.retry)
                state['phase'] = 'reviewed'
            else:
                require(state['phase'] == 'reviewed' and
                        all(x['status'] == 'passed' for x in state['checks']), 'Checks incomplete')
                require(args.review_text.strip(), 'Review evidence required')
                state.update(phase='completed', review=args.review_text)
        if args.action != 'status':
            save(path, state)
        print(json.dumps(state, ensure_ascii=False, indent=2))
    finally:
        os.close(handle)
        lock.unlink()


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as error:
        print('ERROR: ' + str(error), file=sys.stderr)
        sys.exit(2)
