import logging

from PySide2 import QtWidgets, QtCore
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
import pymel.core as pmc

from pymel.core.system import Path

log = logging.getLogger(__name__)


def maya_main_window():
    """Return the maya main window widget"""
    main_window = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window), QtWidgets.QWidget)


class SmartSaveUI(QtWidgets.QDialog):
    """Smart save ui class"""

    def __init__(self):
        super(SmartSaveUI, self).__init__(parent=maya_main_window())
        self.setWindowTitle("Smart Save")
        self.setMinimumWidth(500)
        self.setMaximumHeight(200)
        self.setWindowFlags(self.windowFlags() ^
                            QtCore.Qt.WindowContextHelpButtonHint)
        self.create_ui()

    def create_ui(self):
        self.title_lbl = QtWidgets.QLabel("Smart Save")
        self.title_lbl.setStyleSheet("font: bold 20px")
        self.main_lay = QtWidgets.QVBoxLayout()
        self.main_lay.addWidget(self.title_lbl)
        self.setLayout(self.main_lay)


class SceneFile(object):
    def __init__(self, path=None):
        self.folder_path = Path()
        self.descriptor = 'main'
        self.task = None
        self.ver = 1
        self.ext = '.ma'
        scene = pmc.system.sceneName()
        if not path and scene:
            path = scene
        if not path and not scene:
            log.warning("Unable to initialize SceneFile object from a new"
                        "scene. Please specify a path")
            return
        self._init_from_path(path)

    @property
    def filename(self):
        pattern = "{descriptor}_{task}_v{ver:03d}{ext}"
        return pattern.format(descriptor=self.descriptor,
                              task=self.task,
                              ver=self.ver,
                              ext=self.ext)

    @property
    def path(self):
        return self.folder_path / self.filename

    def _init_from_path(self, path):
        path = Path(path)
        self.folder_path = path.parent
        self.ext = path.ext
        self.descriptor, self.task, ver = path.name.stripext().split("_")
        self.ver = int(ver.split("v")[-1])

    def save(self):
        try:
            return pmc.system.saveAs(self.path)
        except RuntimeError as err:
            log.warning("Missing directories in path. Creating directories...")
            self.folder_path.makedirs_p()
            return pmc.system.saveAs(self.path)

    def next_avail_ver(self):
        pattern = "{descriptor}_{task}_v*{ext}".format(
            descriptor=self.descriptor,
            task=self.task,
            ext=self.ext)
        matching_scene_files = []
        for file_ in self.folder_path.files():
            if file_.name.fnmatch(pattern):
                matching_scene_files.append(file_)
        if not matching_scene_files:
            return 1;

        matching_scene_files.sort(reverse=True)
        latest_scene_file = matching_scene_files[0]
        latest_scene_file = latest_scene_file.name.stripext()
        latest_ver_num = int(latest_scene_file.split("_v")[-1])
        return latest_ver_num + 1

    def increment_save(self):
        self.ver = self.next_avail_ver()
        self.save()