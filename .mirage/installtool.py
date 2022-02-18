#!/usr/bin/env python3
import argparse
import datetime
import getpass
import hashlib
import pathlib
import traceback

import paramiko
from scp import SCPClient

__author__ = "Jordan Blackadar <blackadar@photodiagnostic.com>"

BCC_IP = '192.168.6.6'
DCC_IP = '192.168.5.5'
RCC_IP = 'localhost'

BCC_PACK_LIST = [
        'ckct-BaseCC',
        'ckct-bcc_config',
]
DCC_PACK_LIST = [
        'ckct-dasControl',
        'ckct-dcc_config',
        'ckct-DiscCC',
        'ckct-spellmanXRayControl',
]
RCC_PACK_LIST = [
        'ckct-DataHandler',
        'ckct-imaging',
        'ckct-kmod',
        'ckct-logger',
        'ckct-motorControl',
        'ckct-mscp',
        'ckct-rcc_config',
        'ckct-ReconCC',
        'ckct-recorder',
        'ckct-tools',
        'ckct-utils',
        'ckct-utils49172',
]


def splash():
    """
    Shows the logo splash.
    :return: None
    """
    print(
        " ________  ___  __    ________ _________        ___  ________   ________  _________  ________  ___       ___       _______   ________     \n"
        "|\   ____\|\  \|\  \ |\   ____\\\___   ___\     |\  \|\   ___  \|\   ____\|\___   ___\\\   __  \|\  \     |\  \     |\  ___ \ |\   __  \    \n"
        "\ \  \___|\ \  \/  /|\ \  \___\|___ \  \_|     \ \  \ \  \\\ \  \ \  \___|\|___ \  \_\ \  \|\  \ \  \    \ \  \    \ \   __/|\ \  \|\  \   \n"
        " \ \  \    \ \   ___  \ \  \       \ \  \       \ \  \ \  \\\ \  \ \_____  \   \ \  \ \ \   __  \ \  \    \ \  \    \ \  \_|/_\ \   _  _\  \n"
        "  \ \  \____\ \  \\\ \  \ \  \____   \ \  \       \ \  \ \  \\\ \  \|____|\  \   \ \  \ \ \  \ \  \ \  \____\ \  \____\ \  \_|\ \ \  \\\  \| \n"
        "   \ \_______\ \__\\\ \__\ \_______\  \ \__\       \ \__\ \__\\\ \__\____\_\  \   \ \__\ \ \__\ \__\ \_______\ \_______\ \_______\ \__\\\ _\ \n"
        "    \|_______|\|__| \|__|\|_______|   \|__|        \|__|\|__| \|__|\_________\   \|__|  \|__|\|__|\|_______|\|_______|\|_______|\|__|\|__|\n"
        "                                                                 \|_________|                                                            ")


def menu(options: list, title: str = ''):
    """
    Asks a user to choose an item from a list of choices.
    They will be prompted to enter a number which is an index to the array you provide.
    The index will be returned.
    :param options: List of Strings
    :param title: Title of the Menu
    :return: Index of String Selected by User
    """
    assert len(options) > 0, "Zero option menu was requested, which would soft-lock the user."
    print(f"<< {title if title else 'Selection'} >>")
    print("-" * 32)
    for idx, option in enumerate(options):
        print(f" {idx + 1}. {str(option)}")
    print("-" * 32)
    print()
    selection = None
    while not selection:
        inp = input("> ")
        try:
            selection = int(inp) - 1
            assert selection in range(0, len(options))
            return selection
        except (ValueError, TypeError, AssertionError):
            print(f"'{inp}' is not an option. Try again.")
            selection = None


