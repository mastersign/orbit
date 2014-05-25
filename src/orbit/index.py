# Package orbit.index

class MultiLevelReverseIndex:

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
		return len(self._index) == 0

	def lookup(self, address):
		pivot = self._lookup_attribute_selector(address, self._attribute)
		if self._is_parent:
			if pivot == None:
				if pivot in self._index:
					return self._index[pivot].lookup(address)
				else:
					return []
			else:
				res = []
				if pivot in self._index:
					res.extend(self._index[pivot].lookup(address))
				if None in self._index:
					res.extend(self._index[None].lookup(address))
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

	class Item:
		def __init__(self, a, b, c, value):
			self.a = a
			self.b = b
			self.c = c
			self.value = value
		def __repr__(self):
			return self.value

	class Pattern:
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

