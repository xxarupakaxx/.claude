"""Security boundaries and the real offline worker, using disposable fixtures."""
import base64
from contextlib import contextmanager
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/run.py'
spec = importlib.util.spec_from_file_location('imozuru_run', SCRIPT)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

@contextmanager
def topic():
    with tempfile.TemporaryDirectory(prefix='imozuru-test-') as temporary:
        path = Path(temporary).resolve() / 'topic'
        path.mkdir(mode=0o700)
        fd, chain = r.directory_fd(path)
        try:
            yield path, fd, chain
        finally:
            for parent, _, _, _ in chain:
                os.close(parent)
            os.close(fd)

class Boundaries(unittest.TestCase):
    def http_failure_fixture(self, error=None):
        sock=MagicMock();sock.getpeername.return_value=('1.1.1.1',443)
        conn=MagicMock()
        if error is None:
            wire=b'HTTP/1.1 200 OK\r\n'+b'X-Fixture: x\r\n'*33+b'\r\nbody'
            source=MagicMock();source.makefile.return_value=io.BytesIO(wire)
            response=r.http.client.HTTPResponse(source)
            conn.getresponse.side_effect=response.begin
        else:
            conn.getresponse.side_effect=error
        with patch.object(r.socket,'socket',return_value=sock),patch.object(r.http.client,'HTTPSConnection',return_value=conn),patch.object(r,'limits'),patch.object(r,'apply_sandbox'):
            r.hop('https://fixture.example/','1.1.1.1',0)

    def test_http_parser_header_limit_becomes_safe_failure(self):
        with self.assertRaisesRegex(ValueError, r'^public response rejected \(http_header_limit\)$'):
            self.http_failure_fixture()
        self.assertEqual(r.http.client._MAXHEADERS,32)
        self.assertEqual(r.http.client._MAXLINE,8192)

    def test_http_parser_failures_do_not_expose_untrusted_details(self):
        for error,code in [(r.http.client.LineTooLong('PRIVATE_RESPONSE'),'http_line_limit'),(r.http.client.BadStatusLine('PRIVATE_RESPONSE'),'http_response_invalid'),(r.http.client.IncompleteRead(b'PRIVATE_RESPONSE',42),'http_response_invalid'),(r.http.client.HTTPException('PRIVATE_RESPONSE'),'http_response_invalid')]:
            with self.subTest(kind=type(error).__name__),self.assertRaises(ValueError) as caught:
                self.http_failure_fixture(error)
            self.assertEqual(str(caught.exception),'public response rejected ('+code+')')
            self.assertNotIn('PRIVATE',str(caught.exception))

    @contextmanager
    def activation_fixture(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / 'imozuru'
            profile = package.parent / 'skill-governance/restricted-profiles' / r.PROFILE_ID / 'profile.json'
            profile.parent.mkdir(parents=True)
            profile.write_text(json.dumps({'verifier': {'python_path': r.VERIFIER}}))
            with patch.object(r, 'PACKAGE', package):
                yield

    def activation_result(self, *, race=False, extra=(), scope='imozuru-public-source-v1', code=None):
        rows = [{'code': 'restricted_observation', 'severity': 'BLOCKING', 'message': 'Audit observation failed: discovery_directory_changed', 'path': 'audit/inventory'}] if race else []
        rows.extend(extra)
        state = {'capability_scope': scope, 'capability_status': 'blocked' if rows else 'active', 'findings': rows}
        return subprocess.CompletedProcess([], (2 if rows else 0) if code is None else code, json.dumps(state).encode(), b'UNRELATED_PRIVATE_STDERR')

    def test_activation_retries_only_fresh_scan_once(self):
        race = self.activation_result(race=True)
        with self.activation_fixture(), patch.object(r.subprocess, 'run', side_effect=[race, self.activation_result()]) as invoke, patch.object(sys, 'stderr', new_callable=io.StringIO) as errors:
            r.verify_active()
        self.assertEqual(invoke.call_count, 2)
        self.assertEqual(invoke.call_args_list[0].args, invoke.call_args_list[1].args)
        first, second = [call.kwargs for call in invoke.call_args_list]
        self.assertGreater(first['timeout'], second['timeout'])
        self.assertLessEqual(first['timeout'], 60)
        self.assertEqual({k:v for k,v in first.items() if k!='timeout'}, {k:v for k,v in second.items() if k!='timeout'})
        self.assertEqual(errors.getvalue().count('retrying fresh audit'), 1)
        self.assertIn('fresh activation recheck passed (2/2)', errors.getvalue())
        self.assertNotIn('UNRELATED_PRIVATE_STDERR', errors.getvalue())

    def test_activation_persistent_scan_race_stops_after_two_attempts(self):
        race = self.activation_result(race=True)
        with self.activation_fixture(), patch.object(r.subprocess, 'run', return_value=race) as invoke, patch.object(sys, 'stderr', new_callable=io.StringIO) as errors, self.assertRaisesRegex(ValueError, 'discovery_directory_changed'):
            r.verify_active()
        self.assertEqual(invoke.call_count, 2)
        self.assertNotIn('recheck passed', errors.getvalue())

    def test_activation_other_and_mixed_failures_never_retry(self):
        for result in [
            self.activation_result(race=True, extra=[{'code': 'restricted_package_hash', 'severity': 'BLOCKING', 'message': 'changed bytes'}]),
            self.activation_result(race=True, extra=[{'code': 'restricted_inventory', 'severity': 'unknown', 'message': 'invalid global row', 'path': []}]),
            self.activation_result(race=True, extra=[{'code': 'restricted_global_findings', 'severity': 'BLOCKING', 'message': 'global drift', 'path': 'active'}]),
            self.activation_result(extra=[{'code': 'restricted_observation', 'severity': 'BLOCKING', 'message': 'Audit observation failed: discovery_directory_changed', 'path': 'unexpected'}]),
            self.activation_result(extra=[{'code': 'restricted_observation', 'severity': 'BLOCKING', 'message': 'Audit observation failed: discovery_lstat_failed'}]),
            self.activation_result(extra=[{'code': 'restricted_observation', 'severity': 'BLOCKING', 'message': 'Audit observation failed: unknown_future_code'}]),
            self.activation_result(extra=[{'code': 'restricted_inventory', 'severity': 'BLOCKING', 'message': 'global drift'}]),
            self.activation_result(race=True, scope='other'),
            self.activation_result(race=True, code=1),
            self.activation_result(code=2),
        ]:
            with self.subTest(state=result.stdout), self.activation_fixture(), patch.object(r.subprocess, 'run', return_value=result) as invoke, self.assertRaisesRegex(ValueError, 'activation failed'):
                r.verify_active()
            self.assertEqual(invoke.call_count, 1)

    def test_activation_invalid_json_and_malformed_state_stop(self):
        for raw in [b'{', b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff', b'[]', b'null', b'{"capability_scope":"imozuru-public-source-v1","capability_status":"blocked","findings":[{"code":[],"message":{}}]}']:
            result = subprocess.CompletedProcess([], 2, raw, b'UNRELATED_PRIVATE_STDERR')
            with self.subTest(raw=raw), self.activation_fixture(), patch.object(r.subprocess, 'run', return_value=result) as invoke, self.assertRaisesRegex(ValueError, 'activation failed') as error:
                r.verify_active()
            self.assertEqual(invoke.call_count, 1)
            self.assertNotIn('UNRELATED_PRIVATE_STDERR', str(error.exception))

    def test_activation_timeout_never_retries(self):
        with self.activation_fixture(), patch.object(r.subprocess, 'run', side_effect=subprocess.TimeoutExpired('PRIVATE_ARGUMENT', 60)) as invoke, self.assertRaisesRegex(ValueError, 'audit_timeout') as error:
            r.verify_active()
        self.assertEqual(invoke.call_count, 1)
        self.assertNotIn('PRIVATE_ARGUMENT', str(error.exception))

    def test_activation_retries_share_original_sixty_second_deadline(self):
        with self.activation_fixture(), patch.object(r.time, 'monotonic', side_effect=[0, 0, 59]), patch.object(r.subprocess, 'run', side_effect=[self.activation_result(race=True), self.activation_result()]) as invoke, patch.object(sys, 'stderr', new_callable=io.StringIO):
            r.verify_active()
        self.assertEqual([call.kwargs['timeout'] for call in invoke.call_args_list], [60, 1])
        with self.activation_fixture(), patch.object(r.time, 'monotonic', side_effect=[0, 0, 60]), patch.object(r.subprocess, 'run', return_value=self.activation_result(race=True)) as invoke, patch.object(sys, 'stderr', new_callable=io.StringIO), self.assertRaisesRegex(ValueError, 'audit_timeout'):
            r.verify_active()
        self.assertEqual(invoke.call_count, 1)

    def test_activation_diagnostics_are_bounded_codes_only(self):
        rows = [{'code': 'restricted_' + value, 'path': 'PRIVATE_PATH', 'message': 'PRIVATE_MESSAGE'} for value in ['one', 'two', 'three', 'four', 'five']]
        rows.extend([{'code': 'restricted_newline\nPRIVATE_VALUE'}, {'code': 'restricted_' + 'x' * 49}, {'code': ['bad']}])
        text = r.activation_failure_codes({'findings': rows})
        self.assertEqual(len(text.split(',')), 4)
        self.assertNotIn('PRIVATE', text)
        self.assertNotIn('\n', text)

    def test_activation_uses_explicit_fixed_capability_and_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / 'imozuru'
            profile = package.parent / 'skill-governance/restricted-profiles' / r.PROFILE_ID / 'profile.json'
            profile.parent.mkdir(parents=True)
            profile.write_text(json.dumps({'verifier': {'python_path': r.VERIFIER}}))
            good = {'capability_scope': 'imozuru-public-source-v1', 'capability_status': 'active', 'restricted_status': 'blocked', 'global_drift': 'HOLD'}
            result = subprocess.CompletedProcess([], 0, json.dumps(good).encode(), b'')
            with patch.object(r, 'PACKAGE', package), patch.object(r.subprocess, 'run', return_value=result) as invoke:
                r.verify_active()
                self.assertIn('--require-capability', invoke.call_args.args[0])
                self.assertIn('--summary', invoke.call_args.args[0])
            for key, value in [('capability_status', 'blocked'), ('capability_scope', 'other'), ('capability_status', None)]:
                bad = dict(good); bad[key] = value
                result = subprocess.CompletedProcess([], 0, json.dumps(bad).encode(), b'')
                with patch.object(r, 'PACKAGE', package), patch.object(r.subprocess, 'run', return_value=result), self.assertRaisesRegex(ValueError, 'activation'):
                    r.verify_active()
            result = subprocess.CompletedProcess([], 2, json.dumps(good).encode(), b'')
            with patch.object(r, 'PACKAGE', package), patch.object(r.subprocess, 'run', return_value=result), self.assertRaisesRegex(ValueError, 'activation'):
                r.verify_active()

    def test_verifier_can_run_system_git_without_relaxing_worker_environment(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / 'imozuru'
            governance = package.parent / 'skill-governance'
            profile = governance / 'restricted-profiles' / r.PROFILE_ID / 'profile.json'
            profile.parent.mkdir(parents=True)
            profile.write_text(json.dumps({'verifier': {'python_path': r.VERIFIER}}))
            verifier = governance / 'scripts/governance.py'
            verifier.parent.mkdir()
            verifier.write_text("import json, os, subprocess\n"
                                "assert os.environ['PATH'] == '/usr/bin:/bin'\n"
                                "assert 'IMOZURU_FIXTURE_SENTINEL' not in os.environ\n"
                                "subprocess.run(['git', '--version'], check=True, stdout=subprocess.DEVNULL)\n"
                                "print(json.dumps({'capability_scope':'imozuru-public-source-v1','capability_status':'active'}))\n")
            with patch.object(r, 'PACKAGE', package), patch.dict(os.environ, {'PATH':'/untrusted', 'IMOZURU_FIXTURE_SENTINEL':'not inherited'}):
                r.verify_active()
            self.assertEqual(r.clean_env()['PATH'], '')
            self.assertEqual(r.clean_env()['HOME'], '/nonexistent')

    def test_private_and_ambiguous_urls(self):
        bad = ['file:///etc/passwd', 'http://127.0.0.1/', 'http://10.0.0.1/', 'http://169.254.169.254/', 'http://2130706433/', 'http://0x7f000001/', 'http://0177.0.0.1/', 'http://[::1]/', 'http://[::ffff:127.0.0.1]/', 'http://[64:ff9b::7f00:1]/', 'http://[2002:0808:0808::1]/', 'https://user@example.org/', 'https://example.org:8443/', 'https://example.org./', 'https://example.org/?token=secret', 'https://exa\u200bmple.org/', 'https://example.org/\npath', 'https://example.org\\@evil.org/']
        for url in bad:
            with self.subTest(url=url), self.assertRaises(ValueError):
                r.url_parts(url)

    def test_mixed_public_private_dns_is_rejected(self):
        answers = [(socket.AF_INET, 1, 6, '', ('1.1.1.1',443)), (socket.AF_INET,1,6,'',('127.0.0.1',443))]
        with patch.object(r.socket, 'getaddrinfo', return_value=answers), self.assertRaises(ValueError):
            r.resolve_public('https://example.org/')

    def test_legacy_numeric_hosts_are_rejected(self):
        for host in ['0x7f.0.0.1', '0x7f.1', '127.0x0.1', '0x08080808', '0x8.8.8.8']:
            with self.subTest(host=host), self.assertRaises(ValueError):
                r.url_parts('https://' + host + '/')

    def test_failed_dns_consumes_request_budget(self):
        budget = [0]
        with patch.object(r.socket, 'getaddrinfo', side_effect=socket.gaierror('fixture DNS failure')) as dns:
            for _ in range(20):
                with self.assertRaises(socket.gaierror):
                    r.broker_get('https://missing.example/', budget)
            with self.assertRaisesRegex(ValueError, 'request limit'):
                r.broker_get('https://missing.example/', budget)
        self.assertEqual(dns.call_count, 20)
        self.assertEqual(budget, [20])

    def test_internal_entries_require_activation_first(self):
        for args in [['--hop', 'https://example.org/', '1.1.1.1', '0'], ['--worker', '/tmp/arbitrary', '0', '1', '2', 'report']]:
            with patch.object(sys, 'argv', [str(SCRIPT), *args]), patch.object(r, 'verify_active', side_effect=ValueError('inactive')) as gate, patch.object(r, 'worker') as worker, patch.object(r, 'hop') as hop, self.assertRaisesRegex(ValueError, 'inactive'):
                r.main()
            gate.assert_called_once()
            worker.assert_not_called()
            hop.assert_not_called()

    def test_controller_rejects_unapproved_bootstrap(self):
        with patch.object(r, 'VERIFIER', '/unapproved/python'), self.assertRaisesRegex(ValueError, 'fixed runner Python'):
            r.require_bootstrap()

    def test_remote_markdown_cannot_embed_images_or_html(self):
        spec = importlib.util.spec_from_file_location('fetch_fixture', SCRIPT.with_name('fetch.py'))
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        parser = module._TextExtractor('https://example.org/')
        parser.feed('<p>&lt;img src=http://127.0.0.1/x&gt; ![x](https://example.org/x)</p><a href="https://example.org/a)![x](b">&lt;b&gt; [title]</a>')
        text = parser.text()
        self.assertNotIn('<img', text)
        self.assertNotIn('![x]', text)
        self.assertIn('&lt;img', text)
        self.assertIn('%29', text)
        for control in ['\x9b', '\u202e', '\u2028']:
            self.assertIsNone(module.md_href('https://example.org/' + control))

    def test_internal_topic_binding(self):
        with topic() as (p, fd, chain), patch.object(r, 'TOPICS', p.parent):
            r.validate_worker_topic(p, fd)
            with self.assertRaises(ValueError):
                r.validate_worker_topic(p.parent / 'elsewhere' / 'topic', fd)
            other = p.parent / 'other'; other.mkdir(mode=0o700)
            with self.assertRaisesRegex(ValueError, 'descriptor differs'):
                r.validate_worker_topic(other, fd)

    def test_sandbox_failure_stops_before_adapter_load(self):
        with patch.object(r, 'limits'), patch.object(r, 'apply_sandbox', side_effect=RuntimeError('sandbox unavailable')), patch.object(r.importlib.util, 'spec_from_file_location') as loader, self.assertRaisesRegex(RuntimeError, 'sandbox unavailable'):
            r.worker('/tmp/fixture', -1, -1, -1, 'report', [])
        loader.assert_not_called()

    def test_redirect_is_checked_before_connection(self):
        response = {'status':302,'location':'http://127.0.0.1/','content_type':'','body':''}
        with patch.object(r, 'resolve_public', return_value='1.1.1.1') as dns, patch.object(r,'one_hop',return_value=response) as hop, self.assertRaises(ValueError):
            r.broker_get('https://example.org/', [0])
        self.assertEqual(hop.call_count,1)
        self.assertEqual(dns.call_count,1)

    def test_origin_redirect_and_request_budget(self):
        response = {'status':302,'location':'https://other.example/','content_type':'','body':''}
        with patch.object(r,'resolve_public',return_value='1.1.1.1'), patch.object(r,'one_hop',return_value=response) as hop, self.assertRaises(ValueError):
            r.broker_get('https://api.openalex.org/works',[0],'https://api.openalex.org')
        self.assertEqual(hop.call_count,1)
        with self.assertRaises(ValueError):
            r.broker_get('https://example.org/',[20])

    def test_strict_json_and_frame_limits(self):
        for raw in ['{"x":1,"x":2}', '{"x":NaN}']:
            with self.assertRaises(ValueError): r.strict_json(raw)
        for payload in [struct.pack('!I',r.MAX_FRAME+1),struct.pack('!I',10)+b'{}']:
            rd,wr=os.pipe()
            try:
                os.write(wr,payload);os.close(wr);wr=None
                with self.assertRaises(ValueError):r.frame_read(rd)
            finally:
                os.close(rd)
                if wr is not None:os.close(wr)

    def test_http_input_counts_chunk_framing(self):
        wire = b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n' + b'1\r\nx\r\n' * 200 + b'0\r\n\r\n'
        stream = r.HttpInput(io.BytesIO(wire))
        with patch.object(r, 'MAX_BODY', 512), self.assertRaisesRegex(ValueError, 'HTTP input byte limit'):
            io.BufferedReader(stream).read()

    def test_untrusted_links_and_terminal_controls(self):
        spec = importlib.util.spec_from_file_location('watch_fixture', SCRIPT.with_name('watch.py'))
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        for control in ['\x9b', '\u202e', '\u2028']:
            self.assertEqual(module.md_link('https://example.org/' + control + 'x'), '')
            self.assertNotIn(control, r.terminal_text('fixture' + control))

    def test_atomic_write_preserves_external_hardlink_inode(self):
        with topic() as (p,fd,chain):
            external=p.parent/'external';external.write_text('CANARY')
            os.link(external,p/'result')
            r.safe_write(p/'result','NEW')
            self.assertEqual(external.read_text(),'CANARY')
            self.assertEqual((p/'result').read_text(),'NEW')
            self.assertEqual((p/'result').stat().st_nlink,1)

    def test_atomic_failure_keeps_previous_output(self):
        with topic() as (p,fd,chain):
            target=p/'result';target.write_text('OLD')
            with patch.object(r.os,'replace',side_effect=OSError('fixture failure')),self.assertRaises(OSError):
                r.safe_write(target,'NEW')
            self.assertEqual(target.read_text(),'OLD')
            self.assertEqual([x.name for x in p.iterdir()],['result'])

    def test_unsafe_entries_and_ancestor_swap(self):
        with topic() as (p,fd,chain):
            (p/'link').symlink_to('/etc/passwd')
            with self.assertRaises(ValueError):r.topic_usage(fd)
            (p/'link').unlink();external=p.parent/'external';external.write_text('CANARY');os.link(external,p/'hard')
            with self.assertRaises(ValueError):r.topic_usage(fd)
            (p/'hard').unlink();p.rename(p.with_name('moved'));p.mkdir(mode=0o700)
            with self.assertRaises(ValueError):r.check_chain(chain)

    def test_size_and_count_limits(self):
        with topic() as (p,fd,chain):
            (p/'large').write_bytes(b'12345')
            with patch.object(r,'MAX_TOPIC',4),self.assertRaises(ValueError):r.topic_usage(fd)
            with patch.object(r,'MAX_FILE',4),self.assertRaisesRegex(ValueError,'file size limit'):r.topic_usage(fd)
            with patch.object(r,'MAX_FILES',0),self.assertRaises(ValueError):r.topic_usage(fd)

    def test_real_worker_fetch_watch_chain_and_report(self):
        page = b'<html><body><h1>Public fixture</h1><p>' + b'Primary source. '*120 + b'</p></body></html>'
        feed = b'<rss><channel><item><title>Public update</title><link>https://example.org/post</link><guid>item1</guid><pubDate>Mon, 19 Oct 2026 12:00:00 GMT</pubDate><description>Original words</description></item></channel></rss>'
        work={'id':'https://openalex.org/W1','display_name':'Fixture paper','publication_year':2026,'cited_by_count':1,'doi':'https://doi.org/10.1/fixture','best_oa_location':{}}
        def get(url,budget,origin=None):
            budget[0]+=1
            if 'api.openalex.org' in url:body,ctype=json.dumps({'results':[work]}).encode(),'application/json'
            elif 'feed' in url:body,ctype=feed,'application/rss+xml'
            else:body,ctype=page,'text/html; charset=utf-8'
            return {'body':base64.b64encode(body).decode(),'content_type':ctype,'url':url}
        def fixture_spawn(arguments, pass_fds=()):
            # Trusted test bootstrap exercises the OS worker without a runtime profile.
            proc = subprocess.Popen([sys.executable, '-I', '-S', '-B', __file__, '--fixture-worker', *arguments[1:]], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=r.clean_env(), close_fds=True, pass_fds=pass_fds, start_new_session=True, cwd='/')
            with r.CHILD_LOCK: r.CHILDREN.add(proc)
            return proc
        with topic() as (p,fd,chain),patch.object(r,'broker_get',side_effect=get),patch.object(r, 'spawn', side_effect=fixture_spawn):
            self.assertEqual(r.run_worker(p,fd,chain,'put',[],{'name':'map.md','text':'# Public fixture\n'}),0)
            self.assertEqual((p/'map.md').read_text(),'# Public fixture\n')
            self.assertNotEqual(r.run_worker(p,fd,chain,'put',[],{'name':'../outside','text':'rejected'}),0)
            self.assertNotEqual(r.run_worker(p,fd,chain,'put',[],{'name':'extracts.json','text':'{"x":1,"x":2}'}),0)
            for cmd,args in [('fetch',['primary','https://example.org/page']),('chain',['find','Fixture paper']),('watch',['add','https://example.org/feed']),('watch',['list']),('watch',['check'])]:
                with self.subTest(command=cmd,args=args):self.assertEqual(r.run_worker(p,fd,chain,cmd,args),0)
            self.assertTrue((p/'sources/primary.md').exists());self.assertTrue((p/'watch.tsv').exists());self.assertTrue(list((p/'watch').glob('*.md')))
            line=next(i for i,text in enumerate((p/'sources/primary.md').read_text().split('\n'),1) if 'Primary source.' in text)
            payload = json.dumps({'title':'Fixture <script>','question':'Where?','stopped':'claim located','claims':[{'claim':'Primary words','status':'付いた','quotes':[{'file':'primary.md','line':line,'text':'Primary source.'}]}]})
            self.assertEqual(r.run_worker(p,fd,chain,'put',[],{'name':'extracts.json','text':payload}),0)
            self.assertEqual(r.run_worker(p,fd,chain,'report',[]),0)
            html=(p/'report.html').read_text();self.assertIn('Content-Security-Policy',html);self.assertNotIn('<script>',html)
            (p/'extracts.json').write_text((p/'extracts.json').read_text().replace('Primary source.','Invented quotation.'))
            self.assertNotEqual(r.run_worker(p,fd,chain,'report',[]),0)
            self.assertEqual((p/'report.html').read_text(),html)

    def test_broker_output_flood_is_bounded_and_reaped(self):
        proc = subprocess.Popen([sys.executable, '-I', '-S', '-B', '-c', 'import os,time; os.write(1,b"X"*(2*1024*1024)); time.sleep(10)'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        try:
            with patch.object(r, 'MAX_FRAME', 65536), self.assertRaisesRegex(ValueError, 'output limit'):
                r.bounded_output(proc)
        finally:
            r.terminate(proc)
        self.assertIsNotNone(proc.returncode)

    def test_watchdog_wall_and_memory_kill_and_reap(self):
        for kind in ['wall', 'memory']:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                record = Path(temp) / 'pid'
                result = subprocess.run([sys.executable, '-I', '-S', '-B', __file__, '--fixture-watchdog', kind, str(record)], capture_output=True, timeout=8)
                self.assertEqual(result.returncode, 1)
                self.assertIn((kind + '-time limit' if kind == 'wall' else 'memory limit').encode(), result.stderr)
                pid = int(record.read_text())
                with self.assertRaises(ProcessLookupError): os.kill(pid, 0)

if __name__=='__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--fixture-worker':
        raise SystemExit(r.worker(sys.argv[2], *(int(x) for x in sys.argv[3:6]), sys.argv[6], sys.argv[7:]))
    if len(sys.argv) > 1 and sys.argv[1] == '--fixture-watchdog':
        import threading
        import time
        proc = subprocess.Popen([sys.executable, '-I', '-S', '-B', '-c', 'import time; time.sleep(30)'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        r.CHILDREN.add(proc)
        Path(sys.argv[3]).write_text(str(proc.pid))
        if sys.argv[2] == 'memory': r.MAX_RSS = 1
        r.watchdog(threading.Event(), time.monotonic() + (0 if sys.argv[2] == 'wall' else 5))
        raise SystemExit(2)
    unittest.main()
