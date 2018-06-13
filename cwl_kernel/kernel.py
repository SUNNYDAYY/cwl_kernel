import cwltool
import cwltool.factory
import argparse
import cwltool.argparser
import sys
import six

import os
from cwltool import load_tool, workflow
from cwltool.executors import SingleJobExecutor
from typing import Callable
from cwltool.argparser import arg_parser, generate_parser, DEFAULT_TMP_PREFIX
from cwltool.main import main
from cwltool.load_tool import (FetcherConstructorType, resolve_tool_uri,
                        fetch_document, make_tool, validate_document, jobloaderctx,
                        resolve_overrides, load_overrides)
from cwltool.resolver import ga4gh_tool_registries, tool_resolver
from cwltool.stdfsaccess import StdFsAccess
from cwltool.main import init_job_order, load_job_order



from ipykernel.kernelbase import Kernel


class cwl_kernel(Kernel):

    implementation = 'cwl_kernel'
    implementation_version = '1.0'
    language = 'python'
    language_version = '3'
    language_info = {
        'name': 'python',
        'mimetype': 'text/plain',
        'version':'3'
    }

    banner = "cwlKernel"
    CWLFILEPATH = None

    def cwlengine(self,argslist):

        fetcher_constructor = None
        resolver = tool_resolver
        overrides = []
        executor = SingleJobExecutor()
        make_fs_access = StdFsAccess

        argslist = argslist
        args = arg_parser().parse_args(argslist)

        make_tool_kwds = vars(args)
        uri, tool_file_uri = resolve_tool_uri(args.workflow,
                                              resolver=resolver,
                                              fetcher_constructor=fetcher_constructor)
        stdin = sys.stdin
        job_order_object, input_basedir, jobloader = load_job_order(args,
                                                                    stdin,
                                                                    fetcher_constructor,
                                                                    overrides,
                                                                    tool_file_uri)

        document_loader, workflowobj, uri = fetch_document(uri, resolver=resolver,
                                                           fetcher_constructor=fetcher_constructor)
        try:
            document_loader, avsc_names, processobj, metadata, uri \
                = validate_document(document_loader, workflowobj, uri,
                                    enable_dev=args.enable_dev, strict=args.strict,
                                    preprocess_only=args.print_pre or args.pack,
                                    fetcher_constructor=fetcher_constructor,
                                    skip_schemas=args.skip_schemas,
                                    overrides=overrides)
        except Exception as e:
            return str(e)

        makeTool = workflow.defaultMakeTool
        setattr(args, 'overrides', [])

        tool = make_tool(document_loader, avsc_names, metadata, uri,
                         makeTool, kwargs=make_tool_kwds)
        setattr(args, 'basedir', args.outdir)
        try:
            job_order_object = init_job_order(job_order_object, args, tool,
                                              print_input_deps=args.print_input_deps,
                                              relative_deps=args.relative_deps,
                                              stdout=sys.stdout,
                                              make_fs_access=make_fs_access,
                                              loader=jobloader,
                                              input_basedir=input_basedir
                                              )

        except SystemExit as e:
            return str(e)
        del args.job_order
        del args.workflow
        (out, status) = executor(tool, job_order_object,
                                 logger=None,
                                 makeTool=makeTool,
                                 select_resources=None,
                                 make_fs_access=make_fs_access,
                                 secret_store={},
                                 **vars(args))
        return out



    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):

        sys.argv[1] = None
        sys.stderr = sys.__stderr__
        code = code.encode('unicode-escape').decode('string_escape')
        inputfield = code.split()
        out = None
        if os.path.splitext(inputfield[0])[1] == '.cwl' and self.CWLFILEPATH:
            self.CWLFILEPATH = None
        if self.CWLFILEPATH:
            if os.path.splitext(inputfield[0])[1] in [".yaml", ".json"]:
                out = self.cwlengine(inputfield)
                if isinstance(out,dict):
                    self.CWLFILEPATH = None
                else:
                    argslist = [self.CWLFILEPATH]
                    argslist.extend(inputfield)
                    out = self.cwlengine(argslist)
            else:
                argslist = [self.CWLFILEPATH]
                argslist.extend(inputfield)
                out = self.cwlengine(argslist)
        else:
            houzhui = os.path.splitext(inputfield[0])[1]
            if len(inputfield)==1 :
                if os.path.splitext(inputfield[0])[1] == '.cwl':
                    out = self.cwlengine(inputfield)
                    if out == "2":
                        self.CWLFILEPATH = inputfield[0]
                        out = "require data file"
                elif os.path.splitext(inputfield[0])[1] in [".yaml",".json"]:
                    out = self.cwlengine(inputfield)
                else:
                    self.send_response(self.iopub_socket, 'stream', 'cwl, json, yaml files are required.')
            else:
                out = self.cwlengine(inputfield)

        if isinstance(out,dict):
            outputname = out.keys()[0]
            if isinstance(out[outputname],dict):
                outputpath = out[outputname]['location'][7:]
                with open(outputpath) as file_object:
                    contents = file_object.read()
            else:
                contents = out[outputname]
        else:
            contents = out
        stream_content = {'name': 'stdout', 'text': contents}
        self.send_response(self.iopub_socket, 'stream', stream_content)

        return {'status': 'ok',
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
                }



