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

# Module orbit_framework.index

"""
Dieses Modul unterstützt das Nachrichtensystem von ORBIT
mit einer hierarchischen Indexstruktur.

Das Modul enthält die folgenden Klassen:

- :py:class:`MultiLevelReverseIndex`
"""

class MultiLevelReverseIndex(object):
	"""
	Diese Klasse implementiert eine hierarchischen Indexstruktur
	mit Unterstützung für mehrstufige Schlüssel einschließlich
	Gruppen und Wildcards im Schlüssel.

	**Parameter**

	``attributes``
		Eine Liste mit den Namen der Indexattribute.
	``item_attribut_selector`` (*optional*)
		Eine Funktion die beim Hinzufügen eines Objektes mit :py:meth:`add`
		verwendet wird, um den Attributwert unter Angabe des 
		Objektes und des Attributnamens zu ermitteln.
		Standardwert ist :py:meth:`getattr`.
	``lookup_attribut_selector`` (*optional*)
		Eine Funktion die beim Look-Up mit :py:meth:`lookup` 
		verwendet wird, um den Attributwert unter Angabe des 
		Schlüsselobjektes und des Attributnamens zu ermitteln.
		Standardwert ist :py:meth:`getattr`.

	**Beschreibung**

	Der Index wird mit einer Liste von Attributnamen (Indexattribute) initialisiert.
	Jedes Indexattribut steht für eine Ebene des hierarchischen Index.

	Gruppen für jedes Indexattribut können mit :py:meth:`add_group` und 
	:py:meth:`delete_group` verwaltet werden.

	Objekte werden mit :py:meth:`add` hinzugefügt und anhand der 
	Indexattribute indiziert. Die Attributwerte des Objektes können
	konkrete Werte, ein Gruppennamen oder `None` als Wildcard sein.

	Ein Look-Up erfolgt mit :py:meth:`lookup` und der Angabe eines 
	Schlüsselobjekts. Ein Schlüsselobjekt besitzt wie die indizierten Objekte
	alle Indexattribute.
	Zurückgegeben werden bei einem Look-Up alle Objekte, deren 
	Attributwerte zum angegebenen Schlüsselobjekt passen.
	"""

	def __init__(self, attributes, 
			item_attribute_selector = getattr,
			lookup_attribute_selector = getattr):
		self._attribute = attributes[0]
		self._item_attribute_selector = item_attribute_selector
		self._lookup_attribute_selector = lookup_attribute_selector
		self._sub_attributes = attributes[1:]
		self._is_parent = len(self._sub_attributes) > 0
		self._index = {}
		self._groups = {}

	def add_group(self, attribute, group, keys):
		"""
		Fügt dem Index eine Gruppe für ein Attribut hinzu.

		``attribute``
			Der Name des Indexattributes für das eine Gruppe eingerichtet werden soll.
		``group``
			Der Gruppenname unter dem Objekte indiziert werden können.
		``keys``
			Eine Sequenz von Werten die bei Look-Ups zu Objekten führen welche
			unter dem Gruppennamen indiziert wurden.
		"""
		if not (type(keys) is list):
			keys = list(keys)
		if attribute not in self._groups:
			self._groups[attribute] = {}
		gm = self._groups[attribute]
		if group not in gm:
			gm[group] = keys
		else:
			gm[group].extend(keys)

	def delete_group(self, attribute, group):
		"""
		Entfernt eine Gruppe für ein Attribut aus dem Index.

		``attribute``
			Der Name des Indexattributes für das die Gruppe entfernt werden soll.
		``group``
			Der Name der Gruppe.
		"""
		if attribute not in self._groups:
			return
		gm = self._groups[attribute]
		if group in gm:
			del(gm[group])

	def _get_group(self, group):
		if self._attribute in self._groups:
			gm = self._groups[self._attribute]
			if group in gm:
				return gm[group]
		return []

	def add(self, item):
		"""
		Fügt dem Index ein Objekt hinzu.
		Das Objekt wird anhand der Indexattribute indiziert.

		Die Werte der Indexattribute können konkrete Werte, Gruppennamen
		oder `None` als Wildcard sein.
		"""
		pivot = self._item_attribute_selector(item, self._attribute)
		self._add(item, pivot)
		for pivot2 in self._get_group(pivot):
			self._add(item, pivot2)

	def _add(self, item, pivot):
		if self._is_parent:
			if pivot not in self._index:
				self._index[pivot] = self._create_sub_index()
			self._index[pivot].add(item)
		else:
			if pivot not in self._index:
				self._index[pivot] = set()
			s = self._index[pivot]
			s.add(item)

	def _create_sub_index(self):
		sub_index = MultiLevelReverseIndex(self._sub_attributes)
		sub_index._groups = self._groups
		return sub_index

	def remove(self, item):
		"""
		Entfernt ein Objekt aus dem Index.
		"""
		pivot = self._item_attribute_selector(item, self._attribute)
		self._remove(item, pivot)
		for pivot2 in self._get_group(pivot):
			self._remove(item, pivot2)

	def _remove(self, item, pivot):
		if pivot not in self._index:
			return
		if self._is_parent:
			sub_index = self._index[pivot]
			sub_index.remove(item)
			if sub_index.is_empty():
				del(self._index[pivot])
		else:
			s = self._index[pivot]
			if item not in s:
				return
			s.remove(item)
			if len(s) == 0:
				del(self._index[pivot])

	def is_empty(self):
		"""
		Gibt ``True`` zurück, wenn der Index kein Objekt enthält,
		sonst ``False``. 

		Der Index ist auch dann leer, wenn Gruppen eingerichtet,
		aber keine Objekte indiziert wurden.
		"""
		return len(self._index) == 0

	def lookup(self, key_obj):
		"""
		Ruft eine Liste mit allen Objekten ab, deren indizierte Attributwerte zu den
		Attributwerten des übergebenen Schlüsselobjektes passen.

		Damit ein Objekt im Ergebnis enthalten ist, müssen alle
		Indexattribute passen. Ein Indexattribut passt

		1. wenn der indizierte Attributwert gleich dem Schlüsselattribut ist
		2. oder das indizierte Attribut ein Gruppenname 
		   und das Schlüsselattribut in dieser Gruppe ist,
		3. oder das indizierte Attribut `None` ist.
		"""
		pivot = self._lookup_attribute_selector(key_obj, self._attribute)
		if self._is_parent:
			if pivot == None:
				if pivot in self._index:
					return self._index[pivot].lookup(key_obj)
				else:
					return []
			else:
				res = []
				if pivot in self._index:
					res.extend(self._index[pivot].lookup(key_obj))
				if None in self._index:
					res.extend(self._index[None].lookup(key_obj))
				return res
		else:
			if pivot == None:
				if pivot in self._index:
					return list(self._index[pivot])
				else:
					return []
			else:
				res = []
				if pivot in self._index:
					res.extend(list(self._index[pivot]))
				if None in self._index:
					res.extend(list(self._index[None]))
				return res

