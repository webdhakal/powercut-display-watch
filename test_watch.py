import importlib.machinery
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

class WatchTests(unittest.TestCase):
    def setUp(self):
        loader = importlib.machinery.SourceFileLoader('watch', str(Path(__file__).with_name('powercut-display-watch')))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        try:
            self.w = importlib.util.module_from_spec(spec)
            loader.exec_module(self.w)
        except SyntaxError:
            self.fail('Watcher still uses the incompatible GNOME shell implementation')

    def test_mint_charger_detection(self):
        with tempfile.TemporaryDirectory() as root:
            charger = Path(root) / 'ADP0'
            charger.mkdir()
            (charger / 'type').write_text('Mains\n')
            (charger / 'online').write_text('1\n')
            self.assertEqual(self.w.find_ac(Path(root)), charger / 'online')

    def test_restore_preserves_mint_display_layout(self):
        text = '''Screen 0: current 3840 x 1080
eDP-1 connected primary 1920x1080+1920+0 (normal left inverted right x axis y axis)
   1920x1080 60.00*+
DP-1 connected 1920x1080+0+0 (normal left inverted right x axis y axis)
   1920x1080 60.00*+ 165.00
HDMI-1 disconnected (normal left inverted right x axis y axis)
'''
        outputs = self.w.parse_outputs(text)
        self.assertEqual(outputs[0]['pos'], '1920x0')
        self.assertEqual(outputs[1]['name'], 'DP-1')
        self.assertEqual(outputs[1]['rate'], '60.00')
        cmd = self.w.restore_command(outputs)
        self.assertIn('1920x0', cmd)
        self.assertIn('--primary', cmd)
        self.assertNotIn('HDMI-1', cmd)

    def test_power_restoration_cancelled_if_charger_drops_again(self):
        ac = unittest.mock.Mock()
        ac.read_text.return_value = '0'
        with patch.object(self.w, 'run') as run:
            self.assertFalse(self.w.restore({'outputs': [], 'profile': '', 'sink': ''}, ac))
            run.assert_not_called()

class AudioPriorityTests(unittest.TestCase):
    setUp = WatchTests.setUp
    def cards(self, wired=False, monitor=True, usb=False):
        cards = [{'name': self.w.CARD, 'properties': {}, 'active_profile': 'output:hdmi-stereo',
                  'profiles': {'output:analog-stereo+input:analog-stereo': {'available': True},
                               'output:hdmi-stereo+input:analog-stereo': {'available': True}},
                  'ports': {
                      'analog-output-headphones': {'type': 'Headphones', 'availability': 'available' if wired else 'not available', 'profiles': ['output:analog-stereo+input:analog-stereo']},
                      'analog-output-speaker': {'type': 'Speaker', 'availability': 'availability unknown', 'profiles': ['output:analog-stereo+input:analog-stereo']},
                      'hdmi-output-0': {'type': 'HDMI', 'availability': 'available' if monitor else 'not available', 'profiles': ['output:hdmi-stereo+input:analog-stereo']}}}]
        if usb:
            cards.append({'name': 'alsa_card.usb-FANTECH_FUSION', 'properties': {},
                          'profiles': {'output:analog-stereo': {'available': True}},
                          'ports': {'analog-output-speaker': {'type': 'Speaker', 'availability': 'availability unknown', 'profiles': ['output:analog-stereo']}}})
        return cards

    def test_usb_headset_before_monitor(self):
        choice = self.w.choose_audio(self.cards(usb=True), [], True)
        self.assertEqual(choice['card'], 'alsa_card.usb-FANTECH_FUSION')

    def test_wired_headphones_before_monitor(self):
        choice = self.w.choose_audio(self.cards(wired=True), [], True)
        self.assertEqual(choice['port'], 'analog-output-headphones')

    def test_monitor_when_headphones_absent(self):
        self.assertEqual(self.w.choose_audio(self.cards(), [], True)['port'], 'hdmi-output-0')

    def test_laptop_when_monitor_unavailable(self):
        self.assertEqual(self.w.choose_audio(self.cards(monitor=False), [], True)['port'], 'analog-output-speaker')

    def test_powercut_ignores_stale_monitor_detection(self):
        self.assertEqual(self.w.choose_audio(self.cards(), [], False)['port'], 'analog-output-speaker')

    def test_powercut_keeps_headset(self):
        self.assertEqual(self.w.choose_audio(self.cards(usb=True), [], False)['card'], 'alsa_card.usb-FANTECH_FUSION')

    def test_bluetooth_headphones_before_monitor(self):
        sinks = [{'name': 'bluez_output.test', 'description': 'Wireless Headphones', 'properties': {}, 'ports': [], 'active_port': None}]
        self.assertEqual(self.w.choose_audio(self.cards(), sinks, True)['sink'], 'bluez_output.test')

    def test_generic_usb_speakers_are_not_headphones(self):
        cards = self.cards(usb=True)
        cards[-1]['name'] = 'alsa_card.usb-desktop-speakers'
        self.assertEqual(self.w.choose_audio(cards, [], True)['port'], 'hdmi-output-0')

if __name__ == '__main__':
    unittest.main()
