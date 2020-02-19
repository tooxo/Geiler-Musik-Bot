from discord import Embed
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

        self.prefix = self.bot.command_prefix
        self.cogs = self.bot.cogs

        self.bot.remove_command("help")

    def _get_longest_commands_length(self):
        length = 0
        for cn in self.bot.cogs:
            for cmd in self.bot.cogs[cn].get_commands():
                if cmd.hidden:
                    continue
                _length = len(f"{self.prefix}{cmd.name}")
                if _length > length:
                    length = _length
        return length

    @staticmethod
    def _lengthen_string(input_string, length: int):
        _length = length - len(input_string) + 3
        return f"{input_string}{f' ' * _length}"

    async def help_main(self, ctx):
        cogs = {}
        for cog_name in self.cogs:
            cog = self.cogs[cog_name]
            cog: commands.Cog
            string = ""
            _length = self._get_longest_commands_length()
            for command in cog.get_commands():
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
        embed = Embed(title="Help")
        for s in cogs:
            if cogs[s]:
                embed.add_field(name=f"**{s}**", value=cogs[s], inline=False)
        await ctx.send(embed=embed)

    async def help_command(self, ctx, command):
        embed = Embed(title="Help")
        if command not in self.bot.all_commands:
            embed.description = f'"{command}" was not found.'
            return await ctx.send(embed=embed)
        command: commands.Command = self.bot.all_commands[command]
        if len(command.aliases) > 0:
            a = f"{self.prefix}[{command.name}"
            for alias in command.aliases:
                a += f"|{alias}"
            a += "]"
        else:
            a = f"{self.prefix}{command.name}"
        for param in list(command.params.keys())[2:]:
            if (
                command.params[param].kind == "POSITIONAL_OR_KEYWORD"
                or "KEYWORD_ONLY"
            ):
                a += f" <{param}>"
            else:
                a += f" ({param})"
        embed.add_field(name="**Info**", value=command.short_doc, inline=False)
        embed.add_field(name="**Syntax**", value=f"`{a}`", inline=False)
        embed.set_footer(text="Syntax: [alias] <required> (optional)")
        return await ctx.send(embed=embed)

    @commands.command(aliases=["?", "h"], hidden=True)
    async def help(self, ctx, command=None):
        """
        Displays help for the bots commands.
        :param ctx:
        :param command:
        :return:
        """
        if command:
            return await self.help_command(ctx, command)
        return await self.help_main(ctx)
