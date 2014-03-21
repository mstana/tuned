import base
from decorators import *
import tuned.logs
from subprocess import *

log = tuned.logs.get()

class SysctlPlugin(base.Plugin):
	"""
	Plugin for applying custom sysctl options.
	"""

	def __init__(self, *args, **kwargs):
		super(self.__class__, self).__init__(*args, **kwargs)
		self._has_dynamic_options = True

	def _sysctl_storage_key(self, instance):
		return "%s/options" % instance.name

	def _instance_init(self, instance):
		instance._has_dynamic_tuning = False
		instance._has_static_tuning = True

		# FIXME: do we want to do this here?
		# recover original values in case of crash
		instance._sysctl_original = self._storage.get(self._sysctl_storage_key(instance), {})
		if len(instance._sysctl_original) > 0:
			log.info("recovering old sysctl settings from previous run")
			self._instance_unapply_static(instance)
			instance._sysctl_original = {}
			self._storage.unset(self._sysctl_storage_key(instance))

		instance._sysctl = instance.options

	def _instance_cleanup(self, instance):
		self._storage.unset(self._sysctl_storage_key(instance))

	def _instance_apply_static(self, instance):
		for option, value in instance._sysctl.iteritems():
			original_value = self._read_sysctl(option)
			if original_value != None:
				instance._sysctl_original[option] = original_value
			self._write_sysctl(option, value)

		self._storage.set("options", instance._sysctl_original)

	def _instance_unapply_static(self, instance):
		for option, value in instance._sysctl_original.iteritems():
			self._write_sysctl(option, value)

	def _execute_sysctl(self, arguments):
		execute = ["/sbin/sysctl"] + arguments
		log.debug("executing %s" % execute)
		return tuned.utils.commands.execute(execute)

	def _read_sysctl(self, option):
		retcode, stdout = self._execute_sysctl(["-e", option])
		if retcode == 0:
			parts = map(lambda value: value.strip(), stdout.split("=", 1))
			if len(parts) == 2:
				option, value = parts
				return value
		return None

	def _write_sysctl(self, option, value):
		retcode, stdout = self._execute_sysctl(["-q", "-w", "%s=%s" % (option, value)])
		return retcode == 0
