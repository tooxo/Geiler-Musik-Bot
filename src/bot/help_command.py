"""
Help
"""
from typing import Optional

from discord import Embed, Message
from discord.ext import commands


class Help(commands.Cog):
    """
    Help
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

        self.prefix = self.bot.command_prefix
        self.cogs = self.bot.cogs

        self.bot.remove_command("help")

    def _get_longest_commands_length(self) -> int:
        length = 0
        for cog_name in self.bot.cogs:
            for cmd in self.bot.cogs[cog_name].get_commands():
                if cmd.hidden:
                    continue
                _length = len(f"{self.prefix}{cmd.name}")
                if _length > length:
                    length = _length
        return length

    @staticmethod
    def _lengthen_string(input_string, length: int) -> str:
        _length = length - len(input_string) + 3
        return f"{input_string}{' ' * _length}"

    @staticmethod
    def _split_list(_list: list, _length: int) -> list:
        big_list = []
        counter = 0
        _l = []
        for item in _list:
            if (counter / 10).is_integer() and (counter / 10) != 0.0:
                big_list.append(_l)
                _l = []
            _l.append(item)
            counter += 1
        if len(_l) > 0:
            big_list.append(_l)
        return big_list

    @staticmethod
    def _categorize(_list: list) -> dict:
        _dict = {}
        for item in _list:
            item: commands.Command
            if item.cog_name not in _dict.keys():
                _dict[item.cog_name] = []
            _dict[item.cog_name].append(item)
        return _dict

    @staticmethod
    def _fuse(list_with_sub_lists: list) -> list:
        _l = []
        for sub_list in list_with_sub_lists:
            _l.extend(sub_list)
        return _l

    async def _help_main(self, ctx: commands.Context, page: int = 0) -> Message:
        cogs = {}
        all_commands = []
        for cog in self.bot.cogs:
            for command in self.bot.cogs[cog].get_commands():
                if not command.hidden:
                    all_commands.append(command)
        split_lists = self._split_list(all_commands, 10)
        paged = split_lists[page]
        cats: dict = self._categorize(paged)
        for cog_name in cats:
            cog: commands.Cog = self.cogs[cog_name]
            string = ""
            _length = self._get_longest_commands_length()
            for command in cats[cog_name]:
                command: commands.core.Command
                if command.hidden:
                    continue
                _string = (
                    f"{self._lengthen_string(f'{self.prefix}{command.name}', _length)}"
                    f"{command.short_doc} \n\n"
                )
                string += _string
            if len(string) > 0:
                cogs[cog.qualified_name] = f"```{string}```"
        embed = Embed(title=f"{self.prefix}Help - Page {page + 1}").set_footer(
            text=f"{self.prefix}help <command> for help on a specific command."
        )
        for cog_name in cogs:
            if cogs[cog_name]:
                embed.add_field(
                    name=f"**{cog_name}**", value=cogs[cog_name], inline=False
                )
        return await ctx.send(embed=embed)

    async def help_command(
        self, ctx: commands.Context, command: str, implicit: bool = True
    ) -> Optional[Message]:
        """
        Command to provide help to the user.
        @param ctx:
        @param command:
        @param implicit: If the help command show if a command is not found
        @return:
        """
        embed = Embed(title=f"{self.prefix}Help - {command}")
        if command not in self.bot.all_commands:
            if implicit:
                embed.description = f'"{command}" was not found.'
                return await ctx.send(embed=embed)
            return None
        command: commands.Command = self.bot.all_commands[command]
        if len(command.aliases) > 0:
            syntax_text = f"{self.prefix}[{command.name}"
            for alias in command.aliases:
                syntax_text += f"|{alias}"
            syntax_text += "]"
        else:
            syntax_text = f"{self.prefix}{command.name}"
        for param in list(command.params.keys())[2:]:
            if (
                command.params[param].kind == "POSITIONAL_OR_KEYWORD"
                or "KEYWORD_ONLY"
            ):
                syntax_text += f" <{param}>"
            else:
                syntax_text += f" ({param})"
        embed.add_field(name="**Info**", value=command.short_doc, inline=False)
        embed.add_field(
            name="**Syntax**", value=f"`{syntax_text}`", inline=False
        )
        embed.set_footer(text="Syntax: [alias] <required> (optional)")
        return await ctx.send(embed=embed)

    @commands.command(aliases=["?", "h"], hidden=True)
    async def help(self, ctx: commands.Context, command: str = None):
        """
        Displays help for the bots commands.
        :param ctx:
        :param command:
        :return:
        """
        if command:
            try:
                page = int(command)
                if page == 0:
                    page = 1
                try:
                    return await self._help_main(ctx, page - 1)
                except IndexError:
                    return await ctx.send(
                        embed=Embed(
                            title="Error",
                            description=f"{self.prefix}Help page "
                            f"{page} not found.",
                            color=0xFF0000,
                        )
                    )  # invalid page num
            except (TypeError, ValueError):
                pass  # invalid page num, prop command name
            return await self.help_command(ctx, command)
        return await self._help_main(ctx)
