# DELETE-ANY-PROGRAM-WITH-PYTHON
Hi guys, I have created python script to uninstall any program. This code provides a complete program for managing installed applications on a Windows system, including listing, searching, and uninstalling programs.

import subprocess
import sys
import os
import ctypes
import winreg
import pyautogui
import time

# Check if the script is running with administrative privileges
def is_admin():
    """
    Checks if the script is running with administrative privileges.

    Returns:
        bool: True if the script is running as an administrator, False otherwise.
    """
    try:
        return os.getuid() == 0  # Unix-based systems
    except AttributeError:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0  # Windows systems

# Attempt to re-run the script with administrative privileges if not already running as an administrator
def run_as_admin():
    """
    Attempts to re-run the script with administrative privileges if it is not already running as an administrator.
    """
    if not is_admin():
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([script] + sys.argv[1:])
        shell32 = ctypes.windll.shell32
        ret = shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        if int(ret) <= 32:
            raise OSError(f"Error: {ret}")
        sys.exit(0)

# Retrieve a list of installed programs on the system
def get_installed_programs():
    """
    Retrieves a list of installed programs on the system.

    Returns:
        list of tuple: A list of tuples containing the display name and registry path of each installed program.
    """
    programs = []

    def enum_key(key, path):
        try:
            with winreg.OpenKey(key, path) as subkey:
                for i in range(winreg.QueryInfoKey(subkey)[0]):
                    yield winreg.EnumKey(subkey, i)
        except WindowsError:
            pass

    def get_value(key, subkey, value):
        try:
            with winreg.OpenKey(key, subkey) as sk:
                return winreg.QueryValueEx(sk, value)[0]
        except WindowsError:
            return None

    uninstall_keys = [
        r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
        r'SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
    ]

    for uninstall_key in uninstall_keys:
        for subkey in enum_key(winreg.HKEY_LOCAL_MACHINE, uninstall_key):
            display_name = get_value(winreg.HKEY_LOCAL_MACHINE, f"{uninstall_key}\\{subkey}", "DisplayName")
            if display_name:
                programs.append((display_name, f"{uninstall_key}\\{subkey}"))

    return programs

# Find the uninstallation command for a given program
def find_uninstaller(program_name):
    """
    Finds the uninstallation command for a given program.

    Args:
        program_name (str): The name of the program to find the uninstaller for.

    Returns:
        str: The uninstallation command if found, None otherwise.
    """
    uninstaller_cmd = None

    def enum_key(key, path):
        try:
            with winreg.OpenKey(key, path) as subkey:
                for i in range(winreg.QueryInfoKey(subkey)[0]):
                    yield winreg.EnumKey(subkey, i)
        except WindowsError:
            pass

    def get_value(key, subkey, value):
        try:
            with winreg.OpenKey(key, subkey) as sk:
                return winreg.QueryValueEx(sk, value)[0]
        except WindowsError:
            return None

    uninstall_keys = [
        r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
        r'SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
    ]

    for uninstall_key in uninstall_keys:
        for subkey in enum_key(winreg.HKEY_LOCAL_MACHINE, uninstall_key):
            display_name = get_value(winreg.HKEY_LOCAL_MACHINE, f"{uninstall_key}\\{subkey}", "DisplayName")
            uninstall_string = get_value(winreg.HKEY_LOCAL_MACHINE, f"{uninstall_key}\\{subkey}", "UninstallString")
            if display_name and program_name.lower() in display_name.lower():
                uninstaller_cmd = uninstall_string
                break
        if uninstaller_cmd:
            break

    return uninstaller_cmd

