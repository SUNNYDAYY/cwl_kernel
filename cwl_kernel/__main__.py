from ipykernel.kernelapp import IPKernelApp
from . import cwl_kernel

IPKernelApp.launch_instance(kernel_class=cwl_kernel)
