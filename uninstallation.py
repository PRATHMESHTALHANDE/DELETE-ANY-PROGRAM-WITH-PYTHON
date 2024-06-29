import subprocess
import sys
import os
import ctypes
import winreg
import pyautogui
import time

def is_admin():
    try:
        return os.getuid() == 0
    except AttributeError:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

def run_as_admin():
    if not is_admin():
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([script] + sys.argv[1:])
        shell32 = ctypes.windll.shell32
        ret = shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        if int(ret) <= 32:
            raise OSError(f"Error: {ret}")
        sys.exit(0)

def get_installed_programs():
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

def find_uninstaller(program_name):
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

def run_uninstall_command(command):
    try:
        result = subprocess.run(command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print("Successfully uninstalled the program.")
        else:
            print(f"Failed to uninstall the program. Error: {result.stderr.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to uninstall the program. Error: {e}")

def open_programs_and_features(program_name):
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

def uninstall_application(application_name):
    uninstaller_cmd = find_uninstaller(application_name)
    if uninstaller_cmd:
        print(f"Uninstaller command found: {uninstaller_cmd}")
        run_uninstall_command(uninstaller_cmd)
    else:
        print(f"Uninstall script for {application_name} is not available.")
        print(f"Opening Programs and Features for manual uninstallation...")
        open_programs_and_features(application_name)

def filter_programs(search_text, programs):
    filtered_programs = [(i, program) for i, program in enumerate(programs, 1) if search_text.lower() in program[0].lower()]
    return filtered_programs

def main():
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