# Execute the uninstallation command for a given program
def run_uninstall_command(command):
    """
    Executes the uninstallation command for a given program.

    Args:
        command (str): The uninstallation command to run.
    """
    try:
        result = subprocess.run(command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print("Successfully uninstalled the program.")
        else:
            print(f"Failed to uninstall the program. Error: {result.stderr.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to uninstall the program. Error: {e}")

# Open the Programs and Features control panel and search for the specified program
def open_programs_and_features(program_name):
    """
    Opens the Programs and Features control panel and searches for the specified program.

    Args:
        program_name (str): The name of the program to search for.
    """
    try:
        SW_HIDE = 0
        STARTF_USESHOWWINDOW = 1
        STARTUPINFO = subprocess.STARTUPINFO()
        STARTUPINFO.dwFlags |= STARTF_USESHOWWINDOW
        STARTUPINFO.wShowWindow = SW_HIDE

        process = subprocess.Popen(['control', 'appwiz.cpl'], startupinfo=STARTUPINFO)
        time.sleep(2)  # Wait for the window to open

        # Use pyautogui to type the program name and simulate key presses to find it
        pyautogui.write(program_name)
        pyautogui.press('enter')

        # Hide the Control Panel window
        ctypes.windll.user32.ShowWindow(process.pid, 0)
    except Exception as e:
        print(f"Failed to open Programs and Features: {e}")

# Attempt to uninstall the specified application
def uninstall_application(application_name):
    """
    Attempts to uninstall the specified application either by finding and running its uninstaller command 
    or by opening the Programs and Features control panel for manual uninstallation.

    Args:
        application_name (str): The name of the application to uninstall.
    """
    uninstaller_cmd = find_uninstaller(application_name)
    if uninstaller_cmd:
        print(f"Uninstaller command found: {uninstaller_cmd}")
        run_uninstall_command(uninstaller_cmd)
    else:
        print(f"Uninstall script for {application_name} is not available.")
        print(f"Opening Programs and Features for manual uninstallation...")
        open_programs_and_features(application_name)

# Filter the list of programs based on the provided search text
def filter_programs(search_text, programs):
    """
    Filters the list of programs based on the provided search text.

    Args:
        search_text (str): The text to search for in the program names.
        programs (list of tuple): The list of installed programs.

    Returns:
        list of tuple: A list of tuples containing the index and program information that match the search text.
    """
    filtered_programs = [(i, program) for i, program in enumerate(programs, 1) if search_text.lower() in program[0].lower()]
    return filtered_programs

# Main function providing a menu for listing, searching, uninstalling, and restarting the script
def main():
    """
    The main function of the script. Provides a menu for the user to list installed programs, 
    uninstall a program, search for a program, restart the script, or exit the script.
    """
    if not is_admin():
        run_as_admin()

    programs = []
    restart_program = True
    
    while restart_program:
        print("\nOptions:")
        print("1. List installed programs")
        print("2. Uninstall a program")
        print("3. Search for a program")
        print("4. Restart the program")
        print("5. Exit")
        
        choice = input("Enter your choice: ").strip()

        if choice == '1':
            programs = get_installed_programs()
            print("Installed programs:")
            for i, (program, _) in enumerate(programs, 1):
                print(f"{i}. {program}")
        elif choice == '2':
            if not programs:
                print("Please list installed programs first (Option 1).")
                continue

            sr_numbers = input("Enter the serial numbers of the programs you want to uninstall (comma-separated): ").strip()
            sr_numbers = [int(x.strip()) for x in sr_numbers.split(',') if x.strip().isdigit()]
            programs_to_uninstall = [programs[i-1][0] for i in sr_numbers if 0 < i <= len(programs)]

            if not programs_to_uninstall:
                print("Invalid serial numbers provided.")
                continue

            print("Programs selected for uninstallation:")
            for program in programs_to_uninstall:
                print(program)

            confirm = input("Do you want to uninstall the selected programs? (yes/no): ").strip().lower()
            if confirm == 'yes':
                for program in programs_to_uninstall:
                    print(f"Uninstalling {program}...")
                    uninstall_application(program)
            else:
                print("Uninstallation canceled.")
        elif choice == '3':
            if not programs:
                print("Please list installed programs first (Option 1).")
                continue

            search_text = input("Enter the name or part of the name of the program to search: ").strip()
            filtered_programs = filter_programs(search_text, programs)

            if not filtered_programs:
                print(f"No programs found matching '{search_text}'.")
            else:
                print("Search results:")
                for i, (index, (program, _)) in enumerate(filtered_programs, 1):
                    print(f"{index}. {program}")
        elif choice == '4':
            print("Restarting the program...")
            restart_program = True
            programs = []  # Reset programs list
        elif choice == '5':
            print("Exiting the program.")
            restart_program = False
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()


The main function is the main loop of the script.
Checks if the script is running as admin and attempts to elevate if not.
Provides a menu with options to list programs, uninstall programs, search for programs, restart, or exit.
Handles user input and executes the corresponding actions.





