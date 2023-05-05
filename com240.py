import argparse
import re

operands = {
            "ADD" : "{rd} <- {rs1} + {rs2}",
            "ADDI": "{rd} <- {rs1} + {imm}",
            "AND" : "{rd} <- {rs1} AND {rs2}",
            "BRA" : "goto {label}",
            "BRC" : "if carry, goto {label}",
            "BRN" : "if negative, goto {label}",
            "BRNZ": "if negative or zero, goto {label}",
            "BRV" : "if overflow, goto {label}",
            "BRZ" : "if zero, goto {label}",
            "LI"  : "{rd} <- {imm}",
            "LW"  : "{rd} <- M[{rs1} + {imm}]",
            "MV"  : "{rd} <- {rs1}",
            "NOT" : "{rd} <- {rs1} NOT {rs2}",
            "OR"  : "{rd} <- {rs1} OR {rs2}",
            "SLL" : "{rd} <- {rs1} << {rs2}",
            "SLLI": "{rd} <- {rs1} << {shamt}",
            "SLT" : "{rs1} - {rs2}",
            "SLTI": "{rs1} - {imm}",
            "SRA" : "{rd} <- {rs1} >>> {rs2}",
            "SRAI": "{rd} <- {rs1} >>> {imm}",
            "SRL" : "{rd} <- {rs1} >> {rs2}",
            "SRLI": "{rd} <- {rs1} >> {shamt}",
            "STOP": "all done",
            "SUB" : "{rd} <- {rs1} - {rs2}",
            "SW"  : "M[{rs1} + {imm}] <- {rs2}",
            "XOR" : "{rd} <- {rs1} XOR {rs2}"
           }

modes = sorted(operands.keys(), key=len, reverse=True)
modes = re.compile("|".join(modes))

register = {"ADD", "AND", "NOT", "OR", "SLL", "SRA", "SRL", "SUB", "XOR"}
branch = {"BRA", "BRC", "BRN", "BRNZ", "BRV", "BRZ"}
load = {"LI"}
move = {"MV"}
immediate = {"ADDI", "LW", "SLLI", "SRAI", "SRLI", "SW"}
less_than = {"SLT"}
less_than_imm = {"SLTI"}
stop = {"STOP"}

def swap_entries(A, B):
  j = 0
  for i in range(len(A)):
    stripped_entry = A[i].strip()
    if len(stripped_entry) != 0:
      A[i] = B[j]
      j += 1

def align_labels(Lines):
  lines = []
  for Line in Lines:
    assembly_code = Line.strip()
    if len(assembly_code) != 0:
      lines.append(assembly_code)

  for i in range(len(lines)):
    capitalized_line = lines[i].upper()
    sanitized = re.sub(",", "", capitalized_line)
    lines[i] = sanitized

  matches = [re.search(modes, line) for line in lines]

  lengths = []
  for match in matches:
    operand_start = match.span()[0]
    if operand_start != 0:
      lengths.append(operand_start - 1)

  maximum_length = max(lengths)
  maximum_offset = (maximum_length + 1) *  " "

  for i in range(len(lines)):
    instruction_components = lines[i].split()
    if re.search(modes, instruction_components[0]) is not None:
      instruction_components[0] = maximum_offset + instruction_components[0]
    else:
      offset = (maximum_length - len(instruction_components[0])) * " "
      instruction_components[0] = instruction_components[0] + offset

    lines[i] = " ".join(instruction_components) + "\n"

  swap_entries(Lines, lines)

def align_instructions(Lines):
  lines = []
  for Line in Lines:
    assembly_code = re.search(modes, Line)
    if assembly_code is not None:
      lines.append(Line.rstrip())

  matches = [re.search(modes, line) for line in lines]

  lengths = []
  for match in matches:
    span = match.span()
    lengths.append(span[1] - span[0])

  maximum_length = max(lengths)
  lengths = [maximum_length - length for length in lengths]

  for i in range(len(matches)):
    last_char = matches[i].span()[1]
    offset = lengths[i] * " "

    lines[i] = lines[i][:last_char] + offset + lines[i][last_char:] + "\n"

  swap_entries(Lines, lines)

def create_comments(lines):
  comments = []
  for i in range(len(lines)):
    line = lines[i]

    operand, args = line[0], line[2]
    comment = operands[operand]

    if operand in register:
      rd, r1, rs2 = args
      comment = comment.format(rd=rd, rs1=rs1, rs2=rs2)

    if operand in branch:
      label = args
      comment = comment.format(label=label)

    if operand in load:
      rd, imm = args
      comment = comment.format(rd=rd, imm=imm)

    if operand in move:
      rd, rs1 = args
      comment = comment.format(rd=rd, rs1=rs1)

    if operand in immediate:
      rd, rs1, imm = args
      comment = comment.format(rd=rd, rs1=rs1, imm=imm)

    if operand in less_than:
      rd, rs1, rs2 = args
      comment = comment.format(rd=rd, rs1=rs1, rs2=rs2)

    if operand in less_than_imm:
      rd, rs1, imm = args
      comment = comment.format(rd=rd, rs1=rs1, rs2=rs2)

    instruction_offset = line[1] * " "
    comment_offset = line[3] * " "

    arguments = " ".join(args)
    instruction = operand +  instruction_offset + arguments
    comment = comment_offset + " ; " + comment + "\n"

    comments.append(instruction + comment)

  return comments

def write_comments(Lines, comments):
  j = 0
  for i in range(len(Lines)):
    Line = Lines[i]
    match = re.search(modes, Line)
    if match is not None:
      start = match.span()[0]
      Lines[i] = Line[:start] + comments[j]
      j += 1

def insert_comments(Lines):
  matches = [re.search(modes, Line) for Line in Lines]

  lines, lengths = [], []
  for i in range(len(Lines)):
    match, line  = matches[i], Lines[i]
    if match is not None:
      start, end = match.span()
      lengths.append(len(line) - start)
      operand, args = line[start: end], line[end:].strip()

      if operand in stop:
        lines.append([operand, 0, args.split()])
        continue

      for j in range(end, len(Lines[i])):
        if not line[j].isspace():
          lines.append([operand, j - end, args.split()])
          break

  maximum_length = max(lengths)

  for i in range(len(lines)):
    line, length = lines[i], maximum_length - lengths[i]
    line.append(length)

  comments = create_comments(lines)

  write_comments(Lines, comments)

def remove_comments(Lines):
  for i in range(len(Lines)):
    try:
      j = Lines[i].index(";")
      Lines[i] = Lines[i][:j].rstrip() + "\n"
    except ValueError:
      continue

def read_lines(filename):
  with open(filename, "r+") as File:
    Lines = File.readlines()

  return Lines

def write_lines(filename, Lines):
  with open(filename, "w+") as File:
    File.writelines(Lines)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
                      prog="com240",
                      description="Document Register-Transfer Levels for the RISC240 ISA")
  parser.add_argument("filename",
                      help="RISC240 Assembly Program")

  args = parser.parse_args()
  filename = args.filename

  Lines = read_lines(filename)
  remove_comments(Lines)
  write_lines(filename, Lines)

  Lines = read_lines(filename)

  align_labels(Lines)
  align_instructions(Lines)
  insert_comments(Lines)

  write_lines(filename, Lines)