def multi_menu(options: list, title: str = ''):
    """
    Asks a user to choose multiple items from a list of choices.
    They will be prompted to enter comma-separated numbers which are indexes to the array you provide.
    The list of indexes will be returned.
    :param options: List of Strings
    :param title: Title of the Menu
    :return: List of String Indexes Selected by the User
    """
    assert len(options) > 0, "Zero option multi-menu was requested, which would soft-lock the user."
    print(f"<< {title if title else 'Multi-Selection'} >>")
    print("-" * 32)
    for idx, option in enumerate(options):
        print(f" {idx + 1}. {str(option)}")
    print(f" {len(options) + 1}. Select All")
    print("-" * 32)
    print()
    done = False
    indexes = []
    while not done:
        done = True  # Done until proven otherwise
        print("Please enter comma-separated values. (e.g., 1,4)")
        inps = input("> ").split(",")
        for inp in inps:
            inp = inp.strip()
            try:
                selection = int(inp) - 1
                assert selection in range(0, len(options) + 1)
                indexes.append(selection)
            except (ValueError, TypeError, AssertionError):
                print(f"'{inp}' is not an option. Try again.")
                done = False
                indexes = []
                break
        if len(options) in indexes and len(indexes) > 1:
            print("If you'd like to select all, please don't specify any other options.")
            done = False
            indexes = []
    return indexes


def yesno(question: str = ''):
    """
    Asks a user to confirm yes or no.
    Optionally takes the question to ask to one-line it.
    :return: bool response
    """
    while True:
        sel = input(f"{question} [y/N] > ")
        if sel.lower() == 'y':
            return True
        if sel.lower() == 'n':
            return False
        print("Invalid choice. Enter y/Y or n/N.")


def no_running_sw():
    """
    Asks the user to confirm the software is shut down.
    :return: None
    """
    while True:
        sd = yesno("Before we proceed, can you verify that the CKCT software is shut down?")
        if sd:
            print("Great, let's move on then.")
            break
        else:
            print("I can't upgrade software while it's in use. Please send system shutdown and then come back here.")


def find_rpms(recursive=False, path='.', title_match=''):
    """
    Finds all RPMs in the directory specified.
    :param title_match: string to add to glob match before .rpm - e.g. x86_64
    :param recursive: bool Search recursively for RPMs
    :param path: Path to search
    :return: list of Paths
    """
    path = pathlib.Path(path).resolve()
    assert path.exists(), f"Supplied path {path} does not exist!"
    if recursive:
        return sorted(path.rglob(f"{('*' + title_match) if title_match else ''}*.rpm"))
    else:
        return sorted(path.glob(f"{('*' + title_match) if title_match else ''}*.rpm"))


def verbose_rpm_ask(target: str, arch: str):
    """
    Prompts the user to select RPMs, matching architecture name and presenting target.
    :param target: String name of computer being targeted.
    :param arch: String name of architecture, to filter RPM names by.
    :return: List of RPMs to install
    """
    rpms = find_rpms(title_match=arch)
    to_install = None

    while not rpms:
        print(f"I don't see any RPMs. I'm looking for packages for {arch} to put on a {target} computer."
              "I can look again, or you can quit with Ctrl+C to locate them.")
        recursive = yesno("If you'd like to continue - would you like me to look into folders below this one?")
        rpms = find_rpms(recursive=recursive, title_match=arch)

    done = False
    while not done:
        print("I found the following packages available to install. Which would you like me to handle?")
        to_install = multi_menu(rpms, title="Select Packages")
        if len(to_install) < 1:
            print("Not sure what do do without a selection! "
                  "Try again, or you can quit with Ctrl+C to start over.")
            continue
        if len(rpms) in to_install:
            to_install = range(0, len(rpms))
        print(f"Got it! Just to confirm, we're installing {len(to_install)} packages on the {target} computer. "
              f"You'll have another chance to review, but not to modify this selection.")
        done = yesno("Ready to proceed?")

    return [rpms[i] for i in to_install]


