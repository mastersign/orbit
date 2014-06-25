# coding=utf-8

# Module orbit_framework.tools

"""
Diese Modul enthält unterstützende Klassen und Funktionen.

Das Modul enthält die folgenden Klassen:

- :py:class:`MulticastCallback`
"""

class MulticastCallback:
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
