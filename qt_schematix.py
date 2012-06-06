#!/usr/bin/env python

""" Description..."""

__author__ = "Peter Bennett"
__copyright__ = "Copyright 2012, Peter A Bennett"
__license__ = "LGPL"
__version__ = "0.1"
__maintainer__ = "Peter Bennett"
__email__ = "pab850@googlemail.com"
__contact__ = "www.bytebash.com"

import time
from PySide import QtCore, QtGui, QtOpenGL
from random import *

from ui import Ui_MainWindow

from components import components

# Set the icon theme to tango
QtGui.QIcon.setThemeName("tango")

def createCommandString(item, pos):
    return (str(pos.x()) + "," + str(pos.y()))

class DiagramItem(QtGui.QGraphicsPolygonItem):        
    def __init__(self, addType, parent=None, scene=None):
        super(DiagramItem, self).__init__(parent, scene)
        self.componentType = addType
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.setToolTip(str(self.componentType))
        self.setPolygon(QtGui.QPolygonF([
                        QtCore.QPointF(-25, -25), QtCore.QPointF(25, -25),
                        QtCore.QPointF(25, 25), QtCore.QPointF(-25, 25),
                        QtCore.QPointF(-25, -25)]))
        self.wires = None
    def itemChange(self, change, value):
        """ Re-implement QGraphicsItem.itemChange """
        if change == QtGui.QGraphicsItem.ItemPositionChange:
            for wire in self.wires:
                wire.updatePosition()

        return value       
        
