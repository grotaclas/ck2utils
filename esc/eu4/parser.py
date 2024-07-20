import sys
import os
import re
from collections import OrderedDict

# add the parent folder to the path so that imports work even if the working directory is the eu4 folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from ck2parser import SimpleParser, Obj, String, Number
from localpaths import eu4dir, eu4mod_paths
from eu4.paths import eu4_version, eu4_major_version
from eu4.eu4lib import Religion, Idea, IdeaGroup, Policy, Eu4Color, Country, Mission, MissionGroup, GovernmentReform, \
    CultureGroup, Culture, DLC, BaseGame, Estate
from eu4.cache import disk_cache, cached_property


class Eu4Parser:
    """the methods of this class parse game files and retrieve all kinds of information

    map, event or decision related methods are in the subclasses
    Eu4MapParser. Eu4EventParser and Eu4DecisionParser instead
    """

    # allows the overriding of localisation strings
    localizationOverrides = {}

    def __init__(self):
        self.parser = SimpleParser(*eu4mod_paths)
        self.parser.basedir = eu4dir

    @cached_property
    @disk_cache()
    def _localisation_dict(self):
        localisation_dict = {}

        paths = list(self.parser.files('localisation/*_l_english.yml'))
        # put replace localisations at the end so that they override the normal localisation.
        # TODO: this does not take mod load order into account when multiple mods replace the same localisation
        paths.extend(self.parser.files('localisation/replace/*_l_english.yml'))

        for path in paths:
            with path.open(encoding='utf-8-sig') as f:
                for line in f:
                    match = re.fullmatch(r'\s*([^#\s:]+):\d?\s*"(.*)"[^"]*', line)
                    if match:
                        localisation_dict[match.group(1)] = match.group(2)
        return localisation_dict

    def localize(self, key: str, default: str = None) -> str:
        """localize the key from the english eu4 localisation files

        if the key is not found, the default is returned
        unless it is None in which case the key is returned
        """
        if default is None:
            default = key

        if key in self.localizationOverrides:
            return self.localizationOverrides[key]
        else:
            return self._localisation_dict.get(key, default)

    @cached_property
    def eu4_version(self):
        return eu4_version()

    @cached_property
    def eu4_major_version(self):
        return eu4_major_version()

    @cached_property
    def dlcs(self) -> list[DLC]:
        dlcs = []
        for file, contents in self.parser.parse_files('*dlc/*/*.dlc'):  # also catches builtin_dlc (women in history)
            name = contents['archive'].val.split('/')[1]
            display_name = contents['name'].val
            category = contents['category'].val
            archive = self.parser.basedir / contents['archive'].val
            dlcs.append(DLC(name, display_name, category, archive))
        return dlcs

    @cached_property
    def dlcs_including_base_game(self) -> list[DLC]:
        return [BaseGame(self.parser)] + self.dlcs

    @cached_property
    def dlcs_by_name(self) -> dict[str, DLC]:
        return {dlc.display_name: dlc for dlc in self.dlcs}

    @cached_property
    def all_religions(self):
        all_religions = {}
        for _, tree in self.parser.parse_files('common/religions/*'):
            for group, religions in tree:
                for religion, data in religions:
                    if religion.val in ['defender_of_faith', 'can_form_personal_unions', 'center_of_religion',
                                        'flags_with_emblem_percentage', 'flag_emblem_index_range',
                                        'harmonized_modifier', 'crusade_name', 'ai_will_propagate_through_trade',
                                        'religious_schools']:
                        continue
                    color = Eu4Color.new_from_parser_obj(data['color'])
                    all_religions[religion.val] = Religion(religion.val, self.localize(religion.val), group.val, color, data)
        return all_religions

    def _process_idea_modifiers(self, data):
        return {modifier.val: value.val for modifier, value in data if modifier.val not in ['effect', 'removed_effect']}

    @cached_property
    def all_idea_groups(self, filter_groups=['SYN_ideas', 'JMN_ideas']):
        # collect all ideas to handle duplicate ideas which are not always specified again
        all_ideas = {}
        all_idea_groups = {}
        for _, tree in self.parser.parse_files('common/ideas/*'):
            for n, v in tree:
                idea_group_name = n.val
                if idea_group_name in filter_groups:
                    continue
                category = None
                bonus = None
                traditions = None
                ideas = []
                if idea_group_name == 'compatibility_127':
                    continue
                for n2, v2 in v:
                    idea_name = n2.val
                    if idea_name in ['trigger', 'free', 'ai_will_do', 'important']:
                        continue
                    if idea_name == 'bonus':
                        bonus = Idea(idea_group_name + '_bonus',
                                     self.localize(idea_group_name + '_bonus'),
                                     self._process_idea_modifiers(v2))
                    elif idea_name == 'start':
                        traditions = Idea(idea_group_name + '_start',
                                          self.localize(idea_group_name + '_start'),
                                          self._process_idea_modifiers(v2))
                    elif idea_name == 'category':
                        category = v2.val
                    else:
                        modifiers = None
                        if len(v2) == 0:
                            if idea_name in all_ideas:
                                modifiers = all_ideas[idea_name].modifiers
                            else:
                                print(f'Error: idea {idea_name} is empty and not defined elsewhere')
                        else:
                            modifiers = self._process_idea_modifiers(v2)
                        if modifiers:
                            idea = Idea(idea_name,
                                        self.localize(idea_name),
                                        modifiers)
                            ideas.append(idea)
                            all_ideas[idea_name] = idea

                idea_group = IdeaGroup(idea_group_name,
                                       self.localize(idea_group_name),
                                       ideas,
                                       bonus,
                                       traditions,
                                       category)
                all_idea_groups[idea_group_name] = idea_group
        return all_idea_groups

    @cached_property
    def ideas_and_policies_by_modifier(self):
        ideas_and_policies_by_modifier = {}
        for idea_group in self.all_idea_groups.values():
            for idea in idea_group.get_ideas_including_traditions_and_ambitions():
                for modifier, value in idea.modifiers.items():
                    if modifier not in ideas_and_policies_by_modifier:
                        ideas_and_policies_by_modifier[modifier] = {}
                    if value not in ideas_and_policies_by_modifier[modifier]:
                        ideas_and_policies_by_modifier[modifier][value] = []
                    ideas_and_policies_by_modifier[modifier][value].append(idea)
        for policy in self.all_policies.values():
            for modifier, value in policy.modifiers.items():
                if modifier not in ideas_and_policies_by_modifier:
                    ideas_and_policies_by_modifier[modifier] = {}
                if value not in ideas_and_policies_by_modifier[modifier]:
                    ideas_and_policies_by_modifier[modifier][value] = []
                ideas_and_policies_by_modifier[modifier][value].append(policy)
        return ideas_and_policies_by_modifier

    @cached_property
    def all_policies(self):
        all_policies = {}
        for _, tree in self.parser.parse_files('common/policies/*'):
            for n, v in tree:
                policy_name = n.val
                category = None
                idea_groups = []
                modifiers = {}
                for n2, v2 in v:
                    if n2.val in ['potential', 'ai_will_do', 'effect', 'removed_effect']:
                        pass
                    elif n2.val == 'monarch_power':
                        category = v2.val
                    elif n2.val == 'allow':
                        for n3, v3 in v2:
                            if n3.val == 'full_idea_group':
                                idea_groups.append(self.all_idea_groups[v3.val])
                            else:
                                raise Exception(
                                    'Unexpected key in allow section of the policy "{}"'.format(policy_name))
                    else:
                        modifiers[n2.val] = v2.val
                all_policies[policy_name] = Policy(policy_name,
                                                   self.localize(policy_name),
                                                   self.localize('desc_' + policy_name, default=''),
                                                   category,
                                                   modifiers,
                                                   idea_groups)
        return all_policies

    @cached_property
    def all_mission_groups(self):
        all_mission_groups = {}
        for file, tree in self.parser.parse_files('missions/*'):
            for k, v in tree:
                mission_group_id = k.val_str()
                potential = ''
                slot = 0
                missions = []
                last_mission_position = 0
                for k2, v2 in v:
                    possible_mission_id = k2.val_str()
                    if possible_mission_id not in ['has_country_shield', 'ai', 'generic', 'potential', 'slot',
                                                   'potential_on_load']:
                        display_name = self.localize(possible_mission_id + '_title')
                        if 'position' in v2:
                            position = v2['position']
                        else:
                            position = last_mission_position + 1
                        last_mission_position = position

                        missions.append(Mission(possible_mission_id, display_name,
                                                description=self.localize(possible_mission_id + '_desc'),
                                                position=position))
                    elif possible_mission_id == 'potential':
                        potential = v2
                    elif possible_mission_id == 'slot':
                        slot = v2.val
                all_mission_groups[mission_group_id] = MissionGroup(mission_group_id, file.name, potential, missions, slot=slot)
        return all_mission_groups

    @cached_property
    def all_missions(self) -> dict[str, Mission]:
        return {mission.name: mission
                for group in self.all_mission_groups.values()
                for mission in group.missions}

    @cached_property
    def culture_groups(self) -> dict[str, CultureGroup]:
        """mapping between the script names of the culture groups and CultureGroup objects

        preserves the order of the cultures files
        """
        culture_groups = {}
        for _, tree in self.parser.parse_files('common/cultures/*'):
            for group_name, group_data in tree:
                cultures = []
                for n, value in group_data:
                    if (isinstance(value, Obj) and
                            not re.match(r'(((fe)?male|dynasty)_names|country|province)', n.val)):
                        primary = None
                        if 'primary' in value:
                            primary = value['primary'].val
                        cultures.append(Culture(n.val, self.localize(n.val), primary=primary))
                culture_group = CultureGroup(group_name.val, self.localize(group_name.val), cultures)
                for culture in cultures:
                    culture.culture_group = culture_group
                culture_groups[group_name.val] = culture_group
        return culture_groups

    @cached_property
    def cultures(self):
        return {culture.name: culture
                for culture_group in self.culture_groups.values()
                for culture in culture_group.cultures}

    @cached_property
    def all_countries(self):
        """returns a dictionary. keys are tags and values are Country objects. It is ordered by the tag order"""
        countries = OrderedDict()
        for tag, country_file in self.parser.merge_parse('common/country_tags/*.txt'):
            countries[tag] = Country(tag, self.localize(tag), parser=self, country_file=country_file)
        return countries

    @cached_property
    @disk_cache()
    def tag_to_color_mapping(self):
        country_colors = {}
        for c in self.all_countries.values():
            country_data = self.parser.parse_file('common/' + c.country_file)
            country_colors[c.tag] = Eu4Color.new_from_parser_obj(country_data['color'])
        return country_colors

    def get_country_color(self, country):
        return self.tag_to_color_mapping[country.tag]

    @cached_property
    @disk_cache()
    def country_histories(self) -> dict[str, dict[str, object]]:
        return {c.tag: self.parser.parse_file('history/countries/' + c.tag + '*.txt').get_entries_at_date()
                for c in self.all_countries.values()}

    def _parse_government_attribute_value(self, value):
        if isinstance(value, String):
            if value.val.lower() == 'yes':
                return True
            if value.val.lower() == 'no':
                return False
            return value.val
        if isinstance(value, Number):
            return value.val
        return value

    @cached_property
    def government_type_with_reform_tiers(self):
        result = {}
        for gov_type, gov_data in self.parser.merge_parse('common/governments/*'):
            if gov_type == 'pre_dharma_mapping':
                continue
            tiers = {'basic': [str(gov_data['basic_reform'])]}
            for tier, reforms in gov_data['reform_levels']:
                reforms = [str(reform) for reform in reforms['reforms']]
                tiers[str(tier)] = reforms
            result[str(gov_type)] = tiers
        return result

    @cached_property
    def all_government_reforms(self) -> dict[str, GovernmentReform]:
        reforms_to_type_and_tier = {}
        for gov_type, tiers in self.government_type_with_reform_tiers.items():
            tier_num = 0
            for tier, reforms in tiers.items():
                for reform in reforms:
                    reforms_to_type_and_tier[reform] = (gov_type, tier, tier_num)
                tier_num += 1
        all_reforms = {}
        for file, file_data in self.parser.parse_files('common/government_reforms/*'):
            for reform, reform_data in file_data:
                # legacy reforms are not used since patch 1.30 and some of them have the same key as normal reforms,
                # so we can't put them in the same dictionary anyway
                if 'legacy_government' in reform_data and reform_data['legacy_government'] == 'yes':
                    continue
                reform_name = str(reform)
                if reform_name == 'defaults_reform':
                    continue
                basic_attributes = {'basic_reform': False, 'icon': None, 'modifiers': None, 'potential': None,
                                    'trigger': None, 'effect': None, 'removed_effect': None,
                                    'post_removed_effect': None, 'conditional': []}
                other_attributes = {}
                for k, v in reform_data:
                    # 'allow_normal_conversion' is ignored, because it doesnt seem to have a gameplay impact
                    if k in ['allow_normal_conversion', 'ai', 'legacy_equivalent', 'valid_for_nation_designer',
                             'nation_designer_cost', 'nation_designer_trigger']:
                        continue
                    if k == 'basic_reform' and v == 'yes':
                        basic_attributes['basic_reform'] = True
                    elif k == 'custom_attributes':
                        for attribute_key, attribute_value in v:
                            other_attributes[str(attribute_key)] = self._parse_government_attribute_value(
                                attribute_value)
                    elif k == 'conditional':
                        condition = ''
                        condition_attributes = {}
                        for conditional_key, conditional_value in v:
                            if conditional_key == 'allow':
                                condition = conditional_value
                            elif conditional_key == 'custom_attributes':
                                for attribute_key, attribute_value in conditional_value:
                                    condition_attributes[str(attribute_key)] = self._parse_government_attribute_value(
                                        attribute_value)
                            else:
                                condition_attributes[str(conditional_key)] = self._parse_government_attribute_value(
                                    conditional_value)
                        basic_attributes['conditional'].append((condition, condition_attributes))
                    elif k in basic_attributes:
                        basic_attributes[k] = self._parse_government_attribute_value(v)
                    else:
                        other_attributes[str(k)] = self._parse_government_attribute_value(v)
                if reform_name in reforms_to_type_and_tier:
                    gov_type, tier, tier_num = reforms_to_type_and_tier[reform_name]
                    all_reforms[reform_name] = GovernmentReform(reform_name, self.localize(reform_name), gov_type, tier,
                                                                tier_num, attributes=other_attributes,
                                                                **basic_attributes)
                else:
                    print("Error: Reform {} has no tier".format(reform_name))
        return all_reforms

    @cached_property
    def common_government_reforms(self) -> dict[str, dict[str, int]]:
        common_reforms = {}
        all_reforms = {}
        for gov_type, tiers in self.government_type_with_reform_tiers.items():
            for tier_num, (tier, reforms) in enumerate(tiers.items()):
                for reform_id in reforms:
                    if reform_id in all_reforms:
                        if reform_id not in common_reforms:
                            common_reforms[reform_id] = all_reforms[reform_id]
                        common_reforms[reform_id][gov_type] = tier_num
                    else:
                        all_reforms[reform_id] = {gov_type: tier_num}
        return common_reforms

    @cached_property
    def all_estates(self):
        """returns a dictionary. keys are names and values are Estate objects"""
        estates = {}
        for name, data in self.parser.merge_parse('common/estates/*'):
            if name == 'estate_special':
                continue
            privileges = [p.val for p in data['privileges']]
            agendas = [p.val for p in data['agendas']]
            estates[name] = Estate(name, self.localize(name), privileges=privileges, agendas=agendas)
        return estates


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == '--eu4-version':
        # just print the version number so external scripts can use it
        print(eu4_version())
    else:
        raise Exception("unknown parameters. Only --eu4-version is accepted")
