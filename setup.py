from distutils.core import setup



setup(
    name='cwl_kernel',
    version='1.0',
    packages=['cwl_kernel'],
    description='Simple cwl kernel for Jupyter',
    install_requires=[
        'jupyter_client', 'IPython', 'ipykernel'
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
    ],
)
