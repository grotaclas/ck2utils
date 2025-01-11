#!/usr/bin/env python3
import math
import os
import sys
import re
import numpy as np
from PIL import Image
from pathlib import Path
from colormath.color_conversions import convert_color
from colormath.color_objects import LabColor, sRGBColor, HSLColor

# add the parent folder to the path so that imports work even if the working directory is the eu4 folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from eu4.eu4lib import Eu4Color
from eu4.paths import eu4outpath, verified_for_version
from eu4.colormap import ColorMapGenerator
from eu4.provincelists import is_island, province_is_on_an_island, island, terrain_to_provinces, coastal_provinces
from ck2parser import Date


class MapGenerator:

    def __init__(self):
        self.color_map_generator = ColorMapGenerator()
        self.mapparser = self.color_map_generator.mapparser

    def decision_maps(self):
        # change the version number after verifying that the provinces/areas are still correct
        verified_for_version('1.37.0')

        self.color_map_generator.create_shaded_image({
            'yellow': [prov.id for prov in self.mapparser.all_land_provinces.values() if
                       prov.get('Culture') == 'greek' and prov.region.name in ['balkan_region', 'anatolia_region']],
            # 10 provinces needed
            'blue': ['aegean_archipelago_area', 'northern_greece_area', 'morea_area', 'macedonia_area'],  # claims
        },
            {'orange': [146]},  # always needed
            'Formgreece', crop_to_color=True)

        self.color_map_generator.generate_mapimage_with_several_colors({
            'yellow': ['china_superregion', 'manchuria_region', 'mongolia_region', 'tibet_region'],
            'blue': ['mongol', 'oirats', 'khalkha', 'chahar'],
            'red': [723, 1816, 4678, 2136],
            }, 'Yuan_provinces', crop_to_color=True)

        self.color_map_generator.generate_mapimage_with_several_colors({
            'yellow': ['north_german_region', 'south_german_region'],
            'brightred': [50, 57, 65],
            'blue': [75, 41],
            'lightgreen': [1868, 70],
            'orange': [1876, 67],
            'turquoise': [1762, 85],
            'purple': [44, 45],
            'brown': [61, 63],
            'land': ['erzgebirge_area', 'bohemia_area', 'moravia_area'],  # not needed
            }, 'Formgermany', crop_to_color=True)

        self.color_map_generator.generate_mapimage_with_several_colors({
            'yellow': ['malaya_region', 'indonesia_region'],
            'green': [617, 596, 636, 629], # needed for muslim countries
            'lightgreen': [641], # also needed for muslim countries, but not in malaya or indonesia
            'purple': [622, 2687, 628, 638, 2390], # needed for non-muslim countries
            }, 'Formmalaya', crop_to_color=True)

        self.color_map_generator.generate_mapimage_with_several_colors({
            'orange': ['anatolia_region', 'egypt_region', 'italy_region', 'france_region', 'iberia_region', 'mashriq_region',
            'balkan_region', 'east_midlands_area', 'west_midlands_area', 'yorkshire_area', 'wessex_area',
            'home_counties_area', 'east_anglia_area', 'wales_area', 'scottish_marches_area', 'romandie_area',
            'upper_rhineland_area', 'romandie_area', 'alsace_area', 'palatinate_area', 'lower_rhineland_area',
            'carinthia_area', 85, 'north_brabant_area', 'brabant_area', 'flanders_area', 'wallonia_area',
            96, 'inner_austria_area', 'austria_proper_area', 'tirol_area', 'east_bavaria_area',
            'lower_bavaria_area', 'upper_bavaria_area', 'upper_swabia_area', 'lower_swabia_area', 'switzerland_area',
            'barbary_coast_area', 'kabylia_area', 'tunisia_area', 'djerba_area', 'tripolitania_area',
            'northern_morocco_area', 'algiers_area', 343, 'transdanubia_area'],
            'land': ['lower_nubia_area', 'iraq_arabi_area', 'basra_area']},  # not needed
            'EU4 Roman Empire',
            crop_to_color=True
        )
        self.color_map_generator.generate_mapimage_with_several_colors({
            'yellow': ['low_countries_region'], # claims
            'orange': [95, 97, 98, 99, 4383], # needed core provinces
            'land': [1931] # no claim on East Frisia
            }, 'Formnetherlands', crop_to_color=True)

        self.color_map_generator.generate_mapimage_with_several_colors({
            'important': set(coastal_provinces) & set(province_is_on_an_island),
            'pink': set(coastal_provinces) & set(self.mapparser.all_regions['maghreb_region'].provinceIDs),
            }, 'Province is on an island or maghreb map')

        self.color_map_generator.generate_mapimage_with_several_colors({
            # owned directly - since 1.37.0, all provinces can be owned by subjects
            # 'orange': ['mongolia_region', 'central_asia_region', 'crimea_region', 1816, 1821, 667],
            # owned directly or by a non-tributary subject
            'brightred': [
                'mongolia_region', 'central_asia_region', 'crimea_region', 1816, 1821, 667,
                'khorasan_region', 'persia_region', 295, 280
            ],
            }, 'Formmongols', crop_to_color=True)

        self.color_map_generator.create_shaded_image({
                # 20 owned and cored required
                'yellow': ['manchu'], # technically also manchu_new, but there are no manchu_new provinces at the start and putting it here breaks the script
                # gains cores
                'green': ['manchuria_region']
            },
            # always required
            {
                'orange': [730, 2108],
            }, 'Formmanchu', crop_to_color=True)

        self.formation_map('FormYemen', [387, 388, 390, 4280], [389, 391, 2346], claimed_areas=['yemen_area', 'upper_yemen_area', 'tihama_al_yemen_area', 'hadramut_area'])
        self.formation_map('FormGeorgia', [422, 423, 2203, 2204, 4301], [462, 2196, 4303], claimed_areas=['kartli_kakheti_area', 'samtskhe_area', 'imereti_area'])
        self.formation_map('Persiaprovinces', [414, 429, 433, 2213, 2215], [426, 2218], [416, 432, 2221], claimed_regions=['persia_region'])

    def formation_map(self, filename: str, required_provinces: list[int], optional_provinces: list[int], other_optional_provinces: list[int] = None, claimed_areas: list[str] = [], claimed_regions: list[str] = []):
        color_to_provinces = {
            'green': optional_provinces,
            'Darkturquoise': other_optional_provinces,
            # claims. provinces which are not green get shaded with the default land color
            'land': [prov.id for prov in self.mapparser.all_land_provinces.values() if
                     prov.id not in optional_provinces and (prov.area.name in claimed_areas or prov.region.name in claimed_regions)],
            'important': claimed_areas + claimed_regions,
        }
        if not other_optional_provinces:
            del color_to_provinces['turquoise']
        self.color_map_generator.create_shaded_image(color_to_provinces,
                                                     {'brightred': required_provinces},
                                                     filename, crop_to_color=True, first_shade_width=4, second_shade_width=2, margin=20)

