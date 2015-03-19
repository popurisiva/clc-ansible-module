import clc_server
import clc as clc_sdk
import mock
from mock import patch, create_autospec
import os
import unittest

class TestClcServerFunctions(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter=mock.MagicMock()

    def test_clc_set_credentials_w_creds(self):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'hansolo', 'CLC_V2_API_PASSWD': 'falcon'}):
            clc_server._clc_set_credentials(self.clc, self.module)

        self.clc.v2.SetCredentials.assert_called_once_with(api_username='hansolo', api_passwd='falcon')


    def test_clc_set_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            clc_server._clc_set_credentials(self.clc, self.module)
            self.assertEqual(self.module.fail_json.called, True)

    @patch.object(clc_server, '_find_group')
    def test_find_running_servers_by_group_name(self, mock_find_group):
        # Setup
        mock_group = create_autospec(clc_sdk.v2.Group)

        mock_running_server = mock.MagicMock()
        mock_running_server.status = 'active'
        mock_running_server.powerState = 'started'

        mock_stopped_server = mock.MagicMock()
        mock_stopped_server.status = 'active'
        mock_stopped_server.powerState = 'stopped'

        mock_group.Servers().Servers.return_value = [mock_running_server, mock_stopped_server]
        mock_find_group.return_value = mock_group

        # Function Under Test
        result_servers, result_runningservers = clc_server._find_running_servers_by_group_name(self.module, self.clc, self.datacenter, "MyCoolGroup")

        # Results
        mock_find_group.assert_called_once_with(module=self.module, clc=self.clc, datacenter=self.datacenter, lookup_group="MyCoolGroup")
        self.assertEqual(len(result_servers), 2)
        self.assertEqual(len(result_runningservers),1)

        self.assertIn(mock_running_server, result_runningservers)
        self.assertNotIn(mock_stopped_server, result_runningservers)

        self.assertIn(mock_running_server, result_servers)
        self.assertIn(mock_stopped_server, result_servers)

    def test_find_datacenter(self):
        # Setup Mocks
        def getitem(name):
            return "MyMockGroup"
        self.module.params.__getitem__.side_effect = getitem

        # Function Under Test
        clc_server._find_datacenter(module=self.module, clc=self.clc)

        # assert result
        self.clc.v2.Datacenter.assert_called_once_with("MyMockGroup")

    def test_find_group_w_lookup_group(self):
        # Setup
        self.datacenter.Groups().Get = mock.MagicMock()

        # Function Under Test
        result_group = clc_server._find_group(self.module, self.clc, self.datacenter, "MyCoolGroup")

        # Assert Result
        self.datacenter.Groups().Get.assert_called_once_with("MyCoolGroup")
        self.assertEqual(self.module.called, False)

    def test_find_group_w_no_lookup_group(self):
        # Setup
        self.datacenter.Groups().Get = mock.MagicMock()
        self.module.params = {'group': "DefaultGroupFromModuleParamsLookup"}

        # Function Under Test
        result_group = clc_server._find_group(self.module, self.clc, self.datacenter)

        # Assert Result
        self.datacenter.Groups().Get.assert_called_once_with("DefaultGroupFromModuleParamsLookup")

    def test_find_group_w_group_not_found(self):
        # Setup
        self.datacenter.Groups().Get = mock.Mock(side_effect=clc_sdk.CLCException("Group not found"))

        # Function Under Test
        result_group = clc_server._find_group(self.module, self.clc, self.datacenter)

        # Assert Result
        self.assertEqual(self.module.fail_json.called, True)

    def test_find_template(self):
        self.module.params = {"template": "MyCoolTemplate"}
        self.datacenter.Templates().Search = mock.MagicMock()

        # Function Under Test
        result_template = clc_server._find_template(module=self.module, clc=self.clc, datacenter=self.datacenter)

        # Assert Result
        self.datacenter.Templates().Search.assert_called_once_with("MyCoolTemplate")
        self.assertEqual(self.module.fail_json.called, False)

    def test_find_template_not_found(self):
        self.module.params = {"template": "MyCoolTemplateNotFound"}
        self.datacenter.Templates().Search = mock.MagicMock(side_effect=clc_sdk.CLCException("Template not found"))

        # Function Under Test
        result_template = clc_server._find_template(module=self.module, clc=self.clc, datacenter=self.datacenter)

        # Assert Result
        self.datacenter.Templates().Search.assert_called_once_with("MyCoolTemplateNotFound")
        self.assertEqual(self.module.fail_json.called, True)

    def test_find_default_network(self):
        # Setup
        self.datacenter.Networks().networks = ['TestReturnVlan']

        # Function Under Test
        result = clc_server._find_default_network(self.module, self.clc, self.datacenter)

        # Assert Result
        self.assertEqual(result, 'TestReturnVlan')
        self.assertEqual(self.module.fail_json.called, False)

    def test_find_default_network_not_found(self):
        # Setup
        self.datacenter.Networks = mock.MagicMock(side_effect=clc_sdk.CLCException("Network not found"))

        # Function Under Test
        result = clc_server._find_default_network(self.module, self.clc, self.datacenter)

        # Assert Result
        self.assertEqual(self.module.fail_json.called, True)

    def test_validate_name(self):
        # Setup
        self.module.params = {"name": "MyName"}  # Name is 6 Characters - Pass

        # Function Under Test
        result = clc_server._validate_name(self.module)

        # Assert Result
        self.assertEqual(result, "MyName")
        self.assertEqual(self.module.fail_json.called, False)

    def test_validate_name_too_long(self):
        # Setup
        self.module.params = {"name": "MyNameIsTooLong"}  # Name is >6 Characters - Fail

        # Function Under Test
        result = clc_server._validate_name(self.module)

        # Assert Result
        self.assertEqual(self.module.fail_json.called, True)

    def test_validate_name_too_short(self):
        # Setup
        self.module.params = {"name": ""}  # Name is <1 Characters - Fail

        # Function Under Test
        result = clc_server._validate_name(self.module)

        # Assert Result
        self.assertEqual(self.module.fail_json.called, True)

if __name__ == '__main__':
    unittest.main()