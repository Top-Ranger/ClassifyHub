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
    width: window.width
    spacing: 10

    Component.onCompleted: {
        proxy.start_learning()
    }

    Connections {
        target: proxy

        onLearningRunningChanged: {
            if(value === false) {
                window.update_rate_limit()
                pageStack.pop()
            }
        }
    }

    Label {
        x: parent.width/2.0 - width/2.0
        text: "Learning process started"
        font.bold: true
    }

    BusyIndicator {
        x: parent.width/2.0 - width/2.0
    }

    Label {
        width: parent.width
        text: "Depending on your system, the size of learning data and the amount that needs to be downloaded this might take a while. Please wait."
        wrapMode: Text.Wrap
    }
}
