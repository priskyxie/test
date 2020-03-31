# -*- coding: UTF-8 -*-
import os.path
import os
import sys
import re
import subprocess
import time
import logging
import logging.config
from subprocess import Popen, PIPE

#os.system("rm -f " + "*.log")
ATITOOL = "/root/tools/atitool/atitool"

logger = logging.getLogger(__name__)
logfile = "docker_c2_"+str(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())) +".log"
logconf = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)-15s - [%(levelname)-8s] - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'verbose'
        },
        'file_debug': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'verbose',
            'filename': os.path.join(os.path.dirname(__file__), logfile),
            'maxBytes': 50000000,
            'backupCount': 10
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'file_debug'],
    }
}
logging.config.dictConfig(logconf)

#===================== ATITOOL LIB =======================
def getdir(path = None):
    return os.path.dirname(os.path.abspath(__file__ if path == None else path))


def run_command(command):
    #return Popen([getdir() + "/atitool"] + command, stdout=PIPE, bufsize=1)
    return Popen([ATITOOL] + command, stdout=PIPE, bufsize=1)


def get_gpu_ids():
    p = run_command(["-i"])
    with p.stdout:
        atitool_gpu_ids = []
        for line in iter(p.stdout.readline, b''):
           if "VendorID" in str(line) and "DeviceID" in str(line) and "SSID" in str(line):
              atitool_gpu_ids.append(line.strip().split()[0])
        #logger.info("GPU id = " + ','.join(atitool_gpu_ids))
        return ','.join(str(atitool_gpu_ids))


def find_gpus():
    p = run_command(["-i"])
    gpu_count = 0
    with p.stdout:
        atitool_gpu_ids = []
        for line in iter(p.stdout.readline, b''):
            if "VendorID" in str(line) and "DeviceID" in str(line) and "SSID" in str(line):
                gpu_count = gpu_count + 1
        return str(gpu_count)


def get_num_gpus():
    print(str(find_gpus()))


# run pmlogs with a default logging resolution of 1000 ms (same as atitool), unless specified
def run_atitool(fullpath, resolution=1000):
    p = run_command(["-i=" + get_gpu_ids(), "-pmoutput=" + fullpath, "-logpath=" + getdir(fullpath), "-pmlogall", "-pmperiod=" + str(resolution)])
    print(p.pid)


def run_cmd(cmd):
    logger.info("CMD = %s" % cmd)
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = p.communicate()
    except KeyboardInterrupt:
        logger.debug("User terminated the run!")
        return False
    logger.debug("ReturnCode: %s, Resp: \n%s", p.returncode, stdout)
    return stdout


def docker_login():
    cmd = "docker login --username=svttestacc2018 --password=D3veloper@ccount!"
    logger.info("========================================================================")
    logger.info("docker login cmd:%s", cmd)
    logger.info("========================================================================")
    run_cmd(cmd)


def fetch_system_info():
    cmd = "uname -a"
    logger.info("Linux Kernel:%s" % run_cmd(cmd))
    cmd = "dkms status"
    logger.info("DKMS status:%s" % run_cmd(cmd))
    cmd = r"dpkg -l | grep 'rocm\|rocr\|roct\|hsa\|hcc\|hip_\|compute_roc'"
    #logger.info("Linux Kernel:%s" % run_cmd(cmd))
    logger.info("Linux Kernel:%s" % os.system(cmd))
    # cmd = r"find /sys/kernel/debug/dri/ -name amdgpu_firmware_info"
    # resp = run_cmd(cmd)
    # cmd = "cat %s" % resp
    # #logger.info("Linux Kernel:%s" % run_cmd(cmd))
    # logger.info("Linux Kernel:%s" % os.system(cmd))

    cmd = ATITOOL + ' -i |grep -i "VendorID: 0x1002" |wc -l'
    gpu_number = run_cmd(cmd)
    logger.info("GPU numbers = " + str(gpu_number))
    cmd = ATITOOL + " -i"
    run_cmd(cmd)


