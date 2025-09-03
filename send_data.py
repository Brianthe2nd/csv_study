import paramiko
from scp import SCPClient
import os
import shutil
import zipfile
from datetime import datetime
import uuid


def send_zipped_file(host="13.49.80.166", port=22, username="ec2-user", key_file="my_c71.pem", local_zip="archive.rar"):
    """
    Sends a zipped file to a Linux server via SSH/SCP and saves it in ~/archives.

    :param host: Server IP or hostname
    :param port: SSH port (usually 22)
    :param username: SSH username
    :param key_file: Path to private SSH key file
    :param local_zip: Path to the local .zip file
    """
    try:
        # Load private key
        key = paramiko.RSAKey.from_private_key_file(key_file)

        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host,  username=username, pkey=key)


        # Ensure "archives" folder exists in home directory
        ssh.exec_command("mkdir -p ~/archives")

        # Destination path
        remote_path = f"/home/{username}/archives/{local_zip.split('/')[-1]}"

        # Use SCP to transfer file
        with SCPClient(ssh.get_transport()) as scp:
            scp.put(local_zip, remote_path)

        print(f"✅ File '{local_zip}' uploaded to {host}:{remote_path}")

        ssh.close()

    except Exception as e:
        print(f"❌ Error: {e}")


# send_zipped_file(
#     host="13.49.18.152",
#     port=22,
#     username="admin",
#     key_file="C://users/Brayo/Downloads/my_c71.pem",
#     local_zip="names.rar"
# )



def collect_and_zip_files():
    """
    Collect all .txt, .csv, and .json files from the script's directory,
    copy them into a single new folder, and zip that folder.
    """
    # Script directory (absolute path)
    cwd = os.path.dirname(os.path.abspath(__file__))

    # Create unique folder name
    unique_id = uuid.uuid4().hex[:6]  # short random ID
    folder_name = f"collected_files_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{unique_id}"
    folder_path = os.path.join(cwd, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    # File extensions we care about
    extensions = (".txt", ".csv", ".json")

    # Copy matching files into new folder (flat, no subfolders)
    for file in os.listdir(cwd):
        file_path = os.path.join(cwd, file)  # absolute path
        if file.endswith(extensions) and os.path.isfile(file_path):
            shutil.copy(file_path, folder_path)

    # Create zip file (flat structure based on the collected folder)
    zip_name = f"{folder_name}.zip"
    zip_path = os.path.join(cwd, zip_name)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path):
                zipf.write(file_path, file)  # use just filename inside zip

    print(f"✅ Collected files are in: {folder_path}")
    print(f"✅ Zipped archive created: {zip_path}")

    return folder_path, zip_path