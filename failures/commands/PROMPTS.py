import textwrap

FAILURE_SYNONYMS = "hack, bug, fault, error, exception, crash, glitch, defect, incident, flaw, mistake, anomaly, or side effect"


POSTMORTEM_QUESTIONS = {
        "title":            "Provide a title describing the software failure incident.",
        "summary":          "Summarize the software failure incident. Include information about when the failure occured, what system failed, the cause of failure, the impact of failure, the responsible entity(s), and the impacted entity(s).",
        "time":             "When did the software failure incident happen?",
        "system":           "What system(s) failed in the software failure incident?",
        "ResponsibleOrg":   "Which entity(s) was responsible for causing the software failure incident?",
        "ImpactedOrg":      "Which entity(s) was impacted by the software failure incident?",
        "SEcauses":         "What were the software causes of the failure incident?",
        "NSEcauses":        "What were the non-software causes of the failure incident?",
        "impacts":          "What were the impacts due to the software failure incident?",
        "preventions":      "What could have prevented the software failure incident?", 
        "fixes":            "What could fix the software failure incident?",
        "references":       "From where do the articles gather information about the software failure incident?",
}

PROMPT_ADDITIONS = {
        "title":        {
                                "before": "",
                                "after": "\nIf available, include information about when the failure occured, what system failed, the cause of failure, the impact of failure, the responsible entity(s), and the impacted entity(s).\nTitle should be around 10 words. Return just the title.",
                        },
        "summary":      {
                                "before": "",
                                "after": "\nAnswer in under 250 words.",
                        },              
        "time":         {
                                "before": "",
                                "after": textwrap.dedent("""
                                        Return in a numbered list (with citations in the format: [#, #, ...]). 

                                        If it is not directly mentioned, estimate the timeline with following steps (Calculate step by step):
                                        Step 1: Find any clues about the time of the incident (ex: last November, Friday, today, etc.) in an article.
                                        Step 2: Find the 'Published on ...' date of that article.
                                        Step 3: Using the published date of the article and the clues about the time of incident, what would be the date of the incident? Example: if the article mentions that the incident occured last November, and the article was Published on 2015-06-27, then the incident occured on November 2014. (If available, atleast return the month and year.)
                                        Note: If the timeline cannot be estimated, then return 'unknown'.
                                        """),
                        },
        "system":        {
                                "before": "",
                                "after": "\nIf specific components or models or versions failed include them. Return the products, systems, components, models and versions that failed in a numbered list (with citations in the format: [#, #, ...]).",
                        },           
        "ResponsibleOrg":       {
                                "before": "",
                                "after": "\nReturn in a numbered list (with citations in the format: [#, #, ...]).",
                        },   #If available, include any background information about the entity(s) and how they contributed to the failure.
        "ImpactedOrg":        {
                                "before": "",
                                "after": "\nReturn in a numbered list (with citations in the format: [#, #, ...]).",
                        },   #If available, include any background information about the entity(s) and how they were impacted by the failure.
        "SEcauses":        {
                                "before": "",
                                "after": "\nDo not return non-software causes. Return in a numbered list (with citations in the format: [#, #, ...]).",
                        },         
        "NSEcauses":        {
                                "before": "",
                                "after": "\nDo not return software causes. Return in a numbered list (with citations in the format: [#, #, ...]).",
                        },        
        "impacts":        {
                                "before": "",
                                "after": "\nReturn in a numbered list (with citations in the format: [#, #, ...]).",
                        },          
        "preventions":        {
                                "before": "",
                                "after": "\nReturn in a numbered list (with citations in the format: [#, #, ...]).",
                        },      
        "fixes":        {
                                "before": "",
                                "after": "\nReturn in a numbered list (with citations in the format: [#, #, ...]).",
                        },                
        "references":        {
                                "before": "",
                                "after": "\nProvide all specific entities from where the articles gather information from. Return in a numbered list (with citations in the format: [#, #, ...]).",
                        },
        "recurring":    {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options (with citations in the format: [#, #, ...]).",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": textwrap.dedent("""
                                                {
                                                "one_organization": true or false,
                                                "multiple_organization": true or false,
                                                "unknown": true or false,
                                                }
                                                """),
                                        },
                        },          
        "phase":        {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options (with citations in the format: [#, #, ...]).",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": textwrap.dedent("""
                                                {
                                                "design": true or false,
                                                "operation": true or false,
                                                "unknown": true or false,
                                                }
                                                """),
                                        },
                        },            
        "boundary":     {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options (with citations in the format: [#, #, ...]).",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": textwrap.dedent("""
                                                {
                                                "within_system": true or false,
                                                "outside_system": true or false,
                                                "unknown": true or false,
                                                }
                                                """),
                                        },
                        },         
        "nature":       {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options (with citations in the format: [#, #, ...]).",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": textwrap.dedent("""
                                                {
                                                "non-human_actions": true or false,
                                                "human_actions": true or false,
                                                "unknown": true or false,
                                                }
                                                """),
                                        },
                        },           
        "dimension":    {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options (with citations in the format: [#, #, ...]).",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": textwrap.dedent("""
                                                {
                                                "hardware": true or false,
                                                "software": true or false,
                                                "unknown": true or false,
                                                }
                                                """),
                                        },
                        },        
        "objective":    {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options (with citations in the format: [#, #, ...]).",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": textwrap.dedent("""
                                                {
                                                "malicious": true or false,
                                                "non-malicious": true or false,
                                                "unknown": true or false,
                                                }
                                                """),
                                        },
                        },        
        "intent":       {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options (with citations in the format: [#, #, ...]).",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": textwrap.dedent("""
                                                {
                                                "poor_decisions": true or false,
                                                "accidental_decisions": true or false,
                                                "unknown": true or false,
                                                }
                                                """),
                                        },
                        },           
        "capability":   {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options (with citations in the format: [#, #, ...]).",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": textwrap.dedent("""
                                                {
                                                "development_incompetence": true or false,
                                                "accidental": true or false,
                                                "unknown": true or false,
                                                }
                                                """),
                                        },
                        },       
        "duration":     {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options (with citations in the format: [#, #, ...]).",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": textwrap.dedent("""
                                                {
                                                "permanent": true or false,
                                                "temporary": true or false,
                                                "unknown": true or false,
                                                }
                                                """),
                                        },
                        }, 
        "behaviour":    {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about all six options (with citations in the format: [#, #, ...]).",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": textwrap.dedent("""
                                                {
                                                "crash": true or false,
                                                "omission": true or false,
                                                "timing": true or false,
                                                "value": true or false,
                                                "byzantine": true or false,
                                                "other": true or false,
                                                "unknown": true or false,
                                                }
                                                """),
                                        },
                        },        
        "domain":       {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select any one option, provide relevant information from the articles about all 13 (a to m) options (with citations in the format: [#, #, ...]).",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": textwrap.dedent("""
                                                {
                                                "information": true or false,
                                                "transportation": true or false,
                                                "natural_resources": true or false,
                                                "sales": true or false,
                                                "construction": true or false,
                                                "manufacturing": true or false,
                                                "utilities": true or false,
                                                "finance": true or false,
                                                "knowledge": true or false,
                                                "health": true or false,
                                                "entertainment": true or false,
                                                "government": true or false,
                                                "other": true or false,
                                                "unknown": true or false,
                                                }
                                                """),
                                        },
                        },
        "consequence":          {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about the nine options (with citations in the format: [#, #, ...]).",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": textwrap.dedent("""
                                                {
                                                "death": true or false,
                                                "harm": true or false,
                                                "basic": true or false,
                                                "property": true or false,
                                                "delay": true or false,
                                                "non-human": true or false,
                                                "no_consequence": true or false,
                                                "theoretical_consequence": true or false,
                                                "other": true or false,
                                                "unknown": true or false,
                                                }
                                                """),
                                        },
                        },           
        "cps":          {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nProvide relevant information from the articles on whether the overall system in the incident is a cyber physical system that meets the given description (with citations in the format: [#, #, ...]).\nIf the overall system includes cyber-physical components, classify it as a cyber-physical system, even if specific subsystems or components do not meet the criteria individually.",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": textwrap.dedent("""
                                                {
                                                "cps": true or false,
                                                "unknown": true or false,
                                                }
                                                """),
                                        },
                        },              
        "perception":   {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about all five options (with citations in the format: [#, #, ...]).",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": textwrap.dedent("""
                                                {
                                                "sensor": true or false,
                                                "actuator": true or false,
                                                "processing_unit": true or false,
                                                "network_communication": true or false,
                                                "embedded_software": true or false,
                                                "unknown": true or false,
                                                }
                                                """),
                                        },
                        },       
        "communication":{
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nDo not select an option, provide relevant information from the articles about both options (with citations in the format: [#, #, ...]).",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": textwrap.dedent("""
                                                {
                                                "link_level": true or false,
                                                "connectivity_level": true or false,
                                                "unknown": true or false,
                                                }
                                                """),
                                        },
                        },    
        "application":  {
                                "rationale": 
                                        {
                                        "before": "",
                                        "after": "\nProvide relevant information from the articles on whether the failure was related to the application layer, of the cyber physical system that failed, that meets the given description (with citations in the format: [#, #, ...]).",
                                        },
                                "decision":
                                        {
                                        "before": "",
                                        "after": textwrap.dedent("""
                                                {
                                                "application": true or false,
                                                "unknown": true or false,
                                                }
                                                """),
                                        },
                        },            
}

TAXONOMY_DEFINITIONS = {
        "recurring":            textwrap.dedent("""
                                The software failure incident having happened again at:
                                (a) one_organization: Similar incident has happened before or again within the same organization or with its products and services
                                (b) multiple_organization: Similar incident has happened before or again at other organizations or with their products and services
                                """),
        "phase":                textwrap.dedent("""
                                The software failure incident occurring due to the development phases:
                                (a) design: Failure due to contributing factors introduced by system development, system updates, or procedures to operate or maintain the system
                                (b) operation: Failure due to contributing factors introduced by the operation or misuse of the system
                                """),
        "boundary":             textwrap.dedent("""
                                The boundary of the software failure incident:
                                (a) within_system: Failure due to contributing factors that originate from within the system 
                                (b) outside_system: Failure due to contributing factors that originate from outside the system
                                """),
        "nature":               textwrap.dedent("""
                                The software failure incident occurring due to:
                                (a) non-human_actions: Failure due to contributing factors introduced without human participation
                                (b) human_actions: Failure due to contributing factors introduced by human actions
                                """),
        "dimension":            textwrap.dedent("""
                                The software failure incident occurring due to:
                                (a) hardware: Failure due to contributing factors that originate in hardware
                                (b) software: Failure due to contributing factors that originate in software
                                """),
        "objective":            textwrap.dedent("""
                                The objective of the software failure incident:
                                (a) malicious: Failure due to contributing factors introduced by human(s) with intent to harm the system
                                (b) non-malicious: Failure due to contributing factors introduced without intent to harm the system
                                """),
        "intent":               textwrap.dedent("""
                                The intent of the software failure incident:
                                (a) poor_decisions: Failure due to contributing factors introduced by poor decisions
                                (b) accidental_decisions: Failure due to contributing factors introduced by mistakes or unintended decisions
                                """),
        "capability":           textwrap.dedent("""
                                The software failure incident occurring due to:
                                (a) development_incompetence: Failure due to contributing factors introduced due to lack of professional competence by humans or development organization
                                (b) accidental: Failure due to contributing factors introduced accidentally
                                """),
        "duration":             textwrap.dedent("""
                                The duration of the software failure incident being:
                                (a) permanent: Failure due to contributing factors introduced by all circumstances
                                (b) temporary: Failure due to contributing factors introduced by certain circumstances but not all
                                """),
        "behaviour":            textwrap.dedent("""
                                The behavior of the software failure incident:
                                (a) crash: Failure due to system losing state and not performing any of its intended functions
                                (b) omission: Failure due to system omitting to perform its intended functions at an instance(s)
                                (c) timing: Failure due to system performing its intended functions correctly, but too late or too early 
                                (d) value: Failure due to system performing its intended functions incorrectly
                                (e) byzantine: Failure due to system behaving erroneously with inconsistent responses and interactions
                                (f) other: Failure due to system behaving in a way not described in the (a to e) options; What is the other behaviour?
                                """),
        "domain":               textwrap.dedent("""
                                The industry that the failed system was intended to support:
                                (a) information: Production and distribution of information
                                (b) transportation: Moving people and things
                                (c) natural_resources: Extracting materials from Earth
                                (d) sales: Exchanging money for products
                                (e) construction: Creating built environment
                                (f) manufacturing: Creating products from materials
                                (g) utilities: Power, gas, steam, water, and sewage services
                                (h) finance: Manipulating and moving money for profit
                                (i) knowledge: Education, research, and space exploration
                                (j) health: Healthcare, health insurance, and food industries
                                (k) entertainment: Arts, sports, hospitality, tourism, etc
                                (l) government: Politics, defense, justice, taxes, public services, etc
                                (m) other: Was the system that failed related to an industry not described in the (a to l) options? What is the other industry?
                                """),
        "consequence":          textwrap.dedent("""
                                The consequence of the software failure incident:
                                (a) death: People lost their lives due to the software failure
                                (b) harm: People were physically harmed due to the software failure
                                (c) basic: People's access to food or shelter was impacted because of the software failure
                                (d) property: People's material goods, money, or data was impacted due to the software failure
                                (e) delay: People had to postpone an activity due to the software failure
                                (f) non-human: Non-human entities were impacted due to the software failure
                                (g) no_consequence: There were no real observed consequences of the software failure
                                (h) theoretical_consequence: There were potential consequences discussed of the software failure that did not occur
                                (i) other: Was there consequence(s) of the software failure not described in the (a to h) options? What is the other consequence(s)?
                                """),
        "cps":                  textwrap.dedent("""
                                Whether the overall system in the incident is a cyber physical system (cps) meeting the following definition:
                                cps: Systems that include software and physical components to monitor and/or control physical interactions
                                """),
        #CPS:
        "perception":           textwrap.dedent("""
                                Whether the failure was related to the perception layer of the cyber physical system that failed:
                                (a) sensor: Failure due to contributing factors introduced by sensor error
                                (b) actuator: Failure due to contributing factors introduced by actuator error
                                (c) processing_unit: Failure due to contributing factors introduced by processing error
                                (d) network_communication: Failure due to contributing factors introduced by network communication error
                                (e) embedded_software: Failure due to contributing factors introduced by embedded software error
                                """),
        "communication":        textwrap.dedent("""
                                Whether the failure was related to the communication layer of the cyber physical system that failed:
                                (a) link_level: Failure due to contributing factors introduced by wired or wireless physical layer
                                (b) connectivity_level: Failure due to contributing factors introduced by network or transport layer
                                """),
        "application":          textwrap.dedent("""
                                Whether the failure was related to the application layer of the cyber physical system that failed with the following definition:
                                application: Failure due to contributing factors introduced by bugs, operating system errors, unhandled exceptions, and incorrect usage
                                """),
}

TAXONOMY_QUESTIONS = {
        "recurring":            textwrap.dedent("""
                                (a) one: Have similar incident(s) happened before or again within the same organization or with its products and services?
                                (b) multiple: Have similar incident(s) happened before or again at other organizations or with their products and services?
                                """),
        "phase":                textwrap.dedent("""
                                (a) design: Was the failure due to at least one contributing factor introduced by system development, system updates, or procedures to operate or maintain the system?
                                (b) operation: Was the failure due to at least one contributing factor introduced by the operation or misuse of the system?
                                """),
        "boundary":             textwrap.dedent("""
                                (a) within_system: Was the failure due to at least one contributing factor that originates from within the system?
                                (b) outside_system: Was the failure due to at least one contributing factor that originates from outside the system?
                                """),
        "nature":               textwrap.dedent("""
                                (a) non-human_actions: Was the failure due to at least one contributing factor introduced without human participation?
                                (b) human_actions: Was the failure due to at least one contributing factor introduced by human actions?
                                """),
        "dimension":            textwrap.dedent("""
                                (a) hardware: Was the failure due to at least one contributing factor that originates in hardware?
                                (b) software: Was the failure due to at least one contributing factor that originates in software?
                                """),
        "objective":            textwrap.dedent("""
                                (a) malicious: Was the failure due to at least one contributing factor introduced by human(s) with intent to harm the system?
                                (b) non-malicious: Was the failure due to at least one contributing factor introduced without intent to harm the system?
                                """),
        "intent":               textwrap.dedent("""
                                (a) poor_decisions: Was the failure due to at least one contributing factor introduced by poor decisions?
                                (b) accidental_decisions: Was the failure due to at least one contributing factor introduced by mistakes or unintended decisions?
                                """),
        "capability":           textwrap.dedent("""
                                (a) development_incompetence: Was the failure due to at least one contributing factor introduced due to lack of professional competence by humans or development organization?
                                (b) accidental: Was the failure due to at least one contributing factor introduced accidentally?
                                """),
        "duration":             textwrap.dedent("""
                                (a) permanent: Was the failure due to at least one contributing factor introduced by all circumstances?
                                (b) temporary: Was the failure due to at least one contributing factor introduced by certain circumstances but not all?
                                """),
        "behaviour":            textwrap.dedent("""
                                (a) crash: Was the failure due to system losing state and not performing any of its intended functions?
                                (b) omission: Was the failure due to system omitting to perform its intended functions at an instance(s)?
                                (c) timing: Was the failure due to system performing its intended functions correctly, but too late or too early?
                                (d) value: Was the failure due to system performing its intended functions incorrectly?
                                (e) byzantine: Was the failure due to system behaving erroneously with inconsistent responses and interactions?
                                (f) other: Was the failure due to system behaving in a way not described in the other options?
                                """),
        "domain":               textwrap.dedent("""
                                (a) information: Was the system that failed related to the industry of production and distribution of information?
                                (b) transportation: Was the system that failed related to the industry of moving people and things?
                                (c) natural_resources: Was the system that failed related to the industry of extracting materials from Earth?
                                (d) sales: Was the system that failed related to the industry of exchanging money for products?
                                (e) construction: Was the system that failed related to the industry of creating built environment?
                                (f) manufacturing: Was the system that failed related to the industry of creating products from materials?
                                (g) utilities: Was the system that failed related to the industry of power, gas, steam, water, and sewage services?
                                (h) finance: Was the system that failed related to the industry of manipulating and moving money for profit?
                                (i) knowledge: Was the system that failed related to the industry of education, research, and space exploration?
                                (j) health: Was the system that failed related to the industry of healthcare, health insurance, and food industries?
                                (k) entertainment: Was the system that failed related to the industry of arts, sports, hospitality, tourism, etc?
                                (l) government: Was the system that failed related to the industry of politics, defense, justice, taxes, public services, etc?
                                (m) other: Was the system that failed related to an industry not described in the (a to l) options?
                                """),
        "consequence":          textwrap.dedent("""
                                (a) death: Did people lose their lives due to the software failure?
                                (b) harm: Were people physically harmed due to the software failure?
                                (c) basic: Were people's access to food or shelter impacted because of the software failure?
                                (d) property: Were people's material goods, money, or data impacted due to the software failure?
                                (e) delay: Did people have to postpone an activity due to the software failure?
                                (f) non-human: Were non-human entities impacted due to the software failure?
                                (g) no_consequence: Were there no real observed consequences of the software failure?
                                (h) theoretical_consequence: Were there potential consequences discussed of the software failure that did not occur?
                                (i) other: Was there consequence(s) of the software failure not described in the (a to h) options? What is the other consequence(s)?
                                """),
        "cps":                  textwrap.dedent("""
                                cps: Is the overall system in the incident a cyber physical system (cps)?
                                """),
        #CPS:
        "perception":           textwrap.dedent("""
                                (a) sensor: Was the failure due to at least one contributing factor introduced by sensor error?
                                (b) actuator: Was the failure due to at least one contributing factor introduced by actuator error?
                                (c) processing_unit: Was the failure due to at least one contributing factor introduced by processing error?
                                (d) network_communication: Was the failure due to at least one contributing factor introduced by network communication error?
                                (e) embedded_software: Was the failure due to at least one contributing factor introduced by embedded software error?
                                """),
        "communication":        textwrap.dedent("""
                                (a) link_level: Was the failure due to at least one contributing factor introduced by wired or wireless physical layer?
                                (b) connectivity_level: Was the failure due to at least one contributing factor introduced by network or transport layer?
                                """),
        "application":          textwrap.dedent("""
                                application: Was the failure due to at least one contributing factor introduced by bugs, operating system errors, unhandled exceptions, and incorrect usage?
                                """),
}

CPS_KEYS = ["perception","communication","application"]



### DEPRECIATED
#TODO: Need to update this for Merge command, it uses the title and summary prompts from here.
QUESTIONS = {
        "title":            "Provide a 10 word title for the software failure incident. (return just the title)",
        "summary":          "Summarize the software failure incident. Include information about when the failure occured, what system failed, the cause of failure, the impact of failure, the responsible entity(s), and the impacted entity(s). (answer in under 250 words)",
        "time":             "When did the software failure incident happen? If possible, calculate using article published date and relative time mentioned in article.",
        "system":           "What system failed in the software failure incident? (answer in under 10 words)",
        "ResponsibleOrg":   "Which entity(s) was responsible for causing the software failure incident? (answer in under 10 words)",
        "ImpactedOrg":      "Which entity(s) was impacted by the software failure incident? (answer in under 10 words)",
        "SEcauses":         "What were the software causes of the failure incident? (answer in a list)",
        "NSEcauses":        "What were the non-software causes of the failure incident? (answer in a list)",
        "impacts":          "What happened due to the software failure incident? (answer in a list)",
        "preventions":      "What could have prevented the software failure incident? (answer in a list)", 
        "fixes":            "What could fix the software failure incident? (answer in a list)",
        "recurring":        "Was the software failure incident a recurring occurrence? If 'unknown' (option -1). If 'false' (option false). If true, then has the software failure incident occurred before 'within the same impacted entity' (option 0) or 'at other entity(s)' (option 1) or 'unknown' (option true)?",
        "references":       "From where do the articles gather information about the software failure incident? (answer in a list)",
        "phase":            "Was the software failure due to 'system design' (option 0) or 'operation' (option 1) faults or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?",
        "boundary":         "Was the software failure due to faults from 'within the system' (option 0) or from 'outside the system' (option 1) or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?",
        "nature":           "Was the software failure due to 'human actions' (option 0) or 'non human actions' (option 1) or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?",
        "dimension":        "Was the software failure due to 'hardware' (option 0) or 'software' (option 1) faults or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?",
        "objective":        "Was the software failure due to 'malicious' (option 0) or 'non-malicious' (option 1) faults or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?",
        "intent":           "Was the software failure due to 'deliberate' (option 0) or 'accidental' (option 1) fault or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?",
        "capability":       "Was the software failure 'accidental' (option 0) or due to 'development incompetence' (option 1) or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?",
        "duration":         "Was the software failure due to 'permanent' (option 0) or 'temporary' (option 1) or 'intermittent' (option 2) faults or 'unknown' (option -1)?",
        "domain":           "What application domain is the system: 'information' (option 0) or 'transportation' (option 1) or 'natural resources' (option 2) or 'sales' (option 3) or 'construction' (option 4) or 'manufacturing' (option 5) or 'utilities' (option 6) or 'finance' (option 7) or 'knowledge' (option 8) or 'health' (option 9) or 'entertainment' (option 10) or 'government' (option 11) or 'consumer device' (option 12) or 'multiple' (option 13) or 'other' (option 14) or 'unknown' (option -1)?",
        "cps":              "Does the system contain software that controls physical components (cyber physical system) or is it an IoT system: 'true' (option true) or 'false' (option false) or 'unknown' (option -1)?",
        "perception":       "Was the software failure due to 'sensors' (option 0) or 'actuators' (option 1) or 'processing unit' (option 2) or 'network communication' (option 3) or 'embedded software' (option 4) or 'unknown' (option -1)?",
        "communication":    "Was there a software failure at the communication level? If 'unknown' (option -1). If 'false' (option false). If true, then was the failure at the 'wired/wireless link level' (option 0) or 'connectivity level' (option 1) or 'unknown' (option true)?",
        "application":      "Was the software failure at the application level due to bugs, operating system errors, unhandled exceptions, or incorrect usage: 'true' (option true) or 'false' (option false) or 'unknown' (option -1)?",
        "behaviour":        "Was the software failure due to a 'crash' (option 0) or 'omission' (option 1) or 'timing' (option 2) or 'incorrect value' (option 3) or 'Byzantine' fault (option 4) or 'unknown' (option -1)?"
}


TAXONOMY_OPTIONS = {
            "phase": {"0": "system design", "1": "operation", "2": "both", "3": "neither", "-1": "unknown"},
            "boundary": {"0": "within the system", "1": "outside the system", "2": "both", "3": "neither", "-1": "unknown"},
            "nature": {"0": "human actions", "1": "non human actions", "2": "both", "3": "neither", "-1": "unknown"},
            "dimension": {"0": "hardware", "1": "software", "2": "both", "3": "neither", "-1": "unknown"},
            "objective": {"0": "malicious", "1": "non-malicious", "2": "both", "3": "neither", "-1": "unknown"},
            "intent": {"0": "deliberate", "1": "accidental", "2": "both", "3": "neither", "-1": "unknown"},
            "capability": {"0": "accidental", "1": "development incompetence", "2": "both", "3": "neither", "-1": "unknown"},
            "duration": {"0": "permanent", "1": "temporary", "2": "neither", "-1": "unknown"},
            "domain": {"0": "information", "1": "transportation", "2": "natural resources", "3": "sales", "4": "construction", "5": "manufacturing", "6": "utilities", "7": "finance", "8": "knowledge", "9": "health", "10": "entertainment", "11": "government", "12": "consumer device", "13": "multiple", "14": "other", "-1": "unknown"},
            "cps": {"true": "true", "false": "false", "-1": "unknown"},
            "perception": {"0": "sensors", "1": "actuators", "2": "processing unit", "3": "network communication", "4": "embedded software", "-1": "unknown"},
            "communication": {"true": "true", "false": "false", "0": "wired/wireless link level", "1": "connectivity level", "-1": "unknown"},
            "application": {"true": "true", "false": "false", "-1": "unknown"},
            "behaviour": {"0": "crash", "1": "omission", "2": "timing", "3": "incorrect value", "4": "byzantine fault", "-1": "unknown"},
            "recurring": {"true": "true", "false": "false", "0": "within the same impacted entity", "1": "at other entity(s)", "-1": "unknown"},
        }

# TODO: Get the software failure synonyms from the variable
CLUSTER_PROMPTS  = {
        "SEcauses": {
                "identify_themes": # We call memos as themes
                        textwrap.dedent("""
                        You will be conducting tasks to analyze a factor that caused a software failure incident.

                        Note that a software failure incident could mean a hack, bug, fault, error, exception, crash, glitch, defect, incident, flaw, mistake, anomaly, or side effect.

                        Task: For the provided Factor which was a cause of a software failure incident, identify a theme. Provide a theme for the factor (key: theme) and a description for the theme (key: description).
                        
                        If the Factor is unknown, identify the theme as unknown.
                        
                        Note: Don't identify themes that are too general or vague (For example: Don't create themes like 'Technical Failure', it would be too general.).
                        
                        Return the output in the following JSON format:
                        {
                        "theme": "",
                        "description": "",
                        }

                        Factor:
                        """),

                "reduce_themes": # We call memos as themes
                        textwrap.dedent("""
                        You will be conducting tasks to reduce duplicate themes by grouping themes that are identical and then create unique themes representing each group of identical themes.
                                        
                        Note that each theme represents a factor that caused a software failure incident.
                                        
                        Note that a software failure incident could mean a hack, bug, fault, error, exception, crash, glitch, defect, incident, flaw, mistake, anomaly, or side effect.

                        The provided JSON named Themes contains all the themes and their descriptions.

                        The format of Themes is:
                        [
                        {
                        "theme: "(theme representing a cause of a software failure incident)",
                        "description": "(description of theme)",
                        },
                        ...
                        ]
                        
                        Tasks:
                        Task 1: Group together themes that have identical or similar descriptions.
                        Task 2: Create a unique theme representing the group for each group of identical or similar themes.
                        Task 3: Return a JSON containing only the unique themes, with the following format:
                        {
                        "(grouped unique theme)": "(description of the grouped unique theme)",
                        ...
                        }

                        Note that if there are unknown themes, group them into a theme called unknown.

                        Themes:
                        """),

                "group_themes": #A cause can be in more than one group. # Note, that rather than calling memos or themes, we call them causes.
                        textwrap.dedent("""
                        Given a set of themes representing causes of software failure incidents, you will be conducting tasks to group similar themes into bigger themes.
                                        
                        Note that a software failure incident could mean a hack, bug, fault, error, exception, crash, glitch, defect, incident, flaw, mistake, anomaly, or side effect.
                        
                        The provided list of JSONs named Themes contains all the themes and their descriptions.

                        The format of Themes is:
                        [
                        {
                        "(theme representing a cause of a software failure incident)": "(description of the theme)",
                        },
                        ...
                        ]
                        
                        Tasks: 
                        Task 1: Determine how similar themes in the Themes list can be grouped into bigger themes representing causes of software failure incidents.
                        Task 2: For each group of similar themes under a bigger theme, name the bigger theme and provide a detailed definition under 'description' explaining what causes of software failures the bigger theme encompasses.
                        Task 3: Return a JSON containing the bigger themes, with the following format:
                        {
                        (id): {
                                "theme": "",
                                "description": ""
                                },
                                ...
                        }
                        
                        Note that id should just be a number as a string.
                        
                        Note that there should be more than 3 big themes.
                        
                        Note that if there are unknown themes, group them into a big theme called unknown.
                        
                        Note: Don't create big themes that are too general or vague (For example: Don't create themes like 'Technical Failure', it would be too general.).

                        Themes:
                        """),

                "name_themes": # TODO: Outdated? Not necessary
                        textwrap.dedent("""
                        using all the topics in the list, give a summary (in 2 sentences) and a name (5 words max) for the summary.

                        Format the output as a JSON list with keys "theme" and "description".

                        {
                        (id): {
                                "theme": "",
                                "description": ""
                        },
                        (id): {
                                "theme": "",
                                "description": ""
                        }
                        ...
                        }

                        List of topics:
                        """),
                },
        "NSEcauses": {
                "identify_themes": 
                        textwrap.dedent("""
                        You will be conducting steps to analyze non-software factors that caused a software failure incident.

                        Note that a software failure incident could mean a hack, bug, fault, error, exception, crash, glitch, defect, incident, flaw, mistake, anomaly, or side effect.

                        Step 1: Identify a theme for the Factor that was a non-software cause of a software failure incident. Provide a theme for the factor (key: theme) and a description for the theme (key: description).

                        Return the output in the following JSON format:
                        {
                        "theme": "",
                        "description": "",
                        }

                        Factor:
                        """),

                "reduce_themes": 
                        textwrap.dedent("""
                        You will be conducting steps to group non-software factors that caused a software failure incident by their themes.

                        The following JSON named Factors contains all the factors and their themes

                        The format of Factors is:
                        [
                        {
                                "cause": "(factor that caused the failure)",
                                "theme: "(theme of factor)",
                                "description": "(description of theme)",
                        },
                        ...
                        ]

                        Step 1: Find themes that have similar descriptions that can be grouped together.
                        Step 2: Return a JSON only containing only unique themes, with the following format:
                        {
                        "(grouped theme)": "(description of the grouped theme)",
                                ...
                        }

                        Factors:
                        """),

                "group_themes": 
                        textwrap.dedent("""
                        Determine how all of the categories non-software causes of software engineering failures in the following list of topics can be grouped together into greater than 3 themes,
                        and topics can also be in more than one group.

                        For each theme, provide a detailed definition under 'description' explaining what it encompasses and why it's important in software engineering.

                        Format the output as a list of JSONs with keys "theme", "topics", "description", where description explains the theme.

                        {
                        (id): {
                                "theme": "",
                                "description": ""
                                },
                        (id): {
                                "theme": "",
                                "description": ""
                                },
                                ...
                        }

                        List of topics:
                        """),

                "name_themes": 
                        textwrap.dedent("""
                        using all the topics in the list, give a summary (in 2 sentences) and a name (5 words max) for the summary.

                        Format the output as a JSON list with keys "theme" and "description".

                        {
                        (id): {
                                "theme": "",
                                "description": ""
                        },
                        (id): {
                                "theme": "",
                                "description": ""
                        }
                        ...
                        }

                        List of topics:
                        """),
                },
        
        "impacts": {
                "identify_themes": 
                        textwrap.dedent("""
                        You will be conducting steps to analyze impacts of software failure incidents.

                        Note that a software failure incident could mean a hack, bug, fault, error, exception, crash, glitch, defect, incident, flaw, mistake, anomaly, or side effect.

                        Step 1: Identify a theme for the impact resulting from a software failure incident. Provide a theme for the factor (key: theme) and a description for the theme (key: description). Limit the description to one sentence.

                        Return the output in the following JSON format:
                        {
                        "theme": "",
                        "description": "",
                        }

                        Factor:
                        """),

                "reduce_themes": 
                        textwrap.dedent("""
                        You will be conducting steps to group impacts resulting from software failure incidents by their themes.

                        The following JSON named Factors contains all the impacts and their themes

                        The format of Factors is:
                        [
                        {
                                "impact": "(impact resulting from software failure incident)",
                                "theme: "(theme of impact)",
                                "description": "(description of theme)",
                        },
                        ...
                        ]

                        Step 1: Find themes that have similar descriptions that can be grouped together.
                        Step 2: Return a JSON only containing only unique themes, with the following format:
                        {
                        "(grouped theme)": "(<10 word description of the grouped theme)",
                                ...
                        }

                        Factors:
                        """),

                "group_themes": 
                        textwrap.dedent("""
                        Determine how all of the categories impacts resulting from software engineering failure incidents in the following list of topics can be grouped together into greater than 3 themes,
                        and topics can also be in more than one group.

                        For each theme, provide a detailed definition under 'description' explaining what it encompasses and why it's important in software engineering.

                        Format the output as a list of JSONs with keys "theme", "topics", "description", where description explains the theme.

                        {
                        (id): {
                                "theme": "",
                                "description": ""
                                },
                        (id): {
                                "theme": "",
                                "description": ""
                                },
                                ...
                        }

                        List of topics:
                        """),

                "name_themes": 
                        textwrap.dedent("""
                        using all the topics in the list, give a summary (in 2 sentences) and a name (5 words max) for the summary.

                        Format the output as a JSON list with keys "theme" and "description".

                        {
                        (id): {
                                "theme": "",
                                "description": ""
                        },
                        (id): {
                                "theme": "",
                                "description": ""
                        }
                        ...
                        }

                        List of topics:
                        """),
            
                },
        "fixes": {
                "identify_themes": 
                        textwrap.dedent("""
                        You will be conducting steps to analyze fixes/preventions for software failure incidents.

                        Note that a software failure incident could mean a hack, bug, fault, error, exception, crash, glitch, defect, incident, flaw, mistake, anomaly, or side effect.

                        Step 1: Identify a theme for the Factor that fixed/prevented a software failure incident. Provide a theme for the factor (key: theme) and a description for the theme (key: description). Limit the description to one sentence.

                        Return the output in the following JSON format:
                        {
                        "theme": "",
                        "description": "",
                        }

                        Factor:
                        """),

                "reduce_themes": 
                        textwrap.dedent("""
                        You will be conducting steps to group factors that fixed/prevented a software failure incident by their themes.

                        The following JSON named Factors contains all the factors and their themes

                        The format of Factors is:
                        [
                        {
                                "fix": "(factor that fixed/prevented the failure)",
                                "theme: "(theme of factor)",
                                "description": "(description of theme)",
                        },
                        ...
                        ]

                        Step 1: Find themes that have similar descriptions that can be grouped together.
                        Step 2: Return a JSON only containing only unique themes, with the following format:
                        {
                        "(grouped theme)": "(<10 word description of the grouped theme)",
                                ...
                        }

                        Factors:
                        """),

                "group_themes": 
                        textwrap.dedent("""
                        Determine how all of the categories of software engineering failure fixes/preventions in the following list of topics can be grouped together into greater than 3 themes,
                        and topics can also be in more than one group.

                        For each theme, provide a detailed definition under 'description' explaining what it encompasses and why it's important in software engineering.

                        Format the output as a list of JSONs with keys "theme", "topics", "description", where description explains the theme.

                        {
                        (id): {
                                "theme": "",
                                "description": ""
                                },
                        (id): {
                                "theme": "",
                                "description": ""
                                },
                                ...
                        }

                        List of topics:
                        """),

                "name_themes": 
                        textwrap.dedent("""
                        using all the topics in the list, give a summary (in 2 sentences) and a name (5 words max) for the summary.

                        Format the output as a JSON list with keys "theme" and "description".

                        {
                        (id): {
                                "theme": "",
                                "description": ""
                        },
                        (id): {
                                "theme": "",
                                "description": ""
                        }
                        ...
                        }

                        List of topics:
                        """),
        }
        
}
'''
If an appropriate theme was not found, then create a new theme and description for the factor .
The output format for a new theme should be a JSON
{
"theme": "",
"description": ""
}
'''
CODING_PROMPTS = {
        "SEcauses": {
                "str1": 
                        """Using the following CodeBook containing themes and their descriptions, label the provided Factor (use its Memo and Description as context) with the most appropriate theme (using the id number).""",
                "str2": """\n\nCodeBook = """,
                "str3":
                        """\n\nFactor: """,
                "str4":
                        """\n(Memo: """,
                "str5":
                        """, Description: """,
                "str6":
                        textwrap.dedent(""")\n\nReturn a JSON with the id of the theme that most appropriately descibes the Factor:
                        {
                        "id": ""
                        }
                        """),
                },

        "NSEcauses": {
                "code_item1": 
                        """Using the codes and their definitions from the code book, please proceed to label the response accordingly (using code id). """,
                "code_item2":
                        """ Here is the response """,
                "code_item3":
                        textwrap.dedent(""". The output format should be in JSON.
                        {
                        "code": ""
                        }

                        If none of the themes accurately fit which type of non software engineering cause of software engineering failure the response is, then create a new theme and description.
                        The output format for a new theme should be a JSON
                        {
                        "theme": "",
                        "description": ""
                        }
                        """),
                },

        "impacts": {
                "code_item1": 
                        """Using the codes and their definitions from the code book, please proceed to label the response accordingly (using code id). """,
                "code_item2":
                        """ Here is the response """,
                "code_item3":
                        textwrap.dedent(""". The output format should be in JSON.
                        {
                        "code": ""
                        }

                        If none of the themes accurately fit which type of impact resulting from a software engineering failure the response is, then create a new theme and description.
                        The output format for a new theme should be a JSON
                        {
                        "theme": "",
                        "description": ""
                        }
                        """),
                },
        "fixes": {
                "code_item1": 
                        """Using the codes and their definitions from the code book, please proceed to label the response accordingly (using code id). """,
                "code_item2":
                        """ Here is the response """,
                "code_item3":
                        textwrap.dedent(""". The output format should be in JSON.
                        {
                        "code": ""
                        }

                        If none of the themes accurately fit which type of fix/prevention for a software engineering failure the response is, then create a new theme and description.
                        The output format for a new theme should be a JSON
                        {
                        "theme": "",
                        "description": ""
                        }
                        """),
                }
}