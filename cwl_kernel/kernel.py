import cwltool
import cwltool.factory
import argparse
import cwltool.argparser
import sys
from cwltool import load_tool, workflow
from cwltool.executors import SingleJobExecutor
from typing import Callable
from cwltool.argparser import arg_parser, generate_parser, DEFAULT_TMP_PREFIX



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


    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):

        sys.argv[1] = None
        sys.stderr = sys.__stderr__

        fac = cwltool.factory.Factory()
        echo = fac.make(code)
        result = echo(inp="foo")

        stream_content = {'name': 'stdout', 'text': result['out']}
        self.send_response(self.iopub_socket, 'stream', stream_content)

        return {'status': 'ok',
                # The base class increments the execution count
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
                }

