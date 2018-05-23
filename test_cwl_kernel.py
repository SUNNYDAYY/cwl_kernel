import unittest
import jupyter_kernel_test

class MyKernelTests(jupyter_kernel_test.KernelTests):
    kernel_name = "cwl_kernel"
    language_name = "python"
    def test_cwlkernel_stdout(self):
        # self.flush_channels()
        reply, output_msgs = self.execute_helper(code='/Users/sunbo/Desktop/cwl/1st-tool.cwl')
        self.assertEqual(reply['content']['status'], 'ok')
        self.assertEqual(output_msgs[0]['content']['text'], 'foo\n')

if __name__ == '__main__':
    unittest.main()
