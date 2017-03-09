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

import QtQuick 2.0
import QtQuick.Controls 1.4

Column {
    id: preferences

    width: window.width
    spacing: 10

    Row{
        spacing: 10
        Label {
            id: model_label
            text: "Path to models:"
        }
        TextField {
            id: model_input
            width: window.width - 10 - model_label.width - 10 - model_button.width
            text: settings.getStringConfig("model_path")
        }
        Button {
            id: model_button
            height: model_input.height
            text: "..."

            onClicked: {
                var path = proxy.get_dir_path("Path to models")
                if(path !== "") {
                    model_input.text = path
                }
            }
        }
    }

    Row{
        spacing: 10
        Label {
            id: cache_label
            text: "Path to cache:"
        }
        TextField {
            id: cache_input
            width: window.width - 10 - cache_label.width - 10 - cache_button.width
            text: settings.getStringConfig("cache_path")
        }
        Button {
            id: cache_button
            height: cache_input.height
            text: "..."

            onClicked: {
                var path = proxy.get_dir_path("Path to cache")
                if(path !== "") {
                    cache_input.text = path
                }
            }
        }
    }

    Row{
        spacing: 10
        Label {
            id: cache_age_label
            text: "Maximum cache age (in days):"
        }
        SpinBox {
            id: cache_age_input
            width: window.width - 10 - cache_age_label.width
            value: settings.getIntConfig("maximum_cache_age")
            minimumValue: 1
            maximumValue: 9999
        }
    }

    Row{
        spacing: 10
        CheckBox {
            id: cache_force_input
            width: window.width - 10
            text: "Force cache update"
            checked: settings.getBoolConfig("force_cache_update")
        }
    }

    Row{
        spacing: 10
        Label {
            id: user_label
            text: "Path to user file:"
        }
        TextField {
            id: user_input
            width: window.width - 10 - user_label.width - 10 - user_button.width
            text: settings.getStringConfig("user_file")
        }
        Button {
            id: user_button
            height: user_input.height
            text: "..."

            onClicked: {
                var path = proxy.get_file_path("Path to user file")
                if(path !== "") {
                    user_input.text = path
                }
            }
        }
    }

    Row{
        spacing: 10
        Label {
            id: secret_label
            text: "Path to secret file:"
        }
        TextField {
            id: secret_input
            width: window.width - 10 - secret_label.width - 10 - secret_button.width
            text: settings.getStringConfig("secret_file")
        }
        Button {
            id: secret_button
            height: secret_input.height
            text: "..."

            onClicked: {
                var path = proxy.get_file_path("Path to secret file")
                if(path !== "") {
                    secret_input.text = path
                }
            }
        }
    }

    Row{
        spacing: 10
        Label {
            id: worker_label
            text: "Number of workers (0 = number of processors):"
        }
        SpinBox {
            id: worker_input
            width: window.width - 10 - worker_label.width
            value: settings.getIntConfig("number_worker")
            minimumValue: 0
            maximumValue: 9999
        }
    }

    Row{
        spacing: 10
        Label {
            id: learning_label
            text: "Path to learning folder:"
        }
        TextField {
            id: learning_input
            width: window.width - 10 - learning_label.width - 10 - learning_button.width
            text: settings.getStringConfig("learning_input")
        }
        Button {
            id: learning_button
            height: learning_input.height
            text: "..."

            onClicked: {
                var path = proxy.get_dir_path("Path to learning folder")
                if(path !== "") {
                    learning_input.text = path
                }
            }
        }
    }

    Label {
        id: need_learning_label
        property string learning_path: settings.getStringConfig("learning_input")
        property string model_path: settings.getStringConfig("model_path")
        text: "Learning process will start if changes are saved!"
        font.bold: true
        visible: learning_input.text !== learning_path || model_input.text !== model_path
    }

    Row {
        x: parent.width / 2 - width / 2
        spacing: 10
        Button {
            text: "Discard Changes"
            onClicked: {
                window.settings_enabled = true
                pageStack.pop()
            }
        }
        Button {
            text: "Save Changes"
            onClicked: {
                settings.setStringConfig("model_path", model_input.text)
                settings.setStringConfig("cache_path", cache_input.text)
                settings.setIntConfig("maximum_cache_age", cache_age_input.value)
                settings.setBoolConfig("force_cache_update", cache_force_input.checked)
                settings.setStringConfig("user_file", user_input.text)
                settings.setStringConfig("secret_file", secret_input.text)
                settings.setIntConfig("number_worker", worker_input.value)
                settings.setStringConfig("learning_input", learning_input.text)
                window.settings_enabled = true

                proxy.check_authentification()

                window.update_rate_limit()

                if(need_learning_label.visible) {
                    pageStack.push({item: Qt.resolvedUrl('learning.qml'), replace: true})
                }
                else {
                    pageStack.pop()
                }
            }
        }
    }
}
