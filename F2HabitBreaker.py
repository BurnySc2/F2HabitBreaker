import sys, functools, json
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QMenu, QAction
from screeninfo import get_monitors
import requests


class F2HabitBreaker(QMainWindow):
    def __init__(self):
        super().__init__()

        # One of "game" or "menu"
        self.location = "game"
        self.ui_url = "http://localhost:6119/ui"
        # Target opacity level of the window
        self.window_target_opacity = 0

        self.availableMonitors = []
        monitors = get_monitors()
        for monitor in monitors:
            # Monitor:
            # => [monitor.x, monitor.y, monitor.width, monitor.height]
            # => [0, 0, 1920, 1080]    [ x start, y start, x end, y end ]

            # Get the resolution so we can find the correct position
            X = monitor.width
            Y = monitor.height
            resolution = str(X) + "x" + str(Y)

            # Offsets to add to button position to put it on the right monitor
            xOffset = monitor.x
            yOffset = monitor.y

            self.availableMonitors.append({"resolution": resolution, "xOffset": xOffset, "yOffset": yOffset})


        # Run self.tick function every 1000ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(5000)

        self.placeWindow(0)

        # Dont render frame, and always have window on top
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.show()

    def updateGameLocation(self):
        """ Use the SC2 client API to get information about the location in game, if the usesr is in menu or in game. """
        client_api_ui_response = requests.get(self.ui_url)
        if client_api_ui_response.status_code == 200:
            client_api_ui_data = client_api_ui_response.json()
            if client_api_ui_data["activeScreens"]:
                self.location = "menu"
            else:
                self.location = "game"

    def updateTransparency(self):
        """ Use the information gathered above to set the opacity to 0 if user is out of game. """
        if self.location == "game":
            self.setProperty("windowOpacity", self.window_target_opacity)
        elif self.location == "menu":
            self.setProperty("windowOpacity", 0)

    def tick(self):
        self.updateGameLocation()
        self.updateTransparency()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        for monitor in self.availableMonitors:
            menu.addAction(
                QAction(
                    str(self.availableMonitors.index(monitor)) + ": " + monitor["resolution"],
                    self,
                    triggered=functools.partial(self.placeWindow, self.availableMonitors.index(monitor)),
                )
            )

        menu.addSection("")
        menu.addAction(QAction("Quit", self, triggered=self.quit))
        menu.exec_(event.globalPos())

    def getProfiles(self):
        with open("F2HabitBreaker.json", "r") as f:
            profiles = json.load(f)
            return profiles

    def placeWindow(self, monitorId):
        # find the right position for this resolution
        profile = None
        for f2Profile in self.getProfiles():
            if f2Profile["resolution"] == self.availableMonitors[monitorId]["resolution"]:
                profile = f2Profile

        # if we havent found it then we need to quit                  (uh quitting probably isnt actually the best option?)
        if profile is None:
            print("Unsupported resolution: ")

            QMessageBox.information(
                self,
                "Message",
                "Unsupported Resolution: " + self.availableMonitors[monitorId]["resolution"],
                QMessageBox.Ok,
            )
            self.quit()
        # or if we have found it, we can move/resize the window into place
        else:
            self.resize(profile["width"], profile["height"])
            self.move(
                profile["x-offset"] + self.availableMonitors[monitorId]["xOffset"],
                profile["y-offset"] + self.availableMonitors[monitorId]["yOffset"],
            )
            self.setStyleSheet(
                "QMainWindow { background-color: rgba("
                + str(profile["red"])
                + ", "
                + str(profile["green"])
                + ", "
                + str(profile["blue"])
                + ", 1); }"
            )
            self.window_target_opacity = profile["transparency"] if profile["transparency"] > 0 else 0.01
            self.setProperty("windowOpacity", self.window_target_opacity)

    def quit(self):
        sys.exit()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    F2 = F2HabitBreaker()
    app.exec_()
