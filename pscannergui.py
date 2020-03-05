import pscannercli
import tkinter as tk
from tkinter import ttk


def app(connection):
    cursor = connection.cursor()
    hosts = cursor.execute(f'''SELECT DISTINCT host FROM ports_info''').fetchall()

    root = tk.Tk()
    root.title('Port Scanning Results')

    counter = 1

    for host in hosts:
        data = cursor.execute(f"""SELECT port, state, service FROM ports_info
                              WHERE host='{host[0]}'""").fetchall()

        table = tk.ttk.Treeview(root, columns=(1,2,3,4), show='headings', height='5')
        table.grid(row=counter, column=4)
        table.heading(1, text='Host')
        table.heading(2, text='Port')
        table.heading(3, text='State')
        table.heading(4, text='Service')

        for row in data:
            table.insert('', 'end', values=host+row)

        counter += 1

    root.mainloop()


if __name__ == '__main__':
    connection = pscannercli.initialize_db()
    app(connection)
