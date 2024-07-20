#!/usr/bin/env python3
import csv
import os
import re
import string
from operator import attrgetter

import sys
# add the parent folder to the path so that imports work even if the working directory is the eu4 folder
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from eu4.wiki import get_SVersion_header, WikiTextConverter
from eu4.paths import eu4_major_version, eu4outpath
from eu4.mapparser import Eu4Parser
from eu4.eu4lib import Idea, Policy
from eu4.modifier_list import all_modifiers


class BonusTableGenerator:

    header = '<includeonly>' + get_SVersion_header('table') + '''
{{{!}} class="mildtable plainlist mw-collapsible {{#ifeq: {{lc:{{{collapse|}}}}}|yes|mw-collapsed|}}"
! style="width:30px" {{!}} {{icon|{{{1}}}|24px}}
! style="min-width:120px" {{!}} Traditions
! style="min-width:240px" {{!}} Ideas
! style="min-width:120px" {{!}} Bonuses
! style="min-width:240px" {{!}} Policies
{{#switch:{{lc:{{{1}}}}}'''

    footer = '''| national revolt risk
| global revolt risk = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“national revolt risk”'' was removed/renamed with patch 1.8.</span>[[Category:Bonus table outdated]]
| merchant steering towards inland
| merchant steering to inland = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“merchant steering towards inland”'' was removed with patch 1.10.</span>[[Category:Bonus table outdated]]
| building power cost
| build power cost = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“building power cost”'' was removed with patch 1.12.</span>[[Category:Bonus table outdated]]
| goods produced nationally
| global trade goods size = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“goods produced nationally”'' was renamed with patch 1.12.</span>[[Category:Bonus table outdated]]
| national trade income modifier
| global trade income modifier = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“national trade income modifier”'' was removed with patch 1.13.</span>[[Category:Bonus table outdated]]
| time to fabricate claims
| fabricate claims time = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“time to fabricate claims”'' was renamed with patch 1.16.</span>[[Category:Bonus table outdated]]
| time to justify trade conflict
| justify trade conflict time = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“time to justify trade conflict”'' was renamed with patch 1.16.</span>[[Category:Bonus table outdated]]
| national spy defense
| global spy defense = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“national spy defense”'' was renamed with patch 1.16.</span>[[Category:Bonus table outdated]]
| spy offense = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“spy offense”'' was renamed with patch 1.16.</span>[[Category:Bonus table outdated]]
| covert action relation impact
| discovered relations impact = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“covert action relation impact”'' is no more used since patch 1.17.</span>[[Category:Bonus table outdated]]
| accepted culture threshold = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“accepted culture threshold”'' was removed with patch 1.18.</span>[[Category:Bonus table outdated]]
| better relations over time = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“better relations over time”'' was merged with ''“improve_relation_modifier”'' with patch 1.19.</span>[[Category:Bonus table outdated]]
| build cost = {{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“build cost”'' was renamed to ''“construction cost”'' patch 1.19.</span>[[Category:Bonus table outdated]]
| reduce inflation cost
| inflation reduction cost ={{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">Since patch 1.28 no ideas and policies have the modifier ''“reduce inflation cost”''.</span>[[Category:Bonus table outdated]]
| transport power
| transport combat ability =
{{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">Since patch 1.26 no ideas and policies have the modifier ''“transport combat ability”''.</span>[[Category:Bonus table outdated]]
| number of states =
{{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“number of states”'' was removed with patch 1.30.</span>[[Category:Bonus table outdated]]
| available mercenaries =
{{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“available mercenaries”'' was replaced by ''“mercenary manpower”'' with patch 1.30.</span>[[Category:Bonus table outdated]]
| migration cooldown =
{{!}}-
{{!}}colspan="5"{{!}} <span style="color: red;">The modifier ''“migration cooldown”'' was replaced by ''“migration cost”'' with patch 1.31.</span>[[Category:Bonus table outdated]]

| #default = {{!}}-
{{!}}colspan="5"{{!}}<span style="color: red;">(invalid bonus type “{{lc:{{{1}}}}}” for [[Template:Bonus table]])</span>
}}
{{!}}}</includeonly><noinclude>[[Category:Templates]]{{template doc}}</noinclude>'''

    def __init__(self):
        self.eu4parser = Eu4Parser()
        self.parser = self.eu4parser.parser

    def run(self):
        self.writeFile('bonus_tables', self.generate())

    def generate(self):
        lines = [self.header]
        processed_modifier_names = set()
        for modifier in sorted(all_modifiers, key=lambda m: m.icons[0]):
            lines.append('| {} ='.format("\n| ".join(modifier.icons)))
            if modifier.name not in self.eu4parser.ideas_and_policies_by_modifier:
                lines.append('{{!}}-')
                lines.append('{{!}}colspan="5"{{!}} <span style="color: red;">In patch ' + eu4_major_version() +
                             ' no ideas and policies have the modifier \'\'“' + modifier.icons[0] +
                             '”\'\'</span>[[Category:Bonus table outdated]]')
                continue
            all_values_for_modifier = self.eu4parser.ideas_and_policies_by_modifier[modifier.name].keys()
            for value in sorted(self.eu4parser.ideas_and_policies_by_modifier[modifier.name].keys(), key=lambda x: x if isinstance(x, str) else abs(x)*(-1) ):
                ideas = self.eu4parser.ideas_and_policies_by_modifier[modifier.name][value]
                template_params = {'t': [], 'i': [], 'b': [], 'p': []}
                for idea in self.sort_ideas(ideas):
                    if isinstance(idea, Policy):
                        template_params['p'].append(idea.formatted_name())
                    else:
                        if idea.idea_group.is_basic_idea():
                            formatted_name = '{{grey-bd|' + idea.formatted_name() + '}}'
                        else:
                            formatted_name = idea.formatted_name()
                        if idea.is_bonus():
                            if idea.idea_group.is_basic_idea():
                                if not idea.formatted_name().startswith('Full'):
                                    print('"{}"({})  is the bonus of an idea group with an unclear name'.format(idea.formatted_name(), idea.name))
                            else:
                                if 'ambition' not in formatted_name.lower():
                                    print('"{}"({})  is an ambition with an unclear name'.format(formatted_name, idea.name))
                            template_params['b'].append(formatted_name)
                        elif idea.is_tradition():
                            if 'tradition' not in formatted_name.lower():
                                print('"{}"({}) is a tradition with an unclear name'.format(formatted_name, idea.name))
                            template_params['t'].append(formatted_name)
                        else:
                            template_params['i'].append(formatted_name)

                lines.append('{{BTRow|' + modifier.format_value(value, all_values_for_modifier))
                for param, ideas in template_params.items():
                    if len(ideas) > 0:
                        lines.append("\t|{}= *{}".format(param, "\n*".join(ideas)))
                lines.append('}}')
            processed_modifier_names.add(modifier.name)
        unprocessed_modifier_names = set(self.eu4parser.ideas_and_policies_by_modifier.keys()) - processed_modifier_names
        if unprocessed_modifier_names:
            print('Some idea and policy modifiers are missing from all_modifiers:', file=sys.stderr)
            for modifier in unprocessed_modifier_names:
                print('{}: {}'.format(modifier, [
                    idea.formatted_name() for idea_list in self.eu4parser.ideas_and_policies_by_modifier[modifier].values()
                    for idea in idea_list
                    ]), file=sys.stderr)
        lines.append(self.footer)
        return "\n".join(lines)

    def sort_ideas_key_function(self, idea):
        key = idea.formatted_name()
        if isinstance(idea, Idea) and idea.idea_group.is_basic_idea():
            key = '0' + key # make sure basic ideas get sorted first
        return key

    def sort_ideas(self, ideas):
        return sorted(ideas, key = self.sort_ideas_key_function)

    def writeFile(self, name, content):
        output_file = eu4outpath / '{}.txt'.format(name)
        with output_file.open('w') as f:
            f.write(content)


