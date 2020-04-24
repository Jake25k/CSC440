import sqlite3
from datetime import date

class TalkThread(object):

    def __init__(self, id, cmts):
        self.id = id
        self.comments = cmts

    def add_comments(self, cmts):
        self.comments.append(cmts)

class Comment(object):

    def __init__(self, cmt):
        self.comment_id = cmt[0]
        self.reply_id = cmt[1]
        self.date = cmt[2]
        self.username = cmt[3]
        self.post = cmt[4]


class TalkPage(object):

    def __init__(self, page):
        self.dbcon = sqlite3.connect('wiki/web/talk/talk.db')
        self.cursor = self.dbcon.cursor()

    def get_page_id(self, name):
        self.cursor.execute("SELECT page_id FROM pages WHERE page_name = ?", (name,))
        r = self.cursor.fetchone()
        if r is None:
            return None
        return r[0]

    def add_page(self, name):
        self.cursor.execute("INSERT INTO pages (page_name) VALUES (?)", (name,))
        self.dbcon.commit()
        return self.cursor.execute("SELECT last_insert_rowid()").fetchone()[0]

    def get_page_thread_ids(self, pgid):
        self.cursor.execute("SELECT DISTINCT thread_id FROM thread WHERE page_id = ?", (pgid,))
        ids = []
        r = self.cursor.fetchall()
        for result in r:
            ids.append(result[0])
        return ids

    def new_thread_id(self):
        self.cursor.execute("SELECT max(thread_id) FROM thread")
        f = self.cursor.fetchone()[0]
        if f is None:
            return 1
        else:
            return f + 1

    def thread_of_comment_id(self, cmnt_id):
        self.cursor.execute("SELECT thread_id FROM thread WHERE comment_id = ?", (cmnt_id,))
        return self.cursor.fetchone()[0]

    def get_thread_comments(self, thread_id):
        self.cursor.execute("""SELECT comment_id,reply_id,date,username,post FROM comment INNER JOIN
                                thread USING (comment_id) WHERE thread_id = ?""", (thread_id,))
        comments = []
        for cmt in self.cursor.fetchall():
            comments.append(Comment(cmt))
        return comments

    def add_comment(self, thread_id, page_id, comment_id):
        self.cursor.execute("INSERT INTO thread VALUES (?,?,?)", (thread_id,page_id,comment_id,))
        self.dbcon.commit()

    def comment_exists(self, id):
        self.cursor.execute("SELECT comment_id FROM comment WHERE comment_id = ?", (id,))
        r = self.cursor.fetchone()
        if r is None:
            return False
        else:
            return True

    def get_threads(self, page_name):
        page_id = self.get_page_id(page_name)
        if page_id is None:
            print("Page id does not exist, creating a new talk page")
            page_id = self.add_page(page_name)
            return []

        ids = self.get_page_thread_ids(page_id)
        threads = []
        for tid in ids:
            new_thr = TalkThread(tid, self.get_thread_comments(tid))
            threads.append(new_thr)
        return threads

    # Save a comment to the database and return its comment id
    # cmt_text: string of comment's text
    # reply_to: id of reply comment, optional
    def save_comment(self, cmt_text, reply_to=''):
        d = date.today()
        date_str = d.strftime("%m/%d/%y")
        cmt_data = (reply_to, date_str, "User", cmt_text.rstrip(),)
        self.cursor.execute("INSERT INTO comment (reply_id, date, username, post) VALUES (?,?,?,?)", cmt_data)
        self.dbcon.commit()
        return self.cursor.execute("SELECT last_insert_rowid()").fetchone()[0]

    def post_comment(self, page_name, cmt_text, reply_to):
        pg_id = self.get_page_id(page_name)
        assert pg_id,"Page ID not found"

        # New comments are in their own thread
        if reply_to == '':
            new_thr_id = self.new_thread_id()
            cmt_id = self.save_comment(cmt_text)
            self.add_comment(new_thr_id, pg_id, cmt_id)
        else:
            assert self.comment_exists(reply_to), "Invalid reply number: " + str(reply_to)
            thr_id = self.thread_of_comment_id(reply_to)
            cmt_id = self.save_comment(cmt_text, reply_to)
            self.add_comment(thr_id, pg_id, cmt_id)
