import unittest
import jupyter_kernel_test

class MyKernelTests(jupyter_kernel_test.KernelTests):
    kernel_name = "cwl_kernel"
    language_name = "python"
    def test_cwlkernel_stdout(self):
        self.flush_channels()

        # # input: datafile
        # reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/workflows-master/workflows/make-to-cwl/rna.json')
        # self.assertEqual(reply['content']['status'], 'ok')
        # self.assertEqual(output_msgs[0]['content']['text'], "ATGAAGACTGACTCGATCGATCG\nATGAAGACTGACTCGATCGATCG\nATGAAGACTGACTCGATCGATCG\n")

        # input: cwlfile
        reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/cwl/hello.cwl')
        self.assertEqual(reply['content']['status'], 'ok')
        self.assertEqual(output_msgs[0]['content']['text'], "Hello World\n")

        # # input: cwlfile datafile
        # reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/cwl/hello-para.cwl /Users/sunbo/Desktop/cwl/params.yaml')
        # self.assertEqual(reply['content']['status'], 'ok')
        # self.assertEqual(output_msgs[0]['content']['text'], "Tool definition failed initialization")
        #
        # # input: cwlfile parameter
        # reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/cwl/hello-param.cwl --usermessage message')
        # self.assertEqual(reply['content']['status'], 'ok')
        # self.assertEqual(output_msgs[0]['content']['text'], "-e message")
        #
        # # input*: parameter cwlfile parameter
        # reply, output_msgs = self.execute_helper(code='--no-read-only /Users/sunbo/Desktop/cwl/hello-param.cwl --usermessage message')
        # self.assertEqual(reply['content']['status'], 'ok')
        # self.assertEqual(output_msgs[0]['content']['text'], "-e message")



        # # input(multi-step): cwlfile /n parameter
        # reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/cwl/hello-param.cwl')
        # self.assertEqual(reply['content']['status'], 'ok')
        # reply, output_msgs = self.execute_helper(code='--usermessage message')
        # self.assertEqual(reply['content']['status'], 'ok')
        # self.assertEqual(output_msgs[0]['content']['text'], "-e message")
        #
        # # input(multi-step): cwlfile /n datafile
        # reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/cwl/hello-param.cwl')
        # self.assertEqual(reply['content']['status'], 'ok')
        # self.assertEqual(output_msgs[0]['content']['text'], "require data file/ parameters")
        # reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/cwl/params.yaml')
        # self.assertEqual(reply['content']['status'], 'ok')
        # self.assertEqual(output_msgs[0]['content']['text'], "-e Hello, CWL !\nHello World !\n")


        #
        # reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/cwlProjectsFromCLWViewer/GALES-master/cwl/tools/prodigal.cwl /Users/sunbo/Desktop/cwlProjectsFromCLWViewer/GALES-master/cwl/tools/prodigal.test.json')
        # self.assertEqual(reply['content']['status'], 'ok')
        # self.assertEqual(output_msgs[0]['content']['text'], "No cwlVersion found.Use the following syntax in your CWL document to declare the version: cwlVersion: <version>")
        #
        # reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/workflows-master/workflows/make-to-cwl/rna.json')
        # self.assertEqual(reply['content']['status'], 'ok')
        # self.assertEqual(output_msgs[0]['content']['text'], "ATGAAGACTGACTCGATCGATCG\nATGAAGACTGACTCGATCGATCG\nATGAAGACTGACTCGATCGATCG\n")


        # error: wrong file path
        reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/cwl/hello-para.cwl /Users/sunbo/Desktop/cwl/params.yaml')
        self.assertEqual(reply['content']['status'], 'ok')
        self.assertEqual(output_msgs[0]['content']['text'], "Tool definition failed initialization")


if __name__ == '__main__':
    unittest.main()
