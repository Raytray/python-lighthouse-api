# 
#  lighthouse.py
#  Python Lighthouse API
#
#  Lighthouse simple hosted issue tracking, bug tracking, and project
#	management software.
#
#  They also have an XML-based API for working with your projects
#  
#  http://lighthouseapp.com
#  http://lighthouseapp.com/api
#
#  Created by Clinton Ecker on 2009-01-31.
#  Copyright 2009 Clint Ecker. All rights reserved.
# 
import urllib
import os.path
import pprint
from xmltodict import xmltodict
from dateutil.parser import *
from dateutil.tz import *


class Lighthouse(object):
	"""The main lighthouse object for managing the connection"""
	
	def __init__(self, token=None, url=None):
		super(Lighthouse, self).__init__()
		self.token = token
		self.url = url
		self.projects = []
	
	def _datetime(self, data):
		"""Returns a datetime object representation of string
		
		>>> lh = Lighthouse()
		>>> lh._datetime('2008-09-25T20:04:13+01:00')
		datetime.datetime(2008, 9, 25, 20, 4, 13, tzinfo=tzoffset(None, 3600))
		>>> lh._datetime('2009-01-26T16:47:00-08:00')
		datetime.datetime(2009, 1, 26, 16, 47, tzinfo=tzoffset(None, -28800))
		>>> lh._datetime('2009-01-31T15:42:18-08:00')
		datetime.datetime(2009, 1, 31, 15, 42, 18, tzinfo=tzoffset(None, -28800))
		"""
		return parse(data)
	
	def _integer(self, data):
		"""Returns a literal integer object from a string"
		
		>>> lh = Lighthouse()
		>>> lh._integer('10')
		10
		>>> lh._integer('True')
		Traceback (most recent call last):
		...
		ValueError: invalid literal for int() with base 10: 'True'
		>>> lh._integer('23.5')
		Traceback (most recent call last):
		...
		ValueError: invalid literal for int() with base 10: '23.5'
		"""""
		if data:
			return int(data,10)
		else:
			return None
	
	def _boolean(self, data):
		"""Returns True or False from a string
		
		>>> lh = Lighthouse()
		>>> lh._boolean('1')
		True
		>>> lh._boolean('2')
		False
		>>> lh._boolean('true')
		True
		>>> lh._boolean('True')
		True
		>>> lh._boolean('false')
		False
		>>> lh._boolean('False')
		False
		>>> lh._boolean(1)
		True
		>>> lh._boolean(2)
		False
		>>> lh._boolean(0)
		False
		"""
		if data == 'true' or data == 'True' or data == '1' or data == 1:
			return True
		else:
			return False
	
	def _string(self, data):
		"""Returns a...uh string from a bit of data
		
		>>> lh = Lighthouse()
		>>> lh._string('lol')
		'lol'
		>>> lh._string(1)
		'1'
		>>> lh._string(True)
		'True'
		>>> lh._string('2008-09-25T20:04:13+01:00')
		'2008-09-25T20:04:13+01:00'
		>>> lh._datetime('2008-09-25T20:04:13+01:00')
		datetime.datetime(2008, 9, 25, 20, 4, 13, tzinfo=tzoffset(None, 3600))
		>>> lh._string(_)
		'2008-09-25 20:04:13+01:00'
		"""
		return str(data)
	
	def _nil(self, data):
		"""Returns None
		
		>>> lh = Lighthouse()
		>>> lh._nil('lol')
		>>> lh._nil(1)
		>>> lh._nil(True)
		>>> lh._nil('2008-09-25T20:04:13+01:00')
		>>> lh._datetime('2008-09-25T20:04:13+01:00')
		datetime.datetime(2008, 9, 25, 20, 4, 13, tzinfo=tzoffset(None, 3600))
		>>> lh._nil(_)
		"""
		return None
	
	def _get_data(self, path):
		"""Takes a path, joins it with the project's URL and grabs that 
		resource's XML data
		
		>>> lh = Lighthouse()
		>>> lh._get_data('projects.xml')
		Traceback (most recent call last):
		...
		ValueError: Please set url properly
		>>> lh.url = 'http://ars.lighthouseapp.com'
		>>> lh._get_data('projectx.xml')
		Traceback (most recent call last):
		...
		ExpatError: mismatched tag: line 31, column 4
		>>> lh.url = 'http://example.com'
		>>> lh._get_data('projects.xml')
		Traceback (most recent call last):
		...
		ExpatError: mismatched tag: line 31, column 4
		"""
		if self.url != None:
			endpoint = os.path.join(self.url, path)
			rh = urllib.urlopen(endpoint)
			data = rh.read()
			return self._parse_xml(data)
		else:
			raise ValueError('Please set url properly')

	def _parse_xml(self, xmldata):
		return xmltodict(xmldata)
	
	def _parse_field(self, field):
		field_type = None
		field_name = None
		field_attributes = None
		converter = None
		
		attributes = field.get('attributes', {})
		field_value = field.get('cdata', None)
		field_name = field.get('name', None)
		
		if attributes:
			field_type = attributes.get('type', None)

		if field_type:
			converter = getattr(self,'_'+field_type)
			field_value = converter(field_value)
		
		return (field_name, field_value, field_type)
	
	def init(self):
		"""Pulls in all the projects available and populates them with
		their properties"""
		self.get_projects()
		for p in self.projects:
			self.get_tickets(p)
		return
		
	def get_projects(self):
		"""Retrieves all available projects
		
		>>> lh = Lighthouse()
		>>> lh.url = 'http://ars.lighthouseapp.com'
		>>> lh.init()
		>>> project = lh.projects[0]
		>>> len(lh.projects)
		1
		>>> project.name
		'Ars Technica 5.0'
		"""
		path = Project.endpoint
		project_list = self._get_data(path)
		projects = []
		for project in project_list['children']:
			p_obj = Project()
			for field in project['children']:
				field_name, field_value, field_type = self._parse_field(field)
				p_obj.__setattr__(field_name.replace('-', '_'), field_value)
			projects.append(p_obj)
		self.projects = projects
		return
	
	def get_tickets(self, project):
		"""Retrieves all the tickets in a project
		
		>>> lh = Lighthouse()
		>>> lh.url = 'http://ars.lighthouseapp.com'
		>>> lh.init()
		>>> project = lh.projects[0]
		>>> lh.get_tickets(project)
		>>> lh.get_tickets(123)
		Traceback (most recent call last):
		...
		TypeError: Project must be instance of Project object
		>>> lh.get_tickets('project')
		Traceback (most recent call last):
		...
		TypeError: Project must be instance of Project object
		"""
		if isinstance(project, Project):
			path = Ticket.endpoint % (project.id)
			ticket_list = self._get_data(path)
			tickets = []
			for ticket in ticket_list['children']:
				t_obj = Ticket()
				for field in ticket['children']:
					field_name, field_value, field_type = \
						self._parse_field(field)
					t_obj.__setattr__(field_name.replace('-', '_'),\
						field_value)
				tickets.append(t_obj)
			project.tickets = tickets
			return
		else:
			raise TypeError('Project must be instance of Project object')
				
class Ticket(object):
	"""Tickets are individual issues or bugs"""
	
	endpoint = 'projects/%d/tickets.xml'
	
	def __init__(self):
		super(Ticket, self).__init__()
		
	def __repr__(self):
		if self.title:
			return "Ticket: %s" % (self.title,)
		else:
			return "Ticket: Unnamed"

class Project(object):
	"""Projects contain milestones, tickets, messages, and changesets"""
	
	endpoint = 'projects.xml'
	
	def __init__(self):
		super(Project, self).__init__()
		self.tickets = []
		self.milestones = []
		self.messages = []

	def __repr__(self):
		if self.name:
			return "Project: %s" % (self.name,)
		else:
			return "Project: Unnamed"

class Milestone(object):
	"""Milestones reference tickets"""
	def __init__(self, arg):
		super(Milestone, self).__init__()
		self.arg = arg
		
class Message(object):
	"""Messages are notes"""
	def __init__(self, arg):
		super(Message, self).__init__()
		self.arg = arg
		
class User(object):
	"""A user"""
	def __init__(self, arg):
		super(User, self).__init__()
		self.arg = arg
		
if __name__ == "__main__":
	import doctest
	doctest.testmod(optionflags=doctest.IGNORE_EXCEPTION_DETAIL)