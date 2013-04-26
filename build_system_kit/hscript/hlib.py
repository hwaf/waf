#! /usr/bin/env python

import os, sys, imp
import yaml

from waflib import Context, Options, Configure, Utils, Logs

def options(opt):
	opt.load('compiler_c')

def configure(conf):
	conf.options = Options.options
	conf.load('compiler_c')


def build(bld):
    f = bld.path.find_node('hbuild')
    if not f:
        bld.fatal("no hbuild file")
        pass
    dct = yaml.load(open(f.abspath()))

    build_tgts = dct['build']

    for tgt_name, tgt_data in build_tgts.items():
        #Logs.info(">>> %s: %s" % (tgt_name, tgt_data))
        tgt_dct = dict(tgt_data)
        tgt_dct['target'] = tgt_data.get('target', tgt_name)
        tgt_dct['name'] = tgt_name
        tgt = bld(**tgt_dct)

def recurse_rep(x, y):
	f = getattr(Context.g_module, x.cmd or x.fun, Utils.nada)
	return f(x)

def start(cwd, version, wafdir):
	try:
		os.stat(cwd + os.sep + 'hbuild')
	except:
		print('call from a folder containing a file named "hbuild"')
		sys.exit(1)

	Logs.init_log()
	Context.waf_dir = wafdir
	Context.top_dir = Context.run_dir = Context.launch_dir = cwd
	Context.out_dir = os.path.join(cwd, 'build')
	Context.g_module = imp.new_module('wscript')
	Context.g_module.root_path = os.path.join(cwd, 'hbuild')
	Context.Context.recurse = recurse_rep

	# this is a fake module, which looks like a standard wscript file
	Context.g_module.options = options
	Context.g_module.configure = configure
	Context.g_module.build = build

	Options.OptionsContext().execute()

	do_config = 'configure' in sys.argv
	do_build = len(sys.argv) == 1 or 'build' in sys.argv
	try:
		os.stat(Context.out_dir)
	except:
		do_config = True
	if do_config:
		Context.create_context('configure').execute()

	if 'clean' in sys.argv:
		Context.create_context('clean').execute()
	if do_build:
		Context.create_context('build').execute()
