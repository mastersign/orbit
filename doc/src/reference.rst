API-Referenz
############

Die öffentliche ORBIT-API besteht aus den folgenden Modulen:

- :py:mod:`orbit.setup`
- :py:mod:`orbit.application`
- :py:mod:`orbit.index`
- :py:mod:`orbit.components.common`
- :py:mod:`orbit.components.timer`
- :py:mod:`orbit.jobs.apps`
- :py:mod:`orbit.jobs.services`

orbit.setup
===========

.. automodule:: orbit.setup

Configuration
-------------

.. autoclass:: orbit.setup.Configuration
	:members:

orbit.application
=================

.. automodule:: orbit.application

Core
----

.. autoclass:: orbit.application.Core(config = Configuration())
	:members:

DeviceManager
-------------

.. autoclass:: orbit.application.DeviceManager
	:members:

Blackboard
----------

.. autoclass:: orbit.application.Blackboard
	:members:

Job
---

.. autoclass:: orbit.application.Job
	:members:

Service
-------

.. autoclass:: orbit.application.Service
	:members:

App
---

.. autoclass:: orbit.application.App
	:members:

orbit.index
===========

.. automodule:: orbit.index

MultiLevelReversedIndex
-----------------------

.. autoclass:: orbit.index.MultiLevelReverseIndex(attributes, item_attribute_selector = getattr, lookup_attribute_selector = getattr)
	:members:
