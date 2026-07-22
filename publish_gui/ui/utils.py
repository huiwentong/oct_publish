



def clear_layout(layout):

    while layout.count():

        item = layout.takeAt(0)

        widget = item.widget()

        if widget:
            widget.deleteLater()

        else:
            # spacerItem
            del item