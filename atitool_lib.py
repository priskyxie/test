#!/usr/bin/env python2
import os
from subprocess import Popen, PIPE


def getdir(path = None):
	return os.path.dirname(os.path.abspath(__file__ if path == None else path))


def run_command(command):
	return Popen([getdir() + "/atitool"] + command, stdout=PIPE, bufsize=1)


def get_gpu_ids():
	p = run_command(["-i"])
	with p.stdout:
		atitool_gpu_ids = []
		for line in iter(p.stdout.readline, b''):
			if "VendorID" in str(line) and "DeviceID" in str(line) and "SSID" in str(line):
				atitool_gpu_ids.append(line.strip().split()[0])
		return ','.join(atitool_gpu_ids)


def find_gpus():
	p = run_command(["-i"])
	gpu_count = 0
	with p.stdout:
		atitool_gpu_ids = []
		for line in iter(p.stdout.readline, b''):
			if "VendorID" in str(line) and "DeviceID" in str(line) and "SSID" in str(line):
				gpu_count = gpu_count + 1
		return gpu_count


def get_num_gpus():
	print(find_gpus())


# run pmlogs with a default logging resolution of 1000 ms (same as atitool), unless specified
def run_atitool(fullpath, resolution=1000):
	p = run_command(["-i=" + get_gpu_ids(), "-pmoutput=" + fullpath, "-logpath=" + getdir(fullpath), "-pmlogall", "-pmperiod=" + str(resolution)])
	print(p.pid)
