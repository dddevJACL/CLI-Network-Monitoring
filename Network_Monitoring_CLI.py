from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.patch_stdout import patch_stdout
from Monitoring_Configuration import MonitoringConfiguration, MonitorDNS, MonitorNTP, \
    MonitorHTTPS, MonitorTCP, MonitorHTTP, MonitorUDP, MonitorICMP, Server, TCPServer, UDPServer



def main() -> None:
    """
    Main function to handle user input and manage threads.
    In the Main loop, users can create and monitor servers and services. The loop will terminate
    when users call the exit command.
    Uses prompt-toolkit for handling user input with auto-completion and ensures
    the prompt stays at the bottom of the terminal.
    """

    command_completer: WordCompleter = WordCompleter(['exit', 'new', 'create', 'help', 'view'], ignore_case=True)

    session: PromptSession = PromptSession(completer=command_completer)

    monitoring_list = list()
    server_list = list()
    command_dict = {"exit": exit_loop, "new": new_config, "create": new_server, "help": get_help, "view": view_all}
    exit_command = command_dict["help"](monitoring_list, server_list)
    try:
        with patch_stdout():
            while not exit_command:
                user_input: str = session.prompt("Enter command: ")
                if user_input.lower() not in command_dict:
                    print("Invalid command")
                    exit_command = command_dict["help"](monitoring_list, server_list)
                else:
                    if user_input.lower() != "new":
                        exit_command = command_dict[user_input.lower()](monitoring_list, server_list)
                    else:
                        exit_command = command_dict[user_input.lower()](monitoring_list)

    finally:
        monitoring_list_length = len(monitoring_list)
        print("Exiting application...")
        print("Ending all monitoring...")
        for service in monitoring_list:
            print(f"Ending monitoring of {service.get_name()}")
            service.deactivate()
            monitoring_list_length -= 1
            print(f"{monitoring_list_length} monitoring services left to terminate")

        print("Shutting down servers...")
        for server in server_list:
            print(f"Closing connection to {server.get_name()}")
            server.deactivate()
        print("Finished. Goodbye!")


def get_help(monitoring_list, server_list):
    """Print all valid commands"""
    return_to = "enter the"
    if len(monitoring_list) or len(server_list) >= 1:
        return_to = "return to the"
    commands = "The following are valid commands: \nexit: Exit the application\nhelp: Print all valid commands\n" \
               "new: Configure a new service to monitor\ncreate: Create and monitor a new TCP or UDP Echo Server\n" \
               "view: View all servers created and services being monitored. Optionally delete servers and services\n"
    confirmation = None
    while not confirmation:
        confirmation = confirm_yes_no(f"that your ready to {return_to} main loop? Here are the available commands:\n"
                                      + commands + f"Type YES to {return_to} main loop. Ready")
    return False


def view_all(monitoring_list, server_list):
    """View all services being monitored one by one, with an option to permanently delete them"""
    command_completer: WordCompleter = WordCompleter(['CANCEL'], ignore_case=True)
    current_session: PromptSession = PromptSession(completer=command_completer)

    count = 0
    for service in monitoring_list:
        count += 1
        service_type = service.get_service()
        if service_type == "DNS":
            user_command = current_session.prompt(f"Type cancel to go back to main loop, "
                                                  f"or touch any key to see next item in list: ")
            if user_command.lower() == "cancel":
                return cancel(count)
            dns_string = f"\n#{count}. Service type: DNS\nServer: {service.get_name()}\nQuery: {service.get_query()}\n" \
                         f"Record_type: {service.get_record_type()}\nCheck every: " \
                         f"{service.get_time_interval()} second(s)"
            first_confirmation = confirm_yes_no("following service" + dns_string + "would you like to delete")
            if first_confirmation:
                second_confirmation = confirm_yes_no("that you would like to delete" + dns_string)
                if second_confirmation:
                    target_client = monitoring_list.pop(count - 1)
                    print(f"Ending monitoring of {target_client.get_name()}")
                    target_client.deactivate()
                    del target_client
        elif service_type == "TCP" or service_type == "UDP":
            user_command = current_session.prompt(f"Type cancel to go back to main loop, "
                                                  f"or hit enter to see next item in list: ")
            if user_command.lower() == "cancel":
                return cancel(count)
            tcp_udp = f"\n#{count}. Service type: {service_type}\nHost / IP: {service.get_name()}\n" \
                      f"Port number: {service.get_port()}\nCheck every: {service.get_time_interval()} second(s)"
            first_confirmation = confirm_yes_no("following service" + tcp_udp + "would you like to delete")
            if first_confirmation:
                second_confirmation = confirm_yes_no("that you would like to delete" + tcp_udp)
                if second_confirmation:
                    target_client = monitoring_list.pop(count - 1)
                    print(f"Ending monitoring of {target_client.get_name()}")
                    target_client.deactivate()
                    del target_client
        else:
            user_command = current_session.prompt(f"Type cancel to go back to main loop, "
                                                  f"or hit enter to see next item in list: ")
            if user_command.lower() == "cancel":
                return cancel(count)
            service_str = f"\n#{count}. Service type: {service_type}\nHost / IP: {service.get_name()}\n" \
                          f"Check every: {service.get_time_interval()} second(s)"
            first_confirmation = confirm_yes_no("following service" + service_str + "would you like to delete")
            if first_confirmation:
                second_confirmation = confirm_yes_no("that you would like to delete" + service_str)
                if second_confirmation:
                    target_client = monitoring_list.pop(count - 1)
                    print(f"Ending monitoring of {target_client.get_name()}")
                    target_client.deactivate()
                    del target_client

    if len(server_list) == 1:
        user_command = current_session.prompt(f"Type cancel to go back to main loop, "
                                              f"or hit enter to see next item in list")
        if user_command.lower() == "cancel":
            return cancel(count)
        delete_server(monitoring_list, server_list)
    return False


