# -*- coding: utf-8 -*
import argparse
import codecs
import sys
import uuid


import six
import logging
import os
import pkg_resources
import functools
import datetime

import ruamel.yaml as yaml
import schema_salad.validate as validate
from cwltool import workflow
from cwltool import command_line_tool

from schema_salad.ref_resolver import Loader, file_uri, uri_file_path
from schema_salad.sourceline import strip_dup_lineno
from typing import Callable, cast, TextIO
from six import string_types

from cwltool.argparser import arg_parser, generate_parser, DEFAULT_TMP_PREFIX, get_default_args
from cwltool.cwlrdf import printdot, printrdf, gather
from cwltool.context import  LoadingContext, RuntimeContext, getdefault
from cwltool.errors import UnsupportedRequirement, WorkflowException
from cwltool.main import MultithreadedJobExecutor, SingleJobExecutor
from cwltool.load_tool import (FetcherConstructorType, resolve_tool_uri,
                        fetch_document, make_tool, validate_document, jobloaderctx,
                        resolve_overrides, load_overrides)
from cwltool.loghandler import defaultStreamHandler
from cwltool.mutation import MutationManager
from cwltool.pathmapper import (adjustDirObjs, trim_listing, visit_class)
from cwltool.process import (Process, normalizeFilesDirs,
                      scandeps, shortname, use_custom_schema,
                      use_standard_schema)
from cwltool.resolver import ga4gh_tool_registries, tool_resolver
from cwltool.software_requirements import (DependenciesConfiguration,
                                    get_container_from_software_requirements)
from cwltool.stdfsaccess import StdFsAccess
from cwltool.utils import onWindows, windows_default_container_id, json_dumps
from cwltool.main import supportedCWLversions, printdeps, find_default_container, generate_input_template, print_pack, versionstring,init_job_order, load_job_order
from cwltool.secrets import SecretStore
from cwltool.main import make_relative

from ipykernel.kernelbase import Kernel

_logger = logging.getLogger("cwltool")

