import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import precheck
import verify_shift


def fence(tag, value):
    return '\n```' + tag + '\n' + json.dumps(value) + '\n```\n'


class ShiftChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'core.hooksPath', str(self.root / 'no-hooks'))
        self.git('config', 'commit.gpgSign', 'false')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        (self.repo / 'README.md').write_text('fixture')
        self.git('add', '.')
        self.git('commit', '-qm', 'Initial fixture')
        self.base = self.git('rev-parse', 'HEAD')
        self.board = self.root / 'board.md'
        self.board.write_text('- [ ] **T-1:** implement\n- [ ] **T-2:** second\n')
        self.brief = self.root / 'brief.md'
        self.policy = {'version': 1, 'base_commit': self.base, 'protected_paths': ['private']}
        self.phase = {'task': 'T-1', 'gate': 'python -m unittest', 'cwd': '.', 'done': 'Case passes', 'paths': ['src']}

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.repo, stderr=subprocess.PIPE, text=True).strip()

    def write(self, log='', extra=''):
        self.brief.write_text('# Shift\n' + fence('night-watch-policy', self.policy) +
            '\n## Phase 1 — T-1 implement\n' + fence('night-watch-phase', self.phase) + extra + '\n## Log\n' + log)

    def commit(self, path='src/main.py', message='T-1: implement'):
        p = self.repo / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('print(1)')
        self.git('add', '.')
        self.git('commit', '-qm', message)
        return self.git('rev-parse', 'HEAD')

    def receipt(self, sha, **updates):
        data = {'task': 'T-1', 'status': 'completed', 'gate': {'command': self.phase['gate'],
                'cwd': '.', 'commit': sha, 'exit_code': 0, 'output': 'Ran 1 test\nOK'}}
        data.update(updates)
        return '\n### Phase 1 — T-1 implementation · `' + sha + '`\n' + fence('night-watch-receipt', data)

    def check(self):
        return precheck.check(self.brief, self.board, self.repo)[0]

    def result(self):
        return verify_shift.verify(self.brief, self.repo)

    def test_valid_precheck(self):
        self.write()
        self.assertEqual(self.check(), [])

    def test_missing_empty_closed_and_duplicate_boards(self):
        self.write()
        for text in ('', '- [x] **T-1:** done', '- [ ] **T-2:** other', '- [ ] **T-1:** a\n- [x] **T-1:** b'):
            with self.subTest(text=text):
                self.board.write_text(text)
                self.assertTrue(self.check())
        self.board.unlink()
        self.assertTrue(self.check())

    def test_missing_task_gate_done_and_paths(self):
        for key in ('task', 'gate', 'done', 'paths'):
            original = copy.deepcopy(self.phase)
            del self.phase[key]
            self.write()
            self.assertTrue(self.check(), key)
            self.phase = original

    def test_scopes(self):
        for path in ('private/secret', '.', '../outside', '.github/workflows/job.yml', '/tmp/a', 'src/*'):
            self.phase['paths'] = [path]
            self.write()
            self.assertTrue(self.check(), path)
        (self.repo / 'escape').symlink_to(self.root, target_is_directory=True)
        self.phase['paths'] = ['escape/file']
        self.write()
        self.assertTrue(self.check())

    def test_negated_prose_does_not_trigger_false_refusal(self):
        self.write(extra='\nMust not touch `.github/workflows/` or private/.\n')
        self.assertEqual(self.check(), [])

    def test_fenced_phase_example_not_counted(self):
        self.write(extra='\n```markdown\n## Phase 9 — T-9 fake\n```\n')
        self.assertEqual(self.check(), [])

    def test_complete_receipt(self):
        sha = self.commit()
        self.write(self.receipt(sha))
        self.assertEqual(self.result()['exit_code'], 0)

    def test_empty_log_never_passes(self):
        self.write()
        self.assertEqual(self.result()['exit_code'], 1)

    def test_explicit_interruption_has_distinct_nonzero_exit(self):
        self.write('### STOPPED AFTER PHASE 0 — quota exhausted\n')
        self.assertEqual(self.result()['exit_code'], 2)

    def test_missing_sha_or_gate_evidence_rejected(self):
        sha = self.commit()
        for log in (self.receipt(sha).replace(' · `' + sha + '`', ''), self.receipt(sha, gate={})):
            self.write(log)
            self.assertEqual(self.result()['exit_code'], 1)

    def test_gate_must_match(self):
        sha = self.commit()
        gate = {'command': self.phase['gate'], 'cwd': '.', 'commit': sha, 'exit_code': 0, 'output': 'OK'}
        for key, value in [('command', 'echo passed'), ('cwd', 'src'), ('commit', self.base), ('exit_code', True), ('exit_code', 1), ('output', '')]:
            wrong = dict(gate, **{key: value})
            self.write(self.receipt(sha, gate=wrong))
            self.assertEqual(self.result()['exit_code'], 1, key)

    def test_out_of_scope_actual_change_rejected(self):
        self.write(self.receipt(self.commit('private/key.txt')))
        self.assertEqual(self.result()['exit_code'], 1)

    def test_renamed_protected_source_rejected(self):
        (self.repo / 'private').mkdir()
        (self.repo / 'private/data').write_text('sensitive')
        self.git('add', '.')
        self.git('commit', '-qm', 'Fixture protected file')
        self.policy['base_commit'] = self.git('rev-parse', 'HEAD')
        (self.repo / 'src').mkdir()
        self.git('mv', 'private/data', 'src/data')
        self.git('commit', '-qm', 'T-1: move')
        self.write(self.receipt(self.git('rev-parse', 'HEAD')))
        self.assertEqual(self.result()['exit_code'], 1)

    def test_wrong_task_duplicate_and_dirty_rejected(self):
        sha = self.commit()
        for log in (self.receipt(sha, task='T-2'), self.receipt(sha) * 2):
            self.write(log)
            self.assertEqual(self.result()['exit_code'], 1)
        self.write(self.receipt(sha))
        (self.repo / 'untracked').write_text('unfinished')
        self.assertEqual(self.result()['exit_code'], 1)

    def test_unmerged_commit_rejected(self):
        self.git('checkout', '-qb', 'candidate')
        sha = self.commit()
        self.git('checkout', '--detach', self.base)
        self.write(self.receipt(sha))
        self.assertEqual(self.result()['exit_code'], 1)

    def test_refusal_and_blocked_are_distinct(self):
        sha = self.commit()
        self.write(self.receipt(sha, status='refused', reason='measurement unsuitable', would_change='new data'))
        self.assertEqual(self.result()['exit_code'], 0)
        self.write(self.receipt(sha, status='blocked', reason='missing input') + '\n### STOPPED AFTER PHASE 1 — missing input\n')
        self.assertEqual(self.result()['exit_code'], 2)

    def test_remote_ref_required_when_requested(self):
        sha = self.commit()
        self.write(self.receipt(sha))
        self.assertEqual(verify_shift.verify(self.brief, self.repo, 'refs/remotes/origin/main')['exit_code'], 1)
        self.git('update-ref', 'refs/remotes/origin/main', sha)
        self.assertEqual(verify_shift.verify(self.brief, self.repo, 'refs/remotes/origin/main')['exit_code'], 0)

    def test_cli_json_returns_nonzero_incomplete(self):
        self.write('### STOPPED AFTER PHASE 0 — stopped\n')
        p = subprocess.run([sys.executable, str(Path(verify_shift.__file__)), str(self.brief), '--repo', str(self.repo), '--json'], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(json.loads(p.stdout)['status'], 'incomplete')

    def test_two_phases_with_separate_receipt_commit(self):
        sha = self.commit()
        self.git('commit', '--allow-empty', '-qm', 'Receipt for first task')
        sha2 = self.commit('tests/test_parser.py', 'T-2: add test')
        phase2 = dict(self.phase, task='T-2', paths=['tests'])
        extra = '\n## Phase 2 — T-2 second\n' + fence('night-watch-phase', phase2)
        log2 = self.receipt(sha2, task='T-2').replace('Phase 1 — T-1', 'Phase 2 — T-2')
        self.write(self.receipt(sha) + log2, extra=extra)
        self.assertEqual(self.result()['exit_code'], 0)

    def test_missing_remaining_phase_is_not_success(self):
        sha = self.commit()
        phase2 = dict(self.phase, task='T-2')
        self.write(self.receipt(sha), extra='\n## Phase 2 — T-2 second\n' + fence('night-watch-phase', phase2))
        self.assertEqual(self.result()['exit_code'], 1)

    def test_base_commit_cannot_be_reused_as_delivery(self):
        self.write(self.receipt(self.base))
        self.assertEqual(self.result()['exit_code'], 1)

    def test_duplicate_json_keys_refused(self):
        self.write()
        self.brief.write_text(self.brief.read_text().replace('"version": 1', '"version": 1, "version": 1'))
        self.assertTrue(self.check())

    def test_profile_unavailable_git_status_is_unknown(self):
        from unittest.mock import patch
        # Load by filename because stdlib profile may already be imported by a test runner.
        import importlib.util
        spec = importlib.util.spec_from_file_location('night_profile', Path(precheck.__file__).with_name('profile.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with patch.object(module, 'run', return_value=None):
            self.assertIsNone(module.build(self.repo)['dirty'])


if __name__ == '__main__':
    unittest.main()
