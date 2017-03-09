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
    id: details

    property string dev: ""
    property string repo: ""
    property string computed_class: ""

    ListModel {
        id: classifier_info
    }

    Component.onCompleted: {
        classifier_info.append({"classifier_name": "All classifier combined",
                                   "prob_dev": proxy.get_prob(details.dev, details.repo, 'DEV'),
                                   "prob_hw": proxy.get_prob(details.dev, details.repo, 'HW'),
                                   "prob_edu": proxy.get_prob(details.dev, details.repo, 'EDU'),
                                   "prob_docs": proxy.get_prob(details.dev, details.repo, 'DOCS'),
                                   "prob_web": proxy.get_prob(details.dev, details.repo, 'WEB'),
                                   "prob_data": proxy.get_prob(details.dev, details.repo, 'DATA'),
                                   "prob_other": proxy.get_prob(details.dev, details.repo, 'OTHER'),
                                   "combined": true}
                               )
        var classifier_list = proxy.get_classifier_names()
        for(var i = 0; i < classifier_list.length; ++i) {
            classifier_info.append({"classifier_name": classifier_list[i],
                                       "prob_dev": proxy.get_classifier_prob(details.dev, details.repo, 'DEV', classifier_list[i]),
                                       "prob_hw": proxy.get_classifier_prob(details.dev, details.repo, 'HW', classifier_list[i]),
                                       "prob_edu": proxy.get_classifier_prob(details.dev, details.repo, 'EDU', classifier_list[i]),
                                       "prob_docs": proxy.get_classifier_prob(details.dev, details.repo, 'DOCS', classifier_list[i]),
                                       "prob_web": proxy.get_classifier_prob(details.dev, details.repo, 'WEB', classifier_list[i]),
                                       "prob_data": proxy.get_classifier_prob(details.dev, details.repo, 'DATA', classifier_list[i]),
                                       "prob_other": proxy.get_classifier_prob(details.dev, details.repo, 'OTHER', classifier_list[i]),
                                       "combined": false}
                                   )
        }
    }

    ScrollView {
        anchors.fill: parent

        ListView {
            anchors.fill: parent
            spacing: 10

            boundsBehavior: Flickable.StopAtBounds

            header: Column {
                width: parent.width
                spacing: 10

                Row {
                    spacing: 10

                    Label {
                        text: "Developer:"
                    }

                    Label {
                        text: details.dev
                        font.bold: true
                    }
                }

                Row {
                    spacing: 10

                    Label {
                        text: "Repository:"
                    }

                    Label {
                        text: details.repo
                        font.bold: true
                    }
                }

                Row {
                    spacing: 10

                    Label {
                        text: "URL:"
                    }

                    Label {
                        property string url: proxy.get_url(details.dev, details.repo)
                        text: "<a href=\"" + url + "\">" + url + "</a>"
                        font.bold: true
                        onLinkActivated: {
                            Qt.openUrlExternally(link)
                        }
                    }
                }

                Row {
                    spacing: 10

                    Label {
                        text: "Computed Class:"
                    }

                    Label {
                        text: details.computed_class
                        font.bold: true
                    }
                }

                Label {
                    text: " "
                }

                Label {
                    text: "Classifier information:"
                    font.bold: true
                    font.underline: true
                    font.pixelSize: 14
                }

                Label {
                    text: "Legend:"
                }

                LegendBar {
                }

                Label {
                    text: " "
                }
            }

            footer: Column {
                spacing: 10
                Label {
                    text: " "
                }

                Button {
                    text: "Back"
                    x: window.width / 2.0 - width / 2.0
                    onClicked: {
                        pageStack.pop()
                    }
                }
            }

            model: classifier_info
            delegate: Item {
                height: classifier_label.height
                width: classifier_label.width

                Label {
                    id: classifier_label
                    text: classifier_name
                    font.bold: combined
                    font.italic: combined
                }

                ClassBar {
                    x: window.width / 2.0
                    y: classifier_label.y
                    width: window.width / 2.1
                    height: classifier_label.height

                    dev_prob: prob_dev
                    hw_prob: prob_hw
                    edu_prob: prob_edu
                    docs_prob: prob_docs
                    web_prob: prob_web
                    data_prob: prob_data
                    other_prob: prob_other
                }
            }
        }
    }
}
