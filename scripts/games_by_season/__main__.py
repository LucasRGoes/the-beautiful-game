"""Fetches list of played games over the desired Brasileirão season."""

import re
import json
import time
import argparse
from datetime import datetime

import requests
from bs4 import BeautifulSoup


AJAX = 'https://www.srgoool.com.br/call'
URL = 'https://www.srgoool.com.br/classificacao/Brasileirao/Serie-A/{season}'
USER_AGENT = 'BeautifulGameBot/0.1'


def get_games_by_season(season: int):
	games = []

	html = requests.get(
		URL.format(season=season),
		headers={'user-agent': USER_AGENT}
	)
	soup = BeautifulSoup(html.text, 'html5lib')

	# find the request id to be used on the AJAX requests
	request_id = None
	for script in soup.find_all('script', attrs={'type': 'text/javascript'}):

		m = re.search('id_fase\s?=\s?"([0-9]+)"', script.next)
		if m:
			request_id = int(m.group(1))
			break

	# find the number of weeks of the chosen season
	res = requests.post(
		AJAX,
		data={'id_fase': request_id},
		headers={'user-agent': USER_AGENT},
		params={'ajax': 'get_rodada_info'}
	).json()
	number_weeks = int(res['rodadas']['rodada_max'])

	# for each week of the season, fetch its games
	for week in range(1, number_weeks + 1):

		# sleeping between requests as a good scraping practice
		time.sleep(1)

		res = requests.post(
			AJAX,
			data={'id_fase': request_id, 'rodada': week},
			headers={'user-agent': USER_AGENT},
			params={'ajax': 'get_ranking2'}
		).json()

		# parsing response to create game
		print('Parsing week {}...'.format(week))
		for game in res['list']:
			p_game = {}

			game_date = game.get('data')
			game_time = game.get('hora')

			p_game['week'] = week

			p_game['date_time'] = datetime.strptime(
				'{0}/{1} {2}'.format(game_date, season, game_time),
				'%d/%m/%Y %Hh%M'
			).isoformat()

			p_game['home_team'] = game.get('clubem')
			p_game['away_team'] = game.get('clubev')
			p_game['home_goals'] = int(game.get('placarm_tn'))
			p_game['away_goals'] = int(game.get('placarv_tn'))

			p_game['stadium'] = game.get('estadio')
			p_game['city'] = game.get('cidade')

			games.append(p_game)

	return games


if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		description=('Fetches list of played games over the desired'
					 ' Brasileirão season.')
	)

	parser.add_argument(
		'--output', dest='output', type=str, default='./games_by_season.json',
		help='the path for the output'
	)
	parser.add_argument(
		'fseason', metavar='YYYY', type=int, help='the first desired season')
	parser.add_argument(
		'lseason', metavar='ZZZZ', type=int, help='the last desired season')

	my_args = parser.parse_args()

	for season in range(my_args.fseason, my_args.lseason + 1):
		print('Fetching data from season {}...'.format(season))
		games = get_games_by_season(season)

		print('Writing to file...')
		with open(my_args.output.format(season), 'w', encoding='utf8') as file:
			json.dump(games, file, ensure_ascii=False, indent=4)
