/*
 * Copyright (C) 2016,2017 Marcus Soll
 * Copyright (C) 2016,2017 Malte Vosgerau
 *
 * This file is part of ClassifyHub.
 *
 * ClassifyHub is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * ClassifyHub is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with ClassifyHub. If not, see <http://www.gnu.org/licenses/>.
 */

import QtQuick 2.2
import QtQuick.Window 2.1
import QtQuick.Controls 1.4

import UIProxy 1.0
import SettingsProxy 1.0

ApplicationWindow {
    id: window

    property int rate_limit: -1
    property bool settings_enabled: true

    function update_rate_limit() {
        proxy.get_remaining_rate_limit()
    }

    SettingsProxy {
        id: settings
    }

    Timer {
        id: rate_limit_timer
        repeat: false
        onTriggered: update_rate_limit()
    }

    Component.onCompleted: {
        window.width = settings.width
        window.height = settings.height
        window.x = settings.x
        window.y = settings.y

        update_rate_limit()

        if(proxy.check_learning_needed()) {
            pageStack.push({item: Qt.resolvedUrl('learning.qml'), immediate: true})
        }
    }

    width: 800
    height: 600

    onWidthChanged: {
        settings.width = window.width
    }
    onHeightChanged: {
        settings.height = window.height
    }

    x: 0
    y: 0
    onXChanged: {
        settings.x = window.x
    }
    onYChanged: {
        settings.y = window.y
    }

    UIProxy {
        id: proxy

        onRateLimit: {
            rate_limit = limit
            if(rate_limit === -1) {
                rate_limit_timer.interval = 5000
            }
            else {
                rate_limit_timer.interval = 300000 // 5 min
            }
            rate_limit_timer.restart()
        }
    }

    Item {
        focus: true
        Keys.onReleased: {
            if(event.key === Qt.Key_Back)
            {
                if(pageStack.depth > 1)
                {
                    pageStack.pop()
                }

                event.accepted = true
            }
        }
    }

    menuBar: MenuBar {
        Menu {
            title: "File"
            MenuItem {
                id: open_file

                text: "Open repository file"
                enabled: !proxy.running
                shortcut: StandardKey.Open
            }
            MenuItem {
                id: get_random

                text: "Fetch random repositories"
                enabled: !proxy.running
            }
            MenuItem {
                text: "Save results"
                enabled: proxy.saveReady
                shortcut: StandardKey.Save
                onTriggered: proxy.save_results()
            }

            MenuSeparator {
            }

            MenuItem {
                text: "Exit"
                shortcut: StandardKey.Quit
                enabled: !proxy.running
                onTriggered: {
                    Qt.quit()
                }
            }
        }

        Menu {
            title: "Edit"
            MenuItem {
                text: "Preferences"
                shortcut: StandardKey.Preferences
                enabled: !proxy.running && window.settings_enabled
                onTriggered: {
                    window.settings_enabled = false
                    pageStack.push(Qt.resolvedUrl('preferences.qml'))
                }
            }

            MenuSeparator {
            }

            MenuItem {
                text: "Start learning"
                enabled: !proxy.running
                onTriggered: pageStack.push(Qt.resolvedUrl('learning.qml'))
            }
        }

        Menu {
            title: "About"
            MenuItem {
                text: "About Qt"
                onTriggered: {
                    proxy.show_about_qt()
                }
            }
            MenuItem {
                text: "About PyQt5"
                onTriggered: {
                    proxy.show_about_pyqt()
                }
            }
            MenuItem {
                text: "About ClassifyHub"
                onTriggered: {
                    proxy.show_about_classifyhub()
                }
            }
        }
    }

    statusBar: StatusBar {
        Row {
            spacing: 5
            Label {
                text: "No connection to GitHub"
                font.bold: true
                visible: window.rate_limit === -1
            }
            Label {
                text: "Remaining requests to GitHub:"
                visible: window.rate_limit !== -1
            }
            Label {
                text: "" + window.rate_limit
                font.italic: true
                visible: window.rate_limit !== -1
            }
        }
    }

    StackView {
        id: pageStack
        anchors.fill: parent
        initialItem: Qt.resolvedUrl('main.qml')
    }
}
