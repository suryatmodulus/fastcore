# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/02_utils.ipynb (unless otherwise specified).

__all__ = ['ifnone', 'maybe_attr', 'basic_repr', 'get_class', 'mk_class', 'wrap_class', 'ignore_exceptions', 'dict2obj',
           'store_attr', 'attrdict', 'properties', 'camel2snake', 'snake2camel', 'class2attr', 'hasattrs', 'ShowPrint',
           'Int', 'Str', 'Float', 'tuplify', 'detuplify', 'replicate', 'uniqueify', 'setify', 'merge', 'is_listy',
           'range_of', 'groupby', 'first', 'last_index', 'shufflish', 'IterLen', 'ReindexCollection', 'num_methods',
           'rnum_methods', 'inum_methods', 'fastuple', 'Inf', 'in_', 'lt', 'gt', 'le', 'ge', 'eq', 'ne', 'add', 'sub',
           'mul', 'truediv', 'is_', 'is_not', 'in_', 'true', 'stop', 'gen', 'chunked', 'trace', 'compose', 'maps',
           'partialler', 'mapped', 'instantiate', 'using_attr', 'Self', 'Self', 'remove_patches_path', 'bunzip',
           'join_path_file', 'urlread', 'urljson', 'run_proc', 'do_request', 'sort_by_run', 'PrettyString',
           'round_multiple', 'even_mults', 'num_cpus', 'add_props', 'ContextManagers', 'set_num_threads',
           'ProcessPoolExecutor', 'parallel', 'run_procs', 'parallel_gen']

# Cell
from .imports import *
from .foundation import *
from functools import wraps

import mimetypes,bz2,pickle,random,json,urllib,subprocess
from contextlib import contextmanager
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode

# Cell
def ifnone(a, b):
    "`b` if `a` is None else `a`"
    return b if a is None else a

# Cell
def maybe_attr(o, attr):
    "`getattr(o,attr,o)`"
    return getattr(o,attr,o)

# Cell
def basic_repr(flds=None):
    if isinstance(flds, str): flds = re.split(', *', flds)
    flds = L(flds)
    def _f(self):
        sig = ', '.join(f'{o}={maybe_attr(getattr(self,o), "__name__")}' for o in flds)
        return f'{self.__class__.__name__}({sig})'
    return _f

# Cell
def get_class(nm, *fld_names, sup=None, doc=None, funcs=None, **flds):
    "Dynamically create a class, optionally inheriting from `sup`, containing `fld_names`"
    attrs = {}
    for f in fld_names: attrs[f] = None
    for f in L(funcs): attrs[f.__name__] = f
    for k,v in flds.items(): attrs[k] = v
    sup = ifnone(sup, ())
    if not isinstance(sup, tuple): sup=(sup,)

    def _init(self, *args, **kwargs):
        for i,v in enumerate(args): setattr(self, list(attrs.keys())[i], v)
        for k,v in kwargs.items(): setattr(self,k,v)

    all_flds = [*fld_names,*flds.keys()]
    def _eq(self,b):
        return all([getattr(self,k)==getattr(b,k) for k in all_flds])

    if not sup: attrs['__repr__'] = basic_repr(all_flds)
    attrs['__init__'] = _init
    attrs['__eq__'] = _eq
    res = type(nm, sup, attrs)
    if doc is not None: res.__doc__ = doc
    return res

# Cell
def mk_class(nm, *fld_names, sup=None, doc=None, funcs=None, mod=None, **flds):
    "Create a class using `get_class` and add to the caller's module"
    if mod is None: mod = sys._getframe(1).f_locals
    res = get_class(nm, *fld_names, sup=sup, doc=doc, funcs=funcs, **flds)
    mod[nm] = res

# Cell
def wrap_class(nm, *fld_names, sup=None, doc=None, funcs=None, **flds):
    "Decorator: makes function a method of a new class `nm` passing parameters to `mk_class`"
    def _inner(f):
        mk_class(nm, *fld_names, sup=sup, doc=doc, funcs=L(funcs)+f, mod=f.__globals__, **flds)
        return f
    return _inner

