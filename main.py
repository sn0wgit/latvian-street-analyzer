from typing import Optional
from InquirerPy import inquirer
import requests
import re
from bs4 import BeautifulSoup

WIKIPEDIA_HEADERS = {
	'Accept-Encoding': 'gzip',
	'User-Agent': 'LSA_Bot/20250903 (https://github.com/sn0wgit/latvian-street-analyzer; iaroslav.viazmitin@edu.rtu.lv)'
}

class CityStreetData:
	def __init__(self, street_count: int, street_list: list[str]):
		self.street_count = street_count
		self.street_list = street_list

	def set_kadastrs_link(self, kadastrs_link: str):
		self.kadastrs_link = kadastrs_link

	def get_street_count(self):
		return self.street_count

	def get_street_list(self):
		return self.street_list

	def get_kadastrs_link(self) -> str | None:
		if hasattr(self, 'kadastrs_link'):
			return self.kadastrs_link
		return None
		
continueWork = True

def entry_point():
	CITIES_STREETS_LINK = "https://lv.wikipedia.org/wiki/Kategorija:Latvijas_pils%C4%93tu_ielu_uzskait%C4%ABjumi"
	cities_streets_link_content = requests.get(CITIES_STREETS_LINK, headers=WIKIPEDIA_HEADERS)
	cities_streets_soup = BeautifulSoup(cities_streets_link_content.content, "html.parser")
	print("32", cities_streets_soup)

	def get_all_cities() -> dict[str, str]:
		city_list: dict[str, str] = {"*Visas pilsētas*": "*"}
		soup_city_tags = cities_streets_soup.select(".mw-category-group ul li a")
		for city in soup_city_tags:
			city_name = city.text
			if not city.text.endswith("jumi"):
				if not city.text.startswith("Rīga"):
					city_list[city_name] = city["href"] #type: ignore
				else:
					city_list[city_name] = ""
		return city_list

	def get_streets_wikipedia(city_value: str, vibechecking: bool) -> CityStreetData:
		if city_value == "": # Rīgas gadījums ar vairākām saitēm
			whole_riga_street_list = []
			riga_regions_links = [
				"/wiki/R%C4%ABgas_Centra_rajona_ielu_uzskait%C4%ABjums",
				"/wiki/R%C4%ABgas_Kurzemes_rajona_ielu_uzskait%C4%ABjums", 
				"/wiki/R%C4%ABgas_Latgales_priek%C5%A1pils%C4%93tas_ielu_uzskait%C4%ABjums", 
				"/wiki/R%C4%ABgas_Vidzemes_priek%C5%A1pils%C4%93tas_ielu_uzskait%C4%ABjums", 
				"/wiki/R%C4%ABgas_Zemgales_priek%C5%A1pils%C4%93tas_ielu_uzskait%C4%ABjums", 
				"/wiki/R%C4%ABgas_Zieme%C4%BCu_rajona_ielu_uzskait%C4%ABjums"
			]
			street_count = 0

			for region_link in riga_regions_links:
				riga_temp_data = get_streets_wikipedia(region_link, vibechecking)
				for street in riga_temp_data.get_street_list():
					whole_riga_street_list.append(street)
				street_count += riga_temp_data.get_street_count()

			riga_data = CityStreetData(street_count, whole_riga_street_list)
			riga_data.set_kadastrs_link("https://www.kadastrs.lv/varis/100003003")

			return riga_data

		else:
			selected_city_link = "https://lv.wikipedia.org"+city_value
			print(selected_city_link)
			city_streets_content = requests.get(selected_city_link, headers=WIKIPEDIA_HEADERS)
			city_streets_soup = BeautifulSoup(city_streets_content.content, "html.parser")

			city_description = city_streets_soup.select_one(".mw-content-ltr.mw-parser-output > p").text.replace("\n", "") #type: ignore
			city_street_count: int = int(re.search(r"(\d+)", city_description).group(0)) #type: ignore
			if not vibechecking:
				street_count_confirmation = inquirer.confirm(
					wrap_lines=True,
					message=f'"{city_description}"'+"\n"+\
					f'Vai te ir {city_street_count} ielu?'
				).execute()
				if not street_count_confirmation:
					city_street_count = int(inquirer.number(message="Ievadiet ielu skaitu:").execute())

			city_street_selection = city_streets_soup.select(".mw-parser-output ul li > a")
			city_street_list: list[str] = []
			for street in city_street_selection:
				if (
					"iela" in street.text\
					or "līnija" in street.text\
					or "prospekts" in street.text\
					or "bulvāris" in street.text\
					or "gatve" in street.text\
					or "krastmala" in street.text\
					or "laukums" in street.text\
					or "dambis" in street.text\
					or "skvērs" in street.text\
					or "gāte" in street.text\
					or "šoseja" in street.text\
					or "maģistrāle" in street.text\
					or "aleja" in street.text\
					or "taka" in street.text\
					or "sēta" in street.text\
					or "ostmala" in street.text\
					or "sala" in street.text\
					or "ceļš" in street.text\
					or "dārzs" in street.text\
					or "valnis" in street.text\
					or "tirgus" in street.text\
					or "parks" in street.text\
					or "mols" in street.text\
					or "stūris" in street.text\
					or "pļava" in street.text\
					or "promenāde" in street.text\
					or "Skvērs" in street.text\
					or "rajons" in street.text\
				) and not street.text.endswith(" ielas")\
					and not street.text.endswith("priekšpilsēta")\
					and street.text != "Mazsalaca":
					city_street_list.append(street.text)

			if city_street_count == 0 or vibechecking:
				city_street_count = len(city_street_list)

			city_street_data = CityStreetData(city_street_count, city_street_list)

			kadastrs_link_tag = city_streets_soup.select_one('.references-small ol li [href*="kadastrs.lv"]')
			if kadastrs_link_tag is not None:
				city_street_data.set_kadastrs_link(kadastrs_link_tag["href"]) #type: ignore

			return city_street_data

	def get_streets_kadastrs(city_value: str, vibechecking: bool, reserved_kadastrs_link: Optional[str] = None) -> CityStreetData:
		kadastrs_link: str = ""
		if reserved_kadastrs_link is not None:
			kadastrs_link = re.search(r"https?:\/\/(?:www.)?kadastrs.lv\/varis\/\d*", reserved_kadastrs_link).group(0) #type: ignore
		else:
			kadastrs_link = inquirer.text(
				"Diemžēl, neizdevās automātiski atrast saiti uz kadastrs.lv. Lūdzu, ievietojiet saiti:"
			).execute()

		if not vibechecking:
			while not inquirer.confirm(f'Vai saite "{kadastrs_link}" ir korekta?').execute():
				temp_link = inquirer.text(
					"Lūdzu, ievietojiet korektu saiti:"
				).execute()
				if "kadastrs.lv" in temp_link:
					kadastrs_link = re.search(r"https?:\/\/(?:www.)?kadastrs.lv\/varis\/\d*", temp_link).group(0) #type: ignore
				elif re.search(r"\d*", temp_link) is not None:
					kadastrs_link = "https://www.kadastrs.lv/varis/"+re.search(r"\d*", temp_link).group(0) #type: ignore
				else:
					kadastrs_link = temp_link

		kadastrs_street_list: list[str] = []
		kadastrs_link+="?sort=name&sort_direction=asc&sub_type=street&type=city&page="
		is_not_last_page = True
		kadastrs_page_count = 0
		kadastrs_current_page = 0

		while is_not_last_page:
			kadastrs_current_page += 1

			kadastrs_content = requests.get(kadastrs_link+str(kadastrs_current_page))
			kadastrs_soup = BeautifulSoup(kadastrs_content.content, "html.parser")

			single_page: bool = not kadastrs_soup.select_one(".pagination")

			if not single_page:
				if kadastrs_current_page == 1:
					kadastrs_page_count = int(kadastrs_soup.select_one('.pagination a:nth-last-child(2)').text) #type: ignore

				print(f"{kadastrs_current_page}/{kadastrs_page_count}", end="\r")

			kadastrs_soup_streets = kadastrs_soup.select("td.full_name")

			for kadastrs_soup_street in kadastrs_soup_streets:
				kadastrs_street_list.append(kadastrs_soup_street.text.split(", ")[0])

			disabled_next_page = kadastrs_soup.select_one(".pagination> .disabled.next_page")
			if disabled_next_page or single_page:
				is_not_last_page = False

		return CityStreetData(len(kadastrs_street_list), kadastrs_street_list)

	def match_streets(wikipedia_street_data: CityStreetData, kadastrs_street_data: CityStreetData, vibechecking: bool):
		# step one: compare street count
		wikipedia_street_count = wikipedia_street_data.get_street_count()
		kadastrs_street_count = kadastrs_street_data.get_street_count()

		if wikipedia_street_count != kadastrs_street_count:
			print(f"Wikipedia: {wikipedia_street_count}, kadastrs.lv: {kadastrs_street_count}")
			print("Ierakstītais skaits nesakrīt!")

		#step two: compare street names
		wikipedia_street_list = wikipedia_street_data.get_street_list()
		kadastrs_street_list = kadastrs_street_data.get_street_list()

		name_comparison_exception_count = 0
		def exception_counter() -> str:
			if name_comparison_exception_count == 0:
				return "Nav nesakritību..."
			else:
				return f"{name_comparison_exception_count} nesakritību..."

		wikipedia_street_set = set(wikipedia_street_list)
		kadastrs_street_set = set(kadastrs_street_list)

		name_comparison_exception_count = len(wikipedia_street_set.symmetric_difference(kadastrs_street_set)) #AΔB
		logfiletext = ""

		if name_comparison_exception_count == 0:
			print("Nav nesakritību!")
			logfiletext = "Nav nesakritību!"
		else:
			wikipedia_unique_streets = sorted(list(wikipedia_street_set - kadastrs_street_set))
			kadastrs_unique_streets = sorted(list(kadastrs_street_set - wikipedia_street_set))
			print(f"{name_comparison_exception_count} nesakritību.\n\nLiekas ielas:")
			logfiletext += f"{name_comparison_exception_count} nesakritību.\n\nLiekas ielas:"
			if len(kadastrs_unique_streets) != 0:
				print("* Vikipēdijā:")
				logfiletext += "* Vikipēdijā:"
				for wikipedia_street_name in wikipedia_unique_streets:
					print('"', wikipedia_street_name, '"', sep="")
					logfiletext += "\n"+f'"{wikipedia_street_name}"'
			if len(kadastrs_unique_streets) != 0:
				print("\n\n* Kadastrā:")
				logfiletext += "\n\n* Kadastrā:"
				for kadastrs_street_name in kadastrs_unique_streets:
					print('"', kadastrs_street_name, '"', sep="")
					logfiletext += "\n"+f'"{kadastrs_street_name}"'
			if not vibechecking:
				doSaveLogs = inquirer.confirm(message="Vai vēlies saglabāt šos datus log.txt failā?").execute()
				if doSaveLogs:
					with open("log.txt", "w") as logfile:
						logfile.write(logfiletext)
		return logfiletext+"\n\n\n"
			
	def job(city_selection: str, vibechecking: bool):
		city_streets_wikipedia = get_streets_wikipedia(city_option_list[city_selection], vibechecking)
		city_streets_kadastrs: CityStreetData
		if city_streets_wikipedia.get_kadastrs_link() is not None:
			city_streets_kadastrs = get_streets_kadastrs(city_option_list[city_selection], vibechecking, city_streets_wikipedia.get_kadastrs_link())
		else:
			city_streets_kadastrs = get_streets_kadastrs(city_option_list[city_selection], vibechecking)

		return match_streets(city_streets_wikipedia, city_streets_kadastrs, vibechecking)
		
	city_option_list: dict[str, str] = get_all_cities()

	city_selection = inquirer.select(
		message="Izvēlies pilsētu:",
		choices=list(city_option_list.keys()),
		max_height=20
	).execute()

	if city_option_list[city_selection] == "*":
		output = ""
		for city_iter in list(city_option_list.keys()):
			if city_iter != "*Visas pilsētas*":
				print(f"=== {city_iter} ===")
				output += city_iter + job(city_iter, True)
		doSaveLogs = inquirer.confirm(message="Vai vēlies saglabāt šos datus log.txt failā?").execute()
		if doSaveLogs:
			with open("log.txt", "w") as logfile:
				logfile.write(output)
	else:
		job(city_selection, False)

if __name__ == "__main__":
	print("=== LSA (Latvian Street Analyzer) ===\n")
	while continueWork:
		entry_point()
		continueWork = inquirer.confirm(message="Vai vēlies turpināt?").execute()