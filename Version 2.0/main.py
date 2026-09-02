import sys
import os
import pandas as pd
from PyQt6 import QtWidgets
from ui_main import Ui_DataAgentUI
import json
from agent import Agent
from deepseek_model import DeepSeekModel


# -----------------------------
# Output counter helpers
# -----------------------------
def load_output_counter():
    if not os.path.exists("output_counter.txt"):
        with open("output_counter.txt", "w", encoding="utf-8") as f:
            f.write("0")
        return 0

    with open("output_counter.txt", "r", encoding="utf-8") as f:
        content = f.read().strip()

    if content == "":
        with open("output_counter.txt", "w", encoding="utf-8") as f:
            f.write("0")
        return 0

    return int(content)


def create_output_folder(counter):
    folder = f"outputs/output_{counter}"
    os.makedirs(folder, exist_ok=True)
    return folder


def save_output_counter(counter):
    with open("output_counter.txt", "w", encoding="utf-8") as f:
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
        self.agent = Agent(self.model)

        self.dataset_path = None

        self.ui.btn_addDataset.clicked.connect(self.handle_add_dataset)
        self.ui.btn_cleanData.clicked.connect(self.handle_clean_data)
        self.ui.btn_openOutput.clicked.connect(self.handle_open_output)

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

    def handle_clean_data(self):
        if not self.dataset_path:
            self.ui.txt_logOutput.setText("Please select a dataset first.")
            return

        counter = load_output_counter()
        output_folder = create_output_folder(counter)

        log_text = ""

        # 1) Load dataset
        df = pd.read_csv(self.dataset_path)
        log_text += f"Dataset loaded: {self.dataset_path}\n\n"

        # 2) Generate cleaning plan
        plan = self.agent.generate_plan(df)
        log_text += "=== Cleaning Plan ===\n"
        log_text += json.dumps(plan, indent=4) + "\n\n"

        # 3) Clean dataset
        cleaned_df, logs = self.agent.clean_data(df)

        log_text += "=== Execution Logs ===\n"
        for entry in logs:
            log_text += entry + "\n"
        log_text += "\nData cleaned.\n\n"

        # 4) Save outputs (CSV only)
        cleaned_df.to_csv(os.path.join(output_folder, "cleaned.csv"), index=False)

        with open(os.path.join(output_folder, "logs.txt"), "w", encoding="utf-8") as f:
            for entry in logs:
                f.write(entry + "\n")

        with open(os.path.join(output_folder, "plan.json"), "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=4)

        log_text += f"Outputs saved in: {output_folder}\n"

        save_output_counter(counter + 1)

        self.ui.txt_logOutput.setText(log_text)

    def handle_open_output(self):
        base = "outputs"

        if not os.path.exists(base):
            self.ui.txt_logOutput.setText("No output folder found.")
            return

        folders = [f for f in os.listdir(base) if f.startswith("output_")]

        if not folders:
            self.ui.txt_logOutput.setText("No output folder found.")
            return

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
