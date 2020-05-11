#!/usr/bin/env python3

import db.primedb as db

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from gui.autoscreenmanager import AutoScreenManager
from test.menu import TestingMenu


class PrimeTrackerApp(App):
    def build(self):
        root = AutoScreenManager()
        root.switch_to_widget(TestingMenu())
        return root


def main():
    db.open_()
    PrimeTrackerApp().run()
    db.close()

if __name__ == '__main__': main()
