from nicegui import ui
import subprocess

def do_stuff():
    print("Hello")

ui.button("Ask AI", on_click=do_stuff)

ui.run()