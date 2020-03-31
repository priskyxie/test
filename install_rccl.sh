#! /bin/bash

git clone https://github.com/ROCmSoftwarePlatform/rccl.git
cd rccl/
mkdir build
cd build/
CXX=/opt/rocm/bin/hcc cmake ..
make -j 8
ls
make package
dpkg -i *.deb
cd ../..

git clone https://github.com/ROCmSoftwarePlatform/rccl-tests.git
cd rccl-tests
./install.sh