# Tests

if __name__ == '__main__':

	class Item(object):
		def __init__(self, a, b, c, value):
			self.a = a
			self.b = b
			self.c = c
			self.value = value
		def __repr__(self):
			return self.value

	class Pattern(object):
		def __init__(self, a, b, c):
			self.a = a
			self.b = b
			self.c = c

	# basic test

	print("basic test")
	index = MultiLevelIndex(("b", "a", "c"))
	items = [
		Item(1, 1, 1, "1-1-1"),
		Item(1, 1, 2, "1-1-2"),
		Item(1, 1, None, "1-1-*"),
		Item(1, None, 1, "1-*-1"),
		Item(None, None, 1, "*-*-1")]

	for i in items:
		index.add(i)
	print("1,1,1: " + str(index.lookup(Pattern(1, 1, 1))))
	print("1,1,2: " + str(index.lookup(Pattern(1, 1, 2))))
	print("1,2,1: " + str(index.lookup(Pattern(1, 2, 1))))
	print("1,2,2: " + str(index.lookup(Pattern(1, 2, 2))))
	print("2,1,1: " + str(index.lookup(Pattern(2, 1, 1))))
	print("2,1,2: " + str(index.lookup(Pattern(2, 1, 2))))
	print("2,2,1: " + str(index.lookup(Pattern(2, 2, 1))))
	print("2,2,2: " + str(index.lookup(Pattern(2, 2, 2))))

	index.remove(items[0])
	print("removed 1-1-1")
	print("1,1,1: " + str(index.lookup(Pattern(1, 1, 1))))

	index.add(items[0])
	print("added 1-1-1")
	print("1,1,1: " + str(index.lookup(Pattern(1, 1, 1))))


	for i in items:
		index.remove(i)
	print("removed all")
	print("1,1,1: " + str(index.lookup(Pattern(1, 1, 1))))

	# None test

	print("None test")
	index = MultiLevelIndex(("a", "b", "c"))
	items = [
		Item(1, 1, 1, "1-1-1"),
		Item(1, 1, None, "1-1-*")]
	for i in items:
		index.add(i)
	print("1,1,1: " + str(index.lookup(Pattern(1, 1, 1))))
	print("1,1,N: " + str(index.lookup(Pattern(1, 1, None))))

	# group test

	print("group test")
	index = MultiLevelIndex(("a", "b", "c"))
	items = [
		Item(1, 1, 1, "1-1-1"),
		Item(1, 0, 1, "1-0-1"),
		Item(1, 3, 1, "1-3-2"),
		Item(1, 0, 1, "1-0-2")]
	index.add_group("b", 0, [2, 4])
	for i in items:
		index.add(i)
	print("1,1,1: " + str(index.lookup(Pattern(1, 1, 1))))
	print("1,2,1: " + str(index.lookup(Pattern(1, 2, 1))))
	print("1,3,1: " + str(index.lookup(Pattern(1, 3, 1))))
	print("1,4,1: " + str(index.lookup(Pattern(1, 4, 1))))

