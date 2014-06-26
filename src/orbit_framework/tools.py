# coding=utf-8

## ORBIT ist ein Python-Framework für TinkerForge-Anwendungen
## Copyright (C) 2014 Tobias Kiertscher <dev@mastersign.de>
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as 
## published by the Free Software Foundation, either version 3 
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
## 
## You should have received a copy of the GNU (Lesser) General 
## Public License along with this program. 
## If not, see <http://www.gnu.org/licenses/>.

# Module orbit_framework.tools

"""
Diese Modul enthält unterstützende Klassen und Funktionen.

Das Modul enthält die folgenden Klassen:

- :py:class:`MulticastCallback`
"""

class MulticastCallback(object):
	"""
	Diese Klasse bildet einen einfachen Mechanismus,
	um mehrere Callbacks mit identischer Signatur zu einem Callback zusammenzufassen.

	Mit :py:meth:`add_callback` können Callbacks hinzugefügt werden.
	Mit :py:meth:`remove_callback` können Callbacks wieder entfernt werden.

	Die Klasse implementiert die ``__call__``-Methode, daher können Instanzen 
	der Klasse selbst als Callback weitergegeben werden.
	Wird Klasse als Funktion aufgerufen, werden die mit :py:meth:`add_callback`
	registrierten Funktionen in der gleichen Reihenfolge aufgerufen, in der sie
	hinzugefügt wurden. Dabei werden alle Parameter unverändert weitergegeben.

	*Siehe auch:*
	:py:meth:`add_callback`,
	:py:meth:`remove_callback`
	"""

	def __init__(self):
		self._callbacks = []

	def add_callback(self, callback):
		"""
		Fügt ein Callback hinzu.
		"""
		self._callbacks.append(callback)

	def remove_callback(self, callback):
		"""
		Entfernt ein Callback.
		"""
		self._callbacks.remove(callback)

	def __call__(self, *pargs, **nargs):
		for callback in self._callbacks:
			callback(*pargs, **nargs)
