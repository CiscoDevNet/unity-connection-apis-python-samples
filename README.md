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

## Getting started

* Install Python 3

  (On Windows, choose the option to add to PATH environment variable)

* Clone this repository:

    ```bash
    git clone https://www.github.com/CiscoDevNet/unity-connection-apis-python-samples
    ```

* Create a Python virtual environment:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
* Dependency Installation:

    ```bash
    pip install -r requirements.txt
    ```
  
* Rename the file `.env.example` to `.env` and edit to specify your CUC address and API user credentials - the user must be an administrator:

    ![user config](assets/images/user_config.png)

    >Note: see individual sample header comments for additional configs as needed

    >Note: pre-populated configurations in .env.example will work when connecting to a [DevNet 'Collaboration x.x' Sandbox](https://devnetsandbox.cisco.com/RM/Topology?c=37ab87fa-8dc5-4667-b461-0e7dab07176b)

* If using VS Code, simply open the **Run** tab, select the desired sample and click the green 'run' arrow.

    Otherwise, from the terminal you can launch Flask-based apps like so:

    ```bash
    FLASK_APP=cuni_notification_logger.py python -m flask run --host=0.0.0.0 --port=5000
    ```

## Hints

* Samples based on the Python Flask web server are launched using the lightweight built-in server - for production use, the application should be [deployed to a proper WSGI web server](https://flask.palletsprojects.com/en/1.1.x/deploying/#deployment)