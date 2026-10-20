#!/usr/bin/env python3
"""Run the pinned imozuru adapters with separate public-GET and offline sandboxes."""
import base64
import ctypes
import http.client
import importlib.util
import io
import ipaddress
import json
import os
from pathlib import Path
import re
import resource
import select
import signal
import socket
import ssl
import stat
import struct
import subprocess
import sys
import sysconfig
import tempfile
import threading
import time
import unicodedata
import urllib.parse

PACKAGE = Path(__file__).resolve().parent.parent
SELF = Path(__file__).resolve()
MAX_BODY = 8 * 1024 * 1024
MAX_FRAME = 14 * 1024 * 1024
MAX_OUTPUT = 1024 * 1024
MAX_TOPIC = 64 * 1024 * 1024
MAX_FILES = 256
MAX_FILE = 16 * 1024 * 1024
MAX_RSS = 256 * 1024 * 1024
WALL_SECONDS = 90
MAX_REQUESTS = 20
PROFILE_ID = "marycache-imozuru-2026-10"
VERIFIER = '/Users/yoshiki/.local/share/skill-governance/runtime/pyyaml-6.0.2/bin/python'
TOPICS = Path('/Users/yoshiki/.local/share/imozuru/topics')
CHILDREN = set()
CHILD_LOCK = threading.Lock()
STOPPING = False


def strict_json(data):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError("duplicate JSON key")
            out[k] = v
        return out
    def constant(_):
        raise ValueError("non-finite JSON number")
    return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)


def public_ip(value):
    ip = ipaddress.ip_address(value)
    if not ip.is_global or '%' in value:
        raise ValueError("private, local, or reserved address")
    if ip.version == 6:
        transitions = ("::/96", "64:ff9b::/96", "64:ff9b:1::/48", "2001::/32", "2002::/16")
        if ip.ipv4_mapped or any(ip in ipaddress.ip_network(n) for n in transitions):
            raise ValueError("IPv6 transition address")
    return str(ip)


def url_parts(url):
    if not isinstance(url, str) or not 1 <= len(url) <= 4096:
        raise ValueError("invalid URL size")
    if '\\' in url or any(c.isspace() or unicodedata.category(c) in {'Cc', 'Cf'} for c in url):
        raise ValueError("URL contains whitespace or control characters")
    p = urllib.parse.urlsplit(url)
    if p.scheme not in {'http', 'https'} or not p.hostname or '@' in p.netloc or '%' in p.netloc:
        raise ValueError("only unauthenticated HTTP(S) URLs are allowed")
    port = p.port or (443 if p.scheme == 'https' else 80)
    if port != (443 if p.scheme == 'https' else 80):
        raise ValueError("non-standard port")
    host = p.hostname
    if not host.isascii() or host.endswith('.'):
        raise ValueError("ambiguous hostname")
    try:
        public_ip(host)
    except ValueError:
        try:
            socket.inet_aton(host)
        except OSError:
            pass
        else:
            raise ValueError('ambiguous numeric hostname')
        if ':' in host or re.fullmatch(r'[0-9.]+|0[xX][0-9a-fA-F]+', host):
            raise ValueError("non-public or ambiguous numeric hostname")
        if not re.fullmatch(r'(?=.{1,253}$)[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?', host):
            raise ValueError("invalid hostname")
        if any(not label or len(label) > 63 or label.startswith('-') or label.endswith('-') for label in host.split('.')):
            raise ValueError("invalid DNS label")
    sensitive = {'token', 'access_token', 'api_key', 'apikey', 'password', 'authorization', 'secret'}
    if any(k.lower() in sensitive for k, _ in urllib.parse.parse_qsl(p.query)):
        raise ValueError("credential query parameter")
    return p, host, port


def resolve_public(url):
    _, host, port = url_parts(url)
    answers = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    addresses = {public_ip(answer[4][0]) for answer in answers}
    if not addresses:
        raise ValueError("DNS returned no addresses")
    return sorted(addresses, key=lambda s: (':' in s, s))[0]


def sb_string(value):
    return json.dumps(str(value), ensure_ascii=True)