# Cell
class ignore_exceptions:
    "Context manager to ignore exceptions"
    def __enter__(self): pass
    def __exit__(self, *args): return True

# Cell
def dict2obj(d):
    "Convert (possibly nested) dicts (or lists of dicts) to `SimpleNamespace`"
    if isinstance(d, (L,list)): return L(d).map(dict2obj)
    if not isinstance(d, dict): return d
    return SimpleNamespace(**{k:dict2obj(v) for k,v in d.items()})

# Cell
def _store_attr(self, **attrs):
    for n,v in attrs.items():
        setattr(self, n, v)
        self.__stored_args__[n] = v

# Cell
def store_attr(names=None, self=None, but=None, **attrs):
    "Store params named in comma-separated `names` from calling context into attrs in `self`"
    fr = sys._getframe(1)
    args = fr.f_code.co_varnames[:fr.f_code.co_argcount]
    if self: args = ('self', *args)
    else: self = fr.f_locals[args[0]]
    if not hasattr(self, '__stored_args__'): self.__stored_args__ = {}
    if attrs: return _store_attr(self, **attrs)
    ns = re.split(', *', names) if names else args[1:]
    _store_attr(self, **{n:fr.f_locals[n] for n in ns if n not in L(but)})

# Cell
def attrdict(o, *ks):
    "Dict from each `k` in `ks` to `getattr(o,k)`"
    return {k:getattr(o,k) for k in ks}

# Cell
def properties(cls, *ps):
    "Change attrs in `cls` with names in `ps` to properties"
    for p in ps: setattr(cls,p,property(getattr(cls,p)))

# Cell
_camel_re1 = re.compile('(.)([A-Z][a-z]+)')
_camel_re2 = re.compile('([a-z0-9])([A-Z])')

# Cell
def camel2snake(name):
    "Convert CamelCase to snake_case"
    s1   = re.sub(_camel_re1, r'\1_\2', name)
    return re.sub(_camel_re2, r'\1_\2', s1).lower()

# Cell
def snake2camel(s):
    "Convert snake_case to CamelCase"
    return ''.join(s.title().split('_'))

# Cell
def class2attr(self, cls_name):
    "Return the snake-cased name of the class.  Additionally, remove the substring `cls_name` only if it is a substring at the **end** of the string."
    return camel2snake(re.sub(rf'{cls_name}$', '', self.__class__.__name__) or cls_name.lower())


# Cell
def hasattrs(o,attrs):
    "Test whether `o` contains all `attrs`"
    return all(hasattr(o,attr) for attr in attrs)

# Cell
#hide
class ShowPrint:
    "Base class that prints for `show`"
    def show(self, *args, **kwargs): print(str(self))

# Cell
#hide
class Int(int,ShowPrint): pass

# Cell
#hide
class Str(str,ShowPrint): pass
class Float(float,ShowPrint): pass
add_docs(Str, "An extensible `str`");
add_docs(Int, "An extensible `int`");
add_docs(Float, "An extensible `float`")

# Cell
def tuplify(o, use_list=False, match=None):
    "Make `o` a tuple"
    return tuple(L(o, use_list=use_list, match=match))

# Cell
def detuplify(x):
    "If `x` is a tuple with one thing, extract it"
    return None if len(x)==0 else x[0] if len(x)==1 and getattr(x, 'ndim', 1)==1 else x

# Cell
def replicate(item,match):
    "Create tuple of `item` copied `len(match)` times"
    return (item,)*len(match)

# Cell
def uniqueify(x, sort=False, bidir=False, start=None):
    "Return the unique elements in `x`, optionally `sort`-ed, optionally return the reverse correspondence, optionally prepended with a list or tuple of elements."
    res = L(x).unique()
    if start is not None: res = start+res
    if sort: res.sort()
    if bidir: return res, res.val2idx()
    return res

