import argparse
import re

instructions = {
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

operands = sorted(instructions.keys(), key=len, reverse=True)
operands = re.compile("|".join(operands))

register = {"ADD", "AND", "NOT", "OR", "SLL", "SRA", "SRL", "SUB", "XOR"}
branch = {"BRA", "BRC", "BRN", "BRNZ", "BRV", "BRZ"}
load = {"LI"}
move = {"MV"}
immediate = {"ADDI", "LW", "SLLI", "SRAI", "SRLI", "SW"}
less_than = {"SLT"}
less_than_imm = {"SLTI"}
stop = {"STOP"}

def alignLabels(Lines):
  lines = [Line.strip() for Line in Lines if Line.strip()]
  lines = [re.sub(",", "", line.upper()) for line in lines]

  results = [re.search(operands, line) for line in lines]
  lengths = [res.span()[0] - 1 for res in results if res.span()[0]]

  max_length = max(lengths)
  max_offset = (max_length + 1) *  " "

  for i in range(len(lines)):
    instruction = lines[i].split()

    if re.search(operands, instruction[0]):
      instruction[0] = max_offset + instruction[0]
    else:
      offset = (max(lengths) - len(instruction[0])) * " "
      instruction[0] = instruction[0] + offset

    lines[i] = ' '.join(instruction) + "\n"

  j = 0
  for i in range(len(Lines)):
    if Lines[i].strip():
      Lines[i] = lines[j]
      j += 1

def alignInstructions(Lines):
  lines = [Line[:-1] for Line in Lines if re.search(operands, Line)]
  results = [re.search(operands, line) for line in lines]

  lengths = [res.span()[1] - res.span()[0] for res in results]

  max_length = max(lengths)
  lengths = [max_length - length for length in lengths]

  j = 0
  for i in range(len(results)):
    ending = results[i].span()[1]
    offset = lengths[j] * " "

    lines[j] = lines[j][:ending] + offset + lines[j][ending:] + "\n"
    j += 1

  j = 0
  for i in range(len(Lines)):
    if Lines[i].strip():
      Lines[i] = lines[j]
      j += 1

def insertRTL(Lines):
  results = [re.search(operands, Line) for Line in Lines]

  lines, lengths = list(), list()
  for i in range(len(Lines)):
    result = results[i]
    if result:
      lengths.append(len(Lines[i]) - result.span()[0])
      operand = Lines[i][result.span()[0]: result.span()[1]]
      args = Lines[i][result.span()[1]:].strip()

      for j in range(result.span()[1], len(Lines[i])):
        if Lines[i][j].isspace():
          continue
        else:
          lines.append([operand, j - result.span()[1], args.split()])
          break
      if operand in stop:
        lines.append([operand, 0, args.split()])

  max_length = max(lengths)
  lengths = [max_length - length for length in lengths]
  for i in range(len(lines)):
    lines[i].append(lengths[i])

  commented = list()
  for i in range(len(lines)):
    operand = lines[i][0]
    comment = instructions[operand]
    args = lines[i][2]
    if lines[i][0] in register:
      rd, rs1, rs2 = args
      comment = comment.format(rd=rd, rs1=rs1, rs2=rs2)
    elif operand in branch:
      label = args
      comment =comment.format(label=label)
    elif operand in load:
      rd, imm = args
      comment = comment.format(rd=rd, imm=imm)
    elif operand in move:
      rd, rs1 = args
      comment = comment.format(rd=rd, rs1=rs1)
    elif operand in immediate:
      rd, rs1, imm = args
      comment = comment.format(rd=rd, rs1=rs1, imm=imm)
    elif operand in less_than:
      rd, rs1 = args
      comment = comment.format(rd=rd, rs1=rs1)
    elif operand in less_than_imm:
      rd, rs1, imm = args
      comment = comment.format(rd=rd, rs1=rs1, imm=imm)
    elif operand in stop:
      comment = comment

    offset1 = lines[i][1] * " "
    offset2 = lines[i][3] * " "
    arguments = " ".join(args)

    comment = operand + offset1 + arguments + offset2 + " ; " + comment +"\n"
    commented.append(comment)

  j = 0
  for i in range(len(Lines)):
    result = re.search(operands, Lines[i])
    if result:
      Lines[i] = Lines[i][:result.span()[0]] + commented[j]
      j += 1

def removeComments(Lines):
  for i in range(len(Lines)):
    try:
      Lines[i] = Lines[i][:Lines[i].index(";")].rstrip() + "\n"
    except ValueError:
      continue

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
                      prog="com240",
                      description="Document Register-Transfer Levels for the RISC240 ISA")
  parser.add_argument("filename",
                      help="RISC240 Assembly Program")

  args = parser.parse_args()
  filename = args.filename

  with open(filename, "r") as File:
    Lines = File.readlines()
    removeComments(Lines)

  with open(filename, "w") as File:
    File.writelines(Lines)

  with open(filename, "r") as File:
    Lines = File.readlines()

    alignLabels(Lines)
    alignInstructions(Lines)
    insertRTL(Lines)

  with open(filename, "w") as File:
    File.writelines(Lines)

