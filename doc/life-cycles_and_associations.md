# Life-Cycles and Associations

## Overview

1. `Core()`
	* `Blackboard()`
	* `DeviceManager()`
1. potentially `core.start()`
1. add *Job*s:
	1. `Job(name)`
	1. potentially `core.install(job)`
	1. add *Component*s:
		1. `Component(name)`
		1. potentially `job.register_component(component)`
		1. add *DeviceHandle*s:
			1. `DeviceHandle(...)`
			1. `component.add_device_handle(device_handle)`
		1. add *EventListener*s:
			1. `EventListener(...)`
			1. `component.add_event_listener(event_listener)`
		1. `job.register_component(component)`
	1. `core.install(job)`
1. `core.start()`
1. `job.active = True`
	1. `component.enabled = True` 
		1. `blackboard.add_listener(event_listener)`
		1. `device_manager.add_handler(device_handler)`
1. `job.active = False`
	1. `component.enabled = False` 
		1. `blackboard.remove_listener(event_listener)`
		1. `device_manager.remove_handler(device_handler)`
1. remove *Component*s:
	1. `job.remove_component(component)`
1. remove *Job*s:
	1. `core.uninstall(job)`
1. `core.stop()`


## Core
### Initialization
by user with optional *Configuration*
### Associations

* fix association with *Configuration*
* `install(job)` associates with *Job*s  
  Called by: user
	* `job.on_install(core)`
	* if `started` and `job.background` then `job.active = True` 
* `uninstall(job)` disassociates from *Job*s  
  Called by: user
	* if `job.active` then `job.active = False`
	* `job.on_uninstall()`
* `activate(application)` selectes current *Application*  
  Called by: **???**
	* if `current_application` then `current_application.active = False`
	* `current_application = application`
	* if `current_application` then `current_application.active = True`

### Transitions

* `started = True`  
  Called by: `core.start()`
	* for each *Job*s:
		* `job.on_core_started()`
	* for each *Job*s:
		* if `job.background` then `job.active = True`
* `started = False`  
  Called by: `core.stop()`
	* for each *Job*s:	
		* `job.active = False`

## Blackboard
### Initialization
by *Core* with reference to *Core*
### Associations

* fix association with *Core*
* `add_listener(event_listener)` associates with *EventListener*s  
  Called by: `component.enabled` and `component.add_event_listener(event_listener)`
* `remove_listener(event_listener)` disassociates from *EventListener*s  
  Called by: `component.enabled`

## DeviceManager
### Initialization
by *Core* with reference to *Core*
### Association

* fix association with *Core*
* fix association with *TF.IPConnection*(s)
* `add_handle(device_handle)` associates with *DeviceHandle*s  
  Called by: `component.enabled` and `component.add_device_handle(device_handle)`
	* `device_handle.on_add_handle(device_manager)`
	* for each *TF.Device*:
		* `device_handle.on_bind_device(device)`
* `remove_handle(device_handle)` disassociates from *DeviceHandle*s  
  Called by: `component.enabled`
	* for each *TF.Device*:
		* `device_handle.on_unbind_device(device)`
	* `device_handle.on_remove_handle()`
* `add_device_callback(uid, event_code, device_callback)` associates with *DeviceCallback*s  
  Called by: `device_handle.on_bind_device(device)`
* `remove_device_callback(uid, event_code, device_callback)` disassociates from *DeviceCallback*s  
  Called by: `device_handle.on_unbind_device(device)`
* `_bind_device(device)` associates with *TF.Device*  
  Called by: `device_manager._cb_enumerate(...)`
	* for each *device_callback* with matching device type:
		* `device.register_callback(callback)`
* `_unbind_device(device)` disassociates from *TF.Device"  
  Called by: `device_manager._cb_enumerate(...)`

### Transitions

* `start()`  
  Called by: `core.start()`
* `stop()`
  Called by: `core.stop()`

## Job
### Initialization
stand alone by user
### Associations

* `on_install(core)` associates with *Core*  
  Called by: `core.install(job)`
* `on_uninstall()` disassociates from *Core*  
  Called by: `core.uninstall(job)`
* `add_component(component)` associates with *Component*s  
  Called by: user
	* `component.on_add_component(parent)`
	* if `job.active` then `component.enabled = True`
* `remove_component(component)` disassociates from *Component*s  
  Called by: user
	* if `job.active` then `component.enabled = False`
	* `component.on_remove_component()`

### Transitions

* `active = True`  
  Condition: `core` present and `core.started`
	* for each *component*s:	
		* `component.enabled = True`
	* for each *Component*s:
		* `component.on_job_activated()`  
* `active = False`  
  Condition: `core` present  
	* for each *component*s:	
		* `component.enabled = False`
	* for each *Component*s:
		* `component.on_job_deactivated()`  

### Invariants

* `active = True` only if
	* `core` present
	* `core.started`


## Component
### Initialization
stand alone by user
### Associations

* `on_add_component(parent)` associates with *Job*  
  Called by: `job.add_component(component)`
* `on_remove_component()`disassociates with *Job*  
  Called by: `job.remove_component(component)`
* `add_device_handle(device_handle)` associates *DeviceHandle*s  
  Called by: user and **decorator**
	* if `component.enabled` then `device_manager.add_handle(device_handle)`  
* `add_event_listener(event_listener)` associates *EventListener*s  
  Called by: user and **decorator**
	* if `component.enabled` then `blackboard.add_listener(event_listener)`

### Transitions

* `enabled = True`  
  Condition: `job` present and `job.active`
	* `blackboard.add_listener(event_listener)`
	* `device_manager.add_handle(device_handler)`
* `enabled = False`
  Condition: `job` present
	* `blackboard.remove_listener(event_listener)`
	* `device_manager.remove_handle(device_handler)`   

## Invariants

* `enabled = True` only if	
	* `job` present
	* `job.active` 
	* `core` present
	* `core.started`


## DeviceHandle
### Initialization
by user with *bind_callback*, *unbind_callback*
### Associations

* fix association with *callback*
* `on_add_handle(device_manager)` associated with *DeviceManager*  
  Called by: `device_manager.add_handle(device_handle)`
* `on_remove_handle(device_manager)` disassociated with *DeviceManager*  
  Called by: `device_manager.remove_handle(device_handle)`
* `on_bind_device(device)` associates with *TF.Device*s  
  Called by: `device_manager._bind_device(dev_id, uid)`
	* `bind_callback(device)`
	* `device_manager.add_device_callback(uid, event_code, device_callback)`
* `on_unbind_device(device)` disassociates with *TF.Device*s  
  Called by: `device_manager._unbind_device(uid)`
	* `unbind_callback(device)`
	* `device_manager.remove_device_callback(uid, event_code, device_callback)`
* `register_callback(event_code, device_callback)` associates with *device_callback*s  
  Called by: user
	* for each *TF.Device*:
		* `device_manager.add_device_callback(uid, event_code, device_callback)` 
* `unregister_callback(event_code, device_callback)` disassociates from *device_callback*s  
  Called by: user
	* for each *TF.Device*:
		* `device_manager.remove_device_callback(uid, event_code, device_callback)` 


## EventListener
### Initialization
by user with *callback*
### Associations

* fix association with *callback*
* `on_add_listener(blackboard)` associated with *Blackboard*  
  Called by: `blackboard.add_listener(event_listener)`
* `on_remove_listener(blackboard)` disassociates with *Blackboard*  
  Called by: `blackboard.remove_listener(event_listener)`
