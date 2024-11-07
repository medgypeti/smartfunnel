import requests
import json
import os
from groq import Groq
from typing import Dict, List
import statistics
import pydantic

class SalaryData(pydantic.BaseModel):
    total_compensation: float

def fetch_salary_data(query: str, location: str) -> Dict:
    """
    Fetch salary data from Google Search API using Serper
    """
    url = "https://google.serper.dev/search"
    formatted_query = f"salary {query} {location}"
    
    payload = json.dumps({
        "q": formatted_query,
        "location": "United States",
        "type": "search",
        "engine": "google",
        "gl": "us"
    })
    
    headers = {
        'X-API-KEY': '5cbe6ac71fee0a4d725a0a12a80663b0fcaa28bd',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def extract_salary_info(search_results: Dict) -> List[str]:
    """
    Extract the first 4 snippet results from the search data
    """
    if not search_results or 'organic' not in search_results:
        return []
        
    snippets = []
    for result in search_results.get('organic', [])[:4]:
        snippets.append(result.get('snippet', ''))
    return snippets

def analyze_salaries_with_llm(snippets: List[str]) -> float:
    """
    Use Groq with LLaMA to analyze salary snippets and extract average total pay
    """
    if not snippets:
        return 0.0
        
    client = Groq(api_key="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")
    
    prompt = f"""
    Analyze these salary snippets and extract total compensation figures. Follow these rules:
    1. Only include figures explicitly stated as total pay, total compensation, or total salary
    2. If a range is given, use the average of the range
    3. Convert hourly rates to annual (multiply by 2080)
    4. Ignore experience-based salaries unless they're averages
    5. Return each valid total compensation figure on a new line
    6. Only return the numerical values, no text
    
    For example:
    Input: "The estimated total pay is $100,000 to $120,000"
    Output: 110000
    
    Input: "The average base salary is $80,000 with total compensation of $95,000"
    Output: 95000
    
    Here are the snippets to analyze:
    {json.dumps(snippets, indent=2)}
    """
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="llama3-70b-8192",
    )
    
    try:
        # Get the response and split it into lines
        response_lines = chat_completion.choices[0].message.content.strip().split('\n')
        
        # Convert each line to a float, removing any non-numeric characters
        salaries = []
        for line in response_lines:
            try:
                cleaned_value = ''.join(c for c in line if c.isdigit() or c == '.')
                if cleaned_value:
                    value = float(cleaned_value)
                    if value > 0:  # Only include positive values
                        salaries.append(value)
            except ValueError:
                continue
        
        # Calculate average if we have valid salaries
        if salaries:
            print(f"Found valid total compensation figures: {salaries}")
            return statistics.mean(salaries)
        return 0.0
        
    except Exception as e:
        print(f"Error processing LLM response: {e}")
        return 0.0

def calculate_task_costs(annual_salary: float, hours_per_task: float, times_per_month: int) -> Dict[str, float]:
    """
    Calculate various cost metrics based on salary and task parameters
    """
    # Calculate hourly rate (annual salary divided by 2080 work hours per year)
    hourly_rate = annual_salary / 2080
    
    # Calculate monthly task hours
    monthly_task_hours = hours_per_task * times_per_month
    
    # Calculate monthly cost for this task
    monthly_task_cost = hourly_rate * monthly_task_hours
    
    # Calculate annual cost for this task
    annual_task_cost = monthly_task_cost * 12
    
    return {
        "hourly_rate": hourly_rate,
        "monthly_task_hours": monthly_task_hours,
        "monthly_task_cost": monthly_task_cost,
        "annual_task_cost": annual_task_cost
    }

def get_user_inputs() -> Dict[str, any]:
    """
    Get all necessary inputs from the user including company and task details
    """
    print("\n=== Job Search Parameters ===")
    job_query = input("Enter job title to search (e.g., 'senior procurement manager'): ")
    location = input("Enter location (e.g., 'New York'): ")
    
    print("\n=== Company Information ===")
    company_activity = input("What is your company's main business activity? Please be specific: ")
    
    print("\n=== Task Details ===")
    task_description = input("Please describe the specific task that needs automation (be detailed): ")
    # current_challenges = input("What are the current challenges or bottlenecks in this task? ")
    
    print("\n=== Task Parameters ===")
    while True:
        try:
            hours_per_task = float(input("How many hours does the employee work on this task (per occurrence)? "))
            if hours_per_task <= 0:
                print("Hours must be greater than 0")
                continue
            break
        except ValueError:
            print("Please enter a valid number")
    
    while True:
        try:
            times_per_month = int(input("How many times per month is this task performed? "))
            if times_per_month <= 0:
                print("Frequency must be greater than 0")
                continue
            break
        except ValueError:
            print("Please enter a valid number")
    
    return {
        "job_query": job_query,
        "location": location,
        "company_activity": company_activity,
        "task_description": task_description,
        "hours_per_task": hours_per_task,
        "times_per_month": times_per_month
    }

# def get_user_inputs() -> Dict[str, any]:
#     """
#     Get all necessary inputs from the user
#     """
#     print("\n--- Job Search Parameters ---")
#     job_query = input("Enter job title to search (e.g., 'senior procurement manager'): ")
#     location = input("Enter location (e.g., 'New York'): ")
    
#     print("\n--- Task Parameters ---")
#     while True:
#         try:
#             hours_per_task = float(input("How many hours does the employee work on this task (per occurrence)? "))
#             if hours_per_task <= 0:
#                 print("Hours must be greater than 0")
#                 continue
#             break
#         except ValueError:
#             print("Please enter a valid number")
    
