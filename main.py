import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QListWidget, QDateEdit, QTimeEdit,
    QDoubleSpinBox, QSpinBox, QMessageBox, QStackedWidget, QGroupBox,
    QFormLayout
)
from PyQt5.QtCore import QDate, QTime, Qt
from PyQt5.QtGui import QFont
from datetime import datetime, timedelta

# -----------------------
# Helper Functions
# -----------------------
def calculate_duration_minutes(start_time, end_time):
    start_dt = datetime.combine(datetime.today(), start_time)
    end_dt = datetime.combine(datetime.today(), end_time)
    if end_time < start_time:
        end_dt += timedelta(days=1)
    duration = end_dt - start_dt
    return int(duration.total_seconds() / 60)

def calculate_cost(duration_minutes, hourly_rate, time_increment_minutes):
    # Round up to nearest increment for billing
    rounded_minutes = ((duration_minutes + time_increment_minutes - 1) // time_increment_minutes) * time_increment_minutes
    return hourly_rate * (rounded_minutes / 60)

# -----------------------
# Data Storage
# -----------------------
DATA_DIR = "appts"
CLIENTS_FILE = os.path.join(DATA_DIR, "clients.json")
APPTS_FILE = os.path.join(DATA_DIR, "appointments.json")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

clients = {}
appointments = {}
client_counter = 1
appointment_counter = 1

def load_data():
    global clients, appointments, client_counter, appointment_counter
    # Load clients
    if os.path.exists(CLIENTS_FILE):
        with open(CLIENTS_FILE, "r") as f:
            clients.update(json.load(f))
    # Load appointments
    if os.path.exists(APPTS_FILE):
        with open(APPTS_FILE, "r") as f:
            appts = json.load(f)
            for k, v in appts.items():
                # Convert time strings back to time objects
                v['start'] = datetime.strptime(v['start'], "%H:%M:%S").time()
                v['end'] = datetime.strptime(v['end'], "%H:%M:%S").time()
                appointments[k] = v
    # Update counters
    if clients:
        client_counter = max(int(cid[1:]) for cid in clients.keys()) + 1
    if appointments:
        appointment_counter = max(int(aid[1:]) for aid in appointments.keys()) + 1

def save_data():
    # Save clients
    with open(CLIENTS_FILE, "w") as f:
        json.dump(clients, f, indent=4)
    # Save appointments
    to_save = {}
    for k, v in appointments.items():
        appt_copy = v.copy()
        # Convert time objects to strings
        appt_copy['start'] = appt_copy['start'].strftime("%H:%M:%S")
        appt_copy['end'] = appt_copy['end'].strftime("%H:%M:%S")
        to_save[k] = appt_copy
    with open(APPTS_FILE, "w") as f:
        json.dump(to_save, f, indent=4)

# -----------------------
# Main GUI
# -----------------------
class AppointmentTimerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Appointment Timer")
        self.setGeometry(100, 100, 900, 600)
        self.apply_stylesheet()

        # Load data
        load_data()

        # Stacked widget for pages
        self.pages = QStackedWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.pages)
        self.setLayout(main_layout)

        # Clients page
        self.clients_page = QWidget()
        self.pages.addWidget(self.clients_page)
        self.setup_clients_ui()

        # Appointments page
        self.appointments_page = QWidget()
        self.pages.addWidget(self.appointments_page)
        self.setup_appointments_ui()

        # Track current client
        self.current_client_id = None
        
        # Date filter state
        self.date_filter_active = False
        self.filter_from = None
        self.filter_to = None

        # Refresh client list on startup
        self.refresh_client_list()

    # -------------------
    # Stylesheet
    # -------------------
    def apply_stylesheet(self):
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI'; font-size: 11pt; }
            QLabel { color: #333333; }
            QLineEdit, QDateEdit, QTimeEdit, QDoubleSpinBox, QSpinBox {
                padding: 8px; border: 2px solid #e0e0e0; border-radius: 6px; background-color: #fff;
            }
            QLineEdit:focus, QDateEdit:focus, QTimeEdit:focus, 
            QDoubleSpinBox:focus, QSpinBox:focus {
                border: 2px solid #4a9eff;
            }
            QPushButton {
                padding: 10px 20px; background-color: #4a9eff; color: white; border: none; border-radius: 6px;
                font-weight: bold; min-height: 35px;
            }
            QPushButton:hover { background-color: #3a8eef; }
            QPushButton:pressed { background-color: #2a7edf; }
            QListWidget { border: 2px solid #e0e0e0; border-radius: 6px; background-color: #fff; padding: 5px; }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #f0f0f0; }
            QListWidget::item:hover { background-color: #f5f5f5; }
            QListWidget::item:selected { background-color: #e8f4ff; color: #333; }
            QGroupBox {
                font-weight: bold; border: 2px solid #e0e0e0; border-radius: 8px; 
                margin-top: 10px; padding-top: 15px; background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 15px; padding: 0 5px;
            }
        """)

    # -------------------
    # Clients Page
    # -------------------
    def setup_clients_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        self.clients_page.setLayout(layout)

        layout.addWidget(QLabel("Clients"))

        self.client_list = QListWidget()
        self.client_list.itemDoubleClicked.connect(self.open_client_appointments)
        layout.addWidget(self.client_list)

        # Add client form
        self.client_name_input = QLineEdit()
        self.client_name_input.setPlaceholderText("Name")
        layout.addWidget(self.client_name_input)
        self.client_phone_input = QLineEdit()
        self.client_phone_input.setPlaceholderText("Phone")
        layout.addWidget(self.client_phone_input)
        self.client_email_input = QLineEdit()
        self.client_email_input.setPlaceholderText("Email")
        layout.addWidget(self.client_email_input)

        add_client_btn = QPushButton("Add Client")
        add_client_btn.clicked.connect(self.add_client)
        layout.addWidget(add_client_btn)
        layout.addStretch()

    def refresh_client_list(self):
        self.client_list.clear()
        for cid, data in clients.items():
            display = data['name']
            if data.get('phone'): display += f" • {data['phone']}"
            if data.get('email'): display += f" • {data['email']}"
            self.client_list.addItem(display)

    def add_client(self):
        global client_counter
        name = self.client_name_input.text().strip()
        phone = self.client_phone_input.text().strip()
        email = self.client_email_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Name is required")
            return
        cid = f"c{client_counter}"
        client_counter += 1
        clients[cid] = {"name": name, "phone": phone, "email": email}
        self.client_name_input.clear()
        self.client_phone_input.clear()
        self.client_email_input.clear()
        self.refresh_client_list()
        save_data()

    def open_client_appointments(self, item):
        # Match by name (first bullet)
        name = item.text().split(" • ")[0]
        for cid, data in clients.items():
            if data['name'] == name:
                self.current_client_id = cid
                break
        if self.current_client_id:
            self.load_appointments()
            self.pages.setCurrentWidget(self.appointments_page)

    # -------------------
    # Appointments Page
    # -------------------
    def setup_appointments_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.appointments_page.setLayout(main_layout)

        # Header with client name and back button
        header_layout = QHBoxLayout()
        self.client_label = QLabel("Appointments for:")
        label_font = QFont()
        label_font.setPointSize(16)
        label_font.setBold(True)
        self.client_label.setFont(label_font)
        header_layout.addWidget(self.client_label)
        header_layout.addStretch()
        back_btn = QPushButton("← Back to Clients")
        back_btn.clicked.connect(self.go_back_to_clients)
        header_layout.addWidget(back_btn)
        main_layout.addLayout(header_layout)

        # Date filter section
        filter_group = QGroupBox("Filter by Date Range")
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("From:"))
        self.filter_from_date = QDateEdit()
        self.filter_from_date.setCalendarPopup(True)
        self.filter_from_date.setDate(QDate.currentDate().addYears(-1))
        filter_layout.addWidget(self.filter_from_date)
        filter_layout.addWidget(QLabel("To:"))
        self.filter_to_date = QDateEdit()
        self.filter_to_date.setCalendarPopup(True)
        self.filter_to_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.filter_to_date)
        filter_layout.addStretch()
        apply_filter_btn = QPushButton("Apply Filter")
        apply_filter_btn.clicked.connect(self.apply_date_filter)
        filter_layout.addWidget(apply_filter_btn)
        clear_filter_btn = QPushButton("Clear Filter")
        clear_filter_btn.clicked.connect(self.clear_date_filter)
        filter_layout.addWidget(clear_filter_btn)
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)

        # Totals section
        totals_group = QGroupBox("Totals")
        totals_layout = QHBoxLayout()
        totals_layout.setSpacing(20)
        self.total_appointments_label = QLabel("Appointments: 0")
        totals_layout.addWidget(self.total_appointments_label)
        self.total_duration_label = QLabel("Total Duration: 0 min")
        totals_layout.addWidget(self.total_duration_label)
        totals_layout.addStretch()
        self.total_cost_label = QLabel("Total Cost: $0.00")
        totals_font = QFont()
        totals_font.setBold(True)
        totals_font.setPointSize(12)
        self.total_cost_label.setFont(totals_font)
        totals_layout.addWidget(self.total_cost_label)
        totals_group.setLayout(totals_layout)
        main_layout.addWidget(totals_group)

        # Appointments list section
        list_group = QGroupBox("Appointments")
        list_layout = QVBoxLayout()
        self.appt_list = QListWidget()
        list_layout.addWidget(self.appt_list)
        list_group.setLayout(list_layout)
        main_layout.addWidget(list_group)

        # Appointment form section
        form_group = QGroupBox("Add New Appointment")
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignRight)

        # Date
        self.appt_date = QDateEdit()
        self.appt_date.setCalendarPopup(True)
        self.appt_date.setDate(QDate.currentDate())
        form_layout.addRow("Date:", self.appt_date)

        # Time inputs in horizontal layout
        time_layout = QHBoxLayout()
        time_layout.setSpacing(10)
        self.appt_start = QTimeEdit()
        self.appt_start.setTime(QTime.currentTime())
        time_layout.addWidget(QLabel("Start:"))
        time_layout.addWidget(self.appt_start)
        time_layout.addStretch()
        self.appt_end = QTimeEdit()
        self.appt_end.setTime(QTime.currentTime())
        time_layout.addWidget(QLabel("End:"))
        time_layout.addWidget(self.appt_end)
        time_layout.addStretch()
        time_widget = QWidget()
        time_widget.setLayout(time_layout)
        form_layout.addRow("Time:", time_widget)

        # Rate input (hourly)
        self.rate_input = QDoubleSpinBox()
        self.rate_input.setPrefix("$")
        self.rate_input.setSuffix(" / hour")
        self.rate_input.setValue(31.50)
        self.rate_input.setDecimals(2)
        self.rate_input.setSingleStep(0.50)
        self.rate_input.setMaximum(10000.00)
        form_layout.addRow("Hourly Rate:", self.rate_input)

        # Increment input
        self.increment_input = QSpinBox()
        self.increment_input.setSuffix(" minutes")
        self.increment_input.setValue(6)
        self.increment_input.setMinimum(1)
        self.increment_input.setMaximum(60)
        form_layout.addRow("Billing Increment:", self.increment_input)

        form_group.setLayout(form_layout)
        main_layout.addWidget(form_group)

        # Add button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        add_appt_btn = QPushButton("Add Appointment")
        add_appt_btn.clicked.connect(self.add_appointment)
        button_layout.addWidget(add_appt_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        main_layout.addStretch()

    def go_back_to_clients(self):
        self.refresh_client_list()
        self.pages.setCurrentWidget(self.clients_page)

    def load_appointments(self):
        self.appt_list.clear()
        if not self.current_client_id:
            # Reset totals when no client selected
            self.total_appointments_label.setText("Appointments: 0")
            self.total_duration_label.setText("Total Duration: 0 min")
            self.total_cost_label.setText("Total Cost: $0.00")
            return
        client_name = clients[self.current_client_id]["name"]
        self.client_label.setText(f"Appointments for: {client_name}")
        
        # Filter and display appointments
        total_count = 0
        total_duration = 0
        total_cost = 0.0
        
        for appt in appointments.values():
            if appt["client_id"] == self.current_client_id:
                # Apply date filter if active
                if self.date_filter_active:
                    appt_date = datetime.strptime(appt['date'], "%Y-%m-%d").date()
                    if self.filter_from and appt_date < self.filter_from:
                        continue
                    if self.filter_to and appt_date > self.filter_to:
                        continue
                
                start = appt['start'].strftime("%I:%M %p")
                end = appt['end'].strftime("%I:%M %p")
                dur = f"{appt['duration']} min"
                cost = f"${appt['cost']:.2f}"
                self.appt_list.addItem(f"{appt['date']} • {start}-{end} ({dur}) • {cost}")
                
                # Calculate totals
                total_count += 1
                total_duration += appt['duration']
                total_cost += appt['cost']
        
        # Update totals display
        self.total_appointments_label.setText(f"Appointments: {total_count}")
        self.total_duration_label.setText(f"Total Duration: {total_duration} min")
        self.total_cost_label.setText(f"Total Cost: ${total_cost:.2f}")
    
    def apply_date_filter(self):
        self.filter_from = self.filter_from_date.date().toPyDate()
        self.filter_to = self.filter_to_date.date().toPyDate()
        
        if self.filter_from > self.filter_to:
            QMessageBox.warning(self, "Error", "From date must be before or equal to To date")
            return
        
        self.date_filter_active = True
        self.load_appointments()
    
    def clear_date_filter(self):
        self.date_filter_active = False
        self.filter_from = None
        self.filter_to = None
        self.filter_from_date.setDate(QDate.currentDate().addYears(-1))
        self.filter_to_date.setDate(QDate.currentDate())
        self.load_appointments()

    def add_appointment(self):
        global appointment_counter
        if not self.current_client_id:
            QMessageBox.warning(self, "Error", "No client selected")
            return
        date_str = self.appt_date.date().toString("yyyy-MM-dd")
        start_time = self.appt_start.time().toPyTime()
        end_time = self.appt_end.time().toPyTime()
        rate = self.rate_input.value()
        increment = self.increment_input.value()
        duration = calculate_duration_minutes(start_time, end_time)
        cost = calculate_cost(duration, rate, increment)

        aid = f"a{appointment_counter}"
        appointment_counter += 1
        appointments[aid] = {
            "client_id": self.current_client_id,
            "date": date_str,
            "start": start_time,
            "end": end_time,
            "duration": duration,
            "cost": cost
        }
        self.load_appointments()
        save_data()

# -----------------------
# Run App
# -----------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppointmentTimerApp()
    window.show()
    sys.exit(app.exec_())
