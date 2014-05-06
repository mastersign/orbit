# Package orbit.index

class MultiLevelIndex:

	def __init__(self, attributes):
		self._attribute = attributes[0]
		self._sub_attributes = attributes[1:]
		self._is_parent = len(self._sub_attributes) > 0
		self._index = {}
		self._groups = {}
		self._group_index = {}

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
		if attribute not in self._group_index:
			self._group_index[attribute] = {}
		gi = self._group_index[attribute]
		for key in keys:
			if key in gi:
				gi[key].append(group)
			else:
				gi[key] = [group]

	def delete_group(self, attribute, group):
		if attribute not in self._groups or \
		   attribute not in self._group_index:
			return
		
		gm = self._groups[attribute]
		gi = self._group_index[attribute]
		if group in gm:
			keys = gm[group]
			del(gm[group])
			for key in keys:
				if key in gi:
					lst = gi[key]
					lst.remove(group)
					if len(lst) == 0:
						del(gi[key])

	def _get_groups(self, pivot):
		if self._attribute in self._group_index:
			gi = self._group_index[self._attribute]
			if pivot in gi:
				return gi[pivot]
		return []

	def add(self, value):
		pivot = getattr(value, self._attribute)
		self._add(value, pivot)
		for group in self._get_groups(pivot):
			self._add(value, group)

	def _add(self, value, pivot):
		if self._is_parent:
			if pivot not in self._index:
				self._index[pivot] = self._create_sub_index()
			self._index[pivot].add(value)
		else:
			if pivot not in self._index:
				self._index[pivot] = set()
			s = self._index[pivot]
			s.add(value)

	def _create_sub_index(self):
		sub_index = MultiLevelIndex(self._sub_attributes)
		sub_index._groups = self._groups
		sub_index._group_index = self._group_index
		return sub_index

	def remove(self, value):
		pivot = getattr(value, self._attribute)
		self._remove(value, pivot)
		for group in self._get_groups(pivot):
			self._remove(value, group)

	def _remove(self, value, pivot):
		if pivot not in self._index:
			return
		if self._is_parent:
			sub_index = self._index[pivot]
			sub_index.remove(value)
			if sub_index.is_empty():
				del(self._index[pivot])
		else:
			s = self._index[pivot]
			if value not in s:
				return
			s.remove(value)
			if len(s) == 0:
				del(self._index[pivot])

	def is_empty(self):
		return len(self._index) == 0

	def lookup(self, address):
		pivot = getattr(address, self._attribute)
		if self._is_parent:
			if pivot != None:
				if pivot in self._index:
					return self._index[pivot].lookup(address)
				else:
					return []
			else:
				res = []
				for i in self._index.values():
					res.extend(i.lookup(address))
				return res
		else:
			if pivot != None:
				return list(self._index[pivot])
			else:
				return sum(map(list, self._index.values()), [])

	def __len__(self):
		return sum(map(len, self._index.values()), 0)


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
		Item(1, 2, 1, "1-2-1"),
		Item(1, 2, 2, "1-2-2"),
		Item(2, 1, 1, "2-1-1"),
		Item(2, 1, 2, "2-1-2"),
		Item(2, 2, 1, "2-2-1"),
		Item(2, 2, 2, "2-2-2")]

	for i in items:
		index.add(i)
	print(len(index))
	print("1,1,1: " + str(index.lookup(Pattern(1, 1, 1))))
	print("1,*,1: " + str(index.lookup(Pattern(1, None, 1))))
	print("*,*,*: " + str(index.lookup(Pattern(None, None, None))))

	print("1-1-1: " + str(index.lookup(items[0])))

	index.remove(items[0])
	print(len(index))
	print("1,1,*: " + str(index.lookup(Pattern(1, 1, None))))

	index.add(items[0])
	print(len(index))
	print("1,1,*: " + str(index.lookup(Pattern(1, 1, None))))

	for i in items:
		index.remove(i)
	print(len(index))
	print("*,*,*: " + str(index.lookup(Pattern(None, None, None))))

	# None test

	print("None test")
	index = MultiLevelIndex(("a", "b", "c"))
	items = [
		Item(1, 1, 1, "1-1-1"),
		Item(1, 1, None, "1-1-N")]
	for i in items:
		index.add(i)
	print(len(index))
	print("1,1,1: " + str(index.lookup(Pattern(1, 1, 1))))
	print("1,1,*: " + str(index.lookup(Pattern(1, 1, None))))

	# group test

	print("group test")
	index = MultiLevelIndex(("a", "b", "c"))
	items = [
		Item(1, 1, 1, "1-1-1"),
		Item(1, 2, 1, "1-2-1"),
		Item(1, 3, 1, "1-3-2"),
		Item(1, 4, 1, "1-4-2")]
	index.add_group("b", 0, [2, 4])
	for i in items:
		index.add(i)
	print(len(index))
	print("1,0,*: " + str(index.lookup(Pattern(1, 0, None))))
