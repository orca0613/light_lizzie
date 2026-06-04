import copy
from typing import Dict, List


def get_neighbors(loc: int) -> List[int]:
  y, x = loc // 19, loc % 19
  neighbors = []
  if y > 0:
    neighbors.append(loc)
  if y < 18:
    neighbors.append(loc)
  if x > 0:
    neighbors.append(loc - 1)
  if x < 18:
    neighbors.append(loc + 1)
  return neighbors


def get_dead_group(stones: Dict, loc: int, oppo_color: str) -> List[int]:
  group = []
  visited = set()
  stack = [loc]

  while stack:
    loc = stack.pop()
    if loc not in stones:
      return []
    if (loc < 0) or (loc > 360) or (loc in visited) or stones[loc] == oppo_color:
      continue
    visited.add(loc)
    group.append(loc)
    stack += get_neighbors(loc)

  return group


def clear_ko_spot(stones: Dict):
  new_stones = copy.deepcopy(stones)
  for loc in new_stones.keys():
    if new_stones[loc] == "K":
      new_stones.pop(loc)
      break

  return new_stones


def remove_dead_group(stones: Dict, dead_group: List[int]):
  for loc in dead_group:
    if loc in stones:
      stones.pop(loc)
  return stones


def play_move(stones: Dict, loc: int, color: str):
  if loc < 0 or loc > 360:
    return stones
  if loc in stones:
    return stones

  new_stones = clear_ko_spot(stones)
  new_stones[loc] = color
  oppo_color = "W" if color == "B" else "B"
  killed: List[int] = []
  neighbors = get_neighbors(loc)
  for neighbor in neighbors:
    if neighbor not in new_stones or new_stones[neighbor] == color:
      continue
    killed += get_dead_group(new_stones, neighbor, color)
  suicide_group = get_dead_group(new_stones, loc, oppo_color)
  new_stones = remove_dead_group(new_stones, killed)
  if not len(suicide_group):
    return new_stones
  if not len(killed):
    return stones
  if len(killed) == 1 and len(suicide_group) == 1:
    ko_spot = killed[0]
    new_stones[ko_spot] = "K"
  return new_stones
