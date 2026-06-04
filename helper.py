import json
import os
import re
import sys
from datetime import datetime
from typing import List

from dateutil.relativedelta import relativedelta

from constants import WINDOW_OPTIONS_JSON_PATH


def to_gtp_coord(x, y):
  # I를 제외한 GTP 알파벳 열
  cols = "ABCDEFGHJKLMNOPQRST"
  # x는 열(알파벳), y는 행(숫자, 바둑판은 아래서부터 1)
  gtp_x = cols[x]
  gtp_y = 19 - y
  return f"{gtp_x}{gtp_y}"


def parse_gtp_coord(gtp_coord: str):
  cols = "ABCDEFGHJKLMNOPQRST"
  alpha, digit = gtp_coord[0], int(gtp_coord[1:])
  x = cols.index(alpha)
  y = 19 - digit
  return x * 19 + y


def parse_full_katago_string(data):
  # 1. 각 info 항목을 개별적으로 추출할 패턴
  # info move부터 다음 info 전까지 혹은 문자열 끝까지를 하나의 그룹으로 잡습니다.
  info_blocks = re.findall(r"(info move .*?)(?=info move|$)", data)

  parsed_results = []

  for block in info_blocks:
    # 2. 각 블록 내부에서 필요한 수치 추출
    move = re.search(r"move ([A-Z][0-9]+)", block)
    winrate = re.search(r"winrate ([\d\.]+)", block)
    scoreLead = re.search(r"scoreLead ([\-\d\.]+)", block)
    scoreStdev = re.search(r"scoreStdev ([\-\d\.]+)", block)
    visits = re.search(r"visits (\d+)", block)
    pv = re.search(r"pv ([\w\s]+)", block)  # 다음 수순들

    if move and winrate:
      parsed_results.append(
        {
          "move": move.group(1),
          "winrate": float(winrate.group(1)) * 100,  # 퍼센트로 변환
          "scoreLead": float(scoreLead.group(1)) if scoreLead else 0.0,
          "scoreStdev": float(scoreStdev.group(1)) if scoreStdev else 0.0,
          "visits": int(visits.group(1)) if visits else 0,
          "pv": pv.group(1).strip() if pv else "",
        }
      )

  return parsed_results


def get_info_blocks(data: str):
  info_blocks = re.findall(r"(info move .*?)(?=info move|$)", data)
  return info_blocks


def get_best_data(info_blocks):
  best_block = info_blocks[0]
  move = re.search(r"move ([A-Z][0-9]+)", best_block)
  winrate = re.search(r"winrate ([\d\.]+)", best_block)
  scoreLead = re.search(r"scoreLead ([\-\d\.]+)", best_block)
  scoreStdev = re.search(r"scoreStdev ([\-\d\.]+)", best_block)
  visits = re.search(r"visits (\d+)", best_block)
  pv = re.search(r"pv ([\w\s]+)", best_block)  # 다음 수순들

  return {
    "move": move.group(1),
    "winrate": float(winrate.group(1)) * 100,  # 퍼센트로 변환
    "scoreLead": float(scoreLead.group(1)) if scoreLead else 0.0,
    "scoreStdev": float(scoreStdev.group(1)) if scoreStdev else 0.0,
    "visits": int(visits.group(1)) if visits else 0,
    "pv": pv.group(1).strip() if pv else "",
  }


def get_target_data(
  winrate: float, score: float, complexity: float, analyzed_data: List[float]
):
  return [
    winrate + analyzed_data[0],
    score + analyzed_data[1],
    complexity + analyzed_data[2],
  ]