def calc_md5(path):
    """
    Find the md5sum of the file at the specified path.
    Loads file in 2^13 byte chunks to avoid high memory usage.
    https://stackoverflow.com/questions/16874598/how-do-i-calculate-the-md5-checksum-of-a-file-in-python
    :param path: path to File
    :return: md5sum as a string
    """
    path = pathlib.Path(path).resolve()
    assert path.exists(), f"md5sum requested for nonexistent path {path}!"

    with open(path, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    return file_hash.hexdigest()


def read_md5_file(path):
    """
    Reads md5 file output from md5tool.sh into a Python dict.
    :param path: path to File
    :return: dict file:md5sum
    """
    path = pathlib.Path(path).resolve()
    assert path.exists(), f"md5sum read requested for nonexistent path {path}!"

    with open(path, "r") as f:
        lines = f.readlines()

    hashes = {}
    for line in lines:
        if line[0] != '|' or line[-2] != '|':  # Special markers for md5tool files
            continue  # Skip this line
        row = line.replace('|', '').strip().split(' ')
        hashes[row[2]] = row[0]

    return hashes


def verify_md5s(rpms: list, md5_file):
    """
    Reads the md5 file and generates md5sums for all rpms in the list.
    Prints out mismatches for any present RPMs.
    :param rpms: List of RPM paths to verify
    :param md5_file: path to md5sum file produced by md5tool.sh
    :return: bool all verified
    """
    try:
        hashes = read_md5_file(md5_file)
    except AssertionError as e:
        print(f"I couldn't find the file {md5_file} on disk. Please download that file and try again!")
        return False
    print(f"Ok! I found {len(hashes)} md5sums in the build output. Let's see if they match.")
    passed = True

    for rpm in rpms:
        rpm = rpm.name
        if rpm not in hashes.keys():
            print(f"- [X] {rpm} was not in md5.txt. I can't verify that hash.")
            passed = False
            continue
        md5 = calc_md5(rpm)
        if md5 != hashes[rpm]:
            print(f"- [X] {rpm} failed the check! Expected {hashes[rpm]} but I found the hash to be {md5}.")
            passed = False
        else:
            print(f"- {rpm} matches my hash calculation.")

    return passed


def pack_list(found_rpms: list):
    """
    Checks that all expected RPMs are present, then returns lists to install for each computer.
    See below for the order of those lists!
    :param found_rpms: list of RPMs found to install
    :return: Tuple (rcc_pack_list, dcc_pack_list, bcc_pack_list)
    """
    rcc_pack_list = []
    dcc_pack_list = []
    bcc_pack_list = []

    all_ok = True

    def find_partial(full, partial_list):
        result = list(filter(lambda x: full.startswith(x), partial_list))
        return len(result) > 0

    for rpm in found_rpms:
        name = rpm.name
        if find_partial(name, RCC_PACK_LIST):
            print(f"{name} is assigned to RCC.")
            rcc_pack_list.append(rpm)
        elif find_partial(name, DCC_PACK_LIST):
            print(f"{name} is assigned to DCC.")
            dcc_pack_list.append(rpm)
        elif find_partial(name, BCC_PACK_LIST):
            print(f"{name} is assigned to BCC.")
            bcc_pack_list.append(rpm)
        else:
            all_ok = False
            print(f"I'm not sure where {name} should go. We can proceed if this package should be ignored.")

    if len(rcc_pack_list) != len(RCC_PACK_LIST):
        all_ok = False
        print(f"Something seems wrong with the RCC packages. I found {len(rcc_pack_list)} "
              f"but was expecting {len(RCC_PACK_LIST)}.")

    if len(dcc_pack_list) != len(DCC_PACK_LIST):
        all_ok = False
        print(f"Something seems wrong with the DCC packages. I found {len(dcc_pack_list)} "
              f"but was expecting {len(DCC_PACK_LIST)}.")

    if len(bcc_pack_list) != len(BCC_PACK_LIST):
        all_ok = False
        print(f"Something seems wrong with the BCC packages. I found {len(bcc_pack_list)} "
              f"but was expecting {len(BCC_PACK_LIST)}.")

    if not all_ok:
        cont = yesno("Should we continue anyways, even with the above issue?")
        if not cont:
            return None

    return rcc_pack_list, dcc_pack_list, bcc_pack_list


def auth_prompt(remote_shortname: str):
    """
    :param remote_shortname: str Name to prompt auth for.
    :return: tuple (username, password)  ** Sensitive!! **
    """
    print(f"To continue, I'll need authentication details for {remote_shortname}.")
    print("Don't worry - I won't store these after the script is complete.")
    user = input("Username: ")
    password = getpass.getpass("Password: ")
    return user, password


def remote_connect(remote_ip, remote_username, remote_password):
    """
    Establishes ssh and scp connection.
    :param remote_ip: IP of the remote.
    :param remote_username: Username of the remote.
    :param remote_password: Password of the remote.
    :return: tuple (client, scpclient)
      """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=remote_ip, username=remote_username, password=remote_password, timeout=10)
    scp = SCPClient(client.get_transport())
    return client, scp