def sandbox_profile(topic=None):
    readable = {str(Path(sysconfig.get_path('stdlib')).resolve()), '/System/Library', '/usr/lib', '/private/var/db/timezone'}
    literals = {'/dev/null', '/dev/urandom', '/dev/random', '/private/etc/localtime'}
    if topic:
        readable.add(str(topic))
        readable.add(str(SELF.parent))
    clauses = [f'(subpath {sb_string(p)})' for p in sorted(readable)]
    clauses += [f'(literal {sb_string(p)})' for p in sorted(literals)]
    profile = '(version 1)\n(allow default)\n'
    profile += '(deny file-read* (require-not (require-any ' + ' '.join(clauses) + ')))\n'
    if topic:
        profile += f'(deny file-write* (require-not (subpath {sb_string(topic)})))\n'
    else:
        profile += '(deny file-write*)\n'
    profile += '(deny process-fork)\n(deny process-exec)\n(deny mach-lookup)\n(deny system-socket)\n'
    profile += '(deny network*)\n'
    return profile


def apply_sandbox(profile):
    if sys.platform != 'darwin':
        raise RuntimeError("this restricted profile requires macOS")
    library = ctypes.CDLL('/usr/lib/libsandbox.dylib')
    library.sandbox_init.argtypes = [ctypes.c_char_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_char_p)]
    library.sandbox_init.restype = ctypes.c_int
    error = ctypes.c_char_p()
    result = library.sandbox_init(profile.encode(), 0, ctypes.byref(error))
    if result != 0 or error.value:
        reason = error.value.decode(errors='replace') if error.value else str(result)
        raise RuntimeError('sandbox_init failed: ' + reason)


def limits():
    for kind, amount in ((resource.RLIMIT_CPU, 30), (resource.RLIMIT_FSIZE, MAX_FILE), (resource.RLIMIT_NOFILE, 64), (resource.RLIMIT_CORE, 0)):
        resource.setrlimit(kind, (amount, amount))


def clean_env():
    return {'HOME': '/nonexistent', 'XDG_CONFIG_HOME': '/nonexistent', 'XDG_CACHE_HOME': '/nonexistent', 'PATH': '', 'LANG': 'en_US.UTF-8', 'LC_ALL': 'en_US.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'}


def frame_write(fd, value):
    data = json.dumps(value, ensure_ascii=True, separators=(',', ':'), allow_nan=False).encode()
    if len(data) > MAX_FRAME:
        raise ValueError("IPC frame limit")
    data = struct.pack('!I', len(data)) + data
    while data:
        count = os.write(fd, data)
        data = data[count:]


def read_exact(fd, size):
    chunks = []
    while size:
        data = os.read(fd, min(size, 65536))
        if not data:
            raise ValueError("truncated IPC frame")
        chunks.append(data)
        size -= len(data)
    return b''.join(chunks)


def frame_read(fd):
    size = struct.unpack('!I', read_exact(fd, 4))[0]
    if not 0 < size <= MAX_FRAME:
        raise ValueError("IPC frame limit")
    return strict_json(read_exact(fd, size))


class HttpInput(io.RawIOBase):
    """Count raw HTTP response bytes, including headers and chunk framing."""
    def __init__(self, stream):
        self.stream, self.received = stream, 0

    def readable(self):
        return True

    def readinto(self, target):
        data = self.stream.read(min(len(target), MAX_BODY - self.received + 1))
        self.received += len(data)
        if self.received > MAX_BODY:
            raise ValueError('HTTP input byte limit')
        target[:len(data)] = data
        return len(data)

    def close(self):
        self.stream.close()
        super().close()


class HttpSocket:
    def __init__(self, sock):
        self.sock = sock

    def __getattr__(self, name):
        return getattr(self.sock, name)

    def makefile(self, mode):
        if mode != 'rb':
            raise ValueError('unexpected HTTP stream mode')
        return io.BufferedReader(HttpInput(self.sock.makefile('rb', buffering=0)))


