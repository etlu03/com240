import argparse
import re

operands = {
            "ADD" : "{} <- {} + {}",
            "ADDI": "{} <- {} + {}",
            "AND" : "{} <- {} AND {}",
            "BRA" : "goto {}",
            "BRC" : "if carry, goto {}",
            "BRN" : "if negative, goto {}",
            "BRNZ": "if negative or zero, goto {}",
            "BRV" : "if overflow, goto {}",
            "BRZ" : "if zero, goto {}",
            "LI"  : "{} <- {}",
            "LW"  : "{} <- M[{} + {}]",
            "MV"  : "{} <- {}",
            "NOT" : "{} <- {} NOT {}",
            "OR"  : "{} <- {} OR {}",
            "SLL" : "{} <- {rs1} << {}",
            "SLLI": "{} <- {rs1} << {}",
            "SLT" : "{} - {}",
            "SLTI": "{} - {}",
            "SRA" : "{} <- {} >>> {}",
            "SRAI": "{} <- {} >>> {}",
            "SRL" : "{} <- {} >> {}",
            "SRLI": "{} <- {} >> {}",
            "STOP": "all done",
            "SUB" : "{} <- {} - {}",
            "SW"  : "M[{} + {}] <- {}",
            "XOR" : "{} <- {} XOR {}"
           }

modes = sorted(operands.keys(), key=len, reverse=True)
modes = re.compile("|".join(modes))

three_args = {"ADD", "ADDI",  "AND", "LW",   "NOT", "OR",
              "SLL", "SLLI", "SRA", "SRAI", "SRL", "SRLI",
              "SUB", "SW", "XOR"}
two_args   = {"LI", "MV", "SLT", "SLTI"}
one_args   = {"BRA", "BRC", "BRN", "BRNZ", "BRV", "BRZ"}

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

def retrieve_comments(lines):
  comments = []
  for i in range(len(lines)):
    line = lines[i]

    operand, args = line[0], line[2]
    comment = operands[operand]

    if operand in three_args:
      arg1, arg2, arg3 = args
      comment = comment.format(arg1, arg2, arg3)
    elif operand in two_args:
      arg1, arg2 = args
      comment = comment.format(arg1, arg2)
    elif operand in one_args:
      arg = args
      comment = comment.format(arg1)

    instruction_offset = line[1] * " "
    comment_offset = line[3] * " "

    arguments = " ".join(args)
    instruction = operand +  instruction_offset + arguments
    comment = comment_offset + " ; " + comment + "\n"

    comments.append(instruction + comment)

  return comments

def insert_comments(Lines, comments):
  j = 0
  for i in range(len(Lines)):
    Line = Lines[i]
    match = re.search(modes, Line)
    if match is not None:
      start = match.span()[0]
      Lines[i] = Line[:start] + comments[j]
      j += 1

def write_comments(Lines):
  matches = [re.search(modes, Line) for Line in Lines]

  lines, lengths = [], []
  for i in range(len(Lines)):
    match, line  = matches[i], Lines[i]
    if match is not None:
      start, end = match.span()
      lengths.append(len(line) - start)
      operand, args = line[start: end], line[end:].strip()

      if operand == "STOP":
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

  comments = retrieve_comments(lines)

  insert_comments(Lines, comments)

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

def clear_comments(filename, Lines):
  remove_comments(Lines)
  write_lines(filename, Lines)

def format_file(filename, Lines):
  align_labels(Lines)
  align_instructions(Lines)
  write_lines(filename, Lines)

def main(filename, Lines):
  clear_comments(filename, Lines)
  format_file(filename, Lines)
  write_comments(Lines)
  write_lines(filename, Lines)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
                      prog="com240",
                      description="Document Register-Transfer Levels for the RISC240 ISA")
  parser.add_argument("filename",
                      help="name of RISC240 program")
  parser.add_argument("-r", "--remove",
                      action="store_true",
                      help="remove existing comments",
                      required=False);
  parser.add_argument("-f", "--format",
                      action="store_true",
                      help="normalize RISC240 program",
                      required=False)

  args = parser.parse_args()
  filename, remove, format = args.filename, args.remove, args.format

  Lines = read_lines(filename)
  if remove:
    clear_comments(filename, Lines)
  elif format:
    format_file(filename, Lines)
  else:
    main(filename, Lines)

