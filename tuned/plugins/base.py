import tuned.consts as consts
import tuned.logs
import collections

log = tuned.logs.get()

class Plugin(object):
	"""
	Base class for all plugins.

	Plugins change various system settings in order to get desired performance or power
	saving. Plugins use Monitor objects to get information from the running system.

	Intentionally a lot of logic is included in the plugin to increase plugin flexibility.
	"""

	def __init__(self, monitors_repository, storage_factory, hardware_inventory, device_matcher, instance_factory, global_cfg):
		"""Plugin constructor."""

		self._storage = storage_factory.create(self.__class__.__name__)
		self._monitors_repository = monitors_repository
		self._hardware_inventory = hardware_inventory
		self._device_matcher = device_matcher
		self._instance_factory = instance_factory

		self._instances = collections.OrderedDict()
		self._init_commands()
		self._init_devices()

		self._global_cfg = global_cfg
		self._has_dynamic_options = False

		self._options_used_by_dynamic = self._get_config_options_used_by_dynamic()

	def cleanup(self):
		self.destroy_instances()

	@property
	def name(self):
		return self.__class__.__module__.split(".")[-1].split("_", 1)[1]

	#
	# Plugin configuration manipulation and helpers.
	#

	def _get_config_options(self):
		"""Default configuration options for the plugin."""
		return {}

	def _get_config_options_used_by_dynamic(self):
		"""List of config options used by dynamic tuning. Their previous values will be automatically saved and restored."""
		return []

	def _get_effective_options(self, options):
		"""Merge provided options with plugin default options."""
		# TODO: _has_dynamic_options is a hack
		effective = self._get_config_options().copy()
		for key in options:
			if key in effective or self._has_dynamic_options:
				effective[key] = options[key]
			else:
				log.warn("Unknown option '%s' for plugin '%s'." % (key, self.__class__.__name__))
		return effective

	def _option_bool(self, value):
		if type(value) is bool:
			return value
		value = str(value).lower()
		return value == "true" or value == "1"

	#
	# Interface for manipulation with instances of the plugin.
	#

	def create_instance(self, name, devices_expression, options):
		"""Create new instance of the plugin and seize the devices."""
		if name in self._instances:
			raise Exception("Plugin instance with name '%s' already exists." % name)

		effective_options = self._get_effective_options(options)
		instance = self._instance_factory.create(self, name, devices_expression, effective_options)
		self._instances[name] = instance

		return instance

	def destroy_instance(self, instance):
		"""Destroy existing instance."""
		if instance._plugin != self:
			raise Exception("Plugin instance '%s' does not belong to this plugin '%s'." % (instance, self))
		if instance.name not in self._instances:
			raise Exception("Plugin instance '%s' was already destroyed." % instance)

		instance = self._instances[instance.name]
		self._destroy_instance(instance)
		del self._instances[instance.name]

	def initialize_instances(self):
		"""Initialize all created instances."""
		for (instance_name, instance) in self._instances.items():
			log.debug("initializing instance %s (%s)" % (instance_name, self.name))
			self._instance_init(instance)

	def destroy_instances(self):
		"""Destroy all instances."""
		for instance in self._instances.values():
			log.debug("destroying instance %s (%s)" % (instance.name, self.name))
			self._destroy_instance(instance)
		self._instances.clear()

	def _destroy_instance(self, instance):
		self.release_devices(instance)
		self._instance_cleanup(instance)

	def _instance_init(self, instance):
		raise NotImplementedError()

	def _instance_cleanup(self, instance):
		raise NotImplementedError()

	#
	# Devices handling
	#

	def _init_devices(self):
		self._devices = None
		self._assigned_devices = set()
		self._free_devices = set()

	def _devices_supported(self):
		return self._devices is not None

	def _get_matching_devices(self, instance, devices):
		return set(self._device_matcher.match_list(instance.devices_expression, devices))

	def assign_free_devices(self):
		if not self._devices_supported():
			return

		log.debug("assigning devices to all instances")
		for instance_name, instance in reversed(self._instances.items()):
			to_assign = self._get_matching_devices(instance, self._free_devices)
			instance.active = len(to_assign) > 0
			if not instance.active:
				log.warn("instance %s: no matching devices available" % instance_name)
			else:
				log.info("instance %s: assigning devices %s" % (instance_name, ", ".join(to_assign)))
				instance.devices.update(to_assign) # cannot use |=
				self._assigned_devices |= to_assign
				self._free_devices -= to_assign

	def release_devices(self, instance):
		if not self._devices_supported():
			return

		to_release = instance.devices & self._devices

		instance.active = False
		instance.devices.clear()
		self._assigned_devices -= to_release
		self._free_devices |= to_release

	#
	# Tuning activation and deactivation.
	#

	def _run_for_each_device(self, instance, callback):
		if self._devices_supported():
			devices = instance.devices
		else:
			devices = [None, ]

		for device in devices:
			callback(instance, device)

	def instance_apply_tuning(self, instance):
		"""
		Apply static and dynamic tuning if the plugin instance is active.
		"""
		if not instance.active:
			return

		if instance.has_static_tuning:
			self._instance_apply_static(instance)
		if instance.has_dynamic_tuning and self._global_cfg.get("dynamic_tuning", consts.CFG_DEF_DYNAMIC_TUNING):
			self._run_for_each_device(instance, self._instance_apply_dynamic)

	def instance_update_tuning(self, instance):
		"""
		Apply dynamic tuning if the plugin instance is active.
		"""
		if not instance.active:
			return
		if instance.has_dynamic_tuning and self._global_cfg.get("dynamic_tuning", consts.CFG_DEF_DYNAMIC_TUNING):
			self._run_for_each_device(instance, self._instance_update_dynamic)

	def instance_unapply_tuning(self, instance):
		"""
		Remove all tunings applied by the plugin instance.
		"""
		if instance.has_dynamic_tuning and self._global_cfg.get("dynamic_tuning", consts.CFG_DEF_DYNAMIC_TUNING):
			self._run_for_each_device(instance, self._instance_unapply_dynamic)
		if instance.has_static_tuning:
			self._instance_unapply_static(instance)

	def _instance_apply_static(self, instance):
		self._execute_all_non_device_commands(instance)
		self._execute_all_device_commands(instance, instance.devices)

	def _instance_unapply_static(self, instance):
		self._cleanup_all_device_commands(instance, instance.devices)
		self._cleanup_all_non_device_commands(instance)

	def _instance_apply_dynamic(self, instance, device):
		for option in filter(lambda opt: self._storage_get(instance, self._commands[opt], device) is None, self._options_used_by_dynamic):
			self._save_current_value(instance, self._commands[option], device)

		self._instance_update_dynamic(instance, device)

	def _instance_unapply_dynamic(self, instance, device):
		raise NotImplementedError()

	def _instance_update_dynamic(self, instance, device):
		raise NotImplementedError()

	#
	# Registration of commands for static plugins.
	#

	def _init_commands(self):
		"""
		Initialize commands.
		"""
		self._commands = collections.OrderedDict()
		self._autoregister_commands()
		self._check_commands()

	def _autoregister_commands(self):
		"""
		Register all commands marked using @command_set, @command_get, and @command_custom decorators.
		"""
		for member_name in self.__class__.__dict__:
			if member_name.startswith("__"):
				continue
			member = getattr(self, member_name)
			if not hasattr(member, "_command"):
				continue

			command_name = member._command["name"]
			info = self._commands.get(command_name, {"name": command_name})

			if "set" in member._command:
				info["custom"] = None
				info["set"] = member
				info["per_device"] = member._command["per_device"]
				info["priority"] = member._command["priority"]
			elif "get" in member._command:
				info["get"] = member
			elif "custom" in member._command:
				info["custom"] = member
				info["per_device"] = member._command["per_device"]
				info["priority"] = member._command["priority"]

			self._commands[command_name] = info

		# sort commands by priority
		self._commands = collections.OrderedDict(sorted(self._commands.iteritems(), key=lambda (name, info): info["priority"]))

	def _check_commands(self):
		"""
		Check if all commands are defined correctly.
		"""
		for command_name, command in self._commands.iteritems():
			# do not check custom commands
			if command.get("custom", False):
				continue
			# automatic commands should have 'get' and 'set' functions
			if "get" not in command or "set" not in command:
				raise TypeError("Plugin command '%s' is not defined correctly" % command_name)

	#
	# Operations with persistent storage for status data.
	#

	def _storage_key(self, instance_name, command_name, device_name=None):
		if device_name is not None:
			return "%s/%s/%s" % (command_name, instance_name, device_name)
		else:
			return "%s/%s" % (command_name, instance_name)

	def _storage_set(self, instance, command, value, device_name=None):
		key = self._storage_key(instance.name, command["name"], device_name)
		self._storage.set(key, value)

	def _storage_get(self, instance, command, device_name=None):
		key = self._storage_key(instance.name, command["name"], device_name)
		return self._storage.get(key)

	def _storage_unset(self, instance, command, device_name=None):
		key = self._storage_key(instance.name, command["name"], device_name)
		return self._storage.unset(key)

	#
	# Command execution and cleanup.
	#

	def _execute_all_non_device_commands(self, instance):
		for command in filter(lambda command: not command["per_device"], self._commands.values()):
			new_value = instance.options.get(command["name"], None)
			if new_value is not None:
				self._execute_non_device_command(instance, command, new_value)

	def _execute_all_device_commands(self, instance, devices):
		for command in filter(lambda command: command["per_device"], self._commands.values()):
			new_value = instance.options.get(command["name"], None)
			if new_value is None:
				continue
			for device in devices:
				self._execute_device_command(instance, command, device, new_value)

	def _save_current_value(self, instance, command, device = None):
		if device is not None:
			current_value = command["get"](device)
		else:
			current_value = command["get"]()
		if current_value is not None:
			self._storage_set(instance, command, current_value, device)

	def _execute_device_command(self, instance, command, device, new_value):
		if command["custom"] is not None:
			command["custom"](True, new_value, device)
		else:
			self._save_current_value(instance, command, device)
			command["set"](new_value, device)

	def _execute_non_device_command(self, instance, command, new_value):
		if command["custom"] is not None:
			command["custom"](True, new_value)
		else:
			self._save_current_value(instance, command)
			command["set"](new_value)

	def _cleanup_all_non_device_commands(self, instance):
		for command in filter(lambda command: not command["per_device"], self._commands.values()):
			if (instance.options.get(command["name"], None) is not None) or (command["name"] in self._options_used_by_dynamic):
				self._cleanup_non_device_command(instance, command)

	def _cleanup_all_device_commands(self, instance, devices):
		for command in filter(lambda command: command["per_device"], self._commands.values()):
			if (instance.options.get(command["name"], None) is not None) or (command["name"] in self._options_used_by_dynamic):
				for device in devices:
					self._cleanup_device_command(instance, command, device)

	def _cleanup_device_command(self, instance, command, device):
		if command["custom"] is not None:
			command["custom"](False, None, device)
		else:
			old_value = self._storage_get(instance, command, device)
			if old_value is not None:
				command["set"](old_value, device)
			self._storage_unset(instance, command, device)

	def _cleanup_non_device_command(self, instance, command):
		if command["custom"] is not None:
			command["custom"](False, None)
		else:
			old_value = self._storage_get(instance, command)
			if old_value is not None:
				command["set"](old_value)
			self._storage_unset(instance, command)
