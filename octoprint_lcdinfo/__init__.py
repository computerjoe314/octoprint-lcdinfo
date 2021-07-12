# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import octoprint.plugin
import octoprint.printer
import octoprint.events
import socket


class LcdInfo(
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.EventHandlerPlugin,
    octoprint.plugin.ProgressPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.SettingsPlugin):

    def __init__(self):
        self.waiting_for_preheat = False
        self.print_job_name = ""

    # Plugin startup
    def on_after_startup(self):
        self._logger.info("LcdInfo has started")

    # Events
    def on_event(self, event, payload):

        if event == octoprint.events.Events.PRINT_STARTED:
            self._printer.commands("M117 Printing {}".format(self.print_job_name))
            self.print_job_name = payload["name"]

            if self._settings.get(["M73"]):
                self._printer.commands("M73 P0")

        elif event == octoprint.events.Events.PRINT_FAILED:
            self._printer.commands("M117 Failed {}".format(self.print_job_name))

        elif event == octoprint.events.Events.PRINT_DONE:
            self._printer.commands("M117 Printed {} successfully.".format(self.print_job_name))

        elif event == octoprint.events.Events.PRINT_PAUSED:
            self._printer.commands("M117 Paused {}".format(self.print_job_name))

        elif event == octoprint.events.Events.PRINT_RESUMED:
            self._printer.commands("M117 Printing {}".format(self.print_job_name))

        elif event == octoprint.events.Events.CONNECTED:
            self._printer.commands("M117 Octoprint connected and available at {}".format(self.get_ip()))
            self._logger.info("Octoprint connected and available at {}".format(self.get_ip()))

    # Progress
    def on_print_progress(self, storage, path, progress):

        if self._settings.get(["M73"]):
            self._printer.commands("M73 P{}".format(progress))

    # G-Code M109 and M190 override the current LCD message, and do not allow any other G-Code until completed.
    # This is a workaround to still get the filename on the LCD.
    def flag_wait_for_preheat(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):

        if self.waiting_for_preheat:
            self._printer.commands("M117 Printing {}".format(self.print_job_name))
            self.waiting_for_preheat = False

        if gcode and (("M109" in gcode) or ("M190" in gcode)):
            self.waiting_for_preheat = True

    def get_ip(self):
        # Function credit to user "fatal-error" on StackOverflow
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't have to be reachable.
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '{}.local'.format(socket.gethostname())
        finally:
            s.close()
        return ip

    # Settings

    def get_settings_defaults(self):
        return {"M73": False}

    def get_template_vars(self):
        return {"M73": self._settings.get(["M73"])}

    def get_template_configs(self):
        return [
            {"type": "settings", "custom_bindings": False}
        ]

    # Updates


    def get_update_information(self, *args, **kwargs):
        return {'lcdinfo': {'displayName': self._plugin_name, 'displayVersion': self._plugin_version,
                            'type': "github_release",
                            'current': self._plugin_version, 'user': "computerjoe314",
                            'repo': "octoprint-lcdinfo",
                            'pip': "https://github.com/computerjoe314/octoprint-lcdinfo/archive/{target_version}.zip"}}


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = LcdInfo()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.comm.protocol.gcode.sent": __plugin_implementation__.flag_wait_for_preheat
    }


__plugin_name__ = "lcdinfo"
__plugin_version__ = "1.0.0"
__plugin_description__ = "Show Octoprint information on the printer's lcd screen"
__plugin_pythoncompat__ = ">=3.0,<4"
