starting_prompt =   """Do not mention your name or any names of users in later messages.
                    When playing a game of Dungeons and Dragons, try to be descriptive and creative."""

worlds = {
    'Azeroth': """The game world is a fantasy world where magic is real and anything can happen.
                It takes place in the world of Azeroth, a world of swords and sorcery.
                The game is set in the year 20XX, a time of great turmoil and strife.
                The world is in the midst of a great war between the forces of good and evil.
                The forces of good are led by the mighty king, King Arthur.
                The forces of evil are led by the evil wizard, Merlin.
                """,
}

dnd_prompt = """Let's play a game of dungeon and dragons. 
                You will be the dungeon master and I will be the player. 
                The dungeon master will describe the scene and the player will respond with an action.
                The dungeon master will then describe the results of the action.
                The player will then respond with another action and so on.
                
                """ + worlds['Azeroth'] + """

                The game begins in a random location in the world.
                
                First prompt to begin by creating characters for players to play as.
                Ask only for the race and class of the characters.
                Ask players for character creation until the players say they are done, then start the game."""