def clean_docker():
    cmd = "docker stop $(docker ps -a -q)"
    run_cmd(cmd)
    cmd = "docker rm $(docker ps -a -q)"
    run_cmd(cmd)
    cmd = r"docker rmi docker_build:latest"
    run_cmd(cmd)
    cmd = "docker system prune -f"
    run_cmd(cmd)
    cmd = "reset"
    run_cmd(cmd)

def check_docker_image(image):
    # Check if docker images exists, if not, pull it from docker hub
    # cmd = "docker images -q %s" % image
    # resp = run_cmd(cmd)
    # if not resp:
    #     docker_login()
    #     cmd = "docker pull %s" % image
    #     run_cmd(cmd)
    pass


class TENSORFLOW():
    def __init__(self, docker_image, exec_script_path, parameters,):
        self.docker_image = docker_image
        self.exec_script_path = exec_script_path
        self.parameters = parameters
        self.model = self.parameters.split("--model=")[1].split()[0]
        self.batch_size = self.parameters.split("--batch_size=")[1].split()[0]
        fetch_system_info()
        self.log_dir = "/root/results/tf_%s_%s_%s" % (self.model, self.batch_size, str(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())))
        cmd = "mkdir -p %s" % self.log_dir
        run_cmd(cmd)
        check_docker_image(self.docker_image)
        logger.info("Start running %s %s" % (self.exec_script_path, self.parameters))

    def start_pm_log(self, duration):
        logger.info("====== Start log PM log =========")
        pm_log_path = "pm_tf_" + self.model + "_" + self.batch_size + "_" + str(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))+".csv"
        run_atitool(pm_log_path, duration)

        # gpu_id = 0
        # # for gpu_id in range(int(self.gpu_number)):
        # #     pm_log_path = "pm_" + str(gpu_id) + str(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())) + ".csv"
        # #     logger.info("pm log path =" + pm_log_path)
        # #     cmd = ATITOOL + " -i=%s -pmoutput=%s -pmlogall -pmperiod=%s" % (str(gpu_id), pm_log_path, duration)
        # #     #run_cmd(cmd)
        # #     logger.info("cmd =" + cmd)
        # #     os.system(cmd)
        # command = '["%s", "-i=%s", "-pmoutput=%s", "-pmlogall", "-pmperiod=%s"]' % (self.atitool, str(gpu_id), pm_log_path, duration)
        # logger.info(command)
        # Popen(command, stdout=PIPE, bufsize=1)

    def stop_pm_log(self):
        cmd = "killall atitool"
        run_cmd(cmd)


    def gen_execfile(self, tf_exec):
        with open(tf_exec, "w") as f:
            f.write(r"#!/bin/bash")
            f.write("\n")
            f.write(r"OUTPUT=/results/tensor.log")
            f.write("\n")
            f.write('CMD="%s %s |tee -a $OUTPUT"' %(self.exec_script_path, self.parameters))
            f.write("\n")
            f.write(r"START=$(date '+%s')")
            f.write("\n")
            f.write(r'''echo -e "====== Starting [$(date '+%d-%m-%Y %H:%M:%S')] ======" | tee -a $OUTPUT''')
            f.write("\n")
            f.write(r"eval $CMD")
            f.write("\n")
            f.write(r'''echo -e "===== Finished Training [$(date '+%d-%m-%Y %H:%M:%S')] ======" | tee -a $OUTPUT''')
            f.write("\n")
            f.write(r'''echo "duration $(($(date '+%s')-START)) seconds" | tee -a $OUTPUT''')
            f.write("\n")
        cmd = "chmod +x %s" % tf_exec
        run_cmd(cmd)

    def gen_dockerfile(self, dockerfile):
        work_dir = self.exec_script_path.split()[1].split("/tf_cnn_benchmarks.py")[0]
        with open(dockerfile, "w") as f:
            f.write("FROM %s" % self.docker_image)
            f.write("\n")
            f.write("WORKDIR %s" % work_dir)
            f.write("\n")
            f.write("ADD ./tf_exec.sh %s" % work_dir)
            f.write("\n")
            f.write('CMD ["./tf_exec.sh"]')
            f.write("\n")

    def build_docker(self, docker_build):
        cmd = "docker build -t %s ." % docker_build
        run_cmd(cmd)

    def start_docker(self, docker_image):
        cmd = "docker run -it --network=host --device=/dev/kfd --device=/dev/dri --ipc=host \
        --group-add video --cap-add=SYS_PTRACE --security-opt seccomp=unconfined \
        -v %s:/results -v /data/imagenet-inception:/imagenet %s" % (self.log_dir, docker_image)
        #run_cmd(cmd)
        os.system(cmd + " |tee -a " + logfile)

    def run(self):
        pass
        self.start_pm_log(duration="1000")
        self.gen_execfile("tf_exec.sh")
        self.gen_dockerfile("Dockerfile")
        self.build_docker("docker_build")
        self.start_docker("docker_build")
        clean_docker()
        self.stop_pm_log()