# Cell
def setify(o):
    "Turn any list like-object into a set."
    return o if isinstance(o,set) else set(L(o))

# Cell
def merge(*ds):
    "Merge all dictionaries in `ds`"
    return {k:v for d in ds if d is not None for k,v in d.items()}

# Cell
def is_listy(x):
    "`isinstance(x, (tuple,list,L,slice,Generator))`"
    return isinstance(x, (tuple,list,L,slice,Generator))

# Cell
def range_of(x):
    "All indices of collection `x` (i.e. `list(range(len(x)))`)"
    return list(range(len(x)))

# Cell
def groupby(x, key):
    "Like `itertools.groupby` but doesn't need to be sorted, and isn't lazy"
    res = {}
    for o in x: res.setdefault(key(o), []).append(o)
    return res

# Cell
def first(x):
    "First element of `x`, or None if missing"
    try: return next(iter(x))
    except StopIteration: return None

# Cell
def last_index(x, o):
    "Finds the last index of occurence of `x` in `o` (returns -1 if no occurence)"
    try: return next(i for i in reversed(range(len(o))) if o[i] == x)
    except StopIteration: return -1

# Cell
def shufflish(x, pct=0.04):
    "Randomly relocate items of `x` up to `pct` of `len(x)` from their starting location"
    n = len(x)
    return L(x[i] for i in sorted(range_of(x), key=lambda o: o+n*(1+random.random()*pct)))

# Cell
#hide
class IterLen:
    "Base class to add iteration to anything supporting `__len__` and `__getitem__`"
    def __iter__(self): return (self[i] for i in range_of(self))

# Cell
@docs
class ReindexCollection(GetAttr, IterLen):
    "Reindexes collection `coll` with indices `idxs` and optional LRU cache of size `cache`"
    _default='coll'
    def __init__(self, coll, idxs=None, cache=None, tfm=noop):
        if idxs is None: idxs = L.range(coll)
        store_attr()
        if cache is not None: self._get = functools.lru_cache(maxsize=cache)(self._get)

    def _get(self, i): return self.tfm(self.coll[i])
    def __getitem__(self, i): return self._get(self.idxs[i])
    def __len__(self): return len(self.coll)
    def reindex(self, idxs): self.idxs = idxs
    def shuffle(self): random.shuffle(self.idxs)
    def cache_clear(self): self._get.cache_clear()
    def __getstate__(self): return {'coll': self.coll, 'idxs': self.idxs, 'cache': self.cache, 'tfm': self.tfm}
    def __setstate__(self, s): self.coll,self.idxs,self.cache,self.tfm = s['coll'],s['idxs'],s['cache'],s['tfm']

    _docs = dict(reindex="Replace `self.idxs` with idxs",
                shuffle="Randomly shuffle indices",
                cache_clear="Clear LRU cache")

# Cell
num_methods = """
    __add__ __sub__ __mul__ __matmul__ __truediv__ __floordiv__ __mod__ __divmod__ __pow__
    __lshift__ __rshift__ __and__ __xor__ __or__ __neg__ __pos__ __abs__
""".split()
rnum_methods = """
    __radd__ __rsub__ __rmul__ __rmatmul__ __rtruediv__ __rfloordiv__ __rmod__ __rdivmod__
    __rpow__ __rlshift__ __rrshift__ __rand__ __rxor__ __ror__
""".split()
inum_methods = """
    __iadd__ __isub__ __imul__ __imatmul__ __itruediv__
    __ifloordiv__ __imod__ __ipow__ __ilshift__ __irshift__ __iand__ __ixor__ __ior__
""".split()

