import discord

from config import client


def eval_bf(code) -> (str, bool):
    code = cleanup(list(code))
    bracemap = buildbracemap(code)

    cells, codeptr, cellptr = [0], 0, 0
    output = ""
    count = 0
    while codeptr < len(code):
        count += 1
        if count > 10000:
            return output, True
        command = code[codeptr]

        if command == ">":
            cellptr += 1
            if cellptr == len(cells): cells.append(0)

        if command == "<":
            cellptr = 0 if cellptr <= 0 else cellptr - 1

        if command == "+":
            cells[cellptr] = cells[cellptr] + 1 if cells[cellptr] < 255 else 0

        if command == "-":
            cells[cellptr] = cells[cellptr] - 1 if cells[cellptr] > 0 else 255

        if command == "[" and cells[cellptr] == 0: codeptr = bracemap[codeptr]
        if command == "]" and cells[cellptr] != 0: codeptr = bracemap[codeptr]
        if command == ".": output += chr(cells[cellptr])

        codeptr += 1
    return output, False


def cleanup(code):
    return ''.join(filter(lambda x: x in ['.', '[', ']', '<', '>', '+', '-'], code))


def buildbracemap(code):
    temp_bracestack, bracemap = [], {}

    for position, command in enumerate(code):
        if command == "[": temp_bracestack.append(position)
        if command == "]":
            start = temp_bracestack.pop()
            bracemap[start] = position
            bracemap[position] = start
    return bracemap


@client.event
async def message(m: discord.Message):
    if m.author.bot:
        return

    if not ((m.content.startswith("```bf") or m.content.startswith("```brainfuck")) and m.content.endswith("```")):
        return

    output, timeout = eval_bf(m.content)
    if timeout:
        return_message = "**program timed out:**```\n"
    else:
        return_message = "**program output:**```\n"

    return_message += output
    return_message += "```"
    await m.reply(content=return_message)