class CAFFE2():
    def __init__(self, docker_image, exec_script_path, parameters):
        self.docker_image = docker_image
        self.exec_script_path = exec_script_path
        self.parameters = parameters
        self.model = self.parameters.split("--model ")[1].split()[0]
        self.batch_size = self.parameters.split("--batch_size ")[1].split()[0]
        fetch_system_info()
        self.log_dir = "/root/results/c2_%s_%s_%s" % (self.model, self.batch_size, str(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())))
        cmd = "mkdir -p %s" % self.log_dir
        run_cmd(cmd)
        check_docker_image(self.docker_image)
        logger.info("Start running %s %s" % (self.exec_script_path, self.parameters))

    def start_pm_log(self, duration):
        logger.info("====== Start log PM log =========")
        pm_log_path = "pm_c2_" + self.model + "_" + self.batch_size + "_" + str(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))+".csv"
        run_atitool(pm_log_path, duration)

    def stop_pm_log(self):
        cmd = "killall atitool"
        run_cmd(cmd)


    def gen_execfile(self, c2_exec):
        with open(c2_exec, "w") as f:
            f.write(r"#!/bin/bash")
            f.write("\n")
            #f.write(r"wget https://raw.githubusercontent.com/pramenku/rocm-scripts/master/convnet_benchmarks_dpm.py")
            f.write("\n")
            f.write(r"OUTPUT=/results/caffe2.log")
            f.write("\n")
            f.write('CMD="%s %s |tee -a $OUTPUT"' %(self.exec_script_path, self.parameters))
            f.write("\n")
            f.write(r"START=$(date '+%s')")
            f.write("\n")
            f.write(r'''echo -e "====== Starting [$(date '+%d-%m-%Y %H:%M:%S')] ======" | tee -a $OUTPUT''')
            f.write("\n")
            f.write(r"eval $CMD")
            f.write("\n")
            f.write(r'''echo -e "===== Finished Training [$(date '+%d-%m-%Y %H:%M:%S')] ======" | tee -a $OUTPUT''')
            f.write("\n")
            f.write(r'''echo "duration $(($(date '+%s')-START)) seconds" | tee -a $OUTPUT''')
            f.write("\n")
        cmd = "chmod +x %s" % c2_exec
        run_cmd(cmd)

    def gen_dockerfile(self, dockerfile):
        work_dir = self.exec_script_path.split()[1].split("/convnet_benchmarks_dpm.py")[0]
        with open(dockerfile, "w") as f:
            f.write("FROM %s" % self.docker_image)
            f.write("\n")
            f.write("WORKDIR %s" % work_dir)
            f.write("\n")
            f.write("ADD ./convnet_benchmarks_dpm.py %s" % work_dir)
            f.write("\n")
            f.write("ADD ./c2_exec.sh %s" % work_dir)
            f.write("\n")
            f.write('CMD ["./c2_exec.sh"]')
            f.write("\n")

    def build_docker(self, docker_build):
        cmd = "docker build -t %s ." % docker_build
        run_cmd(cmd)

    def start_docker(self, docker_image):
        cmd = "docker run -it --shm-size 128G --network=host --device=/dev/kfd --device=/dev/dri --ipc=host \
        --group-add video --cap-add=SYS_PTRACE --security-opt seccomp=unconfined \
        -v %s:/results -v /data/imagenet-inception:/imagenet %s" % (self.log_dir, docker_image)
        #run_cmd(cmd)
        os.system(cmd + " |tee -a " + logfile)

    def run(self):
        pass
        self.start_pm_log(duration="1000")
        self.gen_execfile("c2_exec.sh")
        self.gen_dockerfile("Dockerfile")
        self.build_docker("docker_build")
        self.start_docker("docker_build")
        clean_docker()
        self.stop_pm_log()