# Cell
class fastuple(tuple):
    "A `tuple` with elementwise ops and more friendly __init__ behavior"
    def __new__(cls, x=None, *rest):
        if x is None: x = ()
        if not isinstance(x,tuple):
            if len(rest): x = (x,)
            else:
                try: x = tuple(iter(x))
                except TypeError: x = (x,)
        return super().__new__(cls, x+rest if rest else x)

    def _op(self,op,*args):
        if not isinstance(self,fastuple): self = fastuple(self)
        return type(self)(map(op,self,*map(cycle, args)))

    def mul(self,*args):
        "`*` is already defined in `tuple` for replicating, so use `mul` instead"
        return fastuple._op(self, operator.mul,*args)

    def add(self,*args):
        "`+` is already defined in `tuple` for concat, so use `add` instead"
        return fastuple._op(self, operator.add,*args)

def _get_op(op):
    if isinstance(op,str): op = getattr(operator,op)
    def _f(self,*args): return self._op(op,*args)
    return _f

for n in num_methods:
    if not hasattr(fastuple, n) and hasattr(operator,n): setattr(fastuple,n,_get_op(n))

for n in 'eq ne lt le gt ge'.split(): setattr(fastuple,n,_get_op(n))
setattr(fastuple,'__invert__',_get_op('__not__'))
setattr(fastuple,'max',_get_op(max))
setattr(fastuple,'min',_get_op(min))

# Cell
#hide
class _InfMeta(type):
    @property
    def count(self): return itertools.count()
    @property
    def zeros(self): return itertools.cycle([0])
    @property
    def ones(self):  return itertools.cycle([1])
    @property
    def nones(self): return itertools.cycle([None])

# Cell
class Inf(metaclass=_InfMeta):
    "Infinite lists"
    pass

# Cell
def _oper(op,a,b=float('nan')): return (lambda o:op(o,a)) if b!=b else op(a,b)

def _mk_op(nm, mod):
    "Create an operator using `oper` and add to the caller's module"
    op = getattr(operator,nm)
    def _inner(a,b=float('nan')): return _oper(op, a,b)
    _inner.__name__ = _inner.__qualname__ = nm
    _inner.__doc__ = f'Same as `operator.{nm}`, or returns partial if 1 arg'
    mod[nm] = _inner

# Cell
def in_(x, a):
    "`True` if `x in a`"
    return x in a

operator.in_ = in_

# Cell
#nbdev_comment _all_ = ['lt','gt','le','ge','eq','ne','add','sub','mul','truediv','is_','is_not','in_']

# Cell
for op in ['lt','gt','le','ge','eq','ne','add','sub','mul','truediv','is_','is_not','in_']: _mk_op(op, globals())

# Cell
def true(*args, **kwargs):
    "Predicate: always `True`"
    return True

# Cell
def stop(e=StopIteration):
    "Raises exception `e` (by default `StopException`) even if in an expression"
    raise e

# Cell
def gen(func, seq, cond=true):
    "Like `(func(o) for o in seq if cond(func(o)))` but handles `StopIteration`"
    return itertools.takewhile(cond, map(func,seq))

# Cell
def chunked(it, chunk_sz=None, drop_last=False, n_chunks=None):
    "Return batches from iterator `it` of size `chunk_sz` (or return `n_chunks` total)"
    assert bool(chunk_sz) ^ bool(n_chunks)
    if n_chunks: chunk_sz = math.ceil(len(it)/n_chunks)
    if not isinstance(it, Iterator): it = iter(it)
    while True:
        res = list(itertools.islice(it, chunk_sz))
        if res and (len(res)==chunk_sz or not drop_last): yield res
        if len(res)<chunk_sz: return

# Cell
def trace(f):
    "Add `set_trace` to an existing function `f`"
    def _inner(*args,**kwargs):
        set_trace()
        return f(*args,**kwargs)
    return _inner

# Cell
def compose(*funcs, order=None):
    "Create a function that composes all functions in `funcs`, passing along remaining `*args` and `**kwargs` to all"
    funcs = L(funcs)
    if len(funcs)==0: return noop
    if len(funcs)==1: return funcs[0]
    if order is not None: funcs = funcs.sorted(order)
    def _inner(x, *args, **kwargs):
        for f in L(funcs): x = f(x, *args, **kwargs)
        return x
    return _inner

