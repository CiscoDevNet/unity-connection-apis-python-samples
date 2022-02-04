# unity-connection-apis-python-samples

## Overview

Sample scripts demonstrating usage of Cisco Unity Connection APIs with Python

https://developer.cisco.com/site/unity-connection/overview/

## Tested environments

- Ubuntu 19.10
- Python 3.7.5
- Unity Connection 11.5 / 12.5

This project was developed/tested using [Visual Studio Code](https://code.visualstudio.com/)

## Available samples

* `cuni_notification_logger.py` - Demonstrates creating a subscription for mailbox event updates using the CUNI SOAP notification service

* `cupi_add_user.py` - Creates / deletes a test user

* `cumi_send_message.py` -  Executes the following sequence:

    * Creates a test user
    * Sets the user's password
    * Performs a user address lookup
    * Sends a message with audio file attachment
    * Deletes all messages in the user's inbox
    * Deletes the user

* `cupi_add_update_user_notificationdevice.py` - Creates a test user then updates details for the user's default SMTP notification device.

## Getting started

* Install Python 3

  (On Windows, choose the option to add to PATH environment variable)

* Clone this repository:

    ```bash
    git clone https://www.github.com/CiscoDevNet/unity-connection-apis-python-samples
    ```

* Create a [Python virtual environment](https://docs.python.org/3/tutorial/venv.html):

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
* Dependency Installation:

    ```bash
    pip install -r requirements.txt
    ```
  
* [Optional] To enable using a secure HTTPS connection with Unity Connection APIs, you may need to download the CUC `tomcat` certificate (as a PEM chain) and place it in the root directory of this project.

    You can use [openssl](https://www.openssl.org/) to retrieve it from the command line:

    ```
    openssl s_client -showcerts -connect cuc_hostname:443 < /dev/null 2>/dev/null | openssl x509 -outform pem > tomcat.pem
    ```

    Or via a web browser by navigating to the CUC host and clicking on the security icon in the address bar:

    ![more information](assets/images/cert1.png)

    ![PEM chain](assets/images/cert2.png)

    
* Rename the `.env.example` file to `.env`, and edit to specify your CUC details. Note: `APP_USER` must be an administrator:

    ![user config](assets/images/user_config.png)

* If using VS Code, simply open the **Run** tab, select the desired sample and click the green 'run' arrow.

    Otherwise, from the terminal you can launch most samples like:
    
    ```
    python cupi_add_user.py
    ```

    For Flask-based apps (currently only `cuni_notification_logger.py`) use this format:

    ```bash
    FLASK_APP=cuni_notification_logger.py python -m flask run --host=0.0.0.0 --port=5000
    ```
> Note: check the comments in individual sample apps for any special additional configs 

## Hints

* Samples based on Python [Flask(https://flask.palletsprojects.com/en/2.0.x/)] are launched using the lightweight built-in development web server.  For production, applications should always be [deployed to a proper WSGI web server](https://flask.palletsprojects.com/en/2.0.x/deploying/)

* Creating and using a [requests Session](https://2.python-requests.org/en/master/user/advanced/#id1) object allows setting global request parameters like `auth`/`verify`/etc.  In addition, Session implements CUC API `JSESSIONID` cookies (to bypass expensive per-request backend authentication checks), as well as HTTP 1.1 persistent connections (to keep network latency and networking CPU usage lower).