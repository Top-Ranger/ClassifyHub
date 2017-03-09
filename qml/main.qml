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

Item {
    id: main

    Connections {
        target: proxy
        onResultReady: {
            results.clear()
            var data = proxy.get_result_list()
            for(var i = 0; i < data.length; ++i) {
                var splitted = data[i].split("/")
                results.append({"dev": splitted[0], "repo": splitted[1], "determined_class": proxy.get_class(splitted[0], splitted[1]), "prob_dev": proxy.get_prob(splitted[0], splitted[1], 'DEV'), "prob_hw": proxy.get_prob(splitted[0], splitted[1], 'HW'), "prob_edu": proxy.get_prob(splitted[0], splitted[1], 'EDU'), "prob_docs": proxy.get_prob(splitted[0], splitted[1], 'DOCS'), "prob_web": proxy.get_prob(splitted[0], splitted[1], 'WEB'), "prob_data": proxy.get_prob(splitted[0], splitted[1], 'DATA'), "prob_other": proxy.get_prob(splitted[0], splitted[1], 'OTHER')})
            }
            window.update_rate_limit()
        }
    }

    ListModel {
        id: results
    }

    ScrollView {
        anchors.fill: parent

        ListView {
            anchors.fill: parent
            spacing: 10

            boundsBehavior: Flickable.StopAtBounds

            header: Column {
                width: parent.width
                spacing: 20

                Label {
                    x: parent.width/2 - width/2
                    id: title
                    text: "ClassifyHub"
                    font.pixelSize: 20
                }

                TextArea {
                    id: input
                    width: parent.width
                    text: "https://github.com/Top-Ranger/SPtP\nhttps://github.com/Top-Ranger/bakery"
                    readOnly: proxy.running
                    backgroundVisible: !proxy.running

                    onTextChanged: {
                        start_button.enabled = proxy.test_valid_input(text)
                    }

                    Connections {
                        target: open_file

                        onTriggered: {
                            var text = proxy.get_file_content()
                            if(text) {
                               input.text = text
                            }
                        }
                    }

                    Connections {
                        target: get_random

                        onTriggered: {
                            var text = proxy.get_random_repositories()
                            if(text) {
                               input.text = input.text + "\n" + text
                            }
                            window.update_rate_limit()
                        }
                    }
                }

                Button {
                    id: start_button
                    x: parent.width/2 - width/2
                    text: "Start computation"
                    visible: !proxy.running
                    onClicked: {
                        proxy.start_computation(input.text)
                        results.clear()
                    }
                }

                BusyIndicator {
                    height: start_button.height
                    x: parent.width/2 - width/2
                    visible: proxy.running
                }

                Label {
                    visible: results.count !== 0
                    text: "Legend:"
                }

                LegendBar {
                    visible: results.count !== 0
                }

                Row{
                    spacing: 10
                    visible: results.count !== 0

                    Label {
                        id: results_label
                        text: "Result:"
                        font.bold: true
                        font.underline: true
                        font.pixelSize: 14
                    }

                    Label {
                        text: "(Click on an entry for further information)"
                        font.italic: true
                        font.pixelSize:results_label.font.pixelSize
                    }
                }
            }

            model: results
            delegate: MouseArea {
                height: delegate_row.height
                width: window.width
                Row {
                    id: delegate_row
                    spacing: 10
                    Label {
                        id: dev_repo_label
                        text: dev + "/" + repo + ":"
                    }
                    Label {
                        font.bold: true
                        text: determined_class
                    }
                }

                ClassBar {
                    x: window.width / 2.0
                    y: dev_repo_label.y
                    width: window.width / 2.1
                    height: dev_repo_label.height

                    dev_prob: prob_dev
                    hw_prob: prob_hw
                    edu_prob: prob_edu
                    docs_prob: prob_docs
                    web_prob: prob_web
                    data_prob: prob_data
                    other_prob: prob_other
                }

                onClicked: {
                    pageStack.push(Qt.resolvedUrl('details.qml'), {dev: dev, repo: repo, computed_class: determined_class})
                }
            }
        }
    }
}
