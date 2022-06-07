import sqlite3


class BookReader:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = self.connection.cursor()
        self._create_tables()

    def add_chapter(self, book, chapter, RP: int):  # RP = Required Percentage
        pass

    def _create_tables(self):
        pass


class CommandDispatcher:
    def __init__(self, reader):
        self._reader = reader
        self._commands = {
            'read': self._read,
            'stats': self._stats,
            'add_chapter': self._add_chapter,
            'add_prerequisite_chapter': self._add_prerequisite_chapter,
            'remove_prerequisite_chapter': self._remove_prerequisite_chapter,
        }

    def dispatch(self, command):
        command, *parameters = command.split()
        self._handle_command(command, *parameters)

    def _handle_command(self, command, *parameters):
        self._commands[command](
            *parameters) if parameters else self._commands[command]()

    def _read(self, book_name, chapter_name, percent):
        pass

    def _stats(self, book):
        pass

    def _add_chapter(self, book_name, chapter_name, required_percent):
        pass

    def _add_prerequisite_chapter(self, book_name, chapter_name, prerequisite_chapter):
        pass

    def _remove_prerequisite_chapter(self, book_name, chapter_name, prerequisite_chapter):
        pass


def main():
    conn = sqlite3.connect("Reader.db")

    reader = BookReader(conn)
    dispatcher = CommandDispatcher(reader)

    while (command := input()) != 'end':
        dispatcher.dispatch(command)


if __name__ == '__main__':
    main()