def confirm_yes_no(operation):
    """
    The function confirm_yes_no is used to confirm user choice, giving them a second chance in case of input error
    """
    command_completer: WordCompleter = WordCompleter(['YES', 'NO'], ignore_case=True)
    current_session: PromptSession = PromptSession(completer=command_completer)
    user_confirmation = None
    while user_confirmation is None:
        user_confirmation = current_session.prompt(f"\nConfirm {operation}? YES/NO\n")
        if user_confirmation.upper() == "YES":
            return True
        elif user_confirmation.upper() == "NO":
            return False
        else:
            print(f"Invalid choice. Type 'YES' or 'NO' to confirm {operation} operation")
            user_confirmation = None


def exit_loop(monitoring_list, server_list):
    """
    This function is called if user enters 'create' in the main loop.
    This function ends the main loop. Returning True will break the while loop in the main function.
    """
    confirmation = confirm_yes_no("exit")
    if confirmation:
        print("Exiting application might take some time as app finishes closing all processes")
        return True
    else:
        print("Cancelling exit. Going back to main loop...")
        return False


def new_config(monitor_list):
    """
    This function is called if user enters 'new' in the main loop. It confirms the type of service the user
    would like to monitor, and then calls the appropriate corresponding function.
    """
    command_completer: WordCompleter = WordCompleter(['HTTP', 'HTTPS', 'ICMP', 'DNS',
                                                      'NTP', 'TCP', 'UDP', 'CANCEL'], ignore_case=True)
    current_session: PromptSession = PromptSession(completer=command_completer)
    valid_choices = {"HTTP": new_http, "HTTPS": new_https, "ICMP": new_icmp, "DNS": new_dns, "NTP": new_ntp,
                     "TCP": new_tcp, "UDP": new_udp, "CANCEL": cancel}
    user_service_choice = None
    while user_service_choice is None:
        print("Choose a service from HTTP, HTTPS, ICMP, DNS, NTP, TCP, UDP, or type cancel to go back to main loop")
        user_service_choice = current_session.prompt("Enter choice: ")
        if user_service_choice.upper() not in valid_choices:
            print("Invalid choice")
            user_service_choice = None
    return valid_choices[user_service_choice.upper()](monitor_list)


def new_server(monitor_list, server_list):
    """
    This function is called if user enters 'create' in the main loop. It confirms the type of server the user
    would like to create, and then calls the appropriate corresponding function.
    """
    command_completer: WordCompleter = WordCompleter(['TCP', 'UDP', 'CANCEL'], ignore_case=True)
    current_session: PromptSession = PromptSession(completer=command_completer)
    valid_choices = {"TCP": new_tcp_server, "UDP": new_udp_server, "CANCEL": cancel}
    user_server_choice = None
    while user_server_choice is None:
        print("Choose to create and monitor a TCP or UDP server, or type cancel to go back to main loop")
        user_server_choice = current_session.prompt("Enter choice (choose TCP for echo server monitoring): ")
        if user_server_choice.upper() not in valid_choices:
            print("Invalid choice")
            user_server_choice = None
    return valid_choices[user_server_choice.upper()](monitor_list, server_list)


