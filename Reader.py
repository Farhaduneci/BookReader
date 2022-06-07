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

    def add_progress(self, book, chapter, percent):
        if self.has_book(book) and self.has_chapter(book, chapter):
            if self.has_completed_prereqs(book, chapter):
                if self.has_progress(book, chapter):
                    with self.connection:
                        chapter_id = self.get_chapter_id(book, chapter)
                        self.cursor.execute("""
                            UPDATE Progress
                            SET percent = ?
                            WHERE chapter_id = ?
                        """, (percent, chapter_id))
                        self.connection.commit()
                else:
                    with self.connection:
                        chapter_id = self.get_chapter_id(book, chapter)
                        self.cursor.execute("""
                            INSERT INTO Progress(chapter_id, percent)
                            VALUES(?, ?)
                        """, (chapter_id, percent))
                        self.connection.commit()

    def has_progress(self, book, chapter):
        chapter_id = self.get_chapter_id(book, chapter)
        if chapter_id is None:
            return False
        with self.connection:
            self.cursor.execute("""
                SELECT * FROM Progress WHERE chapter_id = ?
            """, (chapter_id,))
            return self.cursor.fetchone() is not None

    def has_completed_prereqs(self, book, chapter):
        return True if \
            self.get_number_of_completed_prereqs(book, chapter) == \
            self.get_number_of_prereqs(book, chapter) else False

    def get_number_of_prereqs(self, book, chapter):
        chapter_id = self.get_chapter_id(book, chapter)
        if chapter_id is None:
            return 0
        with self.connection:
            self.cursor.execute(
                "SELECT COUNT(*) FROM Chapters_Prereqs WHERE chapter_id = ?", (chapter_id,))
            return self.cursor.fetchone()[0]

    def get_number_of_completed_prereqs(self, book, chapter):
        chapter_id = self.get_chapter_id(book, chapter)
        if chapter_id is None:
            return 0
        with self.connection:
            self.cursor.execute("""
                SELECT COUNT(*) FROM Chapters_Prereqs
                JOIN Chapters ON Chapters_Prereqs.prereq_id = Chapters.id
                JOIN Progress ON Chapters.id = Progress.chapter_id
                WHERE Chapters_Prereqs.chapter_id = ? AND Progress.percent >=
                Chapters.req_percent
            """, (chapter_id,))
            return self.cursor.fetchone()[0]

    def add_prereq(self, book, chapter, prereq):
        if self.has_book(book) and self.has_chapter(book, chapter) and self.has_chapter(book, prereq):
            with self.connection:
                chapter_id = self.get_chapter_id(book, chapter)
                prereq_id = self.get_chapter_id(book, prereq)
                self.cursor.execute("""
                    INSERT INTO Chapters_Prereqs(chapter_id, prereq_id)
                    VALUES(?, ?)
                """, (chapter_id, prereq_id))
                self.connection.commit()

    def del_prereq(self, book, chapter, prereq):
        if self.has_book(book) and self.has_chapter(book, chapter) and self.has_chapter(book, prereq):
            with self.connection:
                chapter_id = self.get_chapter_id(book, chapter)
                prereq_id = self.get_chapter_id(book, prereq)
                self.cursor.execute("""
                    DELETE FROM Chapters_Prereqs
                    WHERE chapter_id = ? AND prereq_id = ?
                """, (chapter_id, prereq_id))
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

    def get_chapter_id(self, book, chapter):
        book_id = self.get_book_id(book)
        if book_id is None:
            return None
        with self.connection:
            self.cursor.execute(
                "SELECT id FROM Chapters WHERE title = ? AND book_id = ?", (chapter, book_id))
            return self.cursor.fetchone()[0]

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
        self._reader.add_progress(book_name, chapter_name, percent)

    def _stats(self, book):
        chapters_count = self._reader.get_number_of_chapters(book)
        completed_count = self._reader.get_number_of_completed_chapters(book)
        print(f"{completed_count} of {chapters_count}")

    def _add_chapter(self, book_name, chapter_name, required_percent):
        self._reader.add_chapter(book_name, chapter_name, required_percent)

    def _add_prerequisite_chapter(self, book_name, chapter_name, prerequisite_chapter):
        self._reader.add_prereq(book_name, chapter_name, prerequisite_chapter)

    def _remove_prerequisite_chapter(self, book_name, chapter_name, prerequisite_chapter):
        self._reader.remove_prereq(
            book_name, chapter_name, prerequisite_chapter)


def main():
    conn = sqlite3.connect("Reader.db")

    reader = BookReader(conn)
    dispatcher = CommandDispatcher(reader)

    while (command := input()) != 'end':
        dispatcher.dispatch(command)


if __name__ == '__main__':
    main()
