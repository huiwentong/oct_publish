from dataclasses import dataclass, field, asdict
from publish_components.core import InterFace
from qtpy import QtWidgets, QtCore, QtGui
from qtpy.QtCore import Qt
from pprint import pprint
from publish_core.database.entity import FastSg, SGEntity
try:
    import hou
except:
    pass



TYPE_MAP = {
    '_vdb': 'VDB缓存',
    '_instance': 'instance缓存',
    '_broken': '破碎缓存',
}

class MyItem(QtGui.QStandardItem):
    def __init__(self, text):
        super(MyItem, self).__init__(text)
        self.setEditable(False)
        self.setToolTip(self.text())
        self.setTextAlignment(Qt.AlignCenter)

    def setText(self, text):
        super(MyItem, self).setText(text)
        self.setToolTip(text)



class MyTableModel(QtGui.QStandardItemModel):
    def __init__(self, sg, task:SGEntity, parent=None):
        super(MyTableModel, self).__init__(parent)
        self.setHorizontalHeaderLabels(['组件名称', 'usd输出节点', '输出类型'])
        self.sg = sg
        self.task = task


    def initial(self):
        components = self.task.sg_components
        for i in components:
            comp_item = MyItem(i['name'])
            cache_item = MyItem('历史版本的component')
            type_item = MyItem('暂无')

            self.appendRow([comp_item, cache_item, type_item])

    def populate(self, components):

        for i in components:
            comp_node:hou.SopNode = i
            comp_name = comp_node.parm('comp_selected').evalAsString()
            if comp_name == 'none': continue

            cache_node = None
            cache_type = None
            for _child in comp_node.children():
                if _child.type().name() in ['huiwentong::oct_export_usd', 'huiwentong::oct_export_usd_vdb', 'huiwentong::oct_export_usd_instance', 'huiwentong::oct_export_usd_broken']:
                    cache_node = _child
                    cache_type = TYPE_MAP.get(_child.type().name().split('huiwentong::oct_export_usd')[1], 'MESH缓存')
                    break

            find_items = self.findItems(comp_name, Qt.MatchExactly)
            if find_items:
                comp_item = find_items[0]
                cache_item = self.item(comp_item.row(), 1)
                if cache_item.text() != '历史版本的component':
                    hou.ui.displayMessage(f'存在重名的component节点!!{comp_node.path()}', ['Ok', ])
                    return
                type_item = self.item(comp_item.row(), 2)
            else:
                comp_item = MyItem(comp_name)
                cache_item = MyItem('右键点击选择cache节点')
                type_item = MyItem('暂无')

            if cache_node:
                if cache_type == '破碎缓存':
                    comp_name = cache_node.parm('broken_name').eval()
                comp_item.setText(comp_name)
                comp_item.setData(comp_node, Qt.UserRole)
                cache_item.setText(cache_node.path())
                cache_item.setData(cache_node, Qt.UserRole)
                type_item.setText(cache_type)
            self.appendRow([comp_item, cache_item, type_item])


class MyTableView(QtWidgets.QTableView):
    def __init__(self, parent, interface:InterFace):
        super(MyTableView, self).__init__(parent)
        self.sg = FastSg().client
        self.interface = interface
        self.setMinimumHeight(400)
        self.task:SGEntity = interface.task_entity
        self._model = MyTableModel(sg=self.sg, task=self.task, parent=self)
        self.setModel(self._model)
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

        root_node:hou.SopNode = hou.node('/obj/')
        components = []
        for i in root_node.children():
            if i.type().name() == 'huiwentong::oct_component':
                components.append(i)
        self._model.populate(components)
        self.refresh_submit_info()

    def on_right_click(self, pos):
        menu = QtWidgets.QMenu()
        all_main_items = {}
        for i in self.selectedIndexes():
            index:QtCore.QModelIndex = i
            if index.column() != 0: continue
            comp_item = self._model.item(index.row(), 0)
            cache_item = self._model.item(index.row(), 1)
            type_item = self._model.item(index.row(), 2)
            all_main_items[comp_item.text()] = {
                'comp_item': comp_item,
                'cache_item': cache_item,
                'type_item': type_item,
            }

        menu.addAction('指定usd输出缓存节点')
        menu.addAction('禁用选中的Component')
        menu.addAction('本次暂时不发布这些Component')
        ret = menu.exec_(QtGui.QCursor.pos())
        if not ret: return
        if ret.text() == "指定usd输出缓存节点":
            if len(all_main_items) > 1:
                hou.ui.displayMessage('如果是指定usd输出缓存的话还是一个一个来吧，别一次选太多', ['Ok',])
                return
            if len(all_main_items) == 0:
                hou.ui.displayMessage('先选择一个需要指定缓存的component', ['Ok',])
                return
            for k, v in all_main_items.items():
                comp_item = v['comp_item']
                cache_item = v['cache_item']
                type_item = v['type_item']
                comp_node = comp_item.data(Qt.UserRole)
                def cus_call_back(node):
                    if 'oct_export' in node.type().name() and comp_node.path()+'/' in node.path():
                        return True
                    else:
                        return False
                ret = hou.ui.selectNode(initial_node=comp_node, custom_node_filter_callback=cus_call_back)
                if ret:
                    cache_item.setText(ret)
                    cache_node = hou.node(ret)
                    cache_item.setData(cache_node, Qt.UserRole)
                    cache_type = TYPE_MAP.get(cache_node.type().name().split('huiwentong::oct_export_usd')[1], 'MESH缓存')
                    type_item.setText(cache_type)
                    if cache_type == '破碎缓存':
                        comp_name = cache_node.parm('broken_name').eval()
                        comp_item.setText(comp_name)

        elif ret.text() == "禁用选中的Component":
            for k, v in all_main_items.items():
                comp_item = v['comp_item']
                cache_item = v['cache_item']
                type_item = v['type_item']
                type_item.setText('禁用')
                brush = QtGui.QBrush()
                bbrush = QtGui.QBrush()
                bbrush.setColor(QtGui.QColor(10,10,10))
                brush.setColor(QtGui.QColor(100, 0, 0))
                comp_item.setForeground(brush)
                cache_item.setForeground(brush)
                type_item.setForeground(brush)

                comp_item.setBackground(brush)
                cache_item.setBackground(brush)
                type_item.setBackground(brush)

        elif ret.text() == "本次暂时不发布这些Component":
            for k, v in all_main_items.items():
                comp_item = v['comp_item']
                cache_item = v['cache_item']
                type_item = v['type_item']
                row = comp_item.row()
                self._model.removeRow(row)
            print(self._model.rowCount())

        self.refresh_submit_info()

    def refresh_submit_info(self):
        print('refresh me!')
        self.interface.input_form = {'components': {}}
        for i in range(self._model.rowCount()):
            comp_item = self._model.item(i, 0)
            cache_item = self._model.item(i, 1)
            type_item = self._model.item(i, 2)

            self.interface.input_form['components'][comp_item.text()] = {
                'cache_node': cache_item.data(Qt.UserRole),
                'cache_type': type_item.text(),
            }
        pprint(self.interface.input_form)

@dataclass
class CompInterface(InterFace):

    submit_form: dict = field(
        default_factory=lambda: {
            "components": []
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
            self.input_form['components'] = ['default']
            return
        vlay = QtWidgets.QVBoxLayout(parent.files_group)
        tableView = MyTableView(parent, self)
        vlay.addWidget(tableView)



    def gui_post_interface(self):
        pass


