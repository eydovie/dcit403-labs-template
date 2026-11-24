PEAS	Campus Info Bot
Performance	Correct answers about office locations, hours and contacts; never invents facts; should admit uncertainty and point to the department office; simple replies; should not act like it can take actions.
Environment	New students chatting in a terminal, the facts file, the department office as fallback.
Actuators	Print a text reply only. 
Sensors	The student's typed messages and the facts it was given.


ENVIRONMENT PROPERTIES 
Classification   Justification 
Partially observable   the bot can just see what it has been given, that is the user's inputs. 
Stochastic  outcome is not definite, different students can ask different questions and with different wordings. 
Sequential  the bot needs the inital question in order to answer a follow up questions maintianing context. 
Static  nothing should change while the bot generates a response. 
Discrete    turns of text.
Multi agent The student since they make the choices and ask the questions, the other bot in play canbe from the recieving end; the department office. 
