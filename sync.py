import filecmp
import logging
import os
import shutil
import sys
import time


class SyncManager:

    def __init__(self):
        # List of actions to be performed with files
        self.ACTIONS = ["add", "copy", "delete"]

        self.source_path = ""
        self.replica_path = ""
        self.interval = 0
        self.log_path = ""

        self.get_data()

        self.logger = self.log_setup()

    # Synchronizes folders
    def sync(self):
        self.compare(source=self.source_path, replica=self.replica_path)
        time.sleep(self.interval)

    # Recursive function, which compares content of the source and replica folders (each hierarchy level at a time)
    def compare(self, source, replica):
        comparison = filecmp.dircmp(a=source, b=replica)

        # Compares content of common subfolders
        if comparison.common_dirs:
            for item in comparison.common_dirs:
                self.compare(source=os.path.join(source, os.path.basename(item)),
                             replica=os.path.join(replica, os.path.basename(item)))

        # Copies brandnew files and/or subdirectories from the source to replica folder
        if comparison.left_only:
            self.copy(to_copy=comparison.left_only, source=source, replica=replica, action=self.ACTIONS[0])

        # Deletes files/or subdirectories from the replica folder
        if comparison.right_only:
            self.remove(to_remove=comparison.right_only, path=replica)

        # Syncs modified files, that exist in both folders
        if comparison.diff_files:
            to_copy = []

            for item in comparison.diff_files:
                # Gets time of a last modifications in files
                source_mtime = os.stat(os.path.join(source, item)).st_mtime
                replica_mtime = os.stat(os.path.join(replica, item)).st_mtime

                # If the source file is newer, copy it to the replica folder
                if source_mtime > replica_mtime:
                    to_copy.append(item)
                    self.copy(to_copy=to_copy, source=source, replica=replica, action=self.ACTIONS[1])

    # Adds new files and updates existing ones in the Replica folder
    def copy(self, to_copy, source, replica, action):
        for item in to_copy:
            path_to_check = os.path.join(source, os.path.basename(item))
            path_to_store = os.path.join(replica, os.path.basename(item))

            # Checks if an item is a folder or a file
            if os.path.isdir(path_to_check):
                shutil.copytree(path_to_check, path_to_store)
                self.log(path=path_to_store, is_directory=True, action=action)
            else:
                shutil.copy2(path_to_check, path_to_store)
                self.log(path=path_to_store, is_directory=False, action=action)

    # Gets initial data from the command line
    def get_data(self):
        # Arguments provided by user using command line arguments
        arguments = sys.argv

        if len(arguments) == 5:
            for path in [arguments[1], arguments[2]]:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"Path '{path}' provided to the program does not exist.")

            self.source_path = arguments[1]
            self.replica_path = arguments[2]
            self.interval = float(arguments[3])
            self.log_path = arguments[4]

        else:
            raise TypeError(
                "Required arguments should be passed in the following order:\n" \
                "1. Full path of the source folder;\n" \
                "2. Full path of the replica folder;\n" \
                "3. Synchronization interval, s;\n" \
                "4. Full path of the .log file."
            )

    # Records data about any changes in directories
    def log(self, path, is_directory, action):
        log_message = ""
        # Separate an item name ...
        item_name = os.path.basename(path)
        # ... and its folder path
        target_path = os.path.dirname(path)

        # Pick a message
        if is_directory:
            if action == self.ACTIONS[0]:
                log_message = f"Directory {item_name} was successfully added (target path: {target_path})."
            elif action == self.ACTIONS[1]:
                log_message = f"Directory {item_name} was successfully copied (target path: {target_path})."
            elif action == self.ACTIONS[2]:
                log_message = f"Directory {item_name} was successfully deleted (target path: {target_path})."
            else:
                print("log(): Unknown option")
        else:
            if action == self.ACTIONS[0]:
                log_message = f"File {item_name} was successfully added (target path: {target_path})."
            elif action == self.ACTIONS[1]:
                log_message = f"File {item_name} was successfully copied (target path: {target_path})."
            elif action == self.ACTIONS[2]:
                log_message = f"File {item_name} was successfully deleted (target path: {target_path})."
            else:
                print("log(): Unknown option")

        # Log the message
        self.logger.info(log_message)

    # Initial setup of a logger
    def log_setup(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s  ::  %(message)s")

        # If the folder does not exist, create it
        if not os.path.exists(os.path.dirname(self.log_path)):
            os.mkdir(os.path.dirname(self.log_path))

        # To log to a file
        file_handler = logging.FileHandler(filename=self.log_path, mode='a', encoding="utf-8")
        file_handler.setFormatter(formatter)
        # To log to a console
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

        return logger

    # Just removing....
    def remove(self, to_remove, path):
        for item in to_remove:
            path_to_remove = os.path.join(path, os.path.basename(item))

            # Checks if an item is a folder or a file
            if os.path.isdir(path_to_remove):
                shutil.rmtree(path_to_remove)
                self.log(path=path_to_remove, is_directory=True, action=self.ACTIONS[2])
            else:
                os.remove(path_to_remove)
                self.log(path=path_to_remove, is_directory=False, action=self.ACTIONS[2])