# Cell
def maps(*args, retain=noop):
    "Like `map`, except funcs are composed first"
    f = compose(*args[:-1])
    def _f(b): return retain(f(b), b)
    return map(_f, args[-1])

# Cell
def partialler(f, *args, order=None, **kwargs):
    "Like `functools.partial` but also copies over docstring"
    fnew = partial(f,*args,**kwargs)
    fnew.__doc__ = f.__doc__
    if order is not None: fnew.order=order
    elif hasattr(f,'order'): fnew.order=f.order
    return fnew

# Cell
def mapped(f, it):
    "map `f` over `it`, unless it's not listy, in which case return `f(it)`"
    return L(it).map(f) if is_listy(it) else f(it)

# Cell
def instantiate(t):
    "Instantiate `t` if it's a type, otherwise do nothing"
    return t() if isinstance(t, type) else t

# Cell
def _using_attr(f, attr, x): return f(getattr(x,attr))

# Cell
def using_attr(f, attr):
    "Change function `f` to operate on `attr`"
    return partial(_using_attr, f, attr)

# Cell
class _Self:
    "An alternative to `lambda` for calling methods on passed object."
    def __init__(self): self.nms,self.args,self.kwargs,self.ready = [],[],[],True
    def __repr__(self): return f'self: {self.nms}({self.args}, {self.kwargs})'

    def __call__(self, *args, **kwargs):
        if self.ready:
            x = args[0]
            for n,a,k in zip(self.nms,self.args,self.kwargs):
                x = getattr(x,n)
                if callable(x) and a is not None: x = x(*a, **k)
            return x
        else:
            self.args.append(args)
            self.kwargs.append(kwargs)
            self.ready = True
            return self

    def __getattr__(self,k):
        if not self.ready:
            self.args.append(None)
            self.kwargs.append(None)
        self.nms.append(k)
        self.ready = False
        return self

# Cell
class _SelfCls:
    def __getattr__(self,k): return getattr(_Self(),k)
    def __getitem__(self,i): return self.__getattr__('__getitem__')(i)

Self = _SelfCls()

# Cell
#nbdev_comment _all_ = ['Self']

# Cell
@patch
def readlines(self:Path, hint=-1, encoding='utf8'):
    "Read the content of `fname`"
    with self.open(encoding=encoding) as f: return f.readlines(hint)

# Cell
@patch
def read(self:Path, size=-1, encoding='utf8'):
    "Read the content of `fname`"
    with self.open(encoding=encoding) as f: return f.read(size)

# Cell
@patch
def write(self:Path, txt, encoding='utf8'):
    "Write `txt` to `self`, creating directories as needed"
    self.parent.mkdir(parents=True,exist_ok=True)
    with self.open('w', encoding=encoding) as f: f.write(txt)

# Cell
@patch
def save(fn:Path, o):
    "Save a pickle file, to a file name or opened file"
    if not isinstance(fn, io.IOBase): fn = open(fn,'wb')
    try: pickle.dump(o, fn)
    finally: fn.close()

# Cell
@patch
def load(fn:Path):
    "Load a pickle file from a file name or opened file"
    if not isinstance(fn, io.IOBase): fn = open(fn,'rb')
    try: return pickle.load(fn)
    finally: fn.close()

# Cell
@patch
def ls(self:Path, n_max=None, file_type=None, file_exts=None):
    "Contents of path as a list"
    extns=L(file_exts)
    if file_type: extns += L(k for k,v in mimetypes.types_map.items() if v.startswith(file_type+'/'))
    has_extns = len(extns)==0
    res = (o for o in self.iterdir() if has_extns or o.suffix in extns)
    if n_max is not None: res = itertools.islice(res, n_max)
    return L(res)

