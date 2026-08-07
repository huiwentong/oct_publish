from dataclasses import dataclass, field, asdict
from publish_components.core import InterFace
from qtpy import QtWidgets, QtCore, QtGui, QtUiTools
from qtpy.QtCore import Qt, Signal
from pprint import pprint
from publish_core.database.entity import FastSg, SGEntity
from .publish_file_cfx_shot_ui import Ui_Form


def analysis_upstream(upstream='model: 241174,hair: 244698,dynamic: 244806,animation: 243969', sg=None):
    if not sg:
        sg = FastSg().client
    v_list = []
    for up_v in upstream.split(','):
        v_id = up_v.split(': ')[1]
        v_name = sg.find_one('Version', filters=[['id', 'is', int(v_id)]], fields=['code'])['code']
        v_list.append(v_name)
    return '\n'.join(v_list)


class MyItem(QtGui.QStandardItem):
    def __init__(self, text):
        super(MyItem, self).__init__(text)
        self.setEditable(False)
        self.setToolTip(self.text())

    def setText(self, text):
        super(MyItem, self).setText(text)
        self.setToolTip(text)



class MyTableModel(QtGui.QStandardItemModel):
    def __init__(self, sg, project, parent=None):
        super(MyTableModel, self).__init__(parent)
        self.setHorizontalHeaderLabels(['组件名称', '上游版本', '布料缓存', '毛发缓存'])
        self.sg = sg
        self.project = project

    def populate(self, components):
        for i in components:
            comp_name = i['name']
            filters = [
                ['project', 'name_is', self.project],
                ['code', 'is', comp_name],
            ]
            asset = self.sg.find_one('Asset', filters=filters, fields=['sg_asset_type'])
            if not asset: continue
            if asset['sg_asset_type'] in ['ASB', 'SCN', 'ENV']: continue
            comp_item = MyItem(comp_name)
            upstream_item = MyItem('上游版本，此信息只能自动填入')
            cloth_item = MyItem('右键点击选择布料缓存')
            hair_item = MyItem('右键点击选择毛发缓存')
            self.appendRow([comp_item, upstream_item, cloth_item, hair_item])


