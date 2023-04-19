import subprocess
import time

while True:
    # Lancer le processus
    process = subprocess.Popen(['python', 'bot_V5.py'])

    # Attendre que le processus se termine
    process.wait()

    # Attendre un certain temps avant de relancer le processus
    time.sleep(60)
