# AC Control UI

from __future__ import annotations

import time
from tkinter import Button, Label, Text, Tk, messagebox, simpledialog

from ac_control.automation import ACController
from ac_control.state import StatusSnapshot, StatusStore

# Class for the AC Control Window
class ACControlWindow:
    def __init__(self, controller: ACController, status_store: StatusStore):
        self.controller = controller
        self.status_store = status_store
        self.bgColor = "Black"
        self.fgColor = "Aquamarine"
        self.font = ("Courier New", 25)

        self.mainWindow = Tk()
        self.mainWindow.title("AC Controller")
        self.mainWindow.geometry(
            "%dx%d+0+0"
            % (self.mainWindow.winfo_screenwidth(), self.mainWindow.winfo_screenheight())
        )
        self.mainWindow["bg"] = self.bgColor
        self.mainWindow.attributes("-alpha", 1.0)
        self.mainWindow.grid_columnconfigure(1, minsize = 300)

        self.data_time = Label(
            self.mainWindow,
            background = self.bgColor,
            font = self.font,
            fg = self.fgColor,
            justify = "left",
        )
        self.data_time.grid(sticky = "W", row = 0, column = 0)

        self.data_balance = Label(
            self.mainWindow,
            background = self.bgColor,
            font = self.font,
            fg = self.fgColor,
            justify = "left",
        )
        self.data_balance.grid(sticky = "W", row = 1, column = 0)

        self.data_status = Label(
            self.mainWindow,
            background = self.bgColor,
            font = self.font,
            fg = self.fgColor,
            justify = "left",
        )
        self.data_status.grid(sticky = "W", row = 2, column = 0)

        self.data_schedule_interval = Label(
            self.mainWindow,
            background = self.bgColor,
            font = self.font,
            fg = self.fgColor,
            justify = "left",
        )
        self.data_schedule_interval.grid(row = 6, column = 1)

        self.data_Output = Text(self.mainWindow, background = self.bgColor, fg = self.fgColor)
        self.data_Output.grid(sticky = "W", row = 4, column = 0, rowspan = 10, columnspan = 10)

        self.power_switch = Button(
            self.mainWindow,
            bg = "lightblue",
            width = 10,
            command = self.power_switch_func,
        )
        self.power_switch.grid(row = 3, column = 1)

        self.schedule_set = Button(
            self.mainWindow,
            text = "set schedule",
            bg = "lightblue",
            width = 10,
            command = self.set_schedule_func,
        )
        self.schedule_set.grid(row = 4, column = 1)

        self.schedule_switch = Button(
            self.mainWindow,
            bg = "lightblue",
            width = 10,
            command = self.schedule_switch_func,
        )
        self.schedule_switch.grid(row = 5, column = 1)

        self.log_out = Button(
            self.mainWindow,
            bg = "lightblue",
            text = "LOG OUT",
            width = 10,
            command = self.log_out_func,
        )
        self.log_out.grid(row = 1, column = 1)

        self.onTime = 0
        self.offTime = 0
        self.schedule_time_mark = int(time.time())
        self.schedule_start = False
        self.current_status = "nil"
        self.current_time = "nil"
        self.current_balance = "nil"

        self.mainWindow.protocol("WM_DELETE_WINDOW", self.log_out_func)
        self.update_wnd()
        self.mainWindow.mainloop()

    def scheduler(self) -> None:
        if self.current_status == "nil":
            self.schedule_start = False
            self.log_data("status void -> scheduler will turn off")
            return

        if not self.schedule_start:
            return

        if self.toggle_switch():
            if self.current_status == "ON":
                self.schedule_time_mark = int(time.time()) + self.offTime
            elif self.current_status == "OFF":
                self.schedule_time_mark = int(time.time()) + self.onTime
            return

        self.log_data("Scheduler attempt failed, retrying soon...")
        self.schedule_time_mark = int(time.time()) + 5

    # Update the window with the latest data
    def update_wnd(self):
        self.get_balance()
        self.get_current_time()
        self.get_status()

        self.data_balance["text"] = "Remaining Balance >> " + self.current_balance
        self.data_time["text"] = "Current Time >> " + self.current_time
        self.data_status["text"] = "Current status >> " + self.current_status

        if self.current_status == "ON":
            self.power_switch["text"] = "OFF"
        elif self.current_status == "OFF":
            self.power_switch["text"] = "ON"
        else:
            self.power_switch["text"] = "NOT CONNECTED"

        interval = int(self.schedule_time_mark) - int(time.time())
        if self.schedule_start:
            if interval <= 0:
                self.scheduler()
            self.data_schedule_interval["text"] = interval
            self.schedule_switch["text"] = "SCHEDULED"
        else:
            self.data_schedule_interval["text"] = "nil"
            self.schedule_switch["text"] = "NOT SCHEDULED"

        snapshot = StatusSnapshot(
            current_time = self.current_time,
            balance = self.current_balance,
            status = self.current_status,
            schedule_start = self.schedule_start,
            schedule_interval = interval if self.schedule_start else 0,
            on_time = self.onTime,
            off_time = self.offTime,
        )
        self.status_store.set_snapshot(snapshot)

        # Update the window every second
        self.mainWindow.after(1000, self.update_wnd)

    # Log data to the output box
    def log_data(self, data: str):
        numlines = int(self.data_Output.index("end - 1 line").split(".")[0])
        self.data_Output["state"] = "normal"
        if numlines == 24:
            self.data_Output.delete(1.0, 2.0)
        if self.data_Output.index("end-1c") != "1.0":
            self.data_Output.insert("end", "\n")
        self.data_Output.insert("end", data)
        self.data_Output["state"] = "disabled"

    # Toggle the AC power and log the action
    def toggle_switch(self) -> bool:
        success = self.controller.toggle_power()
        if success:
            self.log_data(f"Toggle requested -> {self.current_time}")
        else:
            self.log_data("ERROR -> unable to toggle")
        return success

    # Get the current status of the AC and log it
    def get_status(self):
        self.current_status = self.controller.get_status()

    # Get the current balance and log it
    def get_balance(self):
        self.current_balance = self.controller.get_balance()

    # Get the current time and log it
    def get_current_time(self):
        self.current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

    # Power switch function with manual override for the scheduler
    def power_switch_func(self):
        if self.schedule_start:
            self.schedule_start = False
            self.log_data("Manual override -> scheduler will turn off")
        self.toggle_switch()

    # Schedule switch function to start or stop the scheduler
    def schedule_switch_func(self):
        if not self.schedule_start:
            self.schedule_start = True
            self.scheduler()
        else:
            self.schedule_start = False

    # Set schedule function to get ON and OFF times from the user
    # and log the updated schedule
    def set_schedule_func(self):
        self.mainWindow.withdraw()
        try:
            self.onTime = int(simpledialog.askstring("Dialog", "ON Time >>"))
            self.offTime = int(simpledialog.askstring("Dialog", "OFF Time >>"))
        except Exception:
            self.log_data("Try again")
            self.mainWindow.deiconify()
            return
        self.mainWindow.deiconify()
        self.log_data("Schedule Updated >>")
        self.log_data("ON Time -> " + str(self.onTime))
        self.log_data("OFF Time -> " + str(self.offTime))

    # Log out function to log out of the controller and close the window
    def log_out_func(self):
        self.controller.logout()
        self.log_data("Logging out...")
        # Check if the logout was successful before closing the window
        # TODO: Implement a more robust way to check if the logout was successful
        if self.controller.driver is None:
            self.mainWindow.destroy()
        else:
            self.log_data("Logout failed, please try again.")