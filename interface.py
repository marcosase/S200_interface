
import pandas as pd
from openepda import OpenEpdaDataLoader
import time
import sys
import numpy as np
from PyQt5 import QtGui
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QVBoxLayout
import pyqtgraph as pg

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        pg.setConfigOption('background', 'w') #before loading widget
        pg.setConfigOption('foreground', 'k')
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        uic.loadUi('template.ui', self) # Load the .ui file
        self.select_btn.clicked.connect(self.open_file)
        self.clear_btn.clicked.connect(self.clear_plot)
        self.plot_btn.clicked.connect(self.plot)#button to plot stuff
        self.plot2_btn.clicked.connect(self.plotx2)#button to plot stuff
        #self.plotter.plotItem.showGrid(True, True, 0.7)
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        
        self.show() # Show the GUI
 
    def open_file(self):
        global file_open
        file_open = QFileDialog.getOpenFileName()
        self.label.setText(file_open[0].split('/')[-1])
        print('*********')
        self.select_header(file_open[0])
        return 
    
    def select_header(self, file):
        global cust, lot_line, cell_line, column_name, hdr_line

        #Selecting the data files of an opened file
        data_names=[]
        fh = openepda.OpenEpdaDataLoader()
        df = pd.DataFrame({})
        fh_read = fh.read_file(file)
                
        last_item = list(fh_read)[-1]
        data_size = fh_read[last_item].size
        for i in fh_read:
            try:
                if fh_read[i].size >100:
                    data_names.append(i)
                else:
                    pass
            except:
                pass
        self.x_cmb_box.clear()
        self.y_cmb_box.clear()
        self.y2_cmb_box.clear()
        
        with open(file) as f:
            n_col = len(f.readlines()[-1].split(','))
            f.close()

        column_name = []
        with open(file) as f:
           
            for i, line in enumerate(f):
                if 'Customer' in line:
                    cust = line.split(' ')[-1].replace('\n','')            
                
                if 'LotID' in line or 'Batch' in line: 
                    lot_line = line.split(' ')[-1].replace('\n','')             
                                
                if 'Cell' in line: 
                    cell_line = line.split(' ')[-1].replace('\n','')

                if ('Current' in line) or ('I_soa' in line) or ('Wavelength' in line):
                    hdr_line = i
                    for j in range(n_col):
                        column_name.append(line.split(',')[2*j].replace('"', ''))
            print(column_name)
            self.x_cmb_box.addItems([k for k in column_name])
            self.y_cmb_box.addItems([k for k in column_name])
            self.y2_cmb_box.addItems([k for k in column_name])
            f.close()
        return cust, lot_line, cell_line, column_name
    
    def plot(self):
        global p1
        
        p1 = self.plotter.plotItem
               
        print(cust, lot_line, cell_line, column_name, file_open[0], hdr_line)
        x_axis = self.x_cmb_box.currentText()
        y_axis = self.y_cmb_box.currentText()
        print("***************")
        df = pd.read_csv(file_open[0], skiprows = hdr_line+2, names=column_name)
        print(df.head())
        x_label = str(x_axis)
        y_label = str(y_axis)
        title = 'LIV' #to be change for the actual name
        self.set_graph(title, x_label, y_label)
        p1.plot(df[x_axis], df[y_axis], symbol='o', pen=(np.random.randint(0,255),np.random.randint(0,255),np.random.randint(0,255)), symbolPen='b', symbolBrush=(np.random.randint(0,255),np.random.randint(0,255),np.random.randint(0,255)), symbolSize=8, name='_'.join(file_open[0].split('_')[1:3]))
    
        #cross hair

        p1.addItem(self.vLine, ignoreBounds=True)
        p1.addItem(self.hLine, ignoreBounds=True)

        vb = p1.vb
        p1.scene().sigMouseMoved.connect(self.mouseMoved)

    def plotx2(self):
        global p1, p2

        t1 = (np.random.randint(0,255),np.random.randint(0,255),np.random.randint(0,255))
        t2 = (np.random.randint(0,255),np.random.randint(0,255),np.random.randint(0,255))
        tfill = (np.random.randint(0,255),np.random.randint(0,255),np.random.randint(0,255))

        color1 = '#%02x%02x%02x' % t1
        color2 = '#%02x%02x%02x' % t2
                
        x_axis = self.x_cmb_box.currentText()
        y_axis = self.y_cmb_box.currentText()
        y2_axis = self.y2_cmb_box.currentText()

        x_label = str(x_axis)
        y_label = str(y_axis)
        title = 'LIV'
        self.set_graph( title, x_label, y_label)


        df = pd.read_csv(file_open[0], skiprows = hdr_line+2, names=column_name)
        
        p1 = self.plotter.plotItem
        p1.setLabels(left = y_axis)

        #Create a new ViewBox
        p2 = pg.ViewBox()
        p1.showAxis('right')
        p1.scene().addItem(p2)
        p1.getAxis('right').linkToView(p2)
        p2.setXLink(p1)
        p1.getAxis('left').setLabel(y_axis, color=color1)
        p1.getAxis('right').setLabel(y2_axis, color=color2)
        p1.getAxis('bottom').setLabel(x_axis)        
        self.updateViews()
        p2.setGeometry(p1.vb.sceneBoundingRect())
        p2.linkedViewChanged(p1.vb, p2.XAxis)

        p1.vb.sigResized.connect(self.updateViews)

        p1.plot(df[x_axis], df[y_axis], symbol='o', pen=t1, symbolPen='b', symbolBrush = tfill, symbolSize=8, name='_'.join(file_open[0].split('_')[1:3]))

        plot2 = pg.ScatterPlotItem(x = df[x_axis].values, y = df[y2_axis].values, symbol='o', pen = t2, symbolPen = 'b',symbolBrush = tfill, symbolSize = 8)
        
        p2.addItem(plot2)
                
    def updateViews(self):
        global p1, p2
        p2.setGeometry(p1.vb.sceneBoundingRect())
        p2.linkedViewChanged(p1.vb, p2.XAxis)


    def clear_plot(self):
        global p1, p2
        self.plotter.clear()
        p2.clear()
        p1.clear()

    def set_graph(self, titulo, eixo_x, eixo_y):
            p1 = self.plotter
            # THESE PARAMETERS ARE FOR RESIZING AND MOVING THE POSITION OF THE LEGEND BOX
            # I INCREASED X-SIZE AND Y-OFFSET
            p1.addLegend(size=(110, 0) ,offset=(10, 10))
            p1.setTitle('<font size="2">Active Power</font>') #,**titleStyle)
            a = p1.getAxis('top')
            a.showValues='false'
            a = p1.getAxis('bottom')
            p1.showAxis('left')
            a = p1.getAxis('left')
            p1.showAxis('right')
            a = p1.getAxis('right')
            p1.showLabel('left', show=True)
            p1.showLabel('right', show=True)
            p1.showGrid(x=True, y=True, alpha=0.1)
            titleStyle = {'color': '#000', 'size': '18pt'}
            p1.setTitle(titulo, **titleStyle)
            # SET AND CHANGE THE FONT SIZE AND COLOR OF THE PLOT AXIS LABEL
            labelStyle = {'color': '#000', 'font-size': '16px'}
            p1.setLabel('bottom', eixo_x, **labelStyle)
            p1.setLabel('left', eixo_y, **labelStyle)
            p1.setLabel('top',)

    def mouseMoved(self, evt):
        global p1
        pos = evt
               
        if p1.sceneBoundingRect().contains(pos):
            mousePoint = p1.vb.mapSceneToView(pos)
            index = int(mousePoint.x())
            if index > 0 and index < len(data1):
                label.setText("<span style='font-size: 12pt'>x=%0.1f,   <span style='color: red'>y1=%0.1f</span>,   <span style='color: green'>y2=%0.1f</span>" % (mousePoint.x(), data1[index], data2[index]))
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
            self.x_value.setText(str( np.round(mousePoint.x(), 4)))
            self.y_value.setText(str( np.round(mousePoint.y(), 4)))

app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()