import sqlite3


class BookReader:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = self.connection.cursor()
        self._create_tables()

    def add_chapter(self, book, chapter, RP: int):  # RP = Required Percentage
        with self.connection:
            if self.has_chapter(book, chapter):
                book_id = self.get_book_id(book)
                self.cursor.execute("""
                    UPDATE Chapters
                    SET req_percent = ?
                    WHERE title = ? AND book_id = ?
                """, (RP, chapter, book_id))
            else:
                if not self.has_book(book):
                    self.cursor.execute("""
                        INSERT INTO Books(title)
                        VALUES(?)
                    """, (book,))

                book_id = self.get_book_id(book)
                self.cursor.execute("""
                    INSERT INTO Chapters(title, book_id, req_percent)
                    VALUES(?, ?, ?)
                """, (chapter, book_id, RP))
            self.connection.commit()

    def has_chapter(self, book, chapter):
        book_id = self.get_book_id(book)
        if book_id is None:
            return False
        with self.connection:
            self.cursor.execute(
                "SELECT * FROM Chapters WHERE title = ? AND book_id = ?", (chapter, book_id))
            return self.cursor.fetchone() is not None

    def has_book(self, book):
        with self.connection:
            self.cursor.execute("SELECT * FROM Books WHERE title = ?", (book,))
            return self.cursor.fetchone() is not None

    def get_book_id(self, book):
        with self.connection:
            self.cursor.execute(
                "SELECT id FROM Books WHERE title = ?", (book,))
            book_id = self.cursor.fetchone()
            return book_id[0] if book_id is not None else None

    def get_number_of_chapters(self, book):
        book_id = self.get_book_id(book)
        if book_id is None:
            return 0
        with self.connection:
            self.cursor.execute(
                "SELECT COUNT(*) FROM Chapters WHERE book_id = ?", (book_id,))
            return self.cursor.fetchone()[0]

    def get_number_of_completed_chapters(self, book):
        book_id = self.get_book_id(book)
        if book_id is None:
            return 0
        with self.connection:
            self.cursor.execute("""
                SELECT COUNT(*) FROM Progress
                JOIN Chapters ON Progress.chapter_id = Chapters.id
                WHERE Progress.percent >= Chapters.req_percent AND Chapters.book_id =
                ?
            """, (book_id,))
            return self.cursor.fetchone()[0]

    def get_chapters(self, book_id):
        if book_id is None:
            return []
        with self.connection:
            self.cursor.execute(
                "SELECT id FROM Chapters WHERE book_id = ?", (book_id,))
            return [chapter[0] for chapter in self.cursor.fetchall()]

    def _create_tables(self):
        with self.connection:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Books(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL UNIQUE
                );
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Chapters(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    book_id INTEGER NOT NULL,
                    req_percent INTEGER NOT NULL,
                    FOREIGN KEY(book_id) REFERENCES Books(id)
                );
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Chapters_Prereqs(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chapter_id INTEGER NOT NULL,
                    prereq_id INTEGER NOT NULL,
                    FOREIGN KEY(chapter_id) REFERENCES Chapters(id),
                    FOREIGN KEY(prereq_id) REFERENCES Chapters(id)
                );
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Progress(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    percent INTEGER NOT NULL,
                    chapter_id INTEGER NOT NULL UNIQUE,
                    FOREIGN KEY(chapter_id) REFERENCES Chapters(id)
                );
            """)
            self.connection.commit()


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
        chapters_count = self._reader.get_number_of_chapters(book)
        completed_count = self._reader.get_number_of_completed_chapters(book)
        print(f"{completed_count} of {chapters_count}")

    def _add_chapter(self, book_name, chapter_name, required_percent):
        self._reader.add_chapter(book_name, chapter_name, required_percent)

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
