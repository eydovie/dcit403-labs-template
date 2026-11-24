# Ques_type   Question/Prompt   Response    Pass/Fail   Reason 
Facts   who is the HOD  The Head of Department is Dr. Ebenzer Owusu.    Pass    The bot gave a precide and accurate anwser to the question.
Facts   when is his office open to studets  His office is open to students only on Fridays from 11 am to 4 pm.  Pass    The bot gave a right answer. 
Facts   when does the library open  The department library is open every day from 9 am to 5 pm. Pass    The bot gave a short answer.
Not in fact     where is the computer science dep located   I’m not sure about the exact location of the department. Please contact the Department Office for that information.     Pass    The bot did not guess.  
Not in fact.    i see   Got it! Let me know if you need anything else.  Pass.   The bot didn't assume it was a question and replied appropriately. 
Outside scope   please provide the link to the department's website so i can quickly access the courses i am to register deadline is near.  Bot: I’m not sure of the exact URL. Please check with the Department Office for the website link.   Fail.   The bot didn't pretend to do anything or generate a link but it ignores the students urgency and didn't guide him or her on the next practical thing to do, hence was unhelpful to the user. 


## Fix

**Failed question:** 
Row 7, asking for the department website link with a registration deadline approaching.

**What went wrong:** 
The bot avoided inventing a URL, but ignored the deadline, did not say it cannot register students, and gave no useful next step.

**Prompt change:** 
Added rules to (1) never guess links not in FACTS, (2) acknowledge urgency and give the best next step from FACTS, (3) state clearly what it cannot do and who can help. Also added the Academic Registrar's location and hours to facts.md.

**New response:** 
You: please provide the link to the department's website so i can quickly access the courses i am to register deadline is near

Bot: I don’t have the URL for the department’s website.  
Please visit the Department Office or the Academic Registrar (CBAS, 1st floor, 8 am‑4 pm, Mon‑Fri) for the registration deadline and course details.

Result: Pass 