def echo_message():
    """This function creates an echo message that will be echoed back and forth by the echo server and client"""
    pre_prompt = "Create a message that will be echoed back and forth by the echo server and client"
    command_completer: WordCompleter = WordCompleter(['CANCEL'], ignore_case=True)
    current_session: PromptSession = PromptSession(completer=command_completer)
    echo = None
    while echo is None:
        print(pre_prompt)
        echo = current_session.prompt(f"Enter your choice of echo message: ")
        if echo.lower() == "cancel":
            return cancel(pre_prompt)
        confirmation = confirm_yes_no(f"{echo} as your echo message?")
        if confirmation:
            return echo
        else:
            echo = None


def server_name():
    """This function creates a custom name to be used by the user created server"""
    pre_prompt = "Create a custom name for your server (e.g 'MyServer', 'TestServer' etc."
    command_completer: WordCompleter = WordCompleter(['CANCEL'], ignore_case=True)
    current_session: PromptSession = PromptSession(completer=command_completer)
    name = None
    while name is None:
        print(pre_prompt)
        name = current_session.prompt(f"Enter your choice of server name: ")
        if name.lower() == "cancel":
            return cancel(pre_prompt)
        confirmation = confirm_yes_no(f"{name} as your server name?")
        if confirmation:
            return name
        else:
            name = None


def delete_server(monitor_list, server_list):
    """This function ends the running of the current existing server, and then deletes it."""
    name = server_list[0].get_name()
    local = "127.0.0.1"
    port = server_list[0].get_port()
    print("This application currently only supports the hosting of one server at a time")
    print("To continue making a new server, you must first remove your current server, and its corresponding client")
    confirmation = confirm_yes_no(f"that you would like to delete your server {name} at {local} at port {port} "
                                  f"(This app currently only can host one server at a time)")
    if not confirmation:
        return False
    target_client = None
    count = 0
    for service in monitor_list:
        if service.get_service() == "TCP" or service.get_service() == "UDP":
            if service.get_message():
                target_client = monitor_list.pop(count)
                break
        count += 1
    if target_client:
        print(f"Ending monitoring of {target_client.get_name()}")
        target_client.deactivate()
        del target_client

    server = server_list.pop()
    print(f"Closing connection to {name}")
    server.deactivate()
    del server
    return True


def new_tcp_server(monitor_list, server_list):
    """
    Create a new tcp server with user inputted name, and port number. Also create a corresponding client that
    will monitor the created server.
    """
    if len(server_list) == 1:
        confirm_del = delete_server(monitor_list, server_list)
        if not confirm_del:
            return False
    server_address = '127.0.0.1'
    tcp_server_name = server_name()
    if not tcp_server_name:
        return False
    tcp_server_port = get_port_number(server_address + " (Local host)", True)
    if not tcp_server_port:
        return False
    user_message = echo_message()
    if not user_message:
        return False
    tcp_time_interval = get_monitoring_time(server_address)
    if not tcp_time_interval:
        return False
    server_list.append(TCPServer(tcp_server_name, tcp_server_port))
    server_list[-1].activate()
    monitor_list.append(MonitorTCP(server_address, tcp_time_interval, tcp_server_port))
    monitor_list[-1].switch_to_client()
    monitor_list[-1].set_message(user_message)
    monitor_list[-1].activate()
    return False


def new_udp_server(monitor_list, server_list):
    """
    Create a new udp server with user inputted name, and port number. Also create a corresponding client that
    will monitor the created server.
    """
    if len(server_list) == 1:
        confirm_del = delete_server(monitor_list, server_list)
        if not confirm_del:
            return False
    server_address = '127.0.0.1'
    udp_server_name = server_name()
    if not udp_server_name:
        return False
    udp_server_port = get_port_number(server_address + " (Local host)", True)
    if not udp_server_port:
        return False
    user_message = echo_message()
    if not user_message:
        return False
    udp_time_interval = get_monitoring_time(server_address)
    if not udp_time_interval:
        return False
    server_list.append(UDPServer(udp_server_name, udp_server_port))
    server_list[-1].activate()
    monitor_list.append(MonitorUDP(server_address, udp_time_interval, udp_server_port))
    monitor_list[-1].switch_to_client()
    monitor_list[-1].set_message(user_message)
    monitor_list[-1].activate()
    return False