def returndeps(obj,              # type: Optional[Mapping[Text, Any]]
              document_loader,  # type: Loader
              stdout,           # type: Union[TextIO, StreamWriter]
              relative_deps,    # type: bool
              uri,              # type: Text
              basedir=None      # type: Text
             ):  # type: (...) -> None
    """Print a JSON representation of the dependencies of the CWL document."""
    deps = {"class": "File", "location": uri}  # type: Dict[Text, Any]

    def loadref(base, uri):
        return document_loader.fetch(document_loader.fetcher.urljoin(base, uri))

    sfs = scandeps(
        basedir if basedir else uri, obj, {"$import", "run"},
        {"$include", "$schemas", "location"}, loadref)
    if sfs:
        deps["secondaryFiles"] = sfs

    if relative_deps:
        if relative_deps == "primary":
            base = basedir if basedir else os.path.dirname(uri_file_path(str(uri)))
        elif relative_deps == "cwd":
            base = os.getcwd()
        else:
            raise Exception(u"Unknown relative_deps %s" % relative_deps)

        visit_class(deps, ("File", "Directory"), functools.partial(make_relative, base))

    return json_dumps(deps, indent=4)


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
    VARIABLELIST = {}
    tempfilelist = []

    def cwlmain(self,
                argsl=None,  # type: List[str]
                args=None,  # type: argparse.Namespace
                job_order_object=None,  # type: MutableMapping[Text, Any]
                stdin=sys.stdin,  # type: IO[Any]
                stdout=None,  # type: Union[TextIO, codecs.StreamWriter]
                stderr=sys.stderr,  # type: IO[Any]
                versionfunc=versionstring,  # type: Callable[[], Text]
                logger_handler=None,  #
                custom_schema_callback=None,  # type: Callable[[], None]
                executor=None,  # type: Callable[..., Tuple[Dict[Text, Any], Text]]
                loadingContext=None,  # type: LoadingContext
                runtimeContext=None  # type: RuntimeContext
                ):  # type: (...) -> int

        if not stdout:
            stdout = codecs.getwriter('utf-8')(sys.stdout)
        _logger.removeHandler(defaultStreamHandler)
        if logger_handler:
            stderr_handler = logger_handler
        else:
            stderr_handler = logging.StreamHandler(stderr)
        _logger.addHandler(stderr_handler)
        try:
            if args is None:
                args = arg_parser().parse_args(argsl)
                if args.workflow and "--outdir" not in argsl:
                    outputPath = args.workflow.split('/')[-1].split('.')[0]
                    setattr(args,"outdir", os.getcwd()+"/"+outputPath+"/"+datetime.datetime.now().strftime('%Y-%m-%d-%H%M'))
            if runtimeContext is None:
                runtimeContext = RuntimeContext(vars(args))
            else:
                runtimeContext = runtimeContext.copy()

            rdflib_logger = logging.getLogger("rdflib.term")
            rdflib_logger.addHandler(stderr_handler)
            rdflib_logger.setLevel(logging.ERROR)
            if args.quiet:
                _logger.setLevel(logging.WARN)
            if runtimeContext.debug:
                _logger.setLevel(logging.DEBUG)
                rdflib_logger.setLevel(logging.DEBUG)
            if args.timestamps:
                formatter = logging.Formatter("[%(asctime)s] %(message)s",
                                              "%Y-%m-%d %H:%M:%S")
                stderr_handler.setFormatter(formatter)
            # version
            if args.version:
                return versionfunc(), 0
            else:
                _logger.info(versionfunc())

            if args.print_supported_versions:
                return "\n".join(supportedCWLversions(args.enable_dev)), 0

            if not args.workflow:
                if os.path.isfile("CWLFile"):
                    setattr(args, "workflow", "CWLFile")
                else:
                    _logger.error("")
                    _logger.error("CWL document required, no input file was provided")
                    arg_parser().print_help()
                    return "CWL document required, no input file was provided",1
            if args.relax_path_checks:
                command_line_tool.ACCEPTLIST_RE = command_line_tool.ACCEPTLIST_EN_RELAXED_RE

            if args.ga4gh_tool_registries:
                ga4gh_tool_registries[:] = args.ga4gh_tool_registries
            if not args.enable_ga4gh_tool_registry:
                del ga4gh_tool_registries[:]

            if custom_schema_callback:
                custom_schema_callback()
            elif args.enable_ext:
                res = pkg_resources.resource_stream(__name__, 'extensions.yml')
                use_custom_schema("v1.0", "http://commonwl.org/cwltool", res.read())
                res.close()
            else:
                use_standard_schema("v1.0")

            if loadingContext is None:
                loadingContext = LoadingContext(vars(args))
            else:
                loadingContext = loadingContext.copy()

            loadingContext.disable_js_validation = \
                args.disable_js_validation or (not args.do_validate)
            loadingContext.construct_tool_object = getdefault(loadingContext.construct_tool_object,
                                                              workflow.default_make_tool)
            loadingContext.resolver = getdefault(loadingContext.resolver, tool_resolver)
            try:
                uri, tool_file_uri = resolve_tool_uri(args.workflow,
                                                  resolver=loadingContext.resolver,
                                                  fetcher_constructor=loadingContext.fetcher_constructor)
            except:
                return "Can't find file "+ args.workflow, 0

            try_again_msg = "" if args.debug else ", try again with --debug for more information"

            try:
                job_order_object, input_basedir, jobloader = load_job_order(
                    args, stdin, loadingContext.fetcher_constructor,
                    loadingContext.overrides_list, tool_file_uri)

                if args.overrides:
                    loadingContext.overrides_list.extend(load_overrides(
                        file_uri(os.path.abspath(args.overrides)), tool_file_uri))


                document_loader, workflowobj, uri = fetch_document(
                    uri, resolver=loadingContext.resolver,
                    fetcher_constructor=loadingContext.fetcher_constructor)

                if args.print_deps:
                    # printdeps(workflowobj, document_loader, stdout, args.relative_deps, uri)
                    result = returndeps(workflowobj, document_loader, stdout, args.relative_deps, uri)
                    return result, 0

                document_loader, avsc_names, processobj, metadata, uri \
                    = validate_document(document_loader, workflowobj, uri,
                                        enable_dev=loadingContext.enable_dev,
                                        strict=loadingContext.strict,
                                        preprocess_only=(args.print_pre or args.pack),
                                        fetcher_constructor=loadingContext.fetcher_constructor,
                                        skip_schemas=args.skip_schemas,
                                        overrides=loadingContext.overrides_list,
                                        do_validate=loadingContext.do_validate)

                if args.print_pre:
                    # stdout.write(json_dumps(processobj, indent=4))
                    return json_dumps(processobj, indent=4), 0

                loadingContext.overrides_list.extend(metadata.get("cwltool:overrides", []))

                tool = make_tool(document_loader, avsc_names,
                                 metadata, uri, loadingContext)
                if args.make_template:
                    yaml.safe_dump(generate_input_template(tool), sys.stdout,
                                   default_flow_style=False, indent=4,
                                   block_seq_indent=2)
                    return yaml.safe_dump(generate_input_template(tool), indent=4), 0

                if args.validate:
                    _logger.info("Tool definition is valid")
                    return "Tool definition is valid", 0

                if args.pack:
                    stdout.write(print_pack(document_loader, processobj, uri, metadata))
                    return print_pack(document_loader, processobj, uri, metadata), 0

                if args.print_rdf:
                    stdout.write(printrdf(tool, document_loader.ctx, args.rdf_serializer))
                    return printrdf(tool, document_loader.ctx, args.rdf_serializer), 0

                if args.print_dot:
                    printdot(tool, document_loader.ctx, stdout)
                    return "args.print_dot still not solved",0

            except (validate.ValidationException) as exc:
                _logger.error(u"Tool definition failed validation:\n%s", exc,
                              exc_info=args.debug)
                infor = "Tool definition failed validation:\n%s"+exc+args.debug
                return infor,1
            except (RuntimeError, WorkflowException) as exc:
                _logger.error(u"Tool definition failed initialization:\n%s", exc,
                              exc_info=args.debug)
                infor = "Tool definition failed initialization:\n%s"+exc+args.debug
                return infor,1
            except Exception as exc:
                _logger.error(
                    u"I'm sorry, I couldn't load this CWL file%s.\nThe error was: %s",
                    try_again_msg,
                    exc if not args.debug else "",
                    exc_info=args.debug)
                return "I'm sorry, I couldn't load this CWL file",1

            if isinstance(tool, int):
                return tool, 0

            # If on MacOS platform, TMPDIR must be set to be under one of the
            # shared volumes in Docker for Mac
            # More info: https://dockstore.org/docs/faq
            if sys.platform == "darwin":
                default_mac_path = "/private/tmp/docker_tmp"
                if runtimeContext.tmp_outdir_prefix == DEFAULT_TMP_PREFIX:
                    runtimeContext.tmp_outdir_prefix = default_mac_path

            for dirprefix in ("tmpdir_prefix", "tmp_outdir_prefix", "cachedir"):
                if getattr(runtimeContext, dirprefix) and getattr(runtimeContext, dirprefix) != DEFAULT_TMP_PREFIX:
                    sl = "/" if getattr(runtimeContext, dirprefix).endswith("/") or dirprefix == "cachedir" \
                        else ""
                    setattr(runtimeContext, dirprefix,
                            os.path.abspath(getattr(runtimeContext, dirprefix)) + sl)
                    if not os.path.exists(os.path.dirname(getattr(runtimeContext, dirprefix))):
                        try:
                            os.makedirs(os.path.dirname(getattr(runtimeContext, dirprefix)))
                        except Exception as e:
                            _logger.error("Failed to create directory: %s", e)
                            infor = "Failed to create directory: %s"+e+""
                            return infor, 1

            if args.cachedir:
                if args.move_outputs == "move":
                    runtimeContext.move_outputs = "copy"
                runtimeContext.tmp_outdir_prefix = args.cachedir

            runtimeContext.secret_store = getdefault(runtimeContext.secret_store, SecretStore())

            try:
                initialized_job_order_object = init_job_order(job_order_object, args, tool,
                                                              jobloader, stdout,
                                                              print_input_deps=args.print_input_deps,
                                                              relative_deps=args.relative_deps,
                                                              input_basedir=input_basedir,
                                                              secret_store=runtimeContext.secret_store)
            except SystemExit as err:
                return err.code
            if not executor:
                if args.parallel:
                    executor = MultithreadedJobExecutor()
                else:
                    executor = SingleJobExecutor()
            assert executor is not None

            if isinstance(initialized_job_order_object, int):
                return initialized_job_order_object

            try:
                runtimeContext.basedir = input_basedir
                del args.workflow
                del args.job_order

                conf_file = getattr(args, "beta_dependency_resolvers_configuration", None)  # Text
                use_conda_dependencies = getattr(args, "beta_conda_dependencies", None)  # Text

                job_script_provider = None  # type: Optional[DependenciesConfiguration]
                if conf_file or use_conda_dependencies:
                    runtimeContext.job_script_provider = DependenciesConfiguration(args)

                runtimeContext.find_default_container = \
                    functools.partial(find_default_container, args)
                runtimeContext.make_fs_access = getdefault(runtimeContext.make_fs_access, StdFsAccess)


                (out, status) = executor(tool,
                                         initialized_job_order_object,
                                         runtimeContext,
                                         logger=_logger)
                # This is the workflow output, it needs to be written
                if out is not None:

                    def loc_to_path(obj):
                        for field in ("path", "nameext", "nameroot", "dirname"):
                            if field in obj:
                                del obj[field]
                        if obj["location"].startswith("file://"):
                            obj["path"] = uri_file_path(obj["location"])

                    visit_class(out, ("File", "Directory"), loc_to_path)

                    # Unsetting the Generation fron final output object
                    visit_class(out, ("File",), MutationManager().unset_generation)

                    if isinstance(out, string_types):
                        stdout.write(out)
                    else:
                        stdout.write(json_dumps(out, indent=4,  # type: ignore
                                                ensure_ascii=False))
                    stdout.write("\n")
                    if hasattr(stdout, "flush"):
                        stdout.flush()  # type: ignore

                if status != "success":
                    _logger.warning(u"Final process status is %s", status)
                    infor = "Final process status is %s"+status+""
                    return infor,1

                _logger.info(u"Final process status is %s", status)
                return out, status

            except (validate.ValidationException) as exc:
                _logger.error(u"Input object failed validation:\n%s", exc,
                              exc_info=args.debug)
                infor = "Input object failed validation:\n%s"+ exc + args.debug
                return infor, 1
            except UnsupportedRequirement as exc:
                _logger.error(
                    u"Workflow or tool uses unsupported feature:\n%s", exc,
                    exc_info=args.debug)
                infor = "Workflow or tool uses unsupported feature:\n%s"+exc+ args.debug
                return infor, 3
            except WorkflowException as exc:
                _logger.error(
                    u"Workflow error%s:\n%s", try_again_msg, strip_dup_lineno(six.text_type(exc)),
                    exc_info=args.debug)
                infor = "Workflow error%s:\n%s"+try_again_msg+strip_dup_lineno(six.text_type(exc))+args.debug
                return infor, 1
            except Exception as exc:
                _logger.error(
                    u"Unhandled error%s:\n  %s", try_again_msg, exc, exc_info=args.debug)
                infor = "Unhandled error%s:\n  %s" + try_again_msg + exc + args.debug
                return infor, 1

        finally:
            _logger.removeHandler(stderr_handler)
            _logger.addHandler(defaultStreamHandler)


    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=None, timeout=60):
        sys.argv[1] = None
        sys.stderr = sys.__stderr__
        inputs = code.strip().split()
        outputs = ""
        vname = None

        if not silent:
            if code.strip() in ['quit', 'quit()', 'exit', 'exit()']:
                self.do_shutdown(True)
                execution_count = "-"
                return {'status': 'ok',
                        'execution_count': execution_count,
                        }
            if code.strip().startswith("'"):
                stream_content = {'name': 'stdout', 'text': code}
                self.send_response(self.iopub_socket, 'stream', stream_content)
                execution_count = "comment"
                return{
                    'status': 'ok',
                    'execution_count': execution_count,
                    }

            # operation: ls(show all variables), i(show value of i), clear(delete all variables)

            if len(inputs) == 1 and "." not in inputs[0]:
                if inputs[0] == "ls":
                    outputs = str(self.VARIABLELIST)
                elif inputs[0] in self.VARIABLELIST.keys():
                    try:
                        outputs = str(self.VARIABLELIST.get(inputs[0]))
                    except:
                        outputs = "can't find variable "+inputs[0]+"."
                        status = 1
                elif inputs[0] == "clear":
                    self.VARIABLELIST.clear()
                elif "-" in inputs[0]:
                    try:
                        outputs, status = self.cwlmain(inputs)
                    except:
                        self.do_shutdown(True)
                        stream_content = {'name': 'stdout', 'text': outputs}
                        self.send_response(self.iopub_socket, 'stream', stream_content)
                        ename = "unrecognized arguments:"+inputs[0]
                        return{
                            'status': 'error',
                            'ename': ename,  # Exception name, as a string
                            'evalue': "",  # Exception value, as a string
                            'traceback': [""],  # traceback frames as strings
                        }
                else:
                    outputs = "can't find operation "+inputs[0]+"."
                    status = 1
            # operation: del i
            elif inputs[0] == "del":
                try:
                    if isinstance(self.VARIABLELIST[inputs[1]], dict):
                        os.remove(self.VARIABLELIST[inputs[1]]["tempFilePath"])
                    self.VARIABLELIST.pop(inputs[1])

                except:
                    outputs = "can't find variable "+inputs[1]+"."
                    status = 1
            # store variable name
            else:
                if "=" in inputs[0] and "-" not in inputs[0]:
                    vname = inputs[0].split('=')[0]
                    del inputs[0]
                for items in inputs:
                    if items in self.VARIABLELIST:
                        if isinstance(self.VARIABLELIST[items],dict):
                            inputs[inputs.index(items)] = str(self.VARIABLELIST[items]["tempFilePath"])
                        else:
                            inputs[inputs.index(items)] = str(self.VARIABLELIST[items])
                result, status = self.cwlmain(inputs)
                # display version
                if status == 0:
                    outputs = str(result)
                # running result
                elif isinstance(result, dict):
                    # 结果为file
                    for keys in result:
                        if isinstance(result[keys],dict):
                            JsonResult = json_dumps(result, indent=4)
                            outputs = outputs + "\n" + JsonResult + "\n" + status
                            if vname:
                                tempPath = os.getcwd() + "/"+ str(uuid.uuid4()) + ".txt"
                                tempFile = open(tempPath, "w")
                                try:
                                    tempFile.write(str(result[keys]))
                                    self.tempfilelist.append(tempPath)
                                    result[keys]["tempFilePath"] = tempPath
                                    self.VARIABLELIST[vname] = result[keys]
                                finally:
                                    tempFile.close()

                        # 结果是int string
                        else:
                            if vname:
                                self.VARIABLELIST[vname] = result[keys]
                            outputs = str(result[keys])

            stream_content = {'name': 'stdout', 'text': outputs}
            self.send_response(self.iopub_socket, 'stream', stream_content)

        return {'status': 'ok',
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
               }


