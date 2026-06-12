
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QFileDialog, QComboBox, QPlainTextEdit, QRadioButton, QCheckBox, QButtonGroup
import pandas as pd
import numpy as np

class MyWindow(QWidget):
    def __init__(self, input_dict):
        super().__init__()

        self.input_dict = input_dict
        self.initUI()

    def initUI(self):
        # Create widgets
        self.default_excel_radio_buttons = [
            QRadioButton('WR6.5IAMC'),
            QRadioButton('WR9.0IAMC'),
            QRadioButton('WR10.0IAMC'),
            QRadioButton('WR12.0IAMC')
        ]

        self.excel_paths = [
            r"W:\Engineer\DBE\IAMCTrackingDocCopies\6p5IAMC-HP_Tracking EMPTY- Copy.xlsx",
            r"W:\Engineer\DBE\IAMCTrackingDocCopies\9p0IAMC-HP_Tracking EMPTY- Copy.xlsx",
            r"W:\Engineer\DBE\IAMCTrackingDocCopies\10IAMC-HP_Tracking EMPTY- Copy.xlsx",
            r"W:\Engineer\DBE\IAMCTrackingDocCopies\12IAMC-HP_Tracking EMPTY- Copy.xlsx"
        ]

        self.excel_label = QLabel('IAMC Tracking Doc:')
        self.excel_input = QLineEdit()
        self.excel_browse_button = QPushButton('Browse')

        self.sheet_label = QLabel('Select Sheet:')
        self.sheet_combo = QComboBox()

        self.filepath_label = QLabel('DAT File Path:')
        self.filepath_input = QLineEdit()
        self.filepath_browse_button = QPushButton('Browse')

        self.note_label = QLabel('Notes:')
        self.note_input = QPlainTextEdit()
        self.note_input.setWordWrapMode(True)

        self.TSCgood_label = QCheckBox("TSC Good?")
        self.partgood_label = QCheckBox("Part Good?")

        self.key_label = QLabel('Choose Band:')
        self.key_combo = QComboBox()
        self.key_combo.addItems(self.input_dict.keys())

        self.submit_button = QPushButton('Submit \n Note: Ensure tracking doc is closed')

        # Create a button group for radio buttons to make them mutually exclusive
        self.radio_button_group = QButtonGroup(self)
        for i, radio_button in enumerate(self.default_excel_radio_buttons):
            self.radio_button_group.addButton(radio_button, i)

        # Connect signals to slots
        for radio_button in self.default_excel_radio_buttons:
            radio_button.toggled.connect(self.toggle_excel_inputs)

        self.excel_browse_button.clicked.connect(self.browse_excel)
        self.filepath_browse_button.clicked.connect(self.browse_filepath)
        self.submit_button.clicked.connect(self.submit_data)

        # Set up layout
        layout = QVBoxLayout()

        for radio_button in self.default_excel_radio_buttons:
            layout.addWidget(radio_button)

        layout.addWidget(self.excel_label)
        layout.addWidget(self.excel_input)
        layout.addWidget(self.excel_browse_button)

        layout.addWidget(self.sheet_label)
        layout.addWidget(self.sheet_combo)
        
        
        layout.addWidget(self.key_label)
        layout.addWidget(self.key_combo)

        layout.addWidget(self.filepath_label)
        layout.addWidget(self.filepath_input)
        layout.addWidget(self.filepath_browse_button)

        layout.addWidget(self.TSCgood_label)
        layout.addWidget(self.partgood_label)


        layout.addWidget(self.note_label)
        layout.addWidget(self.note_input)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

        # Set up window
        self.setWindowTitle('IAMC Pretesting Data Submitter')
        self.setGeometry(100, 100, 400, 400)  # Adjusted to accommodate the larger note input box

        # output Variables
        self.result_excel_filepath = None
        self.result_sheet = None
        self.result_filepath = None
        self.result_note = None
        self.result_TSC = None
        self.result_part = None
        self.result_value = None

        # Set default values
        self.default_excel_radio_buttons[0].setChecked(True)

        # Load sheets for the default state
        self.load_sheets(0)

    def toggle_excel_inputs(self):
        # Toggle Excel file inputs based on radio button state
        for i, radio_button in enumerate(self.default_excel_radio_buttons):
            if radio_button.isChecked():
                self.excel_input.setText(self.excel_paths[i])
                self.load_sheets(i)
                # Uncheck other radio buttons
                for j in range(4):
                    if j != i:
                        self.default_excel_radio_buttons[j].setChecked(False)
                break
            else:
                self.excel_input.clear()
                self.sheet_combo.clear()

    def load_sheets(self, index):
        # Load available sheets from the Excel file
        try:
            sheets = pd.read_excel(self.excel_input.text(), sheet_name=None).keys()
            self.sheet_combo.clear()
            self.sheet_combo.addItems(sheets)
        except Exception as e:
            print(f"Error loading sheets: {e}")

    def browse_excel(self):
        # Open a file dialog to select an Excel file
        filepath, _ = QFileDialog.getOpenFileName(self, 'Select Excel File', '', 'Excel Files (*.xlsx *.xls)')
        if filepath:
            self.excel_input.setText(filepath)
            self.load_sheets(0)  # Load sheets for the default state

    def browse_filepath(self):
        # Open a file dialog to select a file
        
        #filepath, _ = QFileDialog.getOpenFileName(self, 'Select File', '', 'All Files (*)')
        filepath, _ = QFileDialog.getOpenFileName(self, 'Select File', '', 'Dat Files (*.dat)')
        if filepath:
            self.filepath_input.setText(filepath)

    def submit_data(self):
        # Retrieve the input data
        self.result_excel_filepath = self.excel_input.text()
        self.result_sheet = self.sheet_combo.currentText()
        self.result_filepath = self.filepath_input.text()
        self.result_note = self.note_input.toPlainText()
        self.result_TSC = self.TSCgood_label.isChecked()
        self.result_part = self.partgood_label.isChecked()
        self.result_value = self.input_dict[self.key_combo.currentText()]

        # Close the window or perform any other actions
        self.close()


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure



