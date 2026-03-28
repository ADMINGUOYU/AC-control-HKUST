# A/C Scheduler 2.0

> [!TIP]
> Made for HKUST student Hall Air Conditioning service\
> Now coming to web-based version!

Tired of the poorly engineered A/C scheduling system in HKUST student halls? 

... Haha, "University of **Science and Technology**" indeed ...

... Not even would they meter the usage on power consumption ...

This project is here to help! 
Although it is not a nice piece of software, it is a working one!

All it does is to turn the A/C **ON** and **OFF** at a set interval. Helping you to **save MONEY**!

## Usage

> [!TIP]
> Your system must have **Chrome** or **Chromium** installed to run the scheduler, as it relies on Selenium WebDriver to automate the browser interactions.\
**Microsoft Edge is not compatible in some cases.**

1. Clone the repository
    ```bash
    git clone https://github.com/ADMINGUOYU/AC-control-HKUST.git
    ```
    Alternatively, you can download the ZIP file from the GitHub repository and extract it to your desired location. (Code -> Download ZIP)

2. Run the setup script to install the dependencies 
    ```bash
    # Linux/MacOS users
    bash setup.sh
    ```
    ```bat
    @REM Windows users
    @REM Double-click runnable
    setup.bat
    ```
3. Configure your account details (refer to `start.sh` or `start.bat` for the required environment variables)
    > You can set the corresponding `AC_USERNAME` and `AC_PASSWORD` environment variables to avoid hardcoding your credentials in the script.\
    For `AC_USERNAME`, please include the domain `@connect.ust.hk` as part of your username.

    > For Windows users using `start.bat`, right-click the file, select "Edit", and set the `AC_USERNAME` and `AC_PASSWORD` variables in the script before saving it.\
    (Please note if your password contains `^` or `!`, you need to escape them with `^^` and `^!` respectively in the batch file.)

    > **ALWAYS KEEP YOUR CREDENTIALS SAFE!**
4. Run the start script to start the scheduler
    ```bash
    # Linux/MacOS users
    bash start.sh
    ```
    ```bat
    @REM Windows users
    @REM Double-click runnable
    start.bat
    ```

> [!TIP]
> You can connect to `http://<ip_address>:<port>` to access the web-based dashboard. (Replace `<ip_address>` and `<port>` with the actual IP address and port of the machine running the scheduler)\
> NOTE: We only support **http** for now, so make sure to use the correct protocol when accessing the dashboard.