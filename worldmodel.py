import entities
import pygame
import ordered_list
import actions
import occ_grid
import point
import save_load
import image_store

PROPERTY_KEY = 0

BGND_KEY = 'background'
BGND_NUM_PROPERTIES = 4
BGND_NAME = 1
BGND_COL = 2
BGND_ROW = 3

class WorldModel:
   def __init__(self, num_rows, num_cols, background):
      self.background = occ_grid.Grid(num_cols, num_rows, background)
      self.num_rows = num_rows
      self.num_cols = num_cols
      self.occupancy = occ_grid.Grid(num_cols, num_rows, None)
      self.entities = []
      self.action_queue = ordered_list.OrderedList()
   def within_bounds(self, pt):
      return (pt.x >= 0 and pt.x < self.num_cols and
         pt.y >= 0 and pt.y < self.num_rows)
   def is_occupied(self, pt):
      return (self.within_bounds(pt) and
         occ_grid.get_cell(self.occupancy, pt) != None)
   def find_nearest(self, pt, type):
      oftype = [(e, distance_sq(pt, e.get_position()))
         for e in self.entities if isinstance(e, type)]
      return nearest_entity(oftype)
   def add_entity(self, entity):
      pt = entity.get_position()
      if self.within_bounds(pt):
         old_entity = occ_grid.get_cell(self.occupancy, pt)
         if old_entity != None:
            old_entity.clear_pending_actions()
         occ_grid.set_cell(self.occupancy, pt, entity)
         self.entities.append(entity)
   def move_entity(self, entity, pt):
      tiles = []
      if self.within_bounds(pt):
         old_pt = entity.get_position()
         occ_grid.set_cell(self.occupancy, old_pt, None)
         tiles.append(old_pt)
         occ_grid.set_cell(self.occupancy, pt, entity)
         tiles.append(pt)
         entity.set_position(pt)
      return tiles
   def remove_entity(self, entity):
      self.remove_entity_at(entity.get_position())
   def remove_entity_at(self, pt):
      if (self.within_bounds(pt) and
         occ_grid.get_cell(self.occupancy, pt) != None):
         entity = occ_grid.get_cell(self.occupancy, pt)
         entity.set_position(point.Point(-1, -1))
         self.entities.remove(entity)
         occ_grid.set_cell(self.occupancy, pt, None)
   def schedule_action(self, action, time):
      self.action_queue.insert(action, time)
   def unschedule_action(self, action):
      self.action_queue.remove(action)
   def update_on_time(self, ticks):
      tiles = []

      next = self.action_queue.head()
      while next and next.ord < ticks:
         self.action_queue.pop()
         tiles.extend(next.item(ticks))  # invoke action function
         next = self.action_queue.head()

      return tiles
   def get_background_image(self, pt):
      if self.within_bounds(pt):
         entity = occ_grid.get_cell(self.background, pt)
         return entity.get_image()
   def get_background(self, pt):
      if self.within_bounds(pt):
         return occ_grid.get_cell(self.background, pt)
   def set_background(self, pt, bgnd):
      if self.within_bounds(pt):
         occ_grid.set_cell(self.background, pt, bgnd)
   def get_tile_occupant(self, pt):
      if self.within_bounds(pt):
         return occ_grid.get_cell(self.occupancy, pt)
   def get_entities(self):
      return self.entities

   def save_world(self, file):
      self.save_entities(file)
      self.save_background(file)
   def save_entities(self, file):
      for entity in self.get_entities():
         file.write(entity.entity_string() + '\n')
   def save_background(self, file):
      for row in range(0, self.num_rows):
         for col in range(0, self.num_cols):
            entity = self.get_background(point.Point(col, row))
            file.write('background ' +
               entity.get_name() +
               ' ' + str(col) + ' ' + str(row) + '\n')      
   def load_world(self, images, file, run=False):
      for line in file:
         properties = line.split()
         if properties:
            if properties[PROPERTY_KEY] == BGND_KEY:
               self.add_background(properties, images)
            else:
               self.add_entity2(properties, images, run)
   def add_background(self, properties, i_store):
      if len(properties) >= BGND_NUM_PROPERTIES:
         pt = point.Point(int(properties[BGND_COL]), int(properties[BGND_ROW]))
         name = properties[BGND_NAME]
         self.set_background(pt,
            entities.Background(name, image_store.get_images(i_store, name)))
   def add_entity2(self, properties, i_store, run):
      new_entity = save_load.create_from_properties(properties, i_store)
      if new_entity:
         self.add_entity(new_entity)
         if run:
            self.schedule_entity(new_entity, i_store)
   def schedule_entity(self, entity, i_store):
      if isinstance(entity, entities.MinerNotFull):
         actions.schedule_miner(self, entity, 0, i_store)
      elif isinstance(entity, entities.Vein):
         actions.schedule_vein(self, entity, 0, i_store)
      elif isinstance(entity, entities.Ore):
         actions.schedule_ore(self, entity, 0, i_store)         

#these functions help above methods

def nearest_entity(entity_dists):
   if len(entity_dists) > 0:
      pair = entity_dists[0]
      for other in entity_dists:
         if other[1] < pair[1]:
            pair = other
      nearest = pair[0]
   else:
      nearest = None

   return nearest


def distance_sq(p1, p2):
   return (p1.x - p2.x)**2 + (p1.y - p2.y)**2


