#! /usr/bin/env python

import os, sys, imp
import yaml

from waflib import Context, Options, Configure, Utils, Logs
import waflib.Logs as msg

HSCRIPT = 'hbuild.yml'
# override waf default: 'wscript' -> HSCRIPT
Context.WSCRIPT_FILE = HSCRIPT

## replace the Context.load_module with this one, to translate HSCRIPT files
## into 'wscript' ones, on the fly.
def load_module(path):
    """
    Load a source file as a python module.

    :param path: file path
    :type path: string
    :return: Loaded Python module
    :rtype: module
    """
    cache_modules = Context.cache_modules
    try:
        return cache_modules[path]
    except KeyError:
        pass

    module = imp.new_module(Context.WSCRIPT_FILE)
    try:
        dct = yaml.load(open(path, 'rU'))
    except (IOError, OSError):
        raise Errors.WafError('Could not read the file %r' % path)

    module_dir = os.path.dirname(path)
    sys.path.insert(0, module_dir)

    ## translate the yaml code into python-waf code
    ## options
    code = gen_py_code(dct, path)
    exec(compile(code, path, 'exec'), module.__dict__)
    
    sys.path.remove(module_dir)

    cache_modules[path] = module

    return module
#Context.orig_load_module = Context.load_module
Context.load_module = load_module

def gen_py_code(dct, fname):
    """
    Generate a valid python code from a YAML dict
    """
    try:                from io import StringIO
    except ImportError: from cStringIO import StringIO
    buf = StringIO()

    from textwrap import dedent
    def _w(*args):
        return buf.write(dedent(*args))
    _w(
        '''\
        ## -*- python -*-
        # stdlib imports ----------------
        import os
        import os.path as osp

        # waf imports -------------------
        import waflib.Logs as msg

        # functions ---------------------
        def _hwaf_load_fct(ctx, pkgname, fname):
            import imp
            f = open(fname, 'r')
            mod_name = '.'.join(['__hwaf__']+pkgname.split('/')+f.name[:-3].split('/'))
            mod = imp.load_source(mod_name, f.name, f)
            f.close()
            return getattr(mod, ctx.fun)(ctx)
        '''
        )
    ## process project section
    ## TODO
    
    ## process package section
    if not 'package' in dct:
        raise Errors.WafError('Missing "package" section in file [%s]' % fname)
        pass
    
    _w(
        '''\
        PACKAGE = {
        \t"name": %(name)r,
        \t"authors": %(authors)r,
        }

        def pkg_deps(ctx):
        ''' % dct['package'],
        )
    pkgname = dct['package']['name']
    if 'deps' in dct['package']:
        pkgs = dct['package']['deps'].get('public', [])
        for pkg in pkgs:
            buf.write('\tctx.use_pkg(%r)\n' % pkg)
            pass
        pass
    buf.write('\treturn # pkg_deps\n\n')

    ## process options section
    if dct.get('options', None):
        _w(
            '''\
            def options(ctx):
            '''
            )
        tools = dct['options'].get('tools', [])
        for tool_name in tools:
            buf.write('\tctx.load(%r)\n' % tool_name)
            pass
        ## TODO: also allows to add option-flags ?
        ## ctx.options.add_opt(...)
        buf.write('\treturn # options\n\n')
        pass

    ## process configure section
    if dct.get('configure', None):
        _w(
            '''\
            def configure(ctx):
            \tmsg.debug("[configure] package name: %(name)s")
            ''' % dct['package']
            )
        # escape-hatch
        if 'hwaf-call' in dct['configure']:
            calls = dct['configure']['hwaf-call']
            for script in calls:
                buf.write('\t_hwaf_load_fct(ctx, %r, %r)\n' % (pkgname,script,))
                pass
            pass

        # load tools
        tools = dct['configure'].get('tools', [])
        for tool_name in tools:
            buf.write('\tctx.load(%r)\n' % tool_name)
            pass
        # TODO: env
        # TODO: export_tools
        buf.write('\treturn # configure\n\n')
        pass

    ## process build section
    if dct.get('build', None):
        _w(
            '''\
            def build(ctx):
            \tmsg.debug('[build] package name: %(name)s')
            ''' % dct['package'],
            )
        # escape-hatch
        if 'hwaf-call' in dct['build']:
            calls = dct['build']['hwaf-call']
            for script in calls:
                buf.write('\t_hwaf_load_fct(ctx, %r, %r)\n' % (pkgname,script,))
                pass
            pass

        # declare targets
        for tgt_name, tgt_data in dct['build'].items():
            if tgt_name.startswith('hwaf-'):
                continue
            tgt_dct = dict(tgt_data)
            tgt_dct['target'] = tgt_data.get('target', tgt_name)
            buf.write('\tctx(\n')
            for k, v in tgt_dct.items():
                buf.write('\t\t%s = %r,\n'% (k,v))
                pass
            buf.write('\t)# target: %s\n' % tgt_name)
            pass
        # TODO: install-scripts

        buf.write('\treturn # build\n\n')
        pass

    _w('## EOF ##\n')
    
    code = buf.getvalue()
    buf.close()
    if 1: msg.info("loading code:\n%s" % code)
    return code