# currently not used by the wiki
#         self.color_map_generator.generate_mapimage_with_several_colors({
#             'yellow': ['upper_doab_area', 'lower_doab_area', 'oudh_area', 'katehar_area', 'sirhind_area', 'lahore_area', 'sind_sagar_area'], # claims
#             'orange': [522], # needed core provinces
#             'red': [510, 524], # one of these
#             'green': [507, 555] # one of these
#             }, 'Formdehli', crop_to_color=True)

    def superregion_map(self):
        color_to_superregion = {}
        for i, superregion in enumerate(self.mapparser.all_superregions.values()):
            if superregion.contains_land_provinces:
                color_to_superregion[i] = superregion.name

        self.color_map_generator.generate_mapimage_with_several_colors(color_to_superregion, 'Superregion map')

    def region_maps(self):
        maps_to_generate = {
            'Superregion india': [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.superregion.name == 'india_superregion'],
            'Superregion east indies': [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.superregion.name == 'east_indies_superregion'],
            'Oceanian regions': [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.continent.name == 'oceania'],
            'Asian regions': [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.continent.name == 'asia' and prov.superregion.name not in ['india_superregion', 'east_indies_superregion']],
            'European regions': [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.continent.name == 'europe'],
            'Superregion africa': [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.continent.name == 'africa'],
            'Superregion south america': [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.continent.name == 'south_america'],
            'North American regions': [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.continent.name == 'north_america'],
            'Africa northern regions': [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.superregion.name == 'africa_superregion' or prov.region.name == 'egypt_region'],
            'Africa southern regions': [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.superregion.name == 'southern_africa_superregion'],
            'Europe central regions': [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.region.name in ['scandinavia_region', 'north_german_region', 'south_german_region', 'italy_region']],
            'Europe western regions': [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.region.name in ['france_region', 'iberia_region', 'british_isles_region', 'low_countries_region']],
            'Middle East regions': [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.superregion.name in ['persia_superregion', 'near_east_superregion'] and prov.region.name != 'egypt_region'],
            'Superregion Central and South America': [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.superregion.name in ['south_america_superregion', 'andes_superregion', 'central_america_superregion'] and prov.region.name not in ['rio_grande_region', 'california_region']],
            'Superregion china far east': [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.superregion.name in ['china_superregion', 'far_east_superregion'] and prov.region.name not in ['manchuria_region']],
            'Superregion east europe': [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.superregion.name in ['eastern_europe_superregion'] and prov.region.name not in ['manchuria_region']],
            'Superregion north america': [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.superregion.name == 'north_america_superregion' or prov.region.name in['rio_grande_region', 'california_region']],
            'Superregion tartary': [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.superregion.name == 'tartary_superregion' or prov.region.name in['manchuria_region']],
            'Region map':  [prov.id for prov in self.mapparser.all_land_provinces.values()],
            }
        for name, provinces in maps_to_generate.items():
            provinces = set(provinces)
            color_to_provinces = {}
            for i, region in enumerate(self.mapparser.all_regions.values()):
                provinces_in_region = set(region.provinceIDs) & provinces
                if len(provinces_in_region) > 0:
                    color_to_provinces[i+1] = list(provinces_in_region)
            if name in ['Oceanian regions', 'Region map']:
                crop_to_color = False
            else:
                crop_to_color = True
            self.color_map_generator.generate_mapimage_with_several_colors(color_to_provinces, name, crop_to_color=crop_to_color)

        # reorganize the oceania image so that the parts west of the
        # date line are on the left side of the image and the parts
        # east of the date line are on the right of the image
        # provinces with a lower x value are considered to be
        # east of the date line
        x_threshold = 2000
        provinces_east_of_date_line = set()
        for line in self.mapparser.positions_to_provinceID_array:
            provinces_east_of_date_line.update(line[:x_threshold])
        oceania_provinces_west_of_date_line = [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.continent.name == 'oceania' and prov.id not in provinces_east_of_date_line]
        oceania_provinces_east_of_date_line = [prov.id for prov in self.mapparser.all_land_provinces.values() if prov.continent.name == 'oceania' and prov.id in provinces_east_of_date_line]

        c_west = np.isin(self.mapparser.positions_to_provinceID_array, oceania_provinces_west_of_date_line).nonzero()
        c_east = np.isin(self.mapparser.positions_to_provinceID_array, oceania_provinces_east_of_date_line).nonzero()
        west_min_x = c_west[1].min() - 10
        west_max_x = self.mapparser.positions_to_provinceID_array.shape[1] - 1
        min_y = min(c_west[0].min(), c_east[0].min()) - 10
        max_y = self.mapparser.positions_to_provinceID_array.shape[0] - 1
        east_min_x = 0
        east_max_x = c_east[1].max() + 10

        temp_image = Image.open(eu4outpath / 'Oceanian regions.png')
        oceania_west = temp_image.crop((west_min_x, min_y, west_max_x, max_y))
        oceania_east = temp_image.crop((east_min_x, min_y, east_max_x, max_y))
        oceania_full = Image.new('RGB', (oceania_west.size[0] + oceania_east.size[0] + 1, oceania_east.size[1]), (0, 0, 0))
        oceania_full.paste(oceania_west, (0, 0))
        oceania_full.paste(oceania_east, (oceania_west.size[0] + 1, 0))
        oceania_full.save(eu4outpath / 'Oceanian regions.png')

# doesn't work. I have no idea how the color of an area is determined if none is defied in the areas.txt
#     def areas_map(self):
#         color_to_provinces = {}
#         provinces = self.mapparser.all_land_provinces.keys()
#         i = 0
#         for area in self.mapparser.allAreas.values():
#             if area.color:
#                 color = area.color
#             else:
#                 color = i
#             i += 1
#             provinces_in_area = set(area.provinceIDs) & provinces
#             if len(provinces_in_area) > 0:
#                 color_to_provinces[color] = list(provinces_in_area)
#
#         self.color_map_generator.generate_mapimage_with_several_colors(color_to_provinces, 'Areas map', crop_to_color=False)

    def get_similar_colors(self, base_color: LabColor, number_of_colors: int, brightness_step: float = 0.1,
                           color_step: float = 0.1, layers_of_brightness: float = 5) -> list[LabColor]:
        """Generate at least number_of_colors colors which are close to base_color,
        but different enough to be easily distinguished
        @param base_color:
        @param number_of_colors: generate at least this many colors, but could be more depending on layers_of_brightness
        @param brightness_step: Distance in lightness between each shade (L in the L*a*b color space)
        @param color_step: Distance in color (a and b in the L*a*b color space) between each generated color
        @param layers_of_brightness: How many shades to pick. Should be an uneven number.
               More shades results in less color variation
        @return: list of LabColors, one of which may be the base_color
        """
        # the rest of the algorithm assumes that l is between 0 and 1 and a, b are between -1 and 1
        base_l = base_color.lab_l / 100
        base_a = base_color.lab_a / 128
        base_b = base_color.lab_b / 128

        # reduce the number of shades if they are not needed, and we would overflow
        if number_of_colors < 10 and (((base_l - brightness_step * (layers_of_brightness - 1) / 2) < brightness_step) or ((base_l + brightness_step * (layers_of_brightness - 1) / 2) > (1 - brightness_step))):
            layers_of_brightness = layers_of_brightness - 2
        minimum_l = base_l - (layers_of_brightness-1) * brightness_step / 2
        # prevent l from overflowing
        if minimum_l < brightness_step*2:
            minimum_l = brightness_step*2
        if minimum_l + brightness_step*(layers_of_brightness+1) > 1:
            minimum_l = 1-brightness_step*(layers_of_brightness+2)

        ab_steps = math.ceil(math.sqrt(number_of_colors / layers_of_brightness))
        # starting points for a and b, but make sure that we never switch the sign, because this leads to very
        # noticeable color differences
        a_low = abs(base_a) - (ab_steps - 1) / 2 * color_step
        if a_low < 0:
            a_low = 0
        b_low = abs(base_b) - (ab_steps - 1) / 2 * color_step
        if b_low < 0:
            b_low = 0
        # calculate the a and b values to use and apply the correct sign to them
        # the list is reversed, so that the more vibrant colors(further away from 0) are used first
        a_values = reversed([math.copysign(a_low + i * color_step, base_a) for i in range(ab_steps)])
        b_values = reversed([math.copysign(b_low + i * color_step, base_b) for i in range(ab_steps)])
        colors = []
        for a_value in a_values:
            for b_value in b_values:
                for level in range(layers_of_brightness):
                    colors.append(LabColor((minimum_l + level * brightness_step) * 100, a_value * 128, b_value * 128))
        return colors

    def culture_map(self):
        """Experimental culture map. Not currently used by the wiki"""
        color_to_provinces = {}
        for i, culture_group in enumerate(self.mapparser.culture_groups.values()):
            group_color = convert_color(self.mapparser.color_list[i+1], LabColor)
            culture_colors = self.get_similar_colors(group_color, len(culture_group.cultures))
            for culture, color in zip(culture_group.cultures, culture_colors):
                provinces = [prov.id for prov in self.mapparser.all_provinces.values() if prov.get('Culture') == culture.name]
                if len(provinces) > 0:
                    rgb_color = convert_color(color, sRGBColor)
                    color_to_provinces[Eu4Color(rgb_color.clamped_rgb_r, rgb_color.clamped_rgb_g, rgb_color.clamped_rgb_b, is_upscaled=False)] = list(provinces)
        self.color_map_generator.generate_mapimage_with_several_colors(color_to_provinces, 'Cultures')

    def culture_group_map(self):
        color_to_provinces = {}
        for i, culture_group in enumerate(self.mapparser.culture_groups.values()):
            provinces = [prov.id for prov in self.mapparser.all_provinces.values() if prov.get('Culture Group') == culture_group]
            if len(provinces) > 0:
                color_to_provinces[i+1] = list(provinces)
        self.color_map_generator.generate_mapimage_with_several_colors(color_to_provinces, 'Culture groups')

    def religion_map(self):
        color_to_provinces = {}
        for religion in self.mapparser.all_religions.values():
            color_to_provinces[religion.color] = [prov.id for prov in self.mapparser.all_provinces.values()
                                                  if prov.get('Religion') == religion.name]
        color_to_provinces['white'] = [prov.id for prov in self.mapparser.all_provinces.values()
                                       if prov.get('Religion') is None and prov.type == 'Land']
        self.color_map_generator.generate_mapimage_with_several_colors(color_to_provinces, 'Religion')

    def trade_node_map(self):
        color_to_provinces = {}
        for i, trade_node in enumerate(self.mapparser.all_trade_nodes.values()):
            if trade_node.color:
                color_to_provinces[trade_node.color] = trade_node.provinceIDs
            else:
                color_to_provinces[i+1] = trade_node.provinceIDs
        self.color_map_generator.generate_mapimage_with_several_colors(color_to_provinces, 'Trade nodes')

    def trade_company_map(self):
        color_to_provinces = {}
        for tc in self.mapparser.all_trade_companies.values():
            color_to_provinces[tc.color] = tc.provinceIDs
        self.color_map_generator.generate_mapimage_with_several_colors(color_to_provinces, 'Trade companies')

    def colonial_region_map(self):
        color_to_provinces = {}
        for colonial_region in self.mapparser.all_colonial_regions.values():
            color_to_provinces[colonial_region.color] = colonial_region.provinceIDs
        self.color_map_generator.generate_mapimage_with_several_colors(color_to_provinces, 'Colonial regions')

    def island_maps(self):
        self.color_map_generator.generate_mapimage_with_important_provinces(is_island, 'is_island_map', crop=False)
        self.color_map_generator.generate_mapimage_with_important_provinces(island, 'island_map', crop=False)
        self.color_map_generator.generate_mapimage_with_important_provinces(province_is_on_an_island, 'province_is_on_an_island_map', crop=False)

    def coal_map(self):
        coal_provinces = []
        for prov in self.mapparser.all_provinces.values():
            if prov.get('latent trade good'):
                coal_provinces.append(prov.id)
        self.color_map_generator.generate_mapimage_with_several_colors({'cyan': coal_provinces}, 'coalmap', crop_to_color=False)

    def gold_map(self):
        gold_provinces = []
        for prov in self.mapparser.all_provinces.values():
            if prov.get('Trade good') == 'gold':
                gold_provinces.append(prov.id)
        self.color_map_generator.generate_mapimage_with_several_colors({'gold': gold_provinces}, 'Goldmap', crop_to_color=False)

    def terrain_map(self):
        color_to_provinces = {}
        for terrain in self.mapparser.terrains.values():
            if terrain.name == 'inland_ocean':
                # this color is used on the wiki and fits better than the darker blue which the game assigns
                color_to_provinces[Eu4Color(142, 232, 255)] = terrain.provinceIDs
            elif terrain.name == 'open_sea':
                color_to_provinces[Eu4Color(41, 64, 98)] = terrain.provinceIDs
            elif terrain.name not in ['lake', 'ocean']: # just use default colors for oceans and lakes because the game files make oceans white and have no color for lakes
                color_to_provinces[terrain.color] = terrain.provinceIDs
        self.color_map_generator.generate_mapimage_with_several_colors(color_to_provinces, 'Terrain map', crop_to_color=False)
        map_image = Image.open(eu4outpath / 'Terrain map.png')
        legend_image = Image.open(Path(__file__).parent / 'terrain_legend.png')
        map_image.paste(legend_image, (430, 820))
        map_image.save(eu4outpath / 'Terrain map.png')

    def country_map(self):
        empty_provinces = set(self.mapparser.all_land_provinces.keys())
        color_to_provinces = {}
        for country in self.mapparser.all_countries.values():
            provinces = [prov.id for prov in self.mapparser.all_provinces.values() if prov.get('Owner') == country.tag]
            if len(provinces) > 0:
                empty_provinces -= set(provinces)
                color_to_provinces[country.get_color()] = provinces
        color_to_provinces[Eu4Color(150, 150, 150)] = empty_provinces
        self.color_map_generator.generate_mapimage_with_several_colors(color_to_provinces, 'Countries')

    def continent_map(self):
        self.color_map_generator.generate_mapimage_with_several_colors({
            Eu4Color.new_from_rgb_hex('#7fffff'): 'europe',
            Eu4Color.new_from_rgb_hex('#ffff7f'): 'asia',
            Eu4Color.new_from_rgb_hex('#7f7fff'): 'africa',
            Eu4Color.new_from_rgb_hex('#ff7f7f'): 'north_america',
            Eu4Color.new_from_rgb_hex('#7fff7f'): 'south_america',
            Eu4Color.new_from_rgb_hex('#ff7fff'): 'oceania'
        }, 'Continent map')

    def techgroup_map(self):
        tech_group_color = {
            'western': '#ccc000', 'eastern': '#b38000',
            'ottoman': '#7ecb78', 'muslim': '#00cc00',
            'indian': '#0099cc', 'east_african': '#f98c0f',
            'central_african': '#633c27', 'chinese': '#cc4c00',
            'nomad_group': '#662600', 'sub_saharan': '#804c4c',
            'north_american': '#d98c8c', 'mesoamerican': '#800000',
            'south_american': '#006600', 'andean': '#8c4c8c',
            'aboriginal_tech': '#FFFFFF', 'polynesian_tech': '#1a35b1'
        }
        tag_to_tech_group = {}
        for path, tree in self.mapparser.parser.parse_files('history/countries/*'):
            tag = path.stem[:3]
            tree_1444 = tree.at_time(Date(1444,11,11))
            if 'technology_group' in tree_1444:
                tag_to_tech_group[tag] = tree_1444['technology_group']
            else:
                print('Warning: {} has no technology_group'.format(tag))

        color_to_provinces = {}
        for tech_group, color_hex in tech_group_color.items():
            color = Eu4Color.new_from_rgb_hex(color_hex)
            color_to_provinces[color] = [prov.id for prov in self.mapparser.all_land_provinces.values()
                                         if 'Owner' in prov and tag_to_tech_group[prov.get('Owner')] == tech_group]

        self.color_map_generator.generate_mapimage_with_several_colors(color_to_provinces, 'Tech groups')

    # TODO: this is unfinished and waiting for the outcome of the discussion on the talk page
    def mission_map(self):
        tags_with_tag_specific_missions = set()
        tags_with_shared_tag_specific_missions = set()
        for file, tree in self.mapparser.parser.parse_files('missions/*'):
            for slotname, slotdata in tree:
                # print(slotname, slotdata['potential'].str(self.mapparser.parser))
                if 'tag' in slotdata['potential']:
                    tags_with_tag_specific_missions.add(slotdata['potential']['tag'].val)
                elif 'OR' in slotdata['potential']:
                    for k, v in slotdata['potential']: # we have to iterate, because there can be multiple OR
                        if k == 'OR' and 'tag' in v:
                            for k2, v2 in v:
                                if k2 == 'tag':
                                    tags_with_shared_tag_specific_missions.add(v2.val)

                    # print(slotname, slotdata['potential']['OR'].str(self.mapparser.parser))
