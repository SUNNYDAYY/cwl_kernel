import unittest
import jupyter_kernel_test

class MyKernelTests(jupyter_kernel_test.KernelTests):
    kernel_name = "cwl_kernel"
    language_name = "python"
    def test_cwlkernel_stdout(self):
        self.flush_channels()

        # reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/workflows-master/workflows/make-to-cwl/rna.json')
        # self.assertEqual(reply['content']['status'], 'ok')
        # self.assertEqual(output_msgs[0]['content']['text'], "ATGAAGACTGACTCGATCGATCG\nATGAAGACTGACTCGATCGATCG\nATGAAGACTGACTCGATCGATCG\n")


        # reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/cwl/hello-param.cwl /Users/sunbo/Desktop/cwl/params.yaml')
        # self.assertEqual(reply['content']['status'], 'ok')
        # self.assertEqual(output_msgs[0]['content']['text'], "-e Hello, CWL !\nHello World !\n")
        #
        # reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/cwl/hello-param.cwl')
        # self.assertEqual(reply['content']['status'], 'ok')
        # reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/cwl/params.yaml')
        # self.assertEqual(reply['content']['status'], 'ok')
        # self.assertEqual(output_msgs[0]['content']['text'], "-e Hello, CWL !\nHello World !\n")
        #
        # reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/cwl/hello-param.cwl')
        # self.assertEqual(reply['content']['status'], 'ok')
        # reply, output_msgs = self.execute_helper(code='--usermessage message')
        # self.assertEqual(reply['content']['status'], 'ok')
        # self.assertEqual(output_msgs[0]['content']['text'], "-e message")
        #
        # reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/cwl/hello.cwl')
        # self.assertEqual(reply['content']['status'], 'ok')
        # self.assertEqual(output_msgs[0]['content']['text'], "Hello World\n")
        #
        # reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/cwl/params.yaml')
        # self.assertEqual(reply['content']['status'], 'ok')
        # self.assertEqual(output_msgs[0]['content']['text'], "No cwlVersion found.Use the following syntax in your CWL document to declare the version: cwlVersion: <version>")
        #
        # reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/workflows-master/workflows/make-to-cwl/rna.json')
        # self.assertEqual(reply['content']['status'], 'ok')
        # self.assertEqual(output_msgs[0]['content']['text'], "ATGAAGACTGACTCGATCGATCG\nATGAAGACTGACTCGATCGATCG\nATGAAGACTGACTCGATCGATCG\n")



        reply, output_msgs = self.execute_helper(code='--no-match-user --no-read-only /Users/sunbo/Desktop/cwltests-master/cwl/workflow.cwl --events 100')
        self.assertEqual(reply['content']['status'], 'ok')


if __name__ == '__main__':
    unittest.main()
