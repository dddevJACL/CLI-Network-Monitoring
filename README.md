# CLI-Network-Monitoring
Monitor and Configure Network Connections in the CLI

## To run:
1. After cloning or downloading, navigate to the directory on your computer where the do directory lies
2. (optional, suggested) Create a virtual environment, so that installed packages will only affect / be available to this project. To start up a python virtual environment:
      * a. pip install virtualenv                (install the virtual environment package)
      * b. python -m venv network_monitoring     (create a virtual environment, 'network_monitoring' can be replaced with a name of your choosing)
      * c. network_monitoring \Scripts\activate   (activate the virtual environment, type 'deactivate' to close

To run this project, you will need Python installed, and will need to install all 
packages from pip that are listed below:
* pip install prompt-toolkit
* pip install requests
* pip install ntplib
* pip install dnspython


To run the program, open the windows command prompt,
navigate to the folder where you extracted the
python files (Network_Monitoring_App.py and Monitoring_Configuration.py), then type:
python Network_Monitoring_App.py
(Or the given way to run a file on your system)
to start the program.


At any point in the program, type 'cancel' to return to the main loop.
In the main loop, type 'exit' to quit the program.
Type 'help' to see a list of commands


To Monitor a service, type 'new'
Then choose the service you would like to monitor (HTTP, HTTPS, DNS, TCP, etc.)
In this menu, you will first be prompted to enter a url, hostname, or ip address, depending
on the type of service you would like to monitor.
Some services will require more information, like DNS, which will then prompt you for a 
query and then for a record type.
Finally, you will be prompted for a time interval for monitoring (in seconds).

To create an echo server, type 'create'
Choose TCP
Then create a custom name, choose a port number, and choose a message to be echoed.

Type 'view' to see a list of services that you are monitoring, and have an option to delete them.