class PYTORCH():
    def __init__(self, docker_image, exec_script_path, parameters):
        self.docker_image = docker_image
        self.exec_script_path = exec_script_path
        self.parameters = parameters
        self.model = self.parameters.split("--network ")[1].split()[0]
        self.batch_size = self.parameters.split("--batch-size ")[1].split()[0]
        fetch_system_info()
        self.log_dir = "/root/results/py_%s_%s_%s" % (self.model, self.batch_size, str(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())))
        cmd = "mkdir -p %s" % self.log_dir
        run_cmd(cmd)
        check_docker_image(self.docker_image)
        logger.info("Start running %s %s" % (self.exec_script_path, self.parameters))

    def start_pm_log(self, duration):
        logger.info("====== Start log PM log =========")
        pm_log_path = "pm_py_" + self.model + "_" + self.batch_size+ "_" + str(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))+".csv"
        run_atitool(pm_log_path, duration)

    def stop_pm_log(self):
        cmd = "killall atitool"
        run_cmd(cmd)

    def gen_execfile(self, py_exec):
        with open(py_exec, "w") as f:
            f.write(r"#!/bin/bash")
            f.write("\n")
            f.write("git clone https://github.com/priskyxie/pytorch_benchmark.git")
            f.write("\n")
            f.write("git clone https://github.com/pytorch/vision.git")
            f.write("\n")
            f.write("cd /root/vision")
            f.write("\n")
            f.write(r"/usr/bin/python3.6 setup.py install")
            f.write("\n")
            f.write("cd ..")
            f.write("\n")
            f.write(r"OUTPUT=/results/pytorch.log")
            f.write("\n")
            f.write('CMD="%s %s |tee -a $OUTPUT"' %(self.exec_script_path, self.parameters))
            f.write("\n")
            f.write(r"START=$(date '+%s')")
            f.write("\n")
            f.write(r'''echo -e "====== Starting [$(date '+%d-%m-%Y %H:%M:%S')] ======" | tee -a $OUTPUT''')
            f.write("\n")
            f.write(r"eval $CMD")
            f.write("\n")
            f.write(r'''echo -e "===== Finished Training [$(date '+%d-%m-%Y %H:%M:%S')] ======" | tee -a $OUTPUT''')
            f.write("\n")
            f.write(r'''echo "duration $(($(date '+%s')-START)) seconds" | tee -a $OUTPUT''')
            f.write("\n")
        cmd = "chmod +x %s" % py_exec
        run_cmd(cmd)

    def gen_dockerfile(self, dockerfile):
        #work_dir = self.exec_script_path.split()[1].split("/micro_benchmarking_pytorch.py")[0]
        work_dir = "/root"
        with open(dockerfile, "w") as f:
            f.write("FROM %s" % self.docker_image)
            f.write("\n")
            f.write("WORKDIR %s" % work_dir)
            f.write("\n")
            f.write("ADD ./py_exec.sh %s" % work_dir)
            f.write("\n")
            f.write('CMD ["./py_exec.sh"]')
            f.write("\n")

    def build_docker(self, docker_build):
        cmd = "docker build -t %s ." % docker_build
        run_cmd(cmd)

    def start_docker(self, docker_image):
        cmd = "docker run -it --network=host --device=/dev/kfd --device=/dev/dri --ipc=host \
        --group-add video --cap-add=SYS_PTRACE --security-opt seccomp=unconfined \
        -v %s:/results -v /data/imagenet-inception:/imagenet %s" % (self.log_dir, docker_image)
        #run_cmd(cmd)
        os.system(cmd + " |tee -a " + logfile)

    def run(self):
        self.start_pm_log(duration="1000")
        self.gen_execfile("py_exec.sh")
        self.gen_dockerfile("Dockerfile")
        self.build_docker("docker_build")
        self.start_docker("docker_build")
        clean_docker()
        self.stop_pm_log()