#     while True:
#         try:
#             times_per_month = int(input("How many times per month is this task performed? "))
#             if times_per_month <= 0:
#                 print("Frequency must be greater than 0")
#                 continue
#             break
#         except ValueError:
#             print("Please enter a valid number")
    
#     return {
#         "job_query": job_query,
#         "location": location,
#         "hours_per_task": hours_per_task,
#         "times_per_month": times_per_month
#     }

def analyze_automation_potential(inputs: Dict[str, any], annual_salary: float) -> tuple[str, str]:
    """
    Use LLM to analyze automation potential and generate recommendations
    """
    client = Groq(api_key="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")
    
    prompt = f"""
    Analyze this business scenario and provide detailed AI automation recommendations:

    CONTEXT:
    Role: {inputs['job_query']}
    Company Activity: {inputs['company_activity']}
    Task Description: {inputs['task_description']}
    Time Investment: {inputs['hours_per_task']} hours/task, {inputs['times_per_month']} times/month
    Annual Cost: ${annual_salary:,.2f}

    Please come up with the following analysis:
    - Break down the task into smaller steps
    - Estimate the percentage each step represents of the total task
    - Estimate how much time the task takes in a year before automation
    - Estimate how much time the task takes in a year after automation
    - Estimate potential time savings
    - Project potential ROI

    IMPORTANT:
    - Only return the analysis, no other text
    - Stay concise, sharp, and to the point
    - Come up with actionable and practical tips. Avoid jargon and technical terms.
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-70b-8192",
            temperature=0.6,
            max_tokens=2048,
        )
        
        # Split the response into two sections
        full_response = chat_completion.choices[0].message.content
        sections = full_response.split('\n\n2.')
        
        if len(sections) > 1:
            direct_automation = sections[0].replace('1.', '').strip()
            second_order_effects = '2.' + sections[1].strip()
        else:
            direct_automation = full_response
            second_order_effects = "Analysis of second-order effects not available."
            
        return direct_automation, second_order_effects
        
    except Exception as e:
        print(f"Error generating automation analysis: {e}")
        return "Error analyzing automation potential.", "Error analyzing second-order effects."


def main():
    """
    Main function to coordinate the entire process
    """
    # Get user inputs
    inputs = get_user_inputs()
    
    # Fetch and analyze salary data
    search_results = fetch_salary_data(inputs["job_query"], inputs["location"])
    
    if not search_results:
        print("Error: Unable to fetch search results")
        return
    
    snippets = extract_salary_info(search_results)
    
    if not snippets:
        print("Error: No relevant salary information found")
        return
    
    print("\nAnalyzing salary data...")
    average_annual_salary = analyze_salaries_with_llm(snippets)
    
    if average_annual_salary <= 0:
        print("Error: Could not determine valid salary information")
        return
    
    # Calculate task costs
    costs = calculate_task_costs(
        average_annual_salary,
        inputs["hours_per_task"],
        inputs["times_per_month"]
    )
    
    # Analyze automation potential
    print("\nAnalyzing automation potential...")
    direct_automation, second_order_effects = analyze_automation_potential(inputs, average_annual_salary)
    
    # Print comprehensive results
    print("\n====== Cost Analysis Results ======")
    print(f"Average Annual Salary: ${average_annual_salary:,.2f}")
    print(f"Calculated Hourly Rate: ${costs['hourly_rate']:.2f}")
    print(f"\nTask Statistics:")
    print(f"Hours per task: {inputs['hours_per_task']:.1f}")
    print(f"Times per month: {inputs['times_per_month']}")
    print(f"Total monthly hours: {costs['monthly_task_hours']:.1f}")
    print(f"\nCurrent Cost Projections:")
    print(f"Monthly Task Cost: ${costs['monthly_task_cost']:,.2f}")
    print(f"Annual Task Cost: ${costs['annual_task_cost']:,.2f}")
    
    print("\n====== AI Automation Analysis ======")
    print("\n=== Direct Automation Opportunities ===")
    print(direct_automation)
    
    print("\n=== Second-Order Effects and Business Impact ===")
    print(second_order_effects)

if __name__ == "__main__":
    main()

# def main():
#     """
#     Main function to coordinate the entire process
#     """
#     # Get user inputs
#     inputs = get_user_inputs()
    
#     # Fetch and analyze salary data
#     search_results = fetch_salary_data(inputs["job_query"], inputs["location"])
    
#     if not search_results:
#         print("Error: Unable to fetch search results")
#         return
    
#     snippets = extract_salary_info(search_results)
    
#     if not snippets:
#         print("Error: No relevant salary information found")
#         return
    
#     print("\nAnalyzing salary data...")
#     average_annual_salary = analyze_salaries_with_llm(snippets)
    
#     if average_annual_salary <= 0:
#         print("Error: Could not determine valid salary information")
#         return
    
#     # Calculate task costs
#     costs = calculate_task_costs(
#         average_annual_salary,
#         inputs["hours_per_task"],
#         inputs["times_per_month"]
#     )
    
#     # Print results
#     print("\n=== Cost Analysis Results ===")
#     print(f"Average Annual Salary: ${average_annual_salary:,.2f}")
#     print(f"Calculated Hourly Rate: ${costs['hourly_rate']:.2f}")
#     print(f"\nTask Statistics:")
#     print(f"Hours per task: {inputs['hours_per_task']:.1f}")
#     print(f"Times per month: {inputs['times_per_month']}")
#     print(f"Total monthly hours: {costs['monthly_task_hours']:.1f}")
#     print(f"\nCost Projections:")
#     print(f"Monthly Task Cost: ${costs['monthly_task_cost']:,.2f}")
#     print(f"Annual Task Cost: ${costs['annual_task_cost']:,.2f}")

# if __name__ == "__main__":
#     main()
