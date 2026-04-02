# Godding

A tool for connecting things. Break something into parts, put parts back together, check that nothing was left behind.

**"The hand that gives is connected to the hand that receives."**

## What it does

You have an idea. You break it into pieces to understand it. Later, you take scattered pieces and trace them back to one thing. That's it.

```
godding add "your idea"                -- put something in
godding add "part of it"               -- put another thing in
godding link "your idea" "part of it"  -- connect them
godding decompose "your idea"          -- see all the parts
godding compose "part of it"           -- trace it back to where it came from
godding balance                        -- is anything left behind?
```

## Why

Because things get disconnected. Ideas, people, parts of a problem. This tool doesn't fix that — it shows you where the breaks are. You decide what to link. Or not. That's your choice.

## Install

Download a release, or build from source:

```bash
# Requires .NET 8.0 SDK
dotnet build src/Godding/Godding.csproj

# Run
dotnet run --project src/Godding -- add "something" "what it means"
```

## Example: help someone learn something

```bash
# A teacher breaks a subject into parts
godding add "Cooking" "feeding yourself and others"
godding add "Knife skills" "how to cut safely"
godding add "Heat control" "when to turn it up or down"
godding add "Tasting" "knowing when it's right"

godding link Cooking "Knife skills"
godding link Cooking "Heat control"
godding link Cooking Tasting

# A student traces back from what they're struggling with
godding compose "Heat control"
# -> Cooking -> Heat control
# Now they know where it fits

# Check nothing was forgotten
godding balance
```

## Example: understand a problem

```bash
godding add "Why am I stuck" "something isn't working"
godding add "Fear" "afraid of the wrong choice"
godding add "Too many options" "can't pick one"
godding add "No information" "don't know enough yet"

godding link "Why am I stuck" Fear
godding link "Why am I stuck" "Too many options"
godding link "Why am I stuck" "No information"

godding decompose "Why am I stuck"
# Now you can see the parts separately
# Pick one. Start there.
```

## All commands

| Command | What it does |
|---------|-------------|
| `add <name> [description]` | Put something in the tree |
| `link <from> <to>` | Connect two things |
| `unlink <from> <to>` | Disconnect two things |
| `decompose <thing>` | Break it into parts (1 -> many) |
| `compose <thing>` | Trace it back to the source (many -> 1) |
| `tree` | See everything |
| `trace <A> <B>` | Find the path between any two things |
| `balance` | Check that nothing is left behind |
| `search <word>` | Find things by name |
| `show <thing>` | See one thing in detail |
| `list` | List everything |
| `delete <thing>` | Remove something |
| `stats` | Numbers |

## Free

MIT license. Take it, use it, change it. It's not mine. It's not anyone's. It's for all.