def cancel(monitor_list):
    """This function is used to allow users to stop current input at any time, and go back to the main loop"""
    print("Cancelling. Going back to main loop...")
    return False


def get_url(completer):
    """Get a url for creating MonitorConfigurations."""
    command_completer: WordCompleter = WordCompleter([completer, "cancel"], ignore_case=True)
    current_session: PromptSession = PromptSession(completer=command_completer)
    pre_prompt = f"Enter the url of the service you would like to monitor. Must start with {completer}.\n " \
                 f"Or, type cancel to go back to the main loop."
    completer_length = len(completer)
    url = None
    while url is None:
        print(pre_prompt)
        url = current_session.prompt("Enter url: ")
        if url.lower() == "cancel":
            return cancel(completer)
        if url[:completer_length * 2] == completer + completer:
            url = url[completer_length:]
        if url[:completer_length] == completer and len(url) > completer_length:
            confirmation = confirm_yes_no("your url choice of " + url)
            if confirmation:
                return url
        print("Please try again")
        url = None


def get_monitoring_time(name):
    """Get the monitoring interval for MonitoringConfigurations"""
    command_completer: WordCompleter = WordCompleter(["cancel"], ignore_case=True)
    current_session: PromptSession = PromptSession(completer=command_completer)
    pre_prompt = f"Enter an integer that will represent a time interval (in seconds) to monitor {name} " \
                 f"Or type cancel to go back to the main loop"
    monitoring_interval = None
    while monitoring_interval is None:
        print(pre_prompt)
        monitoring_interval = current_session.prompt("WARNING! Integer size affects time it takes to shut down "
                                                     "application!\nEnter an integer (time interval for monitoring "
                                                     "service in seconds): ")
        if monitoring_interval.lower() == "cancel":
            return cancel(name)
        try:
            monitoring_interval = int(monitoring_interval)
            confirmation = confirm_yes_no("your choice of " + str(monitoring_interval) + " seconds?")
            if confirmation:
                return monitoring_interval
            else:
                monitoring_interval = None
        except:
            monitoring_interval = None


def new_http(monitor_list):
    """
    Create a MonitorHTTP object with the required user inputted information, add it to monitoring list, and
    activate monitoring
    """
    http_url = get_url("http://")
    if not http_url:
        return False
    http_time_interval = get_monitoring_time(http_url)
    if not http_time_interval:
        return False
    monitor_list.append(MonitorHTTP(http_url, http_time_interval))
    monitor_list[-1].activate()
    return False


def new_https(monitor_list):
    """
    Create a MonitorHTTPS object with the required user inputted information, add it to monitoring list, and
    activate monitoring
    """
    https_url = get_url("https://")
    if not https_url:
        return False
    https_time_interval = get_monitoring_time(https_url)
    if not https_time_interval:
        return False
    monitor_list.append(MonitorHTTPS(https_url, https_time_interval))
    monitor_list[-1].activate()
    return False


def get_name_or_ip(name_type):
    """Get a hostname or ip address for use in creating MonitoringConfiguration objects"""
    command_completer: WordCompleter = WordCompleter(["cancel"], ignore_case=True)
    current_session: PromptSession = PromptSession(completer=command_completer)
    pre_prompt = f"Enter a {name_type}, or type cancel to go back to the main loop"
    name_or_ip = None
    while name_or_ip is None:
        print(pre_prompt)
        name_or_ip = current_session.prompt(f"Enter your choice of {name_type}, or cancel: ")
        if name_or_ip.lower() == "cancel":
            return cancel(pre_prompt)
        confirmation = confirm_yes_no("your choice of " + name_or_ip)
        if confirmation:
            return name_or_ip
        else:
            name_or_ip = None


def new_icmp(monitor_list):
    """
    Create a MonitorICMP object with the required user inputted information, add it to monitoring list, and
    activate monitoring
    """
    icmp_name = get_name_or_ip("hostname or ip address")
    if not icmp_name:
        return False
    icmp_time_interval = get_monitoring_time(icmp_name)
    if not icmp_time_interval:
        return False
    monitor_list.append(MonitorICMP(icmp_name, icmp_time_interval))
    monitor_list[-1].activate()
    return False