#                    a = slotdata['potential']['OR']
#                    print(slotdata['potential']['OR']['tag'].str(self.mapparser.parser))
                # for k2, v2 in v:
                #     mission = k2.val_str()
                #     if mission not in ['has_country_shield', 'ai', 'generic', 'potential', 'slot', 'potential_on_load']:
                #         if mission not in allmissions:
                #             allmissions[mission] = []
                #     allmissions[mission].append(file)

        empty_provinces = set(self.mapparser.all_land_provinces.keys())
        color_to_provinces = {}
        for country in self.mapparser.all_countries.values():
            if country.tag in tags_with_tag_specific_missions or country.tag in tags_with_shared_tag_specific_missions:
                provinces = [prov.id for prov in self.mapparser.all_provinces.values() if prov.get('Owner') == country.tag]
                if len(provinces) > 0:
                    empty_provinces -= set(provinces)
                    color_to_provinces[country.get_color()] = provinces
        color_to_provinces[Eu4Color(150, 150, 150)] = empty_provinces
        self.color_map_generator.generate_mapimage_with_several_colors(color_to_provinces, 'Missions1444map')

    def mission_map_from_save(self, savefile):
        save_data = open(savefile, encoding='cp1252').read()
        all_missions_regex = re.compile(r'^\t([A-Z]{3})=.*?(country_missions=\{\n(.*?)^\t\t})', re.MULTILINE | re.DOTALL)
        tags_to_mission_groups = {}
        for match in all_missions_regex.finditer(save_data):
            if match[3]:
                tag = match[1]
                # print(f'{tag}: ')
                tags_to_mission_groups[tag] = []
                for mission in match[3].split():
                    if mission not in ['mission_slot={', '}']:
                        # print(mission)
                        tags_to_mission_groups[tag].append(mission)
        tag_count = {}
        min_count = 9999
        max_count = 0
        for tag, mission_groups in tags_to_mission_groups.items():
            count = 0
            country = self.mapparser.all_countries[tag]
            for group in mission_groups:
                count += len(self.mapparser.all_mission_groups[group].missions)
            tag_count[tag] = count
            if count < min_count:
                min_count = count
            if count > max_count:
                max_count = count
            # print(f'{country.display_name}({tag}): {count}')

        empty_provinces = set(self.mapparser.all_land_provinces.keys())
        color_to_provinces = {}

        for tag, count in sorted(tag_count.items(), key=lambda tag_count_tuple: tag_count_tuple[1]):
            country = self.mapparser.all_countries[tag]
            print(f'{country.display_name}({tag}): {count}')
            provinces = [prov.id for prov in self.mapparser.all_provinces.values() if prov.get('Owner') == country.tag]
            if len(provinces) > 0:
                empty_provinces -= set(provinces)
                # color = self.heatmap_color_for(count, min_count, max_count)
                color = self.fixed_colors(count)
                # color = self.greeny_suggested_color(count)
                color_to_provinces[color] = provinces
        color_to_provinces[Eu4Color(150, 150, 150)] = empty_provinces
        self.color_map_generator.generate_mapimage_with_several_colors(color_to_provinces, 'Missions1444heatmap')

    def greeny_suggested_color(self, value):
        if value < 16:
            return Eu4Color(189, 189, 189)
        if value < 21:
            return Eu4Color(68, 182, 196)
        if value < 24:
            return Eu4Color(116, 196, 118)
        if value < 26:
            return Eu4Color(8, 81, 156)
        if value < 30:
            return Eu4Color(221, 52, 151)
        if value < 35:
            return Eu4Color(254, 196, 79)
        if value < 40:
            return Eu4Color(204, 76, 2)
        if value < 50:
            return Eu4Color(227, 26, 28)
        else:
            return Eu4Color(174, 1, 124)

    def fixed_colors(self, value):
        '''colors from https://colorbrewer2.org'''
        if value < 16:
            return Eu4Color(255, 255, 204)
        if value < 21:
            return Eu4Color(255, 237, 160)
        if value < 24:
            return Eu4Color(254, 217, 118)
        if value < 26:
            return Eu4Color(254, 178, 76)
        if value < 30:
            return Eu4Color(253, 141, 60)
        if value < 35:
            return Eu4Color(252, 78, 42)
        if value < 40:
            return Eu4Color(227, 26, 28)
        if value < 50:
            return Eu4Color(189, 0, 38)
        else:
            return Eu4Color(128, 0, 38)

    def heatmap_color_for(self, value, min_value, max_value):
        value = value - min_value
        value = value / (max_value - min_value)
        h = (1 - value)
        s = 1
        l = value / 2

        color = HSLColor(h, s, l)
        return convert_color(color, sRGBColor)

    def map(self, where, name='', crop=True, margin = 10):
        self.color_map_generator.generate_mapimage_with_important_provinces(where, name, crop, margin)

    def achievement_map(self, achievement_name, where, crop=True, margin = 10):
        self.map(where, achievement_name + ' map', crop, margin)

    def achievement_maps(self):
        # change the version number after verifying that the provinces/areas are still correct
        # for the first two achievements, the decision file has to be checked
        verified_for_version('1.37.0', 'Files to validate are:\n* ' + '\n* '.join(['common/achievements.txt', 'decisions/Religion.txt', 'decisions/Muslim.txt']))

        # from the decision zoroastrian_royal_fires in decisions/Religion.txt
        self.achievement_map('Royal Fires', '2221 2207 2235 2236 2218 441 2223')
        # from the decision unify_islam in decisions/Muslim.txt
        self.map(name='Unify Islam', where='504 225 151 410 385 384 124 125 425 382 454 347 388 400')

        self.achievement_map('Albania or Iberia', 'iberia_region caucasia_region')
        self.achievement_map('Almost Prussian Blue', 'east_prussia_area west_prussia_area 1859 4523 4526 254 2963 1931 silesia_area ' + ' '.join([
            str(province.id) for province in self.mapparser.all_regions['north_german_region'].provinces if province.area.name not in ['bohemia_area', 'moravia_area', 'erzgebirge_area']
        ]))
        self.achievement_map('An Industrial Evolution', 'home_counties_area east_midlands_area west_midlands_area east_anglia_area wessex_area yorkshire_area')
        self.map(name='Azur semé de lis or Map', where='167 168 173 174 177 179 180 183 185 186 194 195 196 200 203 204 1879 2753 4111 4112 4385 4386 4388 4389 4390 4391 4695')
        self.achievement_map('Around the World in 80 Years', '965 869 2315 529 561 667 1028')
        self.achievement_map('Avar Khaganate', 'alfold_area transdanubia_area slovakia_area transylvania_area southern_transylvania_area')
        self.achievement_map('Baltic Crusader', 'russia_region ural_region crimea_region')
        self.map(name='EU4BasileusRequirements', where='morea_area northern_greece_area albania_area macedonia_area bulgaria_area thrace_area hudavendigar_area aydin_area germiyan_area kastamonu_area ankara_area karaman_area rum_area cukurova_area dulkadir_area')
        self.achievement_map('Better than Napoleon', '295 50 134')
        self.achievement_map('Breaking the Yoke', '284 303 1082')
        self.achievement_map('Consulate of the Sea', '101 112 121 148 151 137 220 317 336 341 354 358')
        self.achievement_map('Definitely the Sultan of Rum', '295 151 118')
        self.achievement_map('Emperor of Hindustan', 'hindusthan_region jaipur_area malwa_area saurashtra_area tapti_area sindh_area northern_sindh_area khandesh_area ahmedabad_area patan_area jangladesh_area gaur_area west_bengal_area north_bengal_area east_bengal_area jharkhand_area orissa_area garjat_area upper_mahanadi_area gondwana_area telingana_area maidan_area desh_area rayalaseema_area mysore_area konkan_area raichur_doab_area golconda_area berar_area ahmednagar_area andhra_area south_carnatic_area north_carnatic_area')
        self.map('british_isles_region scandinavia_region', 'For Odin')
        self.achievement_map('Georgia on my Mind', 'kartli_kakheti_area samtskhe_area imereti_area american_georgia_area upper_american_georgia_area 2025')
        self.achievement_map('Golden Horn', 'horn_of_africa_region', margin=100)
        self.achievement_map('Great Moravia', '60 4778 134 4762 4761 135 153 154 162 262 263 4723 264 4726 265 266 4725 4724 267 1318 1763 1770 1771 1772 1864 2960 2966 2967 2968 2970 4126 4236 4237 4238 4240')
        self.achievement_map('Great Perm', 'russia_region ural_region scandinavia_region west_siberia_region east_siberia_region cascadia_region hudson_bay_region canada_region')
        self.achievement_map('Imperio español', '852 835 484 808')
        self.achievement_map('The Iron Price', '246 yorkshire_area east_midlands_area east_anglia_area')
        self.achievement_map('It\'s All Greek To Me', '138 504 578 4104')
        self.achievement_map('Knights of the Caribbean', '320 321 163 164 2348 3003 4700 4698 142 2982 124 125 4737 4736 2954 126 127 1247 4559 4560 333 112 4735 2986')
        self.achievement_map('Laughingstock', '1983 2470 4073')
        self.achievement_map('The Levant Turnabout', '149 151 317 326')
        self.map(name='Requirements_Mare_Nostrum', where='101 102 111 112 113 114 115 117 118 119 120 121 122 123 124 125 126 127 130 136 137 142 143 144 145 146 147 148 149 151 159 163 164 197 200 201 212 213 220 221 222 223 226 282 284 285 286 287 316 317 318 319 320 321 325 327 328 330 333 335 337 338 339 341 353 354 355 356 357 358 362 363 364 378 462 1247 1750 1751 1756 1764 1773 1774 1826 1854 1855 1856 1882 1933 1934 1974 2195 2196 2296 2297 2298 2299 2302 2304 2313 2325 2326 2348 2406 2410 2412 2447 2451 2452 2453 2455 2461 2473 2753 2954 2977 2980 2982 2983 2984 2985 2986 2988 2992 3003 4706 4174 4175 4316 4546 4549 4550 4559 4560 4561 4562 4696 4698 4699 4700 4701 4705 4729 4732 4733 4735 4736 4737 4738 4752 4753 4754 4779')
        self.achievement_map('No Trail of Tears', 'susquehanna_area delaware_valley_area hudson_valley_area massachusetts_bay_area connecticut_valley_area chesapeake_area great_valley_area piedmont_north_america_area carolinas_area south_carolina_area appalachia_area south_appalachia_area 929 971 2526 2539 2540 2564 2565 2566')
        self.achievement_map('On the Rhodes Again', '151 2313 379')
        self.achievement_map('Pandya Empire', 'coromandel_region malabar_area mysore_area rayalaseema_area', margin=50)
        self.achievement_map('Philippine Tiger', 'coromandel_region malabar_area mysore_area rayalaseema_area orissa_area west_bengal_area east_bengal_area arakan_area lower_burma_area north_tenasserim_area tenasserim_area malaya_area malacca_area central_thai_area kalimantan_area north_sumatra_area batak_area minangkabau_area west_java_area south_sumatra_area 2379 604 2380 2376 2377 2029')
        self.map(name='Prester John Achievement Map', where='358 2313 151', margin=50)
        self.achievement_map('Raja of the Rajput Reich', 'north_german_region south_german_region')
        self.achievement_map('Rozwi Empire', 'zimbabwe_area butua_area lower_zambezi_area')
        self.achievement_map('Saladin\'s Legacy', 'egypt_region mashriq_region aleppo_area tabuk_area medina_area mecca_area asir_area tihama_al_yemen_area upper_yemen_area yemen_area hadramut_area north_kurdistan_area')
        self.achievement_map('Shemot is Not', 'egypt_region')
        # Sons of Carthage
        self.achievement_map('Carthage', 'sicily_area western_sicily_area 2986 127 4735 baleares_area barbary_coast_area upper_andalucia_area 221 1750 1749 224 4548')
        self.achievement_map('Niger and Sahel', 'sahel_region niger_region')
        self.map('2778', 'Stern des Südens map', margin=400)
        self.achievement_map('Stiff Upper Lippe', 'british_isles_region')
        self.achievement_map('Sun Invasion', '2628 852 2626 853', margin=100)
        self.achievement_map('Sunset Invasion', '227 217 183 236 97 118')

        # Sweden is not overpowered
        self.achievement_map('Achievement sweden conditions', '1 2 3 6 9 11 19 25 27 28 30 33 34 35 36 37 38 39 40 41 42 43 45 46 47 48 1841 1842 1858 1930 1935 1981 1982 2994 2995 2996 4113 4165 4746 4745')
        self.achievement_map('Take that, von Habsburgs!', 'inner_austria_area austria_proper_area carinthia_area tirol_area')
        self.achievement_map('Tatarstan', 'astrakhani bashkir crimean kazani mishary nogaybak siberian')
        self.map(name='EU4TheGreatKhanRequirements', where='russia_region ural_region crimea_region south_china_region xinan_region north_china_region persia_region khorasan_region')
        self.achievement_map('The Sun Never Sets on the Indian Empire', '236 1177 667 4890')
        self.achievement_map('The White Elephant', 'indo_china_region burma_region')
        self.achievement_map('This is Persia!', 'anatolia_region morea_area northern_greece_area macedonia_area egypt_region')
        self.achievement_map('Tiger of Mysore', 'deccan_region coromandel_region')
        self.achievement_map('Trade Hegemon', '388 2999 596')
        self.achievement_map('Where are the penguins', 'madagascar_highlands_area betsimasaraka_area sakalava_area southern_madagascar 1177 1179 833 1180 1084 2727 2736 1086 2735 1087 2734 4869 4868 1085 4858 1246 1109 783 782 2869 1095 2025')

        # the following maps might need updating even if the achievement list didn't change
        # all grassland provinces in Asia
        grassland_in_asia = [provinceID for provinceID in terrain_to_provinces['grasslands'] if provinceID in self.mapparser.all_continents['asia'].provinceIDs]
        self.achievement_map('Eat your greens', grassland_in_asia)

        east_siberian_coastline = [provinceID for provinceID in coastal_provinces if provinceID in self.mapparser.all_regions['east_siberia_region'].provinceIDs]
        self.achievement_map('Relentless Push East', east_siberian_coastline)

        desert_and_coastal_desert = terrain_to_provinces['coastal_desert'] + terrain_to_provinces['desert']
        self.achievement_map('I dont like sand', desert_and_coastal_desert, crop=False)

        tropical_wood_provinces = [province.id for province in self.mapparser.all_land_provinces.values() if province['Trade good'] == 'tropical_wood']
        tropical_provs = [n.val for n in self.mapparser.parser.parse_file(self.mapparser.map_path('climate'))['tropical']]
        possible_provs = [province.id for province in self.mapparser.all_land_provinces.values() if not 'Owner' in province and (province.id in tropical_provs or province.id in terrain_to_provinces['jungle'])]
        self.color_map_generator.generate_mapimage_with_several_colors({'important': tropical_wood_provinces, Eu4Color(218, 220, 57): possible_provs}, 'Tropical Wood map')

    # the tags are chosen kind of arbitrary
    provincelist_definitions = [{'variable_name': 'coastal_provinces', 'condition': 'has_port = yes', 'tag': 'POR'},
                                {'variable_name': 'is_island', 'condition': 'is_island = yes', 'tag': 'ICE'},
                                {'variable_name': 'province_is_on_an_island',
                                 'condition': 'province_is_on_an_island = yes', 'tag': 'IDR'},
                                {'variable_name': 'island', 'condition': 'island = yes', 'tag': 'IKE'}, ]
    provincelist_terrain_definitions = [{'terrain': 'glacier', 'tag': 'GLE'},
                                        {'terrain': 'farmlands', 'tag': 'FAD'},
                                        {'terrain': 'forest', 'tag': 'FOX'},
                                        {'terrain': 'hills', 'tag': 'HMI'},
                                        {'terrain': 'woods', 'tag': 'WOL'},
                                        {'terrain': 'mountain', 'tag': 'MON'},
                                        {'terrain': 'grasslands', 'tag': 'GRA'},
                                        {'terrain': 'jungle', 'tag': 'JOL'},
                                        {'terrain': 'marsh', 'tag': 'MAR'},
                                        {'terrain': 'desert', 'tag': 'DEC'},
                                        {'terrain': 'coastal_desert', 'tag': 'COB'},
                                        {'terrain': 'coastline', 'tag': 'COL'},
                                        {'terrain': 'drylands', 'tag': 'DNZ'},
                                        {'terrain': 'highlands', 'tag': 'HIN'},
                                        {'terrain': 'savannah', 'tag': 'SAV'},
                                        {'terrain': 'steppe', 'tag': 'STE'},
                                        ]

    def print_provincelist_help_message(self):
        print('Please specify a uncompressed save game as a second parameter on which the following run.txt was executed:')
        print('-'*40)
        tags = []
        add_core_code = []
        for condition in self.provincelist_definitions:
            tags.append(condition['tag'])
            add_core_code.append('''
every_province = {{
    limit = {{
        {}
        is_wasteland = no
    }}
    add_core = {}
}}'''.format(condition['condition'], condition['tag']))

        for terrain in self.provincelist_terrain_definitions:
            tags.append(terrain['tag'])
            add_core_code.append('''
every_province = {{
    limit = {{
        has_terrain = {}
        is_wasteland = no
    }}
    add_core = {}
}}'''.format(terrain['terrain'], terrain['tag']))
        print('''
every_province = {
    limit = {
        OR = {
            is_core = ''' +
            '\n            is_core = '.join(tags))
        print('''
        }
    }
    remove_core = ''' + '\n    remove_core = '.join(tags))
        print('\n}\n')
        print('\n'.join(add_core_code))

    def generate_provincelists(self, savefile):
        save_data = open(savefile, encoding='cp1252').read()
        core_regex = re.compile('^-([0-9]{1,4})=.*?(cores=\{\n([^}\n]*)|^\t\})', re.MULTILINE |re.DOTALL)
        tags_to_provinces = {}
        for match in core_regex.finditer(save_data):
            if match[3]:
                provinceID = match[1]
                for tag in match[3].split():
                    if tag not in tags_to_provinces:
                        tags_to_provinces[tag] = []
                    tags_to_provinces[tag].append(provinceID)

        print('Please add the following code to eu4/provincelists.py')
        print('-'*40)
        print('# generated by:')
        print('# eu4/generate_maps.py --generate-provincelists')
        print('from eu4.paths import verified_for_version')
        print("verified_for_version('{}')".format(self.mapparser.eu4_version))
        for condition in self.provincelist_definitions:
            print('{} = [{}]'.format(condition['variable_name'], ','.join(tags_to_provinces[condition['tag']])))
        print('terrain_to_provinces = {')
        for terrain in self.provincelist_terrain_definitions:
            print('    "{}": [{}],'.format(terrain['terrain'], ','.join(tags_to_provinces[terrain['tag']])))
        print('}')

    def generate_all(self):
        self.superregion_map()
        self.region_maps()
        self.island_maps()
        self.decision_maps()
        self.coal_map()
        self.gold_map()
        self.achievement_maps()
        self.culture_group_map()
        self.religion_map()
        self.trade_node_map()
        self.trade_company_map()
        self.terrain_map()
        self.colonial_region_map()
        self.country_map()
        self.continent_map()
        self.techgroup_map()
        # self.mission_map()


if __name__ == '__main__':
    generator = MapGenerator()

    if len(sys.argv) > 1:
        if sys.argv[1] == '--generate-provincelists':
            if len(sys.argv) == 2:
                generator.print_provincelist_help_message()
            else:
                generator.generate_provincelists(sys.argv[2])
        elif sys.argv[1] == '--generate-mission-map':
            if len(sys.argv) == 2:
                print('Please specify a uncompressed 1444-11-11 save game with all DLCs as a second parameter')
            else:
                generator.mission_map_from_save(sys.argv[2])
        else:
            for arg in sys.argv[1:]:
                getattr(generator, arg)()
    else:
        generator.generate_all()
