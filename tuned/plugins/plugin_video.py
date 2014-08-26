import base
from decorators import *
import tuned.logs
from tuned.utils.commands import *
import os

log = tuned.logs.get()

class VideoPlugin(base.Plugin):
	"""
	Plugin for tuning powersave options for some graphic cards.
	"""

	def _init_devices(self):
		self._devices = set()
		self._assigned_devices = set()

		# FIXME: this is a blind shot, needs testing
		for device in self._hardware_inventory.get_devices("drm").match_sys_name("card*").match_property("DEVTYPE", "drm_minor"):
			self._devices.add(device.sys_name)

		self._free_devices = self._devices.copy()

	def _get_config_options(self):
		return {
			"radeon_powersave" : None,
		}

	def _instance_init(self, instance):
		instance._has_dynamic_tuning = False
		instance._has_static_tuning = True

	def _instance_cleanup(self, instance):
		pass

	def _radeon_powersave_files(self, device):
		return {
			"method" : "/sys/class/drm/%s/device/power_method" % device,
			"profile": "/sys/class/drm/%s/device/power_profile" % device,
		}

	@command_set("radeon_powersave", per_device=True)
	def _set_radeon_powersave(self, value, device):
		sys_files = self._radeon_powersave_files(device)
		if not os.path.exists(sys_files["method"]):
			log.warn("radeon_powersave is not supported on '%s'" % device)
			return

		if value in ["default", "auto", "low", "mid", "high"]:
			tuned.utils.commands.write_to_file(sys_files["method"], "profile")
			tuned.utils.commands.write_to_file(sys_files["profile"], value)
		elif value == "dynpm":
			tuned.utils.commands.write_to_file(sys_files["method"], "dynpm")
		else:
			log.warn("Invalid option for radeon_powersave.")

	@command_get("radeon_powersave")
	def _get_radeon_powersave(self, device):
		sys_files = self._radeon_powersave_files(device)
		return tuned.utils.commands.read_file(sys_files["profile"])