def hop(url, ip, connected_fd):
    p, host, port = url_parts(url)
    ip = public_ip(ip)
    context = ssl.create_default_context(cafile='/etc/ssl/cert.pem')
    sock = socket.socket(fileno=connected_fd)
    if public_ip(sock.getpeername()[0]) != ip or sock.getpeername()[1] != port:
        raise ValueError('inherited socket has the wrong peer')
    http.client._MAXLINE, http.client._MAXHEADERS = 8192, 32
    limits()
    apply_sandbox(sandbox_profile())
    if p.scheme == 'https':
        conn = http.client.HTTPSConnection(host, port, timeout=10, context=context)
    else:
        conn = http.client.HTTPConnection(host, port, timeout=10)
    used = False
    def pinned(address, timeout, source_address=None):
        nonlocal used
        if used:
            raise ValueError('connection reuse is disabled')
        used = True
        sock.settimeout(timeout)
        if public_ip(sock.getpeername()[0]) != ip or sock.getpeername()[1] != port:
            raise ValueError('peer address differs from pinned DNS address')
        return sock
    conn._create_connection = pinned
    target = urllib.parse.quote(p.path or '/', safe="/%:@!$&'()*+,;=~")
    if p.query:
        target += '?' + urllib.parse.quote(p.query, safe="=&%/:+?@!$'()*,;~")
    try:
        conn.connect()
        conn.sock = HttpSocket(conn.sock)
        conn.request('GET', target, headers={'User-Agent': 'imozuru-restricted/1', 'Accept-Encoding': 'identity', 'Connection': 'close'})
        response = conn.getresponse()
        if response.headers.get('Content-Encoding', 'identity').lower() != 'identity':
            raise ValueError("encoded response is not permitted")
        location = response.headers.get('Location', '')
        if response.status in {301, 302, 303, 307, 308}:
            body = b''
        elif 200 <= response.status < 300:
            if response.length is not None and response.length > MAX_BODY:
                raise ValueError("response length limit")
            body = response.read(MAX_BODY + 1)
            if len(body) > MAX_BODY or (response.length is not None and response.length > 0):
                raise ValueError("response too large or truncated")
        else:
            raise ValueError('HTTP status ' + str(response.status))
        return {'status': response.status, 'location': location, 'content_type': response.headers.get('Content-Type', ''), 'body': base64.b64encode(body).decode('ascii')}
    finally:
        conn.close()


def terminate(proc):
    if proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    proc.wait(timeout=2)
    proc.stdout.close()
    proc.stderr.close()
    with CHILD_LOCK:
        CHILDREN.discard(proc)


def spawn(arguments, pass_fds=()):
    with CHILD_LOCK:
        if STOPPING:
            raise RuntimeError('execution is stopping')
        proc = subprocess.Popen([VERIFIER, '-I', '-S', '-B', str(SELF), *arguments], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=clean_env(), close_fds=True, pass_fds=pass_fds, start_new_session=True, cwd='/')
        CHILDREN.add(proc)
        return proc


def bounded_output(proc, seconds=15):
    streams = {proc.stdout.fileno(): bytearray(), proc.stderr.fileno(): bytearray()}
    watched, deadline = list(streams), time.monotonic() + seconds
    while watched:
        if time.monotonic() >= deadline:
            raise ValueError('broker wall-time limit')
        ready, _, _ = select.select(watched, [], [], 0.1)
        for fd in ready:
            data = os.read(fd, 65536)
            if not data:
                watched.remove(fd)
            else:
                streams[fd].extend(data)
                limit = MAX_FRAME if fd == proc.stdout.fileno() else MAX_OUTPUT
                if len(streams[fd]) > limit:
                    raise ValueError('broker output limit')
    proc.wait(timeout=2)
    return bytes(streams[proc.stdout.fileno()]), bytes(streams[proc.stderr.fileno()])