class MIOPEN():
    def __init__(self, docker_image, exec_script_path, parameters):
        self.docker_image = docker_image
        self.exec_script_path = exec_script_path
        self.parameters = parameters
        fetch_system_info()
        self.log_dir = "/root/results/miopen_%s" % (str(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())))
        cmd = "mkdir -p %s" % self.log_dir
        run_cmd(cmd)
        check_docker_image(self.docker_image)
        logger.info("Start running %s %s" % (self.exec_script_path, self.parameters))

    def start_pm_log(self, duration):
        logger.info("====== Start log PM log =========")
        pm_log_path = "pm_miopen_" + str(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))+".csv"
        run_atitool(pm_log_path, duration)

    def stop_pm_log(self):
        cmd = "killall atitool"
        run_cmd(cmd)

    def gen_execfile(self, mi_exec):
        with open(mi_exec, "w") as f:
            f.write(r"#!/bin/bash")
            f.write("\n")
            f.write(r"OUTPUT=/results/miopen.log")
            f.write("\n")
            f.write('CMD="%s %s |tee -a $OUTPUT"' %(self.exec_script_path, self.parameters))
            f.write("\n")
            f.write(r"START=$(date '+%s')")
            f.write("\n")
            f.write(r'''echo -e "====== Starting [$(date '+%d-%m-%Y %H:%M:%S')] ======" | tee -a $OUTPUT''')
            f.write("\n")
            f.write(r"eval $CMD")
            f.write("\n")
            f.write(r'''echo -e "===== Finished Training [$(date '+%d-%m-%Y %H:%M:%S')] ======" | tee -a $OUTPUT''')
            f.write("\n")
            f.write(r'''echo "duration $(($(date '+%s')-START)) seconds" | tee -a $OUTPUT''')
            f.write("\n")
        cmd = "chmod +x %s" % mi_exec
        run_cmd(cmd)

    def gen_dockerfile(self, dockerfile):
        work_dir = self.exec_script_path.split("/MIOpenDriver")[0]
        with open(dockerfile, "w") as f:
            f.write("FROM %s" % self.docker_image)
            f.write("\n")
            f.write("WORKDIR %s" % work_dir)
            f.write("\n")
            f.write("ADD ./mi_exec.sh %s" % work_dir)
            f.write("\n")
            f.write('CMD ["./mi_exec.sh"]')
            f.write("\n")

    def build_docker(self, docker_build):
        cmd = "docker build -t %s ." % docker_build
        run_cmd(cmd)

    def start_docker(self, docker_image):
        cmd = "docker run -it --network=host --device=/dev/kfd --device=/dev/dri --ipc=host \
        --group-add video --cap-add=SYS_PTRACE --security-opt seccomp=unconfined \
        -v %s:/results -v /data:/imagenet %s" % (self.log_dir, docker_image)
        #run_cmd(cmd)
        os.system(cmd + " |tee -a " + logfile)

    def run(self):
        self.start_pm_log(duration="1000")
        self.gen_execfile("mi_exec.sh")
        self.gen_dockerfile("Dockerfile")
        self.build_docker("docker_build")
        self.start_docker("docker_build")
        clean_docker()
        self.stop_pm_log()


