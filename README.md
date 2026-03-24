# A/C Scheduler 2.0

> [!TIP]
> Made for HKUST student Hall Air Conditioning service\
> Now coming to web-based version!

Tiered of the poorly engineered A/C scheduling system in HKUST student halls? 

... Haha, "University of **Science and Technology**" indeed ...

... Not even meter the usage on power consumption ...

This project is here to help! 
Although it is not a nice piece of software, it is a working one!

All it does is to turn the A/C **ON** and **OFF** at a set interval. Helping you to **save MONEY**!

## Usage

> [!TIP]
> Your system must have Chrome or Chromium installed to run the scheduler, as it relies on Selenium WebDriver to automate the browser interactions.

1. Clone the repository
    ```bash
    git clone https://github.com/ADMINGUOYU/AC-control-HKUST.git
    ```
2. Run the setup script to install the dependencies 
    ```bash
    bash setup.sh
    ```
3. Configure your account details (refer to `start.sh`)
    > You can set the corresponding `AC_USERNAME` and `AC_PASSWORD` environment variables to avoid hardcoding your credentials in the script.

    > ALWAYS KEEP YOUR CREDENTIALS SAFE!
4. Run the start script to start the scheduler
    ```bash
    bash start.sh
    ```

> [!TIP]
> You can connect to `http://<ip_address>:<port>` to access the web-based dashboard. (Replace `<ip_address>` and `<port>` with the actual IP address and port of the machine running the scheduler)\
> NOTE: We only support **http** for now, so make sure to use the correct protocol when accessing the dashboard.