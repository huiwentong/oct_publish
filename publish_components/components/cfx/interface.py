from dataclasses import dataclass, field, asdict
from publish_components.core import InterFace
from qtpy import QtWidgets, QtCore, QtGui, QtUiTools
import os

from qtpy.QtCore import Qt
from pprint import pprint
from publish_core.database.entity import FastSg, SGEntity
from pathlib import Path
from .publish_file_ui import Ui_Form


class Ui_ChoicesDialog(object):
    def setupUi(self, ChoicesDialog):
        ChoicesDialog.setObjectName("ChoicesDialog")
        ChoicesDialog.resize(400, 350)
        self.verticalLayout = QtWidgets.QVBoxLayout(ChoicesDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.listWidget = QtWidgets.QListWidget(ChoicesDialog)
        self.listWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout.addWidget(self.listWidget)
        self.buttonBox = QtWidgets.QDialogButtonBox(ChoicesDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(ChoicesDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), ChoicesDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), ChoicesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ChoicesDialog)

    def retranslateUi(self, ChoicesDialog):
        ChoicesDialog.setWindowTitle(QtWidgets.QApplication.translate("ChoicesDialog", "Dialog", None, -1))


class ChoiceItem(QtWidgets.QListWidgetItem):

    def __init__(self, *args, **kwargs):
        super(ChoiceItem, self).__init__(*args, **kwargs)

        self._data = None

    def set_data(self, data):
        self._data = data


class ChoiceDialog(QtWidgets.QDialog, Ui_ChoicesDialog):

    def __init__(self, choices=None, parent=None):
        super(ChoiceDialog, self).__init__(parent=parent)
        self.setupUi(self)

        self._choices = []
        if choices:
            self.set_choices(choices)

    def choices(self):
        return self._choices

    def set_choices(self, choices):
        self._choices = choices
        self.refresh()

    def refresh(self):
        for c in self.choices():
            if isinstance(c, dict):
                text = c['text']
                item = QtWidgets.QListWidgetItem(text)
                if c.get('data'):
                    item.setData(QtCore.Qt.UserRole, c.get('data'))
                self.listWidget.addItem(item)
            else:
                self.listWidget.addItem(c)

    def selected_choices(self, role='text'):
        if role == 'text':
            return [item.text() for item in self.listWidget.selectedItems()]
        elif role == 'data':
            return [item.data(QtCore.Qt.UserRole) for item in self.listWidget.selectedItems()]