class DictEditorApp(QWidget):
    def __init__(self, input_dict, series1, series2,typical,minimum):
        super().__init__()

        self.input_dict = input_dict
        self.series1 = series1
        self.series2 = series2
        
        self.typical=typical
        self.minimum=minimum
        
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()

        # Create QLineEdit widgets for dictionary values
        self.line_edits = {}
        for key, value in self.input_dict.items():
            label = QLabel(key)
            line_edit = QLineEdit(str(value))
            self.line_edits[key] = line_edit

            self.layout.addWidget(label)
            self.layout.addWidget(line_edit)

        # Create Matplotlib canvas for plotting
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.layout.addWidget(self.canvas)

        # Add a submit button
        submit_button = QPushButton('Submit', self)
        submit_button.clicked.connect(self.on_submit_clicked)
        self.layout.addWidget(submit_button)
        
        
        
        #finalize layout
        self.setLayout(self.layout)
        self.setWindowTitle('Final Data Submittal')
        self.plot_series()
 
    def on_submit_clicked(self):
        # Update the dictionary with the values from QLineEdit widgets
        for key, line_edit in self.line_edits.items():
            self.input_dict[key] = line_edit.text()

        # Display the updated dictionary
        print("Updated Dictionary:", self.input_dict)
        self.close()
        # Plot the two Pandas Series
        

    def plot_series(self):
        # Clear the previous plot
        self.ax.clear()

        # Get x, y values from Pandas Series
        x_values = self.series1.values
        y_values = self.series2
        
        typical_power=self.typical
        min_power=self.minimum
        # Plot x-y graph
        self.ax.plot(x_values, y_values, marker='o', linestyle='-', color='b')
        
        self.ax.axhline(typical_power, color='g', linestyle='-')
        self.ax.axhline(min_power, color='r', linestyle='-')
        
        self.ax.set_title('')
        self.ax.set_xlabel(self.series1.name)
        self.ax.set_ylabel("Power (dbM)")
        
        # Redraw the canvas
        self.canvas.draw()
        
        

if __name__ == '__main__':
    # run to test gui
    input_dictionary = {'Name': 'Daulton', 'Age': 30, 'City': 'Charlottesville'}

    # test data
    series1 = pd.Series([1, 2, 3, 4, 5], name='Frequency')
    series2 = pd.Series([5, 4, 3, 2, 1], name='Power')
    typical=2
    minimum=1
    app = QApplication(sys.argv)
    window = DictEditorApp(input_dictionary, series1, series2,typical,minimum)
    window.show()
    sys.exit(app.exec_())