# Cell
@patch
def __repr__(self:Path):
    b = getattr(Path, 'BASE_PATH', None)
    if b:
        try: self = self.relative_to(b)
        except: pass
    return f"Path({self.as_posix()!r})"

# Cell
_patched = ['read', 'readlines', 'write', 'save', 'load', 'ls']

@contextmanager
def remove_patches_path():
    "A context manager for disabling Path extensions."
    patches = L(getattr(Path, n) for n in _patched)
    try:
        for n in _patched: delattr(Path, n)
        yield
    finally:
        for (n, f) in zip(_patched, patches): setattr(Path, n, f)

# Cell
def bunzip(fn):
    "bunzip `fn`, raising exception if output already exists"
    fn = Path(fn)
    assert fn.exists(), f"{fn} doesn't exist"
    out_fn = fn.with_suffix('')
    assert not out_fn.exists(), f"{out_fn} already exists"
    with bz2.BZ2File(fn, 'rb') as src, out_fn.open('wb') as dst:
        for d in iter(lambda: src.read(1024*1024), b''): dst.write(d)

# Cell
def join_path_file(file, path, ext=''):
    "Return `path/file` if file is a string or a `Path`, file otherwise"
    if not isinstance(file, (str, Path)): return file
    path.mkdir(parents=True, exist_ok=True)
    return path/f'{file}{ext}'

# Cell
def urlread(url):
    "Retrieve `url`"
    with urlopen(url) as res: return res.read()

# Cell
def urljson(url):
    "Retrieve `url` and decode json"
    return json.loads(urlread(url))

# Cell
def run_proc(*args):
    "Pass `args` to `subprocess.run`, returning `stdout`, or raise `IOError` on failure"
    res = subprocess.run(args, capture_output=True)
    if res.returncode: raise IOError("{} ;; {}".format(res.stdout, res.stderr))
    return res.stdout

# Cell
def do_request(url, post=False, headers=None, **data):
    "Call GET or json-encoded POST on `url`, depending on `post`"
    if data:
        if post: data = json.dumps(data).encode('ascii')
        else:
            url += "?" + urlencode(data)
            data = None
    return urljson(Request(url, headers=headers, data=data or None))

# Cell
def _is_instance(f, gs):
    tst = [g if type(g) in [type, 'function'] else g.__class__ for g in gs]
    for g in tst:
        if isinstance(f, g) or f==g: return True
    return False

def _is_first(f, gs):
    for o in L(getattr(f, 'run_after', None)):
        if _is_instance(o, gs): return False
    for g in gs:
        if _is_instance(f, L(getattr(g, 'run_before', None))): return False
    return True

def sort_by_run(fs):
    end = L(fs).attrgot('toward_end')
    inp,res = L(fs)[~end] + L(fs)[end], L()
    while len(inp):
        for i,o in enumerate(inp):
            if _is_first(o, inp):
                res.append(inp.pop(i))
                break
        else: raise Exception("Impossible to sort")
    return res

# Cell
class PrettyString(str):
    "Little hack to get strings to show properly in Jupyter."
    def __repr__(self): return self

# Cell
def round_multiple(x, mult, round_down=False):
    "Round `x` to nearest multiple of `mult`"
    def _f(x_): return (int if round_down else round)(x_/mult)*mult
    res = L(x).map(_f)
    return res if is_listy(x) else res[0]

# Cell
def even_mults(start, stop, n):
    "Build log-stepped array from `start` to `stop` in `n` steps."
    if n==1: return stop
    mult = stop/start
    step = mult**(1/(n-1))
    return [start*(step**i) for i in range(n)]

# Cell
def num_cpus():
    "Get number of cpus"
    try:                   return len(os.sched_getaffinity(0))
    except AttributeError: return os.cpu_count()

defaults.cpus = num_cpus()

# Cell
def add_props(f, g=None, n=2):
    "Create properties passing each of `range(n)` to f"
    if g is None: return (property(partial(f,i)) for i in range(n))
    return (property(partial(f,i), partial(g,i)) for i in range(n))