class ThisUi(QtWidgets.QWidget, Ui_Form):
    def __init__(self, parent=None, interface=None):
        super(ThisUi, self).__init__(parent)
        self.interface:InterFace = interface

        self.setupUi(self)

        self.sg = FastSg().client
        self.textEdit.setReadOnly(True)
        self.pushButton_pick_abc.clicked.connect(self.on_pick_abc)
        self.listWidget_abc.itemPressed.connect(self.select_abc)
        self.build_view()

        if self.interface.submit_type == 'Dailies':
            self.interface.input_form["rig_path"] = 'default'
            self.interface.input_form["up_verisons"] = ['default']

    def build_view(self, node=None):
        import hou

        if not node:
            node = hou.node('/obj/workplace/cfx_rig_node')
        if not node: return
        text = node.path()
        item = QtWidgets.QListWidgetItem(text, self.listWidget_abc)
        item.setData(QtCore.Qt.UserRole, node)
        self.interface.input_form['rig_path'] = node.path()
        self.enter_upstream_version(node)

    def enter_upstream_version(self, node: hou.SopNode):
        import hou
        self.textEdit.clear()
        comment = node.comment()
        if not comment:
            hou.displayMessage(f'此节点 {node.path()} 没有上游版本信息，不可以发布')

        v_list = []
        v_submit = []
        for v_id in comment.split(','):
            version = v_id.split(' ')[1]
            version_name = self.sg.find_one('Version', [['id', 'is', int(version)]], ['code'])
            v_list.append(version_name['code'])
            v_submit.append(version_name)

        self.interface.input_form['up_verisons'] = v_submit
        self.textEdit.setText(' | '.join(v_list))

    @staticmethod
    def all_rig_nodes():
        import hou
        return hou.sopNodeTypeCategory().nodeType('huiwentong::cfx_rig_node').instances()

    @staticmethod
    def all_vdb_nodes():
        import hou
        nodes = []
        for node in hou.sopNodeTypeCategory().nodeType('oct_filecache_2').instances():
            path = Path(node.parm('file').eval())
            if path.suffix != '.vdb':
                continue
            nodes.append(node)
        return nodes

    @staticmethod
    def all_ass_nodes():
        # 关于这块需要重新写
        
        import hou 

        dirPath = get_ass_file_path()
        if not os.path.isdir(dirPath):
            return []
        nodes = []
        for node in hou.shopNodeTypeCategory().nodeType('arnold_vopnet').instances():
            all_ass_file = os.listdir(dirPath)
            if str(node.name()) + '.ass' not in all_ass_file:
                continue
            nodes.append(node)
        return nodes

    # def replace_des_tex(self):
    #     old_widget: QtWidgets.QPlainTextEdit = self.dialog.w_publish.plainTextEdit_description
    #     layout = self.dialog.w_publish.horizontalLayout_2
    #     index = layout.indexOf(old_widget)
    #     layout.removeWidget(old_widget)
    #     old_widget.deleteLater()
    #     self.dialog.w_publish.plainTextEdit_description = cover_text_editor.MyPlainTextEdit(self.dialog.w_publish)
    #     self.dialog.w_publish.plainTextEdit_description.setMaximumHeight(70)
    #     self.dialog.w_publish.plainTextEdit_description.setObjectName("plainTextEdit_description")  # 保持对象名一致（重要）
    #     layout.insertWidget(index, self.dialog.w_publish.plainTextEdit_description)

    def all_selected_nodes(self):
        nodes = []
        for item in self.listWidget_abc.all_items():
            nodes.append(item.data(QtCore.Qt.UserRole))
        return nodes

    def add_node_to_publish(self, node):
        if node in self.all_selected_nodes():
            return
        text = self.node_display_text(node)
        item = QtWidgets.QListWidgetItem(text, self.listWidget_abc)
        item.setData(QtCore.Qt.UserRole, node)

    @staticmethod
    def node_display_text(node):
        from oct_hou.utils.alembic import check_broken
        from oct_hou import get_ass_file_path
        

        dirPath = get_ass_file_path()
        if 'filecache' in node.type().name():
            file_path = Path(node.parm('file').eval())
        elif 'arnold_vopnet' == node.type().name():
            file_path = Path(os.path.join(dirPath, node.name() + '.ass'))
        else:
            file_path = Path(node.parm('filename').eval())
        if file_path.is_seq():
            file_path = file_path.percent_style_path
            text = '{n} ({f}, {frame})'.format(
                n=node.path(),
                f='{}/{}'.format(file_path.parent.name, file_path.name),
                frame=file_path.pretty_frames
            )
        else:
            text = '{} ({})'.format(
                node.path(), '{}/{}'.format(file_path.parent.name, file_path.name)
            )
        if file_path.suffix == '.abc':
            ret = check_broken(file_path)
            if ret:
                text = '{} {}'.format('[注意]文件损坏: {}'.format(ret.keys()), text)
        return text

    def on_pick_abc(self):
        import hou
        choices = []

        for node in self.all_rig_nodes():
            text = node.path()
            choices.append({'text': text, 'data': node})

        choice_dialog = ChoiceDialog(choices, parent=hou.qt.mainWindow())
        ret = choice_dialog.exec_()
        if ret == QtWidgets.QDialog.Accepted:
            for node in choice_dialog.selected_choices('data'):
                self.build_view(node)

    def select_abc(self):
        l_items = self.listWidget_abc.selectedItems()
        if self.listWidget_abc._mouse_button == QtCore.Qt.RightButton:
            for item in l_items:
                i = self.listWidget_abc.indexFromItem(item).row()
                print(i)
                self.listWidget_abc.takeItem(i)
                self.interface.input_form['rig_path'] = None
                self.interface.input_form['up_verisons'] = None




@dataclass
class CompInterface(InterFace):

    submit_form: dict = field(
        default_factory=lambda: {
            "rig_path": '',
            'up_verisons': []
        }
    )

    tag_list: list = field(
        default_factory=lambda: [283, 282]
    )

    downstream_dcc_only:str | None = 'Houdini'


    def gui_pre_interface(self):
        pass


    def init_ui(self, parent:QtWidgets.QWidget):
        if self.submit_type == 'Dailies':
            self.input_form['rig_path'] = 'default'
            self.input_form['up_verisons'] = ['default']
            return
        vlay = QtWidgets.QVBoxLayout(parent.files_group)
        tableView = ThisUi(parent, self)
        vlay.addWidget(tableView)



    def gui_post_interface(self):
        pass