class SPARSENN():
    def __init__(self, docker_image, exec_script_path, parameters):
        self.docker_image = docker_image
        self.exec_script_path = exec_script_path
        self.parameters = parameters
        fetch_system_info()
        self.log_dir = "/root/results/sparsenn_%s" % (str(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())))
        cmd = "mkdir -p %s" % self.log_dir
        run_cmd(cmd)
        check_docker_image(self.docker_image)
        logger.info("Start running %s %s" % (self.exec_script_path, self.parameters))

    def start_pm_log(self, duration):
        logger.info("====== Start log PM log =========")
        pm_log_path = "pm_sparsenn_" + str(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))+".csv"
        run_atitool(pm_log_path, duration)

    def stop_pm_log(self):
        cmd = "killall atitool"
        run_cmd(cmd)

    def gen_execfile(self, spnn_exec):
        with open(spnn_exec, "w") as f:
            f.write(r"#!/bin/bash")
            f.write("\n")
            f.write("git clone https://github.com/ROCmSoftwarePlatform/dlrm.git")
            f.write("\n")
            f.write("HIP_VISIBLE_DEVICES=0")
            f.write("\n")
            f.write(r"OUTPUT=/results/sparsenn.log")
            f.write("\n")
            f.write('CMD="%s %s |tee -a $OUTPUT"' %(self.exec_script_path, self.parameters))
            f.write("\n")
            f.write(r"START=$(date '+%s')")
            f.write("\n")
            f.write(r'''echo -e "====== Starting [$(date '+%d-%m-%Y %H:%M:%S')] ======" | tee -a $OUTPUT''')
            f.write("\n")
            f.write(r"eval $CMD")
            f.write("\n")
            f.write(r'''echo -e "===== Finished Training [$(date '+%d-%m-%Y %H:%M:%S')] ======" | tee -a $OUTPUT''')
            f.write("\n")
            f.write(r'''echo "duration $(($(date '+%s')-START)) seconds" | tee -a $OUTPUT''')
            f.write("\n")
        cmd = "chmod +x %s" % spnn_exec
        run_cmd(cmd)

    def gen_dockerfile(self, dockerfile):
        work_dir = "/root"
        with open(dockerfile, "w") as f:
            f.write("FROM %s" % self.docker_image)
            f.write("\n")
            f.write("WORKDIR %s" % work_dir)
            f.write("\n")
            f.write("ADD ./spnn_exec.sh %s" % work_dir)
            f.write("\n")
            f.write('CMD ["./spnn_exec.sh"]')
            f.write("\n")

    def build_docker(self, docker_build):
        cmd = "docker build -t %s ." % docker_build
        run_cmd(cmd)

    def start_docker(self, docker_image):
        cmd = "docker run -it --network=host --device=/dev/kfd --device=/dev/dri --ipc=host \
        --group-add video --cap-add=SYS_PTRACE --security-opt seccomp=unconfined \
        -v %s:/results -v /data:/imagenet %s" % (self.log_dir, docker_image)
        #run_cmd(cmd)
        os.system(cmd + " |tee -a " + logfile)

    def run(self):
        self.start_pm_log(duration="1000")
        self.gen_execfile("spnn_exec.sh")
        self.gen_dockerfile("Dockerfile")
        self.build_docker("docker_build")
        self.start_docker("docker_build")
        clean_docker()
        self.stop_pm_log()

if __name__ == "__main__":

    ### BKC 2097
    DOCKER_IMAGE = "47cbd6306a84"
    EXEC_SCRIPT_PATH = "/usr/bin/python3.6 /root/caffe2/caffe2/python/convnet_benchmarks_dpm.py"
    PARAMETERS = "--model Inception --num_gpus 4 --batch_size 256 --iterations 1000"
    #PARAMETERS = "--model AlexNet --batch_size 64 --iterations 1"
    c2 = CAFFE2(DOCKER_IMAGE, EXEC_SCRIPT_PATH, PARAMETERS)
    c2.run()

