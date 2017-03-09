# Copyright (C) 2016,2017 Marcus Soll
# Copyright (C) 2016,2017 Malte Vosgerau
#
# This file is part of ClassifyHub.
#
# ClassifyHub is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ClassifyHub is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ClassifyHub. If not, see <http://www.gnu.org/licenses/>.

##
# \mainpage ClassifyHub documentation
#
# ClassifyHub is an algorithm to tackle the 'GitHub Classification Problem'.
# The goal is to classify GitHub (https://github.com/) repositories into the following categories:
# * <em>DEV</em>: software development projects
# * <em>HW</em>: Solutions for homeworks, exercises and similar
# * <em>EDU</em>: Repositories for didactic content
# * <em>DOCS</em>: Non-didactic documents
# * <em>WEB</em>: (Personal) web pages
# * <em>DATA</em>: Datasets
# * <em>OTHER</em>: Anything not contained in the above categories
#
# The input file must contain multiple URLs to GitHub repositories, where each line is a seperate URL.
# The learning directory must contain one file named after each category containing repositories from that class in
# the input format.
