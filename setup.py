#!/usr/bin/env python
import numpy
import sys

from setuptools import setup
from Cython.Build import cythonize
from Cython.Distutils import build_ext
from setuptools.extension import Extension

desc = "Quantiphyse plugin for DCE"
version = "0.0.1"

extensions = []
compile_args = []
link_args = []

if sys.platform.startswith('win'):
    compile_args.append('/EHsc')
elif sys.platform.startswith('darwin'):
    link_args.append("-stdlib=libc++")

# PK modelling extension
extensions.append(Extension("dce.pk_model",
                 sources=['dce/pk_model.pyx',
                          'src/Optimizer_class.cpp',
                          'src/pkrun2.cpp',
                          'src/ToftsOrton.cpp',
                          'src/ToftsOrtonOffset.cpp',
                          'src/ToftsWeinOffset.cpp',
                          'src/ToftsWeinOffsetVp.cpp',
                          'src/lmlib/lmcurve.cpp',
                          'src/lmlib/lmmin.cpp'],
                 include_dirs=['src/lmlib', 'src', numpy.get_include()],
                 language="c++", extra_compile_args=compile_args, extra_link_args=link_args))

# setup parameters
setup(name='qp-dce',
      cmdclass={'build_ext': build_ext},
      version=version,
      description=desc,
      long_description=desc,
      author='Michael Chappell, Martin Craig',
      author_email='martin.craig@eng.ox.ac.uk',
      packages=['dce'],
      include_package_data=True,
      data_files=[],
      setup_requires=[],
      install_requires=[],
      ext_modules=cythonize(extensions),
      classifiers=["Programming Language :: Python :: 2.7",
                   "Development Status:: 3 - Alpha",
                   'Programming Language :: Python',
                   'Operating System :: MacOS :: MacOS X',
                   'Operating System :: Microsoft :: Windows',
                   'Operating System :: POSIX',
                   "Intended Audience :: Education",
                   "Intended Audience :: Science/Research",
                   "Intended Audience :: End Users/Desktop",
                   "Topic :: Scientific/Engineering :: Bio-Informatics",],
)

