#!/usr/bin/env python
#

from PlanetWars import PlanetWars

turns_remaining = 201

def DoTurn(pw):

  global turns_remaining
  turns_remaining = turns_remaining - 1

  my_planets = pw.MyPlanets()
  enemy_planets = pw.EnemyPlanets()
  neutral_planets = pw.NeutralPlanets()

  my_fleets = pw.MyFleets()
  enemy_fleets = pw.EnemyFleets()

  # sanity checking
  if len(my_planets) == 0 or len(enemy_planets) == 0:
    return

  my_ships = sum(map(lambda p: p.NumShips(), my_planets)) + sum(map(lambda f: f.NumShips(), my_fleets))
  enemy_ships = sum(map(lambda p: p.NumShips(), enemy_planets)) + sum(map(lambda f: f.NumShips(), enemy_fleets))
  
  if my_ships > enemy_ships * 1.5 and turns_remaining < 170:
    berserker = True
  else:
    berserker = False

  if berserker == False:
    potential_targets = enemy_planets + neutral_planets
  else:
    potential_targets = enemy_planets


  if berserker == False and len(my_planets) > 1:
    under_attack = find_under_attack(my_planets, enemy_fleets)
    if len(under_attack) >= 1:
      for needs_defending in sorted(under_attack, key = lambda d: d["turns"]):
        defender = needs_defending["defender"]
        attacker = needs_defending["attacker"]
        ships_incoming = needs_defending["incoming"]
        ships_available = needs_defending["available"]
        turns_remaining = needs_defending["turns"]

        # Planet 0 will be the defender planet
        nearest_backup = sorted(my_planets, key = lambda p: pw.Distance(defender.PlanetID(), p.PlanetID()))[1]

        ships_required = ships_incoming - ships_available + (turns_remaining * defender.GrowthRate())

        # cant do it
        if nearest_backup.NumShips() - 1 <= ships_required or pw.Distance(nearest_backup.PlanetID(), defender.PlanetID()) < turns_remaining:
          continue

        pw.IssueOrder(nearest_backup.PlanetID(), defender.PlanetID(), ships_required)
        nearest_backup = pw.GetPlanet(nearest_backup.PlanetID())
        nearest_backup.RemoveShips(ships_required)

  attacked_this_turn = []

  for source in sorted(pw.MyPlanets(), key = lambda p: p.NumShips(), reverse = True):

    # subtract enemy attackers from source planet's current population
    for enemy_in_flight in enemy_fleets:
      if enemy_in_flight.DestinationPlanet() == source.PlanetID():
        source.RemoveShips(enemy_in_flight.NumShips())

    targets = []
    
    for target in potential_targets:

      # don't send more ships if we are already attacking this planet
      # unless we are in endgame mode
      if berserker == False:
        if target.PlanetID() in map(lambda f: f.DestinationPlanet(), my_fleets):
          continue
      
        if target.PlanetID() in map(lambda p: p.PlanetID(), attacked_this_turn):
          continue
  
      target_distance = pw.Distance(source.PlanetID(), target.PlanetID())
      target_current_population = target.NumShips()
      target_growth_rate = target.GrowthRate()

      # neutral planets don't grow from turn to turn
      if target in neutral_planets:
        target_future_population = target_current_population
      else:
        target_future_population = target_current_population + (target_growth_rate * target_distance)

      # add any enemy attackers to target planet's future population
      for enemy_in_flight in enemy_fleets:
        if enemy_in_flight.DestinationPlanet() == target.PlanetID():
          if target in neutral_planets:
            target_future_population = target_current_population + (target_growth_rate * (enemy_in_flight.TurnsRemaining() - target_distance))
          else:
            target_future_population = target_future_population + enemy_in_flight.NumShips()

      # calculate the value of attacking this planet
      value = (turns_remaining * target_growth_rate - target_future_population) / (target_distance * 2)
      targets.append({"planet":target, "value":value, "fleet_required":target_future_population})

    if berserker == False:
      targets.sort(key = lambda t: t["value"], reverse = True)
    else:
      targets.sort(key = lambda t: t["fleet_required"], reverse = True)

    # send fleets from source planet (if we have enough ships available)
    for target in targets:
      fleet_size = target["fleet_required"] + 1
      if source.NumShips() > fleet_size and fleet_size > 0:
        pw.IssueOrder(source.PlanetID(), target["planet"].PlanetID(), fleet_size)
        source.RemoveShips(fleet_size)
        attacked_this_turn.append(target["planet"])
      else:
        continue

def find_under_attack(my_planets, enemy_fleets):
  
  under_attack = []
    
  for defender in my_planets:
    for attacker in enemy_fleets:
      available_ships = defender.NumShips() + (defender.GrowthRate() * attacker.TurnsRemaining())
      if attacker.DestinationPlanet() == defender.PlanetID() and attacker.NumShips() > available_ships:
        under_attack.append({"defender":defender, "attacker":attacker, "turns":attacker.TurnsRemaining(), "incoming":attacker.NumShips(), "available":available_ships})

  return under_attack
  

def main():
  map_data = ''
  while(True):
    current_line = raw_input()
    if len(current_line) >= 2 and current_line.startswith("go"):
      pw = PlanetWars(map_data)
      DoTurn(pw)
      pw.FinishTurn()
      map_data = ''
    else:
      map_data += current_line + '\n'


if __name__ == '__main__':
  try:
    import psyco
    psyco.full()
  except ImportError:
    pass
  try:
    main()
  except KeyboardInterrupt:
    print 'ctrl-c, leaving ...'
