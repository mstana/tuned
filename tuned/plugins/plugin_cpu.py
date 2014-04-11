import base
from decorators import *
import tuned.logs
import tuned.utils.commands

import os
import struct

log = tuned.logs.get()

# TODO: force_latency -> command
#       intel_pstate

class CPULatencyPlugin(base.Plugin):
	"""
	Plugin for tuning CPU options. Powersaving, governor, required latency, etc.
	"""

	def __init__(self, *args, **kwargs):
		super(self.__class__, self).__init__(*args, **kwargs)

		self._has_cpupower = True
		self._has_energy_perf_bias = True
		self._has_intel_pstate = False

		self._min_perf_pct_save = None
		self._max_perf_pct_save = None
		self._no_turbo_save = None

	def _init_devices(self):
		self._devices = set()
		# current list of devices
		for device in self._hardware_inventory.get_devices("cpu"):
			self._devices.add(device.sys_name)

		self._assigned_devices = set()
		self._free_devices = self._devices.copy()

	def _get_config_options(self):
		return {
			"load_threshold"      : 0.2,
			"latency_low"         : 100,
			"latency_high"        : 1000,
			"force_latency"       : None,
			"governor"            : None,
			"energy_perf_bias"    : None,
			"min_perf_pct"        : None,
			"max_perf_pct"        : None,
			"no_turbo"            : None,
		}

	def _check_cpupower(self):
		if tuned.utils.commands.execute(["cpupower", "frequency-info"])[0] == 0:
			self._has_cpupower = True
		else:
			self._has_cpupower = False
			log.warning("using sysfs fallback, is cpupower installed?")

	def _check_energy_perf_bias(self):
		self._has_energy_perf_bias = False
		retcode = tuned.utils.commands.execute(["x86_energy_perf_policy", "-r"])[0]
		if retcode == 0:
			self._has_energy_perf_bias = True
		elif retcode == -1:
			log.warning("error executing x86_energy_perf_policy tool, ignoring CPU energy performance bias, is the tool installed?")
		else:
			log.warning("your CPU doesn't support MSR_IA32_ENERGY_PERF_BIAS, ignoring CPU energy performance bias")

	def _check_intel_pstate(self):
		self._has_intel_pstate = os.path.exists("/sys/devices/system/cpu/intel_pstate")
		if self._has_intel_pstate:
			log.info("intel_pstate detected")

	def _instance_init(self, instance):
		instance._has_static_tuning = True
		instance._has_dynamic_tuning = False

		# only the first instance of the plugin can control the latency
		if self._instances.values()[0] == instance:
			instance._first_instance = True
			self._cpu_latency_fd = os.open("/dev/cpu_dma_latency", os.O_WRONLY)
			self._latency = None

			if instance.options["force_latency"] is None:
				instance._load_monitor = self._monitors_repository.create("load", None)
				instance._has_dynamic_tuning = True
			else:
				instance._load_monitor = None

			# Check for cpupower, use workaround if not available
			self._check_cpupower()
			# Check for x86_energy_perf_policy, ignore if not available / supported
			self._check_energy_perf_bias()
			# Check for intel_pstate
			self._check_intel_pstate()
		else:
			instance._first_instance = False
			log.info("Latency settings from non-first CPU plugin instance '%s' will be ignored." % instance.name)

		instance._first_device = list(instance.devices)[0]

	def _instance_cleanup(self, instance):
		if instance._first_instance:
			os.close(self._cpu_latency_fd)
			if instance._load_monitor is not None:
				self._monitors_repository.delete(instance._load_monitor)

	def _instance_apply_static(self, instance):
		if instance._first_instance and self._has_intel_pstate:
			self._min_perf_pct_save = self._get_intel_pstate_attr("min_perf_pct")
			self._max_perf_pct_save = self._get_intel_pstate_attr("max_perf_pct")
			self._no_turbo_save = self._get_intel_pstate_attr("no_turbo")

		super(self.__class__, self)._instance_apply_static(instance)

		if not instance._first_instance:
			return

		force_latency_value = instance.options["force_latency"]
		if force_latency_value is not None:
			self._set_latency(force_latency_value)
		if self._has_intel_pstate:
			self._set_intel_pstate_attr("min_perf_pct", instance.options["min_perf_pct"])
			self._set_intel_pstate_attr("max_perf_pct", instance.options["max_perf_pct"])
			self._set_intel_pstate_attr("no_turbo", instance.options["no_turbo"])

	def _instance_unapply_static(self, instance):
		super(self.__class__, self)._instance_unapply_static(instance)

		if instance._first_instance and self._has_intel_pstate:
			self._set_intel_pstate_attr("min_perf_pct", self._min_perf_pct_save)
			self._set_intel_pstate_attr("max_perf_pct", self._max_perf_pct_save)
			self._set_intel_pstate_attr("no_turbo", self._no_turbo_save)

	def _instance_apply_dynamic(self, instance, device):
		self._instance_update_dynamic(instance, device)

	def _instance_update_dynamic(self, instance, device):
		assert(instance._first_instance)
		if device != instance._first_device:
			return

		load = instance._load_monitor.get_load()["system"]
		if load < instance.options["load_threshold"]:
			self._set_latency(instance.options["latency_high"])
		else:
			self._set_latency(instance.options["latency_low"])

	def _instance_unapply_dynamic(self, instance, device):
		pass

	def _get_intel_pstate_attr(self, attr):
		return tuned.utils.commands.read_file("/sys/devices/system/cpu/intel_pstate/%s" % attr, None)

	def _set_intel_pstate_attr(self, attr, val):
		if val is not None:
			tuned.utils.commands.write_to_file("/sys/devices/system/cpu/intel_pstate/%s" % attr, val)

	def _set_latency(self, latency):
		latency = int(latency)
		if self._latency != latency:
			log.info("setting new cpu latency %d" % latency)
			latency_bin = struct.pack("i", latency)
			os.write(self._cpu_latency_fd, latency_bin)
			self._latency = latency

	def _get_available_governors(self, device):
		return tuned.utils.commands.read_file("/sys/devices/system/cpu/%s/cpufreq/scaling_available_governors" % device).split()

	@command_set("governor", per_device=True)
	def _set_governor(self, governor, device):
		if governor not in self._get_available_governors(device):
			log.info("ignoring governor '%s' on cpu '%s', it is not supported" % (governor, device))
			return
		log.info("setting governor '%s' on cpu '%s'" % (governor, device))
		if self._has_cpupower:
			cpu_id = device.lstrip("cpu")
			tuned.utils.commands.execute(["cpupower", "-c", cpu_id, "frequency-set", "-g", str(governor)])
		else:
			tuned.utils.commands.write_to_file("/sys/devices/system/cpu/%s/cpufreq/scaling_governor" % device, str(governor))

	@command_get("governor")
	def _get_governor(self, device):
		governor = None
		if self._has_cpupower:
			cpu_id = device.lstrip("cpu")
			retcode, lines = tuned.utils.commands.execute(["cpupower", "-c", cpu_id, "frequency-info", "-p"])
			if retcode == 0:
				for line in lines.splitlines():
					if line.startswith("analyzing"):
						continue
					l = line.split()
					if len(l) == 3:
						governor = l[2].strip()
						break
		else:
			data = tuned.utils.commands.read_file("/sys/devices/system/cpu/%s/cpufreq/scaling_governor" % device).strip()
			if len(data) > 0:
				governor = data


		if governor is None:
			log.error("could not get current governor on cpu '%s'" % device)

		return governor

	@command_set("energy_perf_bias", per_device=True)
	def _set_energy_perf_bias(self, energy_perf_bias, device):
		if self._has_energy_perf_bias:
			log.info("setting energy_perf_bias '%s' on cpu '%s'" % (energy_perf_bias, device))
			cpu_id = device.lstrip("cpu")
			tuned.utils.commands.execute(["x86_energy_perf_policy", "-c", cpu_id, str(energy_perf_bias)])

	@command_get("energy_perf_bias")
	def _get_energy_perf_bias(self, device):
		energy_perf_bias = None
		if self._has_energy_perf_bias:
			cpu_id = device.lstrip("cpu")
			retcode, lines = tuned.utils.commands.execute(["x86_energy_perf_policy", "-c", cpu_id, "-r"])
			if retcode == 0:
				for line in lines.splitlines():
					l = line.split()
					if len(l) == 2:
						energy_perf_bias = l[1]
						break

		return energy_perf_bias