# Cell
from contextlib import ExitStack

# Cell
class ContextManagers(GetAttr):
    "Wrapper for `contextlib.ExitStack` which enters a collection of context managers"
    def __init__(self, mgrs): self.default,self.stack = L(mgrs),ExitStack()
    def __enter__(self): self.default.map(self.stack.enter_context)
    def __exit__(self, *args, **kwargs): self.stack.__exit__(*args, **kwargs)

# Cell
from multiprocessing import Process, Queue
import concurrent.futures
import time
from multiprocessing import Manager

# Cell
def set_num_threads(nt):
    "Get numpy (and others) to use `nt` threads"
    try: import mkl; mkl.set_num_threads(nt)
    except: pass
    try: import torch; torch.set_num_threads(nt)
    except: pass
    os.environ['IPC_ENABLE']='1'
    for o in ['OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:
        os.environ[o] = str(nt)

# Cell
def _call(lock, pause, n, g, item):
    l = False
    if pause:
        try:
            l = lock.acquire(timeout=pause*(n+2))
            time.sleep(pause)
        finally:
            if l: lock.release()
    return g(item)

# Cell
class ProcessPoolExecutor(concurrent.futures.ProcessPoolExecutor):
    "Same as Python's ProcessPoolExecutor, except can pass `max_workers==0` for serial execution"
    def __init__(self, max_workers=defaults.cpus, on_exc=print, pause=0,
                 mp_context=None, initializer=None, initargs=(),):
        if max_workers is None: max_workers=defaults.cpus
        store_attr()
        self.not_parallel = max_workers==0
        if self.not_parallel: max_workers=1
        super().__init__(max_workers, mp_context=mp_context, initializer=initializer, initargs=initargs)

    def map(self, f, items, timeout=None, chunksize=1, *args, **kwargs):
        self.lock = Manager().Lock()
        g = partial(f, *args, **kwargs)
        if self.not_parallel: return map(g, items)
        _g = partial(_call, self.lock, self.pause, self.max_workers, g)
        try: return super().map(_g, items, timeout=timeout, chunksize=chunksize)
        except Exception as e: self.on_exc(e)

# Cell
try: from fastprogress import progress_bar
except: progress_bar = None

# Cell
def parallel(f, items, *args, n_workers=defaults.cpus, total=None, progress=None, pause=0,
             timeout=None, chunksize=1, **kwargs):
    "Applies `func` in parallel to `items`, using `n_workers`"
    if progress is None: progress = progress_bar is not None
    with ProcessPoolExecutor(n_workers, pause=pause) as ex:
        r = ex.map(f,items, *args, timeout=timeout, chunksize=chunksize, **kwargs)
        if progress:
            if total is None: total = len(items)
            r = progress_bar(r, total=total, leave=False)
        return L(r)

# Cell
def run_procs(f, f_done, args):
    "Call `f` for each item in `args` in parallel, yielding `f_done`"
    processes = L(args).map(Process, args=arg0, target=f)
    for o in processes: o.start()
    yield from f_done()
    processes.map(Self.join())

# Cell
def _f_pg(obj, queue, batch, start_idx):
    for i,b in enumerate(obj(batch)): queue.put((start_idx+i,b))

def _done_pg(queue, items): return (queue.get() for _ in items)

# Cell
def parallel_gen(cls, items, n_workers=defaults.cpus, **kwargs):
    "Instantiate `cls` in `n_workers` procs & call each on a subset of `items` in parallel."
    if n_workers==0:
        yield from enumerate(list(cls(**kwargs)(items)))
        return
    batches = L(chunked(items, n_chunks=n_workers))
    idx = L(itertools.accumulate(0 + batches.map(len)))
    queue = Queue()
    if progress_bar: items = progress_bar(items, leave=False)
    f=partial(_f_pg, cls(**kwargs), queue)
    done=partial(_done_pg, queue, items)
    yield from run_procs(f, done, L(batches,idx).zip())