![Dice](./doc/dice.png "The Dice Bot")

# Discord Dice Bot
##### Created by **[Ethang70](https://github.com/Ethang70)** and **[stevethewright](https://github.com/stevethewright)**.
An essential Discord Bot written in Python that can roll a die plus a few extra things.

## Libraries and Imported Tools
* ### [discord.py](https://github.com/Rapptz/discord.py)
* ### [Wavelink](https://github.com/PythonistaGuild/Wavelink)

## Core Features
* Play music and YouTube videos through voice chat audio.
* Rolling a die. How could we forget! Roll one or multiple die with many sides.
* Play some fun and silly text based games such as Guess the Number.

# Command List
All commands are initiated using **/** as the prefix.

## Music
To play music in a voice channel, the song or video name must be typed in to the music text channel. This will search YouTube and begin playing your audio.

### **/dc**
Disconnects the bot from the current voice channel immediately. Audio queue is cleared.

### **/mv**
Swaps the position of songs in a queue. For example, to swap song 1 with song 3:
> **/mv** 1 3

### **/np**
Shows information about what audio is currently being played in the voice chat.

### **/q**
Brings up the current music queue. This can also be seen in the music text channel.

### **/rm**
Removes a song in the queue at a certain position. For example, to remove audio at the 4th position:
> **/rm** 4

### **/seek**
Jumps to a specified time within the audio. To jump 5 minutes in:
> **/seek** 05:00

When working with audio that is longer than an hour, specify the hour:
> **/seek** 01:00:00

### **/setup**
Sets up the music text channel.

### **/terminate**
Deletes the music text channel.

### **/update**
Forces the musix text channel to update.

### **/vol**
Changes volume of the audio player. Requires a specified volume in percent from 0% - 500%. For example, to change the volume to 50%:
> **/vol** 50

**Note:** This really changes the gain of the player so when going above **100%** the song can start to sound **distorted**.

## Games
Fun and silly text games.

### **/factorcap**
The bot will say if the above message is facts or cap.

### **/gtn**
Play a game of Guess the Number with the Dice Bot. The game when initiated without parameters will make you have to guess a number between 0 and 100. You can specify the low range and the high range, for example, this will set the guessing range from 100 - 200:
> **/gtn** 100 200

### **/question**
Ever wanted to ask a die a question? Well you're in luck, enter in your question after the command and the bot will answer it!
> **/question** Will I have a good day today?

### **/rps**
Play Rock Paper Scissors with the bot! Enter your move and see if you can beat the bot!

> **/rps** r
>
> **/rps** p
>
> **/ rps** s

You can alternatively type out rock, paper or scissors.

## Other Commands

### **/clear**
Clears a specified amount of messages from the text channel the command is sent from. For example, to remove 5 previous messages:
> **/clear** 5

### **/rtd**
Probably the most important command. Rolls a die. You can further specify how many die you'd like to roll and how many sides each die should have.
> **/rtd**

When specifying the number of rolls:
> **/rtd** number_rolls:3

When specifying the number of sides:
> **/rtd** number_faces:12

You can combine these together:
> **/rtd** number_rolls:3 number_faces:12

### **/sid**
Provides a summoner's ID of a League of Legends player in the OCE region.
> **/sid** PinguPaterson

# Planned Features
* Integration with Spotify
* Ability to change music EQ
* Voting system
* Countdown timer

# Release Notes

## v1.0
* Version 1 complete
* Moved to latest discord.py
* Overhaul of commands, changed to discord slash format
* Added buttons for music interaction
* Moved from lavalink to wavelink

## v0.6
* Reduced number of soings in the queue allowed

## v0.5
* Created a rock paper scissors game
* Removed errors when reactions are added to any messages in a server

## v0.4
* Updated the help command to work for all variables

## v0.3
* Gave the bot an idle time and not immediately leave the voice chat call
* Added rest of basic music bot functionality

## v0.2
* Updated Discord together games to include more games
* Moved to Lavalink for music
* Privatised some variables

## v0.1
* Added Discord together games
* Added basic music functionality
* Modified Dice Rolls to be less spammy
* Added a Guess the Number game