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
import QtQuick.Controls 1.4

Row {
    spacing: 5

    Rectangle {
        height: legend_text.height
        width: window.width / 14
        color: "red"
    }

    Label {
        id: legend_text
        text: "DEV"
    }

    Rectangle {
        height: legend_text.height
        width: window.width / 14
        color: "green"
    }

    Label {
        text: "HW"
    }

    Rectangle {
        height: legend_text.height
        width: window.width / 14
        color: "blue"
    }

    Label {
        text: "EDU"
    }

    Rectangle {
        height: legend_text.height
        width: window.width / 14
        color: "cyan"
    }

    Label {
        text: "DOCS"
    }

    Rectangle {
        height: legend_text.height
        width: window.width / 14
        color: "magenta"
    }

    Label {
        text: "WEB"
    }

    Rectangle {
        height: legend_text.height
        width: window.width / 14
        color: "yellow"
    }

    Label {
        text: "DATA"
    }

    Rectangle {
        height: legend_text.height
        width: window.width / 14
        color: "black"
    }

    Label {
        text: "OTHER"
    }
}