def remote_privileged_command(ssh, command, remote_password):
    """
    Executes a command with sudo over established SSH connection.
    :param ssh: Remote connection object from remote_connect
    :param command: Command to execute (WITHOUT sudo)
    :param remote_password: Password of the remote.
    :return: bool Exit Code was 0
    """
    command = "sudo -S -p '' %s" % command
    print(f"Running SSH command '{command}'.")

    stdin, stdout, stderr = ssh.exec_command(command=command)
    stdin.write(remote_password + "\n")
    stdin.flush()

    exitcode = stdout.channel.recv_exit_status()

    print(f"  - Output: {stdout.readlines()}")
    print(f"  - Error Stream: {stderr.readlines()}")
    print(f"  - Exit Code: {exitcode}")

    return exitcode == 0


def remote_command(ssh, command):
    """
    Executes a command over established SSH connection.
    :param ssh: Remote connection object from remote_connect
    :param command: Command to execute.
    :return: bool Exit Code was 0
    """
    print(f"Running SSH command '{command}'.")

    stdin, stdout, stderr = ssh.exec_command(command=command)

    exitcode = stdout.channel.recv_exit_status()

    print(f"  - Output: {stdout.readlines()}")
    print(f"  - Error Stream: {stderr.readlines()}")
    print(f"  - Exit Code: {exitcode}")

    return exitcode == 0


def scp_files(scp, local_files, remote_path):
    """
    Uses SCP to copy a file to a remote destination.
    :param scp: SCP Client object from remote_connect
    :param local_files: List of paths to files to upload
    :param remote_path: str Path to place file remotely
    :return: None
    """
    print(f"Sending files to {scp}: {local_files}")
    try:
        scp.put(local_files, remote_path, preserve_times=True)
        print("Sent files successfully.")
        return True
    except Exception as e:
        print(f"Error sending files: {e}")
        return False


def yum_install_remote(ssh, path, remote_password):
    """
    Install package on remote machine.
    :param ssh: Remote connection object from remote_connect
    :param path: Remote path to package
    :param remote_password: Remote account password for sudo
    :return: bool Successful
    """
    command = f"yum -y install {path}"
    return remote_privileged_command(ssh, command, remote_password)


def install_remote(rpms: list, remote_ip: str, remote_username: str, remote_password: str):
    """
    Confirms the pack list then installs the RPMs remotely.
    :param remote_password: str Account Password
    :param remote_username: str Account Username (with sudo privilege)
    :param remote_ip: IP address to install at.
    :param rpms: list of pathlib.Paths to the RPMs
    :return: None
    """

    def _check_fail(res: bool):
        if not res:
            print("That didn't work. You may have a partial installation - "
                  "please start from scratch or contact service.")
            return False

    ssh, scp = remote_connect(remote_ip, remote_username, remote_password)
    upload_dir = f"installtool-{datetime.date.today().strftime('%Y%m%d')}"

    print(f"Uploading {len(rpms)} files to {upload_dir}...")
    _check_fail(remote_command(ssh, f'mkdir -p {upload_dir}'))
    _check_fail(scp_files(scp, rpms, upload_dir))

    remotes = [f"{upload_dir}/{x.name}" for x in rpms]
    for remote in remotes:
        print(f"Installing {remote}...")
        _check_fail(yum_install_remote(ssh, remote, remote_password))

    print("Great, install complete! Your deployment is finished.")
    return True


