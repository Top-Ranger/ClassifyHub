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

Rectangle {
    id: class_bar

    property real dev_prob: 0.0
    property real hw_prob: 0.0
    property real edu_prob: 0.0
    property real docs_prob: 0.0
    property real web_prob: 0.0
    property real data_prob: 0.0
    property real other_prob: 0.0

    property real normalisation_value: 1.0

    opacity: 1.0
    color: "white"

    function redraw() {
        var divisor = (class_bar.dev_prob + class_bar.hw_prob + class_bar.edu_prob + class_bar.docs_prob + class_bar.web_prob + class_bar.data_prob + class_bar.other_prob)
        if(divisor == 0.0) {
            // Safety guard
            divisor = 1.0
        }

        normalisation_value = 7.0 / divisor
    }

    Component.onCompleted: redraw()

    onDev_probChanged: redraw()
    onHw_probChanged: redraw()
    onEdu_probChanged: redraw()
    onDocs_probChanged: redraw()
    onWeb_probChanged: redraw()
    onData_probChanged: redraw()
    onOther_probChanged: redraw()

    Row {
        spacing: 0
        anchors.left: parent.left

        Rectangle {
            height: class_bar.height
            width: (class_bar.width / 7.0) * class_bar.dev_prob * class_bar.normalisation_value
            color: "red"
        }

        Rectangle {
            height: class_bar.height
            width: (class_bar.width / 7.0) * class_bar.hw_prob * class_bar.normalisation_value
            color: "green"
        }

        Rectangle {
            height: class_bar.height
            width: (class_bar.width / 7.0) * class_bar.edu_prob * class_bar.normalisation_value
            color: "blue"
        }

        Rectangle {
            height: class_bar.height
            width: (class_bar.width / 7.0) * class_bar.docs_prob * class_bar.normalisation_value
            color: "cyan"
        }

        Rectangle {
            height: class_bar.height
            width: (class_bar.width / 7.0) * class_bar.web_prob * class_bar.normalisation_value
            color: "magenta"
        }

        Rectangle {
            height: class_bar.height
            width: (class_bar.width / 7.0) * class_bar.data_prob * class_bar.normalisation_value
            color: "yellow"
        }

        Rectangle {
            height: class_bar.height
            width: (class_bar.width / 7.0) * class_bar.other_prob * class_bar.normalisation_value
            color: "black"
        }
    }
}