def one_hop(url, ip):
    _, _, port = url_parts(url)
    ip = public_ip(ip)
    sock = socket.socket(socket.AF_INET6 if ':' in ip else socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(10)
        sock.connect((ip, port))
        if public_ip(sock.getpeername()[0]) != ip or sock.getpeername()[1] != port:
            raise ValueError('connection peer differs from the pinned address')
        proc = spawn(['--hop', url, ip, str(sock.fileno())], (sock.fileno(),))
    finally:
        sock.close()
    try:
        out, err = bounded_output(proc)
        if proc.returncode:
            raise ValueError('public GET failed: ' + err.decode(errors='replace')[:300])
        value = strict_json(out)
        if not isinstance(value, dict) or set(value) != {'status', 'location', 'content_type', 'body'}:
            raise ValueError("invalid broker response")
        if type(value['status']) is not int or not all(isinstance(value[k], str) for k in ('location', 'content_type', 'body')):
            raise ValueError('invalid broker field types')
        return value
    finally:
        terminate(proc)


def broker_get(url, budget, origin=None):
    first, _, _ = url_parts(url)
    for redirect in range(6):
        if budget[0] >= MAX_REQUESTS:
            raise ValueError("request limit")
        p, _, _ = url_parts(url)
        if first.scheme == 'https' and p.scheme != 'https':
            raise ValueError("HTTPS downgrade")
        if origin and (p.scheme + '://' + p.netloc) != origin:
            raise ValueError("redirect leaves the required origin")
        budget[0] += 1
        ip = resolve_public(url)
        value = one_hop(url, ip)
        if value['status'] in {301, 302, 303, 307, 308}:
            if redirect == 5 or not value['location']:
                raise ValueError("redirect limit or missing location")
            url = urllib.parse.urljoin(url, value['location'])
            continue
        body = base64.b64decode(value['body'], validate=True)
        if len(body) > MAX_BODY:
            raise ValueError("body limit")
        return {'body': value['body'], 'content_type': value['content_type'], 'url': url}
    raise ValueError("redirect limit")


def directory_fd(path, create=False):
    path = Path(path)
    if not path.is_absolute():
        raise ValueError("directory must be absolute")
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    chain = []
    try:
        for name in path.parts[1:]:
            if name in {'', '.', '..'}:
                raise ValueError("unsafe path component")
            try:
                new = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(name, 0o700, dir_fd=fd)
                new = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            info = os.fstat(new)
            chain.append((fd, name, info.st_dev, info.st_ino))
            fd = new
        return fd, chain
    except BaseException:
        for parent, _, _, _ in chain:
            os.close(parent)
        os.close(fd)
        raise


def check_chain(chain):
    for parent, name, device, inode in chain:
        info = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISDIR(info.st_mode) or (info.st_dev, info.st_ino) != (device, inode):
            raise ValueError("topic ancestor changed")


def topic_usage(fd):
    total, count = 0, 0
    for name in os.listdir(fd):
        info = os.stat(name, dir_fd=fd, follow_symlinks=False)
        if info.st_uid != os.getuid():
            raise ValueError("foreign-owned topic entry")
        if stat.S_ISDIR(info.st_mode):
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            try:
                sub, n = topic_usage(child)
            finally:
                os.close(child)
            total += sub
            count += n + 1
        elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
            if info.st_size > MAX_FILE:
                raise ValueError('topic file size limit')
            total += info.st_size
            count += 1
        else:
            raise ValueError("symlink, hardlink or special topic entry")
        if total > MAX_TOPIC or count > MAX_FILES:
            raise ValueError("topic storage limit")
    return total, count


def safe_write(path, text):
    """Create our own inode and publish it without truncating existing inodes."""
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise ValueError('unsafe temporary output')
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            fd = None
            stream.write(text)
        published = os.stat(temporary, follow_symlinks=False)
        if not stat.S_ISREG(published.st_mode) or published.st_uid != os.getuid() or published.st_nlink != 1 or (published.st_dev, published.st_ino) != (info.st_dev, info.st_ino):
            raise ValueError('output changed before publication')
        os.replace(temporary, path)
    finally:
        if fd is not None:
            os.close(fd)
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


class TaskInfo(ctypes.Structure):
    _fields_ = [('virtual_size', ctypes.c_uint64), ('resident_size', ctypes.c_uint64), ('other', ctypes.c_uint64 * 10)]


def resident_bytes(pid):
    library = ctypes.CDLL('/usr/lib/libproc.dylib')
    info = TaskInfo()
    size = library.proc_pidinfo(pid, 4, 0, ctypes.byref(info), ctypes.sizeof(info))
    if size <= 0:
        raise RuntimeError("cannot measure worker memory")
    return info.resident_size


def watchdog(stop, deadline):
    global STOPPING
    while not stop.wait(0.1):
        reason = 'wall-time limit' if time.monotonic() >= deadline else None
        with CHILD_LOCK:
            processes = list(CHILDREN)
        for proc in processes:
            if proc.poll() is None:
                try:
                    if resident_bytes(proc.pid) > MAX_RSS:
                        reason = 'memory limit'
                except RuntimeError:
                    if proc.poll() is None:
                        reason = 'memory monitor failed'
        if reason:
            with CHILD_LOCK:
                STOPPING = True
                processes = list(CHILDREN)
            for proc in processes:
                terminate(proc)
            os.write(2, ('imozuru: ' + reason + '\n').encode())
            os._exit(1)


def worker(topic, topic_fd, read_fd, write_fd, command, args):
    limits()
    apply_sandbox(sandbox_profile(topic=topic))
    os.fchdir(topic_fd)
    os.umask(0o077)
    if command == 'put':
        value = frame_read(read_fd)
        if not isinstance(value, dict) or set(value) != {'name', 'text'} or value['name'] not in {'map.md', 'log.md', 'extracts.json'} or not isinstance(value['text'], str) or len(value['text'].encode()) > MAX_OUTPUT:
            raise ValueError('invalid topic input')
        if value['name'] == 'extracts.json':
            strict_json(value['text'])
        safe_write(value['name'], value['text'])
        return 0
    def request(url, origin=None):
        frame_write(write_fd, {'url': url, 'origin': origin})
        reply = frame_read(read_fd)
        if not isinstance(reply, dict) or set(reply) not in ({'body', 'content_type', 'url'}, {'error'}):
            raise ValueError("invalid response frame")
        if 'error' in reply:
            raise ValueError(reply['error'])
        return base64.b64decode(reply['body'], validate=True), reply['content_type'], reply['url']
    name = {'fetch': 'fetch', 'chain': 'chain', 'watch': 'watch', 'report': 'report'}[command]
    spec = importlib.util.spec_from_file_location('imozuru_' + name, PACKAGE / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module._broker_get = request
    module._safe_write = safe_write
    if command == 'fetch':
        forwarded = ['sources', *args]
    elif command == 'chain':
        forwarded = args
    elif command == 'watch':
        if not args or args[0] not in {'add', 'list', 'check'}:
            raise ValueError("invalid watch command")
        forwarded = [args[0], '.', *args[1:]]
    else:
        if any(arg != '--check' for arg in args):
            raise ValueError("invalid report argument")
        forwarded = ['.', *args]
    sys.argv = [name + '.py', *forwarded]
    return module.main() or 0


def terminal_text(value):
    return ''.join(('\\u%04x' % ord(c)) if unicodedata.category(c) in {'Cc', 'Cf', 'Zl', 'Zp'} and c not in '\n\t' else c for c in value)


def run_worker(topic, fd, chain, command, args, payload=None):
    to_child_r, to_child_w = os.pipe()
    from_child_r, from_child_w = os.pipe()
    proc = spawn(['--worker', str(topic), str(fd), str(to_child_r), str(from_child_w), command, *args], (fd, to_child_r, from_child_w))
    os.close(to_child_r)
    os.close(from_child_w)
    pending, output, errors = bytearray(), bytearray(), bytearray()
    streams = {proc.stdout.fileno(): output, proc.stderr.fileno(): errors}
    watched = [from_child_r, *streams]
    start, budget = time.monotonic(), [0]
    stop = threading.Event()
    monitor = threading.Thread(target=watchdog, args=(stop, start + WALL_SECONDS), daemon=True)
    monitor.start()
    try:
        if payload is not None:
            frame_write(to_child_w, payload)
        while watched:
            if time.monotonic() - start > WALL_SECONDS:
                raise ValueError("worker wall-time limit")
            check_chain(chain)
            topic_usage(fd)
            readable, _, _ = select.select(watched, [], [], 0.1)
            for stream in readable:
                data = os.read(stream, 65536)
                if not data:
                    watched.remove(stream)
                    continue
                if stream in streams:
                    streams[stream].extend(data)
                    if len(streams[stream]) > MAX_OUTPUT:
                        raise ValueError("worker output limit")
                    continue
                pending.extend(data)
                if len(pending) > MAX_FRAME:
                    raise ValueError("IPC frame limit")
                if len(pending) < 4:
                    continue
                size = struct.unpack('!I', pending[:4])[0]
                if not 0 < size <= 8192:
                    raise ValueError("invalid request frame size")
                if len(pending) < size + 4:
                    continue
                if len(pending) != size + 4:
                    raise ValueError("extra request frame bytes")
                request = strict_json(pending[4:])
                pending.clear()
                if not isinstance(request, dict) or set(request) != {'url', 'origin'} or not isinstance(request['url'], str) or request['origin'] not in (None, 'https://api.openalex.org'):
                    raise ValueError("invalid request schema")
                try:
                    reply = broker_get(request['url'], budget, request['origin'])
                except (OSError, ValueError, RuntimeError) as error:
                    reply = {'error': str(error)[:500]}
                frame_write(to_child_w, reply)
        if pending:
            raise ValueError("truncated request frame")
        proc.wait(timeout=2)
        output = terminal_text(output.decode('utf-8', errors='replace')).encode()
        errors = terminal_text(errors.decode('utf-8', errors='replace')).encode()
        if max(len(output), len(errors)) > MAX_OUTPUT:
            raise ValueError('sanitized worker output limit')
        sys.stdout.buffer.write(output)
        sys.stderr.buffer.write(errors)
        check_chain(chain)
        topic_usage(fd)
        return proc.returncode
    finally:
        stop.set()
        monitor.join(timeout=1)
        terminate(proc)
        os.close(to_child_w)
        os.close(from_child_r)


def verify_active():
    governance = PACKAGE.parent / 'skill-governance'
    profile = strict_json((governance / 'restricted-profiles' / PROFILE_ID / 'profile.json').read_bytes())
    if profile.get('verifier', {}).get('python_path') != VERIFIER:
        raise ValueError('unexpected governance interpreter')
    environment = clean_env()
    environment['HOME'] = str(TOPICS.parents[3])
    environment['PATH'] = '/usr/bin:/bin'
    result = subprocess.run([VERIFIER, '-I', '-B', str(governance / 'scripts/governance.py'), 'restricted-audit', '--phase', 'active', '--json', '--require-capability', '--summary'], stdin=subprocess.DEVNULL, capture_output=True, env=environment, timeout=60, close_fds=True)
    state = strict_json(result.stdout)
    if result.returncode or state.get('capability_scope') != 'imozuru-public-source-v1' or state.get('capability_status') != 'active':
        raise ValueError("restricted activation is not valid; run restricted-audit")


def validate_worker_topic(topic, supplied_fd):
    path = Path(topic)
    if path.parent != TOPICS or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', path.name):
        raise ValueError('internal topic must be a fixed private topic')
    fd, chain = directory_fd(path)
    try:
        info, supplied = os.fstat(fd), os.fstat(supplied_fd)
        if (info.st_dev, info.st_ino) != (supplied.st_dev, supplied.st_ino):
            raise ValueError('internal topic descriptor differs from fixed topic')
        if not stat.S_ISDIR(supplied.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError('internal topic must be private and owned by the current user')
        check_chain(chain)
        topic_usage(fd)
    finally:
        for parent, _, _, _ in chain:
            os.close(parent)
        os.close(fd)


def require_bootstrap():
    if str(Path(sys.executable).absolute()) != VERIFIER or not sys.flags.isolated or not sys.flags.no_site or not sys.dont_write_bytecode:
        raise ValueError('use the fixed runner Python with -I -S -B')


def main():
    require_bootstrap()
    if len(sys.argv) > 1 and sys.argv[1] == '--hop':
        if len(sys.argv) != 5:
            raise ValueError("invalid internal broker invocation")
        verify_active()
        value = hop(sys.argv[2], sys.argv[3], int(sys.argv[4]))
        sys.stdout.write(json.dumps(value, separators=(',', ':'), allow_nan=False))
        return 0
    if len(sys.argv) > 1 and sys.argv[1] == '--worker':
        if len(sys.argv) < 7:
            raise ValueError("invalid internal worker invocation")
        verify_active()
        validate_worker_topic(sys.argv[2], int(sys.argv[3]))
        return worker(sys.argv[2], *(int(x) for x in sys.argv[3:6]), sys.argv[6], sys.argv[7:])
    if len(sys.argv) < 3 or sys.argv[2] not in {'init', 'put', 'fetch', 'chain', 'watch', 'report'}:
        print('Usage: run.py <topic-name> init|put|fetch|chain|watch|report [arguments]')
        return 2
    slug, command = sys.argv[1:3]
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', slug):
        raise ValueError("topic must be a single safe name")
    verify_active()
    topic = TOPICS / slug
    fd, chain = directory_fd(topic, create=(command == 'init'))
    try:
        info = os.fstat(fd)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError("topic must be private and owned by the current user")
        check_chain(chain)
        topic_usage(fd)
        if command == 'init':
            print(str(topic))
            return 0
        if command == 'put':
            if len(sys.argv) != 4 or sys.argv[3] not in {'map.md', 'log.md', 'extracts.json'}:
                raise ValueError('put requires map.md, log.md or extracts.json')
            content = sys.stdin.buffer.read(MAX_OUTPUT + 1)
            if len(content) > MAX_OUTPUT:
                raise ValueError('topic input size limit')
            return run_worker(topic, fd, chain, command, [], {'name':sys.argv[3], 'text':content.decode('utf-8')})
        return run_worker(topic, fd, chain, command, sys.argv[3:])
    finally:
        for parent, _, _, _ in chain:
            os.close(parent)
        os.close(fd)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print('imozuru: ' + terminal_text(str(error)), file=sys.stderr)
        raise SystemExit(1)