def main():
    splash()
    while True:
        try:
            chosen = False
            choice = None
            ops = ["Install Recon Packages",
                   "Install DCC Packages",
                   "Install BCC Packages",
                   "Validate md5 Hashes from File",
                   "Deploy a Full Software Release",
                   "Exit"]

            while not chosen:
                choice = menu(ops, title='Select Operation')
                chosen = yesno(f"Got it, you'd like to {ops[choice].lower()}, is that right?")
                if not chosen:
                    print("Ok. What would you like to do?")

            print(f"Alright! Setting up to {ops[choice].lower()}...")

            if choice == 0:  # Recon Install
                to_install = verbose_rpm_ask("Recon", "x86_64")
                no_running_sw()
                user, pw = auth_prompt("RCC")
                install_remote(to_install, RCC_IP, user, pw)
            elif choice == 1:  # DCC Install
                to_install = verbose_rpm_ask("DCC", "armv7l")
                no_running_sw()
                user, pw = auth_prompt("DCC")
                install_remote(to_install, DCC_IP, user, pw)
            elif choice == 2:  # BCC Install
                to_install = verbose_rpm_ask("BCC", "armv7l")
                no_running_sw()
                user, pw = auth_prompt("BCC")
                install_remote(to_install, BCC_IP, user, pw)
            elif choice == 3:  # md5 Verify
                rpms = find_rpms()
                md5file = pathlib.Path('md5.txt')
                verify_md5s(rpms, md5file)
            elif choice == 4:  # Full Deployment
                rpms = find_rpms()
                md5file = pathlib.Path('md5.txt')
                print(f"First, I'll verify the md5sums of the packages against {md5file}.")
                passed = verify_md5s(rpms, md5file)
                if not passed:
                    print("Please re-download the software or ask a developer to fix the release if this "
                          "happens with multiple attempts.")
                    continue
                result = pack_list(rpms)
                if result is None:
                    print("Please download the missing RPMs or ask a software developer to fix the release if this "
                          "happens with multiple attempts.")
                    continue
                no_running_sw()
                rcc, dcc, bcc = result
                print("Great, everything is ready to go. Before we begin, let's make sure the pack list looks good:")
                print(f"Recon: {[x.name for x in rcc]}")
                print(f"DCC: {[x.name for x in dcc]}")
                print(f"BCC: {[x.name for x in bcc]}")
                good = yesno("Ready to deploy these?")
                if good:
                    print("First up, Recon.")
                    user, pw = auth_prompt("RCC")
                    install_remote(rcc, RCC_IP, user, pw)
                    print("Ok, next up is the Disk computer.")
                    user, pw = auth_prompt("DCC")
                    install_remote(dcc, DCC_IP, user, pw)
                    print("Finally, the Base computer.")
                    user, pw = auth_prompt("BCC")
                    install_remote(bcc, BCC_IP, user, pw)
                    print("And that's everything! Your release deployment is all set.")
                else:
                    print("Ok, no problem. Try again when you have everything in place.")
            elif choice == 5:  # Exit
                print(f"Have a great day!")
                exit(0)
            print("Looks like that operation has ended. I'll bring you back to the main menu.\n")
        except Exception:
            print(f"I had some trouble doing that. Please send an e-mail to {__author__} with the following: ")
            print(f"{traceback.format_exc()}\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="CKCT Software Installation Tool")
    args = parser.parse_args()
    main()
