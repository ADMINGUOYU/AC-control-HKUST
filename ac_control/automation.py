# This module defines the ACController class, 
# which uses Selenium to automate interactions

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Exception classes for ACController operations.
class ACControllerError(Exception):
    """
    Raised when the AC controller cannot perform an action.
    """

# Data structure for login configuration.
@dataclass
class LoginConfig:
    username: str
    password: str
    headless: bool = False


class ACController:

    """
    Encapsulates Selenium interactions with the AC control portal.
    """

    # Webpage URLs
    HOME_URL = "https://w5.ab.ust.hk/njggt/app/home"
    LOGOUT_URL = "https://w5.ab.ust.hk/njggt/app/logout"

    # Page element locators
    EMAILFIELD = (By.ID, "i0116")
    PASSWORDFIELD = (By.ID, "i0118")
    NEXTBUTTON = (By.ID, "idSIButton9")
    DUO_OTHERPEOPLE_USING_DEVICE = (By.ID, "dont-trust-browser-button")
    DO_NOT_KEEP_SIGNED_IN = (By.ID, "idBtn_Back")
    LOGOUT_SIGNAL = (By.ID, "login_workload_logo_text")

    def __init__(self, login_config: LoginConfig):

        self.login_config = login_config
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None

    def start(self) -> None:

        """
        Create the browser session and navigate to the home page.
        """

        # Get chrome driver path
        # We expect /bin for Linux/MacOS and /Scripts for Windows.
        driver_path = Path(sys.prefix).resolve()
        if sys.platform.startswith("win"):
            driver_path = driver_path / "Scripts" / "chromedriver.exe"
        else:
            driver_path = driver_path / "bin" / "chromedriver"
        # Check if the driver exists at the expected location
        if not driver_path.exists():
            raise ACControllerError(f"Chromedriver not found at {driver_path}. Please run setup.sh to install it.")

        # Prepare driver options
        options = webdriver.ChromeOptions()
        if self.login_config.headless:
            # DUO 2FA typically requires a visible browser; headless is optional.
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        # Instantiate the driver
        self.driver = webdriver.Chrome(service = Service(driver_path), options = options)
        
        # Set up an explicit wait (timeout)
        self.wait = WebDriverWait(self.driver, 30)

        # Navigate to the home page and perform login steps
        self.driver.get(self.HOME_URL)
        self._perform_login()

    # Login flow
    def _perform_login(self) -> None:
        
        """
        Fill in credentials where possible; DUO requires manual completion.
        """

        if not self.driver or not self.wait:
            # This should never happen since start() initializes these, 
            # but we check to play safe.
            raise ACControllerError("Driver is not initialized.")
        try:
            # Fill in the username and password fields and submit the form.
            self.wait.until(EC.element_to_be_clickable(self.EMAILFIELD)).send_keys(
                self.login_config.username
            )
            self.wait.until(EC.element_to_be_clickable(self.NEXTBUTTON)).click()
            self.wait.until(EC.element_to_be_clickable(self.PASSWORDFIELD)).send_keys(
                self.login_config.password
            )
            self.wait.until(EC.element_to_be_clickable(self.NEXTBUTTON)).click()
            
            # Wait until user complete DUO
            print("Please complete the DUO 2FA authentication when prompted >>>")
            # And click "No, other people use this device" after DUO (for security resons)
            # This time we wait for longer time (2 minutes) (modify self.wait's timeout)
            self.wait.timeout = 120
            self.wait.until(EC.element_to_be_clickable(self.DUO_OTHERPEOPLE_USING_DEVICE)).click()
            print("DUO authentication completed. Continuing with the login flow...")
            # Click "No" on "Keep me signed in?" prompt
            self.wait.until(EC.element_to_be_clickable(self.DO_NOT_KEEP_SIGNED_IN)).click()
            self.wait.timeout = 30

        except Exception:
            # The page flow can differ if the user is already authenticated; allow
            # the user to continue to DUO or any additional prompts manually.
            print("Login flow encountered an issue. Please complete any remaining steps manually.")
            print("If in headless mode, please kill and restart the program.")

    # Methods to interact with the AC control page
    # Get the current AC status (ON/OFF)
    def get_status(self) -> str:

        """
        Return the current AC status ('ON', 'OFF', or 'nil').
        NOTE: 'nil' is returned if the status cannot be determined (e.g., due to a page load issue).
        """

        if not self.driver:
            return "nil"
        try:
            # The status is determined by the text inside a span element
            # within the switch component.
            span_element = self.driver.find_element(
                By.XPATH, '//span[@class="ant-switch-inner"]'
            )
            return span_element.text
        except Exception:
            return "nil"
    # Get the remaining balance (e.g., in minutes)
    def get_balance(self) -> str:

        """
        Return the remaining balance as a string or 'nil'.
        """

        if not self.driver:
            return "nil"
        try:
            # Locate the balance element
            balance_element = self.driver.find_element(
                by = By.CLASS_NAME, value = "ant-progress-text"
            )
            # Fetch the text
            regex = r"(\d+)"
            remain_balance = [float(x) for x in re.findall(regex, balance_element.text)]
            # Return balance in digits of minutes, right-aligned in a 5-character field
            return f"{remain_balance[0]:>5}"
        except Exception:
            return "nil"

    # Toggle the AC power state (ON/OFF)
    def toggle_power(self) -> bool:

        """
        Toggle the AC power state.
        """

        if not self.driver:
            return False
        try:
            # Find that switch
            switch_button = self.driver.find_element(
                by = By.CLASS_NAME, value = "ant-switch"
            )
            # Click the switch to toggle the state
            switch_button.click()
            # Wait for any potential alert to appear and accept it 
            # (e.g., confirmation dialog)
            wait = WebDriverWait(self.driver, timeout = 3)
            try:
                alert = wait.until(EC.alert_is_present())
                alert.accept()
            except TimeoutException:
                pass
            return True
        except Exception:
            return False

    # Logout and clean up the driver session
    def logout(self) -> None:
        if not self.driver:
            return
        try:
            # Navigate Jump to logout URL
            self.driver.get(self.LOGOUT_URL)
            # Wait until logout is complete
            self.wait.until(EC.presence_of_element_located(self.LOGOUT_SIGNAL))
        finally:
            self.driver.quit()
            self.driver = None