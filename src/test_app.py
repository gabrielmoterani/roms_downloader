"""
Simple test app to verify Kivy installation
"""

from kivy.app import App
from kivy.uix.label import Label


class TestApp(App):
    def build(self):
        return Label(text='Hello Kivy! ROM Downloader Test')


if __name__ == '__main__':
    TestApp().run()