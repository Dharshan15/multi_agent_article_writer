from crewai import Agent, Task, Crew
import os 
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
llm = ChatGroq(
    model = "groq/deepseek-r1-distill-llama-70b",
    max_tokens = 1000, # because groq free tier allows only upto 6000 tokens per minute
)

#Agents
planner = Agent(
    role = "Content Planner",
    goal = "Plan engaging and fatually accurate content on {topic}",
    backstory = "You are working on planning a blog article about the topic: {topic}." 
    "You collect information that helps the audience learn something and make informed decisions." 
    "Your work is the basis for the Content Writer to write an article on this topic",
    allow_delegation = False,
    verbose = True,
    llm = llm,
)

writer = Agent(
    role = "Content Writer",
    goal = "Write insightful and factually accurate opinion piece about the topic:{topic}",
    backstory = "You are working on writing a new opinion piece about the topic:{topic}."
    "You base your writing on the work of the Content Planner, who provides an outline "
    "and relevant context about the topic. You follow the main objectives and direction of the outline, "
    "as provided by the Content Planner. You also provide objective and impartial insights "
    "and back them up with information provide by the Content planner. "
    "You acknowledge in your opinion piece when your statements are opinions as opposed "
    "to objective statements",
    allow_delegation = False,
    verbose = True,
    llm = llm,
)

editor = Agent(
    role = "Editor",
    goal = "Edit a given blog post to align with the writing style of the organization.",
    backstory = "You are an editor who receives a blog post from the Content Writer. "
    "Your goal is to review the blog post to ensure that it follows journalistic best practices, "
    "provides balanced viewpoints when providing balanced viewpoints "
    "when providing opinions or assertions, and also avoids major controversial topics "
    "or opinions when possible.",
    allow_delegation = False,
    verbose = True,
    llm = llm,
)

#Tasks
plan = Task(
    description=(
        "1. Prioritize the latest trends, key players, "
            "and noteworthy news on {topic}.\n"
        "2. Identify the target audience, considering "
            "their interests and pain points.\n"
        "3. Develop a detailed content outline including "
            "an introduction, key points, and a call to action.\n"
        "4. Include SEO keywords and relevant data or sources."
    ),
    expected_output="A comprehensive content plan document "
        "with an outline, audience analysis, "
        "SEO keywords, and resources.",
    agent=planner,
)

write = Task(
    description=(
        "1. Use the content plan to craft a compelling "
            "blog post on {topic}.\n"
        "2. Incorporate SEO keywords naturally.\n"
		"3. Sections/Subtitles are properly named "
            "in an engaging manner.\n"
        "4. Ensure the post is structured with an "
            "engaging introduction, insightful body, "
            "and a summarizing conclusion.\n"
        "5. Proofread for grammatical errors and "
            "alignment with the brand's voice.\n"
    ),
    expected_output="A well-written blog post "
        "in markdown format, ready for publication, "
        "each section should have 2 or 3 paragraphs.",
    agent=writer,
)

edit = Task(
    description=("Proofread the given blog post for "
                 "grammatical errors and "
                 "alignment with the brand's voice."),
    expected_output="A well-written blog post in markdown format, "
                    "ready for publication, "
                    "each section should have 2 or 3 paragraphs.",
    agent=editor
)

#crew operates sequentially. Order is important

crew = Crew(
    agents = [planner, writer, editor],
    tasks = [plan, write, edit],
    verbose = True #for logs
)

# result = crew.kickoff(inputs={"topic":"Large language models"}) #input dict contains the variables that we used while defining agents and tasks


from litellm.exceptions import RateLimitError
import time

results = []
inputs = {"topic": "Large language models"}
for i, task in enumerate(crew.tasks):
    while True:  # Retry until success
        try:
            print(f"Running task {i+1}/{len(crew.tasks)}: {task.description[:50]}...")
            # Pass the Task object and inputs separately
            result = task.agent.execute_task(task=task, context=results[-1] if results else None)
            results.append(result)
            break  # Move to next task if successful
        except RateLimitError as e:
            wait_time = 10
            print(f"Rate limit hit on task {i+1}: {e}. Waiting {wait_time}s...")
            time.sleep(wait_time)
    time.sleep(5)  # Small delay between tasks

print(results[-1])  # Final edited blog post