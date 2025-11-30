from datetime import datetime
import os
from enum import Enum

BACKLOG_FILE = "backlog.txt"

class BacklogAction(str, Enum):

    """Enumerateur des valeurs des types actions sur les logs"""

    ADD = "ADD"
    DELETE = "DELETE"
    UPDATE = "UPDATE"

class DocEduc:

    """ Objet qui definit une données stocker dans notre stockage objet au besoin de notre RAG system"""

    def __init__(self, course, description, path):
        self.course =  course
        self.description =  description
        self.path = path

class LoggingLogicFunctions: 

    """Ensemble des fonctions  d'acting et checkpoints sur les fichiers backlog.txt & checkpoints.csv"""

    @staticmethod
    def acting_backlog(document:DocEduc, action: BacklogAction):
        file_exists = os.path.isfile(BACKLOG_FILE)
        headers = "log, date, course, description, path_bucket\n"

        with open(BACKLOG_FILE, "a") as f:
            if not file_exists:
                f.write(headers)


            date_now =  datetime.now()
            line = f"{action}, {date_now}, {document.course}, {document.description}, {document.path}\n"
            f.write(line)

    @staticmethod
    def acting_checkpoints():
        pass