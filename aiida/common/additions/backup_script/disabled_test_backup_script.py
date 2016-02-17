# -*- coding: utf-8 -*-
import unittest
import datetime
import json

# Import needed for date parsing
from dateutil.parser import parse

# Import needed for Django initialization
from aiida.backends.djsite.utils import load_dbenv

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Spyros Zoupanos, Giovanni Pizzi, Martin Uhrin"


class UnitTests(unittest.TestCase):

    _json_test_input_1 = '{"backup_length_threshold": 2, "periodicity": 2,' + \
        ' "oldest_object_backedup": "2014-07-18 13:54:53.688484+00:00", ' + \
        '"end_date_of_backup": null, "days_to_backup": null, "backup_dir": ' +\
        '"/scratch/aiida_user/backupScriptDest"}'

    _json_test_input_2 = '{"backup_length_threshold": 2, "periodicity": 2, ' +\
        '"oldest_object_backedup": "2014-07-18 13:54:53.688484+00:00", ' + \
        '"end_date_of_backup": null, "days_to_backup": null, "backup_dir": ' +\
        '"/scratch/aiida_user/backupScriptDest"}'

    _json_test_input_3 = '{"backup_length_threshold": 2, "periodicity": 2, ' +\
        '"oldest_object_backedup": "2014-07-18 13:54:53.688484+00:00", ' + \
        '"end_date_of_backup": null, "days_to_backup": 2, "backup_dir": ' + \
        '"/scratch/aiida_user/backupScriptDest"}'

    _json_test_input_4 = '{"backup_length_threshold": 2, "periodicity": 2, ' +\
        '"oldest_object_backedup": "2014-07-18 13:54:53.688484+00:00", ' + \
        '"end_date_of_backup": "2014-07-22 14:54:53.688484+00:00", ' + \
        '"days_to_backup": null, "backup_dir": ' + \
        '"/scratch/aiida_user/backupScriptDest"}'

    _json_test_input_5 = '{"backup_length_threshold": 2, "periodicity": 2, ' +\
        '"oldest_object_backedup": "2014-07-18 13:54:53.688484+00:00", ' + \
        '"end_date_of_backup": "2014-07-22 14:54:53.688484+00:00", ' + \
        '"days_to_backup": 2, "backup_dir": "/scratch/aiida_user/backup"}'

    _json_test_input_6 = '{"backup_length_threshold": 2, "periodicity": 2, ' +\
        '"oldest_object_backedup": "2014-07-18 13:54:53.688484", ' + \
        '"end_date_of_backup": "2014-07-22 14:54:53.688484", ' + \
        '"days_to_backup": null, ' \
        '"backup_dir": "/scratch/./aiida_user////backup//"}'

    def setUp(self):
        load_dbenv()
        import backup
        
        self._backup_setup_inst = backup.Backup("", 2)

    def tearDown(self):
        self._backup_setup_inst = None

    def test_loading_basic_params_from_file(self):
        """
        This method tests the correct loading of the basic _backup_setup_inst
        parameters from a JSON string.
        """
        backup_variables = json.loads(self._json_test_input_1)
        self._backup_setup_inst._ignore_backup_dir_existence_check = True
        self._backup_setup_inst._read_backup_info_from_dict(backup_variables)
         
        self.assertEqual(
            self._backup_setup_inst._oldest_object_bk,
            parse("2014-07-18 13:54:53.688484+00:00"),
            "Last _backup_setup_inst start date is not parsed correctly")

        # The destination directory of the _backup_setup_inst
        self.assertEqual(
            self._backup_setup_inst._backup_dir,
            "/scratch/aiida_user/backupScriptDest",
            "_backup_setup_inst destination directory not parsed correctly")
        
        self.assertEqual(
            self._backup_setup_inst._backup_length_threshold,
            datetime.timedelta(hours=2),
            "_backup_length_threshold not parsed correctly")
        
        self.assertEqual(
            self._backup_setup_inst._periodicity,
            2,
            "_periodicity not parsed correctly")

    def test_loading_backup_time_params_from_file_1(self):
        """
        This method tests that the _backup_setup_inst limits are correctly
        loaded from the JSON string and are correctly set.
        
        In the parsed JSON string, no _backup_setup_inst end limits are set
        """
        backup_variables = json.loads(self._json_test_input_2)
        self._backup_setup_inst._ignore_backup_dir_existence_check = True
        self._backup_setup_inst._read_backup_info_from_dict(backup_variables)
        
        self.assertEqual(
            self._backup_setup_inst._days_to_backup,
            None,
            "_days_to_backup should be None/null but it is not")
        
        self.assertEqual(
            self._backup_setup_inst._end_date_of_backup,
            None,
            "_end_date_of_backup should be None/null but it is not")
        
        self.assertEqual(
            self._backup_setup_inst._internal_end_date_of_backup,
            None,
            "_internal_end_date_of_backup should be None/null but it is not")

    def test_loading_backup_time_params_from_file_2(self):
        """
        This method tests that the _backup_setup_inst limits are correctly
        loaded from the JSON string and are correctly set.
        
        In the parsed JSON string, only the daysToBackup limit is set.
        """
        backup_variables = json.loads(self._json_test_input_3)
        self._backup_setup_inst._ignore_backup_dir_existence_check = True
        self._backup_setup_inst._read_backup_info_from_dict(backup_variables)

        self.assertEqual(
            self._backup_setup_inst._days_to_backup,
            2,
            "_days_to_backup should be 2 but it is not")
        
        self.assertEqual(
            self._backup_setup_inst._end_date_of_backup,
            None,
            "_end_date_of_backup should be None/null but it is not")
        
        self.assertEqual(
            self._backup_setup_inst._internal_end_date_of_backup,
            parse("2014-07-20 13:54:53.688484+00:00"),
            "_internal_end_date_of_backup is not the expected one")

    def test_loading_backup_time_params_from_file_3(self):
        """
        This method tests that the _backup_setup_inst limits are correctly
        loaded from the JSON string and are correctly set.
        
        In the parsed JSON string, only the endDateOfBackup limit is set.
        """
        backup_variables = json.loads(self._json_test_input_4)
        self._backup_setup_inst._ignore_backup_dir_existence_check = True
        self._backup_setup_inst._read_backup_info_from_dict(backup_variables)

        self.assertEqual(
            self._backup_setup_inst._days_to_backup,
            None,
            "_days_to_backup should be None/null but it is not")
        
        self.assertEqual(
            self._backup_setup_inst._end_date_of_backup,
            parse("2014-07-22 14:54:53.688484+00:00"),
            "_end_date_of_backup should be None/null but it is not")
        
        self.assertEqual(
            self._backup_setup_inst._internal_end_date_of_backup,
            parse("2014-07-22 14:54:53.688484+00:00"),
            "_internal_end_date_of_backup is not the expected one")

    def test_loading_backup_time_params_from_file_4(self):
        """
        This method tests that the _backup_setup_inst limits are correctly
        loaded from the JSON string and are correctly set.
        
        In the parsed JSON string, the endDateOfBackup & daysToBackuplimit
        are set which should lead to an exception.
        """
        from backup import BackupError
        
        backup_variables = json.loads(self._json_test_input_5)
        self._backup_setup_inst._ignore_backup_dir_existence_check = True
        # An exception should be raised because endDateOfBackup
        # & daysToBackuplimit have been defined in the same time.
        with self.assertRaises(BackupError):
            self._backup_setup_inst._read_backup_info_from_dict(backup_variables)

    def test_full_deserialization_serialization(self):
        """
        This method tests the correct deserialization / serialization of the 
        variables that should be stored in a file.
        """
        
        for input_string in (self._json_test_input_1, self._json_test_input_2,
                             self._json_test_input_3, self._json_test_input_4):
            
            import backup
            backup_inst = backup.Backup("", 2)
            
            input_variables = json.loads(input_string)
            backup_inst._ignore_backup_dir_existence_check = True
            backup_inst._read_backup_info_from_dict(input_variables)
            target_variables = backup_inst._dictionarize_backup_info()
            
            self.assertIs(cmp(input_variables, target_variables), 0,
                          "The test string {} did not succeed".format(
                              input_string) +
                          " the serialization deserialization test.\n" +
                          "Input variables: {}\n".format(input_variables) +
                          "Output variables: {}\n".format(target_variables))

    def test_timezone_addition_and_dir_correction(self):
        """
        This method tests if the timezone is added correctly to timestamps
        that don't have a timezone. Moreover, it checks if the given directory
        paths are normalized as expected.
        """
        backup_variables = json.loads(self._json_test_input_6)
        self._backup_setup_inst._ignore_backup_dir_existence_check = True
        self._backup_setup_inst._read_backup_info_from_dict(backup_variables)

        self.assertIsNotNone(
            self._backup_setup_inst._oldest_object_bk.tzinfo,
            "Timezone info should not be none (timestamp: {})."
            .format(self._backup_setup_inst._oldest_object_bk))

        self.assertIsNotNone(
            self._backup_setup_inst._end_date_of_backup.tzinfo,
            "Timezone info should not be none (timestamp: {})."
            .format(self._backup_setup_inst._end_date_of_backup))

        self.assertIsNotNone(
            self._backup_setup_inst._internal_end_date_of_backup.tzinfo,
            "Timezone info should not be none (timestamp: {})."
            .format(self._backup_setup_inst._internal_end_date_of_backup))

        # The destination directory of the _backup_setup_inst
        self.assertEqual(
            self._backup_setup_inst._backup_dir,
            "/scratch/aiida_user/backup",
            "_backup_setup_inst destination directory is not normalized as expected.")

if __name__ == "__main__":
    unittest.main()