class Wire(QtGui.QGraphicsLineItem):
    def __init__(self, startNode, endNode, parent=None, scene=None):
        super(Wire, self).__init__(parent, scene)
        self.startNode = startNode
        self.endNode = endNode
        self.colour = QtCore.Qt.blue # TODO: colour based on datatype?
        self.checkConnected()
  
    def checkConnected(self):
        if self.startNode and self.endNode:
            # If the wire has a start and end node it is connected
            self.colour = QtCore.Qt.blue
            self.setPen(QtGui.QPen(self.colour, 2, QtCore.Qt.SolidLine,
                    QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
            self.connected = True
        else:
            # This wire is not connected
            self.colour = QtCore.Qt.red
            self.setPen(QtGui.QPen(self.colour, 2, QtCore.Qt.DashLine,
                    QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
            self.connected = False
            
    def updatePosition(self):
        line = QtCore.QLineF(self.mapFromItem(self.startNode, 0, 0),
                             self.mapFromItem(self.endNode, 0, 0))
        self.setLine(line) 
        
    def paint(self, painter, option, widget=None):
        """ Re-implement QGraphicsItem.paint() """
        if (self.startNode.collidesWithItem(self.endNode)):
            # Dont paint if the start and end nodes collide
            # TODO: This could result in obscured connections, maybe disallow
            # items to overlap?
            return 
            
        painter.setPen(self.pen)
        painter.setBrush(self.colour)
        self.setline(QtCore.QLineF(self.startNode.pos(), self.endNode.pos()))
        
    def startItem(self):
        return self.startNode

    def endItem(self):
        return self.endNode
        
        
   
class AddCommand(QtGui.QUndoCommand):
    def __init__(self, addType, scene):
        super(AddCommand, self).__init__()
        self.itemCount = 0
        self.myDiagramItem = DiagramItem(addType)
        self.myGraphicsScene = scene
        self.initialPosition = QtCore.QPointF((self.itemCount * 15) % scene.width(),
                                             (self.itemCount * 15) % scene.height())
        scene.update()
        self.itemCount += 1
        self.setText("Add " + createCommandString(self.myDiagramItem, self.initialPosition))                
    def __del__(self):
        pass
    def undo(self):
        self.myGraphicsScene.removeItem(self.myDiagramItem)
        self.myGraphicsScene.update()
    def redo(self):
        self.myGraphicsScene.addItem(self.myDiagramItem)
        self.myDiagramItem.setPos(self.initialPosition)
        self.myGraphicsScene.clearSelection()
        self.myGraphicsScene.update()

class MoveCommand(QtGui.QUndoCommand):
    def __init__(self, diagramItem, oldPosition):
        super(MoveCommand, self).__init__()
        self.myDiagramItem = diagramItem;
        self.newPosition = diagramItem.pos()
        self.oldPosition = oldPosition
    def undo(self):
        self.myDiagramItem.setPos(self.oldPosition)
        #self.myDiagramItem.scene.update()
        self.setText("Move " + createCommandString(self.myDiagramItem, self.newPosition))
    def redo(self):
        self.myDiagramItem.setPos(self.newPosition)
        self.setText("Move " + createCommandString(self.myDiagramItem, self.newPosition))
    def mergeWith(self, command):
        item = command.myDiagramitem
        
        if self.myDiagramItem != item:
            return False
        
        self.newPosition = item.position()
        self.setText("Move " + createCommandString(self.myDiagramItem, self.newPosition))
      
class DeleteCommand(QtGui.QUndoCommand):
    def __init__(self, scene):
        super(DeleteCommand, self).__init__()
        self.myGraphicsScene = scene
        self.itemList = self.myGraphicsScene.selectedItems()
        self.itemList[0].setSelected(False)
        self.myDiagramItem = self.itemList[0]
        self.setText("Delete " + createCommandString(self.myDiagramItem, self.myDiagramItem.pos()))
    def undo(self):
        self.myGraphicsScene.addItem(self.myDiagramItem)
        self.myGraphicsScene.update()
    def redo(self):
        self.myGraphicsScene.removeItem(self.myDiagramItem)
        
        
class DiagramScene(QtGui.QGraphicsScene):
    itemMoved = QtCore.Signal(DiagramItem, QtCore.QPointF)
    def __init__(self):
        super(DiagramScene, self).__init__()
        self.movingItem = None
    def mousePressEvent(self, event):
        mousePos = QtCore.QPointF(event.buttonDownScenePos(QtCore.Qt.LeftButton).x(),
                          event.buttonDownScenePos(QtCore.Qt.LeftButton).y())
                      
        self.movingItem = self.itemAt(mousePos.x(), mousePos.y())      

        if (self.movingItem and event.button() == QtCore.Qt.LeftButton):
            print "A valid item has started to move..."
            self.oldPos = self.movingItem.pos()
        self.clearSelection()
        QtGui.QGraphicsScene.mousePressEvent(self, event)
    def mouseReleaseEvent(self, event):
        print "Mouse released..."
        
        if (self.movingItem and event.button() == QtCore.Qt.LeftButton):
            print "The moving item was valid..."
            if (self.oldPos != self.movingItem.pos()):
                print "The item was moved a valid distance..."
                self.itemMoved.emit(self.movingItem, self.oldPos)
            self.movingItem = None
        QtGui.QGraphicsScene.mouseReleaseEvent(self, event)

             
class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        
        # UI Setup
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # Set the default icons for UI actions
        self.ui.actionNew.setIcon(QtGui.QIcon.fromTheme("document-new"))
        self.ui.actionOpen.setIcon(QtGui.QIcon.fromTheme("document-open"))
        self.ui.actionSave.setIcon(QtGui.QIcon.fromTheme("document-save"))
        self.ui.actionSave_As.setIcon(QtGui.QIcon.fromTheme("document-save-as"))
        self.ui.actionPrint.setIcon(QtGui.QIcon.fromTheme("document-print"))
        self.ui.actionQuit.setIcon(QtGui.QIcon.fromTheme("system-log-out"))
        self.ui.actionUndo.setIcon(QtGui.QIcon.fromTheme("edit-undo"))
        self.ui.actionRedo.setIcon(QtGui.QIcon.fromTheme("edit-redo"))
        self.ui.actionCut.setIcon(QtGui.QIcon.fromTheme("edit-cut"))
        self.ui.actionCopy.setIcon(QtGui.QIcon.fromTheme("edit-copy"))
        self.ui.actionPaste.setIcon(QtGui.QIcon.fromTheme("edit-paste"))
        self.ui.actionDelete.setIcon(QtGui.QIcon.fromTheme("edit-delete"))
        self.ui.actionPreferences.setIcon(QtGui.QIcon.fromTheme("preferences"))
        self.ui.actionAbout.setIcon(QtGui.QIcon.fromTheme("help-browser"))
        self.ui.actionRun.setIcon(QtGui.QIcon.fromTheme("go-next"))
        # UI ToolBox
        self.buttonGroup = QtGui.QButtonGroup()
        self.buttonGroup.setExclusive(False)
        self.buttonGroup.buttonClicked[int].connect(self.toolBoxButtonClicked)
        self.toolBox = self.ui.componentBrowser
        # Populate the toolbox
        self.createToolBox()  
        # Create a scene for the GraphicsView
        self.scene=DiagramScene()
        self.ui.graphicsView.setScene(self.scene)
        self.scene.setSceneRect(0,0,600,400)
        # Make it bigger
        self.setWindowState(QtCore.Qt.WindowMaximized)
        # Create an UNDO stack and view
        self.undoStack = QtGui.QUndoStack(self)
        self.undoView = QtGui.QUndoView(self.undoStack)
        self.undoView.setWindowTitle("Undo View")
        self.undoView.show()
        self.undoView.setAttribute(QtCore.Qt.WA_QuitOnClose, False)
        self.createActions()
        self.createMenus()
        # Set the window title      
        self.setWindowTitle("Schematix")
    def createActions(self):
        self.ui.actionDelete = QtGui.QAction("&Delete Item", self)
        self.ui.actionDelete.setShortcut("Del");
        QtCore.QObject.connect(self.ui.actionDelete,
                               QtCore.SIGNAL("triggered()"),
                               self.deleteItem)
                               
#        QtCore.QObject.connect(self.scene,
#                               QtCore.SIGNAL("itemMoved()"),
#                               self.itemMoved)
                               
        self.scene.itemMoved.connect(self.itemMoved)
        self.ui.actionUndo = self.undoStack.createUndoAction(self, "&Undo")
        self.ui.actionUndo.setShortcuts(QtGui.QKeySequence.Undo)
        self.ui.actionRedo = self.undoStack.createRedoAction(self, "&Redo")
        self.ui.actionRedo.setShortcuts(QtGui.QKeySequence.Redo)
    def createMenus(self):
        self.newEditMenu = self.ui.menubar.addMenu("&EditNew")
        self.newEditMenu.addAction(self.ui.actionUndo)
        self.newEditMenu.addAction(self.ui.actionRedo)
        self.newEditMenu.addSeparator()
        self.newEditMenu.addAction(self.ui.actionDelete)
        
        
        
        
        QtCore.QObject.connect(self.ui.menuEdit,
                               QtCore.SIGNAL("aboutToShow()"),
                               self.itemMenuAboutToShow)
        QtCore.QObject.connect(self.ui.menuEdit,
                               QtCore.SIGNAL("aboutToHide()"),
                               self.itemMenuAboutToHide)
                    
    def itemMenuAboutToHide(self):
        self.ui.actionDelete.setEnabled(True)
    def itemMenuAboutToShow(self):
        self.ui.actionDelete.setEnabled(len(self.scene.selectedItems())!=0)
    def deleteItem(self):
        print "Delete called..."
        if (len(self.scene.selectedItems()) == 0):
            return
        deleteCommand = DeleteCommand(self.scene)
        self.undoStack.push(deleteCommand);
    def addComponent(self, component):
        # TODO: Make it so that the component has to be dragged onto the
        # canvas from the toolbox, or clicked once in the toolbox and then
        # clicked again on the canvas to place or right click/esc to cancel.
        action = AddCommand(component, self.scene)
        self.undoStack.push(action)
    def itemMoved(self, movedItem, oldPosition):
        print "MAINWINDOW: An item in the graphics view got moved..."
        self.undoStack.push(MoveCommand(movedItem, oldPosition))
    def createToolBox(self):
        """ Populates the toolbox widget of the main UI with components
        from the component library """ 
        id = 0
        # Parse the component library and add components to the toolbox 
        for library_name, library in components:
            # At this level of the loop we have a library of components
            # Create a new section on the toolbox for this library and add
            # its components as buttons
            layout = QtGui.QGridLayout()
            x = 0
            y = 0
            for component in library:
                # For each component, add a button
                title = component["name"]
                layout.addWidget(self.createCellWidget(title,id), y, x)
                id += 1
                if x >= 1:
                    x = 0
                    y += 1
                else:
                    x += 1
            layout.setRowStretch(3, 10)
            layout.setColumnStretch(2, 10)
            itemWidget = QtGui.QWidget()
            itemWidget.setLayout(layout)
            self.toolBox.addItem(itemWidget, library_name)
    def createCellWidget(self, text, id):
        """ Create a button for the toolbox """
        button = QtGui.QToolButton()
        button.setIcon(QtGui.QIcon.fromTheme("emblem-symbolic-link"))
        button.setIconSize(QtCore.QSize(32, 32))
        button.setText(text)
        self.buttonGroup.addButton(button, id)
        layout = QtGui.QGridLayout()
        layout.addWidget(button, 0, 0, QtCore.Qt.AlignHCenter)
        layout.addWidget(QtGui.QLabel(text), 1, 0, QtCore.Qt.AlignCenter)
        widget = QtGui.QWidget()
        widget.setLayout(layout)
        return widget                   
    def toolBoxButtonClicked(self, id):
        """ Event handler for tool box button clicks. For now just add to the
        diagram the component that was clicked by the user """
        # TODO: Add graphics for different block types
        # TODO: Allow components to be 'dragged' from the toolbox onto the
        # canvas
        # TODO: Show contextual help if the mouse is hovered over an item in
        # the toolbox showing information about the relevant component
        buttons = self.buttonGroup.buttons()
        for button in buttons:
            if self.buttonGroup.button(id) != button:
                button.setChecked(False)
        sender = self.buttonGroup.button(id).text()
        self.ui.ObjectInspectorText.setText(sender)
        self.addComponent(id)
        
def main():

    import sys

    app = QtGui.QApplication(sys.argv)

    mainWindow = MainWindow()
    mainWindow.setGeometry(100, 100, 800, 500)
    mainWindow.show()

    sys.exit(app.exec_())    
    
if __name__ == "__main__":
    main()
    
