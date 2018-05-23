import cwltool.factory
from cwltool.argparser import arg_parser, generate_parser, DEFAULT_TMP_PREFIX



if __name__ == '__main__':

    code = "/Users/sunbo/Desktop/cwl/1st-tool.cwl"
    args = arg_parser().parse_args()

    fac = cwltool.factory.Factory()
    echo = fac.make(code)
    result = echo(inp="foo")

    if result["out"] == "foo\n":
        print("11")

    print(result)