class PolicyListGenerator:
    colors = {'ADM': '#7de77d', 'DIP': '#7dc3e7', 'MIL': '#e6e77d'}

    def __init__(self, idea_groups: list[str] = None):
        """if idea_groups are specified, only policies for those groups are generated"""
        self.eu4parser = Eu4Parser()
        self.parser = self.eu4parser.parser
        self.formatted_modifiers = None
        self.idea_groups = idea_groups

    def get_policy_list(self, category):
        """all policies of a category (e.g. ADM) as a list"""
        filtered_idea_groups = {self.eu4parser.all_idea_groups[group] for group in ['firepower_ideas', 'liberty_ideas', 'assimilation_ideas']}
        return [policy for policy in self.eu4parser.all_policies.values() if policy.category == category
                and (
                        self.idea_groups is None
                        or
                        len(set(policy.idea_groups) & filtered_idea_groups) > 0
                )]

    def get_policy(self, idea_group1, idea_group2):
        for policy in self.eu4parser.all_policies.values():
            if idea_group1 in policy.idea_groups and idea_group2 in policy.idea_groups:
                return policy
        return None

    def get_overview_header(self, idea_group):
        if idea_group.name == 'horde_gov_ideas':
            return '| style="background-color:{color}" | [[File:Horde Government idea group.png|link=horde government|46px]]<div style="font-size: x-small">Horde</div>'.format(
                color=self.colors[idea_group.category])
        return '| style="background-color:{color}" | [[File:{name} idea group.png|link={name} ideas|46px]]<div style="font-size: x-small">{name}</div>'.format(
            color=self.colors[idea_group.category],
            name=idea_group.short_name()
        )

    def get_overview_line(self, idea_group, other_groups):
        lines = ['|-', self.get_overview_header(idea_group)]  # one line in the table, but multiple lines in the code
        icon_regex = r'({{icon\|[^}]*}}|\[\[File:[^]]*\]\])'
        regexs = [re.compile(icon_regex + r' {{green\|([^}]*)}}'),
                  re.compile(icon_regex + r' ({{DLC-only\|([^|}]*)\|([^|}]*)}})'),
                  re.compile(icon_regex + r" '''([-+0-9.%]*)'''"),
                  re.compile(icon_regex + r'() .*'),
                  ]

        for other_group in other_groups:
            policy = self.get_policy(idea_group, other_group)
            if policy:
                rearranged_modifier_lines = []
                for modifierline in self.format_modifiers(policy).splitlines():
                    rearranged_modifier_line = None
                    for regex in regexs:
                        if rearranged_modifier_line:
                            continue  # skip after first match
                        match = regex.search(modifierline)
                        if match:
                            icon = match.group(1)
                            value = match.group(2)
                            if 'DLC-only' in value:
                                if match.group(3) in ['Marines force limit', 'Innovativeness gain']:
                                    value = match.group(4) + '%'
                                else:
                                    raise Exception('unhandled DLC-only ' + value)
                            rearranged_modifier_line = '{value} {icon}'.format(value=value, icon=icon)
                    if rearranged_modifier_line:
                        rearranged_modifier_lines.append(rearranged_modifier_line)
                    else:
                        raise Exception('Cant handle line ' + modifierline)
                        # print('Warning: Cant handle line' + modifierline, file=sys.stderr)

                lines.append('| style="background-color:{}" | {}'.format(self.colors[policy.category], "<br>".join(rearranged_modifier_lines)))
            else:
                lines.append('| &nbsp;')
        return lines

    def build_overview(self):
        idea_groups = {category: sorted([group for group in self.eu4parser.all_idea_groups.values()
                                         if group.category == category], key=attrgetter('display_name'))
                       for category in ['ADM', 'DIP', 'MIL']}

        lines = ['== Overview ==', get_SVersion_header(),
                 '<span style="display:inline-block; width:2.2em; height:2.2em;background-color:#7de77d; border:1px solid black">{{icon|adm}}</span> Administrative points',
                 '<span style="display:inline-block; width:2.2em; height:2.2em;background-color:#7dc3e7; border:1px solid black">{{icon|dip}}</span> Diplomatic points',
                 '<span style="display:inline-block; width:2.2em; height:2.2em;background-color:#e6e77d; border:1px solid black">{{icon|mil}}</span> Military points',
                 '{| class="wikitable" style="text-align:center"',
                 '|-',
                 '!']
        for group in idea_groups['DIP'] + idea_groups['MIL']:
            lines.append(self.get_overview_header(group))
        for group in idea_groups['ADM']:
            lines.extend(self.get_overview_line(group, idea_groups['DIP'] + idea_groups['MIL']))
        for group in idea_groups['MIL']:
            lines.extend(self.get_overview_line(group, idea_groups['DIP']))
        lines.append('|}')
        self.writeFile('eu4policies_overview', lines)

    def build_toc(self, category):
        header = '''{| class="toccolours"
! colspan="4" | Contents
|-valign=top
| style="width:280px" |'''
        lines = [header]
        names = {}
        for policy in self.get_policy_list(category):
            if policy.display_name.startswith('The '):
                names[policy.display_name.removeprefix('The ') + ', The'] = policy.display_name
            else:
                names[policy.display_name] = policy.display_name
        max_lines_in_column = round((len(names) + 26) / 4)
        lines_in_column = []
        columns = 1
        for letter in string.ascii_uppercase:
            lines_in_column.append(';' + letter)
            for name_without_the in sorted(names.keys()):
                if name_without_the[:1].upper() == letter:
                    lines_in_column.append(':[[#{}|{}]]'.format(names[name_without_the], name_without_the))
            if len(lines_in_column) >= max_lines_in_column and columns < 4:
                columns += 1
                lines.extend(lines_in_column)
                lines_in_column = ['| style="width:280px" |']
        lines.extend(lines_in_column)
        lines.append('|}')
        return lines

    def format_modifiers(self, policy):
        if not self.formatted_modifiers:
            modifiers = {policy.name: '\n'.join(['{} = {}'.format(key, value) for key, value in policy.modifiers.items()]) for policy in self.eu4parser.all_policies.values()}
            WikiTextConverter().to_wikitext(modifiers=modifiers, strip_icon_sizes=True)
            self.formatted_modifiers = modifiers
        return self.formatted_modifiers[policy.name]

    def format_policy(self, policy):
        result = [
            '{{policy',
            '|name = ' + policy.display_name,
        ]
        # some mods dont have descriptions for policies
        if len(policy.description) > 0:
            result.append(
                '|desc = ' + policy.description
            )
        result.extend([
                '|ig1 = ' + policy.get_idea_group_short_name(0),
                '|ig2 = ' + policy.get_idea_group_short_name(1),
                '|effect = ' + self.format_modifiers(policy),
                '}}'
        ])
        return result

    def get_policy_section(self, category):
        lines = [get_SVersion_header()]
        lines.extend(self.build_toc(category))
        lines.append('')
        lines.append('{{box wrapper|')
        for policy in self.get_policy_list(category):
            lines.extend(self.format_policy(policy))

        lines.append('}}')
        return '\n'.join(lines)

    def handle_category(self, category, category_display_name):
        lines = ['==[[File:{} power.png|link={} power]]{} policies=='.format(
            category_display_name, category_display_name, category_display_name)]
        lines.append(self.get_policy_section(category))

        self.writeFile('eu4policies_' + category, lines)

    # experiment to use File:, but it has no links
    # @staticmethod
    # def _replace_icon(match):
    #     icon = match.group(1)
    #     if icon in icon_to_filename:
    #         filename = icon_to_filename[icon]
    #     else:
    #         filename = icon
    #     return '[[File:{}.png|28px]]'.format(filename)
    #
    # def replace_icons_with_file_images(self, wikitext):
    #     return re.sub(r'{{icon\|([^}]*)}}', self._replace_icon, wikitext)

    def run(self):
        self.build_overview()
        for category, category_display_name in {'ADM': 'Administrative', 'DIP': 'Diplomatic', 'MIL': 'Military'}.items():
            self.handle_category(category, category_display_name)

    @staticmethod
    def writeFile(name, lines):
        output_file = eu4outpath / '{}.txt'.format(name)
        text = "\n".join(lines)
        with output_file.open('w') as f:
            f.write(text)
            # make sure that the file has a newline at the end.
            # This is helpful so that concatenating multiple files doesn't lead joined lines
            if lines[-1] != '':
                f.write("\n")


