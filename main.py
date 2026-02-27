#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Study Monitor App - Beta Version
"""

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.core.text import LabelBase
import os

# Register Android system font for Chinese support
if os.path.exists('/system/fonts/NotoSansCJK-Regular.otf'):
    LabelBase.register('AndroidChinese', '/system/fonts/NotoSansCJK-Regular.otf')
elif os.path.exists('/system/fonts/DroidSansFallback.ttf'):
    LabelBase.register('AndroidChinese', '/system/fonts/DroidSansFallback.ttf')


class StudyMonitorApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Use system font for Chinese support
        label = Label(
            text='学习监督助手',
            font_size='24sp',
            font_name='AndroidChinese' if 'AndroidChinese' in LabelBase.get_registered_fonts() else 'Roboto',
            size_hint_y=0.8
        )
        subtitle = Label(
            text='版本 0.2.0 - 64位',
            font_size='16sp',
            font_name='AndroidChinese' if 'AndroidChinese' in LabelBase.get_registered_fonts() else 'Roboto',
            size_hint_y=0.2
        )
        layout.add_widget(label)
        layout.add_widget(subtitle)
        return layout


if __name__ == '__main__':
    StudyMonitorApp().run()
