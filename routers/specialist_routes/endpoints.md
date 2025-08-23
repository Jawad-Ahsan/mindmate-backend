write patient-profile.py with following endpoints 


1stly create patient_profiles.py methods for creating 

i want to createfollowing patient profiles

1: public -> that is acessible to assigned specialist

3: protected-> that is acessible to admins only

2: private -> that is accessible to himself only 

1stly create patient_profiles.py methods for creating 

then create the patient_profile_router.py with respective endpoints
/patient-public-profile

/patient-protected-profile

/patient-private-profile


/get-specialist-public-profile

/get-specialist-protected-profile

/get-specialist-private-profile


comprehensive specialist profiles 2 profiles, 

1 : Public -> that is public to patients only necessary info for patients to know and decide : Not personal documents / info like cnic,

2 :protected -> that is accessible to admins and himself  incuding documents + all complete profile info 


using langchain create the two llm_wrappers for creating question goal based but in the natural way and empathetic and context understanding 

the other one for analyzing_answers to infer whether the required goal is achieved or not?

both  wrappers use chain of thought reasoning mechanism and work async 

theyworks togather to create a robust workflow that can work as the  chat bot to collect the informatin in the dynamic and natural human like way , just like the whatsapp conversation , concise clear and friendly and also using relvant emojis 

for example to create the workflow for getting details of presenting concern 

, or risk assessment 

but making sure of not going infinite questions for any goal , just put that question in the queue whose info isnt collected and ask one more time in rephrase way after few more questions

but if the question is the most basic like what brings you here today? fr presenting concern ? if the goal is not achived ask again in rephrase and polite, friendly way 

for now create the general pima_llm_wrapper that has general modules of question creating and answers analyzing modules that are reusable , and composable 

also try to optimize the speed for faster answer, question for smooth chatting experience 

use redis if needed, 