class StaticModifiersGenerator:

    def __init__(self):
        self.parser = Eu4Parser()

    def extract_data_from_modifier_line(self, line):
        if line.startswith('* <pre>'):
            line = line.replace('* ', "")
            return '', line, line, ''
        match = re.match(
            r'\* (?P<icon>\{\{icon\|[^}]*\}\}|\[\[[Ff]ile:[^]]*\]\]) (?P<colored_value>(\{\{(red|green)\|)?(?P<value>[^} ]*)(\}\})?) (?P<name>.*)$',
            line)
        if match:
            return match.group('icon'), match.group('colored_value'), match.group('value'), match.group('name')
        else:
            match = re.fullmatch(r'\* (?P<name>[a-zA-Z ]+)', line)
            if match:
                return '', match.group('name'), match.group('name'), ''
            else:
                raise Exception('Unhandled modifier line: ' + line)

    def run(self):
        wiki_converter = WikiTextConverter()

        static_modifiers = {name: modifiers.str(self.parser.parser) for name, modifiers in
                            self.parser.parser.merge_parse('common/static_modifiers/*')}
        wiki_converter.to_wikitext(modifiers=static_modifiers, strip_icon_sizes=True)

        lines = []
        for name, modifiers in static_modifiers.items():
            display_name = self.parser.localize(name)

            lines.append('==={}==='.format(display_name))
            lines.append(get_SVersion_header('table'))
            lines.append('{|')
            for line in modifiers.splitlines():
                icon, colored_value, value, name = self.extract_data_from_modifier_line(line)
                lines.append('| {} || style="text-align:right" | {} || {}'.format(icon, colored_value, name))
                lines.append('|-')
            lines.pop()  # remove extra |-
            lines.append('|}')
            lines.append('')

        PolicyListGenerator.writeFile('static_modifiers', lines)


if __name__ == '__main__':
    StaticModifiersGenerator().run()
    PolicyListGenerator().run()
    BonusTableGenerator().run()


