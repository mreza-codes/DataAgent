import sys
import os
import pandas as pd
from PyQt6 import QtWidgets
from ui_main import Ui_DataAgentUI
import json
from agent import DataAgent
from deepseek_model import DeepSeekModel


# -----------------------------
# Output counter functions
# -----------------------------
def load_output_counter():
    """Read the current output counter from file."""
    if not os.path.exists("output_counter.txt"):
        with open("output_counter.txt", "w") as f:
            f.write("0")
        return 0

    with open("output_counter.txt", "r") as f:
        content = f.read().strip()

    if content == "":
        with open("output_counter.txt", "w") as f:
            f.write("0")
        return 0

    return int(content)


def create_output_folder(counter):
    """Create a new output folder based on counter."""
    folder = f"outputs/output_{counter}"
    os.makedirs(folder, exist_ok=True)
    return folder


def save_output_counter(counter):
    """Save updated counter value."""
    with open("output_counter.txt", "w") as f:
        f.write(str(counter))



# -----------------------------
# Main UI class
# -----------------------------
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_DataAgentUI()
        self.ui.setupUi(self)

        self.model = DeepSeekModel()
        self.agent = DataAgent(self.model)

        self.dataset_path = None

        # Connect buttons
        self.ui.btn_addDataset.clicked.connect(self.handle_add_dataset)
        self.ui.btn_cleanData.clicked.connect(self.handle_clean_data)
        self.ui.btn_openOutput.clicked.connect(self.handle_open_output)


    # -----------------------------
    # Select dataset file
    # -----------------------------
    def handle_add_dataset(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Dataset",
            "",
            "CSV Files (*.csv)"
        )

        if file_path:
            self.dataset_path = file_path
            self.ui.txt_logOutput.setText(f"Dataset loaded:\n{file_path}")


    # -----------------------------
    # Run agent and clean dataset
    # -----------------------------
    def handle_clean_data(self):
        if not self.dataset_path:
            self.ui.txt_logOutput.setText("Please select a dataset first.")
            return

        counter = load_output_counter()
        output_folder = create_output_folder(counter)

        log = ""

        # 1) Load dataset
        self.agent.load_file(self.dataset_path)
        log += f"Dataset loaded: {self.dataset_path}\n\n"

        # 2) Generate cleaning plan
        plan = self.agent.reason()
        log += "=== Cleaning Plan ===\n"
        log += json.dumps(plan, indent=4) + "\n\n"

        # 3) Clean dataset
        cleaned = self.agent.clean_data()
        log += "Data cleaned.\n\n"

        # 4) Export outputs
        self.agent.export_outputs(output_folder)
        log += f"Outputs saved in: {output_folder}\n"

        # 5) Update counter
        save_output_counter(counter + 1)

        self.ui.txt_logOutput.setText(log)


    # -----------------------------
    # Open latest output folder
    # -----------------------------
    def handle_open_output(self):
        base = "outputs"

        # Check if outputs folder exists
        if not os.path.exists(base):
            self.ui.txt_logOutput.setText("No output folder found.")
            return

        # List all output folders
        folders = [f for f in os.listdir(base) if f.startswith("output_")]

        if not folders:
            self.ui.txt_logOutput.setText("No output folder found.")
            return

        # Sort folders by number and get the latest one
        folders.sort(key=lambda x: int(x.split("_")[1]))
        last_folder = folders[-1]

        full_path = os.path.join(base, last_folder)

        if os.path.exists(full_path):
            os.startfile(full_path)
        else:
            self.ui.txt_logOutput.setText("Output folder not found.")



# -----------------------------
# Run application
# -----------------------------
app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
