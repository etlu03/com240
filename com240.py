###############################################################################
#
# @file   com240
# @brief  RISC240 ISA Register-transfer Level Commenter
#
# This script reads a provided assembly program line by line and appends the
# register-transfer level description in the form of a comment following
# each instruction
#
# @author etlu03
#
###############################################################################


from fnmatch import fnmatch
from pathlib import Path

import sys
import argparse
import re


# current RISC240 ISA
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


# divide instructions based on argument count
three_args = {"ADD", "ADDI",  "AND", "LW",   "NOT", "OR",
              "SLL", "SLLI", "SRA", "SRAI", "SRL", "SRLI",
              "SUB", "SW", "XOR"}
two_args   = {"LI", "MV", "SLT", "SLTI"}
one_args   = {"BRA", "BRC", "BRN", "BRNZ", "BRV", "BRZ"}


def swap_elements(A: list[str], B: list[str]) -> None:
  '''
  Exchanges elements from List B to list A if current element
  in list A is not empty

  Key Arguments:
    A: list
    B: list
  '''
  j = 0
  for i in range(len(A)):
    stripped_entry = A[i].strip()
    if len(stripped_entry) != 0:
      A[i] = B[j]
      j += 1


def align_labels(Lines: list[str]) -> None:
  '''
  Ensures all elements in the list `Lines` is aligned with the
  end of the longest label

  Key Arguments:
    Lines: Lines of the Assembly program
  '''
  lines = []
  # extracts all non-empty lines
  for Line in Lines:
    assembly_code = Line.strip()
    if len(assembly_code) != 0:
      lines.append(assembly_code)

  # removes all `,` characters
  for i in range(len(lines)):
    capitalized_line = lines[i].upper()
    sanitized = re.sub(",", "", capitalized_line)
    lines[i] = sanitized

  matches = [re.search(modes, line) for line in lines]

  lengths = []
  # calculates the length of each label
  for match in matches:
    operand_start = match.span()[0]
    if operand_start != 0:
      lengths.append(operand_start - 1)

  # calculates string offset
  maximum_length = max(lengths)
  maximum_offset = (maximum_length + 1) *  " "

  # aligns all lines with the end of the longest label
  for i in range(len(lines)):
    instruction_components = lines[i].split()
    if re.search(modes, instruction_components[0]) is not None:
      instruction_components[0] = maximum_offset + instruction_components[0]
    else:
      offset = (maximum_length - len(instruction_components[0])) * " "
      instruction_components[0] = instruction_components[0] + offset

    lines[i] = " ".join(instruction_components) + "\n"

  swap_elements(Lines, lines)


def align_instructions(Lines: list[str]) -> None:
  '''
  Ensures all element in list `Lines` are aligned with the
  end of the longest instruction

  Key Arguments:
    Lines: Lines of the Assembly program
  '''
  lines = []
  # extracts all lines with a relevant operand
  for Line in Lines:
    assembly_code = re.search(modes, Line)
    if assembly_code is not None:
      lines.append(Line.rstrip())

  matches = [re.search(modes, line) for line in lines]

  lengths = []
  # calculates the length of all used operands
  for match in matches:
    span = match.span()
    lengths.append(span[1] - span[0])

  # calculate offsets
  maximum_length = max(lengths)
  lengths = [maximum_length - length for length in lengths]

  # insert offsets
  for i in range(len(matches)):
    last_char = matches[i].span()[1]
    offset = lengths[i] * " "

    lines[i] = lines[i][:last_char] + offset + lines[i][last_char:] + "\n"

  swap_elements(Lines, lines)


def retrieve_comments(lines: list[str]) -> list[str]:
  '''
  Builds the respective comment for each instruction

  Key Arguments:
    Lines: Lines of the Assembly program
  '''
  comments = []
  # retrieves RTL comment and properly align the entire line
  for i in range(len(lines)):
    line = lines[i]

    operand, args = line[0], line[2]
    comment = operands[operand]

    # checks the number of required arguments
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

    # builds comment
    arguments = " ".join(args)
    instruction = operand +  instruction_offset + arguments
    comment = comment_offset + " ; " + comment + "\n"

    comments.append(instruction + comment)

  return comments


def insert_comments(Lines: list[str], comments: list[str]) -> None:
  '''
  Appends the register-transfer level description to the respective
  element in list `Lines`

  Key Arguemnts:
    Lines: Lines of the Assembly program
    Comments: List of register-transfer level descriptions
  '''
  j = 0
  for i in range(len(Lines)):
    Line = Lines[i]
    match = re.search(modes, Line)
    if match is not None:
      start = match.span()[0]
      Lines[i] = Line[:start] + comments[j]
      j += 1


def write_comments(Lines: list[str]) -> None:
  '''
  Extracts the necessary components from each element in
  list `Lines` to build an register-transfer level description

  Key Arguments:
    Lines: Lines of the Assembly program
  '''
  matches = [re.search(modes, Line) for Line in Lines]

  lines, lengths = [], []
  # extracts operand, instruction offset, arguments
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

  # appends line offset to each element in `lines`
  for i in range(len(lines)):
    line, length = lines[i], maximum_length - lengths[i]
    line.append(length)

  comments = retrieve_comments(lines)

  insert_comments(Lines, comments)


def strip_comments(Lines: list[str]) -> None:
  '''
  Removes the commented-out portion for each element in list `Lines`

  Key Arguments:
    Lines: Lines of the Assembly program
  '''
  for i in range(len(Lines)):
    try:
      j = Lines[i].index(";")
      Lines[i] = Lines[i][:j].rstrip() + "\n"
    except ValueError:
      continue


def read_file(filename: str) -> list[str]:
  '''
  Reads the lines from `filename`

  Key Arguments:
    filename: Path to file
  '''
  with open(filename, "r+") as File:
    Lines = File.readlines()

  return Lines


def write_file(filename: str, Lines: list[str]) -> None:
  '''
  Writes the elements in list `Lines` to `filename`

  Key Arguments:
    filename: Path to file
    Lines: Lines of the Assembly program
  '''
  with open(filename, "w+") as File:
    File.writelines(Lines)


def main(args: argparse.Namespace) -> None:
  '''
  com240 main routine

  Key Arguments:
    args: Command-line arguments
  '''
  filename, remove, format, comment = args.filename, args.remove, args.format, args.comment
  if not fnmatch(filename, "*.asm"):
    file_extension = Path(filename).suffix

    sys.stdout.write(f'Illegal Filename Extension "{file_extension}".\n')
    return

  Lines = read_file(filename)

  # copy a version of the `Lines` to default to
  Old_Lines = list(Lines)

  try:
    if remove or comment or (remove == format):
      strip_comments(Lines)

    if format or comment or (remove == format):
      align_labels(Lines)
      align_instructions(Lines)

    if comment or (remove == format):
      write_comments(Lines)

    write_file(filename, Lines)
  except:
    sys.stdout.write("Oops! Something went wrong.\n")

    write_file(filename, Old_Lines)
    return


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
                      prog="com240",
                      description="Register-transfer Level Documentation for the RISC240 ISA")
  parser.add_argument("filename",
                      help="name of program")
  parser.add_argument("-r", "--remove",
                      action="store_true",
                      help="strip program of existing comments",
                      required=False);
  parser.add_argument("-f", "--format",
                      action="store_true",
                      help="properly format program",
                      required=False)
  parser.add_argument("-c", "--comment",
                      action="store_true",
                      help="write register-transfer levels for each instruction",
                      required=False)

  args = parser.parse_args()
  main(args)

