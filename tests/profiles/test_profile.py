import unittest
import tuned.profiles

class MockProfile(tuned.profiles.profile.Profile):
	def _create_unit(self, name, config):
		return (name, config)

class ProfileTestCase(unittest.TestCase):

	def test_init(self):
		MockProfile("test", {})

	def test_create_units(self):
		profile = MockProfile("test", {
			"main": { "anything": 10 },
			"network" : { "type": "net", "devices": "*" },
			"storage" : { "type": "disk" },
		})

		self.assertIs(type(profile.units), list)
		self.assertEqual(len(profile.units), 2)
		self.assertListEqual(sorted(map(lambda (name, config): name, profile.units)), sorted(["network", "storage"]))

	def test_create_units_empty(self):
		profile = MockProfile("test", {"main":{}})

		self.assertIs(type(profile.units), list)
		self.assertEqual(len(profile.units), 0)

	def test_sets_name(self):
		profile1 = MockProfile("test_one", {})
		profile2 = MockProfile("test_two", {})
		self.assertEqual(profile1.name, "test_one")
		self.assertEqual(profile2.name, "test_two")

	def test_change_name(self):
		profile = MockProfile("oldname", {})
		self.assertEqual(profile.name, "oldname")
		profile.name = "newname"
		self.assertEqual(profile.name, "newname")

	def test_sets_options(self):
		profile = MockProfile("test", {
			"main": { "anything": 10 },
			"network" : { "type": "net", "devices": "*" },
		})

		self.assertIs(type(profile.options), dict)
		self.assertEquals(profile.options["anything"], 10)

	def test_sets_options_empty(self):
		profile = MockProfile("test", {
			"storage" : { "type": "disk" },
		})

		self.assertIs(type(profile.options), dict)
		self.assertEquals(len(profile.options), 0)