def get_record_type():
    """Get a DNS record type for use in creating MonitorDNS objects"""
    command_completer: WordCompleter = WordCompleter(["cancel", "A", "AAAA", "MX", "CNAME"], ignore_case=True)
    current_session: PromptSession = PromptSession(completer=command_completer)
    pre_prompt = "Enter the type of DNS record, or type cancel to go back to the main loop"
    dns_record = None
    while dns_record is None:
        print(pre_prompt)
        dns_record = current_session.prompt("Enter the type of DNS record, or cancel: ")
        if dns_record.lower() == "cancel":
            return cancel(pre_prompt)
        confirmation = confirm_yes_no("your choice of " + dns_record)
        if confirmation:
            return dns_record
        else:
            dns_record = None


def new_dns(monitor_list):
    """
    Create a MonitorDNS object with the required user inputted information, add it to monitoring list, and
    activate monitoring
    """
    dns_server = get_name_or_ip("DNS server")
    if not dns_server:
        return False
    dns_query = get_name_or_ip("DNS query")
    if not dns_query:
        return False
    dns_record_type = get_record_type()
    if not dns_record_type:
        return False
    dns_time_interval = get_monitoring_time(dns_server)
    if not dns_time_interval:
        return False
    monitor_list.append(MonitorDNS(dns_server, dns_time_interval, dns_query, dns_record_type))
    monitor_list[-1].activate()
    return False


def new_ntp(monitor_list):
    """
    Create a MonitorNTP object with the required user inputted information, add it to monitoring list, and
    activate monitoring
    """
    ntp_name = get_name_or_ip("hostname or ip address")
    if not ntp_name:
        return False
    ntp_time_interval = get_monitoring_time(ntp_name)
    if not ntp_time_interval:
        return False
    monitor_list.append(MonitorNTP(ntp_name, ntp_time_interval))
    monitor_list[-1].activate()
    return False


def get_port_number(name, custom_server):
    """Get a port numbers for use in creating MonitorTCP or MonitorUDP objects"""
    command_completer: WordCompleter = WordCompleter(["cancel"], ignore_case=True)
    current_session: PromptSession = PromptSession(completer=command_completer)
    pre_prompt = f"Enter a port number to connect to at {name}"
    port_number = None
    if not custom_server:
        while port_number is None:
            print(pre_prompt)
            port_number = current_session.prompt("Enter a port number: ")
            if port_number.lower() == "cancel":
                return cancel(name)
            try:
                port_number = int(port_number)
                confirmation = confirm_yes_no("your port number choice of " + str(port_number))
                if confirmation:
                    return port_number
                else:
                    port_number = None
            except:
                port_number = None
    else:
        while port_number is None:
            print(pre_prompt)
            port_number = current_session.prompt("Enter a valid port number (1025 - 65534): ")
            if port_number.lower() == "cancel":
                return cancel(name)
            try:
                port_number = int(port_number)
                if 1024 < port_number < 65535:
                    confirmation = confirm_yes_no("your port number choice of " + str(port_number))
                    if confirmation:
                        return port_number
                else:
                    port_number = None
            except:
                port_number = None


def new_tcp(monitor_list):
    """
    Create a MonitorTCP object with the required user inputted information, add it to monitoring list, and
    activate monitoring
    """
    tcp_name = get_name_or_ip("hostname or ip address")
    if not tcp_name:
        return False
    tcp_port = get_port_number(tcp_name, False)
    if not tcp_port:
        return False
    tcp_time_interval = get_monitoring_time(tcp_name)
    if not tcp_time_interval:
        return False
    monitor_list.append(MonitorTCP(tcp_name, tcp_time_interval, tcp_port))
    monitor_list[-1].activate()
    return False


def new_udp(monitor_list):
    """
    Create a MonitorUDP object with the required user inputted information, add it to monitoring list, and
    activate monitoring
    """
    udp_name = get_name_or_ip("hostname or ip address")
    if not udp_name:
        return False
    udp_port = get_port_number(udp_name, False)
    if not udp_port:
        return False
    udp_time_interval = get_monitoring_time(udp_name)
    if not udp_time_interval:
        return False
    monitor_list.append(MonitorUDP(udp_name, udp_time_interval, udp_port))
    monitor_list[-1].activate()
    return False


if __name__ == "__main__":
    main()