class MyTableView(QtWidgets.QTableView):
    refresh = Signal()
    def __init__(self, interface:InterFace=None, parent=None):
        super(MyTableView, self).__init__(parent)
        self.sg = FastSg().client
        self.interface = interface
        self.task:SGEntity = interface.task_entity
        self.proj_name = self.task.project.code
        self.model = MyTableModel(self.sg, self.proj_name, parent=self)
        self.setModel(self.model)
        self.entity:SGEntity = self.task.entity
        self.seqence:SGEntity = self.entity.sg_sequence

        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
                    QTableView {
                        background-color: #202124;
                        alternate-background-color: #24272b;
                        color: #e8eaed;
                        gridline-color: #3c4043;
                        border: 1px solid #3c4043;
                        border-radius: 6px;
                        selection-background-color: #3b82f6;
                        selection-color: white;
                    }

                    QTableView::item {
                        padding: 6px;
                        border: none;
                    }

                    QTableView::item:hover {
                        background-color: #303134;
                    }

                    QTableView::item:selected {
                        background-color: #2563eb;
                        color: white;
                    }

                    QHeaderView::section {
                        background-color: #18191a;
                        color: #d1d5db;
                        padding: 8px;
                        border: none;
                        border-right: 1px solid #3c4043;
                        font-weight: bold;
                    }

                    QTableCornerButton::section {
                        background-color: #18191a;
                        border: none;
                    }

                    QScrollBar:vertical {
                        background: #202124;
                        width: 10px;
                        margin: 0;
                    }

                    QScrollBar::handle:vertical {
                        background: #5f6368;
                        border-radius: 5px;
                        min-height: 30px;
                    }

                    QScrollBar::handle:vertical:hover {
                        background: #80868b;
                    }
                """)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.verticalHeader().setVisible(False)
        self.customContextMenuRequested.connect(self.on_right_click)

        filters =[
            ['project', 'name_is', self.proj_name],
            ['entity', 'name_is', self.entity['code']],
            ['content', 'is', 'rough_layout'],
        ]
        fields = ['sg_components']
        self.shot = self.sg.find_one('Task', filters=filters, fields=fields)
        self.model.populate(self.shot['sg_components'])

    def on_right_click(self, pos):
        index = self.indexAt(pos)
        if index.isValid():
            menu = QtWidgets.QMenu()
            item = self.model.itemFromIndex(index)
            dir_path = f'W:/projects/{self.proj_name.lower()}/shot/{self.seqence.code}/{self.entity["code"]}/cfx/houdini'
            if index.column() == 1:
                print(dir_path)
            elif index.column() == 2:
                path = QtWidgets.QFileDialog.getOpenFileName(self, '选择usd文件', dir_path, 'usd(*.usd)')[0]
                if path:
                    item.setText(path)
            elif index.column() == 3:
                _dir = QtWidgets.QFileDialog.getExistingDirectory(self, dir=dir_path)
                if _dir:
                    item.setText(_dir)

            self.refresh.emit()

class ThisUi(QtWidgets.QWidget, Ui_Form):
    def __init__(self, interface):
        super(ThisUi, self).__init__()
        self.setupUi(self)
        self.initial()
        self.interface = interface
        self.tableView = MyTableView(interface, self)
        self.tableView.refresh.connect(self.refresh_asset_info)
        self.layout().addWidget(self.tableView)
        self.set_bind()
        if self.interface.submit_type == "Dailies":
            self.interface.input_form['components'] = {'default': 'default'}

    def initial(self):
        in_hou = False
        try:
            import hou
            in_hou = True
        except:
            pass
        if in_hou:
            self.pushButton.setEnabled(False)
        else:
            self.pushButton_2.setEnabled(False)

    def set_bind(self):
        self.pushButton.clicked.connect(self.fill_out)
        self.pushButton_2.clicked.connect(self.fill_in)

    def fill_out(self):
        pass

    def refresh_asset_info(self):
        for i in range(self.tableView.model.rowCount()):
            comp_item = self.tableView.model.item(i, 0)
            upstream_item = self.tableView.model.item(i, 1)
            cloth_item = self.tableView.model.item(i, 2)
            hair_item = self.tableView.model.item(i, 3)
            
            if not upstream_item.data(Qt.UserRole):
                if self.interface.input_form['components'].get(comp_item.text()):
                    self.interface.input_form['components'].pop(comp_item.text())
                continue

            self.interface.input_form['components'][comp_item.text()] = {
                'upstream': upstream_item.data(Qt.UserRole),
                'cloth': cloth_item.text(),
                'hair': hair_item.text(),
            }

    def fill_in(self):
        import hou
        for i in range(self.tableView.model.rowCount()):
            comp_item = self.tableView.model.item(i, 0)
            upstream_item = self.tableView.model.item(i, 1)
            cloth_item = self.tableView.model.item(i, 2)
            hair_item = self.tableView.model.item(i, 3)
            comp_node:hou.SopNode = hou.node(f'/obj/workplace_{comp_item.text()}/{comp_item.text()}')
            if not comp_node: continue
            cloth_path = comp_node.parm('cloth_usd_out').eval()
            hair_path = comp_node.parm('hair_c_out').eval()
            upstream = comp_node.comment()
            cloth_item.setText(cloth_path)
            hair_item.setText(hair_path)
            upstream_item.setText(analysis_upstream(upstream))
            upstream_item.setData(upstream, Qt.UserRole)
        self.refresh_asset_info()

@dataclass
class CompInterface(InterFace):

    submit_form: dict = field(
        default_factory=lambda: {
            "components": [],
        }
    )

    tag_list: list = field(
        default_factory=lambda: [283, 282]
    )


    def gui_pre_interface(self):
        pass


    def init_ui(self, parent:QtWidgets.QWidget):
        
        vlay = QtWidgets.QVBoxLayout(parent.files_group)
        tableView = ThisUi(self)
        vlay.addWidget(tableView)



    def gui_post_interface(self):
        pass