def get_similar_moves(info_blocks, target_data, min_count=100):
  similar_moves = []

  for info in info_blocks:
    move = re.search(r"move ([A-Z][0-9]+)", info)
    winrate = re.search(r"winrate ([\d\.]+)", info)
    scoreLead = re.search(r"scoreLead ([\-\d\.]+)", info)
    scoreStdev = re.search(r"scoreStdev ([\-\d\.]+)", info)
    visits = re.search(r"visits (\d+)", info)
    if not (move and winrate and scoreLead and scoreStdev and visits):
      continue
    if int(visits.group(1)) < min_count:
      continue
    similarity = get_similarity(
      [
        float(winrate.group(1)) * 100,
        float(scoreLead.group(1)),
        float(scoreStdev.group(1)),
      ],
      target_data,
    )
    similar_moves.append((similarity, parse_gtp_coord(move.group(1))))

  similar_moves.sort(reverse=True)
  return similar_moves[:5]


def get_similarity(data, target_data):
  distance = 0
  for i in range(len(target_data)):
    distance += abs(target_data[i] - data[i])
  return 1 / (1 + distance)


def get_real_path(relative_path: str) -> str:
  """실제 .exe 파일 또는 스크립트가 있는 위치를 기준으로 절대 경로를 반환합니다."""
  if getattr(sys, "frozen", False):
    # .exe 파일로 실행된 경우, .exe 파일이 있는 폴더 경로
    base_path = os.path.dirname(sys.executable)
  else:
    # 일반 파이썬 스크립트로 실행된 경우, 현재 파일(helper.py)의 부모 폴더 경로
    base_path = os.path.dirname(os.path.abspath(__file__))
    # 만약 helper.py가 최상위에 있다면 위 코드로 충분하고,
    # 혹시 하위 폴더에 있다면 아래처럼 프로젝트 루트를 잡아야 합니다.
    # base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

  return os.path.join(base_path, relative_path)


def load_json(path: str) -> dict:
  real_path = get_real_path(path)
  if os.path.exists(real_path):
    with open(real_path, "r", encoding="utf-8") as f:
      return json.load(f)
  return {}


def update_json(path, json_data):
  real_path = get_real_path(path)
  try:
    with open(real_path, "w", encoding="utf-8") as f:
      json.dump(json_data, f, indent=4)
    return True

  except Exception as e:
    print(e)
    return False


def get_range_by_winrate(winrate: float):
  margin = 10.0 - 7.0 * ((winrate - 50) / 50) ** 2
  margin = max(margin, 2.0)
  return (winrate - margin, winrate + margin)


def get_range_by_score(score: float):
  abs_score = abs(score)
  margin = 1.5 + (abs_score * 0.2)
  return (score - margin, score + margin)


def get_range_by_move_number(move_number: int):
  margin = 10
  return (move_number - margin, move_number + margin)


def get_color_by_score(score: float):
  if score < 50:
    return "#D32F2F"
  if score < 60:
    return "#E67E22"
  if score < 70:
    return "#F1C40F"
  if score < 80:
    return "#2ECC71"
  if score < 90:
    return "#1ABC9C"
  return "#00D2FF"


def normalize_delta_winrate(delta_winrate: float):
  if delta_winrate > 0:
    return 100
  if delta_winrate < -10:
    return 0

  score = round(100 + (delta_winrate * 10), 1)
  return score


def normalize_delta_score(delta_score: float):
  if delta_score > 0:
    return 100
  if delta_score < -2:
    return 0

  score = round(100 + (delta_score * 50), 1)
  return score


def normalize_bluespot_score(bluespot_ratio: float):
  score = round(bluespot_ratio * 1.5, 1)
  return min(score, 100)


def get_past_num_date(years: int, months: int) -> str:
  now = datetime.now()
  past_date = now - relativedelta(years=years, months=months)
  refined = past_date.strftime("%Y%m%d")
  return int(refined)


def close_window(key: str):
  window_option_json = load_json(WINDOW_OPTIONS_JSON_PATH)
  if key == "all":
    for window in window_option_json.keys():
      window_option_json[window] = False

  if key in window_option_json.keys():
    window_option_json[key] = False

  update_json(WINDOW_OPTIONS_JSON_PATH, window_option_json)
  return
